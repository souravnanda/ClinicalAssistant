// frontend/src/App.jsx
/**
 * Root Application Component for ClinicalPrep AI v2.0.
 * 
 * Purpose:
 *   Manages top-level application state, mode switching (Chat vs Voice), 
 *   conversation turn memory, intake step progress tracking, and FastAPI endpoints.
 */

import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import ChatContainer from './components/ChatContainer';
import SummaryCard from './components/SummaryCard';
import EmergencyModal from './components/EmergencyModal';
import { sendIntakeStep, checkBackendHealth } from './services/api';

export const App = () => {
  // Session State, Interaction Mode, and Quick Options Memory
  const [sessionState, setSessionState] = useState(null);
  const [quickOptions, setQuickOptions] = useState([]);
  const [interactionMode, setInteractionMode] = useState('chat'); // 'chat' or 'voice'
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content:
        "Hello! I'm ClinicalPrep AI, your patient-intake assistant. Before we begin, please note that I don't provide medical advice—I'm here to help organize your symptoms before your visit. May I please have your name to get started?"
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [isEmergency, setIsEmergency] = useState(false);
  const [backendStatus, setBackendStatus] = useState('checking');

  // Verify FastAPI backend connectivity on application load
  useEffect(() => {
    const verifyHealth = async () => {
      try {
        await checkBackendHealth();
        setBackendStatus('connected');
      } catch (err) {
        console.error('Backend health verification failed:', err);
        setBackendStatus('disconnected');
      }
    };
    verifyHealth();
  }, []);

  /**
   * Submits patient messages (typed or transcribed) to the FastAPI Pydantic intake engine.
   */
  const handleSendMessage = async (userText) => {
    if (!userText || isLoading) return;

    // 1. Append User Message to UI Chat Stream & Clear Chips
    const updatedMessages = [...messages, { role: 'user', content: userText }];
    setMessages(updatedMessages);
    setQuickOptions([]);
    setIsLoading(true);

    try {
      // 2. Transmit Message Payload and Current Session Memory to FastAPI Endpoint
      const response = await sendIntakeStep(userText, sessionState);

      // 3. Update Client Session Memory & Quick Options with Returned State
      setSessionState(response.updated_state);
      setQuickOptions(response.quick_options || []);

      // 4. Trigger Emergency Modal Overlay if Red Flags Were Detected
      if (response.is_emergency) {
        setIsEmergency(true);
      }

      // 5. Append Assistant Response Question to Chat Feed
      if (response.next_question) {
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: response.next_question }
        ]);
      }
    } catch (err) {
      console.error('Intake Processing Error:', err);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            'I encountered an error processing your input. Please verify that the backend server is running and try again.'
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Derive Current Progression Step & Completion Status
  const currentStep = sessionState?.current_step || 1;
  const isCompleted = sessionState?.is_completed || false;
  const summaryBrief = sessionState?.summary_brief || '';

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col font-sans">
      {/* Top Navigation & Fixed Progress Tracker Header */}
      <Header currentStep={currentStep} isCompleted={isCompleted} />

      {/* Main Container Workspace */}
      <main className="flex-1 max-w-5xl w-full mx-auto p-4 flex flex-col gap-4 pb-12">
        {/* Backend Connection Warning Banner */}
        {backendStatus === 'disconnected' && (
          <div className="bg-amber-50 border border-amber-300 text-amber-800 px-4 py-2 rounded-lg text-xs flex items-center justify-between">
            <span>
              ⚠️ <strong>Backend Disconnected:</strong> Cannot reach FastAPI on http://localhost:8000. Please launch your backend server.
            </span>
          </div>
        )}

        {/* Primary Intake Chat Stream */}
        <div className="flex-1 min-h-[450px]">
          <ChatContainer
            messages={messages}
            quickOptions={quickOptions}
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
            mode={interactionMode}
            onModeChange={setInteractionMode}
          />
        </div>

        {/* Post-Intake Summary Doctor Brief Card */}
        {isCompleted && (
          <div className="mt-4 transition-all duration-300">
            <SummaryCard
              summaryBrief={
                summaryBrief ||
                "### Patient Pre-Visit Summary\nYour clinical intake details have been recorded."
              }
              sessionState={sessionState}
            />
          </div>
        )}
      </main>

      {/* Triage Emergency Red-Flag Warning Overlay */}
      {isEmergency && (
        <EmergencyModal onClose={() => setIsEmergency(false)} />
      )}
    </div>
  );
};

export default App;