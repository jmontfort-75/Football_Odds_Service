"""FastAPI application entrypoint for the Football Odds Service.

Deliberately minimal: an unversioned /health check for infra/uptime
tooling, plus the versioned /api/v1 router for everything else. No
odds/bookmaker logic lives here yet.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import router as v1_router
from app.core.config import settings
from app.models.status import HealthResponse

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("football_odds_service")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "Starting %s in %s mode", settings.service_name, settings.app_env
    )
    yield


app = FastAPI(
    title="Football Odds Service",
    version="0.1.0",
    lifespan=lifespan,
    servers=[{"url": settings.public_api_url}],
)

# Allow the local Next.js dev server (or configured frontend origin) to
# call this API from the browser. Kept narrow rather than wildcard "*".
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(v1_router)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Unversioned liveness check, separate from /api/v1/status."""
    return HealthResponse(status="ok", service=settings.service_name)
