from pathlib import Path

from app.providers.oddschecker import (
    GW3_FIXTURES,
    GW3Fixture,
    fixture_identity_matches,
    fixture_url,
    parse_oddschecker_html,
)

FIXTURE_HTML_PATH = Path(__file__).parent / "fixtures" / "oddschecker_man_city_coventry.html"


def test_gw3_fixtures_has_exactly_ten_unique_fixtures():
    assert len(GW3_FIXTURES) == 10
    slugs = [f["slug"] for f in GW3_FIXTURES]
    assert len(set(slugs)) == 10  # no duplicate fixtures


def test_fixture_url_uses_oddschecker_slug_convention():
    assert fixture_url("man-city-v-coventry") == (
        "https://www.oddschecker.com/football/english/premier-league/man-city-v-coventry"
    )


def test_identity_matches_exact_names():
    fixture = GW3Fixture(home="Arsenal", away="Chelsea", slug="arsenal-v-chelsea", kickoff_utc="2026-09-06T15:30:00Z")
    parsed = parse_oddschecker_html(FIXTURE_HTML_PATH.read_text(), fixture_url("man-city-v-coventry"))
    # Swap in matching names to isolate the matcher from the fixed sample file's own teams.
    parsed.home_team = "Arsenal"
    parsed.away_team = "Chelsea"
    assert fixture_identity_matches(fixture, parsed) is True


def test_identity_matches_oddschecker_abbreviations():
    """Oddschecker labels fixtures with its own short names ("Man City", "Man
    Utd"), never the official long names -- the matcher must see through that
    without becoming so loose it accepts a genuinely wrong fixture."""
    fixture = GW3Fixture(home="Manchester City", away="Coventry City", slug="man-city-v-coventry", kickoff_utc="2026-09-05T14:00:00Z")
    parsed = parse_oddschecker_html(FIXTURE_HTML_PATH.read_text(), fixture_url("man-city-v-coventry"))
    assert parsed.home_team == "Man City"
    assert parsed.away_team == "Coventry"
    assert fixture_identity_matches(fixture, parsed) is True


def test_identity_mismatch_is_detected_strictly():
    """A wrong fixture (even a plausible-looking one) must not be silently accepted."""
    fixture = GW3Fixture(home="Everton", away="Manchester United", slug="everton-v-man-utd", kickoff_utc="2026-09-06T13:00:00Z")
    parsed = parse_oddschecker_html(FIXTURE_HTML_PATH.read_text(), fixture_url("man-city-v-coventry"))
    # parsed is actually Man City v Coventry -- must not match Everton v Man Utd.
    assert fixture_identity_matches(fixture, parsed) is False


def test_market_present_but_unpriced_is_distinct_from_market_absent():
    """Regression guard for the coverage spike's core distinction: a market
    the source structurally has (but with zero current bookmaker prices)
    must not be reported the same way as a market the source never listed."""
    result = parse_oddschecker_html(FIXTURE_HTML_PATH.read_text(), fixture_url("man-city-v-coventry"))
    by_type = {m.market_type: m for m in result.markets}

    unpriced = by_type["OVER_UNDER_2_5"]
    assert unpriced.available is False
    assert "No odds available" in unpriced.note

    present = by_type["1X2"]
    assert present.available is True
    assert present.selections
