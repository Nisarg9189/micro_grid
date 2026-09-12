"""Does the bounded search find the same system as the exhaustive sweep, for less work?

`optimize_sizing.py` simulates every configuration on the lattice. Most of them cannot
win: annualised capital alone is a lower bound on total cost, so any candidate whose
capital already exceeds the best feasible total found so far is provably beaten without
being simulated at all.

This runs both searches over the identical lattice and compares them on the only two
things that matter: whether they agree, and how much work each did.

    PYTHONPATH=src .venv/bin/python scripts/agent_sizing.py [days] [mpc|rbc]

The canonical comparison is the full year under the optimiser, which is what the project
actually recommends from -- but it takes upwards of half an hour, so a shorter horizon is
accepted for a quick check. Agreement is the pass/fail condition either way: a search that
returns a different system is worse than the sweep it replaces, however fast it ran.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402

from gramurja.config import DEFAULT_CONFIG  # noqa: E402
from gramurja.forecast import forecast_weather  # noqa: E402
from gramurja.profiles import generate_profiles  # noqa: E402
from gramurja.search import SearchConfig, capital_of, lattice, search  # noqa: E402
from gramurja.sizing import CapexAssumptions, recommend, sweep  # noqa: E402
from gramurja.weather import fetch_actual_weather  # noqa: E402

SOLAR_OPTIONS = [0, 1, 2, 3, 4, 5, 6, 8, 10, 12]
WIND_OPTIONS = [0, 3]
BATTERY_OPTIONS = [0, 5, 10, 15, 20, 30]

MIN_RELIABILITY_PCT = 99.0


def describe(result) -> str:
    if result is None:
        return "no configuration met the reliability floor"
    return (f"{result.solar_kwp:g} kWp / {result.wind_kw:g} kW / "
            f"{result.battery_kwh:g} kWh at Rs {result.annual_total_inr:,.0f}/yr")


def main() -> None:
    args = [a for a in sys.argv[1:]]
    days = int(args[0]) if args and args[0].isdigit() else 365
    controller = next((a for a in args if a in ("mpc", "rbc")), "mpc")

    weather = fetch_actual_weather("2025-01-01", "2025-12-31")
    profiles = generate_profiles(days=days, config=DEFAULT_CONFIG, weather=weather)
    assumptions = CapexAssumptions()
    weather_forecast = (
        forecast_weather(weather, np.random.default_rng(7)) if controller == "mpc" else None
    )

    grid = lattice(SOLAR_OPTIONS, WIND_OPTIONS, BATTERY_OPTIONS)
    capitals = sorted(capital_of(c, assumptions) for c in grid)

    print(f"\nBOUNDED SEARCH vs EXHAUSTIVE SWEEP -- {days} days, {controller.upper()}")
    print("=" * 76)
    if days < 365:
        print("  WARNING: a short horizon distorts sizing and flatters this comparison.")
        print("  Capital is annualised while energy cost covers only the horizon, so")
        print("  hardware looks far too expensive and 'install nothing' tends to win. A")
        print("  zero-capital winner makes the bound prune almost everything at once, which")
        print("  reports a pruning rate the full year will not reproduce. Use 365 for any")
        print("  number worth quoting.\n")
    print(f"  lattice          {len(grid)} configurations "
          f"({len(SOLAR_OPTIONS)} solar x {len(WIND_OPTIONS)} wind x "
          f"{len(BATTERY_OPTIONS)} battery)")
    print(f"  capital range    Rs {capitals[0]:,.0f} to Rs {capitals[-1]:,.0f} per year")
    print("  the bound        annual_total = capital + energy + carbon, and the last two")
    print("                   are never negative, so capital alone lower-bounds the total")

    print(f"\n  running the bounded search ...", flush=True)
    t0 = time.perf_counter()
    found = search(
        profiles, SOLAR_OPTIONS, WIND_OPTIONS, BATTERY_OPTIONS,
        config=DEFAULT_CONFIG, assumptions=assumptions, controller=controller,
        weather_forecast=weather_forecast,
        search_config=SearchConfig(reliability_floor_pct=MIN_RELIABILITY_PCT),
    )
    search_seconds = time.perf_counter() - t0

    print(f"\n  running the exhaustive sweep ...", flush=True)
    t0 = time.perf_counter()
    swept = sweep(
        profiles, SOLAR_OPTIONS, WIND_OPTIONS, BATTERY_OPTIONS,
        config=DEFAULT_CONFIG, assumptions=assumptions, controller=controller,
        weather_forecast=weather_forecast, progress_every=40,
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
        print("  THE TWO DISAGREE. That is a failure, not a trade-off: the bound is meant")
        print("  to be exact, so a different answer means it is unsound and pruning is")
        print("  discarding the optimum. Do not report a speed-up from this run.")
        gap = (found.best.annual_total_inr - expected.annual_total_inr
               if expected and found.best else float("nan"))
        print(f"  cost gap: Rs {gap:,.0f}/yr")
    else:
        print(f"  Same recommendation, reached with {found.skipped_pct:.0f}% fewer")
        print(f"  simulations -- {found.evaluations} against {len(swept)}. The bound is")
        print("  exact, so this is not an approximation that happened to land correctly:")
        print("  every pruned candidate was provably unable to win.")
        if search_seconds > sweep_seconds:
            print()
            print("  But it took LONGER in wall clock. Fewer simulations is not the same as")
            print("  less time: the sweep saturates every core in one shot, while a bounded")
            print("  search has to finish a round before it knows what the next round can")
            print("  skip. On this lattice the parallelism is worth more than the pruning.")

    print(f"\nCaveat: {days} days at one site, {controller.upper()} controller. The")
    print("agreement check is what matters here; the timings depend on core count.\n")


if __name__ == "__main__":
    main()
