"""Versioned API routes (/api/v1).

This is where future odds/bookmaker endpoints will be added. For now it
only exposes a status endpoint so the versioning scheme is in place
before any real functionality is built on top of it.
"""

import time

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.models.odds import FixtureOdds
from app.models.status import StatusResponse
from app.providers.oddschecker import (
    OddscheckerFetchError,
    OddscheckerParseError,
    get_man_city_v_coventry_odds,
)

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


# Extracting live odds launches a headless browser (see app/providers/oddschecker.py),
# which is too slow/heavy to redo on every request. This is a deliberately
# temporary, in-memory (no persistence, single-process) cache for the spike --
# not a general caching layer. It disappears on restart and is not shared
# across workers.
_ODDS_CACHE_TTL_SECONDS = 300
_odds_cache: dict[str, tuple[float, FixtureOdds]] = {}


@router.get("/odds/oddschecker/man-city-v-coventry", response_model=FixtureOdds)
async def get_man_city_v_coventry_oddschecker_odds() -> FixtureOdds:
    """Feasibility-spike endpoint: normalized Oddschecker odds for the single
    Man City vs Coventry (GW3) fixture. See
    docs/oddschecker-gw3-feasibility-spike.md for scope and limitations.
    """
    cache_key = "man-city-v-coventry"
    cached = _odds_cache.get(cache_key)
    if cached is not None:
        cached_at, cached_odds = cached
        if time.monotonic() - cached_at < _ODDS_CACHE_TTL_SECONDS:
            return cached_odds

    try:
        fixture_odds = await get_man_city_v_coventry_odds()
    except OddscheckerFetchError as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch Oddschecker page: {exc}") from exc
    except OddscheckerParseError as exc:
        raise HTTPException(status_code=502, detail=f"Failed to parse Oddschecker page: {exc}") from exc

    _odds_cache[cache_key] = (time.monotonic(), fixture_odds)
    return fixture_odds
