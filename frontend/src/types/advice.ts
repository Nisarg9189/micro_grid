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
  briefing: string;
  message?: string;
  language?: string;
  numbers_verified?: boolean;
  unverified_numbers?: string[];
}
