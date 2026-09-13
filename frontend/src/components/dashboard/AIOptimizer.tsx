import { Cpu, Sparkles, AlertCircle, CheckCircle2, RotateCw } from "lucide-react";
import { Card } from "../ui/Card";
import { StatusPill } from "../ui/StatusPill";
import { FeatureBar } from "../ui/FeatureBar";
import type { OptimizationState } from "../../types/dashboard";

export interface AIOptimizerProps {
  state: OptimizationState;
  currentStep?: string;
  lastOptimized?: string;
  metrics: {
    horizon: string;
    lastRunTime: string;
  };
  errorMessage?: string | null;
  onExecute: () => void;
}

export function AIOptimizer({
  state,
  currentStep,
  lastOptimized = "Just now",
  metrics,
  errorMessage,
  onExecute,
}: AIOptimizerProps) {
  const isRunning = state === "optimizing";

  return (
    <Card className="p-6 sm:p-8 relative overflow-hidden flex flex-col justify-between">
      <div>
        {/* Header */}
        <div className="flex items-start justify-between gap-4 mb-6">
          <div>
            <div className="flex items-center gap-2">
              <div className="inline-flex items-center gap-2 rounded-full border border-orange-100 bg-orange-50 px-2.5 py-1 font-mono text-[10px] font-bold uppercase tracking-[0.16em] text-[#EA580C]">
                <Sparkles className="h-3.5 w-3.5" />
                Intelligence Engine
              </div>
              <div className="inline-flex items-center rounded-full border border-blue-200 bg-blue-50 px-2 py-0.5 font-mono text-[9px] font-bold uppercase tracking-wider text-blue-700">
                REAL API
              </div>
            </div>
            <h3 className="mt-2 font-heading text-2xl font-bold tracking-tight text-slate-950">
              GRAMURJA AI Optimizer
            </h3>
            <p className="text-sm text-slate-500">
              Real-time LP dispatch engine for off-grid rural communities
            </p>
          </div>

          <StatusPill
            tone={state === "optimizing" ? "orange" : state === "error" ? "danger" : "green"}
            dot
          >
            {state === "optimizing" ? "SOLVING LP..." : state === "error" ? "ERROR" : "OPTIMAL"}
          </StatusPill>
        </div>

        <FeatureBar tone="orange">
          What this does: re-solves the hour-by-hour dispatch (solar, battery, feeders,
          diesel) as a linear program every time you press Run -- this panel shows that
          solve happening, not a canned animation.
        </FeatureBar>

        {/* LP Metrics -- only what the backend actually reports */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          <div className="rounded-xl border border-slate-100 bg-slate-50/70 p-3">
            <div className="font-mono text-[10px] uppercase text-slate-400 mb-1">Horizon</div>
            <div className="font-mono font-bold text-slate-800 text-sm">{metrics.horizon}</div>
          </div>
          <div className="rounded-xl border border-slate-100 bg-slate-50/70 p-3">
            <div className="font-mono text-[10px] uppercase text-slate-400 mb-1">Last Run</div>
            <div className="font-mono font-bold text-slate-800 text-sm truncate">{metrics.lastRunTime}</div>
          </div>
        </div>

        {/* Dispatch Result Card */}
        {state === "success" && (
          <div className="rounded-2xl border border-orange-200/80 bg-gradient-to-br from-orange-50/70 via-amber-50/40 to-white p-5 shadow-sm">
            <h4 className="font-heading text-base font-bold text-slate-950 mb-1">
              Dispatch Plan Ready
            </h4>
            <p className="text-sm text-slate-600 leading-relaxed">
              The Linear Program successfully resolved the optimal dispatch strategy for the horizon. Data on the left has been populated with the solver results.
            </p>
          </div>
        )}

        {/* Dynamic Optimization Progress or Error */}
        <div aria-live="polite" className="mt-4 min-h-[52px]">
          {isRunning && (
            <div className="rounded-xl border border-orange-200 bg-orange-50 p-4 font-mono text-xs text-[#EA580C] flex items-center gap-3 animate-pulse transition-all duration-300">
              <RotateCw className="h-4 w-4 animate-spin" />
              <span>{currentStep || "Running Linear Optimization..."}</span>
            </div>
          )}

          {state === "success" && (
            <div className="rounded-xl border border-green-200 bg-green-50 p-3 font-mono text-xs text-green-800 flex items-center gap-2.5 transition-all duration-300">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              <span>{currentStep || "OPTIMAL DISPATCH FOUND — Synced with grid and battery."}</span>
            </div>
          )}

          {state === "error" && (
            <div className="rounded-xl border border-red-200 bg-red-50 p-3 font-mono text-xs text-red-700 flex items-center gap-2 transition-all duration-300">
              <AlertCircle className="h-4 w-4" />
              <span>{errorMessage || "Optimization failed. Please retry."}</span>
            </div>
          )}
        </div>
      </div>

      {/* Action Execution Footer */}
      <div className="mt-6 pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between gap-4">
        <span className="font-mono text-[11px] text-slate-400">
          Last solved: {lastOptimized}
        </span>

        <button
          onClick={onExecute}
          disabled={isRunning}
          className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-[#EA580C] to-[#F7931A] px-5 py-3 font-mono text-xs font-bold uppercase tracking-wider text-white shadow-[0_6px_20px_rgba(234,88,12,0.25)] transition-all hover:scale-[1.02] hover:shadow-[0_8px_24px_rgba(234,88,12,0.3)] disabled:opacity-60 cursor-pointer"
        >
          <Cpu className={`h-4 w-4 ${isRunning ? "animate-spin" : ""}`} />
          {isRunning ? "Optimizing Dispatch..." : "Execute LP Dispatch Cycle"}
        </button>
      </div>
    </Card>
  );
}
