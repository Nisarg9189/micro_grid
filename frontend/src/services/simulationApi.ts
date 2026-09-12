import type { SimulationRequest, SimulationResponse } from "../types/api";
import { handleApiError } from "./apiError";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function runSimulation(request: SimulationRequest): Promise<SimulationResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 min timeout for simulation

  try {
    const response = await fetch(`${API_URL}/api/simulate`, {
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
      throw new Error("REQUEST TIMEOUT: Simulation took too long to complete.");
    }
    throw err;
  }
}
