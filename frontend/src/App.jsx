/**
 * FILE: frontend/src/App.jsx
 * PURPOSE: Root application component and primary state orchestrator for ClinicalPrep AI.
 * WHY WE NEED IT: Manages global session state (conversation history, intake slot memory, active step, emergency flags), coordinates API requests with FastAPI via api.js, and renders the layout.
 */

import React, { useState } from 'react';
import Header from './components/header';
import ChatContainer from './components/chatcontainer';
import QuickReplyChips from './components/quickreplychips';
import SummaryCard from './components/summarycard';
import EmergencyModal from './components/emergencymodal';
import { sendIntakeStep } from './services/api';
import { Send } from 'lucide-react';

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Hello! I'm ClinicalPrep AI, your patient-intake assistant. Before we begin, please note that I don't provide medical advice—I'm here to help organize your symptoms before your visit. May I please have your name to get started?",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [sessionState, setSessionState] = useState(null);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isEmergency, setIsEmergency] = useState(false);
  const [showEmergencyModal, setShowEmergencyModal] = useState(false);
  const [summaryText, setSummaryText] = useState('');
  const [quickOptions, setQuickOptions] = useState([]);
  const [currentStep, setCurrentStep] = useState(1);

  const handleSendMessage = async (textToSend) => {
    const messageText = textToSend || inputText;
    if (!messageText.trim() || isLoading) return;

    // 1. Append user message to conversation list
    const userMsg = {
      role: 'user',
      content: messageText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setIsLoading(true);

    try {
      // 2. Dispatch network request to FastAPI backend
      const response = await sendIntakeStep(messageText, sessionState);

      if (response) {
        if (response.session_state) {
          setSessionState(response.session_state);
        }

        if (response.active_step) {
          setCurrentStep(response.active_step);
        }

        if (response.is_emergency) {
          setIsEmergency(true);
          setShowEmergencyModal(true);
        }

        if (response.summary) {
          setSummaryText(response.summary);
        }

        if (response.quick_options) {
          setQuickOptions(response.quick_options);
        } else {
          setQuickOptions([]);
        }

        // 3. Append assistant response
        if (response.next_question) {
          const assistantMsg = {
            role: 'assistant',
            content: response.next_question,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          };
          setMessages((prev) => [...prev, assistantMsg]);
        }
      }
    } catch (error) {
      console.error("Failed to send intake message:", error);
      const errorMsg = {
        role: 'assistant',
        content: "I apologize, but I encountered a network error connecting to the server. Please ensure the backend server is running and try again.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-[#FFF8F0] text-[#38240D]">
      {/* Top Header & Intake Tracker */}
      <Header currentStep={currentStep} isEmergency={isEmergency} />

      {/* Triage Emergency Modal */}
      <EmergencyModal
        isOpen={showEmergencyModal}
        onClose={() => setShowEmergencyModal(false)}
      />

      {/* Scrollable Conversation & Summary Brief */}
      <main className="flex-1 overflow-y-auto flex flex-col justify-between">
        <ChatContainer messages={messages} isLoading={isLoading} />

        {summaryText && (
          <div className="px-4 pb-4">
            <SummaryCard summaryText={summaryText} />
          </div>
        )}
      </main>

      {/* Contextual Quick-Reply Chips */}
      <QuickReplyChips
        options={quickOptions}
        onSelect={(option) => handleSendMessage(option)}
        disabled={isLoading}
      />

      {/* Sticky Bottom Input Bar */}
      <footer className="sticky bottom-0 bg-[#FFF8F0]/95 backdrop-blur-md border-t border-brand-200 p-4">
        <div className="max-w-3xl mx-auto flex items-center gap-2">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your response here..."
            disabled={isLoading}
            className="flex-1 px-4 py-3 bg-white border border-brand-200 rounded-xl text-sm focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 disabled:opacity-50 transition-all shadow-xs text-brand-900 placeholder:text-brand-700/50"
          />
          <button
            onClick={() => handleSendMessage()}
            disabled={isLoading || !inputText.trim()}
            className="p-3 bg-brand-500 text-white rounded-xl hover:bg-brand-700 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-xs"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </footer>
    </div>
  );
}