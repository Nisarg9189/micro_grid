import { CheckCircle2 } from "lucide-react";
import type { SizingResponse, SizingCandidate } from "../../types/sizing";

const fmt = (v: number, digits = 0) => v.toLocaleString(undefined, {
  minimumFractionDigits: digits, maximumFractionDigits: digits,
});

export interface SizingResultsProps {
  data: SizingResponse;
  onApply: (candidate: SizingCandidate) => void;
}

// Mirrors report/console.html's SizeResult -- same tiles, same table, same one-click
// "adopt this hardware and re-run" action.
export function SizingResults({ data, onApply }: SizingResultsProps) {
  if (!data.recommended) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
        {data.message || "No configuration held 99% reliability at this horizon."}
      </div>
    );
  }

  const r = data.recommended;

  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50/60 p-5">
      <div className="mb-3 flex items-center gap-2 font-mono text-[11px] font-bold uppercase tracking-wider text-slate-500">
        <CheckCircle2 className="h-4 w-4 text-emerald-600" />
        {data.meta.evaluated} configurations evaluated, ranked by annualised total cost at
        99% reliability
      </div>
      {data.meta.caveat && (
        <p className="mb-4 text-xs text-slate-500">{data.meta.caveat}</p>
      )}

      <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          ["Solar", `${fmt(r.solar_kwp, 1)}`, "kWp"],
          ["Wind", `${fmt(r.wind_kw, 1)}`, "kW"],
          ["Battery", `${fmt(r.battery_kwh, 1)}`, "kWh"],
          ["Total", `₹${fmt(r.total_inr)}`, "/ yr"],
        ].map(([label, value, unit]) => (
          <div key={label} className="rounded-xl border border-slate-200 bg-white p-3">
            <div className="font-mono text-[9px] uppercase tracking-wider text-slate-400">{label}</div>
            <div className="mt-1 font-mono text-lg font-bold text-slate-900">
              {value} <span className="text-xs font-normal text-slate-400">{unit}</span>
            </div>
          </div>
        ))}
      </div>

      <button
        onClick={() => onApply(r)}
        className="mb-4 inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-[#EA580C] to-[#F7931A] px-4 py-2.5 font-mono text-xs font-bold uppercase tracking-wider text-white shadow-sm transition-all hover:scale-[1.02] cursor-pointer"
      >
        Use this hardware and run the optimiser
      </button>

      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-slate-200 text-left font-mono text-[10px] uppercase tracking-wider text-slate-400">
              <th className="px-3 py-2">Solar</th>
              <th className="px-3 py-2 text-right">Wind</th>
              <th className="px-3 py-2 text-right">Battery</th>
              <th className="px-3 py-2 text-right">Diesel</th>
              <th className="px-3 py-2 text-right">Reliab.</th>
              <th className="px-3 py-2 text-right">Capital/yr</th>
              <th className="px-3 py-2 text-right">Energy/yr</th>
              <th className="px-3 py-2 text-right">Total/yr</th>
            </tr>
          </thead>
          <tbody className="font-mono">
            {data.candidates.map((c, i) => (
              <tr
                key={i}
                className={`border-b border-slate-100 last:border-0 ${i === 0 ? "bg-orange-50/60 font-bold" : ""}`}
              >
                <td className="px-3 py-2">{fmt(c.solar_kwp, 1)} kWp</td>
                <td className="px-3 py-2 text-right">{fmt(c.wind_kw, 1)}</td>
                <td className="px-3 py-2 text-right">{fmt(c.battery_kwh, 1)}</td>
                <td className="px-3 py-2 text-right">{fmt(c.diesel_litres, 1)} L</td>
                <td className="px-3 py-2 text-right">{fmt(c.reliability_pct, 1)}%</td>
                <td className="px-3 py-2 text-right">₹{fmt(c.capital_inr)}</td>
                <td className="px-3 py-2 text-right">₹{fmt(c.energy_inr)}</td>
                <td className="px-3 py-2 text-right">₹{fmt(c.total_inr)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
