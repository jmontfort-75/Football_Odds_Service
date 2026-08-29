"""Normalized odds models for the Oddschecker feasibility spike.

These intentionally mirror only what the spike actually retrieves (see
docs/oddschecker-gw3-feasibility-spike.md) -- no consensus/fair-odds
modelling, no multi-provider abstraction.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class Selection(BaseModel):
    """A single bookmaker's price for one outcome of one market."""

    name: str  # selection name exactly as shown at source, e.g. "Man City"
    bookmaker: str  # bookmaker display name, e.g. "bet365"
    raw_odds: str  # raw fractional odds text exactly as shown, e.g. "2/9"
    decimal_odds: float  # normalized decimal odds we computed from raw_odds
    source_decimal_odds: float | None = None  # decimal odds as published by the source, for cross-checking
    bookmaker_updated_at: datetime | None = None  # source's own last-updated timestamp for this price, if given


class Market(BaseModel):
    """One market (e.g. Match Result) for the fixture."""

    market_type: str  # our normalized identifier, e.g. "1X2", "OVER_UNDER_2_5"
    source_market_name: str  # market name exactly as shown at source
    available: bool  # whether the source currently publishes any prices for this market
    note: str | None = None  # explanation when available=False (e.g. "no bookmaker has posted odds yet")
    selections: list[Selection] = Field(default_factory=list)


class FixtureOdds(BaseModel):
    """Normalized, provenance-preserving odds for a single fixture."""

    source: str = "Oddschecker"
    source_fixture_name: str  # fixture name exactly as shown at source, e.g. "Man City vs Coventry"
    source_url: str
    home_team: str
    away_team: str
    fetched_at: datetime  # retrieval timestamp, UTC
    markets: list[Market] = Field(default_factory=list)
