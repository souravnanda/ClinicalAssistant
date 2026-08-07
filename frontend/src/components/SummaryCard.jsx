/**
 * FILE: frontend/src/components/SummaryCard.jsx
 * PURPOSE: Structured Doctor Brief display component.
 * WHY WE NEED IT: Formats extracted clinical slots and session data into a clean, reviewable report once intake reaches completion, complete with direct copy/print controls.
 */

import React from 'react';
import { FileText, Copy, Check } from 'lucide-react';

export default function SummaryCard({ summaryText }) {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(summaryText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!summaryText) return null;

  return (
    <div className="bg-white border-2 border-brand-500 rounded-2xl p-5 shadow-md my-4 max-w-2xl mx-auto">
      <div className="flex items-center justify-between border-b border-brand-100 pb-3 mb-3">
        <div className="flex items-center gap-2 text-brand-900 font-bold">
          <FileText className="w-5 h-5 text-brand-500" />
          <h3>Generated Doctor Brief</h3>
        </div>

        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 text-xs font-medium text-brand-700 hover:text-brand-900 bg-brand-50 px-3 py-1.5 rounded-lg border border-brand-200 transition-all"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-green-600" /> : <Copy className="w-3.5 h-3.5" />}
          <span>{copied ? 'Copied' : 'Copy Text'}</span>
        </button>
      </div>

      <div className="text-xs text-brand-900 font-mono whitespace-pre-wrap bg-brand-50/50 p-4 rounded-xl border border-brand-100 leading-relaxed max-h-80 overflow-y-auto">
        {summaryText}
      </div>
    </div>
  );
}