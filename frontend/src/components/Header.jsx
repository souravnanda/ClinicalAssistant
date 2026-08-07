/**
 * FILE: frontend/src/components/Header.jsx
 * PURPOSE: Sticky top navbar displaying application branding and intake progress.
 * WHY WE NEED IT: Provides visual feedback on current intake completion across the 5 clinical stages (Chief Complaint -> Onset -> Symptoms -> Medications -> Goals) so the patient knows their position in the workflow.
 */

import React from 'react';
import { Activity, ShieldAlert } from 'lucide-react';

const STAGES = [
  'Demographics & Reason',
  'Symptom Details',
  'Interventions & Meds',
  'Doctor Questions',
  'Doctor Brief'
];

export default function Header({ currentStep = 1, isEmergency = false }) {
  const activeStep = Math.min(Math.max(currentStep, 1), 5);
  const progressPercent = (activeStep / 5) * 100;

  return (
    <header className="sticky top-0 z-30 bg-[#FFF8F0]/95 backdrop-blur-md border-b border-brand-200 shadow-sm px-4 py-3 transition-all">
      <div className="max-w-3xl mx-auto flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-brand-500 text-white rounded-xl shadow-xs">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <h1 className="font-bold text-lg text-brand-900 leading-tight">ClinicalPrep AI</h1>
              <p className="text-xs text-brand-700">Patient Intake Assistant</p>
            </div>
          </div>

          {isEmergency && (
            <div className="flex items-center gap-1.5 bg-red-100 text-red-700 px-3 py-1 rounded-full text-xs font-semibold animate-pulse">
              <ShieldAlert className="w-4 h-4" />
              <span>Emergency Flag</span>
            </div>
          )}
        </div>

        {/* 5-Step Progress Tracker */}
        <div className="w-full bg-brand-100 h-2 rounded-full overflow-hidden mt-1">
          <div
            className="bg-brand-500 h-full transition-all duration-500 ease-out"
            style={{ width: `${progressPercent}%` }}
          />
        </div>

        <div className="flex justify-between items-center text-[11px] font-medium text-brand-700">
          <span>Step {activeStep} of 5: {STAGES[activeStep - 1]}</span>
          <span>{progressPercent}% Complete</span>
        </div>
      </div>
    </header>
  );
}