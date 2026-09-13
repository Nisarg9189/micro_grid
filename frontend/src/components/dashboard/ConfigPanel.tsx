import { useState } from "react";
import { Settings2, Cpu, Ruler, RotateCw, Plus, X } from "lucide-react";
import { Card } from "../ui/Card";
import { NumberField } from "../ui/NumberField";
import { SelectField } from "../ui/SelectField";
import { StatusPill } from "../ui/StatusPill";
import { useSimulationContext } from "../../hooks/SimulationContext";
import { useSizing } from "../../hooks/useSizing";
import { SITE_PRESETS } from "../../data/presets";
import { SizingResults } from "./SizingResults";
import { ScenarioPicker } from "./ScenarioPicker";
import { FeatureBar } from "../ui/FeatureBar";

// Full parity with report/console.html's Controls panel: same fields, same site presets,
// same defaults -- so the two evaluator surfaces answer the same question on the same
// terms. Everything here feeds the one shared params object every API call reads.
export function ConfigPanel() {
  const { params, setParam, setParams, executeSimulation, isLoading } = useSimulationContext();
  const sizing = useSizing();
  // Collapsed by default -- results are the point of the page; the config wall
  // shouldn't be the first thing between a visitor and the numbers they came for.
  const [open, setOpen] = useState(false);

  // Custom sites a visitor adds themselves -- session-only (no backend to persist
  // them to), so they live alongside the four built-in presets for as long as the
  // page stays open.
  const [customSites, setCustomSites] = useState<typeof SITE_PRESETS>([]);
  const [addingSite, setAddingSite] = useState(false);
  const [newSiteName, setNewSiteName] = useState("");
  const [newSiteLat, setNewSiteLat] = useState(params.lat);
  const [newSiteLon, setNewSiteLon] = useState(params.lon);

  const allSites = [...SITE_PRESETS, ...customSites];
  const activePreset = allSites.find((p) => p.lat === params.lat && p.lon === params.lon);
  const busy = isLoading || sizing.loading;

  const startAddingSite = () => {
    setNewSiteName("");
    setNewSiteLat(params.lat);
    setNewSiteLon(params.lon);
    setAddingSite(true);
  };

  const confirmAddSite = () => {
    const name = newSiteName.trim();
    if (!name || !Number.isFinite(newSiteLat) || !Number.isFinite(newSiteLon)) return;
    const site = { name, lat: newSiteLat, lon: newSiteLon, site: name };
    setCustomSites((prev) => [...prev, site]);
    setParams({ lat: site.lat, lon: site.lon, site: site.site });
    setAddingSite(false);
  };

  return (
    <Card id="configuration" className="p-6 sm:p-8">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between gap-4 text-left cursor-pointer"
      >
        <div>
          <div className="flex items-center gap-2">
            <Settings2 className="h-4 w-4 text-[#EA580C]" />
            <span className="font-mono text-[10px] font-bold uppercase tracking-[0.16em] text-[#EA580C]">
              Configuration
            </span>
          </div>
          <h3 className="mt-1 font-heading text-xl font-bold tracking-tight text-slate-950">
            {params.site} &middot; {params.days} days &middot; {params.solar} kWp / {params.wind} kW / {params.battery} kWh
          </h3>
          <p className="text-sm text-slate-500">
            Change anything below, then press "Run the optimiser" to apply it. Every
            number on this page comes from that one live simulation -- nothing re-runs
            on its own.
          </p>
        </div>
        <StatusPill tone="slate">{open ? "Collapse" : "Expand"}</StatusPill>
      </button>

      {open && (
        <div className="mt-6 space-y-6">
          <FeatureBar tone="orange">
            What this does: sets the real hardware, site and prices every API call on
            this page reads -- or click a tested scenario below to reproduce a real
            result instantly, or let the sizing agent choose the hardware for you.
          </FeatureBar>

          <ScenarioPicker />

          <div className="grid grid-cols-1 gap-6 min-w-0 lg:grid-cols-2 xl:grid-cols-4">
            {/* Site */}
            <fieldset className="min-w-0">
              <legend className="mb-2 font-mono text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Site
              </legend>
              <div className="mb-3 flex flex-wrap items-center gap-1.5">
                {allSites.map((preset) => (
                  <button
                    key={preset.name}
                    onClick={() => setParams({ lat: preset.lat, lon: preset.lon, site: preset.site })}
                    className={`rounded-lg border px-2.5 py-1 font-mono text-[10px] font-bold uppercase tracking-wider transition-colors cursor-pointer ${
                      activePreset?.name === preset.name
                        ? "border-[#EA580C] bg-[#EA580C] text-white"
                        : "border-slate-200 bg-slate-50 text-slate-600 hover:border-[#EA580C] hover:text-[#EA580C]"
                    }`}
                  >
                    {preset.name}
                  </button>
                ))}
                <button
                  type="button"
                  onClick={() => (addingSite ? setAddingSite(false) : startAddingSite())}
                  title="Add a custom site"
                  className={`inline-flex h-6 w-6 items-center justify-center rounded-lg border transition-colors cursor-pointer ${
                    addingSite
                      ? "border-[#EA580C] bg-orange-50 text-[#EA580C]"
                      : "border-dashed border-slate-300 text-slate-400 hover:border-[#EA580C] hover:text-[#EA580C]"
                  }`}
                >
                  {addingSite ? <X className="h-3.5 w-3.5" /> : <Plus className="h-3.5 w-3.5" />}
                </button>
              </div>

              {addingSite && (
                <div className="mb-3 space-y-2 rounded-xl border border-orange-200 bg-orange-50/40 p-3">
                  <label className="block">
                    <span className="mb-1 block font-mono text-xs text-slate-500">Site name</span>
                    <input
                      type="text"
                      value={newSiteName}
                      onChange={(e) => setNewSiteName(e.target.value)}
                      placeholder="e.g. Bhuj, Kutch"
                      autoFocus
                      className="w-full min-w-0 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 font-mono text-xs font-semibold text-slate-800 outline-none transition-colors focus:border-[#EA580C] focus:ring-2 focus:ring-orange-100"
                    />
                  </label>
                  <NumberField label="Latitude" value={newSiteLat} step={0.01} onChange={setNewSiteLat} />
                  <NumberField label="Longitude" value={newSiteLon} step={0.01} onChange={setNewSiteLon} />
                  <button
                    type="button"
                    onClick={confirmAddSite}
                    disabled={!newSiteName.trim()}
                    className="w-full rounded-lg bg-[#EA580C] px-3 py-1.5 font-mono text-[11px] font-bold uppercase tracking-wider text-white transition-opacity hover:opacity-90 disabled:opacity-40 cursor-pointer"
                  >
                    Add site
                  </button>
                </div>
              )}

              <NumberField label="Latitude" value={params.lat} step={0.01} onChange={(v) => setParam("lat", v)} />
              <NumberField label="Longitude" value={params.lon} step={0.01} onChange={(v) => setParam("lon", v)} />
              <NumberField label="Days to simulate" value={params.days} step={1} min={7} max={90} onChange={(v) => setParam("days", v)} />
            </fieldset>

            {/* Hardware */}
            <fieldset className="min-w-0">
              <legend className="mb-2 font-mono text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Hardware
              </legend>
              <p className="mb-2 text-[11px] text-slate-400">Set it yourself, or let the model decide.</p>
              <NumberField label="Solar kWp" value={params.solar} step={0.5} unit="kWp" onChange={(v) => setParam("solar", v)} />
              <NumberField label="Wind kW" value={params.wind} step={0.5} unit="kW" onChange={(v) => setParam("wind", v)} />
              <NumberField label="Hub height" value={params.hub_height} step={1} unit="m" onChange={(v) => setParam("hub_height", v)} />
              <NumberField
                label="Wind cost"
                value={params.wind_cost_per_kw}
                step={5000}
                min={0}
                unit="Rs/kW"
                onChange={(v) => setParam("wind_cost_per_kw", v)}
              />
              <NumberField label="Battery kWh" value={params.battery} step={1} unit="kWh" onChange={(v) => setParam("battery", v)} />
              <NumberField label="Reserve floor" value={params.battery_reserve} step={0.05} min={0} max={0.9} onChange={(v) => setParam("battery_reserve", v)} />
              <NumberField label="Genset kW" value={params.genset_kw} step={1} unit="kW" onChange={(v) => setParam("genset_kw", v)} />
            </fieldset>

            {/* Load */}
            <fieldset className="min-w-0">
              <legend className="mb-2 font-mono text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Load
              </legend>
              <NumberField label="Pump kW" value={params.pump_kw} step={0.1} unit="kW" onChange={(v) => setParam("pump_kw", v)} />
              <NumberField label="Household kW" value={params.household_kw} step={0.1} unit="kW" onChange={(v) => setParam("household_kw", v)} />
              <NumberField label="Dairy kW" value={params.dairy_kw} step={0.1} unit="kW" onChange={(v) => setParam("dairy_kw", v)} />
              <NumberField label="Cold storage kW" value={params.cold_storage_kw} step={0.1} unit="kW" onChange={(v) => setParam("cold_storage_kw", v)} />
            </fieldset>

            {/* Prices and feeders */}
            <fieldset className="min-w-0">
              <legend className="mb-2 font-mono text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Prices and feeders
              </legend>
              <NumberField label="Diesel ₹/L" value={params.diesel_price} step={1} onChange={(v) => setParam("diesel_price", v)} />
              <NumberField label="Ag tariff ₹/kWh" value={params.ag_tariff} step={0.25} onChange={(v) => setParam("ag_tariff", v)} />
              <NumberField label="Ag feeder kW" value={params.ag_kw} step={1} unit="kW" onChange={(v) => setParam("ag_kw", v)} />
              <NumberField label="Village ₹/kWh" value={params.village_tariff} step={0.25} onChange={(v) => setParam("village_tariff", v)} />
              <NumberField label="Village feeder kW" value={params.village_kw} step={1} unit="kW" onChange={(v) => setParam("village_kw", v)} />
              <NumberField label="Carbon ₹/kg" value={params.carbon_price} step={1} onChange={(v) => setParam("carbon_price", v)} />
              <NumberField label="Grid kg CO₂/kWh" value={params.grid_carbon} step={0.01} onChange={(v) => setParam("grid_carbon", v)} />
            </fieldset>
          </div>

          {/* Run */}
          <div className="flex flex-wrap items-end justify-between gap-4 border-t border-slate-100 pt-5">
            <div className="flex flex-wrap items-end gap-4">
              <div className="w-40 min-w-0">
                <SelectField
                  label="Advice language"
                  value={params.language}
                  onChange={(v) => setParam("language", v)}
                  options={[
                    { value: "english", label: "English" },
                    { value: "gujarati", label: "Gujarati" },
                    { value: "hindi", label: "Hindi" },
                  ]}
                />
              </div>
              <div className="w-32 min-w-0">
                <NumberField
                  label="Advice for day"
                  value={params.advice_day}
                  step={1}
                  min={0}
                  onChange={(v) => setParam("advice_day", v)}
                />
              </div>
            </div>

            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => sizing.getSizing()}
                disabled={busy}
                className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 font-mono text-xs font-bold uppercase tracking-wider text-slate-700 shadow-sm transition-all hover:border-[#EA580C] hover:bg-orange-50 hover:text-[#EA580C] disabled:opacity-60 cursor-pointer"
              >
                <Ruler className={`h-3.5 w-3.5 ${sizing.loading ? "animate-spin" : ""}`} />
                {sizing.loading ? "Sizing…" : "Decide the size for me"}
              </button>
              <button
                onClick={() => executeSimulation()}
                disabled={busy}
                className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-[#EA580C] to-[#F7931A] px-4 py-2.5 font-mono text-xs font-bold uppercase tracking-wider text-white shadow-sm transition-all hover:scale-[1.02] disabled:opacity-60 cursor-pointer"
              >
                {isLoading ? <RotateCw className="h-3.5 w-3.5 animate-spin" /> : <Cpu className="h-3.5 w-3.5" />}
                {isLoading ? "Optimising…" : "Run the optimiser"}
              </button>
            </div>
          </div>

          {sizing.error && (
            <div className="rounded-xl border border-red-200 bg-red-50 p-3 font-mono text-xs text-red-700">
              {sizing.error}
            </div>
          )}

          {sizing.sizing && (
            <SizingResults data={sizing.sizing} onApply={sizing.applyCandidate} />
          )}
        </div>
      )}
    </Card>
  );
}
