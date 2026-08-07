// frontend/src/services/api.js
/**
 * API Client Service Layer.
 * 
 * Purpose: Centralizes all asynchronous HTTP requests from the React frontend 
 * to the FastAPI backend. It handles environment variable resolution, payload 
 * formatting, and standardizes error throwing for UI components to catch.
 */

// Dynamically resolve the backend URL from Vite environment variables, falling back to local dev port
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Checks the operational health and active feature flags of the FastAPI backend.
 * 
 * @returns {Promise<Object>} JSON response containing system health status and version.
 */
export const checkBackendHealth = async () => {
  const response = await fetch(`${API_BASE_URL}/api/health`);
  
  if (!response.ok) {
    throw new Error('Backend health check failed. Ensure FastAPI is running.');
  }
  
  return await response.json();
};

/**
 * Submits the user's chat message and current session state to the Pydantic slot-filling engine.
 * 
 * @param {string} userMessage - The raw text input from the patient.
 * @param {Object|null} sessionState - The current extracted clinical slots (sends empty object if null to satisfy Pydantic validation).
 * @returns {Promise<Object>} JSON response containing updated state, next question, and emergency flags.
 */
export const sendIntakeStep = async (userMessage, sessionState = null) => {
  const payload = {
    user_message: userMessage,
    session_state: sessionState || {} // Prevent 422 Unprocessable Entity errors on first turn
  };

  const response = await fetch(`${API_BASE_URL}/api/v2/intake/step`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to process intake step.');
  }

  return await response.json();
};

/**
 * Uploads a captured web audio blob to the backend for Speech-to-Text transcription.
 * Uses Microsoft VibeVoice ASR for single-pass processing.
 * 
 * @param {Blob} audioBlob - The recorded WebM/WAV audio data from the browser MediaRecorder.
 * @returns {Promise<Object>} JSON response containing the transcript text and diarization segments.
 */
export const transcribeAudio = async (audioBlob) => {
  const formData = new FormData();
  formData.append('file', audioBlob, 'patient_recording.webm');

  const response = await fetch(`${API_BASE_URL}/api/v2/audio/transcribe`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to transcribe audio stream.');
  }

  return await response.json(); 
};

/**
 * Sends a text prompt to the backend Text-to-Speech endpoint and retrieves an audio stream.
 * 
 * @param {string} textPrompt - The assistant's text response to be spoken.
 * @returns {Promise<string>} A temporary local Blob URL that can be played in an HTML5 <audio> element.
 */
export const synthesizeSpeech = async (textPrompt) => {
  const response = await fetch(`${API_BASE_URL}/api/v2/audio/speak`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: textPrompt }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to synthesize speech audio.');
  }

  // Convert the binary audio/mpeg response into a playable object URL
  const audioBlob = await response.blob();
  return URL.createObjectURL(audioBlob);
};