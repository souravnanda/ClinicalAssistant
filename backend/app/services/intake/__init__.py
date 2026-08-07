# ==============================================================================
# FILE: backend/app/services/intake/__init__.py
# PURPOSE: Package initialization file for the Clinical Intake service module.
# SCOPE: Marks the directory as a Python package and exposes key classes for import.
# ==============================================================================

from app.services.intake.schemas import (
    PatientDemographics,
    ClinicalSlots,
    ExtractionResult,
    IntakeSessionState,
)
from app.services.intake.extractor import extract_slots_from_turn
from app.services.intake.state import IntakeStateManager

__all__ = [
    "PatientDemographics",
    "ClinicalSlots",
    "ExtractionResult",
    "IntakeSessionState",
    "extract_slots_from_turn",
    "IntakeStateManager",
]