export function LoadingSkeleton({
  height = "h-24",
  className = "",
}: {
  height?: string;
  className?: string;
}) {
  return (
    <div
      className={`animate-pulse rounded-2xl bg-slate-100 border border-slate-200 ${height} ${className}`}
    />
  );
}
