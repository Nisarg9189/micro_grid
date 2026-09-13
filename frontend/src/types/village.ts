import type { SizingCandidate } from "./sizing";

export interface VillageSizingRequest {
  lat?: number;
  lon?: number;
  site?: string;
  year?: number;
  days?: number;
  households?: number;
  farms?: number;
  hub_height?: number;
  wind_cost_per_kw?: number;
  genset_kw?: number;
  diesel_price?: number;
  ag_tariff?: number;
  village_tariff?: number;
  ag_kw?: number;
  village_kw?: number;
  carbon_price?: number;
  grid_carbon?: number;
}

export interface VillageSizingResponse {
  meta: {
    days: number;
    households: number;
    farms: number;
    evaluated: number;
    lattice_size?: number;
    pruned?: number;
    agent?: string;
    caveat?: string;
  };
  recommended: SizingCandidate | null;
  candidates: SizingCandidate[];
  message?: string;
}
