export interface InfrastructureStatus {
  id: string;
  name: string;
  type: "solar" | "battery" | "generator" | "grid";
  capacity: string;
  output?: string;
  status: "active" | "standby" | "offline" | "warning";
  efficiency?: number;
  soc?: number;
  availableEnergy?: string;
  metrics?: { label: string; value: string }[];
}
