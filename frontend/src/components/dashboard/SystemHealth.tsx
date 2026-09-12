import { ShieldCheck } from "lucide-react";
import { Card } from "../ui/Card";
import type { SystemHealthItem } from "../../types/dashboard";

export function SystemHealth({ items }: { items: SystemHealthItem[] }) {
  return (
    <Card className="p-5 sm:p-6">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-5 w-5 text-green-600" />
          <h4 className="font-heading text-base font-bold text-slate-950">
            Microgrid Diagnostic Health
          </h4>
        </div>
        <span className="font-mono text-[10px] text-slate-400 uppercase tracking-wider">
          ALL CONTROLLERS RESPONSIVE
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {items.map((item) => (
          <div
            key={item.id}
            className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50/70 p-3 font-mono text-xs"
          >
            <div>
              <div className="font-bold text-slate-800">{item.name}</div>
              {item.detail && <div className="text-[10px] text-slate-400">{item.detail}</div>}
            </div>

            <span className="flex items-center gap-1.5 font-bold text-[10px] uppercase">
              <span
                className={`h-2 w-2 rounded-full ${
                  item.status === "online"
                    ? "bg-green-500 shadow-[0_0_6px_rgba(34,197,94,0.6)]"
                    : item.status === "standby"
                    ? "bg-amber-500"
                    : "bg-red-500"
                }`}
              />
              <span
                className={
                  item.status === "online"
                    ? "text-green-700"
                    : item.status === "standby"
                    ? "text-amber-700"
                    : "text-red-700"
                }
              >
                {item.status}
              </span>
            </span>
          </div>
        ))}
      </div>
    </Card>
  );
}
