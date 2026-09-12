"""Shared fixtures for the GramUrja test suite.

The KPI tests build pymgrid-shaped logs by hand rather than running a microgrid. That is
deliberate: the bugs these tests exist to catch were arithmetic errors in reading the log,
so the log has to be a known quantity. Running pymgrid to produce it would hide the very
numbers under test behind a dispatch heuristic.

Column shapes are copied from a real run. pymgrid emits
`(module_name, module_number, field)` normally, and drops the module-number level when
every module type is a singleton (`get_log(drop_singleton_key=True)`), leaving
`(module_name, field)`. Both shapes reach `compute_kpis` in this codebase -- the
status-quo baseline uses the two-level form -- so both are exercised here.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gramurja.weather import WeatherSeries  # noqa: E402


def make_log(columns: dict) -> pd.DataFrame:
    """Build a log frame from {column key: value or sequence}.

    Keys may be 2-tuples `(module, field)` or 3-tuples `(module, number, field)`. A frame
    cannot hold both depths at once, so if a call mixes them the 2-tuples are widened to
    module number 0 -- which is what pymgrid would have emitted anyway once any module
    type in the run had a second instance. Scalars are broadcast to a single row so a
    one-hour case reads as one line of setup.
    """
    width = max(len(key) for key in columns)

    def widen(key: tuple) -> tuple:
        return key if len(key) == width else (key[0], 0, *key[1:])

    values = {
        widen(key): (value if isinstance(value, (list, tuple, np.ndarray)) else [value])
        for key, value in columns.items()
    }
    lengths = {len(v) for v in values.values()}
    assert len(lengths) == 1, f"all columns must be the same length, got {lengths}"

    frame = pd.DataFrame({key: list(value) for key, value in values.items()}, dtype=float)
    frame.columns = pd.MultiIndex.from_tuples(list(values))
    return frame


def simple_log(
    *,
    demand: float,
    unmet: float = 0.0,
    solar: float = 0.0,
    wind: float = 0.0,
    curtailed: float = 0.0,
    grid: float = 0.0,
    grid_price: float = 1.50,
    diesel: float = 0.0,
    genset_co2: float = 0.0,
    grid_co2: float = 0.0,
) -> pd.DataFrame:
    """A single-hour, single-module-per-type log in the two-level column shape.

    `load_current` is negative because pymgrid logs sinks negative, and `load_met` is set
    to the full demand on purpose: it is the field that used to be read for reliability,
    and it reports the load *requested* even when that load was shed.
    """
    return make_log(
        {
            ("load", "load_current"): -demand,
            ("load", "load_met"): demand,
            ("balancing", "loss_load"): unmet,
            ("balancing", "overgeneration"): 0.0,
            ("renewable", "solar_used"): solar,
            ("renewable", "wind_used"): wind,
            ("renewable", "curtailment"): curtailed,
            ("grid", "grid_import"): grid,
            ("grid", "import_price_current"): grid_price,
            ("grid", "co2_production"): grid_co2,
            ("genset", "genset_production"): diesel,
            ("genset", "co2_production"): genset_co2,
        }
    )


@pytest.fixture(scope="session")
def clear_day_weather():
    """48 hours of cloudless, hot, lightly breezy weather, built without the network.

    `fetch_actual_weather` caches on disk and hits Open-Meteo on a miss, so the tests
    never call it; a WeatherSeries is just four arrays and is cheaper to state outright.
    """
    steps = 48
    hour = np.arange(steps) % 24
    return WeatherSeries(
        irradiance=np.clip(900.0 * np.sin(np.pi * (hour - 6.5) / 12.0), 0.0, None),
        temperature=np.full(steps, 32.0),
        wind_speed=np.full(steps, 4.0),
        cloud_cover=np.zeros(steps),
    )
