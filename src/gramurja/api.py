"""HTTP API so the model can be driven from a browser.

The published dashboard is a static snapshot: a page cannot re-run a Python simulation.
This server closes that gap, so a reviewer can change the site, the tariffs or the hardware
and watch the answer change, including asking the model to size the system itself.

One constraint shapes the whole design. A full 8,760-hour optimisation takes about 105
seconds and a full sizing sweep about 25 minutes -- neither is something to wait for behind
a slider. So interactive requests run a shorter horizon (30 days by default, 90 at most)
and every response reports the horizon it used. A 30-day result is a fair comparison
between controllers but is NOT the annual figure, and the API says so in `meta.caveat`
rather than letting the number travel without it.

    PYTHONPATH=src .venv/bin/python scripts/serve.py
"""

from dataclasses import replace
from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .advice import daily_briefing, recommend_irrigation_window
from .baseline import run_smart_rules, run_status_quo
from .config import DEFAULT_CONFIG, DieselUnit, Economics, Feeder
from .forecast import build_forecast, forecast_weather
from .kpi import KPIs, compute_kpis
from .mpc import MPCConfig, run_mpc
from .profiles import generate_profiles
from .sizing import CapexAssumptions, recommend, sweep
from .weather import fetch_actual_weather, wind_output_kw

PAGE = Path(__file__).resolve().parents[2] / "report" / "console.html"

# Coarse grids: the point is an answer while someone waits, not the last rupee.
SIZE_SOLAR = [0, 2, 3, 4, 5, 6, 8]
SIZE_WIND = [0, 3]
SIZE_BATTERY = [0, 5, 10, 15, 20]

app = FastAPI(title="GramUrja AI", docs_url="/api/docs")


class Params(BaseModel):
    lat: float = Field(24.17, ge=-90, le=90)
    lon: float = Field(72.43, ge=-180, le=180)
    site: str = "Palanpur, Banaskantha"
    year: int = Field(2025, ge=2015, le=2025)
    days: int = Field(30, ge=7, le=90, description="horizon; 90 max to bound request time")

    solar: float = Field(3.0, ge=0, le=200)
    wind: float = Field(0.0, ge=0, le=200)
    battery: float = Field(5.0, ge=0, le=500)
    battery_reserve: float = Field(0.20, ge=0, le=0.9)
    c_rate: float = Field(0.25, gt=0, le=2)
    hub_height: float = Field(18.0, ge=5, le=120)
    genset_kw: float = Field(6.0, ge=0, le=500)

    pump_kw: float = Field(3.73, ge=0, le=100)
    household_kw: float = Field(0.4, ge=0, le=100)
    dairy_kw: float = Field(1.2, ge=0, le=100)
    cold_storage_kw: float = Field(0.8, ge=0, le=100)

    diesel_price: float = Field(98.39, gt=0, le=500)
    ag_tariff: float = Field(1.50, ge=0, le=100)
    village_tariff: float = Field(5.00, ge=0, le=100)
    ag_kw: float = Field(10.0, ge=0, le=1000)
    village_kw: float = Field(3.0, ge=0, le=1000)
    carbon_price: float = Field(0.0, ge=0, le=200)
    grid_carbon: float = Field(0.71, ge=0, le=2)

    advice_day: int = Field(5, ge=0)
    language: str = "english"


def _config(p: Params, reference: bool = False):
    floor = (lambda v: v if v > 0 else 1.0) if reference else (lambda v: v)
    battery = floor(p.battery)
    return replace(
        DEFAULT_CONFIG,
        pump_kw=p.pump_kw, household_base_kw=p.household_kw,
        dairy_peak_kw=p.dairy_kw, cold_storage_kw=p.cold_storage_kw,
        solar_capacity_kwp=floor(p.solar), wind_capacity_kw=floor(p.wind),
        battery_capacity_kwh=battery, battery_min_soc=p.battery_reserve,
        battery_max_charge_kw=battery * p.c_rate,
        battery_max_discharge_kw=battery * p.c_rate,
        economics=Economics(diesel_price_per_litre=p.diesel_price,
                            grid_co2_kg_per_kwh=p.grid_carbon),
    )


def _feeders(p: Params):
    return (
        Feeder("agricultural", max_import_kw=p.ag_kw, import_price_per_kwh=p.ag_tariff),
        Feeder("village", max_import_kw=p.village_kw, import_price_per_kwh=p.village_tariff),
    )


def _setup(p: Params, reference: bool = False):
    config = _config(p, reference=reference)
    weather = fetch_actual_weather(
        f"{p.year}-01-01", f"{p.year}-12-31", latitude=p.lat, longitude=p.lon
    )
    profiles = generate_profiles(days=p.days, config=config, weather=weather)
    if p.wind > 0 and p.hub_height != 18.0:
        profiles = replace(profiles, wind_kw=wind_output_kw(
            weather, config.wind_capacity_kw, hub_height_m=p.hub_height)[:len(profiles)])
    return config, weather, profiles


def _kpis(k: KPIs) -> dict:
    return {
        "diesel_litres": round(k.diesel_litres, 1),
        "cost_inr": round(k.total_cost_inr, 0),
        "reliability_pct": round(k.reliability_pct, 2),
        "unmet_kwh": round(k.unmet_kwh, 1),
        "co2_kg": round(k.co2_kg, 0),
        "grid_kwh": round(k.grid_kwh, 0),
        "renewable_pct": round(k.renewable_fraction_pct, 1),
    }


def _resource(weather, profiles, p: Params) -> dict:
    """Resource per unit installed, which needs a 1 kW probe when none is installed."""
    wind_probe = wind_output_kw(weather, 1.0, hub_height_m=p.hub_height)[:len(profiles)]
    solar_probe = generate_profiles(
        days=p.days, config=replace(_config(p, reference=True), solar_capacity_kwp=1.0),
        weather=weather).solar_kw
    return {
        # Extrapolated to a year so the figure is comparable with published yields.
        "solar_kwh_per_kwp_year": round(float(solar_probe.sum()) * 365.0 / p.days, 0),
        "wind_capacity_factor_pct": round(100 * float(wind_probe.mean()), 2),
        "demand_kwh": round(float(profiles.load_kw.sum()), 0),
        "peak_kw": round(float(profiles.load_kw.max()), 2),
    }


@app.get("/")
def index():
    if not PAGE.exists():
        raise HTTPException(503, "console.html has not been built yet")
    return FileResponse(PAGE)


@app.post("/api/simulate")
def simulate(p: Params):
    """Run all three controllers on the given hardware and return the hourly detail."""
    config, weather, profiles = _setup(p)
    feeders = _feeders(p)
    genset = DieselUnit(max_kw=p.genset_kw, litres_per_kwh=0.30)

    status_quo = run_status_quo(profiles, config, agricultural=feeders[0], village=feeders[1])
    rules = run_smart_rules(profiles, config, feeders=feeders, diesel_unit=genset)

    rng = np.random.default_rng(7)
    forecast = build_forecast(profiles, feeders, forecast_weather(weather, rng),
                              p.solar, p.wind, rng=rng)
    log = run_mpc(profiles, config, with_solar=p.solar > 0, with_wind=p.wind > 0,
                  with_battery=p.battery > 0, diesel_unit=genset, feeders=feeders,
                  forecast=forecast, mpc_config=MPCConfig(carbon_price_inr_per_kg=p.carbon_price))
    optimiser = compute_kpis(log, config, diesel_unit=genset)

    def column(module, field, index=0):
        for key in ((module, index, field), (module, field)):
            if key in log.columns:
                return [round(float(v), 3) for v in log[key].to_numpy()]
        return [0.0] * len(profiles)

    return {
        "meta": {
            "days": p.days,
            "site": p.site,
            "caveat": f"{p.days}-day horizon, not an annual figure. "
                      "Controller comparison is fair; absolute totals are not annual.",
        },
        "resource": _resource(weather, profiles, p),
        "kpis": {"status_quo": _kpis(status_quo), "rules": _kpis(rules),
                 "optimiser": _kpis(optimiser)},
        "series": {
            "load_kw": [round(float(v), 3) for v in profiles.load_kw],
            "solar_kw": column("renewable", "solar_used", 0),
            "ag_kw": column("grid", "grid_import", 0),
            "village_kw": column("grid", "grid_import", 1),
            "diesel_kw": column("genset", "genset_production", 0),
            "discharge_kw": column("battery", "discharge_amount", 0),
            "charge_kw": column("battery", "charge_amount", 0),
            "soc": column("battery", "soc", 0),
            "ag_available": [int(v) for v in profiles.grid_status],
            "village_available": [int(v) for v in profiles.grid_status_village],
            "carbon_kg_per_kwh": [round(float(v), 3) for v in profiles.grid_carbon_kg_per_kwh],
        },
    }


@app.post("/api/size")
def size(p: Params):
    """Let the model choose the hardware, rather than being told it."""
    config, weather, profiles = _setup(p, reference=True)
    feeders = _feeders(p)
    genset = DieselUnit(max_kw=p.genset_kw, litres_per_kwh=0.30)
    forecast_wx = forecast_weather(weather, np.random.default_rng(7))

    results = sweep(
        profiles, SIZE_SOLAR, SIZE_WIND, SIZE_BATTERY, config,
        replace(CapexAssumptions(), carbon_price_inr_per_kg=p.carbon_price),
        controller="mpc", weather_forecast=forecast_wx, diesel_unit=genset,
        feeders=feeders, hub_height_m=p.hub_height, progress_every=0,
    )
    # Capital is recovered per YEAR but energy was only simulated over the horizon, so the
    # two must be put on the same footing before ranking. Left unscaled, capital looks
    # ~12x too dear on a 30-day run and the search recommends installing nothing at all.
    scale = 365.0 / p.days

    def annual_total(r):
        return r.annual_capital_inr + (r.annual_energy_inr + r.annual_carbon_inr) * scale

    feasible = sorted((r for r in results if r.kpis.reliability_pct >= 99.0), key=annual_total)
    if not feasible:
        return {"meta": {"days": p.days, "evaluated": len(results)}, "recommended": None,
                "candidates": [],
                "message": "No configuration held 99% reliability. Try a larger genset "
                           "or a bigger feeder allowance."}

    def row(r):
        return {
            "solar_kwp": r.solar_kwp, "wind_kw": r.wind_kw, "battery_kwh": r.battery_kwh,
            "diesel_litres": round(r.kpis.diesel_litres, 1),
            "reliability_pct": round(r.kpis.reliability_pct, 2),
            "capital_inr": round(r.annual_capital_inr, 0),
            "energy_inr": round(r.annual_energy_inr * scale, 0),
            "total_inr": round(annual_total(r), 0),
            "renewable_pct": round(r.kpis.renewable_fraction_pct, 1),
        }

    seasonal = (
        "" if p.days >= 60 else
        f" A {p.days}-day window sits in one season, so the extrapolation is rough -"
        " use 60-90 days here, or the CLI sweep for a true annual answer."
    )
    return {
        "meta": {
            "days": p.days,
            "evaluated": len(results),
            "caveat": f"Each candidate simulated over {p.days} days; energy cost is scaled "
                      f"to a year (x{scale:.1f}) so it is comparable with annualised "
                      f"capital.{seasonal}",
        },
        "recommended": row(feasible[0]),
        "candidates": [row(r) for r in feasible[:10]],
    }


@app.post("/api/advice")
def advice(p: Params):
    """Rank pump start hours, then optionally re-word the result for a farmer."""
    config, _, profiles = _setup(p)
    feeders = _feeders(p)
    genset = DieselUnit(max_kw=p.genset_kw, litres_per_kwh=0.30)
    day = min(p.advice_day, max(0, p.days - 2))

    result = recommend_irrigation_window(profiles, day=day, config=config,
                                         feeders=feeders, diesel_unit=genset)
    briefing = daily_briefing(profiles, result, config)

    payload = {
        "day": day,
        "best_start": result.best.start_hour,
        "hours_needed": result.hours_needed,
        "cost_saved_inr": round(result.cost_saved_inr, 0),
        "diesel_saved_litres": round(result.diesel_saved_litres, 2),
        "options": [{"start_hour": o.start_hour, "cost_inr": round(o.cost_inr, 1),
                     "diesel_litres": round(o.diesel_litres, 2)} for o in result.options],
        "briefing": briefing,
    }

    if p.language.lower() != "english":
        from .explain import render_advice
        rendered = render_advice(briefing, language=p.language.lower())
        payload["message"] = rendered.safe_text
        payload["language"] = rendered.language
        payload["numbers_verified"] = rendered.verified
        payload["unverified_numbers"] = rendered.unverified_numbers
    return payload
