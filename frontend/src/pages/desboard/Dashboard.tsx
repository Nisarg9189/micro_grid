import { AppShell } from "../../components/layout/AppShell";
import { HeroSection } from "../../components/dashboard/HeroSection";
import { ConfigPanel } from "../../components/dashboard/ConfigPanel";
import { KPIGrid } from "../../components/dashboard/KPIGrid";
import { EnergyFlow } from "../../components/dashboard/EnergyFlow";
import { AIOptimizer } from "../../components/dashboard/AIOptimizer";
import { EnergyTelemetry } from "../../components/dashboard/EnergyTelemetry";
import { AgriculturePanel } from "../../components/dashboard/AgriculturePanel";
import { CommunityImpact } from "../../components/dashboard/CommunityImpact";

import { useDashboard } from "../../hooks/useDashboard";
import { useEnergyData } from "../../hooks/useEnergyData";
import { useOptimizer } from "../../hooks/useOptimizer";

export default function Dashboard() {
  const { mode, setMode, kpis } = useDashboard();

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
    <AppShell mode={mode} onModeChange={setMode}>
      {/* 1. Hero Section */}
      <HeroSection
        onRunOptimization={handleRunOptimization}
        isOptimizing={optState === "optimizing"}
      />

      {/* 2. Configuration -- site, hardware, load and prices, wired to every result below */}
      <ConfigPanel />

      {/* 3. KPI Summary Grid */}
      <KPIGrid kpis={kpis} />

      {/* 4. Live Energy Flow Diagram */}
      <EnergyFlow />

      {/* 5. Split Section: Telemetry & AI Optimizer */}
      <div className="grid grid-cols-1 lg:grid-cols-[1.65fr_1fr] gap-8 items-start">
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

      {/* 6. Smart Agriculture & Solar Irrigation -- genuinely wired to /api/advice */}
      <AgriculturePanel />

      {/* 7. Community Social & Environmental Impact */}
      <CommunityImpact />
    </AppShell>
  );
}
