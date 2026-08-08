# backend/app/services/intake/extractor.py
"""
Slot Extraction Engine for ClinicalPrep AI v2.0.

Purpose:
    Parses unstructured patient dialogue into clinical slots using OpenAI 
    Structured Outputs (Pydantic v2 schemas), evaluates emergency red flags, 
    generates targeted follow-up questions, and ensures deterministic quick-reply chips.
"""

import os
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI

from app.services.intake.schemas import ExtractionResult

# Load environment variables dynamically
load_dotenv(find_dotenv())

# CC-SC-R System Prompt with Explicit Quick-Reply Chip Directives
EXTRACTOR_SYSTEM_PROMPT = """
# CONTEXT
You are an empathetic, professional triage nurse assistant for ClinicalPrep AI. 
Your role is to collect structured patient intake details before their doctor's appointment.

# CONSTRAINTS
1. Never offer medical advice, diagnoses, or treatment recommendations.
2. Maintain a warm, supportive, and professional tone.
3. If the patient mentions severe acute symptoms (e.g., chest pain, difficulty breathing, sudden numbness, severe trauma), set `is_emergency=True`.
4. Ask ONLY ONE clear follow-up question at a time during active intake.
5. Store negative answers (e.g., "no medication", "none") as "None reported" rather than leaving fields null.
6. Address the patient warmly by name once their name is captured.

# QUICK REPLY CHIPS DIRECTIVES (`quick_options`)
You MUST ALWAYS populate `quick_options` with non-empty list of string options whenever asking these specific questions:
- Asking for Gender Identity: `["Male", "Female", "Non-Binary"]`
- Asking for Chief Complaint / Reason for visit: `["Headache / Migraine", "Lower Back Pain", "Cough & Fever", "General Health Checkup", "Other"]`
- Asking for Onset / Timeline: `["Yesterday", "3-7 days ago", "More than a week", "More than a month"]`
- Asking for Severity Rating: `["Mild (1-3)", "Moderate (4-6)", "Severe (7-9)", "Very Severe (10)"]`
- Asking for Symptom Pattern: `["Constant", "Intermittent", "Comes and goes in waves", "Worse at night/morning"]`
- Asking for Triggers: `["Movement / Exercise", "Stress / Fatigue", "Eating / Food", "Certain Positions", "None noticed"]`
- Asking for Current Medications: `["Over-the-counter pain relievers", "Prescription medication", "Rest & ice/heat", "None reported"]`
- For open-ended text inputs (e.g., Name, Age, Height, Weight, or clarifying "Other"), set `quick_options` to `[]`.

# STRUCTURE & CHECKPOINTS
1. Step 1 (Demographics): Gather Name, Age, Gender, Height, Weight, and Contact sequentially.
2. Step 2 (Chief Complaint & Onset): Gather Chief Complaint, then Onset/Duration.
3. Step 3 (OPQRST Deep-Dive): Gather Severity (1-10), Pattern/Triggers, and Current Medications.
4. Step 4 (Goals): Ask for questions/goals the patient wants to discuss with the physician.
5. Step 5 (Completion): When all core slots are collected, set `next_question` to "Thank you. Your clinical intake details have been recorded." and generate the complete `summary_brief`.
"""


def get_openai_client() -> OpenAI:
    """Lazily instantiates the OpenAI client when needed."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is missing. Please check your .env file.")
    return OpenAI(api_key=api_key)


def enforce_quick_options_fallback(next_question: str, quick_options: Optional[List[str]]) -> List[str]:
    """
    Deterministic Python fallback mechanism.
    Guarantees quick reply chips are populated if the LLM returns an empty list.
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

    if any(k in q_lower for k in ["pattern", "constant", "intermittent", "come and go", "behave"]):
        return ["Constant", "Intermittent", "Comes and goes in waves", "Worse at night/morning"]

    if any(k in q_lower for k in ["trigger", "worse", "better", "factor", "aggravat"]):
        return ["Movement / Exercise", "Stress / Fatigue", "Eating / Food", "Certain Positions", "None noticed"]

    if any(k in q_lower for k in ["medication", "medicine", "drug", "taking", "prescription"]):
        return ["Over-the-counter pain relievers", "Prescription medication", "Rest & ice/heat", "None reported"]

    return []


async def extract_clinical_slots(
    user_message: str, 
    current_state: Optional[Dict[str, Any]] = None
) -> ExtractionResult:
    """
    Extracts structured clinical slots from user dialogue using OpenAI Pydantic parsing.
    Applies deterministic fallback logic to guarantee quick-reply chip delivery.
    """
    client = get_openai_client()
    state_context = current_state or {}

    prompt_messages = [
        {"role": "system", "content": EXTRACTOR_SYSTEM_PROMPT},
        {"role": "system", "content": f"Current Accumulated Intake State: {state_context}"},
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

        # Apply deterministic fallback to guarantee chips are never omitted
        result.quick_options = enforce_quick_options_fallback(
            next_question=result.next_question,
            quick_options=result.quick_options
        )

        return result

    except Exception as e:
        print(f"⚠️ Slot Extraction API Error: {e}")
        fallback_q = "Could you please tell me what brings you in to see the doctor today?"
        return ExtractionResult(
            next_question=fallback_q,
            is_emergency=False,
            quick_options=enforce_quick_options_fallback(fallback_q, [])
        )