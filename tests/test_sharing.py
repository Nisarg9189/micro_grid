"""Conservation properties of the village-cluster LP.

`sharing.py` is the newest and least-exercised code in the project, and it answers the
question the whole cluster model exists for: does letting a village share surplus pay, and
who gains. An LP will happily return a confident optimum for a model whose accounting is
wrong, so the tests here assert only what must hold whatever dispatch the solver picks:

    per-hour balance   supply into every meter equals load plus what was stored or exported
    line conservation  energy onto the village line, less distribution loss, is the energy
                       that came off it
    reporting          the totals and per-kind breakdowns add up to the same energy

The cases are deliberately tiny -- two days, two farms, one household block -- because the
default 20-farm, 60-day cluster takes about a minute. The properties under test are
structural, so they do not need scale to show up.
"""

import numpy as np
import pytest

from gramurja.config import DEFAULT_CONFIG
from gramurja.sharing import (
    PUMPSET,
    ClusterLP,
    ClusterResult,
    Participant,
    VillageCluster,
    build_participants,
    participant_loads,
    run_cluster,
)
from gramurja.weather import pv_output_kw

DAYS = 2
STEPS = DAYS * 24
LINE_KW = 5.0

# A short horizon keeps each hour's LP small. The receding-horizon logic is unchanged by
# its length, and the conservation properties hold per hour regardless.
HORIZON = 12


def _cluster(**overrides) -> VillageCluster:
    """A three-participant-kind village: two farms, one household block, dairy, water."""
    base = dict(
        farms=2,
        households=20,
        household_blocks=1,
        horizon=HORIZON,
        line_kw=LINE_KW,
    )
    base.update(overrides)
    return VillageCluster(**base)


def _feeder_status() -> tuple[np.ndarray, np.ndarray]:
    """Rationed agricultural supply, and a village feeder that fails over the evening peak.

    The village outage is what creates unserved load: households own no generation and no
    backup, so when the domestic feeder is down they can only be rescued over the line.
    """
    hour = np.arange(STEPS) % 24
    agricultural = np.where((hour >= 6) & (hour < 14), 1.0, 0.0)
    village = np.where((hour >= 18) & (hour <= 22), 0.0, 1.0)
    return agricultural, village


@pytest.fixture(scope="module")
def scenario(clear_day_weather):
    """Loads and feeder availability, shared by the with-line and without-line runs."""
    cluster = _cluster()
    people = build_participants(cluster)
    loads = participant_loads(DAYS, cluster, people)
    agricultural, village = _feeder_status()
    return clear_day_weather, loads, people, agricultural, village


@pytest.fixture(scope="module")
def shared(scenario):
    weather, loads, people, agricultural, village = scenario
    return run_cluster(weather, loads, people, agricultural, village, _cluster())


@pytest.fixture(scope="module")
def isolated(scenario):
    """The same hardware with no village line: every participant stands alone."""
    weather, loads, people, agricultural, village = scenario
    return run_cluster(weather, loads, people, agricultural, village, _cluster(line_kw=0.0))


def _solar_matrix(weather, people) -> np.ndarray:
    solar = np.zeros((len(people), STEPS))
    for row, person in enumerate(people):
        if person.solar_kwp > 0:
            solar[row] = pv_output_kw(weather, person.solar_kwp)[:STEPS]
    return solar


def _solve_one_window(scenario, cluster, solver=None) -> dict:
    """Solve a single planning window and return the full (participants, horizon) plan.

    `ClusterLP.step` only hands back the first hour, since that is all `run_cluster`
    applies, but the constraints the tests below are about hold across the whole window.
    """
    weather, loads, people, agricultural, village = scenario
    lp = ClusterLP(cluster, people, DEFAULT_CONFIG.economics)
    battery = np.array([p.battery_kwh for p in people], dtype=float)

    lp.load.value = loads[:, :cluster.horizon]
    lp.solar.value = _solar_matrix(weather, people)[:, :cluster.horizon]
    lp.ag_up.value = agricultural[:cluster.horizon]
    lp.village_up.value = village[:cluster.horizon]
    lp.soc0.value = battery * 0.5
    lp.problem.solve(**({"solver": solver} if solver is not None else {}))

    return {
        "objective": float(lp.problem.value),
        "battery": battery,
        "ag": np.asarray(lp.ag.value),
        "to_line": np.asarray(lp.to_line.value),
        "from_line": np.asarray(lp.from_line.value),
        "soc": np.asarray(lp.soc.value),
    }


@pytest.fixture(scope="module")
def plan(scenario):
    """One planning window, solved once and inspected by several tests."""
    return _solve_one_window(scenario, _cluster())


# --------------------------------------------------------------------------------------
# The village roster
# --------------------------------------------------------------------------------------

def test_participants_cover_every_kind_in_the_cluster():
    people = build_participants(_cluster())
    kinds = [p.kind for p in people]
    assert kinds == ["farm", "farm", "household", "dairy", "water"]


def test_households_own_no_generation_and_no_backup():
    """This is the premise of the whole model, not an incidental parameter choice."""
    households = [p for p in build_participants(_cluster()) if p.kind == "household"]
    assert households
    for block in households:
        assert block.solar_kwp == 0.0
        assert block.battery_kwh == 0.0
        assert block.genset_kw == 0.0
        # And may never draw agricultural-tariff power.
        assert block.ag_kw == 0.0
        assert block.village_kw > 0.0


def test_only_farms_hold_an_agricultural_connection():
    for person in build_participants(_cluster()):
        if person.kind != "farm":
            assert person.ag_kw == 0.0


# --------------------------------------------------------------------------------------
# Energy balance
# --------------------------------------------------------------------------------------

def test_demand_equals_served_plus_unmet(shared):
    served = shared.demand_kwh - shared.unmet_kwh
    assert shared.demand_kwh == pytest.approx(served + shared.unmet_kwh, abs=1e-6)
    assert 0.0 <= shared.unmet_kwh <= shared.demand_kwh


def test_every_hour_balances_supply_against_load(shared):
    """The identity the LP enforces per participant, checked on the reported series.

    `from_line` is not reported, but the line constraint fixes it at
    `to_line * transfer_efficiency`, so substituting it here also tests that the reported
    `transferred` series really is the quantity the line constraint was written about.
    """
    efficiency = _cluster().transfer_efficiency
    h = shared.hourly

    supply = (h["solar"] + h["ag"] + h["village"] + h["diesel"] + h["discharge"]
              + h["transferred"] * efficiency + h["unmet"])
    sink = h["demand"] + h["charge"] + h["transferred"]

    assert np.abs(supply - sink).max() == pytest.approx(0.0, abs=1e-6)


def test_hourly_series_sum_to_the_reported_totals(shared):
    h = shared.hourly
    assert h["demand"].sum() == pytest.approx(shared.demand_kwh, abs=1e-6)
    assert h["unmet"].sum() == pytest.approx(shared.unmet_kwh, abs=1e-6)
    assert h["solar"].sum() == pytest.approx(shared.solar_used_kwh, abs=1e-6)
    assert h["ag"].sum() == pytest.approx(shared.ag_kwh, abs=1e-6)
    assert h["village"].sum() == pytest.approx(shared.village_kwh, abs=1e-6)
    assert h["diesel"].sum() == pytest.approx(shared.diesel_kwh, abs=1e-6)
    assert h["transferred"].sum() == pytest.approx(shared.transferred_kwh, abs=1e-6)


def test_solar_is_either_used_or_curtailed(scenario, shared):
    """No third destination exists, so the two must account for the whole resource."""
    weather, loads, people, _, _ = scenario
    available = sum(
        float(pv_output_kw(weather, p.solar_kwp)[:STEPS].sum())
        for p in people if p.solar_kwp > 0
    )
    assert available > 0.0
    assert shared.solar_used_kwh + shared.curtailed_kwh == pytest.approx(available, abs=1e-6)
    assert shared.curtailed_kwh >= -1e-9


def test_no_participant_draws_from_a_feeder_it_is_not_entitled_to(scenario, plan):
    """Households must never appear on the agricultural tariff, at any hour."""
    people = scenario[2]
    for row, person in enumerate(people):
        if person.ag_kw == 0.0:
            assert plan["ag"][row].max() == pytest.approx(0.0, abs=1e-6), person.name


# --------------------------------------------------------------------------------------
# The village line
# --------------------------------------------------------------------------------------

def test_energy_off_the_line_is_energy_on_it_less_distribution_loss(shared):
    """Sharing must cost something, or the shared case wins by construction.

    `exported_by_kind` and `imported_by_kind` are rounded to 0.1 kWh per kind and skip
    flows under 1e-6, so the tolerance here is set by the reporting, not by the LP.
    """
    efficiency = _cluster().transfer_efficiency
    exported = sum(shared.exported_by_kind.values())
    imported = sum(shared.imported_by_kind.values())

    assert exported == pytest.approx(shared.transferred_kwh, abs=0.5)
    assert imported == pytest.approx(shared.transferred_kwh * efficiency, abs=0.5)
    assert imported < exported  # the loss is real, not a rounding artefact


def test_a_line_of_zero_capacity_transfers_nothing(isolated):
    assert isolated.transferred_kwh == pytest.approx(0.0, abs=1e-6)
    assert isolated.hourly["transferred"].max() == pytest.approx(0.0, abs=1e-6)
    assert sum(isolated.exported_by_kind.values()) == pytest.approx(0.0, abs=1e-6)
    assert sum(isolated.imported_by_kind.values()) == pytest.approx(0.0, abs=1e-6)


def test_no_participant_exceeds_its_line_capacity(plan):
    """`line_kw` caps each connection, so the aggregate line carries at most n x line_kw."""
    assert plan["to_line"].max() <= LINE_KW + 1e-6
    assert plan["from_line"].max() <= LINE_KW + 1e-6


def test_the_line_conserves_energy_hour_by_hour(plan):
    efficiency = _cluster().transfer_efficiency
    onto = plan["to_line"].sum(axis=0) * efficiency
    off = plan["from_line"].sum(axis=0)
    assert np.abs(onto - off).max() == pytest.approx(0.0, abs=1e-6)


def test_sharing_rescues_load_that_the_isolated_village_sheds(shared, isolated):
    """The claim the model exists to support, on the same loads and the same weather."""
    assert isolated.unmet_kwh > shared.unmet_kwh
    assert isolated.reliability_pct < shared.reliability_pct


# --------------------------------------------------------------------------------------
# Reliability
# --------------------------------------------------------------------------------------

def test_reliability_is_a_bounded_energy_share(shared, isolated):
    for result in (shared, isolated):
        expected = 100.0 * (result.demand_kwh - result.unmet_kwh) / result.demand_kwh
        assert result.reliability_pct == pytest.approx(expected)
        assert 0.0 <= result.reliability_pct <= 100.0


def test_demand_by_kind_sums_to_total_demand(shared):
    """Rounded to 0.1 kWh per kind, so the tolerance scales with the number of kinds."""
    by_kind = sum(shared.demand_by_kind.values())
    assert by_kind == pytest.approx(shared.demand_kwh, abs=0.05 * len(shared.demand_by_kind))
    assert set(shared.demand_by_kind) == {"farm", "household", "dairy", "water"}


def test_unmet_by_kind_sums_to_total_unmet(shared):
    by_kind = sum(shared.unmet_by_kind.values())
    assert shared.unmet_kwh > 0.0, "the scenario must shed something for this to mean anything"
    assert by_kind == pytest.approx(shared.unmet_kwh, abs=0.05 * max(1, len(shared.unmet_by_kind)))


# --------------------------------------------------------------------------------------
# Diesel and cost
# --------------------------------------------------------------------------------------

def test_diesel_litres_use_the_pumpset_fuel_rate(shared):
    """The cluster models the status quo, where farm diesel is a direct-coupled pumpset.

    `ClusterResult.diesel_litres` and `diesel_by_kind` both hard-code 0.75 rather than
    reading `PUMPSET.litres_per_kwh`, so this pins the three to the same number.
    """
    assert PUMPSET.litres_per_kwh == pytest.approx(0.75)
    assert shared.diesel_kwh > 0.0
    assert shared.diesel_litres == pytest.approx(shared.diesel_kwh * PUMPSET.litres_per_kwh)
    assert sum(shared.diesel_by_kind.values()) == pytest.approx(shared.diesel_litres, abs=0.1)


def test_only_participants_with_a_genset_burn_diesel(shared):
    assert set(shared.diesel_by_kind) <= {"farm"}


def test_energy_cost_prices_each_source_at_its_own_rate(shared):
    cluster = _cluster()
    diesel_rate = PUMPSET.litres_per_kwh * DEFAULT_CONFIG.economics.diesel_price_per_litre
    expected = (shared.ag_kwh * cluster.ag_tariff
                + shared.village_kwh * cluster.village_tariff
                + shared.diesel_kwh * diesel_rate)
    assert shared.energy_cost_inr == pytest.approx(expected)
    # The subsidised agricultural feeder is the cheap one; diesel is ~20x the village rate.
    assert cluster.ag_tariff < cluster.village_tariff < diesel_rate


def test_sharing_does_not_cost_more_than_standing_alone(shared, isolated):
    """Unserved load is priced in the objective at VOLL, so compare like with like."""
    voll = _cluster().voll_inr_per_kwh
    shared_total = shared.energy_cost_inr + voll * shared.unmet_kwh
    isolated_total = isolated.energy_cost_inr + voll * isolated.unmet_kwh
    assert shared_total <= isolated_total + 1e-6


# --------------------------------------------------------------------------------------
# Degenerate inputs and reporting hazards
# --------------------------------------------------------------------------------------

def _empty_result(**overrides) -> ClusterResult:
    fields = dict(line_kw=0.0, demand_kwh=0.0, unmet_kwh=0.0, solar_used_kwh=0.0,
                  curtailed_kwh=0.0, ag_kwh=0.0, village_kwh=0.0, diesel_kwh=0.0,
                  transferred_kwh=0.0, energy_cost_inr=0.0)
    fields.update(overrides)
    return ClusterResult(**fields)


def test_zero_demand_reports_zero_reliability_without_raising():
    """Regression: ClusterResult.reliability_pct used to divide by demand_kwh unguarded.

    An empty or all-zero load window is reachable from a sizing sweep or a scenario
    filter, and used to raise ZeroDivisionError. kpi.py guards the identical expression
    in four places; this one now does too.
    """
    assert _empty_result().reliability_pct == 0.0


@pytest.mark.xfail(
    reason="A household block, the dairy and the water pump own no solar, no battery and "
           "no genset, yet over one 12-hour window the LP has them pushing 0.44, 0.43 and "
           "0.10 kWh respectively onto the village line. They can only be re-exporting "
           "energy they imported or drew from a feeder, which is a 3% round-trip loss for "
           "nothing. It is free to the objective because it happens in hours when the "
           "surplus solar it displaces would have been curtailed anyway -- so "
           "exported_by_kind attributes exports to participants with nothing to export.",
    strict=True,
)
def test_a_participant_with_no_generation_cannot_export(scenario, plan):
    people = scenario[2]
    passive = [row for row, p in enumerate(people)
               if p.solar_kwp == 0 and p.battery_kwh == 0 and p.genset_kw == 0]
    assert passive

    for row in passive:
        # Well above the 1e-6 threshold at which the reported breakdown keeps a flow.
        assert plan["to_line"][row].sum() == pytest.approx(0.0, abs=1e-3), people[row].name


@pytest.mark.xfail(
    reason="The per-participant line flows are a degenerate direction of this LP: when a "
           "farm's surplus solar would otherwise be curtailed, moving it onto and off the "
           "line is free, so many different assignments reach the same optimal cost. "
           "CLARABEL and ECOS agree on the objective to six significant figures "
           "(134.087586) yet disagree on the per-participant exports by up to 13% "
           "relative (0.48 vs 0.44 kWh for the household block, 0.085 vs 0.096 kWh for "
           "the water pump). That makes exported_by_kind/imported_by_kind -- the fields "
           "that answer 'who benefits from sharing' -- solver artefacts, not results.",
    strict=True,
)
def test_the_who_benefits_attribution_is_independent_of_the_solver(scenario):
    import cvxpy as cp

    cluster = _cluster()
    clarabel = _solve_one_window(scenario, cluster, solver=cp.CLARABEL)
    ecos = _solve_one_window(scenario, cluster, solver=cp.ECOS)

    # Same optimum...
    assert clarabel["objective"] == pytest.approx(ecos["objective"], rel=1e-6)
    # ...so the attribution behind it had better be the same too.
    assert clarabel["to_line"].sum(axis=1) == pytest.approx(
        ecos["to_line"].sum(axis=1), abs=1e-3
    )


def test_a_participant_never_imports_and_exports_in_the_same_hour(plan):
    """Doing both at once is always wasteful, so a genuine optimum never does it."""
    simultaneous = np.minimum(plan["to_line"], plan["from_line"])
    assert simultaneous.max() == pytest.approx(0.0, abs=1e-4)


def test_a_participant_with_a_battery_respects_its_state_of_charge_floor(plan):
    """20% floor, so the LP may not empty a farm battery to dodge a diesel hour."""
    battery, soc = plan["battery"], plan["soc"]
    for row in range(len(battery)):
        assert soc[row].min() >= battery[row] * 0.20 - 1e-6
        assert soc[row].max() <= battery[row] + 1e-6


def test_a_cluster_with_no_line_and_no_outage_still_solves(clear_day_weather):
    """A trivially easy hour must not be a special case for the solver."""
    cluster = _cluster(line_kw=0.0, horizon=4)
    people = [Participant("one farm", "farm", solar_kwp=3.0, battery_kwh=5.0,
                          genset_kw=6.0, ag_kw=10.0, village_kw=2.0)]
    loads = np.full((1, 4), 1.0)
    result = run_cluster(clear_day_weather, loads, people,
                         np.ones(4), np.ones(4), cluster)

    assert result.demand_kwh == pytest.approx(4.0)
    assert result.unmet_kwh == pytest.approx(0.0, abs=1e-6)
    assert result.reliability_pct == pytest.approx(100.0)
    assert result.transferred_kwh == pytest.approx(0.0, abs=1e-6)
