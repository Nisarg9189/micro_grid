import { KpiCard } from "../ui/KpiCard";
import type { KPI } from "../../types/dashboard";

interface KPIGridProps {
  kpis: KPI[];
}

export function KPIGrid({ kpis }: KPIGridProps) {
  return (
    <section className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-4">
      {kpis.map((kpi) => (
        <KpiCard
          key={kpi.title}
          title={kpi.title}
          value={kpi.value}
          unit={kpi.unit}
          change={kpi.change}
          description={kpi.description}
          trend={kpi.trend}
          tone={kpi.tone}
          icon={kpi.icon}
        />
      ))}
    </section>
  );
}
