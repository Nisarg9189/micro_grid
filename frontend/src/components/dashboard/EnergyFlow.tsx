import {
  Sun,
  BrainCircuit,
  Battery,
  Home,
  Radio,
  Power,
  ArrowRight,
  ArrowDown
} from "lucide-react";
import { Card } from "../ui/Card";
import { StatusPill } from "../ui/StatusPill";
import { EnergyNode } from "../ui/EnergyNode";
import { useSimulationContext } from "../../hooks/SimulationContext";
import { peakLoadIndex, hourLabel } from "../../utils/horizon";

// One decimal place, or an em dash while no simulation has resolved yet -- a fabricated
// "0.0 kW" reads as a real reading of nothing, which is a different claim from "no data".
function fmt(value: number | null, unit: string): string {
  return value == null ? "—" : `${value.toFixed(1)} ${unit}`;
}

export function EnergyFlow() {
  const { data: simData, source } = useSimulationContext();

  // The API returns a full horizon, not a live feed. Rather than the horizon's last
  // hour -- often the middle of the night, where solar reads 0 and nothing looks like
  // it's happening -- this shows the peak-demand hour, where there is actually
  // something for solar, battery, grid and diesel to balance.
  const series = simData?.series ?? null;
  const peak = series ? peakLoadIndex(series.load_kw) : -1;
  const at = (arr?: number[]) => (arr && peak >= 0 ? arr[peak] : null);

  const solarKw = at(series?.solar_kw);
  const socPct = at(series?.soc) != null ? at(series?.soc)! * 100 : null;
  const gridKw = (() => {
    const ag = at(series?.ag_kw);
    const vil = at(series?.village_kw);
    return ag == null && vil == null ? null : (ag ?? 0) + (vil ?? 0);
  })();
  const dieselKw = at(series?.diesel_kw);
  const loadKw = at(series?.load_kw);
  const agAvailable = at(series?.ag_available);
  const villageAvailable = at(series?.village_available);
  const chargeKw = at(series?.charge_kw);
  const dischargeKw = at(series?.discharge_kw);
  const batteryCharging = chargeKw != null && dischargeKw != null && chargeKw > dischargeKw;

  const hasData = source === "simulation" && series != null;

  return (
    <Card id="energy-flow" className="p-6 sm:p-8">
      {/* Header */}
      <div className="mb-7 flex flex-wrap items-end justify-between gap-4">
        <div>
          <span className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-[#EA580C]">
            SYSTEM ARCHITECTURE
          </span>
          <h3 className="mt-1 font-heading text-2xl font-bold tracking-tight text-slate-950">
            Energy Flow
          </h3>
          <p className="mt-1 text-sm text-slate-500">
            {hasData
              ? `Peak-demand hour of a ${simData!.meta.days}-day horizon (${hourLabel(peak)}) -- solar, battery, grid and diesel serving village and irrigation loads.`
              : "Run a simulation to see how solar, battery, grid and diesel combine to serve the load."}
          </p>
        </div>
        <StatusPill tone={hasData ? "green" : source === "offline" ? "danger" : "slate"} dot>
          {hasData ? "SIMULATED DISPATCH" : source === "offline" ? "BACKEND OFFLINE" : "AWAITING SIMULATION"}
        </StatusPill>
      </div>

      {/* Responsive Flow Grid */}
      <div className="grid items-center gap-4 lg:grid-cols-5">

        {/* Step 1: Solar Generation */}
        <div className="flex flex-col items-center">
          <EnergyNode
            icon={Sun}
            title="Solar Array"
            value={fmt(solarKw, "kW")}
            status={solarKw != null && solarKw > 0.05 ? "ACTIVE" : "STANDBY"}
            tone="orange"
            active={solarKw != null && solarKw > 0.05}
          />
        </div>

        {/* Connector 1 */}
        <div className="hidden items-center justify-center lg:flex">
          <div className="h-0.5 w-full bg-gradient-to-r from-orange-300 via-orange-400 to-[#EA580C] relative">
            <span className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#EA580C]" />
            </span>
          </div>
          <ArrowRight className="-ml-2 h-5 w-5 text-[#EA580C]" />
        </div>
        <div className="flex justify-center lg:hidden">
          <ArrowDown className="h-5 w-5 text-[#EA580C]" />
        </div>

        {/* Step 2: AI Optimizer Central Hub */}
        <div className="flex flex-col items-center">
          <div className="relative w-full rounded-2xl border-2 border-orange-200 bg-gradient-to-br from-orange-50 via-amber-50 to-yellow-50 p-5 text-center shadow-[0_10px_25px_rgba(234,88,12,0.08)]">
            {hasData && (
              <span className="absolute -top-2 -right-2 flex h-4 w-4">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-4 w-4 bg-[#EA580C]" />
              </span>
            )}

            <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-[#EA580C] shadow-sm">
              <BrainCircuit className="h-6 w-6" />
            </div>

            <div className="font-heading text-sm font-bold tracking-tight text-slate-950">
              GRAMURJA AI
            </div>
            <div className="font-mono text-[10px] uppercase font-bold text-[#EA580C] mt-0.5">
              LP Solver Dispatch
            </div>
            <div className="mt-2 text-[11px] font-mono text-slate-600 border-t border-orange-200/60 pt-2">
              Objective: Min Cost + 0 Unserved
            </div>
          </div>
        </div>

        {/* Connector 2 */}
        <div className="hidden items-center justify-center lg:flex">
          <div className="h-0.5 w-full bg-gradient-to-r from-[#EA580C] to-green-500 relative">
            <span className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500" />
            </span>
          </div>
          <ArrowRight className="-ml-2 h-5 w-5 text-green-600" />
        </div>
        <div className="flex justify-center lg:hidden">
          <ArrowDown className="h-5 w-5 text-green-600" />
        </div>

        {/* Step 3: Where the energy actually went, this hour */}
        <div className="grid grid-cols-3 gap-2 w-full">
          <div className="rounded-xl border border-green-200 bg-green-50/70 p-3 text-center">
            <Battery className="mx-auto mb-1.5 h-5 w-5 text-green-600" />
            <div className="font-mono text-[10px] font-bold text-slate-800">BATTERY</div>
            <div className="font-mono text-[9px] text-green-700">
              {socPct == null ? "—" : `${socPct.toFixed(0)}% SOC`}
              {socPct != null && (batteryCharging ? " ▲" : " ▼")}
            </div>
          </div>
          <div className="rounded-xl border border-blue-200 bg-blue-50/70 p-3 text-center">
            <Home className="mx-auto mb-1.5 h-5 w-5 text-blue-600" />
            <div className="font-mono text-[10px] font-bold text-slate-800">TOTAL LOAD</div>
            <div className="font-mono text-[9px] text-blue-700">{fmt(loadKw, "kW")}</div>
          </div>
          <div className="rounded-xl border border-orange-200 bg-orange-50/70 p-3 text-center">
            <Power className="mx-auto mb-1.5 h-5 w-5 text-orange-600" />
            <div className="font-mono text-[10px] font-bold text-slate-800">DIESEL</div>
            <div className="font-mono text-[9px] text-orange-700">
              {dieselKw == null ? "—" : dieselKw > 0.05 ? fmt(dieselKw, "kW") : "Standby"}
            </div>
          </div>
        </div>

      </div>

      {/* Balancing Sources Footer */}
      <div className="mt-7 pt-5 border-t border-slate-100 flex flex-wrap items-center justify-between gap-4 font-mono text-[11px] text-slate-500">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <Radio className="h-4 w-4 text-blue-600" />
            Grid draw: <strong className="text-slate-800">{fmt(gridKw, "kW")}</strong>
            {agAvailable != null && (
              <span className={agAvailable ? "text-green-700" : "text-slate-400"}>
                {agAvailable ? "(Ag feeder on)" : "(Ag feeder off)"}
              </span>
            )}
            {villageAvailable != null && !villageAvailable && (
              <span className="text-red-600">(Village feeder off)</span>
            )}
          </span>
          <span className="text-slate-300">•</span>
          <span className="flex items-center gap-1.5">
            <Power className="h-4 w-4 text-slate-500" />
            Diesel: <strong className="text-slate-800">
              {dieselKw == null ? "—" : dieselKw > 0.05 ? "Running" : "Standby"}
            </strong>
          </span>
        </div>

        <span className="text-[10px] uppercase tracking-wider text-slate-400">
          Solar First → Battery Buffer → Grid Support → Diesel Reserve
        </span>
      </div>
    </Card>
  );
}
