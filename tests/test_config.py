"""Parameter invariants and the landmines hiding in them.

Nothing here is arithmetic in the KPI sense; these are the assumptions the rest of the
model is entitled to make about its own configuration. They are worth pinning because two
of them are silent: a zero capacity divides by zero, and the pumpset constant is written
out twice in two different modules.
"""

import numpy as np
import pytest

from gramurja import config as config_module
from gramurja.config import (
    AGRICULTURAL_FEEDER,
    BACKUP_GENSET,
    DEFAULT_CONFIG,
    PUMPSET,
    VILLAGE_FEEDER,
    FarmConfig,
)
from gramurja.profiles import generate_profiles
from gramurja.sizing import _scaled_profiles
from gramurja.weather import WeatherSeries, wind_output_kw


# --------------------------------------------------------------------------------------
# The diesel split
# --------------------------------------------------------------------------------------

def test_the_two_diesel_presets_do_not_share_a_fuel_rate():
    """Sharing one rate overstates whole-farm diesel cost roughly 2.5-fold."""
    assert PUMPSET.litres_per_kwh == pytest.approx(0.75)
    assert BACKUP_GENSET.litres_per_kwh == pytest.approx(0.30)
    assert PUMPSET.litres_per_kwh / BACKUP_GENSET.litres_per_kwh == pytest.approx(2.5)


def test_the_pumpset_is_sized_to_a_5hp_pump():
    """5 HP is 3.73 kW, and the pump load in the profiles is the same number."""
    assert PUMPSET.max_kw == pytest.approx(3.73, abs=0.01)
    assert DEFAULT_CONFIG.pump_kw == pytest.approx(PUMPSET.max_kw)
    assert DEFAULT_CONFIG.pump_hp * 0.7457 == pytest.approx(DEFAULT_CONFIG.pump_kw, abs=0.01)


def test_the_cluster_pumpset_matches_the_config_pumpset():
    """`sharing.py` restates the pumpset rather than importing it.

    Two definitions of the same physical unit will eventually disagree, and the cluster's
    diesel litres and diesel cost both key off its copy.
    """
    from gramurja.sharing import PUMPSET as CLUSTER_PUMPSET

    assert CLUSTER_PUMPSET.litres_per_kwh == pytest.approx(PUMPSET.litres_per_kwh)
    assert CLUSTER_PUMPSET.max_kw == pytest.approx(PUMPSET.max_kw)


@pytest.mark.parametrize("unit", [PUMPSET, BACKUP_GENSET])
def test_diesel_cost_and_carbon_scale_with_the_units_fuel_rate(unit):
    econ = DEFAULT_CONFIG.economics
    assert DEFAULT_CONFIG.genset_cost_per_kwh(unit) == pytest.approx(
        unit.litres_per_kwh * econ.diesel_price_per_litre
    )
    assert DEFAULT_CONFIG.genset_co2_per_kwh(unit) == pytest.approx(
        unit.litres_per_kwh * econ.co2_kg_per_litre_diesel
    )


def test_diesel_is_far_dearer_per_kwh_than_either_feeder():
    """The arbitrage the optimiser exists to exploit, stated as an ordering."""
    diesel = DEFAULT_CONFIG.genset_cost_per_kwh(PUMPSET)
    assert AGRICULTURAL_FEEDER.import_price_per_kwh < VILLAGE_FEEDER.import_price_per_kwh
    assert VILLAGE_FEEDER.import_price_per_kwh < diesel
    assert diesel / AGRICULTURAL_FEEDER.import_price_per_kwh > 15.0


# --------------------------------------------------------------------------------------
# The feeders
# --------------------------------------------------------------------------------------

def test_the_village_feeder_cannot_carry_a_5hp_pump():
    """The single-phase domestic connection is what makes storage worth anything.

    If the village feeder could run the pump, an agricultural outage would cost nothing
    and the battery would have no job.
    """
    assert VILLAGE_FEEDER.max_import_kw < DEFAULT_CONFIG.pump_kw
    assert AGRICULTURAL_FEEDER.max_import_kw > DEFAULT_CONFIG.pump_kw


def test_battery_floor_follows_the_minimum_state_of_charge():
    assert DEFAULT_CONFIG.battery_min_capacity_kwh == pytest.approx(
        DEFAULT_CONFIG.battery_capacity_kwh * DEFAULT_CONFIG.battery_min_soc
    )


# --------------------------------------------------------------------------------------
# The zero-capacity landmine
# --------------------------------------------------------------------------------------

def test_wind_capacity_must_stay_non_zero_in_the_base_config():
    """`_scaled_profiles` divides the wind series by the base config's capacity.

    Setting `wind_capacity_kw = 0` to express "this farm has no turbine" therefore breaks
    every sizing candidate, including the wind-free ones, rather than producing zeros. The
    way to exclude wind is `wind_kw=0` on the candidate, which the base config still
    divides correctly.
    """
    assert DEFAULT_CONFIG.wind_capacity_kw > 0.0
    assert DEFAULT_CONFIG.solar_capacity_kwp > 0.0


def test_scaled_profiles_scales_both_resources_linearly():
    base = FarmConfig()
    profiles = generate_profiles(days=1, config=base)

    doubled = _scaled_profiles(profiles, base, base.solar_capacity_kwp * 2,
                               base.wind_capacity_kw * 3)

    assert doubled.solar_kw == pytest.approx(profiles.solar_kw * 2)
    assert doubled.wind_kw == pytest.approx(profiles.wind_kw * 3)
    # Load is untouched: sizing changes supply, not demand.
    assert doubled.load_kw == pytest.approx(profiles.load_kw)


def test_a_wind_free_candidate_is_expressed_as_zero_wind_kw_not_zero_capacity():
    base = FarmConfig()
    profiles = generate_profiles(days=1, config=base)

    no_wind = _scaled_profiles(profiles, base, base.solar_capacity_kwp, 0.0)
    assert np.all(no_wind.wind_kw == 0.0)


def test_a_zero_capacity_base_config_divides_by_zero():
    """Documenting the landmine rather than the fix: this is a raise, not a wrong number.

    Left as a passing test because it is the behaviour a caller has to know about -- the
    alternative, silently returning zeros, would make every wind sizing result wrong
    without saying so.
    """
    base = FarmConfig(wind_capacity_kw=0.0)
    profiles = generate_profiles(days=1, config=base)

    with pytest.raises(ZeroDivisionError):
        _scaled_profiles(profiles, base, base.solar_capacity_kwp, 0.0)


def test_wind_output_itself_guards_against_zero_capacity():
    """`wind_output_kw` has the guard `_scaled_profiles` lacks."""
    weather = WeatherSeries(
        irradiance=np.zeros(4),
        temperature=np.full(4, 30.0),
        wind_speed=np.full(4, 8.0),
        cloud_cover=np.zeros(4),
    )
    assert np.all(wind_output_kw(weather, 0.0) == 0.0)
    assert wind_output_kw(weather, 3.0).max() > 0.0


# --------------------------------------------------------------------------------------
# Provenance
# --------------------------------------------------------------------------------------

def test_economic_assumptions_are_stated_as_planning_figures():
    """The module docstring is the only place these are labelled as assumptions.

    It is load-bearing: every cost figure in the pitch traces back to these two numbers,
    and dropping the caveat would turn a planning assumption into a claimed measurement.
    """
    assert "not measured values" in config_module.__doc__
    assert DEFAULT_CONFIG.economics.diesel_price_per_litre > 0.0
    assert DEFAULT_CONFIG.economics.co2_kg_per_litre_diesel > 0.0
