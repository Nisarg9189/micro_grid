"""Derive solar, wind and battery sizing from the 8,760-hour profile."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402

from gramurja.config import DEFAULT_CONFIG  # noqa: E402
from gramurja.forecast import forecast_weather  # noqa: E402
from gramurja.profiles import generate_profiles  # noqa: E402
from gramurja.weather import fetch_actual_weather  # noqa: E402
from gramurja.sizing import (  # noqa: E402
    CapexAssumptions,
    SizingResult,
    recommend,
    status_quo_reference,
    sweep,
)

SOLAR_OPTIONS = [0, 1, 2, 3, 4, 5, 6, 8, 10, 12]
# Measured capacity factor at this site is 1.2%, so wind is kept only to show it losing.
WIND_OPTIONS = [0, 3]
BATTERY_OPTIONS = [0, 5, 10, 15, 20, 30]

WEATHER_START = "2025-01-01"
WEATHER_END = "2025-12-31"

MIN_RELIABILITY_PCT = 99.0


def row(result: SizingResult, baseline_litres: float) -> str:
    k = result.kpis
    diesel_cut = 100 * (baseline_litres - k.diesel_litres) / baseline_litres
    return (
        f"{result.solar_kwp:>6.0f}{result.wind_kw:>6.0f}{result.battery_kwh:>8.0f}"
        f"{k.reliability_pct:>9.2f}"
        f"{k.diesel_litres:>10.0f}{diesel_cut:>9.1f}"
        f"{result.annual_capital_inr:>12,.0f}{result.annual_energy_inr:>12,.0f}"
        f"{result.annual_total_inr:>12,.0f}"
    )


def header() -> str:
    return (
        f"{'Solar':>6}{'Wind':>6}{'Batt':>8}{'Reliab':>9}"
        f"{'Diesel':>10}{'Cut':>9}{'Capital':>12}{'Energy':>12}{'Total':>12}\n"
        f"{'kWp':>6}{'kW':>6}{'kWh':>8}{'%':>9}{'L/yr':>10}{'%':>9}"
        f"{'INR/yr':>12}{'INR/yr':>12}{'INR/yr':>12}"
    )


def main() -> None:
    # Defaults to the optimiser, since that is the system being recommended. Pass "rbc"
    # to reproduce the rule-based sizing, which buys no battery at all.
    controller = sys.argv[1] if len(sys.argv) > 1 else "mpc"
    if controller not in ("rbc", "mpc"):
        raise SystemExit("usage: optimize_sizing.py [mpc|rbc]")

    weather = fetch_actual_weather(WEATHER_START, WEATHER_END)
    profiles = generate_profiles(days=365, config=DEFAULT_CONFIG, weather=weather)
    assumptions = CapexAssumptions()

    # Size against forecasts the system will actually have, not perfect foresight.
    weather_forecast = (
        forecast_weather(weather, np.random.default_rng(7)) if controller == "mpc" else None
    )
    print(f"Controller: {controller.upper()}   weather: real ({WEATHER_START}..{WEATHER_END})")
    print(f"Forecast:   {'day-ahead, 17.5% MAE' if weather_forecast else 'n/a'}\n")

    baseline = status_quo_reference(profiles, DEFAULT_CONFIG)
    print(f"Status quo: {baseline.diesel_litres:,.0f} L/yr, "
          f"INR {baseline.total_cost_inr:,.0f}/yr, "
          f"{baseline.reliability_pct:.2f}% reliability\n")

    combos = len(SOLAR_OPTIONS) * len(WIND_OPTIONS) * len(BATTERY_OPTIONS)
    print(f"Sweeping {combos} configurations over 8,760 hours each...\n")
    results = sweep(
        profiles,
        SOLAR_OPTIONS,
        WIND_OPTIONS,
        BATTERY_OPTIONS,
        config=DEFAULT_CONFIG,
        assumptions=assumptions,
        controller=controller,
        weather_forecast=weather_forecast,
    )

    best = recommend(results, MIN_RELIABILITY_PCT)
    if best is None:
        print(f"No configuration reached {MIN_RELIABILITY_PCT}% reliability.")
        return

    print(f"Cheapest 15 configurations meeting {MIN_RELIABILITY_PCT}% reliability")
    print(header())
    print("-" * 85)
    feasible = sorted(
        (r for r in results if r.kpis.reliability_pct >= MIN_RELIABILITY_PCT),
        key=lambda r: r.annual_total_inr,
    )
    for result in feasible[:15]:
        print(row(result, baseline.diesel_litres))

    print("\nRecommended sizing")
    print("-" * 85)
    k = best.kpis
    diesel_cut = 100 * (baseline.diesel_litres - k.diesel_litres) / baseline.diesel_litres
    print(f"  Solar                {best.solar_kwp:>10.0f} kWp")
    print(f"  Wind                 {best.wind_kw:>10.0f} kW")
    print(f"  Battery              {best.battery_kwh:>10.0f} kWh")
    print(f"  Reliability          {k.reliability_pct:>10.2f} %")
    print(f"  Diesel               {k.diesel_litres:>10,.0f} L/yr  ({diesel_cut:.1f}% cut)")
    print(f"  Renewable share      {k.renewable_fraction_pct:>10.1f} %")
    print(f"  Curtailed            {k.renewable_curtailed_kwh:>10,.0f} kWh/yr")
    print(f"  Annualised capital   {best.annual_capital_inr:>10,.0f} INR/yr")
    print(f"  Energy cost          {best.annual_energy_inr:>10,.0f} INR/yr")
    print(f"  Total                {best.annual_total_inr:>10,.0f} INR/yr")
    print(f"  vs status quo        {baseline.total_cost_inr - best.annual_total_inr:>10,.0f} INR/yr saved")


if __name__ == "__main__":
    main()
