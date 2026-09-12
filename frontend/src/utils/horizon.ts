// The API returns a full multi-day hourly series, not a live feed, so any single-point
// readout on this page has to pick WHICH hour it is showing. The last hour of the horizon
// is often the middle of the night (solar reads 0, nothing looks like it's happening),
// so the peak-demand hour is used instead -- the moment the optimiser actually has the
// most to balance, which is also the more informative snapshot to show.

/** Index of the highest-demand hour in an hourly load series, or -1 if empty. */
export function peakLoadIndex(loadKw: number[]): number {
  if (!loadKw.length) return -1;
  let peak = 0;
  for (let i = 1; i < loadKw.length; i++) {
    if (loadKw[i] > loadKw[peak]) peak = i;
  }
  return peak;
}

/** "Day 12, 20:00" from a flat hourly index -- readable, and honest about which hour
 * of a multi-day horizon this is, rather than implying the reading is from right now. */
export function hourLabel(index: number): string {
  if (index < 0) return "";
  const day = Math.floor(index / 24) + 1;
  const hour = index % 24;
  return `Day ${day}, ${hour.toString().padStart(2, "0")}:00`;
}
