import type { SimulationRequest } from "../types/api";
import type { IrrigationAdvice } from "../types/advice";
import { handleApiError } from "./apiError";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function getIrrigationAdvice(request: SimulationRequest): Promise<IrrigationAdvice> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 60000); 

  try {
    const response = await fetch(`${API_URL}/api/advice`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const error = await handleApiError(response);
      throw new Error(error.message);
    }

    return await response.json();
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw new Error("REQUEST TIMEOUT: Advice calculation took too long.");
    }
    throw err;
  }
}
