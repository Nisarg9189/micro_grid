export interface AppError {
  message: string;
  status?: number;
}

export async function handleApiError(response: Response): Promise<AppError> {
  let message = `API request failed with status ${response.status}`;
  try {
    const data = await response.json();
    if (data.detail) {
      if (typeof data.detail === 'string') {
        message = data.detail;
      } else if (Array.isArray(data.detail) && data.detail.length > 0 && data.detail[0].msg) {
        // Pydantic validation error
        message = `Validation Error: ${data.detail[0].msg}`;
      }
    }
  } catch (e) {
    // If not JSON, stick with default message
  }
  return {
    message,
    status: response.status,
  };
}
