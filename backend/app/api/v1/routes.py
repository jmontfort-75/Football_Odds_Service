"""Versioned API routes (/api/v1).

This is where future odds/bookmaker endpoints will be added. For now it
only exposes a status endpoint so the versioning scheme is in place
before any real functionality is built on top of it.
"""

from fastapi import APIRouter

from app.core.config import settings
from app.models.status import StatusResponse

router = APIRouter(prefix="/api/v1", tags=["v1"])


@router.get("/status", response_model=StatusResponse)
def get_status() -> StatusResponse:
    """Basic status endpoint, versioned so future breaking changes to the
    API can live under /api/v2 etc. without touching /health."""
    return StatusResponse(
        status="ok",
        service=settings.service_name,
        environment=settings.app_env,
        version="v1",
    )
