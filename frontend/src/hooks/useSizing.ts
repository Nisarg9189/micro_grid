import { useState, useCallback } from "react";
import type { SizingResponse, SizingCandidate } from "../types/sizing";
import { getSizing } from "../services/sizingApi";
import { useSimulationContext } from "./SimulationContext";

export type SizingState = "idle" | "loading" | "success" | "error";

export function useSizing() {
  const { params, setParams, executeSimulation } = useSimulationContext();
  const [sizing, setSizing] = useState<SizingResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [state, setState] = useState<SizingState>("idle");

  const fetchSizing = useCallback(async () => {
    setLoading(true);
    setError(null);
    setState("loading");

    try {
      const result = await getSizing(params);
      setSizing(result);
      setState("success");
    } catch (err: any) {
      setError(err.message);
      setState("error");
    } finally {
      setLoading(false);
    }
  }, [params]);

  // Adopt a candidate's hardware -- solar/wind/battery only, everything else (site,
  // loads, tariffs) stays as the user set it -- then immediately re-run the optimiser
  // on it, the same one-click flow console.html's "Use this hardware" button gives.
  // The merged object is passed straight to executeSimulation rather than relying on
  // setParams landing in state before the run fires.
  const applyCandidate = useCallback((candidate: SizingCandidate) => {
    const next = {
      ...params,
      solar: candidate.solar_kwp,
      wind: candidate.wind_kw,
      battery: candidate.battery_kwh,
    };
    setParams(next);
    executeSimulation(next);
  }, [params, setParams, executeSimulation]);

  return {
    sizing,
    loading,
    error,
    state,
    getSizing: fetchSizing,
    applyCandidate,
  };
}
