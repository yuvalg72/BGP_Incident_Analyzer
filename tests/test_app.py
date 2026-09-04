from fastapi.testclient import TestClient

from app.analyzer import DEMO_PREFIX, ResourceTarget
from app.main import app

client = TestClient(app)

DEMO_REQUEST = {
    "resource": "198.51.100.25",
    "start": "2026-08-31T20:55:00Z",
    "end": "2026-08-31T21:55:00Z",
    "projects": ["ris", "routeviews"],
    "mode": "demo",
}


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.2.0"}
    assert response.headers["cache-control"] == "no-store"


def test_ready_requires_bgpreader(monkeypatch):
    monkeypatch.setattr("app.main.shutil.which", lambda _name: None)
    response = client.get("/api/ready")
    assert response.status_code == 503
    assert response.json()["detail"] == "bgpreader is not available"


def test_ready_reports_bgpreader(monkeypatch):
    monkeypatch.setattr("app.main.shutil.which", lambda _name: "/usr/bin/bgpreader")
    response = client.get("/api/ready")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "version": "0.2.0",
        "bgpreader": True,
    }


def test_index_serves_application_with_security_headers():
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "BGP Incident Analyzer" in response.text
    assert "BGP Incident Analyzer v0.2.0" in response.text
    assert "BGP Incident Analyzer v1.0" not in response.text
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    csp = response.headers["content-security-policy"]
    assert "frame-ancestors 'none'" in csp
    assert "style-src 'self' 'unsafe-inline'" in csp


def test_demo_analysis_is_never_labeled_as_requested_prefix():
    response = client.post("/api/analyze", json=DEMO_REQUEST)
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "demo"
    assert data["prefix"] == DEMO_PREFIX
    assert data["prefix"] != "198.51.100.25/32"
    assert data["query"]["requested_resource"] == "198.51.100.25"
    assert data["query"]["resolved_prefix"] == "198.51.100.25/32"
    assert data["query"]["bgp_filter"] is None
    assert "no live BGP query was run" in data["source_note"]
    assert data["metrics"]["withdrawals"] == 3
    assert data["severity"] == "warning"


def test_live_analysis_uses_resolved_filter(monkeypatch):
    target = ResourceTarget(
        requested_resource="8.8.8.8",
        display_prefix="8.8.8.0/24",
        bgp_filter="prefix any 8.8.8.8/32",
        resolution="test resolution",
    )

    async def fake_resolve(_resource):
        return target

    async def fake_collect(bgp_filter, _start, _end, _projects):
        assert bgp_filter == target.bgp_filter
        return []

    monkeypatch.setattr("app.main.resolve_resource", fake_resolve)
    monkeypatch.setattr("app.main.collect_live", fake_collect)
    payload = {**DEMO_REQUEST, "resource": "8.8.8.8", "mode": "live"}
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "live"
    assert data["prefix"] == "8.8.8.0/24"
    assert data["query"]["bgp_filter"] == "prefix any 8.8.8.8/32"


def test_auto_fallback_keeps_demo_prefix_distinct(monkeypatch):
    target = ResourceTarget(
        requested_resource="8.8.8.8",
        display_prefix="8.8.8.0/24",
        bgp_filter="prefix any 8.8.8.8/32",
        resolution="test resolution",
    )

    async def fake_resolve(_resource):
        return target

    async def fail_collect(*_args, **_kwargs):
        raise RuntimeError("collector unavailable")

    monkeypatch.setattr("app.main.resolve_resource", fake_resolve)
    monkeypatch.setattr("app.main.collect_live", fail_collect)
    payload = {**DEMO_REQUEST, "resource": "8.8.8.8", "mode": "auto"}
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "demo"
    assert data["prefix"] == DEMO_PREFIX
    assert data["query"]["resolved_prefix"] == "8.8.8.0/24"
    assert data["query"]["bgp_filter"] is None
    assert "instead of live results for 8.8.8.8" in data["source_note"]


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


def test_rejects_naive_timestamp():
    payload = {**DEMO_REQUEST, "start": "2026-08-31T20:55:00"}
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 422


def test_rejects_empty_projects():
    payload = {**DEMO_REQUEST, "projects": []}
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 422


def test_rejects_duplicate_projects():
    payload = {**DEMO_REQUEST, "projects": ["ris", "ris"]}
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 422


def test_rejects_unknown_fields():
    payload = {**DEMO_REQUEST, "unexpected": True}
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 422


def test_rejects_invalid_resource():
    payload = {**DEMO_REQUEST, "resource": "not-an-ip-or-prefix"}
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 422
