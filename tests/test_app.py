from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

DEMO_REQUEST = {
    "resource": "192.0.2.10/32",
    "start": "2026-08-31T20:55:00Z",
    "end": "2026-08-31T21:55:00Z",
    "projects": ["ris", "routeviews"],
    "mode": "demo",
}


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_index_serves_application():
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "BGP Incident Analyzer" in response.text


def test_demo_analysis():
    response = client.post("/api/analyze", json=DEMO_REQUEST)
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "demo"
    assert data["metrics"]["withdrawals"] == 3
    assert data["severity"] == "warning"


def test_rejects_invalid_window():
    payload = {
        **DEMO_REQUEST,
        "start": "2026-08-31T21:55:00Z",
        "end": "2026-08-31T20:55:00Z",
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 422


def test_rejects_window_longer_than_seven_days():
    payload = {
        **DEMO_REQUEST,
        "start": "2026-08-01T00:00:00Z",
        "end": "2026-08-09T00:00:01Z",
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 422


def test_rejects_empty_projects():
    payload = {**DEMO_REQUEST, "projects": []}
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 422


def test_rejects_invalid_resource():
    payload = {**DEMO_REQUEST, "resource": "not-an-ip-or-prefix"}
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 422
