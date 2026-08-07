#**
#* FILE: backend/app/services/intake/schemas.py
#* PURPOSE: Defines Pydantic v2 data validation models for patient demographics, clinical slots, session state, and LLM structured extraction outputs.
#* WHY WE NEED IT: Enforces strict type-safety, JSON schema compliance for OpenAI structured outputs, default values to prevent validation failures, and precise slot tracking across the 5-step intake workflow.
#*/

import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class PatientDemographics(BaseModel):
    """
    PURPOSE: Holds non-clinical administrative and demographic information collected during Step 1 of the intake interview.
    """
    name: Optional[str] = Field(
        default=None, 
        description="Patient's full preferred name."
    )
    age: Optional[int] = Field(
        default=None, 
        description="Patient's age in numerical years."
    )
    gender: Optional[str] = Field(
        default=None, 
        description="Patient's gender identity (e.g., Male, Female, Non-Binary)."
    )
    height: Optional[str] = Field(
        default=None, 
        description="Patient's height measurement (e.g., 5'9\", 175 cm)."
    )
    weight: Optional[str] = Field(
        default=None, 
        description="Patient's body weight measurement (e.g., 160 lbs, 72 kg)."
    )
    contact: Optional[str] = Field(
        default=None, 
        description="Patient's contact phone number or email address."
    )


class ClinicalSlots(BaseModel):
    """
    PURPOSE: Encapsulates structured clinical data gathered using the OPQRST medical intake framework across conversation turns.
    """
    chief_complaint: Optional[str] = Field(
        default=None, 
        description="Primary medical symptom or reason for the upcoming doctor visit."
    )
    onset_duration: Optional[str] = Field(
        default=None, 
        description="Timestamp or timeframe describing when symptoms started and how long they last."
    )
    severity: Optional[str] = Field(
        default=None, 
        description="Pain or discomfort intensity rating (e.g., 7/10, Moderate)."
    )
    pattern: Optional[str] = Field(
        default=None, 
        description="Behavior pattern of the symptom over time (e.g., Constant, Intermittent, Comes and goes in waves)."
    )
    triggers_relievers: Optional[str] = Field(
        default=None, 
        description="Activities, foods, postures, or interventions that worsen or alleviate symptoms."
    )
    current_medications: Optional[str] = Field(
        default=None, 
        description="Prescription medications, OTC drugs, or supplements taken for this condition."
    )
    home_remedies: Optional[str] = Field(
        default=None, 
        description="Non-pharmacological home care treatments attempted by the patient."
    )
    doctor_questions: List[str] = Field(
        default_factory=list, 
        description="List of specific questions or goals the patient wishes to discuss with their physician."
    )


class IntakeSessionState(BaseModel):
    """
    PURPOSE: Maintains the persistent state container for an active intake session, tracking conversation progress, history, and accumulated memory.
    """
    session_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), 
        description="Unique UUID string identifying the intake session."
    )
    current_step: int = Field(
        default=1, 
        description="Active step index (1 to 5) indicating progress through the intake workflow."
    )
    is_completed: bool = Field(
        default=False, 
        description="Boolean flag set to True when all mandatory slots are filled and the Doctor Brief is generated."
    )
    is_emergency: bool = Field(
        default=False, 
        description="Safety flag set to True when red-flag acute emergency symptoms are detected."
    )
    summary_brief: Optional[str] = Field(
        default=None, 
        description="Final markdown summary string of the generated Doctor Brief."
    )
    demographics: PatientDemographics = Field(
        default_factory=PatientDemographics, 
        description="Nested PatientDemographics model holding accumulated demographic information."
    )
    clinical_slots: ClinicalSlots = Field(
        default_factory=ClinicalSlots, 
        description="Nested ClinicalSlots model holding accumulated clinical information."
    )
    conversation_history: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Chronological log of message turns in the session (role, content, timestamp)."
    )


class ExtractionResult(BaseModel):
    """
    PURPOSE: Enforces structured JSON output schema on OpenAI responses during single-turn slot extraction.
    """
    demographics: PatientDemographics = Field(
        default_factory=PatientDemographics, 
        description="Demographic attributes extracted or updated from the user's latest turn."
    )
    clinical_slots: ClinicalSlots = Field(
        default_factory=ClinicalSlots, 
        description="Clinical slot attributes extracted or updated from the user's latest turn."
    )
    is_emergency: bool = Field(
        default=False, 
        description="True if the user input contains acute or life-threatening red-flag symptoms requiring immediate emergency care."
    )
    missing_fields: List[str] = Field(
        default_factory=list, 
        description="List of mandatory intake fields that remain unpopulated."
    )
    next_question: str = Field(
        description="One targeted, empathetic question asking for the highest-priority missing intake slot."
    )
    quick_options: Optional[List[str]] = Field(
        default=None, 
        description="Contextual quick-reply suggestion chips for the frontend UI."
    )