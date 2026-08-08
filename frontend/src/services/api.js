// frontend/src/services/api.js
/**
 * API Client Service Layer for ClinicalPrep AI v2.0.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const checkBackendHealth = async () => {
  const response = await fetch(`${API_BASE_URL}/api/health`);
  if (!response.ok) throw new Error('Backend health check failed.');
  return await response.json();
};

export const sendIntakeStep = async (userMessage, sessionState = null) => {
  const payload = {
    user_message: userMessage,
    session_state: sessionState || {}
  };

  const response = await fetch(`${API_BASE_URL}/api/v2/intake/step`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to process clinical intake step.');
  }

  return await response.json();
};

export const downloadIntakePdf = async (sessionState) => {
  const payload = {
    user_message: "download_pdf",
    session_state: sessionState || {}
  };

  const response = await fetch(`${API_BASE_URL}/api/v2/intake/pdf`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error('Failed to generate PDF document.');
  }

  const blob = await response.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = downloadUrl;
  link.download = 'ClinicalPrep_Patient_Summary.pdf';
  document.body.appendChild(link);
  link.click();
  link.remove();
};

export const transcribeAudio = async (audioBlob) => {
  const formData = new FormData();
  formData.append('file', audioBlob, 'patient_recording.webm');

  const response = await fetch(`${API_BASE_URL}/api/v2/audio/transcribe`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) throw new Error('Failed to transcribe audio.');
  return await response.json(); 
};

export const synthesizeSpeech = async (textPrompt) => {
  const response = await fetch(`${API_BASE_URL}/api/v2/audio/speak`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: textPrompt }),
  });

  if (!response.ok) throw new Error('Failed to synthesize speech audio.');
  const audioBlob = await response.blob();
  return URL.createObjectURL(audioBlob);
};