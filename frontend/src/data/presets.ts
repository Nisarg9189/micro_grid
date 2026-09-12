import type { SimulationRequest } from "../types/api";

// Mirrors report/console.html's PRESETS and DEFAULTS exactly, so the two evaluator
// surfaces answer the same question the same way for the same inputs.
export interface SitePreset {
  name: string;
  lat: number;
  lon: number;
  site: string;
}

export const SITE_PRESETS: SitePreset[] = [
  { name: "Palanpur", lat: 24.17, lon: 72.43, site: "Palanpur, Banaskantha" },
  { name: "Dwarka", lat: 22.24, lon: 68.97, site: "Dwarka" },
  { name: "Mandvi", lat: 22.83, lon: 69.35, site: "Mandvi, Kutch" },
  { name: "Jamnagar", lat: 22.47, lon: 70.06, site: "Jamnagar" },
];

export const DEFAULT_PARAMS: Required<SimulationRequest> = {
  lat: 24.17,
  lon: 72.43,
  site: "Palanpur, Banaskantha",
  year: 2025,
  days: 30,
  solar: 3,
  wind: 0,
  battery: 5,
  battery_reserve: 0.2,
  c_rate: 0.25,
  hub_height: 18,
  genset_kw: 6,
  pump_kw: 3.73,
  household_kw: 0.4,
  dairy_kw: 1.2,
  cold_storage_kw: 0.8,
  diesel_price: 98.39,
  ag_tariff: 1.5,
  village_tariff: 5,
  ag_kw: 10,
  village_kw: 3,
  carbon_price: 0,
  grid_carbon: 0.71,
  advice_day: 5,
  language: "english",
};
