from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200():
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_expected_shape():
    response = client.get("/health")
    body = response.json()
    assert body == {"status": "ok", "service": "football-odds-service"}


def test_v1_status_returns_200():
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == "v1"
