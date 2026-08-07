# ==============================================================================
# FILE: backend/app/api/v2/__init__.py
# PURPOSE: Package initialization for Version 2 (v2) API router endpoints.
# SCOPE: Marks the v2 directory as a Python package and exposes active v2 routers for clean registration in main.py.
# ==============================================================================

from app.api.v2.intake import router as intake_router

__all__ = ["intake_router"]