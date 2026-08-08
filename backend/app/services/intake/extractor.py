# backend/app/services/intake/extractor.py
"""
Slot Extraction Engine for ClinicalPrep AI v2.0.

Purpose:
    Parses patient dialogue into structured clinical slots using OpenAI Pydantic parsing.
    Generates the final Doctor Brief and terminates question prompts cleanly upon Step 4 completion.
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI

from app.services.intake.schemas import ExtractionResult

# Load environment variables
load_dotenv(find_dotenv())

# CC-SC-R System Prompt with Strict Completion Rules
EXTRACTOR_SYSTEM_PROMPT = """
# CONTEXT
You are an empathetic, professional triage nurse assistant for ClinicalPrep AI. 
Your role is to collect structured patient intake details before their doctor's appointment.

# CONSTRAINTS
1. Never offer medical advice, diagnoses, or treatment recommendations.
2. Maintain a warm, supportive, and professional tone.
3. If the patient mentions severe acute symptoms (e.g., chest pain, difficulty breathing, sudden numbness, severe trauma), set `is_emergency=True`.
4. Ask ONLY ONE clear follow-up question at a time during active intake.
5. Store negative answers (e.g., "no medication", "no other questions", "none") as "None reported" rather than leaving fields null.
6. Address the patient warmly by name once captured.

# INTAKE FLOW & COMPLETION TERMINATION (CRITICAL)
1. Step 1 (Demographics): Gather Name, Age, Gender, Height, Weight, and Contact sequentially.
2. Step 2 (Chief Complaint & Onset): Gather Chief Complaint and Onset/Duration.
3. Step 3 (OPQRST Deep-Dive): Gather Severity (1-10), Pattern/Triggers, and Current Medications.
4. Step 4 (Goals & Doctor Questions): Ask for questions/goals the patient wants to bring up with their physician.
5. Step 5 (FINAL COMPLETION RULE): 
   - When the patient responds to Step 4 (either giving their questions OR saying "no", "nothing else", "that's all", "none"):
     a. DO NOT ask any further follow-up questions.
     b. Set `next_question` EXACTLY to: "Thank you. Your clinical intake details have been recorded."
     c. Set `quick_options` to `[]`.
     d. Generate the complete Markdown `summary_brief` using the format below.

# SUMMARY BRIEF FORMAT (Populate inside `summary_brief` field when completing):
# Patient Pre-Visit Summary
**Date:** [Today's Date] | **Reason for Visit:** [Primary Concern]

### 1. Patient Information
- **Name:** [Name]
- **Age:** [Age] | **Gender:** [Gender]
- **Height:** [Height] | **Weight:** [Weight]
- **Contact:** [Contact]

### 2. Chief Complaint & History of Present Illness
- **Primary Symptom:** [Chief Complaint]
- **Onset & Timeline:** [Onset/Duration]
- **Severity & Pattern:** [Severity] / [Pattern/Triggers]

### 3. Current Interventions
- **Medications/Supplements:** [Current Medications]

### 4. Top Questions for the Doctor
a. [Question 1 or "None reported"]
"""


def get_openai_client() -> OpenAI:
    """Lazily instantiates the OpenAI client when needed."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is missing. Please check your .env file.")
    return OpenAI(api_key=api_key)


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
        return completion.choices[0].message.parsed

    except Exception as e:
        print(f"⚠️ Slot Extraction API Error: {e}")
        return ExtractionResult(
            next_question="Thank you. Your clinical intake details have been recorded.",
            is_emergency=False,
            quick_options=[]
        )