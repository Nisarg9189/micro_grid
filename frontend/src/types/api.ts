export interface SimulationRequest {
  lat?: number;
  lon?: number;
  site?: string;
  year?: number;
  days: number;
  solar?: number;
  wind?: number;
  battery?: number;
  battery_reserve?: number;
  c_rate?: number;
  hub_height?: number;
  genset_kw?: number;
  pump_kw?: number;
  household_kw?: number;
  dairy_kw?: number;
  cold_storage_kw?: number;
  diesel_price?: number;
  ag_tariff?: number;
  village_tariff?: number;
  ag_kw?: number;
  village_kw?: number;
  carbon_price?: number;
  grid_carbon?: number;
  advice_day?: number;
  language?: string;
}

export interface SimulationResponse {
  meta: {
    days: number;
    site: string;
    caveat: string;
  };
  resource: {
    solar_kwh_per_kwp_year: number;
    wind_capacity_factor_pct: number;
    demand_kwh: number;
    peak_kw: number;
  };
  kpis: {
    status_quo: {
      diesel_litres: number;
      cost_inr: number;
      reliability_pct: number;
      unmet_kwh: number;
      co2_kg: number;
      grid_kwh: number;
      renewable_pct: number;
    };
    rules: Record<string, number>;
    optimiser: {
      diesel_litres: number;
      cost_inr: number;
      reliability_pct: number;
      unmet_kwh: number;
      co2_kg: number;
      grid_kwh: number;
      renewable_pct: number;
    };
  };
  series: {
    load_kw: number[];
    solar_kw: number[];
    ag_kw: number[];
    village_kw: number[];
    diesel_kw: number[];
    discharge_kw: number[];
    charge_kw: number[];
    soc: number[];
    ag_available: number[];
    village_available: number[];
    carbon_kg_per_kwh: number[];
  };
}
