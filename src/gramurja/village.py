"""Load model for a Banaskantha village microgrid.

The single-farm model treats one holding in isolation. A village is not that model
multiplied: a hundred households do not switch on together, and twenty pumps do not start
in the same minute. That spread -- diversity -- is the whole economic case for sharing
infrastructure, because the aggregate peak sits far below the sum of the individual peaks.

Four load groups, chosen because they behave differently rather than to be exhaustive:

households  - small individually, dominated by an evening peak after solar has gone
pumps       - large, scheduled, and the only genuinely deferrable load here
dairy       - a bulk milk cooler with a hard deadline; milk chills when it arrives
water       - drinking-water pumping into an overhead tank, so critical but shiftable

Every figure below is a modelling assumption. None of it is metered village data.
"""

from dataclasses import dataclass

import numpy as np

HOURS_PER_DAY = 24


@dataclass(frozen=True)
class VillageConfig:
    households: int = 100
    farms: int = 20

    # Electrified rural Gujarat: lighting, fans, television, phone charging.
    household_daily_kwh: float = 2.5
    household_evening_share: float = 0.55

    pump_kw: float = 3.73
    pump_hours_rabi: float = 3.0
    pump_hours_summer: float = 2.0
    pump_hours_monsoon: float = 0.5

    # Village bulk milk cooler, running after each collection.
    dairy_chiller_kw: float = 5.0
    dairy_standby_kw: float = 0.8

    water_pump_kw: float = 3.73
    water_hours_per_day: float = 4.0


@dataclass
class VillageLoads:
    """Aggregate village demand, and the parts it is made of."""

    total_kw: np.ndarray
    household_kw: np.ndarray
    pump_kw: np.ndarray
    dairy_kw: np.ndarray
    water_kw: np.ndarray

    def __len__(self) -> int:
        return len(self.total_kw)

    def annual_kwh(self) -> dict[str, float]:
        return {
            "households": float(self.household_kw.sum()),
            "irrigation": float(self.pump_kw.sum()),
            "dairy": float(self.dairy_kw.sum()),
            "water supply": float(self.water_kw.sum()),
            "total": float(self.total_kw.sum()),
        }

    @property
    def deferrable_kw(self) -> np.ndarray:
        """Load that could move in time without anyone noticing much."""
        return self.pump_kw + self.water_kw

    @property
    def critical_kw(self) -> np.ndarray:
        """Load that must be served when it arrives. Milk does not wait."""
        return self.dairy_kw


def _household_load(hour: np.ndarray, config: VillageConfig, rng: np.random.Generator) -> np.ndarray:
    """Aggregate of many small homes, peaking in the evening.

    Summed over a hundred homes the shape is smooth: individual switching is invisible at
    this scale, so only a small residual noise is added rather than modelling each home.
    """
    evening = np.exp(-0.5 * ((hour - 20.0) / 2.4) ** 2)
    morning = 0.45 * np.exp(-0.5 * ((hour - 7.0) / 1.6) ** 2)
    base = 0.25

    shape = base + morning + config.household_evening_share * 3.0 * evening
    shape = shape / shape.mean()

    mean_kw = config.households * config.household_daily_kwh / HOURS_PER_DAY
    noise = 1.0 + 0.04 * rng.standard_normal(len(hour))
    return np.clip(mean_kw * shape * noise, 0.0, None)


def _daily_pump_hours(month: float, config: VillageConfig) -> float:
    if month >= 11 or month <= 3:
        return config.pump_hours_rabi
    if 4 <= month <= 5:
        return config.pump_hours_summer
    if 6 <= month <= 9:
        return config.pump_hours_monsoon
    return 1.0


def _pump_load(
    days: int,
    month: np.ndarray,
    config: VillageConfig,
    rng: np.random.Generator,
) -> np.ndarray:
    """Every farm pumps on its own schedule, which is what creates diversity.

    Start hours are drawn once per farm and held for the year, since a farmer's routine is
    set by crop, labour and habit rather than redrawn daily. Summing staggered pumps gives
    an aggregate peak well below twenty times one pump.
    """
    steps = days * HOURS_PER_DAY
    load = np.zeros(steps)
    start_hours = rng.integers(5, 17, size=config.farms)

    for farm in range(config.farms):
        for day in range(days):
            hours_today = _daily_pump_hours(month[day * HOURS_PER_DAY], config)
            whole = int(hours_today)
            remainder = hours_today - whole
            start = day * HOURS_PER_DAY + int(start_hours[farm])
            load[start:start + whole] += config.pump_kw
            if remainder > 0 and start + whole < steps:
                load[start + whole] += config.pump_kw * remainder
    return load


def _dairy_load(hour: np.ndarray, config: VillageConfig) -> np.ndarray:
    """Bulk milk cooler: chilling after the morning and evening collections."""
    chilling = (((hour >= 7) & (hour <= 9)) | ((hour >= 18) & (hour <= 20)))
    return np.where(chilling, config.dairy_chiller_kw, config.dairy_standby_kw)


def _water_load(hour: np.ndarray, config: VillageConfig) -> np.ndarray:
    """Filling the overhead tank. The tank is the buffer, so the timing is flexible."""
    hours = int(config.water_hours_per_day)
    pumping = (hour >= 5) & (hour < 5 + hours)
    return np.where(pumping, config.water_pump_kw, 0.0)


def generate_village_loads(
    days: int = 365,
    config: VillageConfig = VillageConfig(),
    seed: int = 11,
) -> VillageLoads:
    rng = np.random.default_rng(seed)
    steps = days * HOURS_PER_DAY
    hour = np.arange(steps) % HOURS_PER_DAY
    month = (np.arange(steps) // HOURS_PER_DAY % 365) / 365 * 12

    household = _household_load(hour, config, rng)
    pump = _pump_load(days, month, config, rng)
    dairy = _dairy_load(hour, config)
    water = _water_load(hour, config)

    return VillageLoads(
        total_kw=household + pump + dairy + water,
        household_kw=household,
        pump_kw=pump,
        dairy_kw=dairy,
        water_kw=water,
    )
