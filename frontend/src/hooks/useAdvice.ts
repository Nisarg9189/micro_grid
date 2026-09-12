import { useState, useCallback } from "react";
import type { IrrigationAdvice } from "../types/advice";
import { getIrrigationAdvice } from "../services/adviceApi";
import { useSimulationContext } from "./SimulationContext";

export type AdviceState = "idle" | "loading" | "success" | "error";

export function useAdvice() {
  const { params } = useSimulationContext();
  const [advice, setAdvice] = useState<IrrigationAdvice | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [state, setState] = useState<AdviceState>("idle");

  const fetchAdvice = useCallback(async () => {
    setLoading(true);
    setError(null);
    setState("loading");

    try {
      // Whatever site, hardware and loads are currently configured -- the same
      // single source of truth /api/simulate reads, so the advice matches the
      // system actually being looked at rather than a fixed default.
      const result = await getIrrigationAdvice(params);
      setAdvice(result);
      setState("success");
    } catch (err: any) {
      setError(err.message);
      setState("error");
    } finally {
      setLoading(false);
    }
  }, [params]);

  return {
    advice,
    loading,
    error,
    state,
    getAdvice: fetchAdvice,
  };
}
