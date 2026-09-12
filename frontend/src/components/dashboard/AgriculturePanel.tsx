import { Sprout, Droplets, Sun, BrainCircuit, CheckCircle2, RotateCw, AlertCircle } from "lucide-react";
import { Card } from "../ui/Card";
import { StatusPill } from "../ui/StatusPill";
import { dashboardImages } from "../../data/dashboardData";
import { useAdvice } from "../../hooks/useAdvice";

export function AgriculturePanel() {
  const { advice, loading, error, state, getAdvice } = useAdvice();

  return (
    <Card id="agriculture" className="p-6 sm:p-8 overflow-hidden">
      <div className="flex flex-wrap items-start justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-100 bg-emerald-50 px-2.5 py-1 font-mono text-[10px] font-bold uppercase tracking-[0.16em] text-emerald-700">
              <Sprout className="h-3.5 w-3.5" />
              Smart Agriculture
            </div>
            {state === "success" && (
              <div className="inline-flex items-center rounded-full border border-blue-200 bg-blue-50 px-2 py-0.5 font-mono text-[9px] font-bold uppercase tracking-wider text-blue-700">
                REAL API
              </div>
            )}
          </div>
          <h3 className="mt-2 font-heading text-2xl font-bold tracking-tight text-slate-950">
            Solar Irrigation & Agricultural Loads
          </h3>
          <p className="text-sm text-slate-500">
            AI-powered scheduling for deep-borewell pumps to minimize diesel cost
          </p>
        </div>

        <div className="flex flex-col items-end gap-2">
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-slate-100 border border-slate-200 px-2.5 py-1 font-mono text-[9px] font-bold uppercase tracking-wider text-slate-500">
              SIMULATED TELEMETRY
            </span>
            <StatusPill tone="green" dot>PUMP OPERATIONAL</StatusPill>
          </div>
          <button
            onClick={getAdvice}
            disabled={loading}
            className="mt-2 inline-flex items-center gap-1.5 rounded-lg border border-emerald-200 bg-emerald-600 px-4 py-2 font-mono text-[11px] font-bold uppercase tracking-wider text-white transition-all hover:bg-emerald-700 disabled:opacity-60"
          >
            {loading ? <RotateCw className="h-3.5 w-3.5 animate-spin" /> : <BrainCircuit className="h-3.5 w-3.5" />}
            {loading ? "Analyzing..." : "Get Irrigation Advice"}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
        
        {/* Left Side: Advice UI */}
        <div className="space-y-6">
          {state === "idle" && (
             <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50/50 p-8 text-center text-slate-500">
                <BrainCircuit className="mx-auto h-8 w-8 mb-3 opacity-50" />
                <p className="font-mono text-sm">Click "Get Irrigation Advice" to request an optimized schedule from the AI.</p>
             </div>
          )}

          {state === "loading" && (
            <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-6 text-emerald-800 animate-pulse">
              <div className="flex items-center gap-3 font-mono font-bold text-sm mb-4">
                <RotateCw className="h-5 w-5 animate-spin" />
                ANALYZING IRRIGATION DEMAND...
              </div>
              <ul className="text-xs space-y-2 ml-8 list-disc opacity-80 font-mono">
                <li>Evaluating Energy availability</li>
                <li>Analyzing Grid Tariffs & Cost</li>
                <li>Minimizing Diesel dependency</li>
                <li>Simulating Schedule options</li>
              </ul>
            </div>
          )}

          {state === "error" && (
            <div className="rounded-2xl border border-red-200 bg-red-50 p-6">
              <div className="flex items-center gap-2 text-red-700 font-bold font-heading mb-2">
                <AlertCircle className="h-5 w-5" />
                IRRIGATION ADVICE UNAVAILABLE
              </div>
              <p className="text-sm text-red-600 mb-4">Unable to calculate a recommendation.</p>
              <p className="text-xs text-red-500 font-mono bg-white/50 p-2 rounded border border-red-100">{error}</p>
            </div>
          )}

          {state === "success" && advice && (
            <div className="space-y-4">
              <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5">
                <h4 className="font-mono text-[10px] font-bold uppercase tracking-[0.16em] text-emerald-700 mb-4 flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4" /> Smart Irrigation Recommendation
                </h4>
                
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
                  <div className="bg-white p-3 rounded-xl border border-emerald-100 shadow-sm">
                    <div className="font-mono text-[9px] uppercase text-slate-400 font-bold">Best Start</div>
                    <div className="mt-1 font-mono text-xl font-bold text-slate-900">{advice.best_start.toString().padStart(2, '0')}:00</div>
                  </div>
                  <div className="bg-white p-3 rounded-xl border border-emerald-100 shadow-sm">
                    <div className="font-mono text-[9px] uppercase text-slate-400 font-bold">Duration</div>
                    <div className="mt-1 font-mono text-xl font-bold text-slate-900">{advice.hours_needed} hr</div>
                  </div>
                  <div className="bg-white p-3 rounded-xl border border-emerald-100 shadow-sm">
                    <div className="font-mono text-[9px] uppercase text-slate-400 font-bold">Cost Saved</div>
                    <div className="mt-1 font-mono text-xl font-bold text-emerald-600">₹{advice.cost_saved_inr}</div>
                  </div>
                  <div className="bg-white p-3 rounded-xl border border-emerald-100 shadow-sm">
                    <div className="font-mono text-[9px] uppercase text-slate-400 font-bold">Diesel Saved</div>
                    <div className="mt-1 font-mono text-xl font-bold text-emerald-600">{advice.diesel_saved_litres} L</div>
                  </div>
                </div>

                <div className="bg-white p-4 rounded-xl border border-emerald-100 shadow-sm text-sm text-slate-700 leading-relaxed">
                  <strong className="block text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-1">AI Briefing</strong>
                  {advice.briefing}
                </div>
              </div>

              {advice.options.length > 0 && (
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
                  <h4 className="font-mono text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500 mb-3">
                    Alternative Schedules
                  </h4>
                  <div className="space-y-2">
                    {advice.options.map((opt, i) => (
                      <div key={i} className={`flex items-center justify-between p-3 rounded-lg border text-sm font-mono ${opt.start_hour === advice.best_start ? 'border-emerald-500 bg-emerald-50 text-emerald-900 font-bold' : 'border-slate-200 bg-white text-slate-700'}`}>
                        <div className="flex items-center gap-3">
                          <span className="w-12">{opt.start_hour.toString().padStart(2, '0')}:00</span>
                          {opt.start_hour === advice.best_start && <span className="text-[9px] bg-emerald-200 text-emerald-800 px-1.5 py-0.5 rounded-sm uppercase tracking-wider">Best</span>}
                        </div>
                        <div className="flex items-center gap-4 text-right">
                          <span className="w-16">₹{opt.cost_inr.toFixed(1)}</span>
                          <span className="w-20 text-slate-500">{opt.diesel_litres.toFixed(1)} L diesel</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Micro Flow Relationship */}
          <div className="rounded-2xl border border-emerald-100 bg-emerald-50/50 p-4 hidden lg:block">
            <span className="font-mono text-[10px] uppercase tracking-wider font-bold text-emerald-800 block mb-3">
              Renewable Agricultural Cycle
            </span>
            <div className="flex flex-wrap items-center justify-between gap-2 text-xs font-mono">
              <span className="inline-flex items-center gap-1 text-amber-700 bg-white px-2.5 py-1 rounded-lg shadow-2xs border border-amber-100">
                <Sun className="h-3.5 w-3.5" /> Solar
              </span>
              <span className="text-emerald-400 font-bold">→</span>
              <span className="inline-flex items-center gap-1 text-[#EA580C] bg-white px-2.5 py-1 rounded-lg shadow-2xs border border-orange-100">
                <BrainCircuit className="h-3.5 w-3.5" /> AI 
              </span>
              <span className="text-emerald-400 font-bold">→</span>
              <span className="inline-flex items-center gap-1 text-blue-700 bg-white px-2.5 py-1 rounded-lg shadow-2xs border border-blue-100">
                <Droplets className="h-3.5 w-3.5" /> Pump
              </span>
              <span className="text-emerald-400 font-bold">→</span>
              <span className="inline-flex items-center gap-1 text-emerald-700 bg-white px-2.5 py-1 rounded-lg shadow-2xs border border-emerald-100">
                <Sprout className="h-3.5 w-3.5" /> Yield
              </span>
            </div>
          </div>
        </div>

        {/* Right Agricultural Image Panel */}
        <div className="relative h-[400px] lg:h-full overflow-hidden rounded-2xl border border-slate-200 shadow-inner group">
          <img
            src={dashboardImages.irrigation}
            alt="Agricultural field powered by solar irrigation"
            className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-105"
            loading="lazy"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-slate-950/20 to-transparent" />
          <div className="absolute bottom-4 left-4 right-4 text-white">
            <div className="font-mono text-[10px] uppercase tracking-wider text-emerald-300">
              Community Farm Microgrid Feed #AG-02
            </div>
            <div className="mt-1 font-heading text-lg font-bold">
              Reliable Water for 42 Farming Families
            </div>
          </div>
        </div>

      </div>
    </Card>
  );
}
