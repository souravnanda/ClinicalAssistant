# ==============================================================================
# FILE: backend/tests/test_intake.py
# PURPOSE: Integration tests for POST /api/v2/intake/step endpoint.
# SCOPE: Validates API request handling, state accumulation across turns,
#        emergency triage triggers, step progression, and error handling
#        using mock extractor responses (no live OpenAI calls).
# ==============================================================================

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.services.intake.schemas import ExtractionResult, PatientDemographics, ClinicalSlots

client = TestClient(app)

# Patch target: the router imports extract_clinical_slots directly into its own
# module namespace, so it must be patched there (not at its definition site) for
# the mock to actually intercept the call.
EXTRACTOR_PATCH_TARGET = "app.api.v2.intake.extract_clinical_slots"


@pytest.fixture
def empty_session_state():
    """A freshly-started session with nothing captured yet."""
    return {
        "session_id": "test_session_123",
        "current_step": 1,
        "is_completed": False,
        "is_emergency": False,
        "summary_brief": None,
        "demographics": {
            "name": None, "age": None, "gender": None,
            "height": None, "weight": None, "contact": None,
        },
        "clinical_slots": {
            "chief_complaint": None, "onset_duration": None, "quality": None,
            "region_radiation": None, "severity": None, "pattern_triggers": None,
            "current_medications": None, "allergies": None, "patient_goals": None,
        },
        "last_question_asked": None,
        "conversation_history": [],
    }


@pytest.fixture
def initial_payload(empty_session_state):
    """Default first-turn request payload."""
    return {
        "user_message": "Hello, my name is Sarah and my lower back has been throbbing since Tuesday.",
        "session_state": empty_session_state,
    }


# ------------------------------------------------------------------------------
# Basic slot extraction & state accumulation
# ------------------------------------------------------------------------------

@patch(EXTRACTOR_PATCH_TARGET)
def test_intake_step_success(mock_extract, initial_payload):
    """Tests successful slot extraction and state progression on turn 1."""
    mock_extract.return_value = ExtractionResult(
        demographics=PatientDemographics(name="Sarah"),
        clinical_slots=ClinicalSlots(
            chief_complaint="Throbbing lower back pain",
            onset_duration="Since Tuesday",
        ),
        is_emergency=False,
        next_question="Hi Sarah, how old are you?",
        quick_options=[],
    )

    response = client.post("/api/v2/intake/step", json=initial_payload)

    assert response.status_code == 200
    data = response.json()

    assert data["updated_state"]["demographics"]["name"] == "Sarah"
    assert data["updated_state"]["clinical_slots"]["chief_complaint"] == "Throbbing lower back pain"
    assert data["updated_state"]["clinical_slots"]["onset_duration"] == "Since Tuesday"
    assert data["next_question"] == "Hi Sarah, how old are you?"
    assert data["is_emergency"] is False
    assert data["is_completed"] is False


@patch(EXTRACTOR_PATCH_TARGET)
def test_slots_persist_non_destructively_across_turns(mock_extract, empty_session_state):
    """
    Regression test for the original repeat-question bug: fields captured in an
    earlier turn must survive into later turns even when the newest extraction
    only fills a different slot. merge_slots() must never null out prior data.
    """
    # Turn 1: capture chief complaint
    mock_extract.return_value = ExtractionResult(
        clinical_slots=ClinicalSlots(chief_complaint="Menstrual/period-related problem"),
        next_question="Can you describe the specific issue you're experiencing?",
        quick_options=[],
    )
    r1 = client.post("/api/v2/intake/step", json={
        "user_message": "periods problem",
        "session_state": empty_session_state,
    })
    state_after_turn1 = r1.json()["updated_state"]
    assert state_after_turn1["clinical_slots"]["chief_complaint"] == "Menstrual/period-related problem"

    # Turn 2: extraction only returns region_radiation this turn (nothing else) —
    # chief_complaint must still be present afterward, not wiped out.
    mock_extract.return_value = ExtractionResult(
        clinical_slots=ClinicalSlots(region_radiation="Abdomen"),
        next_question="Can you tell me more about when the abdominal pain started?",
        quick_options=[],
    )
    r2 = client.post("/api/v2/intake/step", json={
        "user_message": "pain in abdomen",
        "session_state": state_after_turn1,
    })
    state_after_turn2 = r2.json()["updated_state"]
    assert state_after_turn2["clinical_slots"]["chief_complaint"] == "Menstrual/period-related problem"
    assert state_after_turn2["clinical_slots"]["region_radiation"] == "Abdomen"

    # Turn 3: only onset_duration returned — both prior fields must still be intact.
    mock_extract.return_value = ExtractionResult(
        clinical_slots=ClinicalSlots(onset_duration="More than a month"),
        next_question="On a scale of 1 to 10, how severe is the pain?",
        quick_options=[],
    )
    r3 = client.post("/api/v2/intake/step", json={
        "user_message": "More than a month",
        "session_state": state_after_turn2,
    })
    state_after_turn3 = r3.json()["updated_state"]
    assert state_after_turn3["clinical_slots"]["chief_complaint"] == "Menstrual/period-related problem"
    assert state_after_turn3["clinical_slots"]["region_radiation"] == "Abdomen"
    assert state_after_turn3["clinical_slots"]["onset_duration"] == "More than a month"

    # The bot must NOT have regressed to re-asking the Phase 2 chief-complaint
    # question after three consecutive substantive answers.
    assert r3.json()["next_question"] != "What brings you in today?"
    assert "specifically brings you in" not in r3.json()["next_question"].lower()


@patch(EXTRACTOR_PATCH_TARGET)
def test_last_question_asked_is_tracked(mock_extract, empty_session_state):
    """
    The state machine must persist last_question_asked each turn so the extractor
    can be told what the patient's next reply is answering.
    """
    mock_extract.return_value = ExtractionResult(
        clinical_slots=ClinicalSlots(chief_complaint="Headache"),
        next_question="When did the headache start?",
        quick_options=["Today", "Yesterday"],
    )
    response = client.post("/api/v2/intake/step", json={
        "user_message": "I have a headache",
        "session_state": empty_session_state,
    })
    data = response.json()
    assert data["updated_state"]["last_question_asked"] == "When did the headache start?"
    # The assistant's question should also be appended to conversation_history.
    history = data["updated_state"]["conversation_history"]
    assert history[-1] == {"role": "assistant", "content": "When did the headache start?"}


@patch(EXTRACTOR_PATCH_TARGET)
def test_extractor_receives_last_question_and_history(mock_extract, empty_session_state):
    """
    Ensures the extractor is actually invoked with user_message and current_state
    (the router-level plumbing that carries state into the LLM call).
    """
    mock_extract.return_value = ExtractionResult(
        next_question="What brings you in today?",
        quick_options=[],
    )
    empty_session_state["last_question_asked"] = "What brings you in today?"
    empty_session_state["conversation_history"] = [
        {"role": "assistant", "content": "What brings you in today?"}
    ]

    client.post("/api/v2/intake/step", json={
        "user_message": "periods problem",
        "session_state": empty_session_state,
    })

    assert mock_extract.called
    _, kwargs = mock_extract.call_args
    assert kwargs["user_message"] == "periods problem"
    assert kwargs["current_state"]["last_question_asked"] == "What brings you in today?"


# ------------------------------------------------------------------------------
# Step progression
# ------------------------------------------------------------------------------

@patch(EXTRACTOR_PATCH_TARGET)
def test_step_progresses_without_requiring_demographics_first(mock_extract, empty_session_state):
    """
    Regression test: current_step must advance based on chief_complaint alone,
    even when demographics.name has never been captured (a valid flow where the
    bot asks the chief complaint before/instead of the patient's name).
    """
    mock_extract.return_value = ExtractionResult(
        clinical_slots=ClinicalSlots(chief_complaint="Lower back pain"),
        next_question="When did it start?",
        quick_options=[],
    )
    response = client.post("/api/v2/intake/step", json={
        "user_message": "my back hurts",
        "session_state": empty_session_state,
    })
    data = response.json()
    assert data["updated_state"]["demographics"]["name"] is None
    assert data["updated_state"]["current_step"] >= 2


@patch(EXTRACTOR_PATCH_TARGET)
def test_step_is_monotonic_and_never_regresses(mock_extract, empty_session_state):
    """current_step must never decrease turn-over-turn."""
    empty_session_state["current_step"] = 3
    empty_session_state["clinical_slots"]["chief_complaint"] = "Headache"
    empty_session_state["clinical_slots"]["onset_duration"] = "Yesterday"
    empty_session_state["clinical_slots"]["severity"] = "6"

    # A turn that only returns an unrelated/empty extraction shouldn't drop the step.
    mock_extract.return_value = ExtractionResult(
        next_question="Anything else about the pattern of the pain?",
        quick_options=[],
    )
    response = client.post("/api/v2/intake/step", json={
        "user_message": "not sure",
        "session_state": empty_session_state,
    })
    assert response.json()["updated_state"]["current_step"] >= 3


# ------------------------------------------------------------------------------
# Emergency / red-flag handling
# ------------------------------------------------------------------------------

@patch(EXTRACTOR_PATCH_TARGET)
def test_intake_step_emergency_trigger(mock_extract, initial_payload):
    """Tests immediate emergency state shift when red-flag symptoms are detected."""
    initial_payload["user_message"] = "I have sudden severe chest tightness and crushing pain."

    mock_extract.return_value = ExtractionResult(
        clinical_slots=ClinicalSlots(chief_complaint="Severe chest pain"),
        is_emergency=True,
        red_flag_reason="chest_pain",
        next_question="Please call 911 or seek immediate medical attention.",
        quick_options=[],
    )

    response = client.post("/api/v2/intake/step", json=initial_payload)

    assert response.status_code == 200
    data = response.json()
    assert data["is_emergency"] is True
    assert data["updated_state"]["is_emergency"] is True


@patch(EXTRACTOR_PATCH_TARGET)
def test_emergency_flag_persists_across_subsequent_turns(mock_extract, empty_session_state):
    """Once is_emergency is set, it must not silently clear on later turns."""
    mock_extract.return_value = ExtractionResult(
        clinical_slots=ClinicalSlots(chief_complaint="Chest pain"),
        is_emergency=True,
        next_question="Please seek immediate care.",
        quick_options=[],
    )
    r1 = client.post("/api/v2/intake/step", json={
        "user_message": "crushing chest pain",
        "session_state": empty_session_state,
    })
    state_after = r1.json()["updated_state"]
    assert state_after["is_emergency"] is True

    # Follow-up turn where the extractor no longer flags an emergency in isolation.
    mock_extract.return_value = ExtractionResult(
        next_question="Please seek immediate care.",
        is_emergency=False,
        quick_options=[],
    )
    r2 = client.post("/api/v2/intake/step", json={
        "user_message": "ok",
        "session_state": state_after,
    })
    assert r2.json()["updated_state"]["is_emergency"] is True


# ------------------------------------------------------------------------------
# Completion behavior
# ------------------------------------------------------------------------------

@patch(EXTRACTOR_PATCH_TARGET)
def test_intake_completes_and_locks_after_goals_captured(mock_extract, empty_session_state):
    """Once patient_goals is filled, session should complete and lock further turns."""
    empty_session_state["clinical_slots"]["chief_complaint"] = "Headache"
    empty_session_state["clinical_slots"]["onset_duration"] = "3 days ago"
    empty_session_state["clinical_slots"]["severity"] = "5"

    mock_extract.return_value = ExtractionResult(
        clinical_slots=ClinicalSlots(patient_goals="Wants to know if it's migraines"),
        next_question="Thanks, that's everything I need.",
        quick_options=[],
    )
    response = client.post("/api/v2/intake/step", json={
        "user_message": "I want to know if these are migraines",
        "session_state": empty_session_state,
    })
    data = response.json()
    assert data["is_completed"] is True
    assert data["updated_state"]["current_step"] == 5
    assert data["updated_state"]["summary_brief"]
    assert data["quick_options"] == []


@patch(EXTRACTOR_PATCH_TARGET)
def test_completed_session_short_circuits_without_reasking(mock_extract, empty_session_state):
    """
    A locked (is_completed=True) session should return the canned closing message
    immediately via update_session_state's early return, ignoring whatever the
    extractor returns for that turn.
    """
    empty_session_state["is_completed"] = True
    empty_session_state["summary_brief"] = "### Patient Pre-Visit Summary\n..."

    mock_extract.return_value = ExtractionResult(
        next_question="This should be ignored.",
        quick_options=["should", "be", "ignored"],
    )
    response = client.post("/api/v2/intake/step", json={
        "user_message": "one more thing",
        "session_state": empty_session_state,
    })
    data = response.json()
    assert data["is_completed"] is True
    assert data["next_question"] == "Thank you. Your clinical intake details have been recorded."
    assert data["quick_options"] == []


# ------------------------------------------------------------------------------
# Quick-reply chip fallback
# ------------------------------------------------------------------------------

@patch(EXTRACTOR_PATCH_TARGET)
def test_quick_options_passthrough_when_llm_provides_them(mock_extract, empty_session_state):
    mock_extract.return_value = ExtractionResult(
        next_question="How would you rate the severity from 1 to 10?",
        quick_options=["Mild (1-3)", "Moderate (4-6)", "Severe (7-9)", "Very Severe (10)"],
    )
    response = client.post("/api/v2/intake/step", json={
        "user_message": "it hurts a lot",
        "session_state": empty_session_state,
    })
    assert response.json()["quick_options"] == [
        "Mild (1-3)", "Moderate (4-6)", "Severe (7-9)", "Very Severe (10)"
    ]


# ------------------------------------------------------------------------------
# Error handling
# ------------------------------------------------------------------------------

def test_intake_step_invalid_payload():
    """Tests API error handling when required fields are missing in JSON request."""
    invalid_payload = {}  # Missing required user_message field entirely

    response = client.post("/api/v2/intake/step", json=invalid_payload)

    assert response.status_code == 422  # Unprocessable Entity (Validation Error)


@patch(EXTRACTOR_PATCH_TARGET)
def test_intake_step_extractor_failure_returns_500(mock_extract, initial_payload):
    """If the extractor raises unexpectedly, the endpoint should surface a 500, not crash silently."""
    mock_extract.side_effect = RuntimeError("Upstream LLM call failed")

    response = client.post("/api/v2/intake/step", json=initial_payload)

    assert response.status_code == 500
    assert "Intake step execution error" in response.json()["detail"]
