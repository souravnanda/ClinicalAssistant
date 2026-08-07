# backend/app/services/intake/state.py
"""
Session State Machine Engine for ClinicalPrep AI v2.0.

Purpose:
    Manages non-destructive slot merging, monotonic step progression calculation,
    and output response construction for multi-turn clinical conversations.
"""

from typing import Dict, Any, Optional
from app.services.intake.schemas import (
    IntakeSessionState,
    ExtractionResult,
    IntakeStepResponse,
    PatientDemographics,
    ClinicalSlots
)


def merge_slots(current_state: IntakeSessionState, extracted: ExtractionResult) -> IntakeSessionState:
    """
    Non-destructively merges newly extracted demographic and clinical slots into the active session state.
    
    Preserves all previously captured slot values and only updates fields when new non-null and 
    non-empty strings are extracted during the current turn.

    Args:
        current_state (IntakeSessionState): Active session memory instance.
        extracted (ExtractionResult): Structured extraction result from the LLM parser.

    Returns:
        IntakeSessionState: Session memory instance with updated slot values.
    """
    # 1. Merge Demographic Slots
    if extracted.demographics:
        for field, value in extracted.demographics.model_dump().items():
            if value is not None and value != "":
                setattr(current_state.demographics, field, value)

    # 2. Merge Clinical Symptoms Slots
    if extracted.clinical_slots:
        for field, value in extracted.clinical_slots.model_dump().items():
            if value is not None and value != "":
                setattr(current_state.clinical_slots, field, value)

    return current_state


def calculate_current_step(state: IntakeSessionState) -> int:
    """
    Calculates intake stage progression monotonically from Step 1 through Step 5.
    
    Monotonic progression prevents step regression to ensure a consistent patient 
    interview experience.

    Step Progression Criteria:
        - Step 1: Demographics & Initial Chief Complaint Gathering
        - Step 2: History & Onset/Duration Investigation
        - Step 3: Symptom Characteristics (Severity, Pattern, Triggers)
        - Step 4: Interventions, Medications & Goals
        - Step 5: Intake Complete (Doctor Brief Finalized)

    Args:
        state (IntakeSessionState): Active session memory instance.

    Returns:
        int: Calculated progression step number (1 to 5).
    """
    demo = state.demographics
    clin = state.clinical_slots

    # Enforce monotonic step progression (never regress below current step)
    highest_step = max(getattr(state, "current_step", 1) or 1, 1)

    # Step 5 Check: Doctor Brief generated or all primary clinical slots satisfied
    if state.is_completed or (
        clin.chief_complaint and clin.onset_duration and clin.severity and 
        clin.current_medications and clin.patient_goals
    ):
        return 5

    # Step 4 Check: Name, chief complaint, duration, and severity captured
    if demo.name and clin.chief_complaint and clin.onset_duration and clin.severity:
        return max(highest_step, 4)

    # Step 3 Check: Name, chief complaint, and duration captured
    if demo.name and clin.chief_complaint and clin.onset_duration:
        return max(highest_step, 3)

    # Step 2 Check: Name and chief complaint captured
    if demo.name and clin.chief_complaint:
        return max(highest_step, 2)

    # Default to Step 1
    return highest_step


def update_session_state(
    current_state: Optional[Dict[str, Any]], 
    extracted_result: ExtractionResult
) -> IntakeStepResponse:
    """
    Orchestrates session state updates across conversation turns.

    Validates existing session state dictionaries, applies non-destructive slot merging,
    re-calculates current step progression, processes emergency red flags, and constructs 
    the API response payload.

    Args:
        current_state (Optional[Dict[str, Any]]): Existing session dictionary from the client request.
        extracted_result (ExtractionResult): Validated extraction result from the slot extractor.

    Returns:
        IntakeStepResponse: Validated response payload containing updated state, next question, 
                            and triage indicators.
    """
    # 1. Instantiate or validate existing session memory
    if current_state and isinstance(current_state, dict) and len(current_state) > 0:
        session = IntakeSessionState.model_validate(current_state)
    else:
        session = IntakeSessionState()

    # 2. Merge newly extracted slots into session state
    session = merge_slots(session, extracted_result)

    # 3. Monotonically update intake progression step
    session.current_step = calculate_current_step(session)

    # 4. Handle red-flag emergency flags
    if extracted_result.is_emergency:
        session.is_emergency = True

    # 5. Process completion summary brief
    if extracted_result.summary_brief:
        session.summary_brief = extracted_result.summary_brief
        session.is_completed = True
        session.current_step = 5

    # 6. Format and return IntakeStepResponse for client consuming API
    return IntakeStepResponse(
        updated_state=session.model_dump(),
        next_question=extracted_result.next_question or "Thank you. Your clinical intake details have been recorded.",
        is_completed=session.is_completed,
        is_emergency=session.is_emergency,
        quick_options=extracted_result.quick_options or []
    )