import { HeartHandshake, IndianRupee, Droplets, ShieldCheck, Leaf } from "lucide-react";
import { Card } from "../ui/Card";
import { dashboardImages } from "../../data/dashboardData";
import { useSimulationContext } from "../../hooks/SimulationContext";

// One decimal place, or an em dash while no simulation has resolved -- a fabricated
// "0" reads as a real reading of nothing, which is a different claim from "no data".
function fmt(value: number | null, digits = 0): string {
  return value == null ? "—" : value.toLocaleString(undefined, {
    minimumFractionDigits: digits, maximumFractionDigits: digits,
  });
}

// Every figure here used to be hardcoded -- a fixed annual saving, a fixed "916 L",
// and invented beneficiary claims ("120+ households & primary school", "42 Farming
// Families") with no backend field behind any of it. It now reads the same
// status-quo-vs-optimiser comparison the KPI grid above is built from, over whatever
// horizon is actually configured, and says so rather than implying an annual number.
export function CommunityImpact() {
  const { data: simData, source } = useSimulationContext();
  const hasData = source === "simulation" && simData != null;

  const q = simData?.kpis.status_quo;
  const o = simData?.kpis.optimiser;
  const days = simData?.meta.days;
  const period = days ? `${days}-day horizon` : "this horizon";

  const costSaved = q && o ? q.cost_inr - o.cost_inr : null;
  const dieselSavedL = q && o ? q.diesel_litres - o.diesel_litres : null;
  const dieselPct = q && o && q.diesel_litres > 0
    ? (100 * (q.diesel_litres - o.diesel_litres)) / q.diesel_litres
    : null;
  const co2Saved = q && o ? q.co2_kg - o.co2_kg : null;
  const reliabilityPct = o?.reliability_pct ?? null;

  return (
    <Card className="p-6 sm:p-8 overflow-hidden">
      <div className="mb-6">
        <div className="inline-flex items-center gap-2 rounded-full border border-blue-100 bg-blue-50 px-2.5 py-1 font-mono text-[10px] font-bold uppercase tracking-[0.16em] text-blue-700">
          <HeartHandshake className="h-3.5 w-3.5" />
          Rural Social Impact
        </div>
        <h3 className="mt-2 font-heading text-2xl font-bold tracking-tight text-slate-950">
          Community Transformation & Sustainability
        </h3>
        <p className="text-sm text-slate-500">
          {hasData
            ? `Optimiser vs. status quo, over the configured ${period} -- not an annual figure.`
            : "Run a simulation to compare the optimiser against the status quo."}
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1.2fr_0.8fr] gap-6 items-center">

        {/* 4 Impact Stat Cards -- every number below reads the live comparison, none invented */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="rounded-2xl border border-slate-100 bg-slate-50/70 p-5">
            <div className="flex items-center gap-2 text-[#EA580C] mb-2 font-mono text-xs font-bold uppercase">
              <IndianRupee className="h-4 w-4" /> Cost Savings
            </div>
            <div className="font-mono text-3xl font-bold text-slate-950">
              {hasData ? `₹${fmt(costSaved)}` : "—"}
            </div>
            <div className="text-xs text-slate-500 mt-1">
              {hasData ? `Over the ${period}, vs. status quo` : "Awaiting simulation"}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-100 bg-slate-50/70 p-5">
            <div className="flex items-center gap-2 text-blue-600 mb-2 font-mono text-xs font-bold uppercase">
              <Droplets className="h-4 w-4" /> Diesel Reduction
            </div>
            <div className="font-mono text-3xl font-bold text-slate-950">
              {hasData ? `${fmt(dieselPct)}%` : "—"}
            </div>
            <div className="text-xs text-slate-500 mt-1">
              {hasData ? `${fmt(dieselSavedL, 1)} L less over the ${period}` : "Awaiting simulation"}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-100 bg-slate-50/70 p-5">
            <div className="flex items-center gap-2 text-green-600 mb-2 font-mono text-xs font-bold uppercase">
              <Leaf className="h-4 w-4" /> CO₂ Abatement
            </div>
            <div className="font-mono text-3xl font-bold text-slate-950">
              {hasData ? `${fmt(co2Saved)} kg` : "—"}
            </div>
            <div className="text-xs text-slate-500 mt-1">
              {hasData ? `Avoided over the ${period}` : "Awaiting simulation"}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-100 bg-slate-50/70 p-5">
            <div className="flex items-center gap-2 text-indigo-600 mb-2 font-mono text-xs font-bold uppercase">
              <ShieldCheck className="h-4 w-4" /> Grid Reliability
            </div>
            <div className="font-mono text-3xl font-bold text-slate-950">
              {hasData ? `${fmt(reliabilityPct, 1)}%` : "—"}
            </div>
            <div className="text-xs text-slate-500 mt-1">
              {hasData ? "Of demand served, this horizon" : "Awaiting simulation"}
            </div>
          </div>
        </div>

        {/* Side Village Image */}
        <div className="relative h-60 sm:h-72 overflow-hidden rounded-2xl border border-slate-200 shadow-inner group">
          <img
            src={dashboardImages.village}
            alt="Indian rural village energized by clean solar power"
            className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-105"
            loading="lazy"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-slate-950/20 to-transparent" />
          <div className="absolute bottom-4 left-4 right-4 text-white">
            <span className="font-mono text-[10px] uppercase text-orange-300">
              GramUrja Electrification Impact
            </span>
            <h4 className="mt-1 font-heading text-base font-bold">
              {hasData ? simData!.meta.site : "Irrigation, household, dairy and cold-storage loads"}
            </h4>
          </div>
        </div>

      </div>
    </Card>
  );
}
