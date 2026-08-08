// frontend/src/components/SummaryCard.jsx
/**
 * Summary Card Component for ClinicalPrep AI v2.0.
 * 
 * Purpose:
 *   Renders the formatted Markdown Doctor Brief and provides a 1-click trigger
 *   to download the official Clinical Record PDF document.
 */

import React, { useState } from 'react';
import { FileText, Download, CheckCircle, Loader2 } from 'lucide-react';
import { downloadIntakePdf } from '../services/api';

export const SummaryCard = ({ summaryBrief, sessionState }) => {
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownload = async () => {
    try {
      setIsDownloading(true);
      await downloadIntakePdf(sessionState);
    } catch (err) {
      console.error('PDF Download Error:', err);
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg border border-amber-200 overflow-hidden my-4 transition-all">
      {/* Header Banner */}
      <div className="bg-amber-800 text-white p-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <CheckCircle className="w-5 h-5 text-amber-300" />
          <h3 className="font-semibold text-base">Patient Pre-Visit Summary Ready</h3>
        </div>
        <button
          type="button"
          onClick={handleDownload}
          disabled={isDownloading}
          className="bg-white text-amber-900 hover:bg-amber-50 font-medium px-4 py-2 rounded-lg text-xs flex items-center gap-1.5 transition-colors shadow-sm disabled:opacity-50"
        >
          {isDownloading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Download className="w-4 h-4 text-amber-800" />
          )}
          <span>{isDownloading ? 'Generating PDF...' : 'Download Summary PDF'}</span>
        </button>
      </div>

      {/* Markdown Brief Content */}
      <div className="p-6 bg-amber-50/30 text-slate-800 text-sm leading-relaxed font-sans">
        <div className="prose prose-amber max-w-none whitespace-pre-wrap">
          {summaryBrief}
        </div>
      </div>
    </div>
  );
};

export default SummaryCard;