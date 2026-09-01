# BGP Incident Analyzer

An operational web interface for network and security teams investigating BGP announcements, withdrawals, origin changes and AS-path visibility using CAIDA BGPStream data from RIPE RIS and Route Views.

> **Project status:** Experimental proof of concept. Suitable for controlled internal evaluation, not direct Internet exposure.

## Quick start

Requirements: Docker Engine with the Compose plugin and outbound HTTPS access.

```bash
docker compose up -d --build
```

Open `http://localhost:8080`.

The default **Auto fallback** mode uses live `bgpreader` data and shows the included demonstration dataset if the live collector cannot run. Select **Live only** when a fallback must never be used. Every result visibly identifies its mode and source.

## Workflow

1. Enter an IPv4/IPv6 address or CIDR prefix.
2. Select the UTC incident window, up to seven days.
3. Select RIPE RIS, Route Views, or both.
4. Run the analysis.
5. Review the finding, event distribution, observed AS paths, and raw evidence.
6. Copy the incident summary or export the complete JSON result.

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

Without `bgpreader`, local development still supports Demonstration and Auto fallback modes. Live mode requires the CAIDA `bgpstream` package.

## API

Interactive API documentation is available at `http://localhost:8080/api/docs`.

```bash
curl -X POST http://localhost:8080/api/analyze \
  -H 'Content-Type: application/json' \
  -d '{"resource":"192.0.2.10","start":"2026-08-31T20:55:00Z","end":"2026-08-31T21:55:00Z","projects":["ris","routeviews"],"mode":"auto"}'
```

## Operational boundaries

- BGPStream provides public control-plane observations, not packet-path proof.
- A missing update is not proof of uninterrupted reachability.
- Correlate findings with MTR, traceroute, packet captures, FortiGate logs, provider telemetry and ticket timestamps.
- The service has no authentication in this POC. Bind it to a trusted management network or place it behind an authenticated reverse proxy before shared deployment.
- Query windows are limited to seven days and each live query has a 90-second execution limit.

## Validation

```bash
pytest -q
python -m compileall -q app
node --check app/static/app.js
```

A successful test run returns three passing API tests. For deployment validation, confirm that `docker compose up -d --build` completes and that `GET /api/health` returns `{"status":"ok"}`.

## Maintenance

This project is currently maintained as an experimental proof of concept. Use GitHub Issues for reproducible defects and enhancement proposals. Report suspected security vulnerabilities using the private process in [SECURITY.md](SECURITY.md).
