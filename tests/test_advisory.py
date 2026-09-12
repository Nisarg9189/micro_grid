"""Tests for the advisory selection layer.

Two classes of bug are worth guarding against here, and both actually occurred while
writing this module. First, a unit mistake: pymgrid logs battery SoC as a 0..1 fraction,
not kWh, and dividing by capacity a second time turned a real 20% floor into a reported
4%. Second, a design mistake that no type checker would catch: the LP's battery floor is
a hard constraint, so a battery this size touches it on almost every ordinary day, and a
signal built on "did today touch the floor" would have fired every single day -- measured
directly against real weather before it shipped. What actually distinguishes a bad day is
whether the battery recovers by tomorrow morning, which is what is tested instead.

`select_items` is tested as a pure function, independent of any of that: it never touches
a simulation, so its ranking and capping behaviour can be pinned exactly.
"""

from dataclasses import replace

import numpy as np
import pytest

from gramurja.advisory import (
    AdvisoryBriefing,
    AdvisoryConfig,
    AdvisoryItem,
    _diesel_and_battery,
    _feeder_shift,
    _series,
    build_advisory,
    select_items,
)
from gramurja.config import BACKUP_GENSET, DEFAULT_CONFIG, PUMPSET
from gramurja.profiles import HOURS_PER_DAY, Profiles

HOURS_48 = np.zeros(2 * HOURS_PER_DAY)


def make_profiles(**overrides) -> Profiles:
    """A minimal two-day Profiles, so feeder-shift tests do not need generate_profiles."""
    steps = len(HOURS_48)
    base = dict(
        solar_kw=HOURS_48.copy(), wind_kw=HOURS_48.copy(),
        load_kw=np.ones(steps), pump_kw=np.zeros(steps),
        grid_status=np.ones(steps), grid_status_village=np.ones(steps),
        grid_status_scheduled=np.ones(steps),
        grid_carbon_kg_per_kwh=np.full(steps, 0.71),
    )
    base.update(overrides)
    return Profiles(**base)


# --- select_items: pure, no simulation ------------------------------------------------


def item(kind: str, forcing: bool, magnitude: float = 0.0) -> AdvisoryItem:
    return AdvisoryItem(kind=kind, forcing=forcing, magnitude=magnitude, lines=[kind])


def test_no_candidates_selects_nothing():
    assert select_items([], max_items=3) == []


def test_discretionary_items_are_ranked_by_magnitude_descending():
    a, b, c = item("a", False, 5.0), item("b", False, 50.0), item("c", False, 1.0)
    shown = select_items([a, b, c], max_items=3)
    assert [i.kind for i in shown] == ["b", "a", "c"]


def test_the_cap_drops_the_smallest_discretionary_items_first():
    a, b, c = item("a", False, 5.0), item("b", False, 50.0), item("c", False, 1.0)
    shown = select_items([a, b, c], max_items=2)
    assert {i.kind for i in shown} == {"a", "b"}


def test_forcing_items_are_never_dropped_by_the_cap():
    """A plan-invalidating fact is not something a length cap should hide.

    Three forcing items with a cap of one must all still appear -- exactly the same
    principle as a feeder outage always forcing a re-plan in the removed dispatch agent,
    regardless of how full its cooldown was.
    """
    forced = [item(f"f{i}", True) for i in range(3)]
    shown = select_items(forced + [item("discretionary", False, 999.0)], max_items=1)
    assert {i.kind for i in shown} >= {"f0", "f1", "f2"}


def test_discretionary_items_still_fill_remaining_room_after_forcing_ones():
    forced = item("forced", True)
    small = item("small", False, 1.0)
    big = item("big", False, 100.0)
    shown = select_items([forced, small, big], max_items=2)
    assert {i.kind for i in shown} == {"forced", "big"}


def test_display_order_is_stable_regardless_of_input_order():
    a = item("diesel_need", False, 10.0)
    b = item("feeder_shift", True)
    c = item("irrigation_reasoning", False, 5.0)
    shown_1 = select_items([a, b, c], max_items=3)
    shown_2 = select_items([c, a, b], max_items=3)
    assert [i.kind for i in shown_1] == [i.kind for i in shown_2]
    assert shown_1[0].kind == "irrigation_reasoning"


# --- _series: the column-shape robustness that _column in kpi.py also needs -----------


def test_series_reads_the_two_level_key_shape(monkeypatch):
    import pandas as pd
    log = pd.DataFrame({("battery", "soc"): [0.5, 0.6, 0.7]})
    result = _series(log, "battery", "soc")
    assert list(result) == pytest.approx([0.5, 0.6, 0.7])


def test_series_reads_the_three_level_key_shape():
    import pandas as pd
    log = pd.DataFrame({("battery", 0, "soc"): [0.2, 0.3]})
    result = _series(log, "battery", "soc")
    assert list(result) == pytest.approx([0.2, 0.3])


def test_series_returns_zeros_for_a_column_that_does_not_exist():
    import pandas as pd
    log = pd.DataFrame({("battery", "soc"): [0.5, 0.6]})
    result = _series(log, "genset", "genset_production")
    assert list(result) == [0.0, 0.0]


# --- _feeder_shift: a pure function of two days' rosters -------------------------------


def test_no_shift_when_tomorrows_roster_matches_todays():
    scheduled = np.zeros(2 * HOURS_PER_DAY)
    scheduled[6:14] = 1.0
    scheduled[HOURS_PER_DAY + 6:HOURS_PER_DAY + 14] = 1.0
    profiles = make_profiles(grid_status_scheduled=scheduled)
    assert _feeder_shift(profiles, day=0) is None


def test_a_shift_is_forcing_and_names_the_new_block():
    scheduled = np.zeros(2 * HOURS_PER_DAY)
    scheduled[6:14] = 1.0
    scheduled[HOURS_PER_DAY + 14:HOURS_PER_DAY + 22] = 1.0  # rotates to 14:00-22:00
    profiles = make_profiles(grid_status_scheduled=scheduled)
    result = _feeder_shift(profiles, day=0)
    assert result is not None
    assert result.forcing
    assert "14:00-22:00" in result.lines[0]


def test_no_shift_check_past_the_end_of_the_profile():
    """day+1 does not exist -- nothing to compare against, so nothing is raised."""
    profiles = make_profiles()
    assert _feeder_shift(profiles, day=1) is None


# --- _diesel_and_battery: the regression tests for both bugs found while building this -


def _battery_log(soc_by_hour: list[float], genset_kw: list[float] | None = None):
    import pandas as pd
    steps = len(soc_by_hour)
    columns = {("battery", "soc"): soc_by_hour}
    columns[("genset", "genset_production")] = genset_kw or [0.0] * steps
    return pd.DataFrame(columns)


def test_soc_is_read_as_a_fraction_not_divided_by_capacity_again():
    """The regression test for the 4%-instead-of-20% bug.

    pymgrid logs SoC as 0..1 already. A battery recovering to exactly 50% by hour 24
    must be read back as 50%, not 50 / battery_capacity_kwh.
    """
    soc = [0.5] * HOURS_PER_DAY + [0.50] * HOURS_PER_DAY
    log = _battery_log(soc)
    config = replace(DEFAULT_CONFIG, battery_capacity_kwh=5.0)
    items = _diesel_and_battery(log, config, BACKUP_GENSET, AdvisoryConfig())
    # 50% is between the reserve and critical thresholds by default -> a soft mention,
    # and critically, the number printed must say 50, not 10 (50 / 5).
    battery_items = [i for i in items if i.kind.startswith("battery")]
    assert battery_items
    assert "50%" in battery_items[0].lines[0]


def test_touching_the_floor_within_the_day_raises_nothing_on_its_own():
    """The regression test for the every-single-day false alarm.

    A battery that dips to the hard floor mid-day but is back to a healthy level by
    tomorrow morning is behaving exactly as the tariff arbitrage intends. Only the
    RECOVERY hour (index 24) should be read, so a low midday value with a healthy
    recovery must raise nothing.
    """
    soc = [0.2] * 10 + [0.9] * 14 + [0.8] * HOURS_PER_DAY  # floor at hour ~5, fine by hour 24
    log = _battery_log(soc)
    items = _diesel_and_battery(log, DEFAULT_CONFIG, BACKUP_GENSET, AdvisoryConfig())
    assert not [i for i in items if i.kind.startswith("battery")]


def test_a_poor_overnight_recovery_is_forcing():
    config = AdvisoryConfig(battery_recovery_critical_pct=30.0)
    soc = [0.2] * HOURS_PER_DAY + [0.2] * HOURS_PER_DAY  # never recovers
    log = _battery_log(soc)
    items = _diesel_and_battery(log, DEFAULT_CONFIG, BACKUP_GENSET, config)
    critical = [i for i in items if i.kind == "battery_critical"]
    assert critical
    assert critical[0].forcing


def test_a_partial_recovery_is_discretionary():
    config = AdvisoryConfig(battery_recovery_critical_pct=30.0, battery_recovery_reserve_pct=50.0)
    soc = [0.2] * HOURS_PER_DAY + [0.4] * HOURS_PER_DAY  # recovers to 40%: between the two
    log = _battery_log(soc)
    items = _diesel_and_battery(log, DEFAULT_CONFIG, BACKUP_GENSET, config)
    reserve = [i for i in items if i.kind == "battery_reserve"]
    assert reserve
    assert not reserve[0].forcing


def test_a_good_recovery_raises_nothing():
    config = AdvisoryConfig(battery_recovery_critical_pct=30.0, battery_recovery_reserve_pct=50.0)
    soc = [0.2] * HOURS_PER_DAY + [0.9] * HOURS_PER_DAY
    log = _battery_log(soc)
    items = _diesel_and_battery(log, DEFAULT_CONFIG, BACKUP_GENSET, config)
    assert not [i for i in items if i.kind.startswith("battery")]


def test_no_battery_check_at_all_when_the_system_has_none():
    config = replace(DEFAULT_CONFIG, battery_capacity_kwh=0.0)
    soc = [0.2] * (2 * HOURS_PER_DAY)
    log = _battery_log(soc)
    items = _diesel_and_battery(log, config, BACKUP_GENSET, AdvisoryConfig())
    assert not [i for i in items if i.kind.startswith("battery")]


def test_diesel_litres_use_the_unit_passed_in_not_a_hardcoded_rate():
    """The same class of bug compute_kpis now guards against for the same reason."""
    genset_kw = [1.0] * 4 + [0.0] * (2 * HOURS_PER_DAY - 4)  # 4 kWh of diesel today
    log = _battery_log([1.0] * (2 * HOURS_PER_DAY), genset_kw=genset_kw)

    pumpset_items = _diesel_and_battery(log, DEFAULT_CONFIG, PUMPSET, AdvisoryConfig())
    genset_items = _diesel_and_battery(log, DEFAULT_CONFIG, BACKUP_GENSET, AdvisoryConfig())

    pumpset_litres = [i for i in pumpset_items if i.kind == "diesel_need"][0].magnitude
    genset_litres = [i for i in genset_items if i.kind == "diesel_need"][0].magnitude
    assert pumpset_litres == pytest.approx(4.0 * 0.75)
    assert genset_litres == pytest.approx(4.0 * 0.30)


def test_diesel_below_threshold_raises_nothing():
    genset_kw = [0.01] * (2 * HOURS_PER_DAY)
    log = _battery_log([1.0] * (2 * HOURS_PER_DAY), genset_kw=genset_kw)
    items = _diesel_and_battery(log, DEFAULT_CONFIG, BACKUP_GENSET, AdvisoryConfig())
    assert not [i for i in items if i.kind == "diesel_need"]


# --- AdvisoryBriefing -------------------------------------------------------------------


def test_lines_include_the_header_even_with_no_items():
    briefing = AdvisoryBriefing(day=0, header="Run the pump at 09:00.", items=[])
    assert briefing.lines == ["Run the pump at 09:00.", "No other changes needed today."]


def test_lines_include_the_header_and_every_shown_item():
    shown = [item("diesel_need", False, 1.0)]
    briefing = AdvisoryBriefing(day=0, header="H", items=shown, considered=shown)
    assert briefing.lines == ["H", "diesel_need"]


def test_dropped_is_the_complement_of_items_within_considered():
    a, b = item("a", True), item("b", False, 1.0)
    briefing = AdvisoryBriefing(day=0, header="H", items=[a], considered=[a, b])
    assert briefing.dropped == [b]


# --- end to end, on real (but tiny) weather --------------------------------------------


def test_build_advisory_runs_end_to_end(clear_day_weather):
    from gramurja.profiles import generate_profiles

    config = replace(DEFAULT_CONFIG, solar_capacity_kwp=3.0, wind_capacity_kw=0.0,
                      battery_capacity_kwh=5.0, battery_max_charge_kw=1.25,
                      battery_max_discharge_kw=1.25)
    profiles = generate_profiles(days=2, config=config, weather=clear_day_weather)
    briefing = build_advisory(profiles, day=0, config=config)

    assert briefing.header.startswith("Run the irrigation pump")
    assert briefing.lines[0] == briefing.header
    # Every considered item, shown or not, is accounted for in the audit trail.
    assert set(id(i) for i in briefing.items) <= set(id(i) for i in briefing.considered)
