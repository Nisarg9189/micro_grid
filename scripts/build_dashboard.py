"""Export a dashboard dataset from an actual model run.

The dashboard is fed by real output rather than illustrative numbers, so this runs the
recommended system over the year and writes what the page needs: headline KPIs, a
representative week of hourly dispatch, monthly totals, the daily carbon-intensity shape,
and one day's irrigation recommendation.
"""

import json
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402

from gramurja.advice import daily_briefing, recommend_irrigation_window  # noqa: E402
from gramurja.baseline import run_smart_rules, run_status_quo  # noqa: E402
from gramurja.config import AGRICULTURAL_FEEDER, DEFAULT_CONFIG, VILLAGE_FEEDER  # noqa: E402
from gramurja.forecast import build_forecast, forecast_weather  # noqa: E402
from gramurja.kpi import compute_kpis  # noqa: E402
from gramurja.mpc import run_mpc  # noqa: E402
from gramurja.profiles import generate_profiles  # noqa: E402
from gramurja.weather import fetch_actual_weather  # noqa: E402

SOLAR_KWP, BATTERY_KWH = 3.0, 5.0
ANNUAL_CAPITAL_INR = 31_695.0
WEEK_START_DAY = 18
OUTPUT = Path(__file__).resolve().parents[1] / "report" / "dashboard_data.json"


def main() -> None:
    config = replace(
        DEFAULT_CONFIG,
        solar_capacity_kwp=SOLAR_KWP,
        wind_capacity_kw=0.0,
        battery_capacity_kwh=BATTERY_KWH,
        battery_max_charge_kw=BATTERY_KWH * 0.25,
        battery_max_discharge_kw=BATTERY_KWH * 0.25,
    )
    weather = fetch_actual_weather("2025-01-01", "2025-12-31")
    profiles = generate_profiles(days=365, config=config, weather=weather)

    rng = np.random.default_rng(7)
    forecast_wx = forecast_weather(weather, rng)
    forecast = build_forecast(
        profiles, (AGRICULTURAL_FEEDER, VILLAGE_FEEDER), forecast_wx, SOLAR_KWP, 0.0, rng=rng
    )

    print("running status quo and rule-based baselines...")
    status_quo = run_status_quo(profiles, config)
    rules = run_smart_rules(profiles, config)

    print("running the optimiser over 8,760 hours...")
    log = run_mpc(profiles, config, with_solar=True, with_wind=False, forecast=forecast)
    optimiser = compute_kpis(log, config)

    def column(module, field, index=0):
        for key in ((module, index, field), (module, field)):
            if key in log.columns:
                return log[key].to_numpy()
        return np.zeros(len(profiles))

    ag = column("grid", "grid_import", 0)
    village = column("grid", "grid_import", 1)
    solar_used = column("renewable", "solar_used", 0)
    soc = column("battery", "soc", 0)
    discharge = column("battery", "discharge_amount", 0)
    charge = column("battery", "charge_amount", 0)
    diesel = column("genset", "genset_production", 0)

    start = WEEK_START_DAY * 24
    week = slice(start, start + 168)
    hours = np.arange(168)

    print("evaluating irrigation windows...")
    advice = recommend_irrigation_window(profiles, day=WEEK_START_DAY, hours_needed=3, config=config)

    month_index = np.minimum((np.arange(len(profiles)) // 24) // 30, 11)
    monthly = []
    for month in range(12):
        mask = month_index == month
        monthly.append({
            "month": month + 1,
            "solar_kwh": round(float(solar_used[mask].sum()), 1),
            "ag_kwh": round(float(ag[mask].sum()), 1),
            "village_kwh": round(float(village[mask].sum()), 1),
            "diesel_litres": round(float(diesel[mask].sum() * 0.30), 2),
        })

    hour_of_day = np.arange(len(profiles)) % 24
    carbon_curve = [
        round(float(profiles.grid_carbon_kg_per_kwh[hour_of_day == h][0]), 3) for h in range(24)
    ]

    data = {
        "site": {
            "name": "Palanpur, Banaskantha",
            "latitude": 24.17,
            "longitude": 72.43,
            "year": 2025,
            "solar_kwp": SOLAR_KWP,
            "battery_kwh": BATTERY_KWH,
            "wind_kw": 0,
        },
        "kpis": {
            name: {
                "diesel_litres": round(k.diesel_litres, 1),
                "energy_cost_inr": round(k.total_cost_inr, 0),
                "reliability_pct": round(k.reliability_pct, 2),
                "unmet_kwh": round(k.unmet_kwh, 1),
                "co2_kg": round(k.co2_kg, 0),
                "grid_kwh": round(k.grid_kwh, 0),
                "renewable_pct": round(k.renewable_fraction_pct, 1),
            }
            for name, k in (("status_quo", status_quo), ("rules", rules), ("optimiser", optimiser))
        },
        "annual_capital_inr": ANNUAL_CAPITAL_INR,
        "week": {
            "start_day": WEEK_START_DAY,
            "hour": hours.tolist(),
            "load_kw": [round(float(v), 2) for v in profiles.load_kw[week]],
            "pump_kw": [round(float(v), 2) for v in profiles.pump_kw[week]],
            "solar_kw": [round(float(v), 2) for v in solar_used[week]],
            "ag_kw": [round(float(v), 2) for v in ag[week]],
            "village_kw": [round(float(v), 2) for v in village[week]],
            "diesel_kw": [round(float(v), 2) for v in diesel[week]],
            "discharge_kw": [round(float(v), 2) for v in discharge[week]],
            "charge_kw": [round(float(v), 2) for v in charge[week]],
            "soc": [round(float(v), 3) for v in soc[week]],
            "ag_available": [int(v) for v in profiles.grid_status[week]],
            "village_available": [int(v) for v in profiles.grid_status_village[week]],
        },
        "monthly": monthly,
        "carbon_curve": carbon_curve,
        "advice": {
            "day": advice.day,
            "hours_needed": advice.hours_needed,
            "best_start": advice.best.start_hour,
            "cost_saved_inr": round(advice.cost_saved_inr, 0),
            "diesel_saved_litres": round(advice.diesel_saved_litres, 2),
            "options": [
                {"start_hour": o.start_hour,
                 "cost_inr": round(o.cost_inr, 1),
                 "diesel_litres": round(o.diesel_litres, 2)}
                for o in advice.options
            ],
            "briefing": daily_briefing(profiles, advice, config),
        },
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(data, indent=1))
    print(f"wrote {OUTPUT} ({OUTPUT.stat().st_size / 1024:.0f} kB)")


if __name__ == "__main__":
    main()
