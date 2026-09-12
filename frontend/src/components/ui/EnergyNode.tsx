import type { LucideIcon } from "lucide-react";

export interface EnergyNodeProps {
  icon: LucideIcon;
  title: string;
  value: string;
  status: "ACTIVE" | "STANDBY" | "OFFLINE" | "OPTIMIZING";
  tone?: "orange" | "green" | "blue" | "slate";
  active?: boolean;
  /** A second, smaller line under the value -- e.g. a tariff or a feeder's availability. */
  caption?: string;
}

export function EnergyNode({
  icon: Icon,
  title,
  value,
  status,
  tone = "orange",
  active = true,
  caption,
}: EnergyNodeProps) {
  const toneClasses = {
    orange: "border-orange-200 bg-orange-50/70 text-[#EA580C]",
    green: "border-green-200 bg-green-50/70 text-green-700",
    blue: "border-blue-200 bg-blue-50/70 text-blue-700",
    slate: "border-slate-200 bg-slate-50 text-slate-600",
  };

  const statusPills = {
    ACTIVE: "bg-green-100 text-green-800 border-green-200",
    STANDBY: "bg-amber-100 text-amber-800 border-amber-200",
    OFFLINE: "bg-slate-200 text-slate-700 border-slate-300",
    OPTIMIZING: "bg-orange-100 text-[#EA580C] border-orange-200",
  };

  return (
    <div className={`relative flex flex-col items-center justify-center rounded-2xl border p-4 text-center transition-all duration-300 hover:shadow-md ${toneClasses[tone]}`}>
      {active && (
        <span className="absolute -top-1 -right-1 flex h-3 w-3">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-3 w-3 bg-[#EA580C]" />
        </span>
      )}

      <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-xl bg-white shadow-sm">
        <Icon className="h-5 w-5" />
      </div>

      <div className="font-heading text-xs font-bold uppercase tracking-wider text-slate-900">
        {title}
      </div>

      <div className="my-1 font-mono text-xs font-semibold text-slate-700">
        {value}
      </div>
      {caption && (
        <div className="mb-1 font-mono text-[9px] text-slate-400">{caption}</div>
      )}

      <span className={`mt-1 rounded-full border px-2 py-0.5 font-mono text-[9px] font-bold uppercase tracking-wider ${statusPills[status]}`}>
        {status}
      </span>
    </div>
  );
}
