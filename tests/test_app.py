from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}

def test_demo_analysis():
    response = client.post("/api/analyze", json={"resource":"192.0.2.10/32","start":"2026-08-31T20:55:00Z","end":"2026-08-31T21:55:00Z","projects":["ris","routeviews"],"mode":"demo"})
    assert response.status_code == 200
    data=response.json()
    assert data["mode"] == "demo"
    assert data["metrics"]["withdrawals"] == 3
    assert data["severity"] == "warning"

def test_rejects_invalid_window():
    response = client.post("/api/analyze", json={"resource":"1.1.1.1","start":"2026-08-31T21:55:00Z","end":"2026-08-31T20:55:00Z","projects":["ris"],"mode":"demo"})
    assert response.status_code == 422
