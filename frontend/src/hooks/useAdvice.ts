import { useState, useCallback } from "react";
import type { IrrigationAdvice } from "../types/advice";
import { getIrrigationAdvice } from "../services/adviceApi";

export type AdviceState = "idle" | "loading" | "success" | "error";

export function useAdvice() {
  const [advice, setAdvice] = useState<IrrigationAdvice | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [state, setState] = useState<AdviceState>("idle");

  const fetchAdvice = useCallback(async () => {
    setLoading(true);
    setError(null);
    setState("loading");

    try {
      const result = await getIrrigationAdvice({ days: 7, advice_day: 5 }); // using defaults that work
      setAdvice(result);
      setState("success");
    } catch (err: any) {
      setError(err.message);
      setState("error");
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    advice,
    loading,
    error,
    state,
    getAdvice: fetchAdvice,
  };
}
