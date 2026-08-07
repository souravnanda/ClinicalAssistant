/**
 * FILE: frontend/src/services/api.js
 * PURPOSE: Asynchronous HTTP client service for backend communication.
 * WHY WE NEED IT: Centralizes network requests between the React frontend and 
 * the FastAPI backend. Encapsulates request headers, endpoint routing, 
 * payload formatting, and error handling for seamless maintainability.
 */

// Base backend URL loaded from environment variables (Vite scope) with local fallback
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

/**
 * Sends a patient message and current session state to the FastAPI intake endpoint.
 *
 * @param {string} userMessage - The raw text message entered by the patient.
 * @param {Object|null} sessionState - The current intake session state object (or null on turn 1).
 * @returns {Promise<Object>} Resolves to the backend API response payload.
 * @throws {Error} Throws a detailed error message if the HTTP request or validation fails.
 */
export async function sendIntakeStep(userMessage, sessionState = null) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v2/intake/step`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_message: userMessage,
        session_state: sessionState,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const detailMsg = Array.isArray(errorData.detail)
        ? errorData.detail[0]?.msg
        : errorData.detail;
      throw new Error(detailMsg || `Server error (Status ${response.status})`);
    }

    return await response.json();
  } catch (error) {
    console.error("API Service Error [sendIntakeStep]:", error);
    throw error;
  }
}

/**
 * Checks the operational health of the FastAPI backend server.
 *
 * @returns {Promise<Object>} Resolves to the health status payload.
 * @throws {Error} Throws an error if the server is unreachable or unhealthy.
 */
export async function checkBackendHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Health check failed with status ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("API Service Error [checkBackendHealth]:", error);
    throw error;
  }
}