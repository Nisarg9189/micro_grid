import { Info } from "lucide-react";
import type { ReactNode } from "react";

export interface FeatureBarProps {
  children: ReactNode;
  tone?: "orange" | "blue" | "emerald" | "slate";
}

const TONE_CLASSES: Record<NonNullable<FeatureBarProps["tone"]>, string> = {
  orange: "border-orange-200 bg-orange-50/80 text-orange-800",
  blue: "border-blue-200 bg-blue-50/80 text-blue-800",
  emerald: "border-emerald-200 bg-emerald-50/80 text-emerald-800",
  slate: "border-slate-200 bg-slate-50 text-slate-600",
};

// A single, consistent "what this does" line for every dashboard section -- meant to
// be readable at a glance while presenting or scrubbing through a recording, without
// needing the surrounding paragraph read aloud.
export function FeatureBar({ children, tone = "orange" }: FeatureBarProps) {
  return (
    <div
      className={`mb-4 flex items-start gap-2 rounded-lg border px-3 py-2 text-xs font-medium leading-snug ${TONE_CLASSES[tone]}`}
    >
      <Info className="mt-0.5 h-3.5 w-3.5 flex-none" />
      <span>{children}</span>
    </div>
  );
}
