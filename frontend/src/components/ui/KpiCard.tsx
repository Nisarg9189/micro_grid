import type { LucideIcon } from "lucide-react";

export interface KpiCardProps {
  title: string;
  value: string;
  unit?: string;
  change?: string;
  description?: string;
  trend?: "up" | "down" | "neutral";
  tone?: "orange" | "green" | "blue";
  icon: LucideIcon;
}

export function KpiCard({
  title,
  value,
  unit,
  change,
  description,
  tone = "orange",
  icon: Icon,
}: KpiCardProps) {
  const toneClasses = {
    orange: "text-[#EA580C] bg-orange-50 border-orange-100",
    green: "text-[#16A34A] bg-green-50 border-green-100",
    blue: "text-[#2563EB] bg-blue-50 border-blue-100",
  };

  return (
    <div className="group rounded-2xl border border-slate-200 bg-white p-6 shadow-[0_10px_30px_rgba(15,23,42,0.04)] transition-all duration-300 hover:-translate-y-1 hover:border-orange-200 hover:shadow-[0_18px_45px_rgba(234,88,12,0.09)]">
      <div className="mb-4 flex items-center justify-between">
        <span className="font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-slate-500">
          {title}
        </span>
        <div className={`flex h-10 w-10 items-center justify-center rounded-xl border ${toneClasses[tone]} transition-transform duration-300 group-hover:scale-110`}>
          <Icon className="h-5 w-5" strokeWidth={1.9} />
        </div>
      </div>

      <div className="mb-3 flex items-baseline gap-1 font-mono text-3xl font-bold tracking-tight text-slate-950">
        <span>{value}</span>
        {unit && <span className="text-xs font-semibold text-slate-400">{unit}</span>}
      </div>

      <div className="flex items-center justify-between gap-3 font-mono text-[11px]">
        <span className="text-slate-600 truncate">{description}</span>
        {change && (
          <span className="shrink-0 rounded-full bg-green-50 border border-green-100 px-2 py-0.5 font-bold text-green-700">
            {change}
          </span>
        )}
      </div>
    </div>
  );
}
