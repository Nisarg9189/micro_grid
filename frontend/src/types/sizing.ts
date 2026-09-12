export interface SizingCandidate {
  solar_kwp: number;
  wind_kw: number;
  battery_kwh: number;
  diesel_litres: number;
  reliability_pct: number;
  capital_inr: number;
  energy_inr: number;
  total_inr: number;
  renewable_pct: number;
}

export interface SizingResponse {
  meta: {
    days: number;
    evaluated: number;
    caveat?: string;
  };
  recommended: SizingCandidate | null;
  candidates: SizingCandidate[];
  message?: string;
}
