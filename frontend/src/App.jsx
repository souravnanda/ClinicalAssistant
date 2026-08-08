// frontend/src/App.jsx
/**
 * Root Application Component for ClinicalPrep AI v2.0.
 * 
 * Purpose:
 *   Manages top-level application state, mode switching (Chat vs Voice), 
 *   conversation turn memory, intake step progress tracking, and FastAPI endpoints.
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import Header from './components/Header';
import ChatContainer from './components/ChatContainer';
import SummaryCard from './components/SummaryCard';
import EmergencyModal from './components/EmergencyModal';
import { sendIntakeStep, checkBackendHealth, synthesizeSpeech, downloadIntakePdf } from './services/api';

const GREETING = "Hello! I'm ClinicalPrep AI, your patient-intake assistant. Before we begin, please note that I don't provide medical advice—I'm here to help organize your symptoms before your visit. May I please have your name to get started?";

export const App = () => {
  // Session State, Interaction Mode, and Quick Options Memory
  const [sessionState, setSessionState] = useState(null);
  const [quickOptions, setQuickOptions] = useState([]);
  const [interactionMode, setInteractionMode] = useState('chat'); // 'chat' or 'voice'
  const [messages, setMessages] = useState([{ role: 'assistant', content: GREETING }]);
  const [isLoading, setIsLoading] = useState(false);
  const [isEmergency, setIsEmergency] = useState(false);
  const [backendStatus, setBackendStatus] = useState('checking');

  // Restart confirmation + PDF download state, surfaced once intake is complete.
  const [showRestartConfirm, setShowRestartConfirm] = useState(false);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);

  // --- Voice playback, lifted here so text (chat bubble) and audio (TTS) start
  // together instead of the text rendering first and audio trailing behind it. ---
  const audioPlayerRef = useRef(null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const lastSpokenMessageRef = useRef(null);

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
   * Plays a pre-fetched audio URL and tracks speaking state so the mic can be
   * disabled while the assistant is talking (prevents overlap/self-interruption).
   */
  const playAudioUrl = useCallback((audioUrl) => {
    if (!audioPlayerRef.current || !audioUrl) return;
    setIsSpeaking(true);
    audioPlayerRef.current.src = audioUrl;
    audioPlayerRef.current.play().catch((err) => {
      console.warn('Browser autoplay policy restricted audio play:', err);
      setIsSpeaking(false);
    });
  }, []);

  /**
   * Manual "Read Aloud" replay for an already-visible message bubble — text is
   * already on screen, so this just plays audio without touching `messages`.
   */
  const handleReadAloud = useCallback(async (text) => {
    if (!text) return;
    if (isSpeaking && audioPlayerRef.current) {
      audioPlayerRef.current.pause();
      setIsSpeaking(false);
      return;
    }
    try {
      const audioUrl = await synthesizeSpeech(text);
      playAudioUrl(audioUrl);
    } catch (err) {
      console.error('TTS Audio Playback Error:', err);
      setIsSpeaking(false);
    }
  }, [isSpeaking, playAudioUrl]);

  /**
   * Submits patient messages (typed or transcribed) to the FastAPI Pydantic intake engine.
   */
  const handleSendMessage = async (userText) => {
    if (!userText || isLoading) return;

    // 1. Append User Message to UI Chat Stream & Clear Chips
    setMessages((prev) => [...prev, { role: 'user', content: userText }]);
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

      // 5. Append Assistant Response Question to Chat Feed.
      // In Voice Mode, pre-fetch the TTS audio FIRST, then reveal the text bubble
      // at the exact same moment playback starts — this is what keeps the
      // on-screen text and the spoken audio in sync instead of text jumping in
      // a beat before the voice catches up.
      if (response.next_question) {
        const assistantMsg = { role: 'assistant', content: response.next_question };

        if (interactionMode === 'voice') {
          try {
            const audioUrl = await synthesizeSpeech(response.next_question);
            lastSpokenMessageRef.current = response.next_question;
            setMessages((prev) => [...prev, assistantMsg]);
            playAudioUrl(audioUrl);
          } catch (err) {
            // TTS failed — still show the text so the conversation isn't blocked.
            console.error('TTS Audio Playback Error:', err);
            setMessages((prev) => [...prev, assistantMsg]);
          }
        } else {
          setMessages((prev) => [...prev, assistantMsg]);
        }
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

  /**
   * Resets the entire session back to a fresh intake, after explicit confirmation.
   */
  const handleRestartIntake = () => {
    setSessionState(null);
    setQuickOptions([]);
    setMessages([{ role: 'assistant', content: GREETING }]);
    setIsEmergency(false);
    setShowRestartConfirm(false);
    lastSpokenMessageRef.current = null;
    if (audioPlayerRef.current) {
      audioPlayerRef.current.pause();
    }
    setIsSpeaking(false);
  };

  const handleDownloadPdf = async () => {
    try {
      setIsDownloadingPdf(true);
      await downloadIntakePdf(sessionState);
    } catch (err) {
      console.error('PDF Download Error:', err);
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  // Derive Current Progression Step & Completion Status
  const currentStep = sessionState?.current_step || 1;
  const isCompleted = sessionState?.is_completed || false;
  const summaryBrief = sessionState?.summary_brief || '';

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col font-sans">
      {/* Hidden Audio Element for Voice Mode — lifted here so playback and text
          reveal happen from the same place and stay in sync. */}
      <audio
        ref={audioPlayerRef}
        onEnded={() => setIsSpeaking(false)}
        onError={() => setIsSpeaking(false)}
        className="hidden"
      />

      {/* Top Navigation & Fixed Progress Tracker Header */}
      <Header currentStep={currentStep} isCompleted={isCompleted} isEmergency={isEmergency} />

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
            isSpeaking={isSpeaking}
            onReadAloud={handleReadAloud}
            isCompleted={isCompleted}
            showRestartConfirm={showRestartConfirm}
            onRequestRestart={() => setShowRestartConfirm(true)}
            onCancelRestart={() => setShowRestartConfirm(false)}
            onConfirmRestart={handleRestartIntake}
            onDownloadPdf={handleDownloadPdf}
            isDownloadingPdf={isDownloadingPdf}
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
      <EmergencyModal isOpen={isEmergency} onClose={() => setIsEmergency(false)} />
    </div>
  );
};

export default App;
