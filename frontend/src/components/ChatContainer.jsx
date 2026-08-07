/**
 * FILE: frontend/src/components/ChatContainer.jsx
 * PURPOSE: Main chat conversation window wrapper.
 * WHY WE NEED IT: Houses the scrolling list of ChatBubbles, auto-scrolls to new messages upon receipt, and displays typing indicators when waiting for FastAPI responses.
 */

import React, { useEffect, useRef } from 'react';
import ChatBubble from './ChatBubble';

export default function ChatContainer({ messages, isLoading }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4 max-w-3xl w-full mx-auto">
      {messages.map((msg, index) => (
        <ChatBubble key={index} message={msg} />
      ))}

      {isLoading && (
        <div className="flex items-center gap-2 my-3 text-brand-700 text-xs font-medium italic">
          <div className="w-2 h-2 bg-brand-500 rounded-full animate-ping" />
          <span>ClinicalPrep AI is processing...</span>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}