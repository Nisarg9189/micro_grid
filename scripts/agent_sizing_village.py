"""Does the bounded search hold up at the scale the brief actually asks about?

`agent_sizing.py` proved the search agrees with the exhaustive sweep at farm scale, but
left the wall-clock verdict genuinely ambiguous: each farm-scale simulation is cheap enough
(~4 s) that the sweep's full-core parallelism can beat the search's round-by-round pruning
even though the search does less total work.

The village is the harder, more honest test. `village_microgrid.py` sweeps the identical
kind of lattice -- 96 configurations here, 8 solar x 2 wind x 6 battery -- over a much
heavier simulation: 100 households, 20 farms, a dairy chilling centre and the water
supply, two feeder groups, 8,760 hours. Per-evaluation cost dominates pool overhead at this
scale, so this is the setting where fewer simulations should translate into less wall time,
not just less certainty.

Nothing about the search itself changes for the village -- `search()` takes the same
`feeders` and `diesel_unit` arguments `sweep()` does, so this script differs from
`agent_sizing.py` only in which profiles, feeders and diesel unit it hands over.

    PYTHONPATH=src .venv/bin/python scripts/agent_sizing_village.py [days] [mpc|rbc]

As with the farm case, a short horizon distorts the comparison (annualised capital against
a partial year of energy cost flatters "install nothing"), so 365 is the number worth
quoting. Agreement with the sweep is still the pass/fail condition; a faster wrong answer
is not a result.
"""

import sys
import time
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402

from gramurja.config import DEFAULT_CONFIG, DieselUnit, Feeder  # noqa: E402
from gramurja.forecast import forecast_weather  # noqa: E402
from gramurja.profiles import generate_profiles  # noqa: E402
from gramurja.search import SearchConfig, capital_of, lattice, search  # noqa: E402
from gramurja.sizing import CapexAssumptions, recommend, sweep  # noqa: E402
from gramurja.village import VillageConfig, generate_village_loads  # noqa: E402
from gramurja.weather import fetch_actual_weather  # noqa: E402

REFERENCE_SOLAR_KWP = 100.0
REFERENCE_WIND_KW = 20.0

SOLAR_OPTIONS = [0, 10, 20, 30, 40, 60, 80, 120]
WIND_OPTIONS = [0, 20]
BATTERY_OPTIONS = [0, 25, 50, 100, 150, 200]

# Same routing rule as village_microgrid.py: agricultural and domestic supplies are
# separately sanctioned and separately tariffed, and neither may serve the other's load.
AGRICULTURAL = Feeder("agricultural", max_import_kw=60.0, import_price_per_kwh=1.50,
                      serves="irrigation")
VILLAGE_FEEDER = Feeder("village", max_import_kw=50.0, import_price_per_kwh=5.00,
                        serves="domestic")
FEEDERS = (AGRICULTURAL, VILLAGE_FEEDER)
VILLAGE_GENSET = DieselUnit(max_kw=50.0, litres_per_kwh=0.30)

MIN_RELIABILITY_PCT = 99.0


def build_profiles(weather, loads, config):
    base = generate_profiles(days=len(loads.total_kw) // 24, config=config, weather=weather)
    return replace(base, load_kw=loads.total_kw, pump_kw=loads.pump_kw)


def describe(result) -> str:
    if result is None:
        return "no configuration met the reliability floor"
    return (f"{result.solar_kwp:g} kWp / {result.wind_kw:g} kW / "
            f"{result.battery_kwh:g} kWh at Rs {result.annual_total_inr:,.0f}/yr")


def main() -> None:
    args = sys.argv[1:]
    days = int(args[0]) if args and args[0].isdigit() else 365
    controller = next((a for a in args if a in ("mpc", "rbc")), "mpc")

    village = VillageConfig()
    loads = generate_village_loads(days=days, config=village)
    weather = fetch_actual_weather("2025-01-01", "2025-12-31")

    reference = replace(
        DEFAULT_CONFIG, solar_capacity_kwp=REFERENCE_SOLAR_KWP,
        wind_capacity_kw=REFERENCE_WIND_KW,
    )
    profiles = build_profiles(weather, loads, reference)
    assumptions = CapexAssumptions()
    weather_forecast = (
        forecast_weather(weather, np.random.default_rng(7)) if controller == "mpc" else None
    )

    grid = lattice(SOLAR_OPTIONS, WIND_OPTIONS, BATTERY_OPTIONS)
    capitals = sorted(capital_of(c, assumptions) for c in grid)

    print(f"\nBOUNDED SEARCH vs EXHAUSTIVE SWEEP -- village, {days} days, {controller.upper()}")
    print("=" * 76)
    print(f"  village          {village.households} households, {village.farms} farms, "
          "dairy, water supply")
    if days < 365:
        print("  WARNING: a short horizon distorts sizing and flatters this comparison,")
        print("  the same way it does at farm scale -- capital is annualised while energy")
        print("  cost only covers the horizon. Use 365 for any number worth quoting.\n")
    print(f"  lattice          {len(grid)} configurations "
          f"({len(SOLAR_OPTIONS)} solar x {len(WIND_OPTIONS)} wind x "
          f"{len(BATTERY_OPTIONS)} battery)")
    print(f"  capital range    Rs {capitals[0]:,.0f} to Rs {capitals[-1]:,.0f} per year")
    print("  each evaluation  8,760 hours, 2 feeder groups, village-scale demand -- far")
    print("                   heavier than the single-farm case, which is the point: this")
    print("                   is where per-simulation cost should dominate pool overhead")

    print(f"\n  running the bounded search ...", flush=True)
    t0 = time.perf_counter()
    found = search(
        profiles, SOLAR_OPTIONS, WIND_OPTIONS, BATTERY_OPTIONS,
        config=reference, assumptions=assumptions, controller=controller,
        weather_forecast=weather_forecast, diesel_unit=VILLAGE_GENSET, feeders=FEEDERS,
        search_config=SearchConfig(reliability_floor_pct=MIN_RELIABILITY_PCT),
    )
    search_seconds = time.perf_counter() - t0

    print(f"\n  running the exhaustive sweep ...", flush=True)
    t0 = time.perf_counter()
    swept = sweep(
        profiles, SOLAR_OPTIONS, WIND_OPTIONS, BATTERY_OPTIONS,
        config=reference, assumptions=assumptions, controller=controller,
        weather_forecast=weather_forecast, diesel_unit=VILLAGE_GENSET, feeders=FEEDERS,
        progress_every=16,
    )
    sweep_seconds = time.perf_counter() - t0
    expected = recommend(swept, MIN_RELIABILITY_PCT)

    print(f"\n{'':<20}{'sweep':>18}{'search':>18}{'difference':>16}")
    print("-" * 76)
    print(f"  {'simulations':<18}{len(swept):>18,}{found.evaluations:>18,}"
          f"{-found.skipped_pct:>15.1f}%")
    print(f"  {'wall clock (s)':<18}{sweep_seconds:>18,.1f}{search_seconds:>18,.1f}"
          f"{(search_seconds - sweep_seconds) / sweep_seconds * 100:>+15.1f}%")
    print(f"  {'pruned unseen':<18}{0:>18,}{len(found.pruned):>18,}")

    print(f"\nWHAT EACH ONE RECOMMENDED")
    print("-" * 76)
    print(f"  sweep    {describe(expected)}")
    print(f"  search   {describe(found.best)}")

    same = (
        expected is None and found.best is None
    ) or (
        expected is not None and found.best is not None
        and (expected.solar_kwp, expected.wind_kw, expected.battery_kwh)
        == (found.best.solar_kwp, found.best.wind_kw, found.best.battery_kwh)
    )

    print(f"\nVERDICT")
    print("-" * 76)
    if not same:
        print("  THE TWO DISAGREE. Exactly as at farm scale, this is a failure of the bound,")
        print("  not a trade-off -- it is meant to be exact regardless of scale. Do not")
        print("  report a speed-up from this run.")
        gap = (found.best.annual_total_inr - expected.annual_total_inr
               if expected and found.best else float("nan"))
        print(f"  cost gap: Rs {gap:,.0f}/yr")
    else:
        print(f"  Same recommendation, reached with {found.skipped_pct:.0f}% fewer")
        print(f"  simulations -- {found.evaluations} against {len(swept)}.")
        if search_seconds < sweep_seconds:
            saved = (sweep_seconds - search_seconds) / sweep_seconds * 100
            print(f"  And this time it was also {saved:.0f}% faster in wall clock: at this")
            print("  scale each simulation costs enough that skipping one is worth more")
            print("  than the parallelism the sweep gets from evaluating all of them at")
            print("  once. That is the result the farm-scale run could not show.")
        else:
            print("  But it still took LONGER in wall clock, even at this scale. That says")
            print("  pool/round overhead dominates on this lattice size regardless of how")
            print("  heavy each simulation is -- worth widening the lattice before")
            print("  concluding the technique can't win on time.")

    print(f"\nCaveat: {days} days, {controller.upper()} controller, one village. The")
    print("agreement check is what matters here; the timings depend on core count.\n")


if __name__ == "__main__":
    main()
