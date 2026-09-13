import { Link, useLocation } from "react-router-dom";
import { LayoutDashboard, BrainCircuit } from "lucide-react";

const PAGES = [
  { label: "Dashboard", to: "/dashboard", icon: LayoutDashboard },
  { label: "Prediction", to: "/", icon: BrainCircuit },
];

// Every Dashboard tab, in display order. The id is what Dashboard.tsx uses to decide
// which section is visible -- nothing here needs to match a DOM anchor any more.
export const DASHBOARD_TABS = [
  { id: "how-it-works", label: "How It Works" },
  { id: "configuration", label: "Configuration" },
  { id: "village-scale", label: "Village Scale" },
  { id: "results", label: "Results" },
  { id: "energy-flow", label: "Energy Flow" },
  { id: "telemetry", label: "Telemetry" },
  { id: "agriculture", label: "Agriculture" },
  { id: "community", label: "Community" },
] as const;

export type DashboardTabId = (typeof DASHBOARD_TABS)[number]["id"];

export interface PageNavProps {
  // Only meaningful on the Dashboard page -- Prediction has no tabs of its own.
  activeTab?: DashboardTabId;
  onTabChange?: (id: DashboardTabId) => void;
}

// The "which page am I on" bar right below the Hero. The Dashboard/Prediction pair are
// real routes (a Link navigates). Below that, on Dashboard, each Dashboard tab shows or
// hides one section -- clicking one leaves only that section's content visible.
export function PageNav({ activeTab, onTabChange }: PageNavProps) {
  const location = useLocation();

  return (
    <nav className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm">
      <div className="flex flex-wrap items-center gap-1.5">
        {PAGES.map((p) => {
          const active = location.pathname === p.to;
          return (
            <Link
              key={p.to}
              to={p.to}
              className={`inline-flex items-center gap-1.5 rounded-xl px-3.5 py-2 font-mono text-[11px] font-bold uppercase tracking-wider transition-all ${
                active
                  ? "bg-slate-950 text-white shadow-sm"
                  : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"
              }`}
            >
              <p.icon className="h-3.5 w-3.5" />
              {p.label}
            </Link>
          );
        })}
      </div>

      {onTabChange && (
        <div className="flex flex-wrap items-center gap-1 border-t border-slate-100 pt-2">
          {DASHBOARD_TABS.map((t) => {
            const active = t.id === activeTab;
            return (
              <button
                key={t.id}
                onClick={() => onTabChange(t.id)}
                className={`rounded-lg px-3 py-1.5 font-mono text-[10px] font-bold uppercase tracking-wider transition-colors cursor-pointer ${
                  active
                    ? "bg-orange-50 text-[#EA580C] border border-orange-200"
                    : "border border-transparent text-slate-500 hover:bg-slate-50 hover:text-slate-900"
                }`}
              >
                {t.label}
              </button>
            );
          })}
        </div>
      )}
    </nav>
  );
}
