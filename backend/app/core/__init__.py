# ==============================================================================
# FILE: backend/app/core/__init__.py
# PURPOSE: Package initialization file for core system utilities and configurations.
# SCOPE: Exposes core shared utilities like rate limiting and security configurations.
# ==============================================================================

from app.core.limiter import limiter

__all__ = ["limiter"]