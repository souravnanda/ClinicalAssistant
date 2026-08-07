"""
FILE: backend/app/services/intake/state.py
PURPOSE: Session state machine manager ensuring demographic completeness, slot merging, and monotonic step progression.
"""

from typing import Tuple, List, Optional
from app.services.intake.schemas import IntakeSessionState, ExtractionResult
from app.services.intake.extractor import extract_slots_from_turn


def merge_slots(current_state: IntakeSessionState, extraction: ExtractionResult) -> IntakeSessionState:
    """PURPOSE: Safely merges non-null extracted slot values into persistent session memory."""
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
    """PURPOSE: Calculates current intake workflow step (1 through 5) based on filled slots, ensuring monotonic progression."""
    demo = state.demographics
    slots = state.clinical_slots

    calculated_step = 1

    # Step 1 Complete: Demographics (Name, Age, Gender, Height, Weight, Contact) + Chief Complaint
    if demo.name and demo.age and demo.gender and demo.height and demo.weight and demo.contact and slots.chief_complaint:
        calculated_step = 2
        # Step 2 Complete: Onset & Severity Details
        if slots.onset_duration and slots.severity:
            calculated_step = 3
            # Step 3 Complete: Interventions & Medications
            if slots.current_medications:
                calculated_step = 4
                # Step 4 Complete: Doctor Questions
                if slots.doctor_questions:
                    calculated_step = 5

    # Enforce Monotonicity (Step tracker cannot regress)
    return max(state.current_step, calculated_step)


def process_user_turn(
    user_message: str,
    current_state: IntakeSessionState
) -> Tuple[IntakeSessionState, str, Optional[List[str]]]:
    """PURPOSE: Orchestrates conversation turn, merges state, checks workflow completion, and generates Doctor Brief."""
    # 1. Append user message to conversation history
    current_state.conversation_history.append({
        "role": "user",
        "content": user_message
    })

    # 2. Extract slots via LLM Extractor
    extraction: ExtractionResult = extract_slots_from_turn(
        user_message=user_message,
        current_state=current_state
    )

    # 3. Merge newly extracted slots into persistent session state
    updated_state = merge_slots(current_state, extraction)

    # 4. Update workflow progress step safely
    updated_state.current_step = calculate_current_step(updated_state)

    # 5. Handle completion check and brief generation
    if updated_state.current_step == 5 and not updated_state.is_completed:
        updated_state.is_completed = True
        questions_str = ", ".join(updated_state.clinical_slots.doctor_questions) if updated_state.clinical_slots.doctor_questions else "None specified"
        updated_state.summary_brief = (
            f"# CLINICAL PREP BRIEF\n"
            f"**Patient Name:** {updated_state.demographics.name or 'N/A'}\n"
            f"**Age:** {updated_state.demographics.age or 'N/A'} | **Gender:** {updated_state.demographics.gender or 'N/A'}\n"
            f"**Height:** {updated_state.demographics.height or 'N/A'} | **Weight:** {updated_state.demographics.weight or 'N/A'}\n"
            f"**Contact:** {updated_state.demographics.contact or 'N/A'}\n\n"
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