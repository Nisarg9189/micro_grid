export function Footer() {
  return (
    <footer className="mt-14 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm font-mono text-xs text-slate-500">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
          {/* The real dispatch LP, via cvxpy -- not the PuLP/CBC this footer previously
              (and incorrectly) claimed. Everything else that used to sit here -- a
              terminal ID, grid frequency, power factor, a tariff -- had no backend
              endpoint behind it and no physical meter to read it from. */}
          <span className="font-bold text-slate-800">LP SOLVER: CLARABEL (cvxpy)</span>
        </div>
      </div>
      <div className="mt-3 pt-3 border-t border-slate-100 flex flex-wrap justify-between text-[10px] text-slate-400">
        <span>GRAMURJA AI • RURAL MICROGRID INTELLIGENCE PLATFORM</span>
        <span>© {new Date().getFullYear()} ALL RIGHTS RESERVED</span>
      </div>
    </footer>
  );
}
