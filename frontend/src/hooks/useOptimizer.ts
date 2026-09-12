import { useCallback, useMemo } from "react";
import type { OptimizationState } from "../types/dashboard";
import { useSimulationContext } from "./SimulationContext";

export function useOptimizer() {
  const { data: simData, isLoading, error, executeSimulation, lastUpdated } = useSimulationContext();

  const state = useMemo<OptimizationState>(() => {
    if (isLoading) return "optimizing";
    if (error) return "error";
    if (simData) return "success";
    return "idle";
  }, [isLoading, error, simData]);

  const currentStep = useMemo(() => {
    if (isLoading) return "RUNNING OPTIMIZATION...";
    if (error) return "OPTIMIZATION FAILED";
    if (simData) return "OPTIMAL DISPATCH FOUND";
    return "READY";
  }, [isLoading, error, simData]);

  // Only fields the backend actually reports. It does not return solver time or a
  // constraint count, so those are left out entirely rather than filled with a
  // plausible-looking placeholder -- a number that looks like solver output but isn't
  // is exactly the failure mode this project's backend has been built to avoid.
  const metrics = useMemo(() => ({
    horizon: simData ? `${simData.meta.days} days` : "-",
    lastRunTime: lastUpdated || "-",
  }), [simData, lastUpdated]);

  const execute = useCallback(async () => {
    await executeSimulation();
  }, [executeSimulation]);

  return {
    state,
    currentStep,
    lastOptimized: lastUpdated || "Never",
    metrics,
    errorMessage: error,
    execute,
  };
}
