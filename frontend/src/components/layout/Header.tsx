import { Link } from "react-router-dom";
import { Zap, BrainCircuit, CloudOff } from "lucide-react";
import type { OperatingMode } from "../../types/dashboard";
import { useSimulationContext } from "../../hooks/SimulationContext";

export interface HeaderProps {
  mode: OperatingMode;
  onModeChange: (newMode: OperatingMode) => void;
}

export function Header({
  mode,
  onModeChange,
}: HeaderProps) {
  const { source, lastUpdated } = useSimulationContext();
  return (
    <header className="sticky top-4 z-30 flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-200/90 bg-white/90 px-4 py-3 shadow-[0_12px_35px_rgba(15,23,42,0.06)] backdrop-blur-xl sm:px-6">
      {/* Brand & Identity */}
      <div className="flex items-center gap-3">
        <Link to="/" className="flex items-center gap-3 group">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-[#EA580C] to-[#F7931A] text-white shadow-[0_8px_20px_rgba(234,88,12,0.25)] transition-transform duration-300 group-hover:scale-105">
            <Zap className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-heading text-lg font-bold tracking-tight text-slate-950 sm:text-xl">
                GRAMURJA <span className="text-[#EA580C]">AI</span>
              </span>
              <span className="hidden sm:inline-block rounded-full bg-slate-100 px-2 py-0.5 font-mono text-[9px] font-bold tracking-wider text-slate-600">
                V2.4
              </span>
            </div>
            <p className="font-mono text-[9px] uppercase tracking-[0.16em] text-slate-400">
              AI-Powered Rural Microgrid Intelligence
            </p>
          </div>
        </Link>
      </div>

      {/* Center Nav / Links */}
      <nav className="hidden items-center gap-6 lg:flex font-mono text-[11px] font-bold uppercase tracking-wider">
        <span className="text-[#EA580C]">Dashboard</span>
        <a href="#energy-flow" className="text-slate-500 hover:text-slate-900 transition-colors">Energy Flow</a>
        <a href="#telemetry" className="text-slate-500 hover:text-slate-900 transition-colors">Telemetry</a>
        <a href="#agriculture" className="text-slate-500 hover:text-slate-900 transition-colors">Agriculture</a>
        <Link
          to="/"
          className="flex items-center gap-1.5 text-slate-500 hover:text-[#EA580C] transition-colors"
        >
          <BrainCircuit className="h-3.5 w-3.5" />
          Prediction
        </Link>
      </nav>

      {/* Right Actions & Status */}
      <div className="flex items-center gap-3">
        {/* Prediction Page Button */}
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 rounded-xl border border-orange-200 bg-gradient-to-r from-[#EA580C] to-[#F7931A] px-3.5 py-1.5 font-mono text-[10px] font-bold uppercase tracking-wider text-white shadow-sm transition-all hover:scale-[1.03] hover:shadow-[0_4px_12px_rgba(234,88,12,0.25)]"
        >
          <BrainCircuit className="h-3.5 w-3.5" />
          Prediction
        </Link>

        {/* System Online Badge */}
        {source === "offline" ? (
          <div className="hidden sm:flex items-center gap-2 rounded-full border border-red-200 bg-red-50 px-3 py-1.5">
            <CloudOff className="h-3.5 w-3.5 text-red-500" />
            <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-red-700">
              Offline
            </span>
          </div>
        ) : source === "simulation" ? (
          <div className="hidden sm:flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-3 py-1.5" title={`Last optimized: ${lastUpdated}`}>
            <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-blue-700">
              Optimized Simulation
            </span>
          </div>
        ) : (
          <div className="hidden sm:flex items-center gap-2 rounded-full border border-amber-200 bg-amber-50 px-3 py-1.5">
            <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-amber-700">
              Demo Fallback
            </span>
          </div>
        )}

        {/* AUTO / MANUAL Switcher */}
        <div className="flex rounded-xl border border-slate-200 bg-slate-50 p-1">
          <button
            onClick={() => onModeChange("auto")}
            className={`rounded-lg px-3 py-1 font-mono text-[10px] font-bold uppercase tracking-wider transition-all cursor-pointer ${
              mode === "auto"
                ? "bg-slate-950 text-white shadow-sm"
                : "text-slate-500 hover:text-slate-900"
            }`}
          >
            Auto
          </button>
          <button
            onClick={() => onModeChange("manual")}
            className={`rounded-lg px-3 py-1 font-mono text-[10px] font-bold uppercase tracking-wider transition-all cursor-pointer ${
              mode === "manual"
                ? "bg-slate-950 text-white shadow-sm"
                : "text-slate-500 hover:text-slate-900"
            }`}
          >
            Manual
          </button>
        </div>
      </div>
    </header>
  );
}
