import { Cpu, ArrowRight, BrainCircuit, Sun, Battery, Activity } from "lucide-react";
import { dashboardImages } from "../../data/dashboardData";

export interface HeroSectionProps {
  onRunOptimization: () => void;
  isOptimizing?: boolean;
}

export function HeroSection({ onRunOptimization, isOptimizing = false }: HeroSectionProps) {
  const scrollToFlow = () => {
    document.getElementById("energy-flow")?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <section className="grid overflow-hidden rounded-[28px] border border-slate-200 bg-white shadow-[0_20px_60px_rgba(15,23,42,0.06)] lg:grid-cols-[1.05fr_0.95fr]">
      {/* Left Pitch & Actions */}
      <div className="relative flex flex-col justify-center p-7 sm:p-10 lg:p-12">
        <div className="mb-5 inline-flex w-fit items-center gap-2 rounded-full border border-orange-100 bg-orange-50 px-3 py-1.5 font-mono text-[10px] font-bold uppercase tracking-[0.16em] text-[#EA580C]">
          <BrainCircuit className="h-3.5 w-3.5" />
          AI-Powered Rural Energy
        </div>

        <h2 className="max-w-xl font-heading text-4xl font-bold leading-[1.05] tracking-tight text-slate-950 sm:text-5xl lg:text-6xl">
          Smarter energy for{" "}
          <span className="bg-gradient-to-r from-[#EA580C] via-[#F7931A] to-[#FFD600] bg-clip-text text-transparent">
            rural India.
          </span>
        </h2>

        <p className="mt-5 max-w-lg text-base leading-7 text-slate-600 sm:text-lg">
          Intelligent energy optimization for resilient rural communities.
          Optimize solar, balance batteries, reduce diesel, and secure farm irrigation.
        </p>

        {/* Primary CTA Buttons */}
        <div className="mt-8 flex flex-wrap gap-3.5">
          <button
            onClick={onRunOptimization}
            disabled={isOptimizing}
            className="inline-flex min-h-11 items-center gap-2 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] px-5 font-mono text-[11px] font-bold uppercase tracking-wider text-white shadow-[0_10px_25px_rgba(234,88,12,0.25)] transition-all duration-300 hover:scale-[1.02] hover:shadow-[0_14px_35px_rgba(234,88,12,0.32)] disabled:opacity-60 cursor-pointer"
          >
            <Cpu className={`h-4 w-4 ${isOptimizing ? "animate-spin" : ""}`} />
            {isOptimizing ? "Optimizing..." : "Run AI Optimization"}
          </button>
          <button
            onClick={scrollToFlow}
            className="inline-flex min-h-11 items-center gap-2 rounded-full border border-slate-300 bg-white px-5 font-mono text-[11px] font-bold uppercase tracking-wider text-slate-800 transition-all duration-300 hover:border-[#EA580C] hover:bg-orange-50 cursor-pointer"
          >
            View Energy Flow
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>

        {/* Mini Highlights Grid */}
        <div className="mt-9 grid max-w-lg grid-cols-3 gap-3">
          {[
            ["3.0 kW", "Solar Output", Sun, "text-[#EA580C]"],
            ["84%", "Battery SOC", Battery, "text-green-600"],
            ["100%", "Reliability", Activity, "text-blue-600"],
          ].map(([val, label, Icon, colorClass]) => (
            <div key={label as string} className="rounded-xl border border-slate-200 bg-slate-50/80 p-3">
              <div className="flex items-center gap-1.5">
                {/* @ts-ignore */}
                <Icon className={`h-3.5 w-3.5 ${colorClass}`} />
                <span className="font-mono text-base font-bold text-slate-950">{val as string}</span>
              </div>
              <div className="mt-1 font-mono text-[9px] uppercase tracking-wider text-slate-400">
                {label as string}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Right Rural Image + Glass Telemetry Overlay */}
      <div className="relative min-h-[360px] overflow-hidden lg:min-h-[520px]">
        <img
          src={dashboardImages.hero}
          alt="Solar panels providing clean energy to an Indian rural farm landscape"
          className="absolute inset-0 h-full w-full object-cover"
          loading="eager"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/70 via-slate-950/20 to-transparent lg:bg-gradient-to-r lg:from-slate-950/30 lg:to-transparent" />

        {/* Floating Glass Telemetry Card */}
        <div className="absolute right-5 top-5 rounded-2xl border border-white/40 bg-white/85 p-4 shadow-2xl backdrop-blur-xl sm:right-7 sm:top-7">
          <div className="mb-2 flex items-center justify-between gap-4 font-mono text-[9px] font-bold uppercase tracking-[0.16em] text-slate-500">
            <span>Live Telemetry</span>
            <span className="rounded bg-green-100 px-1.5 py-0.5 text-green-700">Online</span>
          </div>
          <div className="flex items-center gap-2 font-mono text-xs font-bold text-slate-900">
            <span className="h-2 w-2 animate-pulse rounded-full bg-green-500" />
            DISPATCH // OPTIMAL
          </div>
          <div className="mt-3 space-y-2 border-t border-slate-200/80 pt-3 font-mono text-[11px]">
            <div className="flex justify-between gap-8">
              <span className="text-slate-500">Solar PV</span>
              <span className="font-bold text-[#EA580C]">3.0 kW</span>
            </div>
            <div className="flex justify-between gap-8">
              <span className="text-slate-500">LFP Battery</span>
              <span className="font-bold text-green-600">84% SOC</span>
            </div>
            <div className="flex justify-between gap-8">
              <span className="text-slate-500">Grid Feed</span>
              <span className="font-bold text-blue-600">3.8 kW (Sync)</span>
            </div>
            <div className="flex justify-between gap-8">
              <span className="text-slate-500">Village Load</span>
              <span className="font-bold text-slate-900">5.8 kW</span>
            </div>
          </div>
        </div>

        {/* Bottom Banner */}
        <div className="absolute bottom-5 left-5 rounded-2xl border border-white/30 bg-slate-950/80 px-4 py-3 text-white shadow-xl backdrop-blur-md sm:bottom-7 sm:left-7">
          <div className="font-mono text-[9px] uppercase tracking-[0.15em] text-white/60">
            Renewable First Framework
          </div>
          <div className="mt-0.5 font-heading text-base font-semibold">
            Solar → AI Optimization → Rural Prosperity
          </div>
        </div>
      </div>
    </section>
  );
}
