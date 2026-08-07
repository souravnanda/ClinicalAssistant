"""
FILE: backend/app/api/v2/intake.py
PURPOSE: FastAPI router for the clinical intake step endpoint.
WHY WE NEED IT: Exposes the primary REST API endpoint (POST /api/v2/intake/step)
that receives patient messages from the React frontend, processes them through
the slot-filling extraction engine and state machine, and returns structured updates.
"""

from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field

from app.services.intake.schemas import IntakeSessionState
from app.services.intake.state import process_user_turn
from app.core.limiter import limiter

# Create APIRouter instance for intake endpoints
router = APIRouter(prefix="/api/v2/intake", tags=["Intake"])


class IntakeStepRequest(BaseModel):
    """
    PURPOSE: Pydantic request model for single-turn patient intake processing.
    WHY WE NEED IT: Validates the incoming JSON payload from the frontend.
    Allows session_state to be optional (None) on turn 1 to prevent 422 errors.
    """
    user_message: str = Field(
        ...,
        description="The natural language message entered by the patient."
    )
    session_state: Optional[IntakeSessionState] = Field(
        default=None,
        description="Current persistent intake state; set to None on initial conversation turn."
    )


@router.post("/step")
@limiter.limit("20/minute")
async def process_intake_step(request_data: IntakeStepRequest, request: Request):
    """
    PURPOSE: Processes a single turn of the patient intake conversation.
    
    ARGS:
        request_data (IntakeStepRequest): Validated request payload containing user_message and session_state.
        request (Request): FastAPI Request object required by slowapi rate limiter.
        
    RETURNS:
        dict: Standardized API response containing:
            - status (str): Execution status ("success").
            - session_state (dict): Updated IntakeSessionState serialized to dictionary.
            - next_question (str): Targeted follow-up question.
            - quick_options (list): List of quick-reply suggestion chips.
            - active_step (int): Active stage index (1 to 5).
            - is_emergency (bool): Red-flag triage alert flag.
            - summary (str|None): Generated Doctor Brief markdown string upon session completion.
            
    RAISES:
        HTTPException: Returns HTTP 500 status code if processing fails.
    """
    try:
        # Initialize a fresh state container if session_state is None on turn 1
        current_state = request_data.session_state or IntakeSessionState()

        # Execute single-turn processing via state machine engine
        updated_session, next_question, quick_options = process_user_turn(
            user_message=request_data.user_message,
            current_state=current_state
        )

        return {
            "status": "success",
            "session_state": updated_session.model_dump(),
            "next_question": next_question,
            "quick_options": quick_options,
            "active_step": updated_session.current_step,
            "is_emergency": updated_session.is_emergency,
            "summary": updated_session.summary_brief if updated_session.is_completed else None
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the intake step: {str(e)}"
        )