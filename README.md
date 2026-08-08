🩺 ClinicalPrep AI (v2.0) — Master Documentation & Progress Report
ClinicalPrep AI is an intelligent, empathetic patient-intake assistant designed to bridge the gap between patients and healthcare providers. It conducts a structured, conversational interview to organize a patient's medical concerns, symptoms, history, and goals into a clean, professional "Doctor Brief" (Patient Pre-Visit Summary) prior to their appointment.


🎯 Purpose & Vision
In traditional healthcare settings, short consultation times often lead to rushed discussions where patients forget critical symptoms or medical history. ClinicalPrep AI solves this by acting as a pre-visit administrative triage nurse:

Bridge Complex Information: Translates casual, unstructured patient speech into organized clinical terms.

Reduce Administrative Burden: Eliminates manual data entry for clinical staff by producing a ready-to-review summary.

Safety First: Integrates automated emergency triage triggers that immediately direct patients with severe, acute symptoms (e.g., severe chest tightness, breathing difficulties) to seek urgent care.

🚀 Version Evolution (v1.0 ➔ v2.0)
Version 1.0 — Proof of Concept
Built as a single-script Streamlit application.

Implemented the CC-SC-R (Context, Constraints, Structure, Checkpoints, Review) system prompt framework.

Generated PDF summaries using fpdf2.

Version 2.0 — The Foundation & Conversational Upgrade
Decoupled Modular Monolith Stack: Migrated from Streamlit to a production-ready React (Vite) frontend and a FastAPI backend.

Multi-Field Slot Filling: Replaced rigid one-by-one questions with Pydantic v2 structured outputs (strict=True) that extract multiple demographic and clinical fields from a single natural response.

Full Audio Pipeline & Mode Switching: Added hands-free voice interaction utilizing browser MediaRecorder audio capture, Speech-to-Text (STT) transcription, Text-to-Speech (TTS) voice streaming, and dedicated Chat/Voice mode toggling.

3-Layer Guardrail Architecture: Prevents intent drift and handles emergency red flags deterministically.

Observability & Tracing: Integrated Langfuse for prompt/cost tracing, Sentry for error logging, and Slowapi for IP rate limiting.

✨ Key Features (v2.0)
Natural Multi-Field Intake: Patients can speak or type freely. The extraction engine extracts populated fields into structured memory and only asks follow-up questions for unpopulated slots.

Dedicated Mode Toggle (Text vs. Voice): Enables seamless switching between standard keyboard typing and hands-free voice interaction, ensuring audio playback and microphone controls do not clash.

3-Layer Safety Guardrails:

Layer 1: Emergency red-flag regex matching (e.g., chest pain, acute trauma).

Layer 2: LLM intent classification (detects off-topic queries or medical advice requests).

Layer 3: Pivot redirect engine (gracefully guides the user back to the active intake step).

Contextual Quick-Reply Chips: Displays dynamic suggestion chips (e.g., Chief Complaint options, Gender identity options, Onset/Duration choices) to speed up user input.

Monotonic Step Progression: Tracks 5 distinct intake stages (Demographics ➔ Onset/Duration ➔ Symptom Characteristics ➔ History & Goals ➔ Brief Generation) without step regression.


ClinicalAssistant/
├── docs/                                 # Product Roadmaps, Technical Architecture & PRD PDFs
├── frontend/                             # React (Vite) Frontend Application
│   ├── src/
│   │   ├── components/                   # Header, ChatContainer, QuickReplyChips, SummaryCard, ModeToggle
│   │   ├── hooks/                        # useAudioRecorder.js (MediaRecorder API)
│   │   ├── services/                     # api.js (Asynchronous HTTP endpoints)
│   │   └── App.jsx                       # Main application state and intake handler
│   ├── package.json
│   └── vite.config.js
└── backend/                              # FastAPI Backend Application
    ├── app/
    │   ├── api/v2/                       # API Routers (/intake, /audio)
    │   ├── core/                         # Rate limiters & CORS configuration
    │   ├── services/
    │   │   ├── intake/                   # schemas.py, extractor.py, state.py
    │   │   ├── audio/                    # voice.py (STT & TTS service wrappers)
    │   │   └── pdf/                      # pdf_generator.py (fpdf2 layout engine)
    │   └── main.py                       # FastAPI entry point & lifespan manager
    └── requirements.txt
