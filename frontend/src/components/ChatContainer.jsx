// frontend/src/components/ChatContainer.jsx
/**
 * Chat Container UI Component for ClinicalPrep AI v2.0.
 * 
 * Purpose:
 *   Serves as the primary conversation interface. Manages chat message streams, 
 *   browser microphone audio recording via `useAudioRecorder`, automatic 
 *   Speech-to-Text (STT) transcription, and Text-to-Speech (TTS) audio playback 
 *   for assistant responses.
 */

import React, { useState, useRef, useEffect } from 'react';
import { Mic, Send, Volume2, Square, Loader2, AlertCircle } from 'lucide-react';
import { useAudioRecorder } from '../hooks/useAudioRecorder';
import { transcribeAudio, synthesizeSpeech } from '../services/api';

export const ChatContainer = ({ messages = [], onSendMessage, isLoading }) => {
  const [inputText, setInputText] = useState('');
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  const messagesEndRef = useRef(null);
  const audioPlayerRef = useRef(null);

  // Initialize custom Web Audio API recorder hook
  const {
    isRecording,
    recordingTime,
    audioBlob,
    error: micError,
    startRecording,
    stopRecording,
    clearAudio,
  } = useAudioRecorder();

  // Scroll to bottom of chat feed on new message or loading state update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading, isTranscribing]);

  // Effect: Process recorded audio blob when user stops microphone recording
  useEffect(() => {
    const processRecordedAudio = async () => {
      if (audioBlob) {
        setIsTranscribing(true);
        try {
          // Post captured WebM audio blob to backend STT endpoint
          const data = await transcribeAudio(audioBlob);
          if (data.transcript && data.transcript.trim()) {
            await onSendMessage(data.transcript.trim());
          }
        } catch (err) {
          console.error('STT Transcription Error:', err);
        } finally {
          setIsTranscribing(false);
          clearAudio();
        }
      }
    };

    processRecordedAudio();
  }, [audioBlob, onSendMessage, clearAudio]);

  // Effect: Automatically play assistant response audio upon receiving new message
  useEffect(() => {
    const lastMessage = messages[messages.length - 1];
    if (lastMessage && lastMessage.role === 'assistant' && !isLoading && !isTranscribing) {
      handlePlayTTS(lastMessage.content);
    }
  }, [messages, isLoading, isTranscribing]);

  /**
   * Synthesizes text prompt into audio via backend TTS service and starts playback.
   */
  const handlePlayTTS = async (textToSpeak) => {
    try {
      if (isPlayingAudio && audioPlayerRef.current) {
        audioPlayerRef.current.pause();
        setIsPlayingAudio(false);
        return;
      }

      setIsPlayingAudio(true);
      const audioUrl = await synthesizeSpeech(textToSpeak);

      if (audioPlayerRef.current) {
        audioPlayerRef.current.src = audioUrl;
        audioPlayerRef.current.play();
      }
    } catch (err) {
      console.error('TTS Audio Playback Error:', err);
      setIsPlayingAudio(false);
    }
  };

  /**
   * Submits typed text input to the intake processor.
   */
  const handleSubmitText = (e) => {
    e.preventDefault();
    if (inputText.trim() && !isLoading && !isTranscribing) {
      onSendMessage(inputText.trim());
      setInputText('');
    }
  };

  /**
   * Formats recording duration from seconds to MM:SS format.
   */
  const formatTimer = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  return (
    <div className="flex flex-col h-full max-w-4xl mx-auto bg-white rounded-xl shadow-md overflow-hidden border border-slate-200">
      {/* Hidden Audio Element for Web Speech Streaming Playback */}
      <audio
        ref={audioPlayerRef}
        onEnded={() => setIsPlayingAudio(false)}
        onError={() => setIsPlayingAudio(false)}
        className="hidden"
      />

      {/* Chat Conversation Feed */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, index) => {
          const isUser = msg.role === 'user';
          return (
            <div
              key={index}
              className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm shadow-sm relative group ${
                  isUser
                    ? 'bg-amber-800 text-white rounded-br-none'
                    : 'bg-slate-100 text-slate-800 rounded-bl-none border border-slate-200'
                }`}
              >
                <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>

                {/* Assistant Speech Manual Playback Trigger */}
                {!isUser && (
                  <button
                    onClick={() => handlePlayTTS(msg.content)}
                    className="mt-2 text-slate-500 hover:text-amber-800 transition-colors flex items-center gap-1 text-xs font-medium"
                    title="Read Aloud"
                  >
                    <Volume2 className="w-3.5 h-3.5" />
                    <span>Read Aloud</span>
                  </button>
                )}
              </div>
              <span className="text-[10px] text-slate-400 mt-1 px-1">
                {isUser ? 'You' : 'ClinicalPrep Assistant'}
              </span>
            </div>
          );
        })}

        {/* Slot Analysis State Indicator */}
        {isLoading && (
          <div className="flex items-center gap-2 text-slate-500 text-xs italic p-2">
            <Loader2 className="w-4 h-4 animate-spin text-amber-800" />
            Analyzing intake slots...
          </div>
        )}

        {/* Speech-to-Text Processing State Indicator */}
        {isTranscribing && (
          <div className="flex items-center gap-2 text-amber-800 text-xs font-medium p-2 bg-amber-50 rounded-lg border border-amber-200">
            <Loader2 className="w-4 h-4 animate-spin" />
            Transcribing voice input...
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Hardware / Permission Error Display */}
      {micError && (
        <div className="bg-red-50 text-red-600 text-xs p-2.5 px-4 border-t border-red-200 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{micError}</span>
        </div>
      )}

      {/* Input Action Controls Bar */}
      <div className="p-3 bg-slate-50 border-t border-slate-200">
        <form onSubmit={handleSubmitText} className="flex items-center gap-2">
          {isRecording ? (
            /* Active Microphone Recording Banner */
            <div className="flex-1 flex items-center justify-between bg-red-50 border border-red-200 rounded-xl px-4 py-2 text-red-700 animate-pulse">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-red-600 animate-ping" />
                <span className="text-xs font-semibold">Recording Voice Input...</span>
              </div>
              <span className="text-xs font-mono font-bold">{formatTimer(recordingTime)}</span>
              <button
                type="button"
                onClick={stopRecording}
                className="bg-red-600 hover:bg-red-700 text-white p-1.5 rounded-lg transition-colors"
                title="Stop Recording"
              >
                <Square className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <>
              {/* Microphone Record Button */}
              <button
                type="button"
                onClick={startRecording}
                disabled={isLoading || isTranscribing}
                className="p-2.5 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-xl transition-colors disabled:opacity-50"
                title="Start Voice Recording"
              >
                <Mic className="w-5 h-5 text-slate-700" />
              </button>

              {/* Text Message Input Field */}
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Type your response or use microphone..."
                disabled={isLoading || isTranscribing}
                className="flex-1 bg-white border border-slate-300 rounded-xl px-4 py-2.5 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-800 focus:border-transparent disabled:opacity-50"
              />

              {/* Submit Message Button */}
              <button
                type="submit"
                disabled={!inputText.trim() || isLoading || isTranscribing}
                className="bg-amber-800 hover:bg-amber-900 text-white p-2.5 rounded-xl transition-colors disabled:opacity-50 flex items-center justify-center"
              >
                <Send className="w-5 h-5" />
              </button>
            </>
          )}
        </form>
      </div>
    </div>
  );
};

// Provides default export fallback to resolve import mismatches in App.jsx
export default ChatContainer;