import {
  Sun,
  Wind,
  BrainCircuit,
  Battery,
  Zap,
  Fuel,
  Home,
  ArrowDown,
} from "lucide-react";
import { Card } from "../ui/Card";
import { StatusPill } from "../ui/StatusPill";
import { EnergyNode } from "../ui/EnergyNode";
import { FeatureBar } from "../ui/FeatureBar";
import { useSimulationContext } from "../../hooks/SimulationContext";
import { peakLoadIndex, hourLabel } from "../../utils/horizon";

// One decimal place, or an em dash while no simulation has resolved yet -- a fabricated
// "0.0 kW" reads as a real reading of nothing, which is a different claim from "no data".
function fmt(value: number | null, unit: string): string {
  return value == null ? "—" : `${value.toFixed(1)} ${unit}`;
}

// The system genuinely has five energy sources, not one undifferentiated "grid" --
// the agricultural feeder and village feeder are separately tariffed, separately
// available hour to hour, and (in the actual dispatch LP) restricted to different
// loads: the ag feeder may power irrigation, the village feeder may not. Collapsing
// them into one "Grid Feed" number, which this component used to do, hid the single
// structural fact the whole project is built around. Each node below reads its own
// real series, and a feeder that's simply unavailable this hour says so rather than
// reading 0 kW the same way an available-but-unused feeder would.
export function EnergyFlow() {
  const { data: simData, params, source } = useSimulationContext();

  // The API returns a full horizon, not a live feed. Rather than the horizon's last
  // hour -- often the middle of the night, where solar reads 0 and nothing looks like
  // it's happening -- this shows the peak-demand hour, where there is actually
  // something for every source to balance.
  const series = simData?.series ?? null;
  const peak = series ? peakLoadIndex(series.load_kw) : -1;
  const at = (arr?: number[]) => (arr && peak >= 0 ? arr[peak] : null);

  const solarKw = at(series?.solar_kw);
  const windKw = at(series?.wind_kw);
  const hasWind = params.wind > 0;
  const agKw = at(series?.ag_kw);
  const villageKw = at(series?.village_kw);
  const dieselKw = at(series?.diesel_kw);
  const loadKw = at(series?.load_kw);
  const socPct = at(series?.soc) != null ? at(series?.soc)! * 100 : null;
  const agAvailable = at(series?.ag_available);
  const villageAvailable = at(series?.village_available);
  const chargeKw = at(series?.charge_kw);
  const dischargeKw = at(series?.discharge_kw);
  const netBatteryKw = chargeKw != null && dischargeKw != null ? dischargeKw - chargeKw : null;

  const hasData = source === "simulation" && series != null;

  // ACTIVE if the feeder is up and actually being drawn on this hour; STANDBY if it's
  // up but the optimiser chose not to use it (solar or battery was cheaper); OFFLINE
  // only when the feeder is genuinely down -- three different facts, not one 0 kW.
  const feederStatus = (kw: number | null, available: number | null) => {
    if (available === 0) return "OFFLINE" as const;
    if (kw != null && kw > 0.05) return "ACTIVE" as const;
    return "STANDBY" as const;
  };

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
              ? `Peak-demand hour of a ${simData!.meta.days}-day horizon (${hourLabel(peak)}) -- every real source and the load the optimiser balanced them against.`
              : "Run a simulation to see how solar, the two feeders, battery and diesel combine to serve the load."}
          </p>
        </div>
        <StatusPill tone={hasData ? "green" : source === "offline" ? "danger" : "slate"} dot>
          {hasData ? "SIMULATED DISPATCH" : source === "offline" ? "BACKEND OFFLINE" : "AWAITING SIMULATION"}
        </StatusPill>
      </div>

      <FeatureBar tone="orange">
        What this does: shows exactly where every kWh came from and went, for one
        snapshot hour -- the real dispatch decision the LP solver made, not an
        illustration.
      </FeatureBar>

      {/* Real sources -- each reads its own series, none combined or invented. A wind
          turbine only appears when one is actually installed (params.wind > 0); the
          Solar node's own caption says plainly that dispatch is a combined figure once
          wind is in the mix, rather than silently crediting wind's output to solar. */}
      <div className={`grid grid-cols-2 gap-3 sm:grid-cols-3 ${hasWind ? "lg:grid-cols-6" : "lg:grid-cols-5"}`}>
        <EnergyNode
          icon={Sun}
          title="Solar Array"
          value={fmt(solarKw, "kW")}
          caption={hasWind ? `${params.solar} kWp -- dispatch combines this with wind` : `${params.solar} kWp installed`}
          status={solarKw != null && solarKw > 0.05 ? "ACTIVE" : "STANDBY"}
          tone="orange"
          active={hasData && solarKw != null && solarKw > 0.05}
        />
        {hasWind && (
          <EnergyNode
            icon={Wind}
            title="Wind Turbine"
            value={fmt(windKw, "kW")}
            caption={`${params.wind} kW installed @ ${params.hub_height}m -- raw availability, not dispatch`}
            status={windKw != null && windKw > 0.05 ? "ACTIVE" : "STANDBY"}
            tone="cyan"
            active={hasData && windKw != null && windKw > 0.05}
          />
        )}
        <EnergyNode
          icon={Zap}
          title="Ag Feeder"
          value={fmt(agKw, "kW")}
          caption={`₹${params.ag_tariff}/kWh`}
          status={feederStatus(agKw, agAvailable)}
          tone="blue"
          active={hasData && agKw != null && agKw > 0.05}
        />
        <EnergyNode
          icon={Home}
          title="Village Feeder"
          value={fmt(villageKw, "kW")}
          caption={`₹${params.village_tariff}/kWh`}
          status={feederStatus(villageKw, villageAvailable)}
          tone="blue"
          active={hasData && villageKw != null && villageKw > 0.05}
        />
        <EnergyNode
          icon={Battery}
          title="Battery"
          value={
            netBatteryKw == null ? "—"
              : `${netBatteryKw >= 0 ? "+" : ""}${netBatteryKw.toFixed(1)} kW`
          }
          caption={socPct == null ? undefined : `${socPct.toFixed(0)}% SOC`}
          status={netBatteryKw != null && Math.abs(netBatteryKw) > 0.05 ? "ACTIVE" : "STANDBY"}
          tone="green"
          active={hasData && netBatteryKw != null && Math.abs(netBatteryKw) > 0.05}
        />
        <EnergyNode
          icon={Fuel}
          title="Diesel Genset"
          value={fmt(dieselKw, "kW")}
          caption={`${params.genset_kw} kW capacity`}
          status={dieselKw != null && dieselKw > 0.05 ? "ACTIVE" : "STANDBY"}
          tone="slate"
          active={hasData && dieselKw != null && dieselKw > 0.05}
        />
      </div>

      <div className="my-4 flex justify-center">
        <ArrowDown className="h-5 w-5 text-slate-300" />
      </div>

      {/* The AI hub -- decides the split above, not shown as a source or sink itself */}
      <div className="mx-auto flex max-w-xs items-center gap-3 rounded-2xl border-2 border-orange-200 bg-gradient-to-br from-orange-50 via-amber-50 to-yellow-50 p-4 shadow-[0_10px_25px_rgba(234,88,12,0.08)]">
        <div className="flex h-11 w-11 flex-none items-center justify-center rounded-xl bg-white text-[#EA580C] shadow-sm">
          <BrainCircuit className="h-5 w-5" />
        </div>
        <div className="min-w-0">
          <div className="font-heading text-sm font-bold tracking-tight text-slate-950">
            GRAMURJA AI &middot; LP Solver Dispatch
          </div>
          <div className="truncate text-[11px] font-mono text-slate-600">
            Objective: Min Cost + 0 Unserved
          </div>
        </div>
      </div>

      <div className="my-4 flex justify-center">
        <ArrowDown className="h-5 w-5 text-slate-300" />
      </div>

      {/* The one destination the API reports -- it does not split load by category,
          so this stays a single honest total rather than a fabricated village/pump split */}
      <div className="mx-auto max-w-xs rounded-xl border border-indigo-200 bg-indigo-50/70 p-4 text-center">
        <Home className="mx-auto mb-1.5 h-5 w-5 text-indigo-600" />
        <div className="font-mono text-[10px] font-bold uppercase tracking-wider text-slate-800">
          Total Load
        </div>
        <div className="font-mono text-sm font-bold text-indigo-700">{fmt(loadKw, "kW")}</div>
      </div>

      {/* Feeder availability, spelled out -- the fact an EnergyNode's caption can't
          hold: WHY a feeder reads 0 kW (down) versus reads 0 kW (up, just not used) */}
      <div className="mt-7 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 border-t border-slate-100 pt-5 font-mono text-[11px] text-slate-500">
        <span className={agAvailable === 0 ? "text-red-600" : "text-slate-500"}>
          Ag feeder: <strong>{agAvailable == null ? "—" : agAvailable ? "up this hour" : "down this hour"}</strong>
        </span>
        <span className="text-slate-300">•</span>
        <span className={villageAvailable === 0 ? "text-red-600" : "text-slate-500"}>
          Village feeder: <strong>{villageAvailable == null ? "—" : villageAvailable ? "up this hour" : "down this hour"}</strong>
        </span>
        <span className="text-slate-300">•</span>
        <span className="uppercase tracking-wider text-slate-400">
          Solar First → Battery Buffer → Feeders → Diesel Reserve
        </span>
      </div>
    </Card>
  );
}
