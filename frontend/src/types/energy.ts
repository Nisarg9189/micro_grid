export type TimeRange = "24h" | "7d" | "30d";

export interface EnergyDataPoint {
  time: string;
  load: number;
  solar: number;
  battery: number;
  grid: number;
  diesel: number;
}

export interface EnergyFlowSummary {
  solarGenerationKW: number;
  batterySOC: number;
  batteryPowerKW: number;
  gridImportKW: number;
  dieselGenerationKW: number;
  villageLoadKW: number;
  irrigationLoadKW: number;
  mode: "auto" | "manual";
}
