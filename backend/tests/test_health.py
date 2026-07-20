from fastapi.testclient import TestClient

from app.factory import create_app


def test_liveness() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json() == {"data": {"status": "ok"}, "meta": None}


def test_disclaimer_is_available() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/safety/disclaimer")
    assert response.status_code == 200
    assert "educational information" in response.json()["data"]["disclaimer"]
