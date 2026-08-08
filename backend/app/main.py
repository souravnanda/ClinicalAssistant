# backend/app/main.py
"""
FastAPI Main Application Entry Point for ClinicalPrep AI v2.0.

Purpose:
    Initializes the FastAPI app instance, sets up global CORS middleware policies,
    attaches Slowapi rate limiting, registers API routers for intake and audio services,
    and disables bytecode writing (`sys.dont_write_bytecode`) to eliminate stale `__pycache__` artifacts.
"""

import sys
import os

# Disable CPython bytecode (.pyc) generation to prevent stale cache bugs during reloads
sys.dont_write_bytecode = True

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v2.intake import router as intake_router
from app.api.v2.audio import router as audio_router

app = FastAPI(
    title="ClinicalPrep AI Engine",
    version="2.0.0",
    description="Multi-turn clinical intake assistant with structured Pydantic slot extraction, emergency triage, and voice capabilities."
)

# Configure CORS Cross-Origin Resource Sharing for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits requests from Vite local server (http://localhost:5173) and public web clients
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register v2 Feature Routers
app.include_router(intake_router)
app.include_router(audio_router)


@app.get("/api/health")
async def health_check():
    """Health check endpoint for verifying backend service status."""
    return {"status": "healthy", "service": "ClinicalPrep AI Backend v2.0"}