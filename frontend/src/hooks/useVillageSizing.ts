import { useState, useCallback } from "react";
import type { VillageSizingRequest, VillageSizingResponse } from "../types/village";
import { getVillageSizing } from "../services/villageApi";

export type VillageSizingState = "idle" | "loading" | "success" | "error";

const BASE_REQUEST: VillageSizingRequest = {
  days: 30,
  households: 100,
  farms: 20,
  genset_kw: 50,
  diesel_price: 98.39,
  ag_tariff: 1.5,
  village_tariff: 5,
  ag_kw: 60,
  village_kw: 50,
  carbon_price: 0,
  grid_carbon: 0.71,
};

export function useVillageSizing() {
  const [sizing, setSizing] = useState<VillageSizingResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [state, setState] = useState<VillageSizingState>("idle");
  const [activeScenario, setActiveScenario] = useState<string | null>(null);

  const run = useCallback(async (scenarioName: string, overrides: VillageSizingRequest) => {
    setLoading(true);
    setError(null);
    setState("loading");
    setActiveScenario(scenarioName);

    try {
      const result = await getVillageSizing({ ...BASE_REQUEST, ...overrides });
      setSizing(result);
      setState("success");
    } catch (err: any) {
      setError(err.message);
      setState("error");
    } finally {
      setLoading(false);
    }
  }, []);

  return { sizing, loading, error, state, activeScenario, run };
}
