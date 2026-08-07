"""
FILE: backend/app/services/intake/state.py
PURPOSE: Session state machine manager for clinical intake workflow.
WHY WE NEED IT: Merges newly extracted slots into persistent session memory, tracks workflow step progression, and handles intake completion state.
"""

from typing import Tuple, List, Optional
from app.services.intake.schemas import IntakeSessionState, ExtractionResult
from app.services.intake.extractor import extract_slots_from_turn


def merge_slots(current_state: IntakeSessionState, extraction: ExtractionResult) -> IntakeSessionState:
    """Merges non-null extracted slot values into current session state memory."""
    # Merge demographics
    for field, value in extraction.demographics.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(current_state.demographics, field, value)

    # Merge clinical slots
    for field, value in extraction.clinical_slots.model_dump(exclude_unset=True).items():
        if value is not None and field != 'doctor_questions':
            setattr(current_state.clinical_slots, field, value)
    
    if extraction.clinical_slots.doctor_questions:
        for question in extraction.clinical_slots.doctor_questions:
            if question not in current_state.clinical_slots.doctor_questions:
                current_state.clinical_slots.doctor_questions.append(question)

    # Merge emergency flag
    if extraction.is_emergency:
        current_state.is_emergency = True

    return current_state


def calculate_current_step(state: IntakeSessionState) -> int:
    """Calculates current intake workflow step (1 through 5) based on filled slots."""
    demo = state.demographics
    slots = state.clinical_slots

    # Step 1: Demographics & Chief Complaint
    if not (demo.name and slots.chief_complaint):
        return 1
    # Step 2: Onset & Severity Details
    if not (slots.onset_duration and slots.severity):
        return 2
    # Step 3: Interventions & Current Medications
    if not slots.current_medications:
        return 3
    # Step 4: Doctor Questions & Goals
    if not slots.doctor_questions:
        return 4
    # Step 5: Brief Generation / Completed
    return 5


def process_user_turn(
    user_message: str,
    current_state: IntakeSessionState
) -> Tuple[IntakeSessionState, str, Optional[List[str]]]:
    """
    PURPOSE: Processes a single user message turn, updates state memory, and returns follow-up actions.
    
    ARGS:
        user_message (str): Patient's natural language input.
        current_state (IntakeSessionState): Current persistent session state.
        
    RETURNS:
        Tuple[IntakeSessionState, str, Optional[List[str]]]:
            - Updated session state object
            - Next targeted follow-up question
            - Quick-reply options list for UI
    """
    # 1. Append user message to conversation history
    current_state.conversation_history.append({
        "role": "user",
        "content": user_message
    })

    # 2. Extract slots via LLM Structured Output Extractor
    extraction: ExtractionResult = extract_slots_from_turn(
        user_message=user_message,
        current_state=current_state
    )

    # 3. Merge newly extracted slots into persistent session state
    updated_state = merge_slots(current_state, extraction)

    # 4. Update workflow progress step
    updated_state.current_step = calculate_current_step(updated_state)

    # 5. Handle completion check and brief generation
    if updated_state.current_step == 5 and not updated_state.is_completed:
        updated_state.is_completed = True
        questions_str = ", ".join(updated_state.clinical_slots.doctor_questions) if updated_state.clinical_slots.doctor_questions else "None specified"
        updated_state.summary_brief = (
            f"# CLINICAL PREP BRIEF\n"
            f"**Patient Name:** {updated_state.demographics.name or 'N/A'}\n"
            f"**Age:** {updated_state.demographics.age or 'N/A'} | **Gender:** {updated_state.demographics.gender or 'N/A'}\n\n"
            f"### CLINICAL DETAILS\n"
            f"- **Chief Complaint:** {updated_state.clinical_slots.chief_complaint or 'N/A'}\n"
            f"- **Onset / Duration:** {updated_state.clinical_slots.onset_duration or 'N/A'}\n"
            f"- **Severity:** {updated_state.clinical_slots.severity or 'N/A'}\n"
            f"- **Current Medications:** {updated_state.clinical_slots.current_medications or 'N/A'}\n"
            f"- **Questions for Doctor:** {questions_str}"
        )

    # 6. Append assistant response to conversation history
    updated_state.conversation_history.append({
        "role": "assistant",
        "content": extraction.next_question
    })

    return updated_state, extraction.next_question, extraction.quick_options