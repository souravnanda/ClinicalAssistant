# backend/app/services/intake/extractor.py
"""
Slot Extraction Engine for ClinicalPrep AI v2.0.

Purpose:
    Uses OpenAI Structured Outputs with Pydantic v2 schemas to parse unstructured 
    patient dialogue into clinical slots, evaluate emergency red flags, generate 
    targeted follow-up questions, and enforce deterministic quick-reply chips.
"""

import os
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI

from app.services.intake.schemas import ExtractionResult

# Load environment variables dynamically from .env
load_dotenv(find_dotenv())

# CC-SC-R System Prompt with Explicit Sequential Intake Rules
EXTRACTOR_SYSTEM_PROMPT = """
# CONTEXT
You are an empathetic, professional triage nurse assistant for ClinicalPrep AI. 
Your role is to collect structured patient intake details before their doctor's appointment.

# CONSTRAINTS & MANDATORY SEQUENCE
1. Never offer medical advice, diagnoses, or treatment recommendations.
2. Maintain a warm, supportive, and professional tone.
3. Address the patient warmly by name once captured.
4. DO NOT SKIP STEPS or complete the intake prematurely. You MUST follow this exact sequence:

   - PHASE 1 (Demographics): Gather Name, Age, Gender, Height, Weight, and Contact Info.
   - PHASE 2 (Chief Complaint): Ask "What brings you in today?" or "What is the primary reason for your visit?"
   - PHASE 3 (OPQRST Deep-Dive):
     * Onset / Duration: "When did this symptom start and how long does it last?"
     * Severity (1-10 Scale): "How would you rate the severity on a scale of 1 to 10?"
     * Pattern / Triggers: "Is the discomfort constant or intermittent, and what triggers or relieves it?"
     * Current Medications: "Are you currently taking any medications, OTC pain relievers, or supplements?"
   - PHASE 4 (Goals): "What specific questions or goals do you want to discuss with your physician?"
   - PHASE 5 (Completion): ONLY after Phase 1 through Phase 4 are fully answered, set `next_question` to "Thank you. Your clinical intake details have been recorded." and generate the `summary_brief`.

# QUICK REPLY CHIPS DIRECTIVES (`quick_options`)
Always populate `quick_options` appropriately:
- Asking Gender: ["Male", "Female", "Non-Binary"]
- Asking Chief Complaint: ["Headache / Migraine", "Lower Back Pain", "Cough & Fever", "General Health Checkup", "Other"]
- Asking Onset/Timeline: ["Yesterday", "3-7 days ago", "More than a week", "More than a month"]
- Asking Severity: ["Mild (1-3)", "Moderate (4-6)", "Severe (7-9)", "Very Severe (10)"]
- Asking Pattern: ["Constant", "Intermittent", "Comes and goes in waves", "Worse at night/morning"]
- Asking Medications: ["Over-the-counter pain relievers", "Prescription medication", "Rest & ice/heat", "None reported"]
- Open-ended text inputs (Name, Age, Contact, Goals): Set `quick_options` to `[]`.
"""


def get_openai_client() -> OpenAI:
    """Lazily instantiates the OpenAI client when needed."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is missing. Please check your .env file.")
    return OpenAI(api_key=api_key)


def enforce_quick_options_fallback(next_question: str, quick_options: Optional[List[str]]) -> List[str]:
    """
    Deterministic Python fallback mechanism for quick reply chips.
    Guarantees contextual chips are populated even if the LLM returns an empty list.
    """
    if quick_options and len(quick_options) > 0:
        return quick_options

    q_lower = (next_question or "").lower()

    if "gender" in q_lower:
        return ["Male", "Female", "Non-Binary"]
    if any(k in q_lower for k in ["chief complaint", "reason", "brings you in", "visiting", "today"]):
        return ["Headache / Migraine", "Lower Back Pain", "Cough & Fever", "General Health Checkup", "Other"]
    if any(k in q_lower for k in ["start", "when", "how long", "onset", "timeline", "duration"]):
        return ["Yesterday", "3-7 days ago", "More than a week", "More than a month"]
    if any(k in q_lower for k in ["scale", "severe", "severity", "rate", "1-10", "1 to 10"]):
        return ["Mild (1-3)", "Moderate (4-6)", "Severe (7-9)", "Very Severe (10)"]
    if any(k in q_lower for k in ["pattern", "constant", "intermittent", "come and go"]):
        return ["Constant", "Intermittent", "Comes and goes in waves", "Worse at night/morning"]
    if any(k in q_lower for k in ["medication", "medicine", "drug", "taking"]):
        return ["Over-the-counter pain relievers", "Prescription medication", "Rest & ice/heat", "None reported"]

    return []


async def extract_clinical_slots(
    user_message: str, 
    current_state: Optional[Dict[str, Any]] = None
) -> ExtractionResult:
    """
    Extracts structured clinical slots from user dialogue using OpenAI Pydantic parsing.
    """
    client = get_openai_client()
    state_context = current_state or {}

    prompt_messages = [
        {"role": "system", "content": EXTRACTOR_SYSTEM_PROMPT},
        {"role": "system", "content": f"Current Accumulated Session Memory: {state_context}"},
        {"role": "user", "content": user_message}
    ]

    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=prompt_messages,
            response_format=ExtractionResult,
            temperature=0.1,
        )
        result: ExtractionResult = completion.choices[0].message.parsed
        result.quick_options = enforce_quick_options_fallback(result.next_question, result.quick_options)
        return result

    except Exception as e:
        print(f"⚠️ Slot Extraction API Error: {e}")
        fallback_q = "Could you please describe what brings you in to see the doctor today?"
        return ExtractionResult(
            next_question=fallback_q,
            is_emergency=False,
            quick_options=enforce_quick_options_fallback(fallback_q, [])
        )