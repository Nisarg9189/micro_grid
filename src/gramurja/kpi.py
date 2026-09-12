"""KPI extraction from a pymgrid run log."""

from dataclasses import asdict, dataclass

import pandas as pd

from .config import BACKUP_GENSET, DEFAULT_CONFIG, DieselUnit, FarmConfig
from .farm import SOLAR_FIELD, WIND_FIELD


@dataclass
class KPIs:
    demand_kwh: float
    served_kwh: float
    unmet_kwh: float
    reliability_pct: float

    solar_used_kwh: float
    wind_used_kwh: float
    renewable_curtailed_kwh: float
    renewable_fraction_pct: float

    grid_kwh: float
    grid_cost_inr: float

    diesel_kwh: float
    diesel_litres: float
    diesel_cost_inr: float

    total_cost_inr: float
    co2_kg: float

    def as_dict(self) -> dict:
        return asdict(self)


def _column(log: pd.DataFrame, module: str, field: str) -> float:
    """Sum every column for a module/field.

    Column keys gain a module index once more than one module of a type is present
    (two renewables, say), so match on the first and last levels rather than the whole key.
    """
    total = 0.0
    for col in log.columns:
        key = col if isinstance(col, tuple) else (col,)
        if key[0] == module and key[-1] == field:
            total += float(log[col].sum())
    return total


def _grid_cost(log: pd.DataFrame) -> float:
    """Price each feeder's import at its own tariff.

    The subsidised agricultural feeder and the domestic village feeder cost very
    different amounts per kWh, so a single blended price would misstate the bill.
    """
    total = 0.0
    for col in log.columns:
        key = col if isinstance(col, tuple) else (col,)
        if key[0] != "grid" or key[-1] != "grid_import":
            continue
        price_key = key[:-1] + ("import_price_current",)
        if price_key in log.columns:
            total += float((log[col] * log[price_key]).sum())
    return total


def compute_kpis(
    log: pd.DataFrame,
    config: FarmConfig = DEFAULT_CONFIG,
    diesel_unit: DieselUnit = BACKUP_GENSET,
) -> KPIs:
    econ = config.economics

    # Sinks are logged negative in pymgrid; demand is reported as a positive quantity.
    demand_kwh = abs(_column(log, "load", "load_current"))
    # load_met is the load the module asked for, not what reached it: any shortfall is
    # booked separately against the balancing module, so served has to be derived.
    unmet_kwh = _column(log, "balancing", "loss_load")
    served_kwh = demand_kwh - unmet_kwh

    solar_used_kwh = _column(log, "renewable", SOLAR_FIELD)
    wind_used_kwh = _column(log, "renewable", WIND_FIELD)
    curtailed_kwh = _column(log, "renewable", "curtailment")

    grid_kwh = _column(log, "grid", "grid_import")
    diesel_kwh = _column(log, "genset", "genset_production")

    diesel_litres = diesel_kwh * diesel_unit.litres_per_kwh
    diesel_cost = diesel_litres * econ.diesel_price_per_litre
    grid_cost = _grid_cost(log)

    co2_kg = _column(log, "genset", "co2_production") + _column(log, "grid", "co2_production")

    # Share of delivered energy, not of load: renewable_used includes energy routed into
    # the battery, so dividing by load served can exceed 100% once round-trip losses exist.
    renewable_used = solar_used_kwh + wind_used_kwh
    total_supply = renewable_used + grid_kwh + diesel_kwh

    return KPIs(
        demand_kwh=demand_kwh,
        served_kwh=served_kwh,
        unmet_kwh=unmet_kwh,
        reliability_pct=100.0 * served_kwh / demand_kwh if demand_kwh else 0.0,
        solar_used_kwh=solar_used_kwh,
        wind_used_kwh=wind_used_kwh,
        renewable_curtailed_kwh=curtailed_kwh,
        renewable_fraction_pct=100.0 * renewable_used / total_supply if total_supply else 0.0,
        grid_kwh=grid_kwh,
        grid_cost_inr=grid_cost,
        diesel_kwh=diesel_kwh,
        diesel_litres=diesel_litres,
        diesel_cost_inr=diesel_cost,
        total_cost_inr=diesel_cost + grid_cost,
        co2_kg=co2_kg,
    )


def combine_kpis(*parts: KPIs) -> KPIs:
    """Add KPIs from sub-systems simulated separately.

    Percentages are recomputed from the summed totals; averaging them would weight a
    small sub-system the same as a large one.
    """
    total = {
        field: sum(getattr(p, field) for p in parts)
        for field in (
            "demand_kwh", "served_kwh", "unmet_kwh",
            "solar_used_kwh", "wind_used_kwh", "renewable_curtailed_kwh",
            "grid_kwh", "grid_cost_inr",
            "diesel_kwh", "diesel_litres", "diesel_cost_inr",
            "total_cost_inr", "co2_kg",
        )
    }

    renewable_used = total["solar_used_kwh"] + total["wind_used_kwh"]
    supply = renewable_used + total["grid_kwh"] + total["diesel_kwh"]

    return KPIs(
        **total,
        reliability_pct=(
            100.0 * total["served_kwh"] / total["demand_kwh"] if total["demand_kwh"] else 0.0
        ),
        renewable_fraction_pct=100.0 * renewable_used / supply if supply else 0.0,
    )


def compare(baseline: KPIs, optimized: KPIs) -> dict:
    def pct_drop(before: float, after: float) -> float:
        return 100.0 * (before - after) / before if before else 0.0

    return {
        "diesel_litres_saved": baseline.diesel_litres - optimized.diesel_litres,
        "diesel_reduction_pct": pct_drop(baseline.diesel_litres, optimized.diesel_litres),
        "cost_saved_inr": baseline.total_cost_inr - optimized.total_cost_inr,
        "cost_reduction_pct": pct_drop(baseline.total_cost_inr, optimized.total_cost_inr),
        "co2_avoided_kg": baseline.co2_kg - optimized.co2_kg,
        "reliability_change_pct": optimized.reliability_pct - baseline.reliability_pct,
    }
