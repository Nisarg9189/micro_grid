import {
  Sun,
  BrainCircuit,
  Battery,
  Home,
  Sprout,
  Radio,
  Power,
  ArrowRight,
  ArrowDown
} from "lucide-react";
import { Card } from "../ui/Card";
import { StatusPill } from "../ui/StatusPill";
import { EnergyNode } from "../ui/EnergyNode";

export function EnergyFlow() {
  return (
    <Card id="energy-flow" className="p-6 sm:p-8">
      {/* Header */}
      <div className="mb-7 flex flex-wrap items-end justify-between gap-4">
        <div>
          <span className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-[#EA580C]">
            SYSTEM ARCHITECTURE
          </span>
          <h3 className="mt-1 font-heading text-2xl font-bold tracking-tight text-slate-950">
            Live Energy Flow
          </h3>
          <p className="mt-1 text-sm text-slate-500">
            GRAMURJA AI continuously directs solar and storage to serve rural village and irrigation loads.
          </p>
        </div>
        <StatusPill tone="green" dot>AI DISPATCH ACTIVE</StatusPill>
      </div>

      {/* Responsive Flow Grid */}
      <div className="grid items-center gap-4 lg:grid-cols-5">
        
        {/* Step 1: Solar Generation */}
        <div className="flex flex-col items-center">
          <EnergyNode
            icon={Sun}
            title="Solar Array"
            value="3.0 kW (100%)"
            status="ACTIVE"
            tone="orange"
            active
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
            <span className="absolute -top-2 -right-2 flex h-4 w-4">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-4 w-4 bg-[#EA580C]" />
            </span>

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

        {/* Step 3: Destination Loads & Balancing */}
        <div className="grid grid-cols-3 gap-2 w-full">
          <div className="rounded-xl border border-green-200 bg-green-50/70 p-3 text-center">
            <Battery className="mx-auto mb-1.5 h-5 w-5 text-green-600" />
            <div className="font-mono text-[10px] font-bold text-slate-800">LFP BATT</div>
            <div className="font-mono text-[9px] text-green-700">84% SOC</div>
          </div>
          <div className="rounded-xl border border-blue-200 bg-blue-50/70 p-3 text-center">
            <Home className="mx-auto mb-1.5 h-5 w-5 text-blue-600" />
            <div className="font-mono text-[10px] font-bold text-slate-800">VILLAGE</div>
            <div className="font-mono text-[9px] text-blue-700">3.4 kW</div>
          </div>
          <div className="rounded-xl border border-emerald-200 bg-emerald-50/70 p-3 text-center">
            <Sprout className="mx-auto mb-1.5 h-5 w-5 text-emerald-600" />
            <div className="font-mono text-[10px] font-bold text-slate-800">AGRI PUMP</div>
            <div className="font-mono text-[9px] text-emerald-700">2.4 kW</div>
          </div>
        </div>

      </div>

      {/* Balancing Sources Footer */}
      <div className="mt-7 pt-5 border-t border-slate-100 flex flex-wrap items-center justify-between gap-4 font-mono text-[11px] text-slate-500">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <Radio className="h-4 w-4 text-blue-600" />
            Grid Feeder: <strong className="text-slate-800">Connected (₹4.20/u)</strong>
          </span>
          <span className="text-slate-300">•</span>
          <span className="flex items-center gap-1.5">
            <Power className="h-4 w-4 text-slate-500" />
            Diesel Backup: <strong className="text-slate-800">Standby (Preserved)</strong>
          </span>
        </div>

        <span className="text-[10px] uppercase tracking-wider text-slate-400">
          Solar First → Battery Buffer → Grid Support → Diesel Reserve
        </span>
      </div>
    </Card>
  );
}
