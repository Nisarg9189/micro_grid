import type { SimulationRequest } from "../types/api";
import type { VillageSizingRequest } from "../types/village";

// Every scenario here is one this project actually ran and reported a real result for --
// not a hypothetical. Each one answers a specific question this session tested live.
export interface FarmScenario {
  name: string;
  question: string;
  finding: string;
  overrides: Partial<SimulationRequest>;
}

export const FARM_SCENARIOS: FarmScenario[] = [
  {
    name: "Default farm",
    question: "Baseline: one Palanpur farm, factory-default hardware and prices.",
    finding: "Reference point every other scenario is compared against.",
    overrides: {
      lat: 24.17, lon: 72.43, site: "Palanpur, Banaskantha",
      hub_height: 18, wind: 0, wind_cost_per_kw: 120_000,
      pump_kw: 3.73, household_kw: 0.4, dairy_kw: 1.2, cold_storage_kw: 0.8,
    },
  },
  {
    name: "Coastal wind site",
    question: "Best case for wind: Dwarka coast, 80m shared mast, cheap turbine.",
    finding: "Wind still loses -- a single farm's demand is too small to use the output.",
    overrides: {
      lat: 22.24, lon: 68.97, site: "Dwarka",
      hub_height: 80, wind: 0, wind_cost_per_kw: 55_000,
      pump_kw: 3.73, household_kw: 0.4, dairy_kw: 1.2, cold_storage_kw: 0.8,
    },
  },
  {
    name: "Inflated demand farm",
    question: "What if one farm's load were 10-40x larger?",
    finding: "Diesel use jumps ~40x, but wind still isn't selected -- battery/diesel stay cheaper.",
    overrides: {
      lat: 24.17, lon: 72.43, site: "Palanpur, Banaskantha",
      hub_height: 18, wind: 0, wind_cost_per_kw: 120_000,
      pump_kw: 50, household_kw: 20, dairy_kw: 10, cold_storage_kw: 10,
      ag_kw: 100, village_kw: 50, genset_kw: 60,
    },
  },
  {
    name: "Cheapest wind price",
    question: "Isolate price: what if a turbine cost only Rs 10,000/kW -- near free?",
    finding: "Still 0 kW recommended. This was never a price problem.",
    overrides: {
      lat: 24.17, lon: 72.43, site: "Palanpur, Banaskantha",
      hub_height: 18, wind: 0, wind_cost_per_kw: 10_000,
      pump_kw: 3.73, household_kw: 0.4, dairy_kw: 1.2, cold_storage_kw: 0.8,
    },
  },
  {
    name: "Wind turbine installed (manual)",
    question: "Our AI wouldn't choose this -- but an operator always can. What happens if you install one anyway?",
    finding: "It generates real, visible power (see the Wind Turbine node below) -- it just doesn't earn back its own cost, which is why the optimiser never picks it on its own.",
    overrides: {
      lat: 22.24, lon: 68.97, site: "Dwarka",
      hub_height: 80, wind: 20, wind_cost_per_kw: 55_000,
      pump_kw: 3.73, household_kw: 0.4, dairy_kw: 1.2, cold_storage_kw: 0.8,
    },
  },
];

export interface VillageScenario {
  name: string;
  question: string;
  overrides: VillageSizingRequest;
}

export const VILLAGE_SCENARIOS: VillageScenario[] = [
  {
    name: "Default village",
    question: "100 households, 20 farms, dairy and water supply -- Palanpur, farm-mast wind pricing.",
    overrides: {
      lat: 24.17, lon: 72.43, site: "Palanpur, Banaskantha",
      hub_height: 18, wind_cost_per_kw: 120_000,
    },
  },
  {
    name: "Coastal village (best case for wind)",
    question: "Same village demand, but Dwarka coast, 80m shared mast, Rs 55,000/kW turbine -- every factor stacked in wind's favor at once.",
    overrides: {
      lat: 22.24, lon: 68.97, site: "Dwarka",
      hub_height: 80, wind_cost_per_kw: 55_000,
    },
  },
];
