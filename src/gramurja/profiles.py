"""Synthetic hourly profiles for a Banaskantha farm.

These are generated, not measured. They are shaped to match the seasonal pattern of
the region (rabi irrigation peak, monsoon cloud cover, Jyotigram-style rationed
agricultural feeder supply) so the optimizer is exercised against realistic structure.
Replace with metered data before reporting savings for a real site.
"""

from dataclasses import dataclass

import numpy as np

from .config import DEFAULT_CONFIG, FarmConfig, Feeder
from .weather import WeatherSeries, pv_output_kw, wind_output_kw

HOURS_PER_DAY = 24


@dataclass
class Profiles:
    solar_kw: np.ndarray
    wind_kw: np.ndarray
    load_kw: np.ndarray
    pump_kw: np.ndarray
    grid_status: np.ndarray
    grid_status_village: np.ndarray
    grid_status_scheduled: np.ndarray

    def __len__(self) -> int:
        return len(self.load_kw)

    def status_for(self, feeder: Feeder) -> np.ndarray:
        if feeder.name == "agricultural":
            return self.grid_status
        if feeder.name == "village":
            return self.grid_status_village
        raise ValueError(f"no availability series for feeder {feeder.name!r}")


def _seasonal_solar_factor(day_of_year: np.ndarray) -> np.ndarray:
    month = (day_of_year % 365) / 365 * 12
    monsoon = np.exp(-0.5 * ((month - 7.5) / 1.6) ** 2) * 0.45
    winter_haze = np.exp(-0.5 * ((month - 0.5) / 1.8) ** 2) * 0.18
    return 1.0 - monsoon - winter_haze


def _wind_output(
    hour: np.ndarray,
    day_index: np.ndarray,
    capacity_kw: float,
    rng: np.random.Generator,
    capacity_factor: float = 0.20,
) -> np.ndarray:
    """Wind peaks during the southwest monsoon, when solar is at its weakest.

    That anti-correlation is the reason wind earns a place in the mix at all here.
    """
    month = (day_index % 365) / 365 * 12
    seasonal = 0.55 + 0.9 * np.exp(-0.5 * ((month - 7.5) / 2.2) ** 2)
    diurnal = 0.7 + 0.5 * np.sin(np.pi * (hour - 8) / 14.0)
    noise = rng.weibull(2.0, size=len(hour))

    shape = np.clip(seasonal * diurnal * noise, 0.0, None)
    shape = shape / shape.mean() * capacity_factor
    return capacity_kw * np.clip(shape, 0.0, 1.0)


def _daily_pump_hours(month: float) -> float:
    if month >= 11 or month <= 3:
        return 3.0
    if 4 <= month <= 5:
        return 2.0
    if 6 <= month <= 9:
        return 0.5
    return 1.0


def generate_profiles(
    days: int = 365,
    config: FarmConfig = DEFAULT_CONFIG,
    pump_start_hour: int = 7,
    seed: int = 42,
    weather: WeatherSeries | None = None,
) -> Profiles:
    """Build the hourly series for one farm.

    Pass `weather` to drive solar and wind from measured Open-Meteo data for the site;
    without it the generation series are synthetic, which overstates solar yield by
    roughly a third and wind by an order of magnitude at this location.
    """
    rng = np.random.default_rng(seed)
    steps = days * HOURS_PER_DAY

    hour = np.arange(steps) % HOURS_PER_DAY
    day_index = np.arange(steps) // HOURS_PER_DAY
    month = (day_index % 365) / 365 * 12

    daylight = np.clip(np.sin(np.pi * (hour - 6.5) / 12.0), 0, None)
    seasonal = _seasonal_solar_factor(day_index)
    cloud = np.repeat(
        np.clip(rng.normal(0.88, 0.16, size=days), 0.15, 1.0),
        HOURS_PER_DAY,
    )
    if weather is not None:
        solar_kw = pv_output_kw(weather, config.solar_capacity_kwp)[:steps]
        wind_kw = wind_output_kw(weather, config.wind_capacity_kw)[:steps]
    else:
        solar_kw = config.solar_capacity_kwp * daylight * seasonal * cloud
        wind_kw = _wind_output(hour, day_index, config.wind_capacity_kw, rng)

    household = config.household_base_kw + np.where(
        (hour >= 18) & (hour <= 22), 0.5, 0.0
    )
    dairy = np.where(((hour >= 5) & (hour <= 7)) | ((hour >= 17) & (hour <= 19)),
                     config.dairy_peak_kw, 0.1)
    cold_storage = config.cold_storage_kw * (0.6 + 0.4 * (hour >= 10) * (hour <= 18))

    pump_kw = np.zeros(steps)
    for d in range(days):
        hours_today = _daily_pump_hours(month[d * HOURS_PER_DAY])
        whole_hours = int(hours_today)
        remainder = hours_today - whole_hours
        start = d * HOURS_PER_DAY + pump_start_hour
        pump_kw[start:start + whole_hours] = config.pump_kw
        if remainder > 0:
            pump_kw[start + whole_hours] = config.pump_kw * remainder

    load_kw = household + dairy + cold_storage + pump_kw

    grid_status, grid_status_scheduled = _generate_grid_status(days, rng)

    return Profiles(
        solar_kw=solar_kw,
        wind_kw=wind_kw,
        load_kw=load_kw,
        pump_kw=pump_kw,
        grid_status=grid_status,
        grid_status_village=_generate_village_grid_status(days, rng),
        grid_status_scheduled=grid_status_scheduled,
    )


ROSTER_START_HOURS = (6, 14, 22)


def _generate_grid_status(
    days: int,
    rng: np.random.Generator,
    unplanned_outage_rate: float = 0.05,
) -> tuple[np.ndarray, np.ndarray]:
    """Rationed agricultural feeder on a published rotating roster.

    Jyotigram supply is scheduled, not random: farmers are told which eight-hour block
    they get, and the block rotates week to week. Returns the actual availability and the
    published schedule separately, because the split is the point -- a controller can plan
    against the roster but cannot foresee an unplanned outage, and that is precisely the
    part of the forecasting problem that has any value.
    """
    steps = days * HOURS_PER_DAY
    scheduled = np.zeros(steps)
    for day in range(days):
        start_hour = ROSTER_START_HOURS[(day // 7) % len(ROSTER_START_HOURS)]
        start = day * HOURS_PER_DAY + start_hour
        scheduled[start:start + 8] = 1.0

    actual = scheduled.copy()
    actual[rng.random(steps) < unplanned_outage_rate] = 0.0
    return actual, scheduled


def _generate_village_grid_status(
    days: int,
    rng: np.random.Generator,
    outage_rate: float = 0.07,
) -> np.ndarray:
    """Village feeder: nominally continuous, with intermittent multi-hour outages.

    Gujarat's Jyotigram scheme deliberately splits the two: villages get round-the-clock
    single-phase supply while agricultural feeders are rationed to a daily block. Domestic
    and dairy load therefore must not be modelled on the agricultural feeder's schedule.
    """
    steps = days * HOURS_PER_DAY
    status = np.ones(steps)
    outage_hours = int(steps * outage_rate)
    started = 0
    while started < outage_hours:
        start = rng.integers(0, steps)
        length = rng.integers(1, 4)
        status[start:start + length] = 0.0
        started += length
    return status
