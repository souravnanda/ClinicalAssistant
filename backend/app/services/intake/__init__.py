# backend/app/services/intake/__init__.py
"""
Clinical Intake Service Package Initialization.

Purpose:
    Exposes core clinical intake schemas, extraction utilities, and session 
    state machine functions for structured slot extraction and multi-turn interview progression.
"""

from app.services.intake.schemas import (
    DemographicsSlots,
    PatientDemographics,
    ClinicalSlots,
    ExtractionResult,
    IntakeSessionState,
    IntakeStepRequest,
    IntakeStepResponse,
)
from app.services.intake.extractor import (
    extract_clinical_slots,
)
from app.services.intake.state import (
    merge_slots,
    calculate_current_step,
    update_session_state,
    generate_fallback_summary,
)

__all__ = [
    "DemographicsSlots",
    "PatientDemographics",
    "ClinicalSlots",
    "ExtractionResult",
    "IntakeSessionState",
    "IntakeStepRequest",
    "IntakeStepResponse",
    "extract_clinical_slots",
    "merge_slots",
    "calculate_current_step",
    "update_session_state",
    "generate_fallback_summary",
]