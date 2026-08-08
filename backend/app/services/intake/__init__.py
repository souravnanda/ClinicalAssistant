# backend/app/services/intake/__init__.py
"""
Clinical Intake Service Package Initialization.

Purpose:
    Exposes core clinical intake schemas and session state machine functions 
    for structured slot extraction and multi-turn interview progression.
"""

from app.services.intake.schemas import (
    PatientDemographics,
    ClinicalSlots,
    ExtractionResult,
    IntakeSessionState,
    IntakeStepRequest,
    IntakeStepResponse,
)
from app.services.intake.state import (
    merge_slots,
    calculate_current_step,
    update_session_state,
)

__all__ = [
    "PatientDemographics",
    "ClinicalSlots",
    "ExtractionResult",
    "IntakeSessionState",
    "IntakeStepRequest",
    "IntakeStepResponse",
    "merge_slots",
    "calculate_current_step",
    "update_session_state",
]