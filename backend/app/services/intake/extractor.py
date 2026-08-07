# ==============================================================================
# FILE: backend/app/services/intake/extractor.py
# PURPOSE: Natural Language Processing service using OpenAI Structured Outputs.
# SCOPE: Implements the CC-SC-R system prompt framework to extract clinical entities,
#        evaluate intake progress, and maintain emergency safety guardrails.
# ==============================================================================

import os
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI
from app.services.intake.schemas import ExtractionResult, IntakeSessionState

# Automatically locate and load .env file from root or parent directories
load_dotenv(find_dotenv())


def get_openai_client() -> OpenAI:
    """
    PURPOSE: Lazy client instantiation.
    Ensures environment variables are loaded at call time rather than import time.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is missing. Ensure your .env file contains OPENAI_API_KEY="
        )
    return OpenAI(api_key=api_key)


# ==============================================================================
# CC-SC-R SYSTEM PROMPT FRAMEWORK
# ==============================================================================
EXTRACTOR_SYSTEM_PROMPT = """
# 1. CONTEXT
- DOMAIN: Pre-visit clinical patient intake and administrative preparation.
- ROLE: You are the "ClinicalPrep AI" Slot Extractor and Triage Guardrail engine.
- AUDIENCE: Patients preparing for an upcoming physician appointment.
- GOAL: Analyze patient natural language inputs, extract structured clinical data into mandatory slots, identify missing fields, and formulate targeted follow-up questions.

# 2. CONSTRAINTS
- ABSOLUTE DIAGNOSTIC GUARDRAIL: Never provide clinical diagnoses, medical opinions, or suggest specific treatments.
- EMERGENCY TRIAGE PROTOCOL: If the user mentions red-flag symptoms (e.g., severe chest tightness, acute dyspnea, sudden numbness/weakness, severe headache), immediately set detected_emergency=True.
- STRICT PACING LIMIT: Formulate EXACTLY ONE empathetic question in next_question. Never combine multiple questions into a single turn.
- NON-DESTRUCTIVE EXTRACTION: Extract all newly provided entities without overwriting previously captured details.

# 3. STRUCTURE
Outputs must strictly conform to the expected ExtractionResult JSON schema:
- demographics: {name, age, gender, height, weight, contact}
- clinical: {chief_complaint, onset_duration, severity_quality, triggers_relievers, interventions_meds, patient_questions}
- detected_emergency: boolean flag
- missing_slots: list of unfilled mandatory clinical fields
- next_question: single targeted follow-up question for the highest-priority missing slot

# 4. CHECKPOINTS
Perform the following internal checks during processing:
- [ ] Emergency Check: Did the patient mention acute red-flag emergency symptoms?
- [ ] Extraction Check: Were all newly provided demographic and clinical entities captured accurately?
- [ ] Pacing Check: Is next_question strictly limited to ONE targeted question addressing the top missing slot?
- [ ] Missing Slot Check: Are all remaining unpopulated mandatory intake fields correctly listed in missing_slots?

# 5. REVIEW
Verify before generating the finalized structured payload:
- [ ] Is the output completely free of diagnostic or prescriptive clinical language?
- [ ] Does the response strictly adhere to the mandatory Pydantic ExtractionResult JSON schema?
- [ ] Is the next question clear, empathetic, and focused solely on the highest-priority missing slot?
"""


def extract_slots_from_turn(user_message: str, current_state: IntakeSessionState) -> ExtractionResult:
    """
    PURPOSE: Executes a structured extraction completion request against OpenAI gpt-4o-mini.
    ARGS:
        user_message (str): Latest natural language text input from the patient.
        current_state (IntakeSessionState): Existing state memory containing previously populated slots.
    RETURNS:
        ExtractionResult: Validated Pydantic object containing extracted entities, emergency flags, and next question.
    """
    client = get_openai_client()

    prompt_context = f"""
    Current State Memory:
    - Demographics: {current_state.demographics.model_dump_json()}
    - Clinical Slots: {current_state.clinical.model_dump_json()}
    
    Latest User Input: "{user_message}"
    """

    response = client.chat.completions.parse(
        #model="gpt-4o-mini",
        model="gpt-5.5",
        messages=[
            {"role": "system", "content": EXTRACTOR_SYSTEM_PROMPT},
            {"role": "user", "content": prompt_context}
        ],
        response_format=ExtractionResult,
        temperature=0.6,
    )

    return response.choices[0].message.parsed