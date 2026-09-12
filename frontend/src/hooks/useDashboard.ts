import { useState, useCallback, useMemo } from "react";
import type { OperatingMode, KPI } from "../types/dashboard";
import { dashboardKPIs, initialInfrastructure, systemHealthList } from "../data/dashboardData";
import { useSimulationContext } from "./SimulationContext";
import { Activity, Droplets, ShieldCheck, Leaf } from "lucide-react";

// For generator and calibration simulations
const toggleGenerator = async (target: boolean) => {
  await new Promise((r) => setTimeout(r, 800));
  return { running: target };
};
const calibrateSensors = async () => {
  await new Promise((r) => setTimeout(r, 1400));
  return { message: "Pyranometer sensors calibrated (Zero offset normalized)" };
};

export function useDashboard() {
  const [mode, setMode] = useState<OperatingMode>("auto");
  const [generatorRunning, setGeneratorRunning] = useState(false);
  const [isGeneratorPending, setIsGeneratorPending] = useState(false);
  const [isCalibrating, setIsCalibrating] = useState(false);
  const [calibrationFeedback, setCalibrationFeedback] = useState<string | null>(null);

  const { data: simData, source } = useSimulationContext();

  const kpis = useMemo<KPI[]>(() => {
    if (simData && source === "simulation") {
      const opt = simData.kpis.optimiser;
      return [
        {
          title: "Annual Energy Cost",
          value: `₹${opt.cost_inr.toLocaleString()}`,
          unit: "/ year",
          change: "OPTIMIZED",
          description: "Calculated via LP Dispatch",
          trend: "down",
          tone: "orange",
          icon: Activity,
        },
        {
          title: "Diesel Consumption",
          value: opt.diesel_litres.toLocaleString(),
          unit: "L / year",
          change: "OPTIMIZED",
          description: "Reduced via solar/battery",
          trend: "down",
          tone: "orange",
          icon: Droplets,
        },
        {
          title: "Grid Reliability",
          value: `${opt.reliability_pct}%`,
          unit: "uptime",
          change: opt.reliability_pct >= 99 ? "STABLE" : "WARNING",
          description: `${opt.unmet_kwh.toFixed(1)} kWh unserved load`,
          trend: opt.reliability_pct >= 99 ? "neutral" : "down",
          tone: opt.reliability_pct >= 99 ? "green" : "orange",
          icon: ShieldCheck,
        },
        {
          title: "Carbon Emissions",
          value: opt.co2_kg.toLocaleString(),
          unit: "kg CO₂",
          change: "OPTIMIZED",
          description: `${opt.renewable_pct}% Renewable Fraction`,
          trend: "down",
          tone: "green",
          icon: Leaf,
        }
      ];
    }
    return dashboardKPIs; // Fallback
  }, [simData, source]);

  const handleModeChange = useCallback((newMode: OperatingMode) => {
    setMode(newMode);
  }, []);

  const handleGeneratorToggle = useCallback(async (targetState: boolean) => {
    setIsGeneratorPending(true);
    try {
      const res = await toggleGenerator(targetState);
      setGeneratorRunning(res.running);
    } finally {
      setIsGeneratorPending(false);
    }
  }, []);

  const handleCalibrate = useCallback(async () => {
    setIsCalibrating(true);
    setCalibrationFeedback(null);
    try {
      const res = await calibrateSensors();
      setCalibrationFeedback(res.message);
      setTimeout(() => setCalibrationFeedback(null), 4000);
    } finally {
      setIsCalibrating(false);
    }
  }, []);

  return {
    mode,
    setMode: handleModeChange,
    generatorRunning,
    isGeneratorPending,
    toggleGenerator: handleGeneratorToggle,
    isCalibrating,
    calibrationFeedback,
    calibrate: handleCalibrate,
    infrastructure: initialInfrastructure, // Real physical backend has no infrastructure telemetry
    health: systemHealthList, // Simulated health status
    kpis,
    source,
  };
}
