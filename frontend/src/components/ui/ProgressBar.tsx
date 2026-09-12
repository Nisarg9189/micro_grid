export interface ProgressBarProps {
  value: number; // 0 - 100
  max?: number;
  tone?: "green" | "orange" | "blue" | "auto";
  height?: "sm" | "md" | "lg";
  className?: string;
}

export function ProgressBar({
  value,
  max = 100,
  tone = "auto",
  height = "md",
  className = "",
}: ProgressBarProps) {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));

  let barColor = "bg-[#22C55E]";
  if (tone === "auto") {
    if (percentage < 20) barColor = "bg-red-500";
    else if (percentage < 50) barColor = "bg-amber-500";
    else barColor = "bg-[#22C55E]";
  } else if (tone === "orange") {
    barColor = "bg-[#EA580C]";
  } else if (tone === "blue") {
    barColor = "bg-[#2563EB]";
  } else if (tone === "green") {
    barColor = "bg-[#22C55E]";
  }

  const heightClasses = {
    sm: "h-1.5",
    md: "h-2.5",
    lg: "h-3.5",
  };

  return (
    <div className={`w-full overflow-hidden rounded-full bg-slate-100 ${heightClasses[height]} ${className}`}>
      <div
        className={`h-full rounded-full transition-all duration-500 ${barColor}`}
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
}
