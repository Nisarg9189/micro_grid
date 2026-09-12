"""Check the synthesised forecast against genuine archived forecasts.

Year-long runs cannot use real forecasts: Open-Meteo's previous-runs archive reaches back
about 92 days, so `forecast_weather` manufactures a series with the site's measured error
instead. This asks whether that substitution is fair, by running the optimiser over the
window where real forecasts *are* available, three times over the same actual weather:

  perfect    - the controller sees the future exactly. An upper bound.
  archived   - the controller plans on what Open-Meteo's model actually predicted a day
               ahead, as issued at the time.
  synthesised - the controller plans on our manufactured forecast.

If archived and synthesised land close together, the year-long results stand. If they
diverge, the synthetic forecast is flattering the optimiser and the annual figures need
re-stating.
"""

import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402

from gramurja.config import AGRICULTURAL_FEEDER, DEFAULT_CONFIG, VILLAGE_FEEDER  # noqa: E402
from gramurja.forecast import build_forecast, forecast_weather  # noqa: E402
from gramurja.kpi import KPIs, compute_kpis  # noqa: E402
from gramurja.mpc import run_mpc  # noqa: E402
from gramurja.profiles import generate_profiles  # noqa: E402
from gramurja.weather import WeatherSeries, fetch_forecast_pairs  # noqa: E402

SOLAR_KWP = 3.0
BATTERY_KWH = 5.0
FEEDERS = (AGRICULTURAL_FEEDER, VILLAGE_FEEDER)


def _slice(weather: WeatherSeries, start: int, end: int) -> WeatherSeries:
    return WeatherSeries(
        irradiance=weather.irradiance[start:end],
        temperature=weather.temperature[start:end],
        wind_speed=weather.wind_speed[start:end],
        cloud_cover=weather.cloud_cover[start:end],
    )


def _whole_days(actual: WeatherSeries, forecast: WeatherSeries) -> tuple[int, int]:
    """Largest day-aligned window where both series carry data."""
    valid = np.flatnonzero(~np.isnan(forecast.irradiance) & ~np.isnan(actual.irradiance))
    start = int(np.ceil(valid[0] / 24) * 24)
    end = int(((valid[-1] + 1) // 24) * 24)
    return start, end


def _mae_fraction(actual: np.ndarray, predicted: np.ndarray) -> float:
    daylight = actual > 5.0
    return float(np.abs(actual - predicted)[daylight].mean() / actual[daylight].mean())


def main() -> None:
    actual_weather, archived_weather = fetch_forecast_pairs(past_days=92)
    start, end = _whole_days(actual_weather, archived_weather)
    actual_weather = _slice(actual_weather, start, end)
    archived_weather = _slice(archived_weather, start, end)
    days = (end - start) // 24

    config = replace(
        DEFAULT_CONFIG,
        solar_capacity_kwp=SOLAR_KWP,
        wind_capacity_kw=0.0,
        battery_capacity_kwh=BATTERY_KWH,
        battery_max_charge_kw=BATTERY_KWH * 0.25,
        battery_max_discharge_kw=BATTERY_KWH * 0.25,
    )
    profiles = generate_profiles(days=days, config=config, weather=actual_weather)
    synthetic_weather = forecast_weather(actual_weather, np.random.default_rng(7))

    print(f"Window: {days} days ({end - start} hours) where archived forecasts exist")
    print(f"System: {SOLAR_KWP:.0f} kWp solar, {BATTERY_KWH:.0f} kWh battery\n")
    print("Irradiance error against measured actuals")
    print(f"  archived forecast    {100 * _mae_fraction(actual_weather.irradiance, archived_weather.irradiance):.1f}% MAE")
    print(f"  synthesised forecast {100 * _mae_fraction(actual_weather.irradiance, synthetic_weather.irradiance):.1f}% MAE\n")

    def dispatch(weather: WeatherSeries | None) -> KPIs:
        forecast = None
        if weather is not None:
            forecast = build_forecast(profiles, FEEDERS, weather, SOLAR_KWP, 0.0)
        log = run_mpc(profiles, config, with_wind=False, forecast=forecast)
        return compute_kpis(log, config)

    runs = {
        "perfect": dispatch(None),
        "archived": dispatch(archived_weather),
        "synthesised": dispatch(synthetic_weather),
    }

    print(f"{'run':<14}{'diesel L':>11}{'grid kWh':>11}{'cost INR':>12}"
          f"{'unmet kWh':>11}{'vs perfect':>12}")
    print("-" * 71)
    reference = runs["perfect"].total_cost_inr
    for name, kpis in runs.items():
        gap = kpis.total_cost_inr - reference
        print(f"{name:<14}{kpis.diesel_litres:>11,.1f}{kpis.grid_kwh:>11,.0f}"
              f"{kpis.total_cost_inr:>12,.0f}{kpis.unmet_kwh:>11,.1f}"
              f"{gap:>+12,.0f}")

    archived_gap = runs["archived"].total_cost_inr - reference
    synthetic_gap = runs["synthesised"].total_cost_inr - reference
    print(f"\nCost of forecast error: archived INR {archived_gap:,.0f}, "
          f"synthesised INR {synthetic_gap:,.0f}")
    if archived_gap > 0:
        print(f"The synthetic forecast reproduces {100 * synthetic_gap / archived_gap:.0f}% "
              "of the penalty a real forecast imposes.")
        if synthetic_gap < archived_gap:
            print("It is the more optimistic of the two, so annual figures are a mild upper bound.")


if __name__ == "__main__":
    main()
