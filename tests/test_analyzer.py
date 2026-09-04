import asyncio
import os
from datetime import datetime, timezone

import pytest

import app.analyzer as analyzer
from app.analyzer import _parse_bgpreader_line, collect_live, resolve_resource, summarize


def _event(event_type="A", origin_asn=64512, timestamp="2026-08-31T21:00:00Z"):
    return {
        "timestamp": timestamp,
        "type": event_type,
        "project": "ris",
        "collector": "rrc00",
        "peer_asn": 64501,
        "peer_ip": "192.0.2.1",
        "prefix": "203.0.113.0/24",
        "as_path": "64501 64510 64512" if event_type == "A" else "",
        "origin_asn": origin_asn if event_type == "A" else None,
    }


def _install_fake_bgpreader(tmp_path, body: str, monkeypatch) -> None:
    executable = tmp_path / "bgpreader"
    executable.write_text("#!/usr/bin/env python3\n" + body, encoding="utf-8")
    executable.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ.get('PATH', '')}")


def test_resolve_resource_normalizes_network_without_network_access():
    prefix, source = asyncio.run(resolve_resource("192.0.2.17/24"))
    assert prefix == "192.0.2.0/24"
    assert source == "user-supplied prefix"


def test_parse_bgpreader_announcement():
    line = (
        "U|A|1788200000|ris|rrc00|||64501|192.0.2.1|"
        "203.0.113.0/24||64501 64510 64512|64512|||"
    )
    event = _parse_bgpreader_line(line)
    assert event is not None
    assert event["type"] == "A"
    assert event["peer_asn"] == 64501
    assert event["origin_asn"] == 64512
    assert event["prefix"] == "203.0.113.0/24"


def test_parse_bgpreader_withdrawal():
    line = (
        "U|W|1788200001|routeviews|route-views.linx|||64502|198.51.100.1|"
        "203.0.113.0/24||||||"
    )
    event = _parse_bgpreader_line(line)
    assert event is not None
    assert event["type"] == "W"
    assert event["origin_asn"] is None
    assert event["as_path"] == ""


def test_parse_bgpreader_rejects_state_and_rib_elements():
    state = "U|S|1788200000|ris|rrc00|||64501|192.0.2.1|||||||"
    rib = (
        "R|R|1788200000|ris|rrc00|||64501|192.0.2.1|203.0.113.0/24||"
        "64501 64512|64512|||"
    )
    assert _parse_bgpreader_line(state) is None
    assert _parse_bgpreader_line(rib) is None


def test_parse_bgpreader_rejects_malformed_line():
    assert _parse_bgpreader_line("not|a|valid|record") is None


def test_collect_live_reads_fake_bgpreader(tmp_path, monkeypatch):
    line = (
        "U|A|1788200000|ris|rrc00|||64501|192.0.2.1|"
        "203.0.113.0/24||64501 64510 64512|64512|||"
    )
    _install_fake_bgpreader(tmp_path, f"print({line!r})\n", monkeypatch)
    events = asyncio.run(
        collect_live(
            "203.0.113.0/24",
            datetime(2026, 8, 31, 20, tzinfo=timezone.utc),
            datetime(2026, 8, 31, 21, tzinfo=timezone.utc),
            ["ris"],
        )
    )
    assert len(events) == 1
    assert events[0]["origin_asn"] == 64512


def test_collect_live_enforces_event_limit(tmp_path, monkeypatch):
    line = (
        "U|A|1788200000|ris|rrc00|||64501|192.0.2.1|"
        "203.0.113.0/24||64501 64510 64512|64512|||"
    )
    _install_fake_bgpreader(
        tmp_path,
        f"for _ in range(3):\n    print({line!r}, flush=True)\n",
        monkeypatch,
    )
    monkeypatch.setattr(analyzer, "MAX_EVENTS", 2)
    with pytest.raises(RuntimeError, match="2-event safety limit"):
        asyncio.run(
            collect_live(
                "203.0.113.0/24",
                datetime(2026, 8, 31, 20, tzinfo=timezone.utc),
                datetime(2026, 8, 31, 21, tzinfo=timezone.utc),
                ["ris"],
            )
        )


def test_collect_live_enforces_timeout(tmp_path, monkeypatch):
    _install_fake_bgpreader(tmp_path, "import time\ntime.sleep(2)\n", monkeypatch)
    monkeypatch.setattr(analyzer, "QUERY_TIMEOUT_SECONDS", 0.05)
    with pytest.raises(RuntimeError, match="0.05-second safety limit"):
        asyncio.run(
            collect_live(
                "203.0.113.0/24",
                datetime(2026, 8, 31, 20, tzinfo=timezone.utc),
                datetime(2026, 8, 31, 21, tzinfo=timezone.utc),
                ["ris"],
            )
        )


def test_summarize_multiple_origins_is_critical():
    events = [_event(origin_asn=64512), _event(origin_asn=64513)]
    result = summarize("203.0.113.0/24", events, "live", "test")
    assert result["severity"] == "critical"
    assert result["origins"] == [64512, 64513]
    assert "Multiple origin ASNs" in result["finding"]


def test_summarize_withdrawal_without_recovery_is_critical():
    result = summarize("203.0.113.0/24", [_event(event_type="W")], "live", "test")
    assert result["severity"] == "critical"
    assert result["metrics"]["withdrawals"] == 1
    assert result["metrics"]["announcements"] == 0


def test_summarize_no_events_is_unknown():
    result = summarize("203.0.113.0/24", [], "live", "test")
    assert result["severity"] == "unknown"
    assert result["metrics"]["events"] == 0


def test_summarize_aggregates_timeline_by_minute():
    events = [
        _event(timestamp="2026-08-31T21:00:01Z"),
        _event(event_type="W", timestamp="2026-08-31T21:00:59Z"),
    ]
    result = summarize("203.0.113.0/24", events, "live", "test")
    assert result["timeline"] == [
        {
            "time": "2026-08-31T21:00:00Z",
            "announcements": 1,
            "withdrawals": 1,
        }
    ]
