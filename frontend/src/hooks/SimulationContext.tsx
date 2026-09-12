import React, { createContext, useContext, useState, useCallback, useEffect } from "react";
import { runSimulation } from "../services/simulationApi";
import type { SimulationResponse, SimulationRequest } from "../types/api";
import { DEFAULT_PARAMS } from "../data/presets";

export type DataSource = "live" | "simulation" | "demo" | "offline";
export type SimParams = Required<SimulationRequest>;

interface SimulationContextValue {
  params: SimParams;
  setParam: <K extends keyof SimParams>(key: K, value: SimParams[K]) => void;
  setParams: (partial: Partial<SimParams>) => void;
  data: SimulationResponse | null;
  source: DataSource;
  isLoading: boolean;
  error: string | null;
  lastUpdated: string | null;
  // `override` lets a caller run with a params object that hasn't landed in state yet --
  // needed when applying a sizing recommendation, where setParams() and the follow-up
  // run are triggered in the same action and waiting a render for state to settle would
  // be a real (if usually harmless) race rather than a guarantee.
  executeSimulation: (override?: SimParams) => Promise<void>;
}

const SimulationContext = createContext<SimulationContextValue | null>(null);

export function SimulationProvider({ children }: { children: React.ReactNode }) {
  const [params, setParamsState] = useState<SimParams>(DEFAULT_PARAMS);
  const [data, setData] = useState<SimulationResponse | null>(null);
  const [source, setSource] = useState<DataSource>("demo"); // starts with demo fallback
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const setParam = useCallback(<K extends keyof SimParams>(key: K, value: SimParams[K]) => {
    setParamsState((prev) => ({ ...prev, [key]: value }));
  }, []);

  const setParams = useCallback((partial: Partial<SimParams>) => {
    setParamsState((prev) => ({ ...prev, ...partial }));
  }, []);

  const executeSimulation = useCallback(async (override?: SimParams) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await runSimulation(override ?? params);
      setData(res);
      setSource("simulation");
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err: any) {
      setError(err.message);
      setSource("offline");
    } finally {
      setIsLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params]);

  // Fetch initial state on mount, with the default parameters.
  useEffect(() => {
    executeSimulation();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <SimulationContext.Provider
      value={{
        params, setParam, setParams,
        data, source, isLoading, error, lastUpdated, executeSimulation,
      }}
    >
      {children}
    </SimulationContext.Provider>
  );
}

export function useSimulationContext() {
  const ctx = useContext(SimulationContext);
  if (!ctx) throw new Error("useSimulationContext must be used within SimulationProvider");
  return ctx;
}
