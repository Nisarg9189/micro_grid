"""Arithmetic invariants for the reported KPIs.

Every headline figure in the pitch comes out of `compute_kpis`, so a wrong column read
here does not produce an obviously broken run -- it produces a plausible number that is
simply false. Two such errors have already shipped and been caught by eye:

    reliability        read `load_met`, which is the load the module *asked* for, so a run
                       that shed a third of its load still reported 100% uptime
    renewable share    divided renewable output by load served, so energy routed into the
                       battery was counted against a smaller denominator and the share
                       could exceed 100%

The tests below pin both, plus the invariants that would catch the same class of mistake
elsewhere: per-feeder pricing, the diesel fuel-rate split, and the aggregation rules.
"""

import pytest

from conftest import make_log, simple_log
from gramurja.config import BACKUP_GENSET, DEFAULT_CONFIG, PUMPSET
from gramurja.kpi import KPIs, _column, _grid_cost, combine_kpis, compare, compute_kpis

DIESEL_PRICE = DEFAULT_CONFIG.economics.diesel_price_per_litre


# --------------------------------------------------------------------------------------
# _column: the log key shapes that actually reach it
# --------------------------------------------------------------------------------------

def test_column_reads_two_level_keys():
    """`get_log(drop_singleton_key=True)` drops the module-number level."""
    log = make_log({("genset", "genset_production"): [1.0, 2.0, 3.0]})
    assert _column(log, "genset", "genset_production") == pytest.approx(6.0)


def test_column_reads_three_level_keys():
    """The full shape, as emitted whenever any module type has more than one instance."""
    log = make_log({("genset", 0, "genset_production"): [1.0, 2.0, 3.0]})
    assert _column(log, "genset", "genset_production") == pytest.approx(6.0)


def test_column_sums_two_modules_of_the_same_type():
    """Two feeders, or solar plus wind, must aggregate rather than shadow each other.

    Matching on the first and last levels only is what makes this work; matching the whole
    key would find neither, and matching the first level alone would pick up `reward`.
    """
    log = make_log(
        {
            ("grid", 0, "grid_import"): [4.0, 0.0],
            ("grid", 1, "grid_import"): [1.0, 2.0],
            ("grid", 0, "reward"): [-99.0, -99.0],
        }
    )
    assert _column(log, "grid", "grid_import") == pytest.approx(7.0)


def test_column_returns_zero_for_an_absent_module():
    """A run without a genset has no genset columns at all, and must read as zero diesel."""
    log = make_log({("load", "load_current"): -5.0})
    assert _column(log, "genset", "genset_production") == 0.0


@pytest.mark.xfail(
    reason="_column requires key[0]==module and key[-1]==field, which a single-level "
           "string key can only satisfy when module == field. Latent only: pymgrid always "
           "emits at least (module, field), so no current caller hits this.",
    strict=True,
)
def test_column_reads_a_flat_string_key():
    log = make_log({("genset", "genset_production"): 6.0})
    flat = log.copy()
    flat.columns = ["genset_production"]
    assert _column(flat, "genset", "genset_production") == pytest.approx(6.0)


# --------------------------------------------------------------------------------------
# Reliability: derived from the balancing module, never from load_met
# --------------------------------------------------------------------------------------

def test_reliability_reflects_shed_load_not_requested_load():
    """Demand 100, 10 shed: 90 served, 90% reliable. The bug reported 100%.

    `load_met` in the fixture is set to the full 100, so a reading of it would give exactly
    the wrong answer and this assertion is the one that catches it.
    """
    kpis = compute_kpis(simple_log(demand=100.0, unmet=10.0, grid=90.0))

    assert kpis.demand_kwh == pytest.approx(100.0)
    assert kpis.unmet_kwh == pytest.approx(10.0)
    assert kpis.served_kwh == pytest.approx(90.0)
    assert kpis.reliability_pct == pytest.approx(90.0)
    assert kpis.reliability_pct != pytest.approx(100.0)


def test_served_plus_unmet_equals_demand():
    log = simple_log(demand=73.5, unmet=4.25, grid=69.25)
    kpis = compute_kpis(log)
    assert kpis.served_kwh + kpis.unmet_kwh == pytest.approx(kpis.demand_kwh)


def test_reliability_is_100_only_when_nothing_is_shed():
    kpis = compute_kpis(simple_log(demand=100.0, unmet=0.0, grid=100.0))
    assert kpis.reliability_pct == pytest.approx(100.0)


def test_reliability_over_many_hours_weights_by_energy():
    """A shed hour in a low-demand hour must not cost the same as one in a peak hour."""
    log = make_log(
        {
            ("load", "load_current"): [-10.0, -90.0],
            ("load", "load_met"): [10.0, 90.0],
            ("balancing", "loss_load"): [5.0, 0.0],
        }
    )
    kpis = compute_kpis(log)
    # 5 kWh shed out of 100 kWh, not "one of two hours was 50% short".
    assert kpis.reliability_pct == pytest.approx(95.0)


def test_demand_is_reported_positive_from_negative_sink_logging():
    kpis = compute_kpis(simple_log(demand=42.0))
    assert kpis.demand_kwh == pytest.approx(42.0)


# --------------------------------------------------------------------------------------
# Renewable share: fraction of total supply, not of load served
# --------------------------------------------------------------------------------------

def test_renewable_fraction_cannot_exceed_100_under_heavy_charging():
    """100 kWh of solar against 10 kWh of load: the rest went into the battery.

    Dividing by load served gave 1000%. Dividing by total supply gives 100%, which is the
    honest reading -- every kWh supplied that hour was renewable, whatever it was used for.
    """
    kpis = compute_kpis(simple_log(demand=10.0, solar=100.0))

    assert kpis.renewable_fraction_pct == pytest.approx(100.0)
    assert 0.0 <= kpis.renewable_fraction_pct <= 100.0


@pytest.mark.parametrize(
    "solar,wind,grid,diesel,expected",
    [
        (80.0, 0.0, 20.0, 0.0, 80.0),
        (30.0, 10.0, 40.0, 20.0, 40.0),
        (0.0, 0.0, 50.0, 50.0, 0.0),
        (50.0, 50.0, 0.0, 0.0, 100.0),
    ],
)
def test_renewable_fraction_is_share_of_total_supply(solar, wind, grid, diesel, expected):
    kpis = compute_kpis(
        simple_log(demand=5.0, solar=solar, wind=wind, grid=grid, diesel=diesel)
    )
    assert kpis.renewable_fraction_pct == pytest.approx(expected)
    assert 0.0 <= kpis.renewable_fraction_pct <= 100.0


def test_renewable_fraction_ignores_curtailed_energy():
    """Curtailed output never reached the bus, so it cannot count towards the share."""
    served = compute_kpis(simple_log(demand=10.0, solar=10.0, grid=10.0))
    curtailing = compute_kpis(
        simple_log(demand=10.0, solar=10.0, curtailed=500.0, grid=10.0)
    )
    assert curtailing.renewable_curtailed_kwh == pytest.approx(500.0)
    assert curtailing.renewable_fraction_pct == pytest.approx(served.renewable_fraction_pct)
    assert curtailing.renewable_fraction_pct == pytest.approx(50.0)


def test_solar_and_wind_are_read_from_their_own_renewable_modules():
    """Solar and wind share the `renewable` module name and differ only in the field."""
    log = make_log(
        {
            ("load", "load_current"): -10.0,
            ("renewable", 0, "solar_used"): 7.0,
            ("renewable", 0, "curtailment"): 1.0,
            ("renewable", 1, "wind_used"): 3.0,
            ("renewable", 1, "curtailment"): 2.0,
        }
    )
    kpis = compute_kpis(log)
    assert kpis.solar_used_kwh == pytest.approx(7.0)
    assert kpis.wind_used_kwh == pytest.approx(3.0)
    assert kpis.renewable_curtailed_kwh == pytest.approx(3.0)


# --------------------------------------------------------------------------------------
# Diesel: the pumpset/genset fuel-rate split
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("unit,rate", [(PUMPSET, 0.75), (BACKUP_GENSET, 0.30)])
def test_diesel_litres_follow_the_units_own_fuel_rate(unit, rate):
    """A direct-coupled pumpset burns 2.5x what a proper genset does per kWh.

    Sharing one rate between them overstated whole-farm diesel cost roughly 2.5-fold, so
    both presets are pinned here rather than only the default.
    """
    assert unit.litres_per_kwh == pytest.approx(rate)

    kpis = compute_kpis(simple_log(demand=100.0, diesel=100.0), diesel_unit=unit)
    assert kpis.diesel_kwh == pytest.approx(100.0)
    assert kpis.diesel_litres == pytest.approx(100.0 * rate)
    assert kpis.diesel_cost_inr == pytest.approx(100.0 * rate * DIESEL_PRICE)


def test_pumpset_diesel_is_two_and_a_half_times_the_genset():
    pumpset = compute_kpis(simple_log(demand=100.0, diesel=100.0), diesel_unit=PUMPSET)
    genset = compute_kpis(simple_log(demand=100.0, diesel=100.0), diesel_unit=BACKUP_GENSET)
    assert pumpset.diesel_litres == pytest.approx(genset.diesel_litres * 2.5)


def test_no_genset_means_no_diesel_or_diesel_cost():
    kpis = compute_kpis(simple_log(demand=100.0, grid=100.0), diesel_unit=PUMPSET)
    assert kpis.diesel_kwh == 0.0
    assert kpis.diesel_litres == 0.0
    assert kpis.diesel_cost_inr == 0.0


@pytest.mark.xfail(
    reason="compute_kpis derives litres from the diesel_unit passed in, but reads co2 "
           "straight out of the log, where it was priced by the unit given to "
           "build_microgrid. Nothing cross-checks the two, so a caller that passes the "
           "wrong unit gets diesel litres and diesel CO2 that silently disagree. Latent: "
           "every call site in src/ and scripts/ currently pairs them correctly.",
    strict=True,
)
def test_diesel_co2_is_consistent_with_reported_litres():
    co2_per_litre = DEFAULT_CONFIG.economics.co2_kg_per_litre_diesel
    # Log produced by a microgrid built with the pumpset: 100 kWh at 0.75 L/kWh.
    log = simple_log(demand=100.0, diesel=100.0, genset_co2=100.0 * 0.75 * co2_per_litre)

    kpis = compute_kpis(log, diesel_unit=BACKUP_GENSET)
    assert kpis.co2_kg == pytest.approx(kpis.diesel_litres * co2_per_litre)


# --------------------------------------------------------------------------------------
# Grid cost: each feeder at its own tariff
# --------------------------------------------------------------------------------------

def test_grid_cost_prices_each_feeder_at_its_own_tariff():
    """The whole point of the two-feeder model is that the tariffs differ 3.3-fold.

    Agricultural import is Rs 1.50/kWh and village import Rs 5.00/kWh. 10 kWh of the
    first and 4 kWh of the second cost Rs 35, not 14 kWh at some blended Rs 3.25 (Rs 45.50).
    """
    log = make_log(
        {
            ("load", "load_current"): -14.0,
            ("grid", 0, "grid_import"): 10.0,
            ("grid", 0, "import_price_current"): 1.50,
            ("grid", 1, "grid_import"): 4.0,
            ("grid", 1, "import_price_current"): 5.00,
        }
    )
    kpis = compute_kpis(log)

    assert kpis.grid_kwh == pytest.approx(14.0)
    assert kpis.grid_cost_inr == pytest.approx(35.0)
    blended = 14.0 * (1.50 + 5.00) / 2
    assert kpis.grid_cost_inr != pytest.approx(blended)


def test_grid_cost_follows_an_hourly_price_series():
    """Prices are logged per hour, so the cost has to be the dot product, not mean x total."""
    log = make_log(
        {
            ("load", "load_current"): [-3.0, -3.0],
            ("grid", "grid_import"): [1.0, 3.0],
            ("grid", "import_price_current"): [10.0, 1.0],
        }
    )
    assert _grid_cost(log) == pytest.approx(1.0 * 10.0 + 3.0 * 1.0)
    # The seductive wrong answer: 4 kWh at the mean price of 5.50.
    assert _grid_cost(log) != pytest.approx(22.0)


def test_grid_cost_is_zero_without_grid_import():
    log = simple_log(demand=10.0, diesel=10.0)
    assert compute_kpis(log).grid_cost_inr == 0.0


def test_total_cost_is_diesel_plus_grid():
    kpis = compute_kpis(
        simple_log(demand=100.0, grid=60.0, grid_price=2.0, diesel=40.0),
        diesel_unit=PUMPSET,
    )
    assert kpis.total_cost_inr == pytest.approx(kpis.diesel_cost_inr + kpis.grid_cost_inr)
    assert kpis.total_cost_inr == pytest.approx(120.0 + 40.0 * 0.75 * DIESEL_PRICE)


@pytest.mark.xfail(
    reason="_grid_cost only prices an import column when its paired "
           "import_price_current column exists, and silently charges nothing otherwise. "
           "A log missing the price column therefore reports a free grid rather than an "
           "error. Latent: build_microgrid always supplies the price series.",
    strict=True,
)
def test_grid_cost_does_not_silently_price_import_at_zero():
    log = make_log({("load", "load_current"): -10.0, ("grid", "grid_import"): 10.0})
    assert compute_kpis(log).grid_cost_inr > 0.0


# --------------------------------------------------------------------------------------
# CO2
# --------------------------------------------------------------------------------------

def test_co2_sums_genset_and_grid_emissions():
    log = make_log(
        {
            ("load", "load_current"): -30.0,
            ("genset", "co2_production"): 7.0,
            ("grid", 0, "co2_production"): 2.0,
            ("grid", 1, "co2_production"): 3.0,
        }
    )
    assert compute_kpis(log).co2_kg == pytest.approx(12.0)


# --------------------------------------------------------------------------------------
# Degenerate inputs
# --------------------------------------------------------------------------------------

def test_zero_demand_reports_zero_reliability_without_raising():
    kpis = compute_kpis(simple_log(demand=0.0))
    assert kpis.demand_kwh == 0.0
    assert kpis.reliability_pct == 0.0


def test_zero_supply_reports_zero_renewable_share_without_raising():
    kpis = compute_kpis(simple_log(demand=10.0, unmet=10.0))
    assert kpis.renewable_fraction_pct == 0.0
    assert kpis.reliability_pct == 0.0


def test_an_empty_log_produces_all_zeros():
    """Nothing logged is not the same as a crash, and it must not be 100% of anything."""
    log = make_log({("balance", "reward"): 0.0})
    kpis = compute_kpis(log)
    assert kpis.demand_kwh == 0.0
    assert kpis.reliability_pct == 0.0
    assert kpis.renewable_fraction_pct == 0.0
    assert kpis.total_cost_inr == 0.0


# --------------------------------------------------------------------------------------
# combine_kpis: sub-systems simulated separately
# --------------------------------------------------------------------------------------

def _kpis(**overrides) -> KPIs:
    """A KPIs record with everything zero except what the test cares about."""
    fields = dict.fromkeys(KPIs.__dataclass_fields__, 0.0)
    fields.update(overrides)
    return KPIs(**fields)


def test_combine_weights_reliability_by_energy_not_by_subsystem():
    """A 1,000 kWh irrigation system and a 10 kWh domestic one are not equal votes.

    The status-quo baseline is built exactly this way -- irrigation on the agricultural
    feeder, everything else on the village feeder -- so averaging the two percentages
    would let the small half drag the headline reliability down by 25 points.
    """
    big = _kpis(demand_kwh=1000.0, served_kwh=1000.0, unmet_kwh=0.0, reliability_pct=100.0)
    small = _kpis(demand_kwh=10.0, served_kwh=5.0, unmet_kwh=5.0, reliability_pct=50.0)

    total = combine_kpis(big, small)

    assert total.demand_kwh == pytest.approx(1010.0)
    assert total.served_kwh == pytest.approx(1005.0)
    assert total.reliability_pct == pytest.approx(100.0 * 1005.0 / 1010.0)
    assert total.reliability_pct == pytest.approx(99.50495, abs=1e-4)
    assert total.reliability_pct != pytest.approx(75.0)  # the arithmetic mean


def test_combine_recomputes_renewable_share_from_summed_totals():
    solar_heavy = _kpis(solar_used_kwh=900.0, grid_kwh=100.0, renewable_fraction_pct=90.0)
    diesel_only = _kpis(diesel_kwh=10.0, renewable_fraction_pct=0.0)

    total = combine_kpis(solar_heavy, diesel_only)

    assert total.renewable_fraction_pct == pytest.approx(100.0 * 900.0 / 1010.0)
    assert total.renewable_fraction_pct != pytest.approx(45.0)  # the arithmetic mean


def test_combine_adds_absolute_quantities():
    a = _kpis(diesel_kwh=10.0, diesel_litres=7.5, diesel_cost_inr=100.0, co2_kg=20.0,
              grid_kwh=5.0, grid_cost_inr=7.5, total_cost_inr=107.5)
    b = _kpis(diesel_kwh=4.0, diesel_litres=1.2, diesel_cost_inr=40.0, co2_kg=3.0,
              grid_kwh=1.0, grid_cost_inr=5.0, total_cost_inr=45.0)

    total = combine_kpis(a, b)

    assert total.diesel_kwh == pytest.approx(14.0)
    assert total.co2_kg == pytest.approx(23.0)
    assert total.total_cost_inr == pytest.approx(152.5)
    assert total.total_cost_inr == pytest.approx(total.diesel_cost_inr + total.grid_cost_inr)


def test_combine_keeps_litres_from_parts_with_different_fuel_rates():
    """Summed litres must not be recoverable from one rate: that is the split working.

    Irrigation runs a 0.75 L/kWh pumpset and the rest of the farm a 0.30 L/kWh genset, so
    the combined litres correspond to no single fuel rate. A later `diesel_kwh * rate`
    check on the combined record would be wrong, not the record.
    """
    pumpset = _kpis(diesel_kwh=100.0, diesel_litres=75.0)
    genset = _kpis(diesel_kwh=100.0, diesel_litres=30.0)

    total = combine_kpis(pumpset, genset)

    assert total.diesel_kwh == pytest.approx(200.0)
    assert total.diesel_litres == pytest.approx(105.0)
    assert total.diesel_litres != pytest.approx(200.0 * 0.75)
    assert total.diesel_litres != pytest.approx(200.0 * 0.30)


def test_combine_of_a_single_part_is_that_part():
    one = _kpis(demand_kwh=100.0, served_kwh=90.0, unmet_kwh=10.0, reliability_pct=90.0,
                solar_used_kwh=50.0, grid_kwh=40.0)
    total = combine_kpis(one)
    assert total.reliability_pct == pytest.approx(one.reliability_pct)
    assert total.renewable_fraction_pct == pytest.approx(100.0 * 50.0 / 90.0)


def test_combine_with_zero_demand_does_not_raise():
    total = combine_kpis(_kpis(), _kpis())
    assert total.reliability_pct == 0.0
    assert total.renewable_fraction_pct == 0.0


# --------------------------------------------------------------------------------------
# compare
# --------------------------------------------------------------------------------------

def test_compare_reports_percentage_drops_against_the_baseline():
    baseline = _kpis(diesel_litres=100.0, total_cost_inr=1000.0, co2_kg=270.0,
                     reliability_pct=80.0)
    optimized = _kpis(diesel_litres=25.0, total_cost_inr=400.0, co2_kg=70.0,
                      reliability_pct=99.0)

    result = compare(baseline, optimized)

    assert result["diesel_litres_saved"] == pytest.approx(75.0)
    assert result["diesel_reduction_pct"] == pytest.approx(75.0)
    assert result["cost_saved_inr"] == pytest.approx(600.0)
    assert result["cost_reduction_pct"] == pytest.approx(60.0)
    assert result["co2_avoided_kg"] == pytest.approx(200.0)
    # Percentage points, not a percentage of the baseline.
    assert result["reliability_change_pct"] == pytest.approx(19.0)


def test_compare_against_a_zero_baseline_does_not_raise():
    """The all-solar baseline burns no diesel, and 0 -> 0 is not a division."""
    baseline = _kpis(diesel_litres=0.0, total_cost_inr=0.0, co2_kg=0.0)
    optimized = _kpis(diesel_litres=0.0, total_cost_inr=0.0, co2_kg=0.0)

    result = compare(baseline, optimized)

    assert result["diesel_reduction_pct"] == 0.0
    assert result["cost_reduction_pct"] == 0.0


def test_compare_reports_a_regression_as_a_negative_drop():
    baseline = _kpis(diesel_litres=100.0, total_cost_inr=500.0)
    optimized = _kpis(diesel_litres=150.0, total_cost_inr=600.0)

    result = compare(baseline, optimized)

    assert result["diesel_litres_saved"] == pytest.approx(-50.0)
    assert result["diesel_reduction_pct"] == pytest.approx(-50.0)
    assert result["cost_reduction_pct"] == pytest.approx(-20.0)


def test_compare_does_not_report_growth_from_zero_as_no_change():
    """Regression: pct_drop used to return 0.0 from a zero baseline.

    That reported 0 litres -> 40 litres as a 0% change, reading as "no difference" in a
    comparison table where it is the worst outcome in it. It now returns NaN, which is
    visible in output and cannot be mistaken for a result.
    """
    result = compare(_kpis(diesel_litres=0.0), _kpis(diesel_litres=40.0))
    assert result["diesel_reduction_pct"] != 0.0


def test_a_mismatched_diesel_unit_is_rejected_rather_than_silently_wrong():
    """Litres come from the caller's DieselUnit; CO2 comes from the log.

    Nothing structurally ties the two, so pairing them wrongly would report litres and
    emissions that disagree by the 2.5x between a pumpset and a backup genset. Every
    call site currently pairs them correctly, which is exactly why this needs a test:
    the failure would be silent and would land in a published figure.
    """
    factor = DEFAULT_CONFIG.economics.co2_kg_per_litre_diesel
    # A log genuinely produced by a backup genset at 0.30 L/kWh.
    log = simple_log(demand=100.0, diesel=40.0, genset_co2=40.0 * 0.30 * factor)

    # Read with the right unit, it agrees.
    assert compute_kpis(log, DEFAULT_CONFIG, BACKUP_GENSET).diesel_litres == pytest.approx(12.0)

    # Read with the wrong one, it refuses instead of returning a 2.5x-wrong figure.
    with pytest.raises(ValueError, match="diesel unit mismatch"):
        compute_kpis(log, DEFAULT_CONFIG, PUMPSET)


def test_an_unmodelled_co2_column_is_not_treated_as_a_mismatch():
    """Zero CO2 against nonzero diesel is a partial log, not a wrong unit.

    Fixtures that isolate diesel arithmetic legitimately leave emissions unset, and no
    CO2 figure from such a log is publishable, so the guard must not fire on it.
    """
    log = simple_log(demand=100.0, diesel=40.0, genset_co2=0.0)
    assert compute_kpis(log, DEFAULT_CONFIG, PUMPSET).diesel_litres == pytest.approx(30.0)
