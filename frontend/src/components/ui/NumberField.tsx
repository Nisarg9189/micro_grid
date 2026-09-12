export interface NumberFieldProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  step?: number;
  min?: number;
  max?: number;
  unit?: string;
}

// Label above, input below -- a side-by-side row with a fixed-width input has no room
// to shrink on a narrow viewport, which forces the row (and the page with it) wider
// than the screen rather than wrapping. Stacking avoids that at every width.
export function NumberField({ label, value, onChange, step = 1, min, max, unit }: NumberFieldProps) {
  return (
    <label className="block py-1.5 min-w-0">
      <span className="mb-1 block font-mono text-xs text-slate-500">{label}</span>
      <span className="flex items-center gap-1.5">
        <input
          type="number"
          value={Number.isFinite(value) ? value : ""}
          step={step}
          min={min}
          max={max}
          onChange={(e) => onChange(e.target.value === "" ? 0 : Number(e.target.value))}
          className="w-full min-w-0 rounded-lg border border-slate-200 bg-slate-50/70 px-2.5 py-1.5 font-mono text-xs font-semibold text-slate-800 outline-none transition-colors focus:border-[#EA580C] focus:bg-white focus:ring-2 focus:ring-orange-100"
        />
        {unit && <span className="shrink-0 font-mono text-[10px] text-slate-400">{unit}</span>}
      </span>
    </label>
  );
}
