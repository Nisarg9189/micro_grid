import {
  Activity,
  Droplets,
  ShieldCheck,
  Leaf
} from "lucide-react";
import type { KPI } from "../types/dashboard";

// Shown only until the real /api/simulate call resolves (see useDashboard.ts) -- the
// figures below match this project's own published farm-scale headline result, not an
// invented placeholder.
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

export const dashboardImages = {
  hero: "https://images.unsplash.com/photo-1509391366360-2e959784a276?auto=format&fit=crop&w=1400&q=85",
  irrigation: "https://images.unsplash.com/photo-1625246333195-78d9c38ad449?auto=format&fit=crop&w=1200&q=85",
  battery: "https://images.unsplash.com/photo-1473341304170-971dccb5ac1e?auto=format&fit=crop&w=1200&q=85",
  village: "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=1400&q=85",
};
