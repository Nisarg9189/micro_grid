"""The layer that decides what is worth telling a farmer today, not just how to phrase it.

`advice.py` already answers one question well: when should the pump run? It re-simulates
every candidate start hour and reports the cheapest. But the optimiser knows more about a
day than that -- whether the feeder's schedule is about to shift, whether diesel will be
needed, whether the battery is being held in reserve -- and until now all of that either
went unreported or was jammed into one fixed template regardless of whether it mattered
today.

This module is the selection layer above those signals. It follows the same rule as every
other agent in this project: **no language model touches a number, and every decision is
deterministic and auditable.** The only judgement made here is *which* signals earn a place
in a short message, and that judgement is a plain, inspectable priority rule -- not a
learned or LLM-driven one.

Signals split into two kinds, mirroring the forcing/discretionary split in the (now
removed) dispatch agent:

**Forcing** -- a fact that invalidates a plan the farmer might otherwise be relying on.
The feeder's rostered start hour changing tomorrow is forcing: a farmer who does not know
this may show up to irrigate a window that no longer exists. A battery falling to a
critical reserve is forcing for the same reason cost is not why VoLL is priced above
diesel in the LP -- reliability is not a thing this project trades away for a shorter
message. Forcing items are always shown, even past the message cap.

**Discretionary** -- worth mentioning if there is room, ranked by the size of the
consequence in its own unit (rupees, litres, percentage points). These fill whatever space
forcing items leave, and are the ones a length cap is allowed to drop.

Every number surfaced still comes from a real simulation, exactly as in `advice.py`: one
extra MPC run at the recommended pump timing supplies the hourly diesel and battery detail
that `recommend_irrigation_window` computes internally but does not expose.
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .advice import (
    FEEDERS,
    IrrigationAdvice,
    recommend_irrigation_window,
    scheduled_feeder_blocks,
    slice_profiles,
    with_pump_at,
)
from .config import BACKUP_GENSET, DEFAULT_CONFIG, DieselUnit, FarmConfig, Feeder
from .mpc import run_mpc
from .profiles import HOURS_PER_DAY, Profiles


@dataclass(frozen=True)
class AdvisoryConfig:
    """Thresholds for what counts as material enough to mention.

    Kept separate from `AgentConfig` in the (removed) dispatch module deliberately: these
    govern a farmer's attention, not a controller's reliability, and the right values for
    one say nothing about the other.
    """

    max_items: int = 3

    # Below this, timing genuinely does not matter today, and saying so beats padding the
    # message with a number too small to act on.
    irrigation_saving_threshold_inr: float = 1.0

    # Below this much diesel today, it is not worth a line of its own.
    diesel_litres_threshold: float = 0.1

    # Below this SoC by the start of tomorrow, a real deficit is carrying over -- forcing.
    #
    # A battery this size touches its configured floor (config.battery_min_soc, a hard
    # LP constraint) on almost every ordinary day: it is cheapest to run down through the
    # afternoon and recharge overnight on the subsidised feeder, so a daily dip to the
    # floor is the arbitrage working as intended, not a warning. Measured directly: three
    # sample days all bottomed out at exactly the configured 20% floor at some point, and
    # a signal on that basis would fire every day, which defeats the whole point of a
    # ranked, capped message -- an alert seen daily stops being read.
    #
    # What actually distinguishes an ordinary day from a bad one is whether the battery
    # RECOVERS by the next morning. That is the number checked here: SoC at the day
    # boundary 24 hours in, not the day's minimum.
    battery_recovery_critical_pct: float = 30.0

    # Recovers, but to less than a comfortable margin -- worth a soft mention.
    battery_recovery_reserve_pct: float = 50.0


@dataclass(frozen=True)
class AdvisoryItem:
    """One candidate fact, and whether it is allowed to survive the message cap."""

    kind: str
    forcing: bool
    magnitude: float  # ranks discretionary items against others of the SAME kind's peers
    lines: list[str]


@dataclass
class AdvisoryBriefing:
    day: int
    header: str  # the one line always shown: what to do, unconditionally
    items: list[AdvisoryItem] = field(default_factory=list)
    considered: list[AdvisoryItem] = field(default_factory=list)
    # The irrigation search this briefing was built from, so a caller that also wants the
    # raw start-hour/cost table (the console does) does not have to re-run the search.
    irrigation: IrrigationAdvice | None = None

    @property
    def lines(self) -> list[str]:
        if not self.items:
            return [self.header, "No other changes needed today."]
        return [self.header] + [line for item in self.items for line in item.lines]

    @property
    def dropped(self) -> list[AdvisoryItem]:
        """What was considered but did not make it past the cap -- the audit trail."""
        shown = {id(item) for item in self.items}
        return [item for item in self.considered if id(item) not in shown]


def select_items(candidates: list[AdvisoryItem], max_items: int) -> list[AdvisoryItem]:
    """Forcing items are always shown; discretionary ones fill what room is left.

    A forcing item can push the shown count past `max_items` -- a plan-invalidating fact
    is not something a length cap should hide, the same way a feeder outage always forces
    a re-plan in the dispatch agent regardless of how recently it last re-planned.
    """
    forcing = [c for c in candidates if c.forcing]
    discretionary = sorted((c for c in candidates if not c.forcing), key=lambda c: -c.magnitude)
    remaining = max(0, max_items - len(forcing))
    chosen = forcing + discretionary[:remaining]

    # Stable, readable order: reasoning about the header first, then urgent notes, then
    # softer ones -- independent of the ranking that decided which of them made the cut.
    order = {"irrigation_reasoning": 0, "feeder_shift": 1, "battery_critical": 1,
             "diesel_need": 2, "battery_reserve": 2}
    return sorted(chosen, key=lambda c: order.get(c.kind, 9))


def _series(log: pd.DataFrame, module: str, field: str, index: int = 0) -> np.ndarray:
    """One module's hourly column, trying both the 2- and 3-level key shapes.

    pymgrid drops the module-index level only when every module type in the run is a
    singleton; two feeders means the whole log stays 3-level even for modules -- battery,
    genset -- that are singletons themselves. Trying both shapes means this does not care
    which case applies.
    """
    for key in ((module, index, field), (module, field)):
        if key in log.columns:
            return log[key].to_numpy(dtype=float)
    return np.zeros(len(log))


def _irrigation_reasoning(advice: IrrigationAdvice, config: AdvisoryConfig) -> AdvisoryItem | None:
    saving = advice.cost_saved_inr
    if saving <= config.irrigation_saving_threshold_inr:
        return None
    worst = advice.worst
    return AdvisoryItem(
        kind="irrigation_reasoning", forcing=False, magnitude=saving,
        lines=[
            f"That is about Rs {saving:,.0f} cheaper than the worst timing today "
            f"({worst.start_hour:02d}:00), and uses "
            f"{advice.diesel_saved_litres:.1f} litres less diesel."
        ],
    )


def _feeder_shift(profiles: Profiles, day: int) -> AdvisoryItem | None:
    """The agricultural feeder's rostered block changing tomorrow -- forcing.

    The roster rotates among a few start hours over the course of a season; most days
    tomorrow's block is identical to today's and this raises nothing at all.
    """
    if day + 1 >= len(profiles) // HOURS_PER_DAY:
        return None
    today = scheduled_feeder_blocks(profiles, day)
    tomorrow = scheduled_feeder_blocks(profiles, day + 1)
    if today == tomorrow:
        return None
    spans = (" and ".join(f"{a:02d}:00-{b:02d}:00" for a, b in tomorrow)
             if tomorrow else "no scheduled block")
    return AdvisoryItem(
        kind="feeder_shift", forcing=True, magnitude=0.0,
        lines=[f"Note: the agricultural feeder's schedule changes tomorrow, to {spans}. "
               "Plan irrigation around the new timing, not today's."],
    )


def _diesel_and_battery(
    log: pd.DataFrame,
    config: FarmConfig,
    diesel_unit: DieselUnit,
    advisory_config: AdvisoryConfig,
) -> list[AdvisoryItem]:
    """Read the day's diesel and battery detail from the log `run_mpc` was given.

    `diesel_unit` is threaded through explicitly rather than read off `config` -- the same
    unit `run_mpc` was called with, so litres here cannot mismatch the log's own CO2, the
    class of bug `compute_kpis` now guards against.
    """
    items: list[AdvisoryItem] = []
    hours = min(HOURS_PER_DAY, len(log))

    diesel_kw = _series(log, "genset", "genset_production")[:hours]
    diesel_hours = int(np.sum(diesel_kw > 0.05))
    diesel_kwh = float(diesel_kw.sum())
    diesel_litres = diesel_kwh * diesel_unit.litres_per_kwh
    if diesel_litres > advisory_config.diesel_litres_threshold:
        items.append(AdvisoryItem(
            kind="diesel_need", forcing=False, magnitude=diesel_litres,
            lines=[f"Diesel backup will run about {diesel_hours} hour"
                   f"{'s' if diesel_hours != 1 else ''} today, using roughly "
                   f"{diesel_litres:.1f} litres."],
        ))

    if config.battery_capacity_kwh > 0:
        # pymgrid logs "soc" as a 0..1 fraction already, not kWh -- dividing by capacity
        # again here previously reported a 5 kWh battery's 20% floor as 4%.
        soc_pct = 100.0 * _series(log, "battery", "soc")
        # SoC one full day in, i.e. at tomorrow's start -- not today's minimum, which
        # touches the floor on almost every ordinary day and says nothing distinctive.
        recovery = float(soc_pct[HOURS_PER_DAY]) if len(soc_pct) > HOURS_PER_DAY else float(soc_pct[-1])
        if recovery <= advisory_config.battery_recovery_critical_pct:
            items.append(AdvisoryItem(
                kind="battery_critical", forcing=True, magnitude=0.0,
                lines=[f"The battery is not expected to recover overnight -- only about "
                       f"{recovery:.0f}% charge by tomorrow morning. Expect to lean on "
                       "the grid or diesel again tomorrow too."],
            ))
        elif recovery <= advisory_config.battery_recovery_reserve_pct:
            items.append(AdvisoryItem(
                kind="battery_reserve", forcing=False,
                magnitude=advisory_config.battery_recovery_reserve_pct - recovery,
                lines=[f"Battery recovers only partially overnight, to about "
                       f"{recovery:.0f}% by tomorrow morning."],
            ))

    return items


def build_advisory(
    profiles: Profiles,
    day: int,
    config: FarmConfig = DEFAULT_CONFIG,
    feeders: tuple[Feeder, ...] = FEEDERS,
    diesel_unit: DieselUnit = BACKUP_GENSET,
    advisory_config: AdvisoryConfig = AdvisoryConfig(),
) -> AdvisoryBriefing:
    """Everything the optimiser knows about today, ranked down to what fits in a message.

    Reproduces `recommend_irrigation_window`'s search once (unchanged), then runs one
    further simulation AT the chosen timing to read the hourly detail that search discards
    once it has its summary KPIs -- diesel hours and the battery's trajectory.
    """
    advice = recommend_irrigation_window(
        profiles, day, config=config, feeders=feeders, diesel_unit=diesel_unit,
    )
    best = advice.best
    end_hour = best.start_hour + advice.hours_needed
    header = (f"Run the irrigation pump from {best.start_hour:02d}:00 to {end_hour:02d}:00 "
              f"({advice.hours_needed} hours).")

    start = day * HOURS_PER_DAY
    window = slice_profiles(profiles, start, start + 2 * HOURS_PER_DAY)
    chosen = with_pump_at(window, 0, best.start_hour, advice.hours_needed, config.pump_kw)
    log = run_mpc(
        chosen, config, with_wind=config.wind_capacity_kw > 0,
        diesel_unit=diesel_unit, feeders=feeders,
    )

    candidates = [item for item in (
        _irrigation_reasoning(advice, advisory_config),
        _feeder_shift(profiles, day),
    ) if item is not None]
    candidates += _diesel_and_battery(log, config, diesel_unit, advisory_config)

    shown = select_items(candidates, advisory_config.max_items)
    return AdvisoryBriefing(
        day=day, header=header, items=shown, considered=candidates, irrigation=advice,
    )


def daily_advisory(
    profiles: Profiles,
    day: int,
    config: FarmConfig = DEFAULT_CONFIG,
    feeders: tuple[Feeder, ...] = FEEDERS,
    diesel_unit: DieselUnit = BACKUP_GENSET,
    advisory_config: AdvisoryConfig = AdvisoryConfig(),
) -> list[str]:
    """The plain-English lines, ready for `explain.render_advice` -- the same handoff
    `advice.daily_briefing` already had, extended to more than one kind of signal."""
    return build_advisory(
        profiles, day, config, feeders, diesel_unit, advisory_config,
    ).lines
