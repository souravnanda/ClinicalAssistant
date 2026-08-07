# ==============================================================================
# FILE: backend/app/services/intake/schemas.py
# PURPOSE: Defines Pydantic v2 data models for clinical slot extraction and intake state tracking.
# SCOPE: Serves as the single source of truth for structured data validation, forced LLM JSON outputs,
#        and transient in-memory session state representation.
# ==============================================================================

from pydantic import BaseModel, Field
from typing import Optional, List


class PatientDemographics(BaseModel):
    """
    PURPOSE: Captures fundamental patient demographic data during Step 1 of the intake interview.
    ROLE: Ensures standard identification parameters are populated before clinical deep-dive.
    """
    name: Optional[str] = Field(None, description="Patient's full legal name")
    age: Optional[int] = Field(None, description="Patient's age in years")
    gender: Optional[str] = Field(None, description="Gender identity (e.g., Male, Female, Non-binary)")
    height: Optional[str] = Field(None, description="Patient height measurement (e.g., '5 ft 10 in' or '178 cm')")
    weight: Optional[str] = Field(None, description="Patient weight measurement (e.g., '70 kg' or '154 lbs')")
    contact: Optional[str] = Field(None, description="Phone number or primary email address for clinic records")


class ClinicalSlots(BaseModel):
    """
    PURPOSE: Holds extracted medical symptoms structured around OPQRST guidelines.
    ROLE: Tracks collected clinical details across turns to ensure no required field is omitted.
    """
    chief_complaint: Optional[str] = Field(None, description="Primary medical concern or visit reason")
    onset_duration: Optional[str] = Field(None, description="Symptom timeline (e.g., '3 days ago', 'Yesterday morning')")
    severity_quality: Optional[str] = Field(None, description="Pain rating (1-10) and character (e.g., '7/10 constant throbbing')")
    triggers_relievers: Optional[str] = Field(None, description="Aggravating or alleviating factors (e.g., 'worse with movement, better with rest')")
    interventions_meds: Optional[str] = Field(None, description="Current medications, remedies, or OTC drugs taken for relief")
    patient_questions: List[str] = Field(default_factory=list, description="Top 1 to 3 key questions or goals for the physician visit")


class ExtractionResult(BaseModel):
    """
    PURPOSE: Enforces 100% strict JSON schema compliance on LLM output via OpenAI Structured Outputs.
    ROLE: Evaluates user conversation per turn to extract demographic and clinical slots, detect red-flags,
          and formulate the single next targeted follow-up question.
    """
    demographics: PatientDemographics
    clinical: ClinicalSlots
    detected_emergency: bool = Field(False, description="Flag indicating emergency red-flag symptoms (e.g., chest pain, severe dyspnea)")
    missing_slots: List[str] = Field(..., description="List of unpopulated mandatory clinical intake fields")
    next_question: str = Field(..., description="1 empathetic, targeted follow-up question addressing the highest-priority missing slot")


class IntakeSessionState(BaseModel):
    """
    PURPOSE: Represents the transient in-memory state object for an ongoing patient intake session.
    ROLE: Retains state across multiple HTTP requests before saving finalized data to permanent storage.
    """
    session_id: str = Field(..., description="Unique UUID tracking the active chat intake session")
    current_step: int = Field(1, ge=1, le=5, description="Active stage in the 5-step intake pipeline (1 to 5)")
    demographics: PatientDemographics = Field(default_factory=PatientDemographics)
    clinical: ClinicalSlots = Field(default_factory=ClinicalSlots)
    is_complete: bool = Field(False, description="Set to True when all mandatory clinical slots are populated")
    is_emergency: bool = Field(False, description="Set to True if red-flag triage triggers emergency redirection")