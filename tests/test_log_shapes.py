"""The contract between pymgrid's log and `compute_kpis`, checked against a real log.

The KPI tests hand-build their fixtures, which is the only way to test arithmetic against
known numbers -- but it also means a rename inside pymgrid, or a change to which modules a
run assembles, would leave those tests green while every reported figure quietly became
zero. `_column` returns 0.0 for a column it cannot find; it does not raise.

So these tests run the real thing over three days. They assert structure and invariants,
never specific energy values, because the dispatch heuristic is free to change its mind.
"""

from dataclasses import replace

import pytest

from gramurja.baseline import run_rule_based
from gramurja.config import AGRICULTURAL_FEEDER, PUMPSET
from gramurja.farm import build_microgrid
from gramurja.kpi import _grid_cost, compute_kpis
from gramurja.profiles import generate_profiles

DAYS = 3


@pytest.fixture(scope="module")
def full_farm_log():
    """Solar, wind, battery, genset and both feeders: every module type present.

    Two renewables and two grids mean pymgrid keeps the module-number level, so this is
    the three-level column shape.
    """
    profiles = generate_profiles(days=DAYS)
    return run_rule_based(build_microgrid(profiles))


@pytest.fixture(scope="module")
def irrigation_only_log():
    """The status-quo irrigation half: one feeder, one pumpset, nothing else.

    Every module type is a singleton here, so `drop_singleton_key=True` collapses the
    column keys to `(module, field)` -- the other shape `_column` has to handle.
    """
    profiles = generate_profiles(days=DAYS)
    microgrid = build_microgrid(
        replace(profiles, load_kw=profiles.pump_kw),
        with_solar=False,
        with_wind=False,
        with_battery=False,
        diesel_unit=PUMPSET,
        feeders=(AGRICULTURAL_FEEDER,),
    )
    return run_rule_based(microgrid)


def test_a_full_farm_log_uses_three_level_column_keys(full_farm_log):
    depths = {len(col) if isinstance(col, tuple) else 1 for col in full_farm_log.columns}
    assert depths == {3}


def test_an_all_singleton_log_uses_two_level_column_keys(irrigation_only_log):
    depths = {len(col) if isinstance(col, tuple) else 1 for col in irrigation_only_log.columns}
    assert depths == {2}


def test_every_field_the_kpi_layer_reads_exists_in_a_real_log(full_farm_log):
    """If pymgrid renames one of these, `_column` returns 0.0 rather than raising."""
    expected = {
        ("load", "load_current"),
        ("balancing", "loss_load"),
        ("renewable", "solar_used"),
        ("renewable", "wind_used"),
        ("renewable", "curtailment"),
        ("grid", "grid_import"),
        ("grid", "import_price_current"),
        ("grid", "co2_production"),
        ("genset", "genset_production"),
        ("genset", "co2_production"),
    }
    present = {(col[0], col[-1]) for col in full_farm_log.columns}
    assert expected <= present, expected - present


@pytest.mark.parametrize("log_name", ["full_farm_log", "irrigation_only_log"])
def test_kpis_from_a_real_log_satisfy_the_reporting_invariants(log_name, request):
    log = request.getfixturevalue(log_name)
    kpis = compute_kpis(log, diesel_unit=PUMPSET)

    assert kpis.demand_kwh > 0.0, "the run must have had load, or nothing below means much"
    assert kpis.served_kwh + kpis.unmet_kwh == pytest.approx(kpis.demand_kwh)
    assert 0.0 <= kpis.reliability_pct <= 100.0
    assert 0.0 <= kpis.renewable_fraction_pct <= 100.0
    assert kpis.diesel_litres == pytest.approx(kpis.diesel_kwh * PUMPSET.litres_per_kwh)
    assert kpis.total_cost_inr == pytest.approx(kpis.diesel_cost_inr + kpis.grid_cost_inr)
    assert kpis.grid_cost_inr >= 0.0
    assert kpis.co2_kg >= 0.0


def test_grid_cost_on_a_real_log_matches_a_per_feeder_hand_calculation(full_farm_log):
    """Recompute feeder by feeder from the raw columns, not from `_grid_cost`."""
    log = full_farm_log
    by_hand = 0.0
    for index in (0, 1):
        imports = log[("grid", index, "grid_import")]
        prices = log[("grid", index, "import_price_current")]
        by_hand += float((imports * prices).sum())

    assert _grid_cost(log) == pytest.approx(by_hand)
    assert by_hand > 0.0


def test_a_real_log_has_more_solar_than_wind_at_this_site(full_farm_log):
    """Not an arithmetic invariant -- a sanity check that the two are not swapped.

    A 10 kWp array against a 3 kW turbine at a 0.20 capacity factor; if wind ever came out
    ahead, the fields have been crossed somewhere.
    """
    kpis = compute_kpis(full_farm_log)
    assert kpis.solar_used_kwh > kpis.wind_used_kwh > 0.0


def test_curtailment_is_reported_separately_from_used_output(full_farm_log):
    """Curtailed energy is real and worth reporting; it just is not supply."""
    kpis = compute_kpis(full_farm_log)
    assert kpis.renewable_curtailed_kwh > 0.0, (
        "a 10 kWp array on a 3 kW farm load must curtail something over three days"
    )
    assert kpis.renewable_fraction_pct <= 100.0
