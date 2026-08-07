/**
 * FILE: frontend/src/components/ChatBubble.jsx
 * PURPOSE: Individual message bubble renderer for user and assistant turns.
 * WHY WE NEED IT: Differentiates patient inputs from AI questions using distinct background colors, alignment, animations, and avatars for readable conversation flow.
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Bot, User } from 'lucide-react';

export default function ChatBubble({ message }) {
  const isUser = message.role === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.25 }}
      className={`flex items-start gap-2.5 my-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
    >
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-white shadow-xs ${
          isUser ? 'bg-brand-700' : 'bg-brand-500'
        }`}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      <div
        className={`max-w-[82%] sm:max-w-[75%] px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-xs ${
          isUser
            ? 'bg-brand-700 text-white rounded-tr-xs'
            : 'bg-white text-brand-900 border border-brand-200 rounded-tl-xs'
        }`}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>
        <span
          className={`block text-[10px] mt-1 text-right ${
            isUser ? 'text-brand-100' : 'text-brand-500'
          }`}
        >
          {message.timestamp || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </motion.div>
  );
}