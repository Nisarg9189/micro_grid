import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from "recharts";
import type { EnergyDataPoint } from "../../types/energy";
import { CustomTooltip } from "./CustomTooltip";

export interface EnergyAreaChartProps {
  data: EnergyDataPoint[];
  height?: number | string;
}

export function EnergyAreaChart({ data, height = 340 }: EnergyAreaChartProps) {
  return (
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 12, right: 8, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="chartSolarGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#F7931A" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#F7931A" stopOpacity={0.02} />
            </linearGradient>
            <linearGradient id="chartBatteryGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#22C55E" stopOpacity={0.35} />
              <stop offset="95%" stopColor="#22C55E" stopOpacity={0.02} />
            </linearGradient>
            <linearGradient id="chartGridGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.02} />
            </linearGradient>
            <linearGradient id="chartDieselGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#EF4444" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#EF4444" stopOpacity={0.02} />
            </linearGradient>
          </defs>

          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(148, 163, 184, 0.2)" />
          <XAxis
            dataKey="time"
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#64748B", fontSize: 11, fontFamily: "monospace" }}
            dy={8}
          />
          <YAxis
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#64748B", fontSize: 11, fontFamily: "monospace" }}
            unit=" kW"
          />
          <Tooltip content={(props: any) => <CustomTooltip {...props} />} />

          <Area
            type="monotone"
            dataKey="solar"
            name="Solar PV"
            stackId="dispatch"
            stroke="#F7931A"
            strokeWidth={1.8}
            fill="url(#chartSolarGrad)"
          />
          <Area
            type="monotone"
            dataKey="battery"
            name="Battery Storage"
            stackId="dispatch"
            stroke="#22C55E"
            strokeWidth={1.8}
            fill="url(#chartBatteryGrad)"
          />
          <Area
            type="monotone"
            dataKey="grid"
            name="Grid Import"
            stackId="dispatch"
            stroke="#3B82F6"
            strokeWidth={1.8}
            fill="url(#chartGridGrad)"
          />
          <Area
            type="monotone"
            dataKey="diesel"
            name="Diesel Backup"
            stackId="dispatch"
            stroke="#EF4444"
            strokeWidth={1.8}
            fill="url(#chartDieselGrad)"
          />
          <Area
            type="monotone"
            dataKey="load"
            name="Total Load Demand"
            stroke="#0F172A"
            strokeWidth={2.4}
            strokeDasharray="4 4"
            fill="none"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
