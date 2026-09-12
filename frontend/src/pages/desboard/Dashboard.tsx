import { AppShell } from "../../components/layout/AppShell";
import { HeroSection } from "../../components/dashboard/HeroSection";
import { KPIGrid } from "../../components/dashboard/KPIGrid";
import { EnergyFlow } from "../../components/dashboard/EnergyFlow";
import { AIOptimizer } from "../../components/dashboard/AIOptimizer";
import { EnergyTelemetry } from "../../components/dashboard/EnergyTelemetry";
import { InfrastructureStatus } from "../../components/dashboard/InfrastructureStatus";
import { AgriculturePanel } from "../../components/dashboard/AgriculturePanel";
import { CommunityImpact } from "../../components/dashboard/CommunityImpact";
import { SystemHealth } from "../../components/dashboard/SystemHealth";

import { useDashboard } from "../../hooks/useDashboard";
import { useEnergyData } from "../../hooks/useEnergyData";
import { useOptimizer } from "../../hooks/useOptimizer";

export default function Dashboard() {
  const {
    mode,
    setMode,
    generatorRunning,
    isGeneratorPending,
    toggleGenerator,
    isCalibrating,
    calibrationFeedback,
    calibrate,
    infrastructure,
    health,
    kpis,
  } = useDashboard();

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
    recommendation,
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

      {/* 2. KPI Summary Grid */}
      <KPIGrid kpis={kpis} />

      {/* 3. Live Energy Flow Diagram */}
      <EnergyFlow />

      {/* 4. Split Section: Telemetry & AI Optimizer */}
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
          recommendation={recommendation}
          metrics={optMetrics}
          errorMessage={optError}
          onExecute={handleRunOptimization}
        />
      </div>

      {/* 5. Infrastructure Asset Monitoring */}
      <InfrastructureStatus
        items={infrastructure}
        generatorRunning={generatorRunning}
        isGeneratorPending={isGeneratorPending}
        onToggleGenerator={toggleGenerator}
        isCalibrating={isCalibrating}
        calibrationFeedback={calibrationFeedback}
        onCalibrate={calibrate}
      />

      {/* 6. Smart Agriculture & Solar Irrigation */}
      <AgriculturePanel />

      {/* 7. Community Social & Environmental Impact */}
      <CommunityImpact />

      {/* 8. Diagnostic System Health Strip */}
      <SystemHealth items={health} />
    </AppShell>
  );
}