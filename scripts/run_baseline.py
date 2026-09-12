"""Phase 2: establish the baselines every later savings claim is measured against."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gramurja.baseline import run_smart_rules, run_status_quo  # noqa: E402
from gramurja.config import DEFAULT_CONFIG  # noqa: E402
from gramurja.kpi import KPIs, compare  # noqa: E402
from gramurja.profiles import generate_profiles  # noqa: E402

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


def print_table(status_quo: KPIs, smart: KPIs) -> None:
    print(f"{'Metric':<22}{'Unit':<6}{'Status quo':>16}{'Solar+battery RBC':>20}")
    print("-" * 64)
    for label, field, unit in ROWS:
        a = getattr(status_quo, field)
        b = getattr(smart, field)
        print(f"{label:<22}{unit:<6}{a:>16,.1f}{b:>20,.1f}")


def main() -> None:
    days = 365
    profiles = generate_profiles(days=days, config=DEFAULT_CONFIG)

    print(f"Simulating {days} days ({len(profiles)} hourly steps)\n")

    status_quo = run_status_quo(profiles, DEFAULT_CONFIG)
    smart = run_smart_rules(profiles, DEFAULT_CONFIG)

    print_table(status_quo, smart)

    delta = compare(status_quo, smart)
    print("\nSolar + battery under rule-based control, vs status quo")
    print("-" * 64)
    print(f"  Diesel saved            {delta['diesel_litres_saved']:>12,.0f} L "
          f"({delta['diesel_reduction_pct']:.1f}%)")
    print(f"  Cost saved              {delta['cost_saved_inr']:>12,.0f} INR "
          f"({delta['cost_reduction_pct']:.1f}%)")
    print(f"  CO2 avoided             {delta['co2_avoided_kg']:>12,.0f} kg")
    print(f"  Reliability change      {delta['reliability_change_pct']:>12,.2f} pp")
    print("\nThese are the numbers the optimizer must beat in Phase 4.")


if __name__ == "__main__":
    main()
