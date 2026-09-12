import {
  Cloud,
  TrendingUp,
  Settings2,
  BrainCircuit,
  BarChart3,
  Sprout,
  ArrowRight,
  ArrowDown,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Card } from "../ui/Card";

interface Stage {
  icon: LucideIcon;
  title: string;
  detail: string;
  href?: string; // present only for stages that are an actual section on this page
}

// The real pipeline this project runs, start to end -- not a marketing diagram, a map
// of what actually executes. Weather and forecasting happen inside /api/simulate and
// have no page section of their own, so those two steps aren't links; every step from
// Configure onward corresponds to a section further down this same page, and clicking
// one scrolls straight to it.
const STAGES: Stage[] = [
  {
    icon: Cloud,
    title: "Weather",
    detail: "Open-Meteo ERA5 reanalysis for the configured site and year -- real historical data, not synthetic.",
  },
  {
    icon: TrendingUp,
    title: "Forecast",
    detail: "Solar, wind, load and feeder-availability predictions, carrying the site's measured ~17.5% forecast error.",
  },
  {
    icon: Settings2,
    title: "Configure & Size",
    detail: "Set the site, hardware, loads and prices yourself, or let the model search for the cheapest system.",
    href: "#configuration",
  },
  {
    icon: BrainCircuit,
    title: "MPC Dispatch",
    detail: "A 24-hour receding-horizon linear program decides solar, battery, feeder and diesel every hour.",
    href: "#energy-flow",
  },
  {
    icon: BarChart3,
    title: "Results",
    detail: "Cost, diesel, reliability and CO2 -- and every hour of the dispatch it took to get there.",
    href: "#telemetry",
  },
  {
    icon: Sprout,
    title: "Advisory",
    detail: "The same dispatch turned into a farmer's irrigation schedule, in English, Gujarati or Hindi.",
    href: "#agriculture",
  },
];

function scrollTo(href: string) {
  document.querySelector(href)?.scrollIntoView({ behavior: "smooth", block: "start" });
}

export function SystemPipeline() {
  return (
    <Card className="p-6 sm:p-8">
      <span className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-[#EA580C]">
        How It Works
      </span>
      <h3 className="mt-1 font-heading text-2xl font-bold tracking-tight text-slate-950">
        From weather to a farmer's schedule
      </h3>
      <p className="mt-1 max-w-2xl text-sm text-slate-500">
        The whole pipeline this page runs, start to end. The first two steps happen
        inside every simulation; the rest are sections on this page -- click a step to
        jump straight to it.
      </p>

      <div className="mt-6 flex flex-col gap-2 lg:flex-row lg:items-stretch lg:gap-0">
        {STAGES.map((stage, i) => {
          const Icon = stage.icon;
          const isLast = i === STAGES.length - 1;
          const content = (
            <div className="flex h-full flex-col items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50/70 p-4 text-center transition-colors hover:border-[#EA580C] hover:bg-orange-50/60">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-[#EA580C] shadow-sm">
                <Icon className="h-5 w-5" />
              </div>
              <div className="font-mono text-[10px] font-bold uppercase tracking-wider text-slate-800">
                {i + 1}. {stage.title}
              </div>
              <p className="text-[11px] leading-snug text-slate-500">{stage.detail}</p>
            </div>
          );

          return (
            <div key={stage.title} className="flex flex-1 flex-col items-stretch lg:flex-row">
              <div className="flex-1">
                {stage.href ? (
                  <button
                    onClick={() => scrollTo(stage.href!)}
                    className="h-full w-full cursor-pointer text-left"
                    aria-label={`Jump to ${stage.title}`}
                  >
                    {content}
                  </button>
                ) : (
                  content
                )}
              </div>
              {!isLast && (
                <div className="flex items-center justify-center py-1 lg:px-2 lg:py-0">
                  <ArrowDown className="h-4 w-4 text-slate-300 lg:hidden" />
                  <ArrowRight className="hidden h-4 w-4 flex-none text-slate-300 lg:block" />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </Card>
  );
}
