"""Builds the pymgrid Microgrid for a Banaskantha farm."""

from collections.abc import Sequence

import numpy as np
from pymgrid import Microgrid
from pymgrid.modules import (
    BatteryModule,
    GensetModule,
    GridModule,
    LoadModule,
    RenewableModule,
)

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

SOLAR_FIELD = "solar_used"
WIND_FIELD = "wind_used"


def build_microgrid(
    profiles: Profiles,
    config: FarmConfig = DEFAULT_CONFIG,
    with_solar: bool = True,
    with_wind: bool = True,
    with_battery: bool = True,
    with_genset: bool = True,
    diesel_unit: DieselUnit = BACKUP_GENSET,
    feeders: Sequence[Feeder] = (AGRICULTURAL_FEEDER, VILLAGE_FEEDER),
    forecaster: str | float | None = None,
    forecast_horizon: int = 23,
) -> Microgrid:
    """Assemble the farm microgrid.

    with_genset is off for the domestic half of the status-quo baseline: a diesel pumpset
    turns the pump shaft and cannot power household, dairy or cold-storage load, so those
    loads simply go unserved when the feeder is down.

    Each feeder becomes its own grid module, so import is capped per connection rather
    than pooled. During an agricultural outage only the single-phase village feeder is
    left, and it cannot carry the pump on its own.
    """
    modules = [LoadModule(time_series=profiles.load_kw)]

    if with_solar:
        modules.append(
            RenewableModule(
                time_series=profiles.solar_kw,
                forecaster=forecaster,
                forecast_horizon=forecast_horizon,
                provided_energy_name=SOLAR_FIELD,
            )
        )

    if with_wind:
        modules.append(
            RenewableModule(
                time_series=profiles.wind_kw,
                forecaster=forecaster,
                forecast_horizon=forecast_horizon,
                provided_energy_name=WIND_FIELD,
            )
        )

    if with_battery:
        modules.append(
            BatteryModule(
                min_capacity=config.battery_min_capacity_kwh,
                max_capacity=config.battery_capacity_kwh,
                max_charge=config.battery_max_charge_kw,
                max_discharge=config.battery_max_discharge_kw,
                efficiency=config.battery_efficiency,
                init_soc=config.battery_init_soc,
            )
        )

    for feeder in feeders:
        series = np.column_stack(
            [
                np.full(len(profiles), feeder.import_price_per_kwh),
                np.full(len(profiles), config.economics.grid_export_price_per_kwh),
                profiles.grid_carbon_kg_per_kwh,
                profiles.status_for(feeder),
            ]
        )
        modules.append(
            GridModule(
                max_import=feeder.max_import_kw,
                max_export=0.0,
                time_series=series,
                forecaster=forecaster,
                forecast_horizon=forecast_horizon,
            )
        )

    if with_genset:
        modules.append(
            GensetModule(
                running_min_production=0.0,
                running_max_production=diesel_unit.max_kw,
                genset_cost=config.genset_cost_per_kwh(diesel_unit),
                co2_per_unit=config.genset_co2_per_kwh(diesel_unit),
            )
        )

    return Microgrid(modules)
