# ==============================================================================
# FILE: backend/app/services/intake/state.py
# PURPOSE: Deterministic state machine engine for managing active intake progression.
# SCOPE: Updates transient session memory with extracted slots, evaluates stage completion rules,
#        handles emergency state shifts, and advances step tracking monotonically.
# ==============================================================================

from app.services.intake.schemas import IntakeSessionState, ExtractionResult


class IntakeStateManager:
    """
    PURPOSE: Manages session updates, slot state merges, and progress step calculations for active sessions.
    ROLE: Ensures immutable updates to state memory and regulates transition between steps 1 through 5.
    """

    @staticmethod
    def update_session_state(state: IntakeSessionState, extraction: ExtractionResult) -> IntakeSessionState:
        """
        PURPOSE: Merges newly extracted slots into session memory and advances the active step counter.
        ARGS:
            state (IntakeSessionState): Active session state before current turn processing.
            extraction (ExtractionResult): Extracted entities and flags returned by extractor engine.
        RETURNS:
            IntakeSessionState: Updated session state ready for storage or immediate UI rendering.
        """
        # 1. Triage Check: If red-flags detected, flag session for emergency intervention
        if extraction.detected_emergency:
            state.is_emergency = True
            return state

        # 2. Merge Demographics: Perform non-null attribute updates
        for field, value in extraction.demographics.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(state.demographics, field, value)

        # 3. Merge Clinical Details: Perform non-null attribute updates
        for field, value in extraction.clinical.model_dump(exclude_unset=True).items():
            if value is not None and value != []:
                setattr(state.clinical, field, value)

        # 4. Step Progress Calculation: Re-evaluate state rules to set monotonic step (1-5)
        state.current_step = IntakeStateManager._calculate_step(state)

        # 5. Completion Evaluation: Set flag when zero mandatory slots remain missing
        if not extraction.missing_slots:
            state.is_complete = True

        return state

    @staticmethod
    def _calculate_step(state: IntakeSessionState) -> int:
        """
        PURPOSE: Internal step-evaluation logic enforcing sequential milestone progress.
        MILESTONES:
            Step 1: Patient Demographics & Chief Complaint Intake
            Step 2: OPQRST Symptom Deep-Dive (Onset, Severity, Quality)
            Step 3: Interventions & Medications History
            Step 4: Appointment Goals & Doctor Questions
            Step 5: Finalized Brief Generation
        """
        demo = state.demographics
        clin = state.clinical

        # Step 1: Demographics & Initial Visit Reason
        if not demo.name or not clin.chief_complaint:
            return 1
            
        # Step 2: Symptom OPQRST Timeline and Severity
        if not clin.onset_duration or not clin.severity_quality:
            return 2
            
        # Step 3: Remedies, Interventions, and Current Medications
        if not clin.interventions_meds:
            return 3
            
        # Step 4: Questions for Physician / Appointment Goals
        if not clin.patient_questions:
            return 4
            
        # Step 5: All Core Data Gathered -> Ready for PDF Summary Generation
        return 5