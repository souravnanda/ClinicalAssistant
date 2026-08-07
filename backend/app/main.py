# ==============================================================================
# FILE: backend/app/main.py
# PURPOSE: Main FastAPI entrypoint registering core routers, CORS, and rate limiters.
# SCOPE: Serves health check endpoints and routes traffic to modular backend services.
# ==============================================================================

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded


from app.core.limiter import limiter
from app.api.v2.intake import router as intake_v2_router

app = FastAPI(
    title="ClinicalPrep AI Engine",
    version="2.0.0",
    description="Decoupled Modular Monolith for Patient Intake & Brief Generation"
)

# Attach Slowapi Rate Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS for decoupled frontend (Vercel / Localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Router Modules
app.include_router(intake_v2_router)


@app.get("/api/health", tags=["System"])
@limiter.limit("10/minute")
def health_check(request: Request):
    """System health check endpoint."""
    return {
        "status": "healthy",
        "service": "ClinicalPrep AI Backend",
        "version": "2.0.0"
    }