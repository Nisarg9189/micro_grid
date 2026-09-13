import { Landmark, RotateCw } from "lucide-react";
import { Card } from "../ui/Card";
import { SizingResults } from "./SizingResults";
import { useVillageSizing } from "../../hooks/useVillageSizing";
import { VILLAGE_SCENARIOS } from "../../data/scenarios";

// The single-farm sizing agent above (ConfigPanel/SizingResults) answers "how should one
// farm be built?". This answers a different question the project tested separately: "does
// the answer change once you aggregate a whole village's demand?" It hits its own backend
// endpoint (/api/village/size) that runs the same bounded search against a real 100-
// household, 20-farm load model -- not a scaled-up guess.
export function VillageSizing() {
  const { sizing, loading, error, activeScenario, run } = useVillageSizing();

  return (
    <Card id="village-scale" className="p-6 sm:p-8">
      <div className="flex items-center gap-2">
        <Landmark className="h-4 w-4 text-[#EA580C]" />
        <span className="font-mono text-[10px] font-bold uppercase tracking-[0.16em] text-[#EA580C]">
          Village-Scale Validation
        </span>
      </div>
      <h3 className="mt-1 font-heading text-xl font-bold tracking-tight text-slate-950">
        Does wind ever win once demand is a whole village, not one farm?
      </h3>
      <p className="mt-1 text-sm text-slate-500">
        This runs the same bounded search agent against a real aggregate load -- 100
        households, 20 farms, a dairy chiller and the water supply -- instead of one
        farm's demand. It's a live, shortened-horizon version of a 365-day study already
        run offline; both agree on the answer.
      </p>

      <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2">
        {VILLAGE_SCENARIOS.map((s) => {
          const isThisLoading = loading && activeScenario === s.name;
          return (
            <button
              key={s.name}
              onClick={() => run(s.name, s.overrides)}
              disabled={loading}
              className="flex items-start justify-between gap-3 rounded-xl border border-slate-200 bg-slate-50/60 p-4 text-left transition-colors hover:border-[#EA580C] hover:bg-orange-50/40 disabled:opacity-60 cursor-pointer"
            >
              <div>
                <div className="font-mono text-xs font-bold uppercase tracking-wider text-slate-800">
                  {s.name}
                </div>
                <div className="mt-1 text-[11px] text-slate-500">{s.question}</div>
              </div>
              {isThisLoading ? (
                <RotateCw className="mt-0.5 h-4 w-4 flex-none animate-spin text-[#EA580C]" />
              ) : null}
            </button>
          );
        })}
      </div>

      {loading && (
        <p className="mt-4 font-mono text-[11px] text-slate-400">
          Running a real bounded search over a 60-configuration village lattice
          (~20-40 seconds)...
        </p>
      )}

      {error && (
        <div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-3 font-mono text-xs text-red-700">
          {error}
        </div>
      )}

      {sizing && (
        <div className="mt-5">
          <SizingResults data={sizing} />
        </div>
      )}
    </Card>
  );
}
