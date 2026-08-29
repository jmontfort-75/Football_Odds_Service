from pathlib import Path

import pytest

from app.providers.oddschecker import OddscheckerParseError, parse_oddschecker_html

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "oddschecker_man_city_coventry.html"
FIXTURE_URL = "https://www.oddschecker.com/football/english/premier-league/man-city-v-coventry"


@pytest.fixture
def fixture_html() -> str:
    return FIXTURE_PATH.read_text()


def test_parses_fixture_identity(fixture_html):
    result = parse_oddschecker_html(fixture_html, FIXTURE_URL)
    assert result.source == "Oddschecker"
    assert result.source_fixture_name == "Man City v Coventry"
    assert result.home_team == "Man City"
    assert result.away_team == "Coventry"
    assert result.source_url == FIXTURE_URL


def test_1x2_market_is_available_with_all_three_selections(fixture_html):
    result = parse_oddschecker_html(fixture_html, FIXTURE_URL)
    market = next(m for m in result.markets if m.market_type == "1X2")

    assert market.available is True
    selection_names = {s.name for s in market.selections}
    assert selection_names == {"Man City", "Draw", "Coventry"}
    assert all(s.decimal_odds > 1.0 for s in market.selections)
    assert all(s.bookmaker for s in market.selections)
    assert all(s.raw_odds for s in market.selections)


def test_1x2_selection_carries_provenance(fixture_html):
    result = parse_oddschecker_html(fixture_html, FIXTURE_URL)
    market = next(m for m in result.markets if m.market_type == "1X2")
    bet365_man_city = next(
        s for s in market.selections if s.name == "Man City" and s.bookmaker == "bet365"
    )
    assert bet365_man_city.raw_odds == "2/9"
    assert bet365_man_city.decimal_odds == 1.222
    assert bet365_man_city.source_decimal_odds == 1.222
    assert bet365_man_city.bookmaker_updated_at is not None


def test_unpopulated_markets_are_reported_as_unavailable_not_empty_success(fixture_html):
    """This fixture was captured 7 days before kickoff: Oddschecker had not
    yet posted BTTS/Over-Under/team-total prices. The provider must say so
    explicitly rather than silently returning an empty-but-"available" market.
    """
    result = parse_oddschecker_html(fixture_html, FIXTURE_URL)
    by_type = {m.market_type: m for m in result.markets}

    for market_type in ("OVER_UNDER_2_5", "BTTS", "TEAM_TOTAL_HOME_GOALS", "TEAM_TOTAL_AWAY_GOALS"):
        market = by_type[market_type]
        assert market.available is False
        assert market.selections == []
        assert market.note  # explanation must be present, not silently blank


def test_missing_bestodds_payload_raises_explicit_error():
    with pytest.raises(OddscheckerParseError):
        parse_oddschecker_html("<html><body>not a fixture page</body></html>", FIXTURE_URL)


def test_malformed_json_in_script_tag_raises_explicit_error():
    broken_html = '<script type="application/json"><!--{not valid json--></script>'
    with pytest.raises(OddscheckerParseError):
        parse_oddschecker_html(broken_html, FIXTURE_URL)
