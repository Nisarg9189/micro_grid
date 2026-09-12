"""Derive solar, wind and battery sizing from the load profile.

Sizing is chosen the way it is in practice: minimise annualised total cost -- capital
recovered over each asset's life, plus O&M, fuel and grid -- subject to a floor on
reliability. Capacity that buys no cost reduction is not installed, so the answer comes
out of the 8,760-hour profile rather than being assumed up front.

Capital costs below are Indian small-system planning figures and are assumptions, not
quotes. Re-check them against current vendor pricing before publishing a payback number.
"""

from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, replace

from .baseline import run_rule_based, run_status_quo
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
from .forecast import build_forecast
from .kpi import KPIs, compute_kpis
from .mpc import MPCConfig, run_mpc
from .profiles import Profiles
from .weather import WeatherSeries

BATTERY_C_RATE = 0.25


@dataclass(frozen=True)
class CapexAssumptions:
    solar_inr_per_kwp: float = 50_000.0
    wind_inr_per_kw: float = 120_000.0
    battery_inr_per_kwh: float = 18_000.0

    solar_life_years: int = 25
    wind_life_years: int = 20
    battery_life_years: int = 10

    solar_om_rate: float = 0.01
    wind_om_rate: float = 0.03
    battery_om_rate: float = 0.01

    discount_rate: float = 0.09
    carbon_price_inr_per_kg: float = 0.0


@dataclass
class SizingResult:
    solar_kwp: float
    wind_kw: float
    battery_kwh: float
    kpis: KPIs
    annual_capital_inr: float
    annual_energy_inr: float
    annual_carbon_inr: float

    @property
    def annual_total_inr(self) -> float:
        return self.annual_capital_inr + self.annual_energy_inr + self.annual_carbon_inr


def capital_recovery_factor(rate: float, years: int) -> float:
    if rate == 0:
        return 1.0 / years
    growth = (1 + rate) ** years
    return rate * growth / (growth - 1)


def annual_capital_cost(
    solar_kwp: float,
    wind_kw: float,
    battery_kwh: float,
    assumptions: CapexAssumptions = CapexAssumptions(),
) -> float:
    a = assumptions
    items = [
        (solar_kwp * a.solar_inr_per_kwp, a.solar_life_years, a.solar_om_rate),
        (wind_kw * a.wind_inr_per_kw, a.wind_life_years, a.wind_om_rate),
        (battery_kwh * a.battery_inr_per_kwh, a.battery_life_years, a.battery_om_rate),
    ]
    return sum(
        capex * capital_recovery_factor(a.discount_rate, life) + capex * om
        for capex, life, om in items
    )


def _scaled_profiles(
    profiles: Profiles,
    base_config: FarmConfig,
    solar_kwp: float,
    wind_kw: float,
) -> Profiles:
    """Solar and wind output scale linearly with installed capacity."""
    return replace(
        profiles,
        solar_kw=profiles.solar_kw * (solar_kwp / base_config.solar_capacity_kwp),
        wind_kw=profiles.wind_kw * (wind_kw / base_config.wind_capacity_kw),
    )


def evaluate(
    profiles: Profiles,
    solar_kwp: float,
    wind_kw: float,
    battery_kwh: float,
    config: FarmConfig = DEFAULT_CONFIG,
    assumptions: CapexAssumptions = CapexAssumptions(),
    controller: str = "rbc",
    weather_forecast: WeatherSeries | None = None,
    diesel_unit: DieselUnit = BACKUP_GENSET,
    feeders: tuple[Feeder, ...] = (AGRICULTURAL_FEEDER, VILLAGE_FEEDER),
    hub_height_m: float = 18.0,
) -> SizingResult:
    """Size against a given controller.

    Sizing and control are coupled: a myopic controller never charges from the cheap
    agricultural feeder to displace diesel later, so it undervalues storage and sizes it
    away. The controller used here therefore changes the answer, not just the cost.
    """
    sized_config = replace(
        config,
        battery_capacity_kwh=battery_kwh,
        battery_max_charge_kw=battery_kwh * BATTERY_C_RATE,
        battery_max_discharge_kw=battery_kwh * BATTERY_C_RATE,
    )
    scaled = _scaled_profiles(profiles, config, solar_kwp, wind_kw)
    present = dict(
        with_solar=solar_kwp > 0,
        with_wind=wind_kw > 0,
        with_battery=battery_kwh > 0,
    )

    if controller == "mpc":
        forecast = None
        if weather_forecast is not None:
            # Rebuilt per candidate rather than scaled: solar and wind do not scale
            # together, so one ratio applied to their sum would be wrong.
            forecast = build_forecast(
                scaled,
                feeders,
                weather_forecast,
                solar_kwp if solar_kwp > 0 else 0.0,
                wind_kw if wind_kw > 0 else 0.0,
                hub_height_m=hub_height_m,
            )
        log = run_mpc(
            scaled,
            sized_config,
            diesel_unit=diesel_unit,
            feeders=feeders,
            forecast=forecast,
            mpc_config=MPCConfig(carbon_price_inr_per_kg=assumptions.carbon_price_inr_per_kg),
            **present,
        )
    else:
        log = run_rule_based(
            build_microgrid(
                scaled, sized_config, diesel_unit=diesel_unit, feeders=feeders, **present
            )
        )
    kpis = compute_kpis(log, sized_config, diesel_unit=diesel_unit)

    return SizingResult(
        solar_kwp=solar_kwp,
        wind_kw=wind_kw,
        battery_kwh=battery_kwh,
        kpis=kpis,
        annual_capital_inr=annual_capital_cost(solar_kwp, wind_kw, battery_kwh, assumptions),
        annual_energy_inr=kpis.total_cost_inr,
        annual_carbon_inr=kpis.co2_kg * assumptions.carbon_price_inr_per_kg,
    )


def _evaluate_one(args) -> SizingResult:
    return evaluate(*args)


def sweep(
    profiles: Profiles,
    solar_options: list[float],
    wind_options: list[float],
    battery_options: list[float],
    config: FarmConfig = DEFAULT_CONFIG,
    assumptions: CapexAssumptions = CapexAssumptions(),
    workers: int | None = None,
    controller: str = "rbc",
    weather_forecast: WeatherSeries | None = None,
    progress_every: int = 20,
    diesel_unit: DieselUnit = BACKUP_GENSET,
    feeders: tuple[Feeder, ...] = (AGRICULTURAL_FEEDER, VILLAGE_FEEDER),
    hub_height_m: float = 18.0,
) -> list[SizingResult]:
    jobs = [
        (
            profiles, s, w, b, config, assumptions, controller,
            weather_forecast, diesel_unit, feeders, hub_height_m,
        )
        for s in solar_options
        for w in wind_options
        for b in battery_options
    ]

    results = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_evaluate_one, job) for job in jobs]
        for done, future in enumerate(as_completed(futures), start=1):
            results.append(future.result())
            if progress_every and done % progress_every == 0:
                print(f"  {done}/{len(jobs)} configurations", flush=True)
    return results


def recommend(
    results: list[SizingResult],
    min_reliability_pct: float = 99.0,
) -> SizingResult | None:
    feasible = [r for r in results if r.kpis.reliability_pct >= min_reliability_pct]
    if not feasible:
        return None
    return min(feasible, key=lambda r: r.annual_total_inr)


def status_quo_reference(
    profiles: Profiles,
    config: FarmConfig = DEFAULT_CONFIG,
) -> KPIs:
    return run_status_quo(profiles, config)
