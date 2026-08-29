from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.api.v1 import routes as odds_routes
from app.main import app
from app.models.odds import FixtureOdds, Market, Selection
from app.providers.oddschecker import OddscheckerFetchError

client = TestClient(app)


def _sample_fixture_odds() -> FixtureOdds:
    return FixtureOdds(
        source_fixture_name="Man City v Coventry",
        source_url="https://www.oddschecker.com/football/english/premier-league/man-city-v-coventry",
        home_team="Man City",
        away_team="Coventry",
        fetched_at=datetime.now(timezone.utc),
        markets=[
            Market(
                market_type="1X2",
                source_market_name="Win Market",
                available=True,
                selections=[
                    Selection(name="Man City", bookmaker="bet365", raw_odds="2/9", decimal_odds=1.222),
                ],
            ),
            Market(
                market_type="BTTS",
                source_market_name="Both Teams To Score",
                available=False,
                note="No odds available at the moment (per source)",
            ),
        ],
    )


def setup_function():
    odds_routes._odds_cache.clear()


def test_endpoint_returns_normalized_contract(monkeypatch):
    async def fake_get_odds():
        return _sample_fixture_odds()

    monkeypatch.setattr(odds_routes, "get_man_city_v_coventry_odds", fake_get_odds)

    response = client.get("/api/v1/odds/oddschecker/man-city-v-coventry")

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "Oddschecker"
    assert body["home_team"] == "Man City"
    market_types = {m["market_type"] for m in body["markets"]}
    assert "1X2" in market_types
    btts = next(m for m in body["markets"] if m["market_type"] == "BTTS")
    assert btts["available"] is False
    assert btts["selections"] == []


def test_endpoint_returns_502_on_fetch_failure_instead_of_fabricating_data(monkeypatch):
    async def fake_get_odds_failure():
        raise OddscheckerFetchError("Cloudflare blocked the request")

    monkeypatch.setattr(odds_routes, "get_man_city_v_coventry_odds", fake_get_odds_failure)

    response = client.get("/api/v1/odds/oddschecker/man-city-v-coventry")

    assert response.status_code == 502
    assert "Cloudflare" in response.json()["detail"]


def test_endpoint_caches_successful_response(monkeypatch):
    call_count = 0

    async def fake_get_odds():
        nonlocal call_count
        call_count += 1
        return _sample_fixture_odds()

    monkeypatch.setattr(odds_routes, "get_man_city_v_coventry_odds", fake_get_odds)

    first = client.get("/api/v1/odds/oddschecker/man-city-v-coventry")
    second = client.get("/api/v1/odds/oddschecker/man-city-v-coventry")

    assert first.status_code == second.status_code == 200
    assert call_count == 1  # second request served from the in-memory cache
