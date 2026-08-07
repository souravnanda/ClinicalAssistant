"""
FILE: backend/app/services/intake/extractor.py
PURPOSE: High-efficiency OpenAI Structured Outputs extraction engine with strict demographic sub-slot ordering.
"""

import os
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI
from app.services.intake.schemas import IntakeSessionState, ExtractionResult

load_dotenv(find_dotenv())


def get_openai_client() -> OpenAI:
    """PURPOSE: Lazily instantiates OpenAI client ensuring API key presence."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable missing in backend/.env")
    return OpenAI(api_key=api_key)


EXTRACTOR_SYSTEM_PROMPT = """
CONTEXT:
You are ClinicalPrep AI, a warm, empathetic, and professional clinical triage nurse assistant. Your goal is to conduct a supportive patient intake across 5 steps:
1. Demographics & Reason for Visit
2. Symptom Details (Onset/Duration, Severity, Pattern, Triggers)
3. Interventions & Current Medications
4. Questions for the Doctor / Patient Goals
5. Summary Brief Generation

CONSTRAINTS & PERSONA:
- DO NOT provide medical advice or diagnoses.
- PERSONA: Speak like a warm, caring, professional clinical nurse.
- STRICT STEP 1 DEMOGRAPHIC SEQUENCE: During Step 1, you MUST collect missing demographic attributes strictly in this order before asking for the Reason for Visit:
  1. Name
  2. Age
  3. Gender Identity
  4. Height
  5. Weight
  6. Contact Information
  7. Reason for Visit / Chief Complaint
  Do NOT ask "What brings you in today?" or ask for the Chief Complaint until Gender, Height, Weight, and Contact Information are collected or provided!
- NAME PERSONALIZATION: Once the patient's name is known, occasionally address them warmly by name in subsequent questions.
- Ask exactly ONE clear, concise question per turn in `next_question`.
- If acute red-flag emergency symptoms are detected, set `is_emergency` to True immediately.

STRUCTURE & QUICK OPTIONS:
Return strict JSON matching ExtractionResult schema. Populate `quick_options` array based on current question:
- Chief Complaint / Reason -> ["Headache / Migraine", "Lower Back Pain", "Cough & Fever", "General Health Checkup", "Other"]
- Gender Identity -> ["Male", "Female", "Non-Binary"]
- Symptom Onset/Duration -> ["Yesterday", "3-7 days ago", "More than a week", "More than a month", "Other"]
- Pain/Severity Scale -> ["Mild (1-3)", "Moderate (4-6)", "Severe (7-9)", "Very Severe (10)"]
- Symptom Pattern -> ["Constant", "Intermittent", "Comes and goes in waves", "Worse at night/morning", "Other"]
- Free-text/Administrative questions (Name, Age, Height, Weight, Contact) -> set `quick_options` to null.

CHECKPOINTS:
- Sequence Check: Are Gender, Height, Weight, and Contact filled? If not, ask for the next missing demographic field BEFORE asking for the Chief Complaint.
- Emergency Check: Are any life-threatening symptoms present?
- Pacing Check: Is `next_question` strictly 1 single concise question?

REVIEW:
- Ensure existing filled demographic slots are preserved and target the next unpopulated demographic field in sequence.
"""


def extract_slots_from_turn(
    user_message: str,
    current_state: IntakeSessionState
) -> ExtractionResult:
    """
    PURPOSE: Calls OpenAI API with structured output parsing to extract slots and quick options.
    """
    client = get_openai_client()

    demo_clean = current_state.demographics.model_dump(exclude_none=True)
    slots_clean = current_state.clinical_slots.model_dump(exclude_none=True)

    user_prompt = (
        f"Demo:{demo_clean}\n"
        f"Slots:{slots_clean}\n"
        f"Step:{current_state.current_step}\n"
        f"Msg:\"{user_message}\""
    )

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": EXTRACTOR_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        response_format=ExtractionResult,
        temperature=0.1,
    )

    return response.choices[0].message.parsed