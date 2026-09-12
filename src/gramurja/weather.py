"""Open-Meteo weather for the farm site, and conversion to generator output.

Two endpoints are used, for different jobs:

archive        - what the weather actually did. Drives real generation.
previous-runs  - what the forecast said it would do, as issued. This is the only way to
                 measure genuine forecast error; the historical-forecast endpoint serves
                 best-available analysis and is identical to the archive, so it reports
                 zero error and is useless for this.

Responses are cached on disk, since a year of hourly data is a large request to repeat.
"""

import hashlib
import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import numpy as np

# Palanpur, Banaskantha district headquarters.
BANASKANTHA_LAT = 24.17
BANASKANTHA_LON = 72.43

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
PREVIOUS_RUNS_URL = "https://previous-runs-api.open-meteo.com/v1/forecast"

CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "weather"


@dataclass
class WeatherSeries:
    irradiance: np.ndarray
    temperature: np.ndarray
    wind_speed: np.ndarray
    cloud_cover: np.ndarray

    def __len__(self) -> int:
        return len(self.irradiance)


def _request(url: str, params: dict) -> dict:
    query = urllib.parse.urlencode(params)
    # Python hashes strings with a per-process seed, so the digest has to be stable
    # instead: worker processes would otherwise all miss the cache and refetch.
    digest = hashlib.sha256(f"{url}?{query}".encode()).hexdigest()[:16]
    cache_path = CACHE_DIR / f"{urllib.parse.urlparse(url).netloc}_{digest}.json"

    if cache_path.exists():
        return json.loads(cache_path.read_text())

    with urllib.request.urlopen(f"{url}?{query}", timeout=120) as response:
        payload = json.load(response)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(payload))
    return payload


def _column(hourly: dict, key: str) -> np.ndarray:
    return np.array(
        [np.nan if value is None else value for value in hourly[key]], dtype=float
    )


def fetch_actual_weather(
    start_date: str,
    end_date: str,
    latitude: float = BANASKANTHA_LAT,
    longitude: float = BANASKANTHA_LON,
) -> WeatherSeries:
    hourly = _request(
        ARCHIVE_URL,
        {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": "shortwave_radiation,temperature_2m,cloud_cover,wind_speed_10m",
            "wind_speed_unit": "ms",
            "timezone": "Asia/Kolkata",
        },
    )["hourly"]

    return WeatherSeries(
        irradiance=_column(hourly, "shortwave_radiation"),
        temperature=_column(hourly, "temperature_2m"),
        wind_speed=_column(hourly, "wind_speed_10m"),
        cloud_cover=_column(hourly, "cloud_cover"),
    )


def fetch_forecast_pairs(
    past_days: int = 92,
    latitude: float = BANASKANTHA_LAT,
    longitude: float = BANASKANTHA_LON,
) -> tuple[WeatherSeries, WeatherSeries]:
    """Return (actual, day-ahead forecast) over the same hours.

    The forecast columns carry what the model run issued a day earlier predicted, so the
    difference between the two is real numerical-weather-prediction error at this site.
    """
    fields = ["shortwave_radiation", "temperature_2m", "wind_speed_10m", "cloud_cover"]
    hourly = _request(
        PREVIOUS_RUNS_URL,
        {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": ",".join(fields + [f"{f}_previous_day1" for f in fields]),
            "past_days": past_days,
            "forecast_days": 1,
            "wind_speed_unit": "ms",
            "timezone": "Asia/Kolkata",
        },
    )["hourly"]

    actual = WeatherSeries(*(_column(hourly, f) for f in fields))
    forecast = WeatherSeries(*(_column(hourly, f"{f}_previous_day1") for f in fields))
    return actual, forecast


def pv_output_kw(
    weather: WeatherSeries,
    capacity_kwp: float,
    temperature_coefficient: float = -0.004,
    system_efficiency: float = 0.85,
    nominal_cell_temperature: float = 45.0,
) -> np.ndarray:
    """Irradiance and cell temperature to AC output.

    Banaskantha runs hot, and panels lose roughly 0.4%/degC above 25degC, so cell
    temperature is not a detail here: a 45degC afternoon costs around 8% of nameplate.
    """
    irradiance = np.nan_to_num(weather.irradiance, nan=0.0)
    ambient = np.nan_to_num(weather.temperature, nan=25.0)

    cell_temperature = ambient + irradiance / 800.0 * (nominal_cell_temperature - 20.0)
    derate = 1.0 + temperature_coefficient * (cell_temperature - 25.0)

    output = capacity_kwp * (irradiance / 1000.0) * derate * system_efficiency
    return np.clip(output, 0.0, capacity_kwp)


def wind_output_kw(
    weather: WeatherSeries,
    capacity_kw: float,
    hub_height_m: float = 18.0,
    cut_in_ms: float = 3.0,
    rated_ms: float = 12.0,
    cut_out_ms: float = 25.0,
    shear_exponent: float = 0.20,
) -> np.ndarray:
    """Small-turbine power curve, with wind sheared from the 10 m measurement height."""
    if capacity_kw <= 0:
        return np.zeros(len(weather))

    speed = np.nan_to_num(weather.wind_speed, nan=0.0) * (hub_height_m / 10.0) ** shear_exponent

    ramp = (speed**3 - cut_in_ms**3) / (rated_ms**3 - cut_in_ms**3)
    output = capacity_kw * np.clip(ramp, 0.0, 1.0)
    output[(speed < cut_in_ms) | (speed >= cut_out_ms)] = 0.0
    return output
