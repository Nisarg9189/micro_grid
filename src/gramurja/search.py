"""Finding the cheapest viable system without simulating every candidate.

`sizing.sweep` evaluates a full lattice -- 120 configurations at farm scale, each a full
8,760-hour simulation. Every point costs the same to evaluate whether or not it could
possibly win, and most cannot: a 12 kWp array with 30 kWh of storage carries more
annualised capital on its own than the winning system's entire yearly bill.

That observation is the whole method here, and it is exact rather than a heuristic:

    annual_total = annual_capital + annual_energy + annual_carbon

Energy and carbon costs are both non-negative, so **annualised capital alone is a lower
bound on total cost**. Capital is closed-form -- capacities times prices times a capital
recovery factor, no simulation involved -- so it can be computed for every candidate up
front, for free. Any candidate whose capital already exceeds the best feasible total found
so far cannot beat it, and can be skipped without ever being simulated.

So this is branch-and-bound with a provable bound, not a surrogate model or a guided
guess. It searches exactly the same discrete lattice as the sweep and is guaranteed to
return the same optimum -- the only thing that changes is how many simulations that takes.
An approximate search that ran faster and sometimes returned a different recommendation
would be worse than the sweep, not better, which is why there is no approximation in here.

Two practical notes:

**Candidates are evaluated in batches.** The sweep gets parallelism across all 120
configurations at once, so a search that evaluated one at a time could do a third of the
work and still finish later. Batches keep every core busy and make a wall-clock comparison
fair.

**A good incumbent early tightens the bound.** Evaluating in ascending capital order alone
starts with systems that are cheap to build and expensive to run, so the bound stays loose
for a while. A small opening probe of mid-range configurations buys a decent incumbent
first, after which the bound prunes hard.
"""

import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field

from .config import (
    AGRICULTURAL_FEEDER,
    BACKUP_GENSET,
    DEFAULT_CONFIG,
    VILLAGE_FEEDER,
    DieselUnit,
    FarmConfig,
    Feeder,
)
from .profiles import Profiles
from .sizing import (
    CapexAssumptions,
    SizingResult,
    _evaluate_one,
    annual_capital_cost,
)
from .weather import WeatherSeries


@dataclass(frozen=True)
class Candidate:
    solar_kwp: float
    wind_kw: float
    battery_kwh: float

    def label(self) -> str:
        return f"{self.solar_kwp:g} kWp / {self.wind_kw:g} kW / {self.battery_kwh:g} kWh"


@dataclass(frozen=True)
class SearchConfig:
    """How the search is run.

    Defaults match `scripts/optimize_sizing.py` so the comparison is like for like.
    """

    reliability_floor_pct: float = 99.0

    # Annualised capital is compared against `capital + (energy + carbon) * horizon_scale`,
    # not the raw annual_total_inr, so a search run over less than a year still ranks
    # candidates correctly. Left at 1.0 (a full year, so no correction needed), a 30-day
    # request would compare a whole year of capital against 30 days of energy cost and
    # rank "install nothing" as cheapest -- the same failure `/api/size`'s wrapper around
    # `sizing.sweep` already corrects for after the fact. Set this to `365 / days` so the
    # bound the search prunes against is sound at whatever horizon it is actually run over.
    horizon_scale: float = 1.0

    # Candidates evaluated per round. Zero means one per core, which is what keeps the
    # search competitive on wall clock against a sweep that parallelises everything.
    batch: int = 0

    # Mid-range configurations evaluated first, purely to establish a usable incumbent
    # before the bound starts pruning. These are not treated as likely winners -- they
    # are ordinary candidates whose only privilege is going first.
    opening_probes: int = 6

    workers: int | None = None


@dataclass
class SearchResult:
    best: SizingResult | None
    evaluated: list[SizingResult] = field(default_factory=list)
    lattice_size: int = 0
    pruned: list[Candidate] = field(default_factory=list)
    reliability_floor_pct: float = 99.0

    @property
    def evaluations(self) -> int:
        return len(self.evaluated)

    @property
    def skipped(self) -> int:
        return self.lattice_size - self.evaluations

    @property
    def skipped_pct(self) -> float:
        return 100.0 * self.skipped / self.lattice_size if self.lattice_size else 0.0

    # Set from the SearchConfig the run used, so feasible() ranks candidates the same
    # way the search itself did -- not by the unscaled annual_total_inr, which is only
    # correct when horizon_scale is 1.0 (a full year).
    horizon_scale: float = 1.0

    def feasible(self) -> list[SizingResult]:
        """Evaluated candidates that met the reliability floor, cheapest first."""
        return sorted(
            (
                r for r in self.evaluated
                if r.kpis.reliability_pct >= self.reliability_floor_pct
            ),
            key=lambda r: scaled_total(r, self.horizon_scale),
        )


def lattice(
    solar_options: list[float],
    wind_options: list[float],
    battery_options: list[float],
) -> list[Candidate]:
    return [
        Candidate(s, w, b)
        for s in solar_options
        for w in wind_options
        for b in battery_options
    ]


def capital_of(
    candidate: Candidate, assumptions: CapexAssumptions = CapexAssumptions()
) -> float:
    """Annualised capital for a candidate -- closed form, no simulation.

    This is the bound. It is cheap enough to compute for the whole lattice before
    evaluating anything.
    """
    return annual_capital_cost(
        candidate.solar_kwp, candidate.wind_kw, candidate.battery_kwh, assumptions
    )


def scaled_total(result: SizingResult, horizon_scale: float) -> float:
    """Capital plus energy and carbon scaled to a comparable horizon.

    `capital + (energy + carbon) * horizon_scale`, not the raw `annual_total_inr` --
    equal to it when horizon_scale is 1.0 (a full year), and otherwise the same
    per-candidate correction `/api/size` already applies to `sweep`'s results after the
    fact. Capital alone is still a valid lower bound on this: energy, carbon and
    horizon_scale are all non-negative, so the pruning in `search()` stays sound at any
    horizon, not only a full year.
    """
    return result.annual_capital_inr + (result.annual_energy_inr + result.annual_carbon_inr) * horizon_scale


def opening_order(
    candidates: list[Candidate], assumptions: CapexAssumptions, probes: int
) -> list[Candidate]:
    """Candidates in the order they should be evaluated.

    Ascending capital is the order the bound wants, because it lets the search stop the
    moment capital overtakes the incumbent. But the cheapest-capital systems are the ones
    that burn the most diesel, so going straight down that list leaves the incumbent poor
    and the bound loose for a long time.

    So a handful of candidates spread across the middle of the capital range go first.
    They tend to be where the optimum actually sits -- between "buy nothing and burn fuel"
    and "buy everything" -- and a good incumbent early is what makes the bound bite.
    """
    by_capital = sorted(candidates, key=lambda c: capital_of(c, assumptions))
    if probes <= 0 or len(by_capital) <= probes:
        return by_capital

    # Evenly spaced picks across the middle half of the capital range.
    lo, hi = len(by_capital) // 4, (3 * len(by_capital)) // 4
    span = max(hi - lo, 1)
    picks = [by_capital[lo + (i * span) // probes] for i in range(probes)]

    seen = set()
    ordered = []
    for c in picks + by_capital:
        if c not in seen:
            seen.add(c)
            ordered.append(c)
    return ordered


def search(
    profiles: Profiles,
    solar_options: list[float],
    wind_options: list[float],
    battery_options: list[float],
    config: FarmConfig = DEFAULT_CONFIG,
    assumptions: CapexAssumptions = CapexAssumptions(),
    controller: str = "mpc",
    weather_forecast: WeatherSeries | None = None,
    diesel_unit: DieselUnit = BACKUP_GENSET,
    feeders: tuple[Feeder, ...] = (AGRICULTURAL_FEEDER, VILLAGE_FEEDER),
    hub_height_m: float = 18.0,
    search_config: SearchConfig = SearchConfig(),
    progress: bool = True,
) -> SearchResult:
    """Branch-and-bound over the sizing lattice.

    Returns the same optimum `sizing.sweep` would, having simulated fewer candidates.
    """
    candidates = lattice(solar_options, wind_options, battery_options)
    ordered = opening_order(candidates, assumptions, search_config.opening_probes)

    batch = search_config.batch or (os.cpu_count() or 4)
    result = SearchResult(
        best=None,
        lattice_size=len(candidates),
        reliability_floor_pct=search_config.reliability_floor_pct,
        horizon_scale=search_config.horizon_scale,
    )
    best_total = float("inf")
    capital = {c: capital_of(c, assumptions) for c in candidates}

    queue = list(ordered)
    pool = ProcessPoolExecutor(max_workers=search_config.workers)
    try:
        while queue:
            # Anything whose capital already exceeds the best feasible total cannot win,
            # so it never needs simulating. Re-checked each round: the bound only tightens.
            remaining, pruned_now = [], []
            for candidate in queue:
                if capital[candidate] >= best_total:
                    pruned_now.append(candidate)
                else:
                    remaining.append(candidate)
            result.pruned.extend(pruned_now)
            queue = remaining
            if not queue:
                break

            taking, queue = queue[:batch], queue[batch:]
            futures = [
                pool.submit(
                    _evaluate_one,
                    (
                        profiles, c.solar_kwp, c.wind_kw, c.battery_kwh, config,
                        assumptions, controller, weather_forecast, diesel_unit,
                        feeders, hub_height_m,
                    ),
                )
                for c in taking
            ]
            for future in as_completed(futures):
                evaluated = future.result()
                result.evaluated.append(evaluated)
                total = scaled_total(evaluated, search_config.horizon_scale)
                if (
                    evaluated.kpis.reliability_pct >= search_config.reliability_floor_pct
                    and total < best_total
                ):
                    best_total = total
                    result.best = evaluated

            if progress:
                incumbent = f"Rs {best_total:,.0f}" if result.best else "none yet"
                print(
                    f"  {result.evaluations}/{result.lattice_size} evaluated, "
                    f"{len(result.pruned)} pruned, incumbent {incumbent}",
                    flush=True,
                )
    finally:
        pool.shutdown()

    return result
