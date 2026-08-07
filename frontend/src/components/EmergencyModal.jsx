/**
 * FILE: frontend/src/components/EmergencyModal.jsx
 * PURPOSE: High-priority modal overlay triggered during acute red-flag detection.
 * WHY WE NEED IT: Enforces clinical safety by instantly halting non-diagnostic intake when critical symptoms (e.g., chest pain, severe dyspnea) are mentioned, directing patients to 911 / emergency care.
 */

import React from 'react';
import { AlertTriangle, PhoneCall } from 'lucide-react';

export default function EmergencyModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
      <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border-2 border-red-500 text-center animate-in fade-in zoom-in duration-200">
        <div className="w-12 h-12 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto mb-4">
          <AlertTriangle className="w-7 h-7" />
        </div>

        <h2 className="text-xl font-bold text-red-700 mb-2">Emergency Symptom Detected</h2>
        <p className="text-sm text-gray-700 leading-relaxed mb-6">
          Your input contains indicators that require immediate medical evaluation. Please stop this intake session and contact emergency medical services right away.
        </p>

        <div className="flex flex-col gap-3">
          <a
            href="tel:911"
            className="flex items-center justify-center gap-2 w-full py-3 bg-red-600 text-white font-bold rounded-xl shadow-md hover:bg-red-700 transition-all"
          >
            <PhoneCall className="w-5 h-5" />
            <span>Call 911 / Emergency Care</span>
          </a>

          <button
            onClick={onClose}
            className="w-full py-2.5 text-xs text-gray-500 hover:text-gray-800 font-medium"
          >
            Acknowledge & Continue Assessment
          </button>
        </div>
      </div>
    </div>
  );
}