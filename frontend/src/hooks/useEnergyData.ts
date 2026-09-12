import { useState, useMemo } from "react";
import type { TimeRange, EnergyDataPoint } from "../types/energy";
import { useSimulationContext } from "./SimulationContext";
import { hourlyData, sevenDayData, thirtyDayData } from "../data/energyData";

export function useEnergyData() {
  const [timeRange, setTimeRange] = useState<TimeRange>("24h");
  const { data: simData, source, isLoading, error, executeSimulation } = useSimulationContext();

  const data = useMemo<EnergyDataPoint[]>(() => {
    if (simData && source === "simulation") {
      const series = simData.series;
      const length = series.load_kw.length;
      let startIdx = 0;
      
      if (timeRange === "24h") {
        startIdx = Math.max(0, length - 24);
      } else {
        startIdx = 0;
      }

      const parsed: EnergyDataPoint[] = [];
      for (let i = startIdx; i < length; i++) {
        parsed.push({
          time: `${(i % 24).toString().padStart(2, '0')}:00`,
          load: series.load_kw[i],
          solar: series.solar_kw[i],
          battery: series.discharge_kw[i] - series.charge_kw[i],
          grid: series.ag_kw[i] + series.village_kw[i],
          diesel: series.diesel_kw[i],
        });
      }
      return parsed;
    }

    // Fallback data
    switch (timeRange) {
      case "7d": return sevenDayData;
      case "30d": return thirtyDayData;
      case "24h":
      default: return hourlyData;
    }
  }, [timeRange, simData, source]);

  return {
    timeRange,
    setTimeRange,
    data,
    loading: isLoading,
    error,
    refresh: executeSimulation,
    source,
  };
}
