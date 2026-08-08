# backend/app/services/intake/state.py
"""
Session State Machine Engine for ClinicalPrep AI v2.0.

Purpose:
    Manages non-destructive slot merging, monotonic step progression calculation, 
    automatic fallback brief compilation, and output response construction.
"""

from typing import Dict, Any, Optional
from datetime import date
from app.services.intake.schemas import (
    IntakeSessionState,
    ExtractionResult,
    IntakeStepResponse
)


def generate_fallback_summary(session: IntakeSessionState) -> str:
    """
    Synthesizes a clean Markdown summary brief directly from collected session state memory
    if the LLM omits the `summary_brief` string in its response payload.
    """
    demo = session.demographics
    clin = session.clinical_slots

    today_str = date.today().strftime("%B %d, %Y")
    
    return f"""### Patient Pre-Visit Summary
**Date:** {today_str} | **Reason for Visit:** {clin.chief_complaint or 'General Consultation'}

### 1. Patient Information
- **Name:** {demo.name or 'Not reported'}
- **Age:** {demo.age or 'Not reported'} | **Gender:** {demo.gender or 'Not reported'}
- **Height:** {demo.height or 'Not reported'} | **Weight:** {demo.weight or 'Not reported'}
- **Contact:** {demo.contact or 'Not reported'}

### 2. Chief Complaint & History of Present Illness
- **Primary Symptom:** {clin.chief_complaint or 'Not reported'}
- **Onset & Timeline:** {clin.onset_duration or 'Not reported'}
- **Severity & Pattern:** {clin.severity or 'Not reported'} / {clin.pattern_triggers or 'Not reported'}

### 3. Current Interventions
- **Medications/Supplements:** {clin.current_medications or 'None reported'}

### 4. Top Questions for the Doctor
a. {clin.patient_goals or 'None reported'}
"""


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

    # Check if final slot (patient goals) or all core clinical slots are populated
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
    """Orchestrates session state updates across conversation turns and guarantees summary generation."""
    if current_state and isinstance(current_state, dict) and len(current_state) > 0:
        session = IntakeSessionState.model_validate(current_state)
    else:
        session = IntakeSessionState()

    # Lock state if session was previously completed
    if session.is_completed:
        return IntakeStepResponse(
            updated_state=session.model_dump(),
            next_question="Thank you. Your clinical intake details have been recorded.",
            is_completed=True,
            is_emergency=session.is_emergency,
            quick_options=[]
        )

    # 1. Merge slots
    session = merge_slots(session, extracted_result)

    if extracted_result.is_emergency:
        session.is_emergency = True

    # 2. Recalculate step progression
    session.current_step = calculate_current_step(session)

    # 3. Detect completion triggers
    next_q = extracted_result.next_question or ""
    is_completion_phrase = "Thank you. Your clinical intake details have been recorded" in next_q

    if (
        extracted_result.summary_brief or 
        session.summary_brief or 
        session.current_step == 5 or 
        is_completion_phrase
    ):
        session.is_completed = True
        session.current_step = 5

        # Guarantee summary_brief exists
        if extracted_result.summary_brief:
            session.summary_brief = extracted_result.summary_brief
        elif not session.summary_brief:
            session.summary_brief = generate_fallback_summary(session)

        next_q = "Thank you. Your clinical intake details have been recorded."

    quick_opts = [] if session.is_completed else (extracted_result.quick_options or [])

    return IntakeStepResponse(
        updated_state=session.model_dump(),
        next_question=next_q,
        is_completed=session.is_completed,
        is_emergency=session.is_emergency,
        quick_options=quick_opts
    )