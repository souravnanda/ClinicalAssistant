# backend/app/api/v2/intake.py
"""
Clinical Intake API Router (v2).

Purpose:
    Exposes REST HTTP endpoints for processing multi-turn patient intake conversations 
    and generating downloadable clinical record PDF documents.
"""

from fastapi import APIRouter, Request, HTTPException, Response
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.services.intake.schemas import IntakeStepRequest, IntakeStepResponse
from app.services.intake.extractor import extract_clinical_slots
from app.services.intake.state import update_session_state
from app.services.pdf.pdf_generator import generate_clinical_record_pdf

router = APIRouter(prefix="/api/v2/intake", tags=["Clinical Intake Engine"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/step", response_model=IntakeStepResponse)
@limiter.limit("20/minute")
async def process_intake_step(request: Request, payload: IntakeStepRequest) -> IntakeStepResponse:
    """Processes a single turn of the patient intake conversation."""
    try:
        user_message = payload.user_message
        current_state = payload.session_state

        extracted_result = await extract_clinical_slots(user_message=user_message, current_state=current_state)
        updated_state = update_session_state(
            current_state=current_state,
            extracted_result=extracted_result,
            user_message=user_message,
        )

        return updated_state

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intake step execution error: {str(e)}")


@router.post("/pdf")
@limiter.limit("10/minute")
async def export_intake_pdf(request: Request, payload: IntakeStepRequest):
    """
    Generates and downloads a formatted Clinical Pre-Visit Record PDF.
    """
    try:
        session_state = payload.session_state or {}
        pdf_bytes = generate_clinical_record_pdf(session_state)

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=ClinicalPrep_Patient_Summary.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation error: {str(e)}")