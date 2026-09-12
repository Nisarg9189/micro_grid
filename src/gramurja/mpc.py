"""Receding-horizon dispatch optimiser.

pymgrid ships a ModelPredictiveControl, but it converts the microgrid to a "nonmodular"
form that permits only one module of each type. This farm has two renewables and two
feeders, so that path is unavailable and the linear program is written directly here.

The LP only chooses actions. pymgrid still steps the microgrid and remains the authority
on physics, so an infeasible or over-optimistic plan shows up as unserved load or
overgeneration in the log rather than as a flattering number.

Forecasts are perfect foresight: the controller reads the true future of the profile
arrays. That makes these results an upper bound on what the optimiser can achieve, to be
revisited once Phase 3 supplies real forecasts.
"""

from dataclasses import dataclass

import cvxpy as cp
import numpy as np
import pandas as pd
from pymgrid import Microgrid

from .config import (
    AGRICULTURAL_FEEDER,
    BACKUP_GENSET,
    DEFAULT_CONFIG,
    VILLAGE_FEEDER,
    DieselUnit,
    FarmConfig,
    Feeder,
)
from .farm import build_microgrid
from .forecast import Forecast
from .profiles import Profiles


@dataclass(frozen=True)
class MPCConfig:
    horizon: int = 24

    # Above diesel's marginal cost, so the optimiser prefers burning fuel to shedding load.
    voll_inr_per_kwh: float = 100.0

    battery_wear_inr_per_kwh: float = 0.0

    # Grid (0.71 kg/kWh) and diesel (0.81 kg/kWh) are within a few percent once battery
    # round-trip losses are counted, so pricing carbon barely changes which of the two the
    # optimiser picks. What it does change is how much renewable capacity is worth buying.
    carbon_price_inr_per_kg: float = 0.0

    # Without a value on energy left in the battery the LP empties it at every horizon
    # end, since stored energy is worth nothing beyond the last step it can see.
    terminal_soc_value_inr_per_kwh: float = 5.0


class DispatchLP:
    """The horizon LP, compiled once and re-solved with new parameter values each step."""

    def __init__(
        self,
        config: FarmConfig,
        diesel_unit: DieselUnit,
        feeders: tuple[Feeder, ...],
        mpc_config: MPCConfig,
        has_battery: bool,
        has_genset: bool,
    ):
        h = mpc_config.horizon
        self.horizon = h
        self.feeders = feeders
        self.has_battery = has_battery
        self.has_genset = has_genset

        self.load = cp.Parameter(h, nonneg=True)
        self.renewable = cp.Parameter(h, nonneg=True)
        self.feeder_available = [cp.Parameter(h, nonneg=True) for _ in feeders]
        self.soc_initial = cp.Parameter(nonneg=True)

        self.imports = [cp.Variable(h, nonneg=True) for _ in feeders]
        self.diesel = cp.Variable(h, nonneg=True)
        self.renewable_used = cp.Variable(h, nonneg=True)
        self.unmet = cp.Variable(h, nonneg=True)
        self.charge = cp.Variable(h, nonneg=True)
        self.discharge = cp.Variable(h, nonneg=True)
        self.soc = cp.Variable(h + 1, nonneg=True)

        constraints = [self.renewable_used <= self.renewable]

        for imp, feeder, available in zip(self.imports, feeders, self.feeder_available):
            constraints.append(imp <= feeder.max_import_kw * available)

        genset_cap = diesel_unit.max_kw if has_genset else 0.0
        constraints.append(self.diesel <= genset_cap)

        efficiency = config.battery_efficiency
        if has_battery:
            constraints += [
                self.charge <= config.battery_max_charge_kw / efficiency,
                self.discharge <= config.battery_max_discharge_kw * efficiency,
                self.soc >= config.battery_min_capacity_kwh,
                self.soc <= config.battery_capacity_kwh,
                self.soc[0] == self.soc_initial,
                self.soc[1:] == self.soc[:-1] + efficiency * self.charge - self.discharge / efficiency,
            ]
        else:
            constraints += [self.charge == 0, self.discharge == 0, self.soc == 0]

        supply = (
            self.renewable_used + self.diesel + self.discharge + self.unmet + sum(self.imports)
        )
        constraints.append(supply == self.load + self.charge)

        economics = config.economics
        carbon_price = mpc_config.carbon_price_inr_per_kg
        diesel_cost = diesel_unit.litres_per_kwh * economics.diesel_price_per_litre
        diesel_carbon = diesel_unit.litres_per_kwh * economics.co2_kg_per_litre_diesel
        grid_carbon = economics.grid_co2_kg_per_kwh

        cost = (
            cp.sum((diesel_cost + carbon_price * diesel_carbon) * self.diesel)
            + cp.sum(mpc_config.voll_inr_per_kwh * self.unmet)
            + cp.sum(mpc_config.battery_wear_inr_per_kwh * (self.charge + self.discharge))
            - mpc_config.terminal_soc_value_inr_per_kwh * self.soc[h]
        )
        for imp, feeder in zip(self.imports, feeders):
            cost = cost + cp.sum(
                (feeder.import_price_per_kwh + carbon_price * grid_carbon) * imp
            )

        self.problem = cp.Problem(cp.Minimize(cost), constraints)

    def solve(
        self,
        load: np.ndarray,
        renewable: np.ndarray,
        feeder_status: list[np.ndarray],
        soc_initial: float,
    ) -> dict:
        self.load.value = load
        self.renewable.value = renewable
        self.soc_initial.value = soc_initial
        for parameter, status in zip(self.feeder_available, feeder_status):
            parameter.value = status

        self.problem.solve(solver=cp.CLARABEL)
        if self.problem.status not in ("optimal", "optimal_inaccurate"):
            raise RuntimeError(f"dispatch LP failed: {self.problem.status}")

        return {
            "imports": [float(imp.value[0]) for imp in self.imports],
            "diesel": float(self.diesel.value[0]),
            "battery_net": float(self.discharge.value[0] - self.charge.value[0]),
        }


def _window(
    believed: np.ndarray,
    actual: np.ndarray,
    start: int,
    horizon: int,
) -> np.ndarray:
    """Horizon slice of the forecast, with the current step replaced by the truth.

    The controller measures the present and predicts only the future, so leaving step 0
    forecast would make it wrong about conditions it can see.
    """
    window = believed[start:start + horizon].copy()
    if len(window) < horizon:
        window = np.concatenate([window, np.zeros(horizon - len(window))])
    window[0] = actual[start]
    return window


def run_mpc(
    profiles: Profiles,
    config: FarmConfig = DEFAULT_CONFIG,
    with_solar: bool = True,
    with_wind: bool = True,
    with_battery: bool = True,
    with_genset: bool = True,
    diesel_unit: DieselUnit = BACKUP_GENSET,
    feeders: tuple[Feeder, ...] = (AGRICULTURAL_FEEDER, VILLAGE_FEEDER),
    mpc_config: MPCConfig = MPCConfig(),
    forecast: Forecast | None = None,
    max_steps: int | None = None,
) -> pd.DataFrame:
    """Run the optimiser over the profiles.

    `forecast` is what the controller believes; omit it for perfect foresight, which is an
    upper bound rather than an achievable result.
    """
    microgrid = build_microgrid(
        profiles,
        config,
        with_solar=with_solar,
        with_wind=with_wind,
        with_battery=with_battery,
        with_genset=with_genset,
        diesel_unit=diesel_unit,
        feeders=feeders,
    )

    lp = DispatchLP(config, diesel_unit, feeders, mpc_config, with_battery, with_genset)

    renewable_total = np.zeros(len(profiles))
    if with_solar:
        renewable_total = renewable_total + profiles.solar_kw
    if with_wind:
        renewable_total = renewable_total + profiles.wind_kw

    feeder_series = [profiles.status_for(feeder) for feeder in feeders]
    if forecast is None:
        forecast = Forecast(
            renewable_kw=renewable_total,
            load_kw=profiles.load_kw,
            feeder_status=feeder_series,
        )

    steps = max_steps if max_steps is not None else len(profiles)
    horizon = mpc_config.horizon

    for step in range(steps):
        soc_initial = (
            float(microgrid.modules.battery[0].current_charge)
            if with_battery
            else 0.0
        )
        plan = lp.solve(
            load=_window(forecast.load_kw, profiles.load_kw, step, horizon),
            renewable=_window(forecast.renewable_kw, renewable_total, step, horizon),
            feeder_status=[
                _window(believed, actual, step, horizon)
                for believed, actual in zip(forecast.feeder_status, feeder_series)
            ],
            soc_initial=soc_initial,
        )

        action = {"grid": plan["imports"]}
        if with_genset:
            running = 1.0 if plan["diesel"] > 1e-6 else 0.0
            action["genset"] = [np.array([running, plan["diesel"]])]
        if with_battery:
            action["battery"] = [plan["battery_net"]]

        microgrid.step(action, normalized=False)

    return microgrid.get_log(drop_singleton_key=True)
