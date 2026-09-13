import { FlaskConical } from "lucide-react";
import { useSimulationContext } from "../../hooks/SimulationContext";
import { DEFAULT_PARAMS } from "../../data/presets";
import { FARM_SCENARIOS } from "../../data/scenarios";

// Every button here reproduces one of the real, live-tested configurations from this
// project's own investigation into farm-scale wind economics -- not a hypothetical demo
// toggle. Each one merges onto DEFAULT_PARAMS (not the current live params) so it always
// reproduces the exact tested condition, regardless of what a viewer changed beforehand.
export function ScenarioPicker() {
  const { params, setParams, executeSimulation, isLoading } = useSimulationContext();

  const run = (overrides: (typeof FARM_SCENARIOS)[number]["overrides"]) => {
    const next = { ...DEFAULT_PARAMS, ...overrides };
    setParams(next);
    executeSimulation(next);
  };

  const isActive = (overrides: (typeof FARM_SCENARIOS)[number]["overrides"]) =>
    Object.entries(overrides).every(([k, v]) => (params as any)[k] === v);

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6">
      <div className="mb-4 flex items-center gap-2 font-mono text-[10px] font-bold uppercase tracking-[0.16em] text-[#EA580C]">
        <FlaskConical className="h-4 w-4" />
        Tested Scenarios
      </div>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {FARM_SCENARIOS.map((s) => (
          <button
            key={s.name}
            onClick={() => run(s.overrides)}
            disabled={isLoading}
            className={`rounded-xl border p-3.5 text-left transition-colors disabled:opacity-60 cursor-pointer ${
              isActive(s.overrides)
                ? "border-[#EA580C] bg-orange-50/60"
                : "border-slate-200 bg-slate-50/60 hover:border-[#EA580C] hover:bg-orange-50/40"
            }`}
          >
            <div className="font-mono text-xs font-bold uppercase tracking-wider text-slate-800">
              {s.name}
            </div>
            <div className="mt-1 text-[11px] text-slate-500">{s.question}</div>
            <div className="mt-1.5 text-[11px] font-medium text-emerald-700">{s.finding}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
