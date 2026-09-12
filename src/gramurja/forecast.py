"""What the controller believes about the future.

Kept deliberately separate from `Profiles`, which is what actually happens. The optimiser
plans against a `Forecast`; pymgrid then steps the microgrid on the real series. Any gap
between the two shows up as diesel burnt or load shed, which is the whole point of Phase 3.

The current hour is always known exactly -- it is a measurement, not a prediction -- so
every forecast window is pinned to the true value at its first step.
"""

from dataclasses import dataclass

import numpy as np

from .config import Feeder
from .profiles import Profiles
from .weather import WeatherSeries, pv_output_kw, wind_output_kw

# Day-ahead irradiance error for Banaskantha, measured against Open-Meteo's own previous
# model runs over 92 days: mean absolute error of ~17.5% of mean daylight irradiance.
MEASURED_IRRADIANCE_MAE_FRACTION = 0.175


@dataclass
class Forecast:
    renewable_kw: np.ndarray
    load_kw: np.ndarray
    feeder_status: list[np.ndarray]


def perfect_foresight(profiles: Profiles, feeders: tuple[Feeder, ...]) -> Forecast:
    return Forecast(
        renewable_kw=profiles.solar_kw + profiles.wind_kw,
        load_kw=profiles.load_kw,
        feeder_status=[profiles.status_for(feeder) for feeder in feeders],
    )


def _correlated_error(steps: int, rng: np.random.Generator, hours_per_day: int = 24) -> np.ndarray:
    """Forecast error is persistent within a day, not independent hour to hour.

    A weather model that misses a cloud bank is wrong all afternoon, so sampling white
    noise per hour would let the optimiser average the error away and flatter the result.
    """
    days = int(np.ceil(steps / hours_per_day))
    daily = np.repeat(rng.normal(0.0, 1.0, days), hours_per_day)[:steps]
    hourly = rng.normal(0.0, 1.0, steps)
    return 0.8 * daily + 0.6 * hourly


def forecast_weather(
    actual: WeatherSeries,
    rng: np.random.Generator,
    mae_fraction: float = MEASURED_IRRADIANCE_MAE_FRACTION,
) -> WeatherSeries:
    """Synthesise a day-ahead weather forecast with the site's measured error magnitude.

    Used for the full year, where archived forecasts are not available. The 92-day window
    covered by the previous-runs API should use the genuine forecast instead.
    """
    irradiance = np.nan_to_num(actual.irradiance, nan=0.0)
    daylight = irradiance > 5.0
    if not daylight.any():
        return actual

    # Scale the noise so mean absolute error lands on the measured fraction: for a standard
    # normal, E|x| = sqrt(2/pi), so the multiplier below converts target MAE into a sigma.
    error = _correlated_error(len(irradiance), rng)
    error = error / np.abs(error[daylight]).mean()
    target = mae_fraction * irradiance[daylight].mean()

    forecast_irradiance = np.clip(irradiance + error * target, 0.0, None)
    forecast_irradiance[~daylight] = irradiance[~daylight]

    return WeatherSeries(
        irradiance=forecast_irradiance,
        temperature=actual.temperature,
        wind_speed=actual.wind_speed,
        cloud_cover=actual.cloud_cover,
    )


def build_forecast(
    profiles: Profiles,
    feeders: tuple[Feeder, ...],
    weather_forecast: WeatherSeries,
    solar_capacity_kwp: float,
    wind_capacity_kw: float,
    load_error_fraction: float = 0.05,
    rng: np.random.Generator | None = None,
    hub_height_m: float = 18.0,
) -> Forecast:
    """Assemble what the controller can actually know a day ahead.

    Feeder availability is forecast from the published roster: the schedule is knowable,
    unplanned outages are not. Load is largely schedule-driven -- pump hours, milking
    times -- so it carries only modest error.
    """
    rng = rng or np.random.default_rng(0)
    steps = len(profiles)

    renewable = (
        pv_output_kw(weather_forecast, solar_capacity_kwp)[:steps]
        + wind_output_kw(weather_forecast, wind_capacity_kw, hub_height_m=hub_height_m)[:steps]
    )

    load_noise = 1.0 + load_error_fraction * _correlated_error(steps, rng)
    load = np.clip(profiles.load_kw * load_noise, 0.0, None)

    status = []
    for feeder in feeders:
        if feeder.name == "agricultural":
            status.append(profiles.grid_status_scheduled)
        else:
            # The village feeder is nominally continuous and its outages are unannounced,
            # so the best a controller can assume is that it will be there.
            status.append(np.ones(steps))

    return Forecast(renewable_kw=renewable, load_kw=load, feeder_status=status)
