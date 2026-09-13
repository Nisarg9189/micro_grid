import type { LucideIcon } from "lucide-react";

export type OptimizationState = "idle" | "optimizing" | "success" | "error";

export interface KPI {
  title: string;
  value: string;
  unit?: string;
  change?: string;
  description?: string;
  trend?: "up" | "down" | "neutral";
  tone?: "orange" | "green" | "blue";
  icon: LucideIcon;
}

export interface AIRecommendation {
  id: string;
  title: string;
  description: string;
  action: string;
  impactDailySavings: string;
  impactCO2Avoided: string;
  confidence: number;
  priority: "low" | "medium" | "high";
}

export interface SystemHealthItem {
  id: string;
  name: string;
  status: "online" | "standby" | "warning" | "offline";
  detail?: string;
}
