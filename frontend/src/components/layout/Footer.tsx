import { technicalSpecs } from "../../data/dashboardData";

export function Footer() {
  return (
    <footer className="mt-14 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm font-mono text-xs text-slate-500">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
          <span className="font-bold text-slate-800">
            LP SOLVER: {technicalSpecs.solver}
          </span>
          <span className="text-slate-300">|</span>
          <span>TERMINAL: {technicalSpecs.terminalId}</span>
        </div>

        <div className="flex items-center gap-4 text-[11px]">
          <span>FREQ: <strong className="text-slate-700">{technicalSpecs.frequency}</strong></span>
          <span>PF: <strong className="text-slate-700">{technicalSpecs.powerFactor}</strong></span>
          <span>TARIFF: <strong className="text-slate-700">{technicalSpecs.tariff}</strong></span>
        </div>
      </div>
      <div className="mt-3 pt-3 border-t border-slate-100 flex flex-wrap justify-between text-[10px] text-slate-400">
        <span>GRAMURJA AI • RURAL MICROGRID INTELLIGENCE PLATFORM</span>
        <span>© {new Date().getFullYear()} ALL RIGHTS RESERVED</span>
      </div>
    </footer>
  );
}
