"""Baseline controllers.

Two reference points are needed to make a savings claim meaningful:

status quo  - rationed grid plus a diesel pumpset, no solar, wind or battery. This is what
              the farmer runs today and is where the Rs/year diesel figure comes from.
smart rules - the full solar + wind + battery microgrid under rule-based control. This is a
              non-AI system, so the gap between it and the optimizer isolates what the
              optimization actually contributes, separate from the hardware.
"""

from dataclasses import replace

import pandas as pd
from pymgrid import Microgrid
from pymgrid.algos import RuleBasedControl

from .config import (
    AGRICULTURAL_FEEDER,
    BACKUP_GENSET,
    DEFAULT_CONFIG,
    PUMPSET,
    VILLAGE_FEEDER,
    FarmConfig,
)
from .farm import build_microgrid
from .kpi import KPIs, combine_kpis, compute_kpis
from .profiles import Profiles


def run_rule_based(microgrid: Microgrid, max_steps: int | None = None) -> pd.DataFrame:
    controller = RuleBasedControl(microgrid)
    controller.run(max_steps=max_steps)
    return controller.microgrid.get_log(drop_singleton_key=True)


def run_status_quo(profiles: Profiles, config: FarmConfig = DEFAULT_CONFIG) -> KPIs:
    """Today's setup, simulated as the two separate systems it physically is.

    Irrigation sits on the rationed agricultural feeder with a diesel pumpset behind it.
    Everything else sits on the village feeder with no backup at all, because a pumpset
    drives a pump shaft and cannot power a milking machine or a cold store. Modelling both
    on one bus was charging pumpset fuel rates to domestic load and overstating the
    baseline roughly fourfold.
    """
    irrigation_kpis = compute_kpis(
        run_rule_based(
            build_microgrid(
                replace(profiles, load_kw=profiles.pump_kw),
                config,
                with_solar=False,
                with_wind=False,
                with_battery=False,
                diesel_unit=PUMPSET,
                feeders=(AGRICULTURAL_FEEDER,),
            )
        ),
        config,
        diesel_unit=PUMPSET,
    )

    domestic_kpis = compute_kpis(
        run_rule_based(
            build_microgrid(
                replace(profiles, load_kw=profiles.load_kw - profiles.pump_kw),
                config,
                with_solar=False,
                with_wind=False,
                with_battery=False,
                with_genset=False,
                feeders=(VILLAGE_FEEDER,),
            )
        ),
        config,
    )

    return combine_kpis(irrigation_kpis, domestic_kpis)


def run_smart_rules(profiles: Profiles, config: FarmConfig = DEFAULT_CONFIG) -> KPIs:
    microgrid = build_microgrid(
        profiles,
        config,
        with_solar=True,
        with_wind=True,
        with_battery=True,
        diesel_unit=BACKUP_GENSET,
    )
    return compute_kpis(run_rule_based(microgrid), config, diesel_unit=BACKUP_GENSET)
