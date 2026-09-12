"""One parameterised entry point, so a reviewer can change the question without editing code.

Every other script fixes its site and hardware in the source. This one takes them on the
command line, which makes the model's claims checkable: point it at a different district,
a different tariff, a different battery, and see whether the conclusions hold.

    # the headline case
    PYTHONPATH=src .venv/bin/python scripts/simulate.py

    # somewhere windy, with a turbine
    PYTHONPATH=src .venv/bin/python scripts/simulate.py --lat 22.24 --lon 68.97 \
        --site "Dwarka" --solar 6 --wind 3 --hub-height 50

    # what if diesel were cheaper and grid dearer?
    PYTHONPATH=src .venv/bin/python scripts/simulate.py --diesel-price 70 --village-tariff 8

    # derive the hardware instead of assuming it
    PYTHONPATH=src .venv/bin/python scripts/simulate.py --sweep

Run with --help for the full list.
"""

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402

from gramurja.advice import daily_briefing, recommend_irrigation_window  # noqa: E402
from gramurja.baseline import run_smart_rules, run_status_quo  # noqa: E402
from gramurja.config import DEFAULT_CONFIG, DieselUnit, Economics, Feeder  # noqa: E402
from gramurja.forecast import build_forecast, forecast_weather  # noqa: E402
from gramurja.kpi import compute_kpis  # noqa: E402
from gramurja.mpc import MPCConfig, run_mpc  # noqa: E402
from gramurja.profiles import generate_profiles  # noqa: E402
from gramurja.sizing import CapexAssumptions, recommend, sweep  # noqa: E402
from gramurja.weather import fetch_actual_weather, wind_output_kw  # noqa: E402

SWEEP_SOLAR = [0, 1, 2, 3, 4, 5, 6, 8, 10, 12]
SWEEP_WIND = [0, 3]
SWEEP_BATTERY = [0, 5, 10, 15, 20, 30]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Simulate a rural microgrid for any site, hardware and tariff.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    site = p.add_argument_group("site")
    site.add_argument("--lat", type=float, default=24.17, help="latitude")
    site.add_argument("--lon", type=float, default=72.43, help="longitude")
    site.add_argument("--site", default="Palanpur, Banaskantha", help="name, for the report only")
    site.add_argument("--year", type=int, default=2025, help="calendar year of weather to use")

    hw = p.add_argument_group("hardware")
    hw.add_argument("--solar", type=float, default=3.0, help="solar capacity, kWp")
    hw.add_argument("--wind", type=float, default=0.0, help="wind capacity, kW")
    hw.add_argument("--battery", type=float, default=5.0, help="battery capacity, kWh")
    hw.add_argument("--battery-reserve", type=float, default=0.20, help="reserve floor, fraction")
    hw.add_argument("--c-rate", type=float, default=0.25, help="battery charge/discharge rate, C")
    hw.add_argument("--hub-height", type=float, default=18.0, help="turbine hub height, m")
    hw.add_argument("--genset-kw", type=float, default=6.0, help="backup genset rating, kW")

    load = p.add_argument_group("load")
    load.add_argument("--pump-kw", type=float, default=3.73, help="irrigation pump draw, kW")
    load.add_argument("--household-kw", type=float, default=0.4, help="household base load, kW")
    load.add_argument("--dairy-kw", type=float, default=1.2, help="dairy peak load, kW")
    load.add_argument("--cold-storage-kw", type=float, default=0.8, help="cold storage load, kW")

    econ = p.add_argument_group("economics")
    econ.add_argument("--diesel-price", type=float, default=98.39, help="INR per litre")
    econ.add_argument("--ag-tariff", type=float, default=1.50, help="agricultural feeder, INR/kWh")
    econ.add_argument("--village-tariff", type=float, default=5.00, help="village feeder, INR/kWh")
    econ.add_argument("--ag-kw", type=float, default=10.0, help="agricultural feeder capacity, kW")
    econ.add_argument("--village-kw", type=float, default=3.0, help="village feeder capacity, kW")
    econ.add_argument("--carbon-price", type=float, default=0.0, help="INR per kg CO2")
    econ.add_argument("--grid-carbon", type=float, default=0.71, help="grid mean kg CO2/kWh")

    run = p.add_argument_group("run")
    run.add_argument("--days", type=int, default=365, help="days to simulate")
    run.add_argument("--sweep", action="store_true", help="derive hardware instead of using it")
    run.add_argument("--advice-day", type=int, default=20, help="day to produce pump advice for")
    run.add_argument("--json", metavar="PATH", help="also write results as JSON")
    return p.parse_args()


def build_config(a: argparse.Namespace, reference: bool = False):
    """Turn the command line into a FarmConfig.

    `reference=True` is only for the sizing sweep, where these capacities are the
    denominators candidates are scaled against and so must be non-zero. On a direct run
    they are the actual hardware: substituting 1.0 for a requested 0 would hand the system
    a kilowatt of generation nobody asked for, which is exactly the bug this guards.
    """
    floor = (lambda v: v if v > 0 else 1.0) if reference else (lambda v: v)
    battery = floor(a.battery)
    return replace(
        DEFAULT_CONFIG,
        pump_kw=a.pump_kw,
        household_base_kw=a.household_kw,
        dairy_peak_kw=a.dairy_kw,
        cold_storage_kw=a.cold_storage_kw,
        solar_capacity_kwp=floor(a.solar),
        wind_capacity_kw=floor(a.wind),
        battery_capacity_kwh=battery,
        battery_min_soc=a.battery_reserve,
        battery_max_charge_kw=battery * a.c_rate,
        battery_max_discharge_kw=battery * a.c_rate,
        economics=Economics(
            diesel_price_per_litre=a.diesel_price,
            grid_co2_kg_per_kwh=a.grid_carbon,
        ),
    )


def main() -> None:
    a = parse_args()
    config = build_config(a, reference=a.sweep)
    feeders = (
        Feeder("agricultural", max_import_kw=a.ag_kw, import_price_per_kwh=a.ag_tariff),
        Feeder("village", max_import_kw=a.village_kw, import_price_per_kwh=a.village_tariff),
    )
    genset = DieselUnit(max_kw=a.genset_kw, litres_per_kwh=0.30)

    print(f"Site      {a.site}  ({a.lat}, {a.lon})")
    print(f"Weather   ERA5 reanalysis, calendar {a.year}, {a.days} days")
    print(f"Hardware  {a.solar:g} kWp solar · {a.wind:g} kW wind · {a.battery:g} kWh battery")
    print(f"Tariffs   agricultural Rs {a.ag_tariff}/kWh ({a.ag_kw:g} kW) · "
          f"village Rs {a.village_tariff}/kWh ({a.village_kw:g} kW)")
    print(f"Diesel    Rs {a.diesel_price}/L · carbon priced at Rs {a.carbon_price}/kg\n")

    weather = fetch_actual_weather(
        f"{a.year}-01-01", f"{a.year}-12-31", latitude=a.lat, longitude=a.lon
    )
    profiles = generate_profiles(days=a.days, config=config, weather=weather)
    if a.wind > 0 and a.hub_height != 18.0:
        profiles = replace(profiles, wind_kw=wind_output_kw(
            weather, config.wind_capacity_kw, hub_height_m=a.hub_height)[:len(profiles)])

    # Report the resource per unit installed, which needs a probe when none is installed.
    probe = generate_profiles(days=a.days, config=replace(
        config, solar_capacity_kwp=1.0, wind_capacity_kw=1.0), weather=weather)
    solar_yield = probe.solar_kw.sum()
    wind_cf = wind_output_kw(weather, 1.0, hub_height_m=a.hub_height)[:len(probe)].sum() / len(probe)
    print(f"Resource  solar {solar_yield:,.0f} kWh/kWp/yr · "
          f"wind capacity factor {100 * wind_cf:.1f}% at {a.hub_height:g} m")
    print(f"Demand    {profiles.load_kw.sum():,.0f} kWh/yr, peak {profiles.load_kw.max():.1f} kW\n")

    rng = np.random.default_rng(7)
    forecast_wx = forecast_weather(weather, rng)

    if a.sweep:
        combos = len(SWEEP_SOLAR) * len(SWEEP_WIND) * len(SWEEP_BATTERY)
        print(f"Deriving hardware: {combos} configurations over {a.days} days each.")
        print("Each candidate is a full simulation, so this takes a few minutes.\n")
        results = sweep(
            profiles, SWEEP_SOLAR, SWEEP_WIND, SWEEP_BATTERY, config,
            replace(CapexAssumptions(), carbon_price_inr_per_kg=a.carbon_price),
            controller="mpc", weather_forecast=forecast_wx,
            diesel_unit=genset, feeders=feeders, hub_height_m=a.hub_height,
            progress_every=max(10, combos // 6),
        )
        best = recommend(results, 99.0)
        if best is None:
            print("No configuration reached 99% reliability. Try a larger genset or feeder.")
            return
        print(f"\nCheapest configuration holding 99% reliability:")
        print(f"  {best.solar_kwp:g} kWp solar · {best.wind_kw:g} kW wind · "
              f"{best.battery_kwh:g} kWh battery")
        print(f"  diesel {best.kpis.diesel_litres:,.0f} L/yr · "
              f"reliability {best.kpis.reliability_pct:.1f}%")
        print(f"  capital Rs {best.annual_capital_inr:,.0f}/yr · "
              f"energy Rs {best.annual_energy_inr:,.0f}/yr · "
              f"total Rs {best.annual_total_inr:,.0f}/yr")
        return

    status_quo = run_status_quo(profiles, config, agricultural=feeders[0],
                                village=feeders[1])
    rules = run_smart_rules(profiles, config, feeders=feeders, diesel_unit=genset)
    forecast = build_forecast(profiles, feeders, forecast_wx, a.solar, a.wind, rng=rng)
    optimiser = compute_kpis(
        run_mpc(profiles, config,
                with_solar=a.solar > 0, with_wind=a.wind > 0, with_battery=a.battery > 0,
                diesel_unit=genset, feeders=feeders, forecast=forecast,
                mpc_config=MPCConfig(carbon_price_inr_per_kg=a.carbon_price)),
        config, diesel_unit=genset)

    rows = [("Diesel", "diesel_litres", " L", 1), ("Energy cost", "total_cost_inr", " INR", 0),
            ("Reliability", "reliability_pct", " %", 2), ("Unserved", "unmet_kwh", " kWh", 1),
            ("Renewable share", "renewable_fraction_pct", " %", 1), ("CO2", "co2_kg", " kg", 0)]
    print(f"{'Metric':<18}{'Status quo':>15}{'Rule-based':>14}{'Optimiser':>14}")
    print("-" * 61)
    for label, field, unit, dp in rows:
        print(f"{label:<18}{getattr(status_quo, field):>15,.{dp}f}"
              f"{getattr(rules, field):>14,.{dp}f}{getattr(optimiser, field):>14,.{dp}f}")

    saved = status_quo.total_cost_inr - optimiser.total_cost_inr
    print(f"\nOptimiser vs status quo: Rs {saved:,.0f}/yr less on energy, "
          f"{status_quo.diesel_litres - optimiser.diesel_litres:,.0f} L less diesel")
    print(f"Optimiser vs rule-based: Rs {rules.total_cost_inr - optimiser.total_cost_inr:,.0f}/yr, "
          f"{rules.diesel_litres - optimiser.diesel_litres:,.0f} L "
          "- this is what the optimisation itself contributes")

    if 0 <= a.advice_day < a.days:
        advice = recommend_irrigation_window(profiles, day=a.advice_day, config=config,
                                             feeders=feeders, diesel_unit=genset)
        print(f"\nIrrigation advice for day {a.advice_day}:")
        for line in daily_briefing(profiles, advice, config):
            print(f"  - {line}")

    if a.json:
        payload = {
            "site": {"name": a.site, "lat": a.lat, "lon": a.lon, "year": a.year},
            "hardware": {"solar_kwp": a.solar, "wind_kw": a.wind, "battery_kwh": a.battery},
            "resource": {"solar_kwh_per_kwp": round(solar_yield, 1),
                         "wind_capacity_factor": round(wind_cf, 4)},
            "kpis": {name: k.as_dict() for name, k in
                     (("status_quo", status_quo), ("rules", rules), ("optimiser", optimiser))},
        }
        Path(a.json).write_text(json.dumps(payload, indent=1))
        print(f"\nWrote {a.json}")


if __name__ == "__main__":
    main()
