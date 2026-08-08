// frontend/src/components/ModeToggle.jsx
/**
 * Interaction Mode Toggle Switch Component for ClinicalPrep AI v2.0.
 * 
 * Purpose:
 *   Allows patients to switch seamlessly between Text Chat and Hands-Free Voice Mode.
 *   Enforces single-mode operational boundaries to prevent keyboard and speech clashes.
 */

import React from 'react';
import { MessageSquare, Mic } from 'lucide-react';

export const ModeToggle = ({ mode, onModeChange, disabled = false }) => {
  return (
    <div className="flex items-center justify-center p-1 bg-slate-200/80 rounded-xl max-w-xs mx-auto my-2 border border-slate-300">
      {/* Text Chat Mode Button */}
      <button
        type="button"
        disabled={disabled}
        onClick={() => onModeChange('chat')}
        className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-lg text-xs font-semibold transition-all duration-200 ${
          mode === 'chat'
            ? 'bg-white text-amber-900 shadow-sm'
            : 'text-slate-600 hover:text-slate-900'
        }`}
      >
        <MessageSquare className="w-3.5 h-3.5" />
        <span>Text Chat</span>
      </button>

      {/* Hands-Free Voice Mode Button */}
      <button
        type="button"
        disabled={disabled}
        onClick={() => onModeChange('voice')}
        className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-lg text-xs font-semibold transition-all duration-200 ${
          mode === 'voice'
            ? 'bg-amber-800 text-white shadow-sm animate-pulse'
            : 'text-slate-600 hover:text-slate-900'
        }`}
      >
        <Mic className="w-3.5 h-3.5" />
        <span>Voice Mode</span>
      </button>
    </div>
  );
};

export default ModeToggle;