import React, { createContext, useContext, useState, useCallback, useEffect } from "react";
import { runSimulation } from "../services/simulationApi";
import type { SimulationResponse } from "../types/api";

export type DataSource = "live" | "simulation" | "demo" | "offline";

interface SimulationContextValue {
  data: SimulationResponse | null;
  source: DataSource;
  isLoading: boolean;
  error: string | null;
  lastUpdated: string | null;
  executeSimulation: () => Promise<void>;
}

const SimulationContext = createContext<SimulationContextValue | null>(null);

export function SimulationProvider({ children }: { children: React.ReactNode }) {
  const [data, setData] = useState<SimulationResponse | null>(null);
  const [source, setSource] = useState<DataSource>("demo"); // starts with demo fallback
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const executeSimulation = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      // 7 days is the minimum required by backend
      const res = await runSimulation({ days: 7 });
      setData(res);
      setSource("simulation");
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err: any) {
      setError(err.message);
      setSource("offline");
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Fetch initial state on mount
  useEffect(() => {
    executeSimulation();
  }, [executeSimulation]);

  return (
    <SimulationContext.Provider value={{ data, source, isLoading, error, lastUpdated, executeSimulation }}>
      {children}
    </SimulationContext.Provider>
  );
}

export function useSimulationContext() {
  const ctx = useContext(SimulationContext);
  if (!ctx) throw new Error("useSimulationContext must be used within SimulationProvider");
  return ctx;
}
