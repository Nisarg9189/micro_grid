"""Site and economic parameters for a representative Banaskantha farm.

Economic figures are planning assumptions, not measured values. Diesel price and
tariff must be re-checked against current Gujarat rates before any published claim.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DieselUnit:
    """A diesel source, sized and fuelled according to what it actually is.

    A direct-coupled diesel pumpset burns roughly 0.75 L/kWh: ~2.8 L/h to turn a 5 HP
    (3.73 kW) pump. That inefficiency is what makes the status quo cost ~Rs 1.65 lakh a
    year at 600 pump-hours. A proper backup genset is far better, ~0.30 L/kWh, so the two
    must not share one number or whole-farm diesel cost comes out ~2.5x too high.
    """

    max_kw: float
    litres_per_kwh: float


PUMPSET = DieselUnit(max_kw=3.73, litres_per_kwh=0.75)
BACKUP_GENSET = DieselUnit(max_kw=6.0, litres_per_kwh=0.30)


@dataclass(frozen=True)
class Feeder:
    """One physical grid connection.

    Gujarat's Jyotigram scheme runs two separate rural feeders, and the split is the whole
    point: the agricultural feeder is three-phase and rationed to a daily block, while the
    village feeder is single-phase and near-continuous. A 5 HP pump draws more than the
    single-phase connection can deliver, so when the agricultural feeder is down the pump
    cannot simply fall back to the domestic supply. Capping import per feeder is what
    encodes that, and it is what gives storage something to do.
    """

    name: str
    max_import_kw: float
    import_price_per_kwh: float

    # Which load this connection is allowed to serve. Agricultural and domestic supplies
    # are separately sanctioned and separately tariffed -- running a pump off a domestic
    # connection is not a physical impossibility so much as a different contract, and the
    # price difference is exactly why it matters. "all" lets a connection serve both.
    serves: str = "all"


AGRICULTURAL_FEEDER = Feeder("agricultural", max_import_kw=10.0, import_price_per_kwh=1.50)
VILLAGE_FEEDER = Feeder("village", max_import_kw=3.0, import_price_per_kwh=5.00)


@dataclass(frozen=True)
class Economics:
    diesel_price_per_litre: float = 98.39
    co2_kg_per_litre_diesel: float = 2.7

    grid_export_price_per_kwh: float = 0.0
    grid_co2_kg_per_kwh: float = 0.71


@dataclass(frozen=True)
class FarmConfig:
    pump_hp: float = 5.0
    pump_kw: float = 3.73

    household_base_kw: float = 0.4
    dairy_peak_kw: float = 1.2
    cold_storage_kw: float = 0.8

    solar_capacity_kwp: float = 10.0
    wind_capacity_kw: float = 3.0

    battery_capacity_kwh: float = 20.0
    battery_min_soc: float = 0.2
    battery_max_charge_kw: float = 5.0
    battery_max_discharge_kw: float = 5.0
    battery_efficiency: float = 0.95
    battery_init_soc: float = 0.5

    economics: Economics = field(default_factory=Economics)

    def genset_cost_per_kwh(self, unit: DieselUnit) -> float:
        return unit.litres_per_kwh * self.economics.diesel_price_per_litre

    def genset_co2_per_kwh(self, unit: DieselUnit) -> float:
        return unit.litres_per_kwh * self.economics.co2_kg_per_litre_diesel

    @property
    def battery_min_capacity_kwh(self) -> float:
        return self.battery_capacity_kwh * self.battery_min_soc


DEFAULT_CONFIG = FarmConfig()
