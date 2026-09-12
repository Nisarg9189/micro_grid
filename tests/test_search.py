"""Tests for the branch-and-bound sizing search.

The whole value of this module is that it returns the *same* answer as the exhaustive
sweep while simulating fewer candidates. A search that ran faster and sometimes picked a
different system would be worse than the sweep it replaces, so the central test here runs
both over an identical small lattice and asserts they agree -- not that the search merely
found something plausible.

The rest guard the two ways this could silently go wrong: the bound could be unsound (and
prune the optimum), or the ordering could quietly drop candidates from the lattice.
"""

import numpy as np
import pytest

from gramurja.config import DEFAULT_CONFIG
from gramurja.profiles import generate_profiles
from gramurja.search import (
    Candidate,
    SearchConfig,
    SearchResult,
    capital_of,
    lattice,
    opening_order,
    scaled_total,
    search,
)
from gramurja.sizing import (
    CapexAssumptions,
    SizingResult,
    annual_capital_cost,
    recommend,
    sweep,
)

ASSUMPTIONS = CapexAssumptions()

# Deliberately tiny: every candidate is a real simulation, so the lattice is kept small
# and the horizon short. The claim under test is agreement with the sweep, which does not
# need a big search space to be meaningful.
SOLAR = [0.0, 2.0, 4.0]
WIND = [0.0]
BATTERY = [0.0, 5.0]


@pytest.fixture
def short_profiles(clear_day_weather):
    return generate_profiles(days=2, config=DEFAULT_CONFIG, weather=clear_day_weather)


# --- the bound ------------------------------------------------------------------------


def test_capital_is_the_closed_form_capital():
    c = Candidate(3.0, 0.0, 5.0)
    assert capital_of(c, ASSUMPTIONS) == annual_capital_cost(3.0, 0.0, 5.0, ASSUMPTIONS)


def test_capital_needs_no_simulation():
    """The bound has to be free, or computing it for the whole lattice is pointless."""
    assert capital_of(Candidate(12.0, 3.0, 30.0), ASSUMPTIONS) > 0


@pytest.mark.parametrize(
    "candidate",
    [Candidate(0, 0, 0), Candidate(2, 0, 5), Candidate(12, 3, 30), Candidate(1, 0, 30)],
)
def test_capital_is_a_lower_bound_on_total(candidate):
    """Soundness. Everything rests on this.

    total = capital + energy + carbon, and energy and carbon are both non-negative, so a
    candidate whose capital alone exceeds the incumbent total cannot beat it. If this ever
    stopped holding -- a negative energy cost from an export tariff, say -- the pruning
    would start discarding the true optimum and the search would be silently wrong.
    """
    capital = capital_of(candidate, ASSUMPTIONS)
    kpis = type("K", (), {"reliability_pct": 100.0})()
    for energy, carbon in [(0.0, 0.0), (1_000.0, 0.0), (0.0, 500.0), (9_000.0, 900.0)]:
        result = SizingResult(
            candidate.solar_kwp, candidate.wind_kw, candidate.battery_kwh,
            kpis, capital, energy, carbon,
        )
        assert result.annual_total_inr >= capital


def test_capital_rises_with_every_capacity():
    """Monotonicity is what makes a whole region prunable rather than one point."""
    base = capital_of(Candidate(2, 0, 5), ASSUMPTIONS)
    assert capital_of(Candidate(3, 0, 5), ASSUMPTIONS) > base
    assert capital_of(Candidate(2, 1, 5), ASSUMPTIONS) > base
    assert capital_of(Candidate(2, 0, 10), ASSUMPTIONS) > base


# --- the lattice and the ordering -----------------------------------------------------


def test_the_lattice_is_the_full_product():
    assert len(lattice(SOLAR, WIND, BATTERY)) == len(SOLAR) * len(WIND) * len(BATTERY)


def test_ordering_keeps_every_candidate_exactly_once():
    """A bug here would drop candidates silently, which reads as a faster search.

    The opening probes are spliced in front of the capital-ordered list, so a mistake in
    the de-duplication would either lose candidates or evaluate some twice.
    """
    full = lattice([0, 1, 2, 3, 4, 5, 6, 8, 10, 12], [0, 3], [0, 5, 10, 15, 20, 30])
    ordered = opening_order(full, ASSUMPTIONS, probes=6)
    assert len(ordered) == len(full)
    assert set(ordered) == set(full)
    assert len(set(ordered)) == len(ordered)


def test_ordering_without_probes_is_purely_ascending_capital():
    full = lattice(SOLAR, WIND, BATTERY)
    ordered = opening_order(full, ASSUMPTIONS, probes=0)
    capitals = [capital_of(c, ASSUMPTIONS) for c in ordered]
    assert capitals == sorted(capitals)


def test_probes_do_not_all_come_from_the_cheap_end():
    """Their whole purpose is a usable incumbent, which the cheapest systems never give.

    The lowest-capital configurations buy nothing and burn diesel, so they set a poor
    incumbent and leave the bound loose.
    """
    full = lattice([0, 1, 2, 3, 4, 5, 6, 8, 10, 12], [0, 3], [0, 5, 10, 15, 20, 30])
    probes = opening_order(full, ASSUMPTIONS, probes=6)[:6]
    cheapest_six = sorted(full, key=lambda c: capital_of(c, ASSUMPTIONS))[:6]
    assert set(probes) != set(cheapest_six)
    assert all(capital_of(c, ASSUMPTIONS) > 0 for c in probes)


def test_a_lattice_smaller_than_the_probe_count_is_handled():
    small = lattice([0.0, 2.0], [0.0], [0.0])
    assert len(opening_order(small, ASSUMPTIONS, probes=6)) == 2


# --- agreement with the sweep, which is the point -------------------------------------


def test_the_search_finds_what_the_sweep_finds(short_profiles):
    """The central claim: same lattice, same recommendation, fewer simulations.

    Run against the rule-based controller, which is far cheaper per candidate than the
    optimiser and exercises the same search machinery.
    """
    swept = sweep(
        short_profiles, SOLAR, WIND, BATTERY,
        config=DEFAULT_CONFIG, assumptions=ASSUMPTIONS,
        controller="rbc", progress_every=0,
    )
    expected = recommend(swept, 99.0)

    found = search(
        short_profiles, SOLAR, WIND, BATTERY,
        config=DEFAULT_CONFIG, assumptions=ASSUMPTIONS, controller="rbc",
        search_config=SearchConfig(batch=4, opening_probes=2), progress=False,
    )

    if expected is None:
        assert found.best is None
        return

    assert found.best is not None
    assert (found.best.solar_kwp, found.best.wind_kw, found.best.battery_kwh) == (
        expected.solar_kwp, expected.wind_kw, expected.battery_kwh
    )
    assert found.best.annual_total_inr == pytest.approx(expected.annual_total_inr)


def test_the_search_never_evaluates_more_than_the_lattice(short_profiles):
    found = search(
        short_profiles, SOLAR, WIND, BATTERY,
        config=DEFAULT_CONFIG, assumptions=ASSUMPTIONS, controller="rbc",
        search_config=SearchConfig(batch=4, opening_probes=2), progress=False,
    )
    assert found.evaluations <= found.lattice_size
    assert found.evaluations + len(found.pruned) == found.lattice_size


def test_nothing_pruned_could_have_won(short_profiles):
    """Every skipped candidate must have capital at or above the winning total.

    This is the property that would break first if the bound were applied with the wrong
    comparison or against a stale incumbent.
    """
    found = search(
        short_profiles, SOLAR, WIND, BATTERY,
        config=DEFAULT_CONFIG, assumptions=ASSUMPTIONS, controller="rbc",
        search_config=SearchConfig(batch=2, opening_probes=2), progress=False,
    )
    if found.best is None:
        assert not found.pruned
        return
    for candidate in found.pruned:
        assert capital_of(candidate, ASSUMPTIONS) >= found.best.annual_total_inr


# --- the result object ----------------------------------------------------------------


def test_feasible_applies_the_reliability_floor():
    """It used to filter on `>= 0`, which admits everything."""
    def result(reliability, total):
        kpis = type("K", (), {"reliability_pct": reliability})()
        return SizingResult(1.0, 0.0, 0.0, kpis, total, 0.0, 0.0)

    found = SearchResult(
        best=None,
        evaluated=[result(100.0, 10.0), result(50.0, 1.0), result(99.5, 20.0)],
        lattice_size=3,
        reliability_floor_pct=99.0,
    )
    totals = [r.annual_total_inr for r in found.feasible()]
    assert totals == [10.0, 20.0]


def test_skipped_counts_what_was_never_simulated():
    found = SearchResult(best=None, evaluated=[], lattice_size=120)
    assert found.skipped == 120
    assert found.skipped_pct == pytest.approx(100.0)


def test_an_empty_lattice_does_not_divide_by_zero():
    assert SearchResult(best=None, lattice_size=0).skipped_pct == 0.0


# --- horizon_scale: the fix that lets the API call this over a horizon shorter than a
# year and still get a sound recommendation, not "install nothing" ------------------


def _result(capital: float, energy: float, carbon: float = 0.0) -> SizingResult:
    kpis = type("K", (), {"reliability_pct": 100.0})()
    return SizingResult(1.0, 0.0, 0.0, kpis, capital, energy, carbon)


def test_scaled_total_matches_annual_total_at_a_full_year():
    """horizon_scale=1.0 must reproduce the plain annual_total_inr exactly.

    Every existing caller (the CLI scripts, the benchmark, the tests above) runs a full
    year and relies on this being a no-op -- confirmed structurally by the fact none of
    those tests needed to change when horizon_scale was added.
    """
    r = _result(capital=1000.0, energy=500.0, carbon=50.0)
    assert scaled_total(r, 1.0) == pytest.approx(r.annual_total_inr)


def test_scaled_total_shrinks_energy_for_a_short_horizon():
    """The actual bug this exists to fix: at 30/365 scale, a 30-day energy cost of 500
    should count as ~41, not the full 500 -- otherwise a cheap-capital, diesel-heavy
    system looks artificially competitive against one with real solar and battery."""
    r = _result(capital=1000.0, energy=500.0, carbon=0.0)
    scale = 30.0 / 365.0
    assert scaled_total(r, scale) == pytest.approx(1000.0 + 500.0 * scale)


def test_capital_alone_still_bounds_the_scaled_total():
    """The bound's soundness proof only used energy, carbon >= 0 -- unaffected by
    multiplying them by a non-negative scale. Checked directly rather than trusted."""
    r = _result(capital=1000.0, energy=500.0, carbon=50.0)
    for scale in (0.0, 0.1, 1.0, 5.0):
        assert r.annual_capital_inr <= scaled_total(r, scale)


def test_a_scaled_search_prunes_soundly_against_its_own_scaled_incumbent(short_profiles):
    """The property that would break first if horizon_scale leaked into the bound but
    not the incumbent comparison, or vice versa: every pruned candidate's raw capital
    must still be at or above the winning candidate's *scaled* total -- not its unscaled
    one, which pruning never sees or compares against.
    """
    scale = 365.0 / (len(short_profiles) // 24)  # the fixture's own short horizon
    found = search(
        short_profiles, SOLAR, WIND, BATTERY,
        config=DEFAULT_CONFIG, assumptions=ASSUMPTIONS, controller="rbc",
        search_config=SearchConfig(batch=4, opening_probes=2, horizon_scale=scale),
        progress=False,
    )
    assert found.best is not None
    assert found.horizon_scale == pytest.approx(scale)
    winning_total = scaled_total(found.best, scale)
    for candidate in found.pruned:
        assert capital_of(candidate, ASSUMPTIONS) >= winning_total


def test_feasible_ranks_by_the_scaled_total_not_the_unscaled_one():
    """A regression test in the shape of the bug: with a small enough scale, a
    cheap-capital/expensive-energy candidate must outrank an expensive-capital/
    cheap-energy one, reversing their order under the unscaled total.
    """
    cheap_capital_pricey_energy = _result(capital=100.0, energy=1000.0)
    pricier_capital_cheap_energy = _result(capital=500.0, energy=100.0)

    found = SearchResult(
        best=None,
        evaluated=[cheap_capital_pricey_energy, pricier_capital_cheap_energy],
        lattice_size=2,
        horizon_scale=0.1,
    )
    ranked = found.feasible()
    assert ranked[0] is cheap_capital_pricey_energy  # 100 + 1000*0.1 = 200
    assert ranked[1] is pricier_capital_cheap_energy  # 500 + 100*0.1 = 510
