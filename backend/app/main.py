# backend/app/main.py
"""
Primary Entry Point for ClinicalPrep AI v2.0 FastAPI Monolith Backend.

This module initializes the core FastAPI application, configures CORS middleware for 
frontend client communication, sets up rate-limiting defenses, manages lifespan events 
for AI model initialization, and mounts versioned API routers.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Core System Utilities & Rate Limiting Engine
from app.core.limiter import limiter

# Feature API v2 Routers
from app.api.v2.intake import router as intake_router
from app.api.v2.audio import router as audio_router  # Microsoft VibeVoice STT & TTS pipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application lifespan (startup and shutdown events).
    
    Purpose: Pre-loads heavy resources (such as Hugging Face VibeVoice ASR models 
    or database connection pools) into GPU/CPU memory prior to receiving HTTP requests, 
    and handles graceful cleanup upon server termination.
    """
    print("🚀 Starting ClinicalPrep AI v2.0 Backend...")
    # Startup: Model warm-up and resource pre-allocation occur here
    yield
    # Shutdown: Release GPU memory locks and close active network connections
    print("🛑 Shutting down ClinicalPrep AI v2.0 Backend...")


# Initialize the Main FastAPI Application Instance
app = FastAPI(
    title="ClinicalPrep AI API",
    version="2.0.0",
    description=(
        "Decoupled Modular Monolith Backend for ClinicalPrep AI. "
        "Provides structured patient intake slot-filling, red-flag emergency triage, "
        "and Microsoft VibeVoice Speech-to-Text / Text-to-Speech audio processing."
    ),
    lifespan=lifespan
)

# ------------------------------------------------------------------------------
# 1. Rate Limiting Configuration
# Purpose: Prevents API quota exhaustion, DDoS attacks, and spamming on heavy 
# LLM/STT processing endpoints using Slowapi IP-based limits.
# ------------------------------------------------------------------------------
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ------------------------------------------------------------------------------
# 2. CORS (Cross-Origin Resource Sharing) Middleware
# Purpose: Permits the React frontend (running locally on Vite or hosted on Vercel) 
# to make asynchronous HTTP requests and stream multipart web audio blobs to the backend.
# ------------------------------------------------------------------------------
allowed_origins = [
    "http://localhost:5173",          # Vite React local development server
    "http://127.0.0.1:5173",         # Local IP fallback for browser client
    "https://clinical-prep-ai.vercel.app",  # Production Vercel frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,           # Allows session cookies and authorization headers
    allow_methods=["*"],              # Permits GET, POST, OPTIONS, DELETE, etc.
    allow_headers=["*"],              # Permits multipart/form-data and JSON headers
)

# ------------------------------------------------------------------------------
# 3. Application Router Registrations
# Purpose: Mounts isolated, feature-specific endpoint groups into the main app space.
# ------------------------------------------------------------------------------

# Mounts Clinical Intake Router (/api/v2/intake/step) for Pydantic v2 slot extraction
app.include_router(intake_router)

# Mounts Audio Router (/api/v2/audio/transcribe & /speak) for VibeVoice STT & TTS
app.include_router(audio_router)


# ------------------------------------------------------------------------------
# 4. System Health Check Endpoint
# Purpose: Diagnostic endpoint for monitoring deployment health, service availability, 
# and confirming active feature capabilities.
# ------------------------------------------------------------------------------
@app.get("/api/health", tags=["System Health"])
@limiter.limit("10/minute")  # Restricts rate-check spam to 10 requests per minute per IP
async def health_check(request: Request):
    """
    Returns system status, version metadata, and active feature capabilities.
    """
    return {
        "status": "healthy",
        "service": "ClinicalPrep AI Backend",
        "version": "2.0.0",
        "features": {
            "pydantic_slot_filling": True,
            "vibevoice_stt": True,
            "tts_synthesis": True
        }
    }


# Local Server Launcher (Executed when running `python app/main.py` directly)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)