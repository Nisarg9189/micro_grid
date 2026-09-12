import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from "react";
import { runSimulation } from "../services/simulationApi";
import type { SimulationResponse, SimulationRequest } from "../types/api";
import type { OperatingMode } from "../types/dashboard";
import { DEFAULT_PARAMS } from "../data/presets";

export type DataSource = "live" | "simulation" | "demo" | "offline";
export type SimParams = Required<SimulationRequest>;

// How long to wait after the last config change before an AUTO-mode run fires. Long
// enough that typing a number or clicking through several fields doesn't fire a request
// per keystroke; short enough that it still reads as "the page keeps itself in sync".
const AUTO_RUN_DEBOUNCE_MS = 800;

interface SimulationContextValue {
  params: SimParams;
  setParam: <K extends keyof SimParams>(key: K, value: SimParams[K]) => void;
  setParams: (partial: Partial<SimParams>) => void;
  mode: OperatingMode;
  setMode: (mode: OperatingMode) => void;
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
  const [mode, setMode] = useState<OperatingMode>("auto");
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

  // AUTO mode: a config change re-runs the simulation on its own, after a short debounce,
  // instead of waiting for the "Run the optimiser" button. MANUAL mode does nothing here
  // -- unchanged from before this existed. Skips the very first render, since the mount
  // effect above already fires the initial run.
  const isFirstParamsChange = useRef(true);
  useEffect(() => {
    if (isFirstParamsChange.current) {
      isFirstParamsChange.current = false;
      return;
    }
    if (mode !== "auto") return;
    const timer = setTimeout(() => {
      executeSimulation();
    }, AUTO_RUN_DEBOUNCE_MS);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params, mode]);

  return (
    <SimulationContext.Provider
      value={{
        params, setParam, setParams, mode, setMode,
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
