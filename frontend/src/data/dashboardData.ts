import {
  Activity,
  Droplets,
  ShieldCheck,
  Leaf
} from "lucide-react";
import type { KPI, AIRecommendation, SystemHealthItem } from "../types/dashboard";
import type { InfrastructureStatus } from "../types/infrastructure";

export const DEMO_MODE = true;

export const dashboardImages = {
  hero: "https://images.unsplash.com/photo-1509391366360-2e959784a276?auto=format&fit=crop&w=1400&q=85",
  irrigation: "https://images.unsplash.com/photo-1625246333195-78d9c38ad449?auto=format&fit=crop&w=1200&q=85",
  battery: "https://images.unsplash.com/photo-1473341304170-971dccb5ac1e?auto=format&fit=crop&w=1200&q=85",
  village: "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=1400&q=85",
};

export const dashboardKPIs: KPI[] = [
  {
    title: "Annual Energy Cost",
    value: "₹84,709",
    unit: "/ year",
    change: "-49.5%",
    description: "₹83,027 saved vs status quo",
    trend: "down",
    tone: "orange",
    icon: Activity,
  },
  {
    title: "Diesel Consumption",
    value: "184",
    unit: "L / year",
    change: "-83%",
    description: "Reduced from 1,100 L baseline",
    trend: "down",
    tone: "orange",
    icon: Droplets,
  },
  {
    title: "Grid Reliability",
    value: "100.0%",
    unit: "uptime",
    change: "STABLE",
    description: "0.0 kWh unserved load",
    trend: "neutral",
    tone: "green",
    icon: ShieldCheck,
  },
  {
    title: "Carbon Abatement",
    value: "8,290",
    unit: "kg CO₂",
    change: "-31.9%",
    description: "3,892 kg emissions avoided",
    trend: "down",
    tone: "green",
    icon: Leaf,
  },
];

export const optimizerMetrics = {
  status: "OPTIMAL",
  solarUtilization: 92,
  batteryEfficiency: 94,
  dieselAvoided: 83,
  costReduction: 49.5,
  lastRunTime: "Just now",
};

export const defaultRecommendation: AIRecommendation = {
  id: "rec-01",
  title: "Solar Storage Pre-Charge Window",
  description: "Charge battery using available solar during the current low-demand window before evening peak.",
  action: "EXECUTE LP DISPATCH CYCLE",
  impactDailySavings: "₹126 daily saving",
  impactCO2Avoided: "0.8 kg CO₂ avoided",
  confidence: 96.8,
  priority: "high",
};

export const initialInfrastructure: InfrastructureStatus[] = [
  {
    id: "inf-solar",
    name: "Solar Array",
    type: "solar",
    capacity: "3 kWp",
    output: "3.0 kW",
    status: "active",
    efficiency: 98,
    metrics: [
      { label: "Generation", value: "3.0 kW" },
      { label: "Capacity", value: "100%" },
    ],
  },
  {
    id: "inf-battery",
    name: "LFP Storage",
    type: "battery",
    capacity: "5 kWh",
    output: "4.2 kWh Available",
    soc: 84,
    status: "active",
    metrics: [
      { label: "SOC", value: "84%" },
      { label: "Usable", value: "4.2 kWh" },
    ],
  },
  {
    id: "inf-genset",
    name: "Diesel Genset",
    type: "generator",
    capacity: "3.5 kVA",
    status: "standby",
    metrics: [
      { label: "Fuel Saved", value: "916 L" },
      { label: "Cutoff", value: "Conserving" },
    ],
  },
  {
    id: "inf-grid",
    name: "DISCOM Interface",
    type: "grid",
    capacity: "Rural Feeder",
    output: "Synced (50.02 Hz)",
    status: "active",
    metrics: [
      { label: "ToD Tariff", value: "₹4.20/unit" },
      { label: "Power Factor", value: "0.98" },
    ],
  },
];

export const systemHealthList: SystemHealthItem[] = [
  { id: "h-1", name: "Solar Controller", status: "online", detail: "Active MPPT tracking" },
  { id: "h-2", name: "Battery Controller", status: "online", detail: "Cell balance 99.4%" },
  { id: "h-3", name: "AI Optimizer", status: "online", detail: "LP Solver CBC active" },
  { id: "h-4", name: "Grid Interface", status: "online", detail: "50.02 Hz / PF 0.98" },
  { id: "h-5", name: "Genset Relay", status: "standby", detail: "Cutoff for fuel conservation" },
];

export const technicalSpecs = {
  solver: "PuLP / CBC",
  terminalId: "GRM-9189-IN",
  frequency: "50.02 Hz",
  powerFactor: "0.98",
  tariff: "₹4.20 / unit",
};
