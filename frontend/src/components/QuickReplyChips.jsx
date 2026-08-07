/**
 * FILE: frontend/src/components/QuickReplyChips.jsx
 * PURPOSE: Contextual suggestion buttons rendered above the message input bar.
 * WHY WE NEED IT: Reduces patient typing effort on mobile devices by offering one-tap responses (e.g., timeline choices, pain scale ratings) tailored to the active question.
 */

import React from 'react';

export default function QuickReplyChips({ options = [], onSelect, disabled = false }) {
  if (!options || options.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2 px-4 py-2 justify-center max-w-3xl mx-auto">
      {options.map((option, index) => (
        <button
          key={index}
          onClick={() => onSelect(option)}
          disabled={disabled}
          className="px-3.5 py-1.5 text-xs font-medium bg-white text-brand-700 border border-brand-200 rounded-full shadow-xs hover:bg-brand-50 hover:border-brand-500 hover:text-brand-900 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {option}
        </button>
      ))}
    </div>
  );
}