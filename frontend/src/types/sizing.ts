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
    // Present since /api/size started running the bounded search agent instead of the
    // exhaustive sweep -- lattice_size is every configuration that COULD have been run,
    // pruned is how many the agent proved couldn't win without simulating them.
    lattice_size?: number;
    pruned?: number;
    agent?: string;
    caveat?: string;
  };
  recommended: SizingCandidate | null;
  candidates: SizingCandidate[];
  message?: string;
}
