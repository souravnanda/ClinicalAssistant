/**
 * FILE: frontend/src/services/api.js
 * PURPOSE: HTTP API client for backend communication.
 * WHY WE NEED IT: Encapsulates all asynchronous network requests to FastAPI (/api/v2/intake/step), isolating network error handling, request formatting, and JSON parsing from UI components.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

/**
 * Sends a patient message and current session state to the FastAPI backend.
 * 
 * @param {string} userMessage - The text input provided by the patient.
 * @param {Object|null} sessionState - The current PatientSlotState JSON object.
 * @returns {Promise<Object>} Updated session_state, next_question, active_step, and emergency flags.
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
      if (response.status === 429) {
        throw new Error("Rate limit exceeded. Please wait a moment before sending another message.");
      }
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Server returned status code ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("API Error [sendIntakeStep]:", error);
    throw error;
  }
}

/**
 * Checks FastAPI backend health status.
 * 
 * @returns {Promise<boolean>} True if server is healthy, false otherwise.
 */
export async function checkBackendHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`);
    const data = await response.json();
    return data.status === 'healthy';
  } catch (error) {
    console.error("Health Check Failed:", error);
    return false;
  }
}