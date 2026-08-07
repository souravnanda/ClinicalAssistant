"""
FILE: backend/app/services/intake/__init__.py
PURPOSE: Package initialization for the clinical intake service module.
WHY WE NEED IT: Exposes schemas, slot extraction functions, and state engine processing functions for clean module imports across the backend application.
"""

from app.services.intake.schemas import (
    PatientDemographics,
    ClinicalSlots,
    IntakeSessionState,
    ExtractionResult,
)
from app.services.intake.extractor import extract_slots_from_turn
from app.services.intake.state import (
    process_user_turn,
    merge_slots,
    calculate_current_step,
)

__all__ = [
    "PatientDemographics",
    "ClinicalSlots",
    "IntakeSessionState",
    "ExtractionResult",
    "extract_slots_from_turn",
    "process_user_turn",
    "merge_slots",
    "calculate_current_step",
]