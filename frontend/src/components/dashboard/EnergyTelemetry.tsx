import { Card } from "../ui/Card";
import { EnergyAreaChart } from "../charts/EnergyAreaChart";
import type { EnergyDataPoint, TimeRange } from "../../types/energy";
import { LoadingSkeleton } from "../ui/LoadingSkeleton";
import type { DataSource } from "../../hooks/SimulationContext";
export interface EnergyTelemetryProps {
  data: EnergyDataPoint[];
  timeRange: TimeRange;
  onTimeRangeChange: (range: TimeRange) => void;
  isLoading?: boolean;
  source?: DataSource;
}

export function EnergyTelemetry({
  data,
  timeRange,
  onTimeRangeChange,
  isLoading = false,
  source = "demo",
}: EnergyTelemetryProps) {
  return (
    <Card id="telemetry" className="p-6 sm:p-8">
      {/* Top Bar with Title, Legend & Time Range Filter */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-[#EA580C]">
              TELEMETRY CH-01
            </span>
            {source === "simulation" ? (
              <span className="rounded bg-blue-100 border border-blue-200 px-1.5 py-0.5 font-mono text-[9px] font-bold uppercase tracking-wider text-blue-700">
                SIMULATION HORIZON
              </span>
            ) : source === "offline" ? (
              <span className="rounded bg-red-100 border border-red-200 px-1.5 py-0.5 font-mono text-[9px] font-bold uppercase tracking-wider text-red-700">
                OFFLINE
              </span>
            ) : (
              <span className="rounded bg-slate-100 border border-slate-200 px-1.5 py-0.5 font-mono text-[9px] font-bold uppercase tracking-wider text-slate-400">
                DEMO DATA
              </span>
            )}
          </div>
          <h3 className="mt-1 font-heading text-2xl font-bold tracking-tight text-slate-950">
            {timeRange === "24h" ? "24-Hour" : timeRange === "7d" ? "7-Day" : "30-Day"} Energy Dispatch Schedule
          </h3>
          <p className="mt-0.5 text-sm text-slate-500">
            Real-time multi-source generation overlaid with village load requirement
          </p>
        </div>

        {/* Time Horizon Filter */}
        <div className="flex items-center gap-1.5 rounded-xl border border-slate-200 bg-slate-50 p-1">
          {(["24h", "7d", "30d"] as const).map((range) => (
            <button
              key={range}
              onClick={() => onTimeRangeChange(range)}
              className={`rounded-lg px-3.5 py-1.5 font-mono text-xs font-bold uppercase tracking-wider transition-all cursor-pointer ${
                timeRange === range
                  ? "bg-slate-950 text-white shadow-sm"
                  : "text-slate-500 hover:text-slate-900"
              }`}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      {/* Semantic Legend Pills */}
      <div className="flex flex-wrap items-center gap-3 font-mono text-xs mb-6">
        <span className="inline-flex items-center gap-1.5 rounded-lg border border-orange-200 bg-orange-50 px-2.5 py-1 text-[#EA580C]">
          <span className="h-2 w-2 rounded-full bg-[#F7931A]" />
          Solar (PV)
        </span>
        <span className="inline-flex items-center gap-1.5 rounded-lg border border-green-200 bg-green-50 px-2.5 py-1 text-green-700">
          <span className="h-2 w-2 rounded-full bg-[#22C55E]" />
          Battery Storage
        </span>
        <span className="inline-flex items-center gap-1.5 rounded-lg border border-blue-200 bg-blue-50 px-2.5 py-1 text-blue-700">
          <span className="h-2 w-2 rounded-full bg-[#3B82F6]" />
          Grid Import
        </span>
        <span className="inline-flex items-center gap-1.5 rounded-lg border border-red-200 bg-red-50 px-2.5 py-1 text-red-700">
          <span className="h-2 w-2 rounded-full bg-[#EF4444]" />
          Diesel Reserve
        </span>
        <span className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-100 px-2.5 py-1 text-slate-800">
          <span className="h-0.5 w-3 bg-slate-900 border-dashed" />
          Load Demand
        </span>
      </div>

      {/* Recharts Chart or Loading Skeleton */}
      {isLoading ? (
        <LoadingSkeleton height="h-[340px]" />
      ) : (
        <EnergyAreaChart data={data} height={340} />
      )}

      {/* Bottom Telemetry Annotations */}
      <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4 font-mono text-[11px] text-slate-500">
        <span>Dashed line: Total community load demand curve</span>
        <span className="font-semibold text-slate-700">Peak Demand: 6.5 kW @ 20:00 HRS</span>
      </div>
    </Card>
  );
}
