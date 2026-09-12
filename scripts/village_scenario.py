"""Size a village microgrid at a coastal site, where wind has a chance.

Banaskantha rejects wind on measured physics: 2.5 m/s mean, a 1.2% capacity factor. This
runs the same engine at Dwarka on the Saurashtra coast, at village scale, so a shared
80 m turbine is plausible where a single farm's 18 m mast is not. It is a check that the
engine follows the resource rather than carrying a bias against wind.

Demand is one farm's profile multiplied by the number of farms, so only the site and the
scale change. A real village would have a different demand shape; this is a controlled
comparison, not a village survey.
"""

import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402

from gramurja.config import DEFAULT_CONFIG, DieselUnit, Feeder  # noqa: E402
from gramurja.forecast import forecast_weather  # noqa: E402
from gramurja.profiles import generate_profiles  # noqa: E402
from gramurja.sizing import CapexAssumptions, recommend, sweep  # noqa: E402
from gramurja.weather import fetch_actual_weather, wind_output_kw  # noqa: E402

DWARKA = (22.24, 68.97)
FARMS = 20
HUB_HEIGHT_M = 80.0

REFERENCE_SOLAR_KWP = 100.0
REFERENCE_WIND_KW = 50.0

SOLAR_OPTIONS = [0, 20, 40, 60, 80, 120]
WIND_OPTIONS = [0, 10, 20, 40, 60]
BATTERY_OPTIONS = [0, 50, 100, 200, 400]

# A shared village turbine is a different machine from a farm mast: bigger, taller, and
# far cheaper per kW than the micro-wind figure used for the single-farm case.
COMMUNITY_WIND_INR_PER_KW = 70_000.0


def main() -> None:
    weather = fetch_actual_weather(
        "2025-01-01", "2025-12-31", latitude=DWARKA[0], longitude=DWARKA[1]
    )

    reference = replace(
        DEFAULT_CONFIG,
        solar_capacity_kwp=REFERENCE_SOLAR_KWP,
        wind_capacity_kw=REFERENCE_WIND_KW,
    )
    profiles = generate_profiles(days=365, config=reference, weather=weather)
    profiles = replace(
        profiles,
        load_kw=profiles.load_kw * FARMS,
        pump_kw=profiles.pump_kw * FARMS,
        wind_kw=wind_output_kw(weather, REFERENCE_WIND_KW, hub_height_m=HUB_HEIGHT_M),
    )

    feeders = (
        Feeder("agricultural", max_import_kw=10.0 * FARMS, import_price_per_kwh=1.50),
        Feeder("village", max_import_kw=3.0 * FARMS, import_price_per_kwh=5.00),
    )
    genset = DieselUnit(max_kw=6.0 * FARMS, litres_per_kwh=0.30)
    assumptions = replace(CapexAssumptions(), wind_inr_per_kw=COMMUNITY_WIND_INR_PER_KW)

    solar_unit = profiles.solar_kw.sum() / REFERENCE_SOLAR_KWP
    wind_unit = profiles.wind_kw.sum() / REFERENCE_WIND_KW
    night = profiles.solar_kw < 0.01
    print(f"Dwarka village microgrid  -  {FARMS} farms, {profiles.load_kw.sum():,.0f} kWh/yr")
    print(f"  solar yield      {solar_unit:,.0f} kWh/kWp")
    print(f"  wind yield       {wind_unit:,.0f} kWh/kW at {HUB_HEIGHT_M:.0f} m "
          f"(CF {100 * wind_unit / 8760:.1f}%)")
    print(f"  wind after dark  {100 * profiles.wind_kw[night].sum() / profiles.wind_kw.sum():.0f}% "
          f"of its output, when solar delivers nothing\n")

    forecast = forecast_weather(weather, np.random.default_rng(7))
    combos = len(SOLAR_OPTIONS) * len(WIND_OPTIONS) * len(BATTERY_OPTIONS)
    print(f"Sweeping {combos} configurations...\n")

    results = sweep(
        profiles,
        SOLAR_OPTIONS,
        WIND_OPTIONS,
        BATTERY_OPTIONS,
        config=reference,
        assumptions=assumptions,
        controller="mpc",
        weather_forecast=forecast,
        diesel_unit=genset,
        feeders=feeders,
        hub_height_m=HUB_HEIGHT_M,
        progress_every=25,
    )

    feasible = sorted(
        (r for r in results if r.kpis.reliability_pct >= 99.0),
        key=lambda r: r.annual_total_inr,
    )
    print(f"\n{'Solar':>7}{'Wind':>7}{'Batt':>7}{'Diesel':>10}{'Renew':>8}"
          f"{'Capital':>13}{'Energy':>13}{'Total':>13}")
    print(f"{'kWp':>7}{'kW':>7}{'kWh':>7}{'L/yr':>10}{'%':>8}"
          f"{'INR/yr':>13}{'INR/yr':>13}{'INR/yr':>13}")
    print("-" * 78)
    for r in feasible[:12]:
        print(f"{r.solar_kwp:>7,.0f}{r.wind_kw:>7,.0f}{r.battery_kwh:>7,.0f}"
              f"{r.kpis.diesel_litres:>10,.0f}{r.kpis.renewable_fraction_pct:>8.1f}"
              f"{r.annual_capital_inr:>13,.0f}{r.annual_energy_inr:>13,.0f}"
              f"{r.annual_total_inr:>13,.0f}")

    best = recommend(results, 99.0)
    print(f"\nRecommended: {best.solar_kwp:,.0f} kWp solar, {best.wind_kw:,.0f} kW wind, "
          f"{best.battery_kwh:,.0f} kWh battery")
    print(f"  wind selected: {'YES' if best.wind_kw > 0 else 'no'}")

    cheapest_with_wind = min(
        (r for r in feasible if r.wind_kw > 0), key=lambda r: r.annual_total_inr, default=None
    )
    cheapest_without = min(
        (r for r in feasible if r.wind_kw == 0), key=lambda r: r.annual_total_inr, default=None
    )
    if cheapest_with_wind and cheapest_without:
        gap = cheapest_with_wind.annual_total_inr - cheapest_without.annual_total_inr
        print(f"  best with wind    INR {cheapest_with_wind.annual_total_inr:,.0f}/yr")
        print(f"  best without wind INR {cheapest_without.annual_total_inr:,.0f}/yr")
        print(f"  wind costs        INR {gap:+,.0f}/yr")


if __name__ == "__main__":
    main()
