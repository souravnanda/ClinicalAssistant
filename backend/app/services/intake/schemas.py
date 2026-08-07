"""
FILE: backend/app/services/intake/schemas.py
PURPOSE: Defines Pydantic v2 schemas for patient demographics, clinical slots, intake session state, and LLM extraction outputs.
"""

import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class PatientDemographics(BaseModel):
    """PURPOSE: Stores non-clinical patient identification fields gathered during Step 1."""
    name: Optional[str] = Field(default=None, description="Patient's full preferred name.")
    age: Optional[int] = Field(default=None, description="Patient's age in years.")
    gender: Optional[str] = Field(default=None, description="Patient's gender identity.")
    height: Optional[str] = Field(default=None, description="Patient's height measurement.")
    weight: Optional[str] = Field(default=None, description="Patient's body weight measurement.")
    contact: Optional[str] = Field(default=None, description="Patient's contact information.")


class ClinicalSlots(BaseModel):
    """PURPOSE: Stores structured clinical data gathered using the medical intake framework."""
    chief_complaint: Optional[str] = Field(default=None, description="Primary medical symptom or reason for visit.")
    onset_duration: Optional[str] = Field(default=None, description="When symptoms started and how long they last.")
    severity: Optional[str] = Field(default=None, description="Pain or discomfort intensity rating.")
    pattern: Optional[str] = Field(default=None, description="Symptom behavior pattern over time.")
    triggers_relievers: Optional[str] = Field(default=None, description="Factors worsening or alleviating symptoms.")
    current_medications: Optional[str] = Field(default=None, description="Prescription or OTC medications taken.")
    home_remedies: Optional[str] = Field(default=None, description="Home care treatments attempted.")
    doctor_questions: List[str] = Field(default_factory=list, description="Questions patient wants to ask physician.")


class IntakeSessionState(BaseModel):
    """PURPOSE: Persistent state container tracking conversation memory, progress, and safety flags."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique session identifier.")
    current_step: int = Field(default=1, description="Active step index (1 to 5).")
    is_completed: bool = Field(default=False, description="True when intake workflow is complete.")
    is_emergency: bool = Field(default=False, description="True when acute emergency symptoms are detected.")
    summary_brief: Optional[str] = Field(default=None, description="Generated Doctor Brief markdown text.")
    demographics: PatientDemographics = Field(default_factory=PatientDemographics)
    clinical_slots: ClinicalSlots = Field(default_factory=ClinicalSlots)
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)


class ExtractionResult(BaseModel):
    """PURPOSE: Enforces structured JSON output schema on OpenAI for single-turn slot extraction."""
    demographics: PatientDemographics = Field(default_factory=PatientDemographics)
    clinical_slots: ClinicalSlots = Field(default_factory=ClinicalSlots)
    is_emergency: bool = Field(default=False, description="True if input contains acute red-flag symptoms.")
    missing_fields: List[str] = Field(default_factory=list, description="List of unpopulated mandatory fields.")
    next_question: str = Field(description="Targeted follow-up question asking for highest priority missing slot.")
    quick_options: Optional[List[str]] = Field(default=None, description="Quick-reply suggestion chips for frontend.")