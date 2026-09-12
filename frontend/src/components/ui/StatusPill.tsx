import React from "react";

export interface StatusPillProps {
  children: React.ReactNode;
  tone?: "green" | "blue" | "orange" | "amber" | "slate" | "danger";
  size?: "sm" | "md";
  dot?: boolean;
}

export function StatusPill({
  children,
  tone = "green",
  size = "sm",
  dot = false,
}: StatusPillProps) {
  const toneClasses = {
    green: "bg-green-50 text-green-700 border-green-200",
    blue: "bg-blue-50 text-blue-700 border-blue-200",
    orange: "bg-orange-50 text-[#EA580C] border-orange-200",
    amber: "bg-amber-50 text-amber-700 border-amber-200",
    slate: "bg-slate-100 text-slate-600 border-slate-200",
    danger: "bg-red-50 text-red-700 border-red-200",
  };

  const dotClasses = {
    green: "bg-green-500",
    blue: "bg-blue-500",
    orange: "bg-[#EA580C]",
    amber: "bg-amber-500",
    slate: "bg-slate-400",
    danger: "bg-red-500",
  };

  const sizeClasses = {
    sm: "px-2.5 py-0.5 text-[10px]",
    md: "px-3 py-1 text-xs",
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-mono font-bold uppercase tracking-wider ${toneClasses[tone]} ${sizeClasses[size]}`}
    >
      {dot && <span className={`h-1.5 w-1.5 rounded-full ${dotClasses[tone]}`} />}
      {children}
    </span>
  );
}
