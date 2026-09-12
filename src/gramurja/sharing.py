"""Does letting a village share surplus actually pay, and who benefits?

The village model aggregates every load onto one bus, which quietly assumes sharing is
already perfect and free. That makes it useless for answering this question: you cannot
price something you have assumed. So this models the village as its actual participants and
runs it twice, changing exactly one parameter.

    independent   every participant stands alone. A farm with surplus curtails it while a
                  household two fields away sits in the dark.
    shared        the same total hardware plus a village line they can push surplus into
                  and draw from.

The participants are deliberately unlike each other, because that is where sharing gets its
value:

    farms        own the panels and the land, pump on their own schedule, and sit on the
                 rationed agricultural feeder with a diesel pumpset behind it
    households   no generation of their own, evening-peaked, on the domestic feeder, and
                 with no backup at all -- when that feeder fails they simply go without
    dairy        a bulk milk cooler with a hard deadline; milk chills when it arrives
    water        drinking-water pumping into a tank, so critical but shiftable

Two things stop the shared case being free by construction, which is the trap here: energy
crossing the line loses a few percent, and every connection has a capacity limit. Without
both, sharing costs nothing and the answer is meaningless.

Households are modelled in blocks rather than individually -- a hundred separate LP
participants would be slow and would pretend to a precision the load model does not have.
What matters for sharing is the mix of kinds, not the meter count.
"""

from dataclasses import dataclass, field

import cvxpy as cp
import numpy as np

from .config import DEFAULT_CONFIG, DieselUnit, FarmConfig
from .profiles import HOURS_PER_DAY
from .weather import WeatherSeries, pv_output_kw

PUMPSET = DieselUnit(max_kw=3.73, litres_per_kwh=0.75)
BATTERY_EFFICIENCY = 0.95


@dataclass(frozen=True)
class Participant:
    name: str
    kind: str                  # farm | household | dairy | water
    solar_kwp: float = 0.0
    battery_kwh: float = 0.0
    genset_kw: float = 0.0
    # Entitlement per connection, in kW. A farm really has both: an agricultural
    # connection for the pump and a domestic one for the farmhouse. Households have only
    # the domestic one, and may never draw agricultural-tariff power.
    ag_kw: float = 0.0
    village_kw: float = 0.0


@dataclass(frozen=True)
class VillageCluster:
    farms: int = 20
    households: int = 100
    household_blocks: int = 5

    solar_kwp_per_farm: float = 3.0
    battery_kwh_per_farm: float = 5.0
    genset_kw_per_farm: float = 6.0
    c_rate: float = 0.25

    household_daily_kwh: float = 2.5
    dairy_chiller_kw: float = 5.0
    dairy_standby_kw: float = 0.8
    water_pump_kw: float = 3.73
    water_hours_per_day: float = 4.0

    ag_kw_per_farm: float = 10.0
    farmhouse_kw: float = 2.0
    ag_tariff: float = 1.50
    village_kw_per_block: float = 12.0
    dairy_connection_kw: float = 6.0
    water_connection_kw: float = 4.0
    village_tariff: float = 5.00

    line_kw: float = 0.0
    transfer_efficiency: float = 0.97

    horizon: int = 24
    voll_inr_per_kwh: float = 100.0
    terminal_soc_value: float = 5.0


@dataclass
class ClusterResult:
    line_kw: float
    demand_kwh: float
    unmet_kwh: float
    solar_used_kwh: float
    curtailed_kwh: float
    ag_kwh: float
    village_kwh: float
    diesel_kwh: float
    transferred_kwh: float
    energy_cost_inr: float
    unmet_by_kind: dict = field(default_factory=dict)
    diesel_by_kind: dict = field(default_factory=dict)
    # Who pushed energy onto the line and who pulled it off, by kind of participant.
    exported_by_kind: dict = field(default_factory=dict)
    imported_by_kind: dict = field(default_factory=dict)
    demand_by_kind: dict = field(default_factory=dict)
    # Village-level hourly series, for looking at how the whole thing behaves.
    hourly: dict = field(default_factory=dict)

    @property
    def diesel_litres(self) -> float:
        return self.diesel_kwh * 0.75

    @property
    def reliability_pct(self) -> float:
        return 100.0 * (self.demand_kwh - self.unmet_kwh) / self.demand_kwh


def build_participants(cluster: VillageCluster) -> list[Participant]:
    """Who is in the village, what they own, and which wire they may use."""
    people = [
        Participant(f"farm {i + 1}", "farm",
                    solar_kwp=cluster.solar_kwp_per_farm,
                    battery_kwh=cluster.battery_kwh_per_farm,
                    genset_kw=cluster.genset_kw_per_farm,
                    ag_kw=cluster.ag_kw_per_farm,
                    village_kw=cluster.farmhouse_kw)
        for i in range(cluster.farms)
    ]
    per_block = cluster.households // cluster.household_blocks
    people += [
        # No panels, no battery, no genset: this is the point. Households are the ones
        # who go dark, and the ones sharing can actually rescue.
        Participant(f"{per_block} homes ({i + 1})", "household",
                    village_kw=cluster.village_kw_per_block)
        for i in range(cluster.household_blocks)
    ]
    people.append(Participant("dairy chilling centre", "dairy",
                              village_kw=cluster.dairy_connection_kw))
    people.append(Participant("water supply", "water",
                              village_kw=cluster.water_connection_kw))
    return people


def participant_loads(
    days: int,
    cluster: VillageCluster,
    people: list[Participant],
    config: FarmConfig = DEFAULT_CONFIG,
    seed: int = 3,
) -> np.ndarray:
    """Hourly demand per participant, shape (participants, steps)."""
    rng = np.random.default_rng(seed)
    steps = days * HOURS_PER_DAY
    hour = np.arange(steps) % HOURS_PER_DAY
    month = (np.arange(steps) // HOURS_PER_DAY % 365) / 365 * 12
    per_block = cluster.households // cluster.household_blocks

    loads = np.zeros((len(people), steps))
    pump_starts = rng.integers(5, 16, size=cluster.farms)
    farm_index = 0

    for row, person in enumerate(people):
        if person.kind == "farm":
            # A farmhouse plus its own animals, plus the pump on its own schedule.
            own = config.household_base_kw + np.where((hour >= 18) & (hour <= 22), 0.3, 0.0)
            own = own + np.where(((hour >= 5) & (hour <= 6)) | ((hour >= 17) & (hour <= 18)),
                                 0.4, 0.05)
            pump = np.zeros(steps)
            for day in range(days):
                m = month[day * HOURS_PER_DAY]
                hours = 3.0 if (m >= 11 or m <= 3) else 2.0 if m <= 5 else 0.5 if m <= 9 else 1.0
                whole = int(hours)
                begin = day * HOURS_PER_DAY + int(pump_starts[farm_index])
                pump[begin:begin + whole] = config.pump_kw
                if hours - whole > 0 and begin + whole < steps:
                    pump[begin + whole] = config.pump_kw * (hours - whole)
            loads[row] = own + pump
            farm_index += 1

        elif person.kind == "household":
            evening = np.exp(-0.5 * ((hour - 20.0) / 2.4) ** 2)
            morning = 0.45 * np.exp(-0.5 * ((hour - 7.0) / 1.6) ** 2)
            shape = 0.25 + morning + 1.65 * evening
            shape = shape / shape.mean()
            mean_kw = per_block * cluster.household_daily_kwh / HOURS_PER_DAY
            loads[row] = np.clip(mean_kw * shape * (1 + 0.04 * rng.standard_normal(steps)), 0, None)

        elif person.kind == "dairy":
            chilling = ((hour >= 7) & (hour <= 9)) | ((hour >= 18) & (hour <= 20))
            loads[row] = np.where(chilling, cluster.dairy_chiller_kw, cluster.dairy_standby_kw)

        elif person.kind == "water":
            hours = int(cluster.water_hours_per_day)
            loads[row] = np.where((hour >= 5) & (hour < 5 + hours), cluster.water_pump_kw, 0.0)

    return loads


class ClusterLP:
    """One receding-horizon LP across every participant, with a line between them.

    Written separately from `mpc.py` because the question is different: this needs a
    balance per participant plus a shared line, where that module needs a balance per
    tariff group. Keeping them apart leaves the validated single-farm path untouched.
    """

    def __init__(self, cluster: VillageCluster, people: list[Participant], economics):
        n, h = len(people), cluster.horizon
        self.n, self.h, self.cluster, self.people = n, h, cluster, people

        col = lambda values: np.array(values, dtype=float).reshape(n, 1)
        battery = col([p.battery_kwh for p in people])
        rate = battery * cluster.c_rate
        genset = col([p.genset_kw for p in people])
        ag_cap = col([p.ag_kw for p in people])
        village_cap = col([p.village_kw for p in people])

        self.load = cp.Parameter((n, h), nonneg=True)
        self.solar = cp.Parameter((n, h), nonneg=True)
        self.ag_up = cp.Parameter(h, nonneg=True)
        self.village_up = cp.Parameter(h, nonneg=True)
        self.soc0 = cp.Parameter(n, nonneg=True)

        self.solar_used = cp.Variable((n, h), nonneg=True)
        self.ag = cp.Variable((n, h), nonneg=True)
        self.village = cp.Variable((n, h), nonneg=True)
        self.diesel = cp.Variable((n, h), nonneg=True)
        self.charge = cp.Variable((n, h), nonneg=True)
        self.discharge = cp.Variable((n, h), nonneg=True)
        self.to_line = cp.Variable((n, h), nonneg=True)
        self.from_line = cp.Variable((n, h), nonneg=True)
        self.unmet = cp.Variable((n, h), nonneg=True)
        self.soc = cp.Variable((n, h + 1), nonneg=True)

        e = BATTERY_EFFICIENCY
        c = [
            self.solar_used <= self.solar,
            self.diesel <= genset,
            self.charge <= rate / e,
            self.discharge <= rate * e,
            self.to_line <= cluster.line_kw,
            self.from_line <= cluster.line_kw,
            self.soc >= battery * 0.20,
            self.soc <= battery,
            self.soc[:, 0] == self.soc0,
            self.soc[:, 1:] == self.soc[:, :-1] + e * self.charge - self.discharge / e,
            # Each participant balances on their own meter.
            self.solar_used + self.ag + self.village + self.diesel + self.discharge
            + self.from_line + self.unmet == self.load + self.charge + self.to_line,
            # The line conserves energy, less distribution loss.
            cp.sum(self.to_line, axis=0) * cluster.transfer_efficiency
            == cp.sum(self.from_line, axis=0),
        ]
        # Feeder entitlement: a household may not draw agricultural-tariff power, and a
        # pump may not run off the domestic connection.
        for step in range(h):
            c.append(self.ag[:, step] <= cp.multiply(ag_cap.flatten(), self.ag_up[step]))
            c.append(self.village[:, step] <= cp.multiply(village_cap.flatten(),
                                                          self.village_up[step]))

        diesel_cost = PUMPSET.litres_per_kwh * economics.diesel_price_per_litre
        cost = (
            cp.sum(cluster.ag_tariff * self.ag)
            + cp.sum(cluster.village_tariff * self.village)
            + cp.sum(diesel_cost * self.diesel)
            + cp.sum(cluster.voll_inr_per_kwh * self.unmet)
            - cluster.terminal_soc_value * cp.sum(self.soc[:, h])
        )
        self.problem = cp.Problem(cp.Minimize(cost), c)

    def step(self, load, solar, ag_up, village_up, soc0) -> dict:
        self.load.value = load
        self.solar.value = solar
        self.ag_up.value = ag_up
        self.village_up.value = village_up
        self.soc0.value = soc0
        self.problem.solve(solver=cp.CLARABEL)
        if self.problem.status not in ("optimal", "optimal_inaccurate"):
            raise RuntimeError(f"cluster LP failed: {self.problem.status}")
        first = lambda v: np.asarray(v.value)[:, 0]
        return {
            "solar_used": first(self.solar_used), "ag": first(self.ag),
            "village": first(self.village), "diesel": first(self.diesel),
            "charge": first(self.charge), "discharge": first(self.discharge),
            "to_line": first(self.to_line), "from_line": first(self.from_line),
            "unmet": first(self.unmet),
        }


def run_cluster(
    weather: WeatherSeries,
    loads: np.ndarray,
    people: list[Participant],
    ag_status: np.ndarray,
    village_status: np.ndarray,
    cluster: VillageCluster,
    config: FarmConfig = DEFAULT_CONFIG,
) -> ClusterResult:
    """Step the village hour by hour, applying only the first hour of each plan."""
    n, steps = loads.shape
    horizon = cluster.horizon

    solar = np.zeros((n, steps))
    for row, person in enumerate(people):
        if person.solar_kwp > 0:
            solar[row] = pv_output_kw(weather, person.solar_kwp)[:steps]

    battery = np.array([p.battery_kwh for p in people], dtype=float)
    soc = battery * 0.5
    lp = ClusterLP(cluster, people, config.economics)

    totals = dict.fromkeys(
        ("solar_used", "ag", "village", "diesel", "transferred", "unmet", "curtailed"), 0.0)
    unmet_kind, diesel_kind = {}, {}
    exported_kind, imported_kind = {}, {}
    kinds = sorted({p.kind for p in people})
    series = {name: np.zeros(steps) for name in
              ("demand", "solar", "ag", "village", "diesel", "discharge", "charge",
               "transferred", "unmet")}

    def win2(a, t):
        block = a[:, t:t + horizon]
        return np.pad(block, ((0, 0), (0, horizon - block.shape[1]))) \
            if block.shape[1] < horizon else block

    def win1(a, t):
        block = a[t:t + horizon]
        return np.concatenate([block, np.zeros(horizon - len(block))]) \
            if len(block) < horizon else block

    for t in range(steps):
        plan = lp.step(win2(loads, t), win2(solar, t),
                       win1(ag_status, t), win1(village_status, t), soc)
        soc = np.clip(soc + BATTERY_EFFICIENCY * plan["charge"]
                      - plan["discharge"] / BATTERY_EFFICIENCY,
                      battery * 0.20, battery)

        totals["solar_used"] += plan["solar_used"].sum()
        totals["curtailed"] += max(0.0, solar[:, t].sum() - plan["solar_used"].sum())
        for key, name in (("ag", "ag"), ("village", "village"), ("diesel", "diesel"),
                          ("unmet", "unmet")):
            totals[name] += plan[key].sum()
        totals["transferred"] += plan["to_line"].sum()

        for row, person in enumerate(people):
            k = person.kind
            if plan["unmet"][row] > 1e-6:
                unmet_kind[k] = unmet_kind.get(k, 0.0) + plan["unmet"][row]
            if plan["diesel"][row] > 1e-6:
                diesel_kind[k] = diesel_kind.get(k, 0.0) + plan["diesel"][row]
            if plan["to_line"][row] > 1e-6:
                exported_kind[k] = exported_kind.get(k, 0.0) + plan["to_line"][row]
            if plan["from_line"][row] > 1e-6:
                imported_kind[k] = imported_kind.get(k, 0.0) + plan["from_line"][row]

        series["demand"][t] = loads[:, t].sum()
        series["solar"][t] = plan["solar_used"].sum()
        series["ag"][t] = plan["ag"].sum()
        series["village"][t] = plan["village"].sum()
        series["diesel"][t] = plan["diesel"].sum()
        series["discharge"][t] = plan["discharge"].sum()
        series["charge"][t] = plan["charge"].sum()
        series["transferred"][t] = plan["to_line"].sum()
        series["unmet"][t] = plan["unmet"].sum()

    diesel_cost = PUMPSET.litres_per_kwh * config.economics.diesel_price_per_litre
    return ClusterResult(
        line_kw=cluster.line_kw,
        demand_kwh=float(loads.sum()),
        unmet_kwh=totals["unmet"],
        solar_used_kwh=totals["solar_used"],
        curtailed_kwh=totals["curtailed"],
        ag_kwh=totals["ag"],
        village_kwh=totals["village"],
        diesel_kwh=totals["diesel"],
        transferred_kwh=totals["transferred"],
        energy_cost_inr=(totals["ag"] * cluster.ag_tariff
                         + totals["village"] * cluster.village_tariff
                         + totals["diesel"] * diesel_cost),
        unmet_by_kind={k: round(v, 1) for k, v in unmet_kind.items()},
        diesel_by_kind={k: round(v * 0.75, 1) for k, v in diesel_kind.items()},
        exported_by_kind={k: round(v, 1) for k, v in exported_kind.items()},
        imported_by_kind={k: round(v, 1) for k, v in imported_kind.items()},
        demand_by_kind={
            k: round(float(loads[[i for i, p in enumerate(people) if p.kind == k]].sum()), 1)
            for k in kinds
        },
        hourly={name: values for name, values in series.items()},
    )
