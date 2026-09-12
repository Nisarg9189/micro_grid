"""Size a Banaskantha village microgrid serving the whole community, not one farm.

The single-farm case is dominated by an irrigation pump that runs in daylight. A village is
harder: households push the peak into the evening, after solar has gone. Storage therefore
has a different job here, and the sizing reflects that.
"""

import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402

from gramurja.baseline import run_rule_based  # noqa: E402
from gramurja.config import DEFAULT_CONFIG, DieselUnit, Feeder  # noqa: E402
from gramurja.farm import build_microgrid  # noqa: E402
from gramurja.forecast import forecast_weather  # noqa: E402
from gramurja.kpi import combine_kpis, compute_kpis  # noqa: E402
from gramurja.profiles import generate_profiles  # noqa: E402
from gramurja.sizing import CapexAssumptions, recommend, sweep  # noqa: E402
from gramurja.village import VillageConfig, generate_village_loads  # noqa: E402
from gramurja.weather import fetch_actual_weather  # noqa: E402

REFERENCE_SOLAR_KWP = 100.0
REFERENCE_WIND_KW = 20.0

SOLAR_OPTIONS = [0, 10, 20, 30, 40, 60, 80, 120]
WIND_OPTIONS = [0, 20]
BATTERY_OPTIONS = [0, 25, 50, 100, 150, 200]

# Village-scale connections, with routing enforced rather than implied. At farm scale the
# domestic feeder was physically too small to start the pump, so the restriction came for
# free. A 50 kW village transformer is not, so the rule has to be stated: agricultural and
# domestic supplies are separately sanctioned and separately tariffed, and neither may
# serve the other's load.
AGRICULTURAL = Feeder("agricultural", max_import_kw=60.0, import_price_per_kwh=1.50,
                      serves="irrigation")
VILLAGE = Feeder("village", max_import_kw=50.0, import_price_per_kwh=5.00,
                 serves="domestic")
FEEDERS = (AGRICULTURAL, VILLAGE)

VILLAGE_GENSET = DieselUnit(max_kw=50.0, litres_per_kwh=0.30)
FARM_PUMPSETS = DieselUnit(max_kw=30.0, litres_per_kwh=0.75)


def build_profiles(weather, loads, config):
    base = generate_profiles(days=365, config=config, weather=weather)
    return replace(base, load_kw=loads.total_kw, pump_kw=loads.pump_kw)


def status_quo(profiles, loads, config):
    """Today: pumps on the rationed feeder behind diesel pumpsets, everything else
    on the village feeder with no backup at all."""
    irrigation = compute_kpis(
        run_rule_based(
            build_microgrid(
                replace(profiles, load_kw=loads.pump_kw), config,
                with_solar=False, with_wind=False, with_battery=False,
                diesel_unit=FARM_PUMPSETS, feeders=(AGRICULTURAL,),
            )
        ),
        config, diesel_unit=FARM_PUMPSETS,
    )
    domestic = compute_kpis(
        run_rule_based(
            build_microgrid(
                replace(profiles, load_kw=loads.total_kw - loads.pump_kw), config,
                with_solar=False, with_wind=False, with_battery=False,
                with_genset=False, feeders=(VILLAGE,),
            )
        ),
        config,
    )
    return combine_kpis(irrigation, domestic)


def main() -> None:
    village = VillageConfig()
    loads = generate_village_loads(days=365, config=village)
    weather = fetch_actual_weather("2025-01-01", "2025-12-31")

    reference = replace(
        DEFAULT_CONFIG,
        solar_capacity_kwp=REFERENCE_SOLAR_KWP,
        wind_capacity_kw=REFERENCE_WIND_KW,
    )
    profiles = build_profiles(weather, loads, reference)

    breakdown = loads.annual_kwh()
    print(f"Village: {village.households} households, {village.farms} farms, "
          f"dairy chilling centre, drinking-water supply")
    for name, value in breakdown.items():
        if name != "total":
            print(f"  {name:<14}{value:>10,.0f} kWh/yr{100 * value / breakdown['total']:>7.1f}%")
    print(f"  {'total':<14}{breakdown['total']:>10,.0f} kWh/yr")
    print(f"  peak {loads.total_kw.max():.1f} kW, load factor "
          f"{100 * loads.total_kw.mean() / loads.total_kw.max():.0f}%, "
          f"pump diversity {loads.pump_kw.max() / (village.farms * village.pump_kw):.2f}\n")

    baseline = status_quo(profiles, loads, reference)
    print(f"Status quo: {baseline.diesel_litres:,.0f} L/yr, INR {baseline.total_cost_inr:,.0f}/yr, "
          f"{baseline.reliability_pct:.1f}% reliability, {baseline.co2_kg:,.0f} kg CO2")
    print(f"            {baseline.unmet_kwh:,.0f} kWh/yr unserved\n")

    forecast = forecast_weather(weather, np.random.default_rng(7))
    combos = len(SOLAR_OPTIONS) * len(WIND_OPTIONS) * len(BATTERY_OPTIONS)
    print(f"Sweeping {combos} configurations...\n")

    results = sweep(
        profiles, SOLAR_OPTIONS, WIND_OPTIONS, BATTERY_OPTIONS,
        config=reference, assumptions=CapexAssumptions(), controller="mpc",
        weather_forecast=forecast, diesel_unit=VILLAGE_GENSET, feeders=FEEDERS,
        progress_every=16,
    )

    feasible = sorted(
        (r for r in results if r.kpis.reliability_pct >= 99.0),
        key=lambda r: r.annual_total_inr,
    )
    print(f"\n{'Solar':>7}{'Wind':>6}{'Batt':>7}{'Diesel':>10}{'Renew':>8}"
          f"{'Capital':>13}{'Energy':>13}{'Total':>13}")
    print(f"{'kWp':>7}{'kW':>6}{'kWh':>7}{'L/yr':>10}{'%':>8}"
          f"{'INR/yr':>13}{'INR/yr':>13}{'INR/yr':>13}")
    print("-" * 77)
    for r in feasible[:10]:
        print(f"{r.solar_kwp:>7,.0f}{r.wind_kw:>6,.0f}{r.battery_kwh:>7,.0f}"
              f"{r.kpis.diesel_litres:>10,.0f}{r.kpis.renewable_fraction_pct:>8.1f}"
              f"{r.annual_capital_inr:>13,.0f}{r.annual_energy_inr:>13,.0f}"
              f"{r.annual_total_inr:>13,.0f}")

    best = recommend(results, 99.0)
    saved = baseline.total_cost_inr - best.annual_total_inr
    print(f"\nRecommended: {best.solar_kwp:,.0f} kWp solar, {best.wind_kw:,.0f} kW wind, "
          f"{best.battery_kwh:,.0f} kWh battery")
    print(f"  diesel        {best.kpis.diesel_litres:>10,.0f} L/yr  "
          f"({100 * (baseline.diesel_litres - best.kpis.diesel_litres) / baseline.diesel_litres:.1f}% cut)")
    print(f"  reliability   {best.kpis.reliability_pct:>10.1f} %")
    print(f"  CO2           {best.kpis.co2_kg:>10,.0f} kg/yr  "
          f"({100 * (baseline.co2_kg - best.kpis.co2_kg) / baseline.co2_kg:.1f}% cut)")
    print(f"  total cost    {best.annual_total_inr:>10,.0f} INR/yr")
    print(f"  saved         {saved:>10,.0f} INR/yr  "
          f"({saved / village.households:,.0f} per household)")


if __name__ == "__main__":
    main()
