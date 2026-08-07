# ==============================================================================
# FILE: backend/app/api/v2/intake.py
# PURPOSE: FastAPI router exposing the clinical intake step processing endpoint.
# SCOPE: Receives user HTTP requests, invokes the slot extractor service, updates session state,
#        and returns structured payloads to the client UI.
# ==============================================================================

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field
from app.core.limiter import limiter
from app.services.intake.schemas import IntakeSessionState
from app.services.intake.extractor import extract_slots_from_turn
from app.services.intake.state import IntakeStateManager

router = APIRouter(prefix="/api/v2/intake", tags=["Clinical Intake"])


class IntakeStepRequest(BaseModel):
    """Payload sent by the frontend on each patient chat turn."""
    user_message: str = Field(..., min_length=1, description="Latest text response from the patient")
    session_state: IntakeSessionState = Field(..., description="Active session state object")


class IntakeStepResponse(BaseModel):
    """Response returned to the frontend after slot extraction and state updates."""
    updated_state: IntakeSessionState
    next_question: str
    is_emergency: bool
    is_complete: bool


@router.post(
    "/step",
    response_model=IntakeStepResponse,
    status_code=status.HTTP_200_OK,
    summary="Process a single turn of clinical intake",
    description="Extracts slots from patient text, merges them into session state, and calculates the next targeted question."
)
@limiter.limit("20/minute")
def process_intake_step(request: Request, body: IntakeStepRequest) -> IntakeStepResponse:
    """Processes incoming patient input through the slot extractor and state machine."""
    try:
        # 1. Extract clinical entities & slots from latest user message
        extraction_result = extract_slots_from_turn(
            user_message=body.user_message,
            current_state=body.session_state
        )

        # 2. Merge extracted slots into session state memory & calculate step progress
        updated_state = IntakeStateManager.update_session_state(
            state=body.session_state,
            extraction=extraction_result
        )

        # 3. Return updated state and conversation payload
        return IntakeStepResponse(
            updated_state=updated_state,
            next_question=extraction_result.next_question,
            is_emergency=updated_state.is_emergency,
            is_complete=updated_state.is_complete
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing intake turn: {str(e)}"
        )