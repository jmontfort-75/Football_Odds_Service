"""Oddschecker odds extraction for a single hardcoded fixture (feasibility spike).

Findings that shaped this module (see docs/oddschecker-gw3-feasibility-spike.md):

* Plain HTTP requests (curl, the WebFetch tool) are blocked site-wide by
  Cloudflare with a 403 "Sorry, you have been blocked" page -- this happens
  even for the Oddschecker homepage, so it is not URL-specific.
* A real, JS-executing browser (headless Chromium via Playwright) passes the
  Cloudflare check and receives a normal 200 response with the real page.
* The odds themselves are NOT in a clean server-rendered HTML table -- they
  live in a large embedded JSON blob (a `<script type="application/json">`
  tag wrapped in an HTML comment) that React hydrates from. That blob only
  contains bets/odds for markets that currently have bookmaker prices; a
  market with no odds yet simply has no entries under it. Some markets exist
  in `markets.entities` but have zero bets, and the DOM confirms this ("No
  odds available at the moment. Check again later."), which is a genuine
  data-availability gap this far ahead of kickoff -- not a parsing failure.

So the extraction pipeline is: render the page with a real browser once,
then parse the embedded JSON (preference order step 2), not the HTML table
(step 4) and not raw HTTP (step 1, which is blocked outright).
"""

import json
import re
from datetime import datetime, timezone

from app.core.config import settings
from app.models.odds import FixtureOdds, Market, Selection
from app.providers.odds_conversion import fractional_to_decimal

FIXTURE_URL = "https://www.oddschecker.com/football/english/premier-league/man-city-v-coventry"

BASE_URL = "https://www.oddschecker.com/football/english/premier-league"


class GW3Fixture(dict):
    """A single GW3 fixture as verified in Phase 1 of the full-coverage spike
    (see docs/oddschecker-gw3-full-coverage-spike.md) -- cross-checked against
    mancity.com, ESPN, and SportsMole, and confirmed against Oddschecker's own
    live competition index page (all ten `{home}-v-{away}` slugs below were
    observed there). Plain dict subclass, not a new abstraction: just a
    typed-by-convention data holder for the fixtures this spike investigates.
    """


# Premier League GW3, 2026/27 season (kickoff Sat 5 / Sun 6 Sep 2026, plus the
# Friday-night opener). Slugs are Oddschecker's own `{home}-v-{away}` URL
# convention, verified live against https://www.oddschecker.com/football/english/premier-league.
GW3_FIXTURES: list[GW3Fixture] = [
    GW3Fixture(home="Ipswich Town", away="Liverpool", slug="ipswich-v-liverpool", kickoff_utc="2026-09-04T19:00:00Z"),
    GW3Fixture(home="Newcastle United", away="AFC Bournemouth", slug="newcastle-v-bournemouth", kickoff_utc="2026-09-05T11:30:00Z"),
    GW3Fixture(home="Brentford", away="Sunderland", slug="brentford-v-sunderland", kickoff_utc="2026-09-05T14:00:00Z"),
    GW3Fixture(home="Brighton & Hove Albion", away="Leeds United", slug="brighton-v-leeds", kickoff_utc="2026-09-05T14:00:00Z"),
    GW3Fixture(home="Fulham", away="Crystal Palace", slug="fulham-v-crystal-palace", kickoff_utc="2026-09-05T14:00:00Z"),
    GW3Fixture(home="Manchester City", away="Coventry City", slug="man-city-v-coventry", kickoff_utc="2026-09-05T14:00:00Z"),
    GW3Fixture(home="Nottingham Forest", away="Tottenham Hotspur", slug="nottingham-forest-v-tottenham", kickoff_utc="2026-09-05T14:00:00Z"),
    GW3Fixture(home="Hull City", away="Aston Villa", slug="hull-v-aston-villa", kickoff_utc="2026-09-05T16:30:00Z"),
    GW3Fixture(home="Everton", away="Manchester United", slug="everton-v-man-utd", kickoff_utc="2026-09-06T13:00:00Z"),
    GW3Fixture(home="Arsenal", away="Chelsea", slug="arsenal-v-chelsea", kickoff_utc="2026-09-06T15:30:00Z"),
]


def fixture_url(slug: str) -> str:
    """Build an Oddschecker fixture URL from its `{home}-v-{away}` slug."""
    return f"{BASE_URL}/{slug}"

_CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)

# (our market_type identifier, Oddschecker's marketTypeName, optional line filter)
_TARGET_MARKETS: list[tuple[str, str, float | None]] = [
    ("1X2", "Win Market", None),
    ("OVER_UNDER_2_5", "Total Goals Over/Under", 2.5),
    ("BTTS", "Both Teams To Score", None),
    ("TEAM_TOTAL_HOME_GOALS", "Total Home Goals", None),
    ("TEAM_TOTAL_AWAY_GOALS", "Total Away Goals", None),
]

_JSON_SCRIPT_RE = re.compile(
    r'<script[^>]*type="application/(?:ld\+json|json)"[^>]*>(.*?)</script>', re.S
)


class OddscheckerFetchError(RuntimeError):
    """Raised when the fixture page cannot be retrieved."""


class OddscheckerParseError(RuntimeError):
    """Raised when the fixture page was retrieved but the expected embedded
    odds data could not be found or was malformed. We never fabricate or
    default odds -- an extraction failure surfaces as this exception."""


def _strip_html_comment(raw: str) -> str:
    text = raw.strip()
    if text.startswith("<!--"):
        text = text[len("<!--"):]
    if text.endswith("-->"):
        text = text[: -len("-->")]
    return text.strip()


def _find_best_odds_payload(html: str) -> dict:
    """Locate the embedded JSON script tag holding bestOdds.markets/bets/odds."""
    candidates = _JSON_SCRIPT_RE.findall(html)
    for raw in candidates:
        text = _strip_html_comment(raw)
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            continue
        best_odds = data.get("bestOdds")
        if isinstance(best_odds, dict) and best_odds.get("markets", {}).get("entities"):
            return data
    raise OddscheckerParseError(
        "Could not find an embedded bestOdds JSON payload in the fixture page "
        "(page structure may have changed, or the fixture failed to load)"
    )


def _parse_source_timestamp(raw: str | None) -> datetime | None:
    """Parse Oddschecker's nanosecond-precision feed timestamps.

    Example: "2026-08-25T23:36:19.187726243Z". Python's datetime.fromisoformat
    only accepts up to microsecond precision, so we truncate the fractional
    part before parsing. Returns None on any unexpected format -- this field
    is supplementary provenance, not required for the selection to be valid.
    """
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        if "." in raw:
            head, rest = raw.split(".", 1)
            frac, _, offset = rest.partition("+")
            frac = frac[:6]
            raw = f"{head}.{frac}+{offset}" if offset else f"{head}.{frac}"
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def _build_market(
    market_type: str,
    market_type_name: str,
    line_filter: float | None,
    markets_by_type_name: dict[str, dict],
    bets: dict[str, dict],
    odds: dict[str, dict],
    bookmakers: dict[str, dict],
) -> Market:
    market_entity = markets_by_type_name.get(market_type_name)
    if market_entity is None:
        return Market(
            market_type=market_type,
            source_market_name=market_type_name,
            available=False,
            note="Market not present in the source page for this fixture",
        )

    source_market_name = market_entity.get("marketTypeName", market_type_name)
    market_id = market_entity["ocMarketId"]

    matching_bets = [
        (bet_id, bet)
        for bet_id, bet in bets.items()
        if bet.get("marketId") == market_id
        and (line_filter is None or bet.get("line") == line_filter)
    ]

    if not matching_bets:
        return Market(
            market_type=market_type,
            source_market_name=source_market_name,
            available=False,
            note="No odds available at the moment (per source) -- likely too far ahead of kickoff",
        )

    selections: list[Selection] = []
    for bet_id, bet in matching_bets:
        bet_odds = odds.get(str(bet_id), {})
        for bookmaker_code, price in bet_odds.items():
            if price.get("status") != "ACTIVE":
                continue
            raw_odds = price.get("odds")
            if not raw_odds:
                continue
            try:
                decimal_odds = fractional_to_decimal(raw_odds)
            except ValueError:
                # Skip prices we can't confidently convert rather than guessing.
                continue
            bookmaker_name = bookmakers.get(bookmaker_code, {}).get("bookmakerName", bookmaker_code)
            selections.append(
                Selection(
                    name=bet.get("betName", "UNKNOWN"),
                    bookmaker=bookmaker_name,
                    raw_odds=raw_odds,
                    decimal_odds=decimal_odds,
                    source_decimal_odds=price.get("oddsDecimal"),
                    bookmaker_updated_at=_parse_source_timestamp(price.get("betFeedTimestamp")),
                )
            )

    if not selections:
        return Market(
            market_type=market_type,
            source_market_name=source_market_name,
            available=False,
            note="Market entries existed but no ACTIVE, parseable bookmaker prices were found",
        )

    return Market(
        market_type=market_type,
        source_market_name=source_market_name,
        available=True,
        selections=selections,
    )


def parse_oddschecker_html(html: str, source_url: str) -> FixtureOdds:
    """Parse a saved/fetched Oddschecker fixture page into normalized odds.

    Pure function -- no network access -- so it can be unit tested against a
    saved fixture file.
    """
    payload = _find_best_odds_payload(html)
    best_odds = payload["bestOdds"]

    markets = best_odds["markets"]["entities"]
    bets = best_odds["bets"]["entities"]
    odds = best_odds["odds"]
    bookmakers = best_odds["bookmakers"]["entities"]

    if not markets:
        raise OddscheckerParseError("bestOdds payload present but contained no markets")

    # Fixture/team names exactly as Oddschecker labels them, taken from a
    # market's own marketName field, e.g. "Man City v Coventry#Win Market".
    any_market_name = next(iter(markets.values()))["marketName"]
    fixture_name = any_market_name.split("#", 1)[0]
    if " v " not in fixture_name:
        raise OddscheckerParseError(f"Unexpected fixture name format: {fixture_name!r}")
    home_team, away_team = (part.strip() for part in fixture_name.split(" v ", 1))

    markets_by_type_name = {m["marketTypeName"]: m for m in markets.values()}

    result_markets = [
        _build_market(market_type, type_name, line_filter, markets_by_type_name, bets, odds, bookmakers)
        for market_type, type_name, line_filter in _TARGET_MARKETS
    ]

    return FixtureOdds(
        source_fixture_name=fixture_name,
        source_url=source_url,
        home_team=home_team,
        away_team=away_team,
        fetched_at=datetime.now(timezone.utc),
        markets=result_markets,
    )


async def fetch_fixture_html(url: str = FIXTURE_URL, render_wait_ms: int = 5000) -> str:
    """Render the fixture page with a real (headless) browser and return its HTML.

    A real browser is required: plain HTTP requests to oddschecker.com are
    blocked site-wide by Cloudflare (see module docstring). This is local,
    free (Playwright + Chromium, no paid service), and used read-only.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError as exc:  # pragma: no cover - dependency documented in pyproject
        raise OddscheckerFetchError(
            "playwright is not installed; run `pip install playwright` and "
            "`playwright install chromium`"
        ) from exc

    async with async_playwright() as p:
        # Explicit, not relying on the Playwright default: production must
        # never open a visible browser. Override only via
        # ODDSCHECKER_HEADLESS=false in .env for local interactive debugging.
        browser = await p.chromium.launch(headless=settings.oddschecker_headless)
        try:
            page = await browser.new_page(user_agent=_CHROME_UA)
            response = await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            if response is None or response.status >= 400:
                status = response.status if response else "no response"
                raise OddscheckerFetchError(f"Unexpected HTTP status fetching {url}: {status}")
            # Let the client-side app finish hydrating the embedded odds JSON.
            await page.wait_for_timeout(render_wait_ms)
            return await page.content()
        finally:
            await browser.close()


async def get_man_city_v_coventry_odds() -> FixtureOdds:
    html = await fetch_fixture_html(FIXTURE_URL)
    return parse_oddschecker_html(html, FIXTURE_URL)


_TEAM_ABBREVIATIONS = {
    "manchester": "man",
    "united": "utd",
}


def _normalize_team_name(name: str) -> str:
    """Loose normalization for identity matching only (not for display) --
    lowercases, expands Oddschecker's own standard club abbreviations (it
    labels fixtures "Man City"/"Man Utd", never the full official names), and
    strips punctuation/whitespace so e.g. "Manchester City" and "Man City"
    normalize to the same string."""
    lowered = name.lower()
    for full, short in _TEAM_ABBREVIATIONS.items():
        lowered = re.sub(rf"\b{full}\b", short, lowered)
    return re.sub(r"[^a-z0-9]", "", lowered)


def fixture_identity_matches(expected: GW3Fixture, parsed: FixtureOdds) -> bool:
    """Strict-ish identity check: the parsed page's home/away team names must
    correspond to the expected fixture's home/away, not just contain a
    similar substring for one side. Guards against silently accepting a
    wrong fixture that merely looks similar (see spike Phase 2)."""
    exp_home = _normalize_team_name(expected["home"])
    exp_away = _normalize_team_name(expected["away"])
    got_home = _normalize_team_name(parsed.home_team)
    got_away = _normalize_team_name(parsed.away_team)
    home_ok = exp_home in got_home or got_home in exp_home
    away_ok = exp_away in got_away or got_away in exp_away
    return home_ok and away_ok


async def get_fixture_odds(slug: str) -> FixtureOdds:
    """Fetch and parse odds for any GW3 fixture by its Oddschecker slug --
    the same pipeline as get_man_city_v_coventry_odds, generalized so the
    full-coverage spike doesn't need a bespoke function per fixture."""
    url = fixture_url(slug)
    html = await fetch_fixture_html(url)
    return parse_oddschecker_html(html, url)
