import { useState } from "react";
import { AppShell } from "../../components/layout/AppShell";
import { PageNav } from "../../components/layout/PageNav";
import type { DashboardTabId } from "../../components/layout/PageNav";
import { HeroSection } from "../../components/dashboard/HeroSection";
import { SystemPipeline } from "../../components/dashboard/SystemPipeline";
import { ConfigPanel } from "../../components/dashboard/ConfigPanel";
import { KPIGrid } from "../../components/dashboard/KPIGrid";
import { EnergyFlow } from "../../components/dashboard/EnergyFlow";
import { AIOptimizer } from "../../components/dashboard/AIOptimizer";
import { EnergyTelemetry } from "../../components/dashboard/EnergyTelemetry";
import { AgriculturePanel } from "../../components/dashboard/AgriculturePanel";
import { CommunityImpact } from "../../components/dashboard/CommunityImpact";
import { VillageSizing } from "../../components/dashboard/VillageSizing";

import { useDashboard } from "../../hooks/useDashboard";
import { useEnergyData } from "../../hooks/useEnergyData";
import { useOptimizer } from "../../hooks/useOptimizer";

export default function Dashboard() {
  const { kpis } = useDashboard();
  // Which single tab is visible below the Hero. Sections stay mounted (just hidden) when
  // not active, so switching away and back never loses a sizing run, an advice fetch, or
  // any other in-progress result -- only visibility changes, not component state.
  const [activeTab, setActiveTab] = useState<DashboardTabId>("results");
  const show = (id: DashboardTabId) => (activeTab === id ? "" : "hidden");

  const {
    timeRange,
    setTimeRange,
    data: energyData,
    loading: isEnergyLoading,
    source: energySource,
  } = useEnergyData();

  const {
    state: optState,
    currentStep: optStep,
    lastOptimized,
    metrics: optMetrics,
    errorMessage: optError,
    execute: handleRunOptimization,
  } = useOptimizer();

  return (
    <AppShell>
      {/* Hero -- always visible */}
      <HeroSection />

      {/* Page switcher + Dashboard tabs -- only the selected tab's section is visible */}
      <PageNav activeTab={activeTab} onTabChange={setActiveTab} />

      <div className={show("how-it-works")}>
        <SystemPipeline />
      </div>

      <div className={show("configuration")}>
        <ConfigPanel />
      </div>

      <div className={show("village-scale")}>
        <VillageSizing />
      </div>

      <div className={show("results")} id="results">
        <KPIGrid kpis={kpis} />
      </div>

      <div className={show("energy-flow")}>
        <EnergyFlow />
      </div>

      <div className={`${show("telemetry")} grid grid-cols-1 lg:grid-cols-[1.65fr_1fr] gap-8 items-start`}>
        <EnergyTelemetry
          data={energyData}
          timeRange={timeRange}
          onTimeRangeChange={setTimeRange}
          isLoading={isEnergyLoading}
          source={energySource}
        />
        <AIOptimizer
          state={optState}
          currentStep={optStep}
          lastOptimized={lastOptimized}
          metrics={optMetrics}
          errorMessage={optError}
          onExecute={handleRunOptimization}
        />
      </div>

      {/* Infrastructure and diagnostic-health panels were removed here: they had no
          real backend to read from (no live SCADA/telemetry exists in this project),
          rendered fixed numbers regardless of the props they were given, and included
          a generator start/stop control and a sensor-calibration button that operated
          on nothing real. A fake control that always reports success is worse than no
          control. See docs/phase2-audit.md, which already flagged this. */}

      <div className={show("agriculture")}>
        <AgriculturePanel />
      </div>

      <div className={show("community")}>
        <CommunityImpact />
      </div>
    </AppShell>
  );
}
