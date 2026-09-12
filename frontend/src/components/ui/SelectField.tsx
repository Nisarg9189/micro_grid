export interface SelectFieldProps {
  label: string;
  value: string;
  options: { value: string; label: string }[];
  onChange: (value: string) => void;
}

// Stacked, same as NumberField -- a side-by-side row has no room to shrink at narrow
// widths and forces the page wider than the screen instead of wrapping.
export function SelectField({ label, value, options, onChange }: SelectFieldProps) {
  return (
    <label className="block py-1.5 min-w-0">
      <span className="mb-1 block font-mono text-xs text-slate-500">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full min-w-0 rounded-lg border border-slate-200 bg-slate-50/70 px-2.5 py-1.5 font-mono text-xs font-semibold text-slate-800 outline-none transition-colors focus:border-[#EA580C] focus:bg-white focus:ring-2 focus:ring-orange-100"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </label>
  );
}
