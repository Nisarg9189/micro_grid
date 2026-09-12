import type { EnergyDataPoint } from "../types/energy";

export const hourlyData: EnergyDataPoint[] = [
  { time: "00:00", load: 2.1, solar: 0, battery: 0, grid: 2.1, diesel: 0 },
  { time: "04:00", load: 2.0, solar: 0, battery: 0, grid: 2.0, diesel: 0 },
  { time: "08:00", load: 3.5, solar: 1.2, battery: -0.5, grid: 2.8, diesel: 0 },
  { time: "12:00", load: 5.8, solar: 3.0, battery: -1.0, grid: 3.8, diesel: 0 },
  { time: "16:00", load: 4.2, solar: 1.8, battery: 0.5, grid: 1.9, diesel: 0 },
  { time: "20:00", load: 6.5, solar: 0, battery: 2.5, grid: 3.0, diesel: 1.0 },
  { time: "23:00", load: 2.2, solar: 0, battery: 0.2, grid: 2.0, diesel: 0 },
];

export const sevenDayData: EnergyDataPoint[] = [
  { time: "Mon", load: 68.4, solar: 28.5, battery: 12.0, grid: 25.5, diesel: 2.4 },
  { time: "Tue", load: 72.1, solar: 31.0, battery: 14.5, grid: 24.8, diesel: 1.8 },
  { time: "Wed", load: 65.0, solar: 29.2, battery: 13.0, grid: 22.8, diesel: 0.0 },
  { time: "Thu", load: 74.8, solar: 32.4, battery: 15.2, grid: 27.2, diesel: 0.0 },
  { time: "Fri", load: 79.2, solar: 30.8, battery: 14.0, grid: 31.4, diesel: 3.0 },
  { time: "Sat", load: 62.5, solar: 33.1, battery: 16.0, grid: 13.4, diesel: 0.0 },
  { time: "Sun", load: 58.0, solar: 34.0, battery: 15.5, grid: 8.5, diesel: 0.0 },
];

export const thirtyDayData: EnergyDataPoint[] = [
  { time: "Week 1", load: 480, solar: 215, battery: 95, grid: 160, diesel: 10 },
  { time: "Week 2", load: 510, solar: 228, battery: 102, grid: 172, diesel: 8 },
  { time: "Week 3", load: 495, solar: 210, battery: 98, grid: 175, diesel: 12 },
  { time: "Week 4", load: 460, solar: 235, battery: 110, grid: 115, diesel: 0 },
];
