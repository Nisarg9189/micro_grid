export interface AdviceOption {
  start_hour: number;
  cost_inr: number;
  diesel_litres: number;
}

export interface IrrigationAdvice {
  day: number;
  best_start: number;
  hours_needed: number;
  cost_saved_inr: number;
  diesel_saved_litres: number;
  options: AdviceOption[];
  // The backend returns this as a list of lines (one fact per line, e.g. the timing
  // recommendation, the savings, a feeder-schedule note), not a single paragraph.
  briefing: string[];
  message?: string;
  language?: string;
  numbers_verified?: boolean;
  unverified_numbers?: string[];
}
