import type { VillageSizingRequest, VillageSizingResponse } from "../types/village";
import { handleApiError } from "./apiError";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Village-scale search costs more per candidate than the farm-scale one (100 households +
// 20 farms + dairy + water, two feeder groups), so this gets a longer timeout even though
// the endpoint itself is capped to finish in well under a minute for the horizon it uses.
export async function getVillageSizing(
  request: VillageSizingRequest
): Promise<VillageSizingResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 180000);

  try {
    const response = await fetch(`${API_URL}/api/village/size`, {
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
      throw new Error("REQUEST TIMEOUT: Village sizing search took too long to complete.");
    }
    throw err;
  }
}
