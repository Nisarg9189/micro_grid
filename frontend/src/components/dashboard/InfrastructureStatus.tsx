import { useState } from "react";
import { Sun, Battery, Power, Radio, RefreshCw, CheckCircle2 } from "lucide-react";
import { Card } from "../ui/Card";
import { StatusPill } from "../ui/StatusPill";
import { ProgressBar } from "../ui/ProgressBar";
import { ConfirmModal } from "../ui/ConfirmModal";
import { DEMO_MODE } from "../../data/dashboardData";
import type { InfrastructureStatus as InfraType } from "../../types/infrastructure";

export interface InfrastructureProps {
  items: InfraType[];
  generatorRunning: boolean;
  isGeneratorPending?: boolean;
  onToggleGenerator: (target: boolean) => void;
  isCalibrating?: boolean;
  calibrationFeedback?: string | null;
  onCalibrate: () => void;
}

export function InfrastructureStatus({
  generatorRunning,
  isGeneratorPending = false,
  onToggleGenerator,
  isCalibrating = false,
  calibrationFeedback,
  onCalibrate,
}: InfrastructureProps) {
  const [showGenModal, setShowGenModal] = useState(false);

  const handleGenConfirm = () => {
    setShowGenModal(false);
    onToggleGenerator(!generatorRunning);
  };

  return (
    <div id="infrastructure" className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <span className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-[#EA580C]">
            MICROGRID ASSETS
          </span>
          <h3 className="font-heading text-2xl font-bold tracking-tight text-slate-950">
            Infrastructure Monitoring
          </h3>
        </div>

        {/* Sensor Calibration Action */}
        <div className="flex items-center gap-3">
          {calibrationFeedback && (
            <span aria-live="polite" className="flex items-center gap-1.5 font-mono text-xs font-semibold text-green-700 bg-green-50 px-3 py-1.5 rounded-xl border border-green-200 animate-fadeIn">
              <CheckCircle2 className="h-4 w-4" />
              {calibrationFeedback}
              {DEMO_MODE && <span className="ml-1 rounded bg-green-100/50 px-1 py-0.5 text-[9px] text-green-600 uppercase">SIMULATED</span>}
            </span>
          )}

          <button
            onClick={onCalibrate}
            disabled={isCalibrating}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 font-mono text-xs font-bold uppercase tracking-wider text-slate-700 hover:border-[#EA580C] hover:bg-orange-50 hover:text-[#EA580C] shadow-sm transition-all disabled:opacity-50 cursor-pointer"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isCalibrating ? "animate-spin text-[#EA580C]" : ""}`} />
            {isCalibrating ? "Calibrating..." : "Calibrate Sensors"}
          </button>
        </div>
      </div>

      {/* 4 Asset Cards Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-4">
        
        {/* Solar Card */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <span className="font-mono text-[11px] font-bold uppercase tracking-wider text-slate-500">
              SOLAR ARRAY
            </span>
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-50 border border-amber-100 text-[#F59E0B]">
              <Sun className="h-5 w-5" />
            </div>
          </div>

          <div className="mb-2 font-mono text-2xl font-bold text-slate-950">
            3.0 kW <span className="text-xs text-slate-400 font-semibold">/ 3 kWp</span>
          </div>

          <ProgressBar value={100} tone="orange" height="sm" className="mb-3" />

          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-slate-500">Generation: 100% capacity</span>
            <StatusPill tone="green" dot>ACTIVE</StatusPill>
          </div>
        </Card>

        {/* Battery Card */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <span className="font-mono text-[11px] font-bold uppercase tracking-wider text-slate-500">
              LFP STORAGE
            </span>
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-green-50 border border-green-100 text-[#16A34A]">
              <Battery className="h-5 w-5" />
            </div>
          </div>

          <div className="mb-2 font-mono text-2xl font-bold text-slate-950">
            84% <span className="text-xs text-slate-400 font-semibold">SOC (4.2 kWh)</span>
          </div>

          <ProgressBar value={84} tone="green" height="sm" className="mb-3" />

          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-slate-500">Total: 5.0 kWh Bank</span>
            <StatusPill tone="green" dot>HEALTHY</StatusPill>
          </div>
        </Card>

        {/* Generator Card with Safety Confirm Modal */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <span className="font-mono text-[11px] font-bold uppercase tracking-wider text-slate-500">
              DIESEL GENSET
            </span>
            <div className={`flex h-10 w-10 items-center justify-center rounded-xl border ${generatorRunning ? "bg-red-50 border-red-100 text-red-600" : "bg-slate-100 border-slate-200 text-slate-500"}`}>
              <Power className="h-5 w-5" />
            </div>
          </div>

          <div className="mb-2 font-mono text-2xl font-bold text-slate-950">
            3.5 kVA <span className="text-xs text-slate-400 font-semibold">Reserve</span>
          </div>

          <div className="text-xs font-mono text-slate-500 mb-3">
            {generatorRunning ? "Running (Peak Backup Mode)" : "Cutoff • 916 L Conserved"}
          </div>

          <div className="flex items-center justify-between">
            <StatusPill tone={generatorRunning ? "danger" : "slate"} dot>
              {generatorRunning ? "RUNNING" : "STANDBY"}
            </StatusPill>

            <button
              onClick={() => setShowGenModal(true)}
              disabled={isGeneratorPending}
              aria-haspopup="dialog"
              className={`rounded-xl px-3 py-1 font-mono text-[10px] font-bold uppercase tracking-wider transition-all cursor-pointer ${
                generatorRunning
                  ? "bg-red-600 text-white hover:bg-red-700 shadow-sm"
                  : "border border-slate-300 bg-white text-slate-700 hover:border-[#EA580C] hover:bg-orange-50"
              }`}
            >
              {isGeneratorPending
                ? "Pending..."
                : generatorRunning
                ? "Stop Genset"
                : "Start Genset"}
            </button>
          </div>
        </Card>

        {/* DISCOM Grid Card */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <span className="font-mono text-[11px] font-bold uppercase tracking-wider text-slate-500">
              DISCOM GRID
            </span>
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 border border-blue-100 text-[#2563EB]">
              <Radio className="h-5 w-5" />
            </div>
          </div>

          <div className="mb-2 font-mono text-2xl font-bold text-slate-950">
            ₹4.20 <span className="text-xs text-slate-400 font-semibold">/ unit (Off-Peak)</span>
          </div>

          <div className="text-xs font-mono text-slate-500 mb-3">
            Feeder Synced • Frequency 50.02 Hz
          </div>

          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-slate-500">Rural Ag Feeder</span>
            <StatusPill tone="blue" dot>CONNECTED</StatusPill>
          </div>
        </Card>

      </div>

      {/* Safety Confirmation Modal for Generator */}
      <ConfirmModal
        isOpen={showGenModal}
        title={generatorRunning ? "Stop Diesel Generator?" : "Start Diesel Generator?"}
        message={
          generatorRunning
            ? "Stopping the backup generator will switch the load entirely to solar and battery storage. Ensure storage levels are sufficient."
            : "Starting the diesel backup generator will consume fuel (approx ₹95/L). GramUrja AI recommends using stored solar energy first."
        }
        confirmLabel={generatorRunning ? "Confirm Shutdown" : "Start Backup Genset"}
        isDangerous={!generatorRunning}
        onConfirm={handleGenConfirm}
        onCancel={() => setShowGenModal(false)}
      />
    </div>
  );
}
