from __future__ import annotations

import asyncio
import ipaddress
import json
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

import httpx


DEMO_EVENTS = [
    {"timestamp": "2026-08-31T20:55:11Z", "type": "A", "project": "ris", "collector": "rrc00", "peer_asn": 64501, "peer_ip": "192.0.2.1", "prefix": "192.0.2.0/24", "as_path": "64501 64510 64512", "origin_asn": 64512},
    {"timestamp": "2026-08-31T21:07:43Z", "type": "W", "project": "ris", "collector": "rrc10", "peer_asn": 64502, "peer_ip": "198.51.100.2", "prefix": "192.0.2.0/24", "as_path": "", "origin_asn": None},
    {"timestamp": "2026-08-31T21:08:02Z", "type": "W", "project": "routeviews", "collector": "route-views.linx", "peer_asn": 64503, "peer_ip": "203.0.113.3", "prefix": "192.0.2.0/24", "as_path": "", "origin_asn": None},
    {"timestamp": "2026-08-31T21:08:18Z", "type": "W", "project": "ris", "collector": "rrc12", "peer_asn": 64504, "peer_ip": "192.0.2.4", "prefix": "192.0.2.0/24", "as_path": "", "origin_asn": None},
    {"timestamp": "2026-08-31T21:49:04Z", "type": "A", "project": "ris", "collector": "rrc10", "peer_asn": 64502, "peer_ip": "198.51.100.2", "prefix": "192.0.2.0/24", "as_path": "64502 64510 64512", "origin_asn": 64512},
    {"timestamp": "2026-08-31T21:49:12Z", "type": "A", "project": "routeviews", "collector": "route-views.linx", "peer_asn": 64503, "peer_ip": "203.0.113.3", "prefix": "192.0.2.0/24", "as_path": "64503 64510 64512", "origin_asn": 64512},
    {"timestamp": "2026-08-31T21:49:31Z", "type": "A", "project": "ris", "collector": "rrc12", "peer_asn": 64504, "peer_ip": "192.0.2.4", "prefix": "192.0.2.0/24", "as_path": "64504 64510 64512", "origin_asn": 64512},
]


async def resolve_resource(resource: str) -> tuple[str, str]:
    resource = resource.strip()
    try:
        network = ipaddress.ip_network(resource, strict=False)
        return str(network), "user-supplied prefix"
    except ValueError:
        try:
            ipaddress.ip_address(resource)
        except ValueError as exc:
            raise ValueError("Enter a valid IPv4/IPv6 address or prefix") from exc

    url = "https://stat.ripe.net/data/network-info/data.json"
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.get(url, params={"resource": resource})
            response.raise_for_status()
            prefix = response.json().get("data", {}).get("prefix")
            if prefix:
                return prefix, "resolved by RIPEstat"
    except (httpx.HTTPError, json.JSONDecodeError):
        pass
    host_prefix = f"{resource}/32" if ":" not in resource else f"{resource}/128"
    return host_prefix, "host prefix fallback; verify aggregation"


def _parse_bgpreader_line(line: str) -> dict[str, Any] | None:
    fields = line.rstrip().split("|")
    if len(fields) < 13 or fields[0] not in {"U", "R"}:
        return None
    try:
        ts = datetime.fromtimestamp(float(fields[2]), tz=timezone.utc).isoformat().replace("+00:00", "Z")
        path = fields[11]
        origin = fields[12]
        return {
            "timestamp": ts, "type": fields[1], "project": fields[3],
            "collector": fields[4], "peer_asn": int(fields[7]), "peer_ip": fields[8],
            "prefix": fields[9], "as_path": path,
            "origin_asn": int(origin) if origin.isdigit() else None,
        }
    except (ValueError, IndexError):
        return None


async def collect_live(prefix: str, start: datetime, end: datetime, projects: list[str]) -> list[dict[str, Any]]:
    if not shutil.which("bgpreader"):
        raise RuntimeError("bgpreader is not installed in this runtime")
    args = ["bgpreader", "-w", f"{int(start.timestamp())},{int(end.timestamp())}", "-t", "updates", "-k", prefix]
    for project in projects:
        args.extend(["-p", project])
    proc = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=90)
    except asyncio.TimeoutError:
        proc.kill()
        raise RuntimeError("BGP query exceeded the 90-second safety limit")
    if proc.returncode != 0:
        raise RuntimeError(stderr.decode(errors="replace").strip() or "bgpreader query failed")
    return [event for line in stdout.decode(errors="replace").splitlines() if (event := _parse_bgpreader_line(line))]


def summarize(prefix: str, events: list[dict[str, Any]], mode: str, source_note: str) -> dict[str, Any]:
    announcements = [e for e in events if e["type"] == "A"]
    withdrawals = [e for e in events if e["type"] == "W"]
    origins = sorted({e["origin_asn"] for e in announcements if e["origin_asn"]})
    collectors = sorted({e["collector"] for e in events})
    peers = {e["peer_asn"] for e in events}
    paths = Counter(e["as_path"] for e in announcements if e["as_path"])
    timeline: dict[str, dict[str, int]] = defaultdict(lambda: {"announcements": 0, "withdrawals": 0})
    for event in events:
        minute = event["timestamp"][:16] + ":00Z"
        timeline[minute]["announcements" if event["type"] == "A" else "withdrawals"] += 1

    severity = "normal"
    finding = "No material routing instability was observed in the selected window."
    if len(origins) > 1:
        severity, finding = "critical", f"Multiple origin ASNs were observed ({', '.join('AS' + str(x) for x in origins)}). Validate authorization and RPKI immediately."
    elif withdrawals and announcements:
        severity, finding = "warning", f"The prefix was withdrawn by {len(withdrawals)} observation peers and later announced again. This is consistent with a routing interruption or reconvergence event."
    elif withdrawals:
        severity, finding = "critical", f"{len(withdrawals)} withdrawals were observed without a recovery announcement in the selected window."
    elif not events:
        severity, finding = "unknown", "No matching BGP updates were returned. This does not prove that the prefix remained reachable; inspect RIB state and data-source coverage."

    return {
        "prefix": prefix, "mode": mode, "source_note": source_note,
        "severity": severity, "finding": finding,
        "metrics": {"events": len(events), "announcements": len(announcements), "withdrawals": len(withdrawals), "collectors": len(collectors), "peers": len(peers), "origins": len(origins)},
        "origins": origins, "collectors": collectors,
        "paths": [{"path": path, "count": count} for path, count in paths.most_common(8)],
        "timeline": [{"time": key, **timeline[key]} for key in sorted(timeline)],
        "events": sorted(events, key=lambda e: e["timestamp"]),
    }
