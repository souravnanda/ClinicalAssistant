# backend/app/services/intake/state.py
"""
Session State Machine Engine for ClinicalPrep AI v2.0.

Purpose:
    Manages non-destructive slot merging, monotonic step progression calculation, 
    and output construction for multi-turn clinical conversations.
"""

from typing import Dict, Any, Optional
from app.services.intake.schemas import (
    IntakeSessionState,
    ExtractionResult,
    IntakeStepResponse
)


def merge_slots(current_state: IntakeSessionState, extracted: ExtractionResult) -> IntakeSessionState:
    """Non-destructively merges newly extracted slots into active session memory."""
    if extracted.demographics:
        for field, value in extracted.demographics.model_dump().items():
            if value is not None and value != "":
                setattr(current_state.demographics, field, value)

    if extracted.clinical_slots:
        for field, value in extracted.clinical_slots.model_dump().items():
            if value is not None and value != "":
                setattr(current_state.clinical_slots, field, value)

    return current_state


def calculate_current_step(state: IntakeSessionState) -> int:
    """Calculates intake stage progression monotonically from Step 1 through Step 5."""
    demo = state.demographics
    clin = state.clinical_slots

    highest_step = max(getattr(state, "current_step", 1) or 1, 1)

    if state.is_completed or bool(state.summary_brief):
        return 5

    if clin.chief_complaint and clin.onset_duration and clin.severity and clin.patient_goals:
        return 5

    if demo.name and clin.chief_complaint and clin.onset_duration and clin.severity:
        return max(highest_step, 4)

    if demo.name and clin.chief_complaint and clin.onset_duration:
        return max(highest_step, 3)

    if demo.name and clin.chief_complaint:
        return max(highest_step, 2)

    return highest_step


def update_session_state(
    current_state: Optional[Dict[str, Any]], 
    extracted_result: ExtractionResult
) -> IntakeStepResponse:
    """Orchestrates session state updates across conversation turns."""
    if current_state and isinstance(current_state, dict) and len(current_state) > 0:
        session = IntakeSessionState.model_validate(current_state)
    else:
        session = IntakeSessionState()

    # If session was already completed on a prior turn, lock state
    if session.is_completed:
        return IntakeStepResponse(
            updated_state=session.model_dump(),
            next_question="Thank you. Your clinical intake details have been recorded.",
            is_completed=True,
            is_emergency=session.is_emergency,
            quick_options=[]
        )

    # Merge slots and update step
    session = merge_slots(session, extracted_result)

    if extracted_result.is_emergency:
        session.is_emergency = True

    if extracted_result.summary_brief or session.summary_brief:
        if extracted_result.summary_brief:
            session.summary_brief = extracted_result.summary_brief
        session.is_completed = True
        session.current_step = 5

    session.current_step = calculate_current_step(session)

    next_q = "Thank you. Your clinical intake details have been recorded." if session.is_completed else (
        extracted_result.next_question or "Could you please elaborate?"
    )

    quick_opts = [] if session.is_completed else (extracted_result.quick_options or [])

    return IntakeStepResponse(
        updated_state=session.model_dump(),
        next_question=next_q,
        is_completed=session.is_completed,
        is_emergency=session.is_emergency,
        quick_options=quick_opts
    )