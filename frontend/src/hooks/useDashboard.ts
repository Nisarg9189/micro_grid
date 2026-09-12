import { useMemo } from "react";
import type { KPI } from "../types/dashboard";
import { dashboardKPIs } from "../data/dashboardData";
import { useSimulationContext } from "./SimulationContext";
import { Activity, Droplets, ShieldCheck, Leaf } from "lucide-react";

export function useDashboard() {
  // mode lives in SimulationContext now, not here -- AUTO actually debounce-reruns the
  // simulation on every config change there; this used to hold its own copy that nothing
  // but the header's own highlight state ever read.
  const { data: simData, source, mode, setMode } = useSimulationContext();

  const kpis = useMemo<KPI[]>(() => {
    if (simData && source === "simulation") {
      const opt = simData.kpis.optimiser;
      const days = simData.meta.days;
      // The backend is explicit that this is a `days`-long horizon, not an annual
      // total (see meta.caveat) -- a 7-day cost labelled "/ year" would be a real
      // number shown at the wrong scale, which reads as a much larger saving than
      // the simulation actually found. Label the true horizon instead of assuming.
      const period = days === 365 ? "/ year" : `/ ${days}d`;
      return [
        {
          title: days === 365 ? "Annual Energy Cost" : "Energy Cost",
          value: `₹${opt.cost_inr.toLocaleString()}`,
          unit: period,
          change: "OPTIMIZED",
          description: days === 365
            ? "Calculated via LP Dispatch"
            : `${days}-day horizon, not an annual figure`,
          trend: "down",
          tone: "orange",
          icon: Activity,
        },
        {
          title: "Diesel Consumption",
          value: opt.diesel_litres.toLocaleString(),
          unit: `L ${period}`,
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
    return dashboardKPIs; // Fallback shown only until the real simulation resolves.
  }, [simData, source]);

  return {
    mode,
    setMode,
    kpis,
    source,
  };
}
