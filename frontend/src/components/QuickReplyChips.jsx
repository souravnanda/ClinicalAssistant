// frontend/src/components/QuickReplyChips.jsx
/**
 * Quick Reply Suggestion Chips Component for ClinicalPrep AI v2.0.
 * 
 * Purpose:
 *   Renders dynamic, single-tap option buttons above the chat input field 
 *   to streamline patient responses for common questions (e.g., Chief Complaint, 
 *   Gender identity, Onset/Duration).
 */

import React from 'react';

export const QuickReplyChips = ({ options = [], onSelectOption, disabled = false }) => {
  if (!options || options.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-wrap items-center gap-2 px-4 py-2 bg-amber-50/50 border-t border-slate-100">
      <span className="text-xs font-medium text-amber-900/70 mr-1">Suggested:</span>
      {options.map((option, index) => (
        <button
          key={index}
          type="button"
          disabled={disabled}
          onClick={() => onSelectOption(option)}
          className="px-3 py-1.5 text-xs font-medium rounded-lg bg-white text-slate-700 border border-slate-300 shadow-sm hover:bg-amber-800 hover:text-white hover:border-amber-800 transition-all duration-150 active:scale-95 disabled:opacity-50 disabled:pointer-events-none"
        >
          {option}
        </button>
      ))}
    </div>
  );
};

export default QuickReplyChips;