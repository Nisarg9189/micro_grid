"""Phase 2: establish the baselines every later savings claim is measured against."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dataclasses import replace  # noqa: E402

import numpy as np  # noqa: E402

from gramurja.baseline import run_smart_rules, run_status_quo  # noqa: E402
from gramurja.config import AGRICULTURAL_FEEDER, DEFAULT_CONFIG, VILLAGE_FEEDER  # noqa: E402
from gramurja.forecast import build_forecast, forecast_weather  # noqa: E402
from gramurja.kpi import KPIs, compare, compute_kpis  # noqa: E402
from gramurja.mpc import run_mpc  # noqa: E402
from gramurja.profiles import generate_profiles  # noqa: E402
from gramurja.weather import fetch_actual_weather  # noqa: E402

FEEDERS = (AGRICULTURAL_FEEDER, VILLAGE_FEEDER)

WEATHER_START = "2025-01-01"
WEATHER_END = "2025-12-31"

# The sizing sweep's recommendation, not the reference capacities in DEFAULT_CONFIG.
# Those exist to scale candidates during a sweep and are far larger than anything
# worth installing.
SOLAR_KWP = 3.0
WIND_KW = 0.0
BATTERY_KWH = 5.0
BATTERY_C_RATE = 0.25

ROWS = [
    ("Demand", "demand_kwh", "kWh"),
    ("Served", "served_kwh", "kWh"),
    ("Unmet load", "unmet_kwh", "kWh"),
    ("Reliability", "reliability_pct", "%"),
    ("Solar used", "solar_used_kwh", "kWh"),
    ("Wind used", "wind_used_kwh", "kWh"),
    ("Renewable curtailed", "renewable_curtailed_kwh", "kWh"),
    ("Renewable share", "renewable_fraction_pct", "%"),
    ("Grid import", "grid_kwh", "kWh"),
    ("Grid cost", "grid_cost_inr", "INR"),
    ("Diesel energy", "diesel_kwh", "kWh"),
    ("Diesel volume", "diesel_litres", "L"),
    ("Diesel cost", "diesel_cost_inr", "INR"),
    ("Total energy cost", "total_cost_inr", "INR"),
    ("CO2", "co2_kg", "kg"),
]


def print_table(status_quo: KPIs, rules: KPIs, optimiser: KPIs) -> None:
    print(f"{'Metric':<22}{'Unit':<6}{'Status quo':>15}{'Rule-based':>14}{'Optimiser':>14}")
    print("-" * 71)
    for label, field, unit in ROWS:
        print(
            f"{label:<22}{unit:<6}"
            f"{getattr(status_quo, field):>15,.1f}"
            f"{getattr(rules, field):>14,.1f}"
            f"{getattr(optimiser, field):>14,.1f}"
        )


def print_delta(title: str, delta: dict) -> None:
    print(f"\n{title}")
    print("-" * 71)
    print(f"  Diesel saved            {delta['diesel_litres_saved']:>12,.0f} L "
          f"({delta['diesel_reduction_pct']:.1f}%)")
    print(f"  Cost saved              {delta['cost_saved_inr']:>12,.0f} INR "
          f"({delta['cost_reduction_pct']:.1f}%)")
    print(f"  CO2 avoided             {delta['co2_avoided_kg']:>12,.0f} kg")
    print(f"  Reliability change      {delta['reliability_change_pct']:>12,.2f} pp")


def main() -> None:
    config = replace(
        DEFAULT_CONFIG,
        solar_capacity_kwp=SOLAR_KWP,
        wind_capacity_kw=WIND_KW,
        battery_capacity_kwh=BATTERY_KWH,
        battery_max_charge_kw=BATTERY_KWH * BATTERY_C_RATE,
        battery_max_discharge_kw=BATTERY_KWH * BATTERY_C_RATE,
    )
    weather = fetch_actual_weather(WEATHER_START, WEATHER_END)
    profiles = generate_profiles(days=365, config=config, weather=weather)

    print(f"Simulating {len(profiles)} hourly steps on measured weather "
          f"({WEATHER_START}..{WEATHER_END})")
    print(f"System: {SOLAR_KWP:.0f} kWp solar, {WIND_KW:.0f} kW wind, "
          f"{BATTERY_KWH:.0f} kWh battery\n")

    rng = np.random.default_rng(7)
    forecast = build_forecast(
        profiles, FEEDERS, forecast_weather(weather, rng), SOLAR_KWP, WIND_KW, rng=rng
    )

    status_quo = run_status_quo(profiles, config)
    rules = run_smart_rules(profiles, config)
    optimiser = compute_kpis(
        run_mpc(
            profiles,
            config,
            with_solar=SOLAR_KWP > 0,
            with_wind=WIND_KW > 0,
            forecast=forecast,
        ),
        config,
    )

    print_table(status_quo, rules, optimiser)
    print_delta("Rule-based control, vs status quo", compare(status_quo, rules))
    print_delta("Optimiser, vs status quo", compare(status_quo, optimiser))
    print_delta("What the optimiser adds over rules", compare(rules, optimiser))
    print("\nThe optimiser plans on a day-ahead forecast, not on perfect foresight.")


if __name__ == "__main__":
    main()
