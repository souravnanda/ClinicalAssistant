# ==============================================================================
# FILE: backend/tests/test_intake.py
# PURPOSE: Integration tests for POST /api/v2/intake/step endpoint.
# SCOPE: Validates API request handling, state updates, emergency triage triggers,
#        and error handling using mock extractor responses.
# ==============================================================================

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.services.intake.schemas import ExtractionResult, PatientDemographics, ClinicalSlots

client = TestClient(app)


@pytest.fixture
def initial_payload():
    """Provides a default initial request payload for tests."""
    return {
        "user_message": "Hello, my name is Sarah and my lower back has been throbbing since Tuesday.",
        "session_state": {
            "session_id": "test_session_123",
            "current_step": 1,
            "demographics": {"name": None, "age": None, "gender": None, "height": None, "weight": None, "contact": None},
            "clinical": {
                "chief_complaint": None,
                "onset_duration": None,
                "severity_quality": None,
                "triggers_relievers": None,
                "interventions_meds": None,
                "patient_questions": []
            },
            "is_complete": False,
            "is_emergency": False
        }
    }


@patch("app.api.v2.intake.extract_slots_from_turn")
def test_intake_step_success(mock_extract, initial_payload):
    """Tests successful slot extraction and state progression on turn 1."""
    # Mock LLM Extraction Result
    mock_extract.return_value = ExtractionResult(
        demographics=PatientDemographics(name="Sarah"),
        clinical=ClinicalSlots(
            chief_complaint="Throbbing lower back pain",
            onset_duration="Since Tuesday"
        ),
        detected_emergency=False,
        missing_slots=["age", "severity_quality", "interventions_meds", "patient_questions"],
        next_question="Hi Sarah, how old are you?"
    )

    response = client.post("/api/v2/intake/step", json=initial_payload)

    assert response.status_code == 200
    data = response.json()
    
    # Assert state updates
    assert data["updated_state"]["demographics"]["name"] == "Sarah"
    assert data["updated_state"]["clinical"]["chief_complaint"] == "Throbbing lower back pain"
    assert data["updated_state"]["clinical"]["onset_duration"] == "Since Tuesday"
    assert data["next_question"] == "Hi Sarah, how old are you?"
    assert data["is_emergency"] is False
    assert data["is_complete"] is False


@patch("app.api.v2.intake.extract_slots_from_turn")
def test_intake_step_emergency_trigger(mock_extract, initial_payload):
    """Tests immediate emergency state shift when red-flag symptoms are detected."""
    initial_payload["user_message"] = "I have sudden severe chest tightness and crushing pain."
    
    # Mock LLM Emergency Detection
    mock_extract.return_value = ExtractionResult(
        demographics=PatientDemographics(),
        clinical=ClinicalSlots(chief_complaint="Severe chest pain"),
        detected_emergency=True,
        missing_slots=["severity_quality"],
        next_question="Please call 911 or seek immediate medical attention."
    )

    response = client.post("/api/v2/intake/step", json=initial_payload)

    assert response.status_code == 200
    data = response.json()
    
    # Assert emergency flags
    assert data["is_emergency"] is True
    assert data["updated_state"]["is_emergency"] is True


def test_intake_step_invalid_payload():
    """Tests API error handling when required fields are missing in JSON request."""
    invalid_payload = {"user_message": ""}  # Missing required session_state

    response = client.post("/api/v2/intake/step", json=invalid_payload)
    
    assert response.status_code == 422  # Unprocessable Entity (Validation Error)