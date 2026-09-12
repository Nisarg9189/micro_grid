import type { SimulationRequest } from "../types/api";
import type { SizingResponse } from "../types/sizing";
import { handleApiError } from "./apiError";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function getSizing(request: SimulationRequest): Promise<SizingResponse> {
  const controller = new AbortController();
  // The sweep evaluates every candidate on the lattice, so it runs far longer than a
  // single simulation -- matched to the same order of magnitude the backend itself
  // documents (up to a few minutes for a short-horizon sweep).
  const timeoutId = setTimeout(() => controller.abort(), 180000);

  try {
    const response = await fetch(`${API_URL}/api/size`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
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
    if (err.name === "AbortError") {
      throw new Error("REQUEST TIMEOUT: Sizing sweep took too long to complete.");
    }
    throw err;
  }
}
