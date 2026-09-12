"""Farmer-facing recommendations, derived from the optimiser rather than guessed.

Everything the dispatch optimiser does so far takes the irrigation schedule as given: the
pump runs when the farmer runs it, and the optimiser decides only where the power comes
from. This module closes the loop the other way. It asks what the pump schedule *should*
be, by shifting the pump to each candidate start hour, re-running the optimiser over the
day, and comparing what each choice actually costs.

That makes the advice a measured result rather than a rule of thumb. "Run the pump at 11"
is not a heuristic about sunshine here; it is the cheapest of twelve simulated alternatives.

No language model is involved, and deliberately so. The numbers come from the optimiser and
the sentences are assembled from them, so the advice cannot drift from what the model
actually found. A language model's proper job here is phrasing and translation, not
arithmetic.
"""

from dataclasses import dataclass, replace

import numpy as np

from .config import (
    AGRICULTURAL_FEEDER,
    BACKUP_GENSET,
    DEFAULT_CONFIG,
    VILLAGE_FEEDER,
    DieselUnit,
    FarmConfig,
    Feeder,
)
from .forecast import Forecast
from .kpi import compute_kpis
from .mpc import run_mpc
from .profiles import HOURS_PER_DAY, Profiles

FEEDERS = (AGRICULTURAL_FEEDER, VILLAGE_FEEDER)


@dataclass
class WindowOption:
    start_hour: int
    diesel_litres: float
    cost_inr: float
    unmet_kwh: float


@dataclass
class IrrigationAdvice:
    day: int
    hours_needed: int
    options: list[WindowOption]

    @property
    def best(self) -> WindowOption:
        return min(self.options, key=lambda o: (o.unmet_kwh > 0.01, o.cost_inr))

    @property
    def worst(self) -> WindowOption:
        return max(self.options, key=lambda o: o.cost_inr)

    @property
    def cost_saved_inr(self) -> float:
        return self.worst.cost_inr - self.best.cost_inr

    @property
    def diesel_saved_litres(self) -> float:
        return self.worst.diesel_litres - self.best.diesel_litres


def slice_profiles(profiles: Profiles, start: int, stop: int) -> Profiles:
    return Profiles(
        solar_kw=profiles.solar_kw[start:stop],
        wind_kw=profiles.wind_kw[start:stop],
        load_kw=profiles.load_kw[start:stop],
        pump_kw=profiles.pump_kw[start:stop],
        grid_status=profiles.grid_status[start:stop],
        grid_status_village=profiles.grid_status_village[start:stop],
        grid_status_scheduled=profiles.grid_status_scheduled[start:stop],
        grid_carbon_kg_per_kwh=profiles.grid_carbon_kg_per_kwh[start:stop],
    )


def with_pump_at(
    profiles: Profiles,
    day_offset: int,
    start_hour: int,
    hours: int,
    pump_kw: float,
) -> Profiles:
    """Move one day's pumping to a new start hour, leaving every other day alone."""
    pump = profiles.pump_kw.copy()
    day_slice = slice(day_offset * HOURS_PER_DAY, (day_offset + 1) * HOURS_PER_DAY)

    other_load = profiles.load_kw - profiles.pump_kw
    pump[day_slice] = 0.0
    begin = day_offset * HOURS_PER_DAY + start_hour
    pump[begin:begin + hours] = pump_kw

    return replace(profiles, pump_kw=pump, load_kw=other_load + pump)


def recommend_irrigation_window(
    profiles: Profiles,
    day: int,
    hours_needed: int = 3,
    config: FarmConfig = DEFAULT_CONFIG,
    earliest_hour: int = 5,
    latest_hour: int = 18,
    feeders: tuple[Feeder, ...] = FEEDERS,
    diesel_unit: DieselUnit = BACKUP_GENSET,
    horizon_days: int = 2,
) -> IrrigationAdvice:
    """Evaluate every feasible pump start and return them ranked by what they cost.

    A two-day window is simulated rather than one, so that a choice which merely pushes
    cost into tomorrow -- draining the battery late in the day, say -- is charged for it.
    """
    start = day * HOURS_PER_DAY
    stop = start + horizon_days * HOURS_PER_DAY
    window = slice_profiles(profiles, start, stop)

    options = []
    for start_hour in range(earliest_hour, latest_hour - hours_needed + 1):
        candidate = with_pump_at(window, 0, start_hour, hours_needed, config.pump_kw)
        log = run_mpc(
            candidate,
            config,
            with_wind=config.wind_capacity_kw > 0,
            diesel_unit=diesel_unit,
            feeders=feeders,
        )
        kpis = compute_kpis(log, config, diesel_unit=diesel_unit)
        options.append(
            WindowOption(
                start_hour=start_hour,
                diesel_litres=kpis.diesel_litres,
                cost_inr=kpis.total_cost_inr,
                unmet_kwh=kpis.unmet_kwh,
            )
        )

    return IrrigationAdvice(day=day, hours_needed=hours_needed, options=options)


def scheduled_feeder_blocks(profiles: Profiles, day: int) -> list[tuple[int, int]]:
    """Hours the agricultural feeder is rostered on, as contiguous blocks.

    A block beginning at 22:00 runs past midnight, so within a single day it shows up as
    two separate runs. Reporting first-on to last-on would call that "00:00 to 24:00".
    """
    day_slice = slice(day * HOURS_PER_DAY, (day + 1) * HOURS_PER_DAY)
    on = np.flatnonzero(profiles.grid_status_scheduled[day_slice] > 0)
    if len(on) == 0:
        return []

    blocks = []
    start = previous = int(on[0])
    for hour in on[1:]:
        hour = int(hour)
        if hour != previous + 1:
            blocks.append((start, previous + 1))
            start = hour
        previous = hour
    blocks.append((start, previous + 1))
    return blocks


def daily_briefing(
    profiles: Profiles,
    advice: IrrigationAdvice,
    config: FarmConfig = DEFAULT_CONFIG,
) -> list[str]:
    """Assemble the advice into lines a farmer can act on.

    Each line states what to do and why, so the recommendation can be judged rather than
    merely obeyed -- a farmer who knows the reason can overrule it when the model is wrong
    about something only they can see.
    """
    lines = []
    best, worst = advice.best, advice.worst
    end_hour = best.start_hour + advice.hours_needed

    lines.append(
        f"Run the irrigation pump from {best.start_hour:02d}:00 to {end_hour:02d}:00 "
        f"({advice.hours_needed} hours)."
    )

    if advice.cost_saved_inr > 1.0:
        lines.append(
            f"That is about Rs {advice.cost_saved_inr:,.0f} cheaper than the worst timing "
            f"today ({worst.start_hour:02d}:00), and uses "
            f"{advice.diesel_saved_litres:.1f} litres less diesel."
        )
    else:
        lines.append("Timing makes little difference today - any window costs about the same.")

    blocks = scheduled_feeder_blocks(profiles, advice.day)
    if blocks:
        spans = " and ".join(f"{a:02d}:00-{b:02d}:00" for a, b in blocks)
        lines.append(
            f"Agricultural feeder is scheduled {spans}. "
            "Unplanned outages are still possible."
        )

    day_slice = slice(advice.day * HOURS_PER_DAY, (advice.day + 1) * HOURS_PER_DAY)
    solar_today = profiles.solar_kw[day_slice].sum()
    solar_typical = profiles.solar_kw.sum() / (len(profiles) / HOURS_PER_DAY)
    if solar_typical > 0 and solar_today < 0.7 * solar_typical:
        lines.append(
            f"Expect weak sun tomorrow - about {100 * solar_today / solar_typical:.0f}% "
            "of a normal day. Battery reserve is being held back."
        )

    if best.diesel_litres > 0.1:
        lines.append(
            f"Around {best.diesel_litres:.1f} litres of diesel will still be needed "
            "even with the best timing."
        )
    else:
        lines.append("No diesel should be needed at all with this timing.")

    return lines
