# BGP Incident Analyzer

An operational web interface for network and security teams investigating BGP announcements, withdrawals, origin changes and AS-path visibility using CAIDA BGPStream data from RIPE RIS and Route Views.

> **Project status:** Experimental proof of concept. Suitable for controlled internal evaluation, not direct Internet exposure.

## Objective and success criteria

The POC tests whether public BGP observations can be turned into a concise, repeatable incident record without requiring analysts to manually download and parse collector files.

The experiment is successful when an operator can:

- submit a valid IP address or prefix and bounded UTC window;
- obtain matching announcements, withdrawals, origin ASNs and AS paths;
- identify whether live data or demonstration fallback produced the result;
- export a readable summary and complete JSON evidence;
- reproduce the API tests and container deployment from this repository.

Assumptions: outbound access to RIPEstat and CAIDA data sources is available, public collectors observe the relevant prefix, and control-plane evidence is correlated with operational telemetry.

**Decision date:** Review production suitability by `01/12/2026`. Until then, the repository remains an experimental POC.

## Architecture

![BGP Incident Analyzer architecture](docs/images/architecture.png)

The service resolves a resource, queries CAIDA BGPStream, validates and summarizes the returned control-plane events, and presents the evidence in a browser workspace. See the [architecture and security boundaries](docs/architecture.md) or open the [scalable SVG diagram](docs/images/architecture.svg).

The application image is layered on CAIDA's official BGPStream 2.3.0 container image. The Dockerfile pins its manifest digest rather than relying on a floating `latest` tag.

## Analysis workflow

![BGP incident analysis workflow](docs/images/analysis-flow.png)

The workflow keeps the incident window in UTC and preserves a visible distinction between live and demonstration data. Open the [scalable SVG workflow](docs/images/analysis-flow.svg).

## Quick start

Requirements: Docker Engine with the Compose plugin and outbound HTTPS access.

```bash
docker compose up -d --build
```

Open `http://localhost:17991`.

The default host port is intentionally a non-standard unprivileged port. To use a different host-side port while keeping the container on `17991`:

```bash
BGP_ANALYZER_PORT=19091 docker compose up -d --build
```

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
uvicorn app.main:app --reload --port 17991
```

Without `bgpreader`, local development still supports Demonstration and Auto fallback modes. Live mode requires the CAIDA `bgpstream` package.

## API

Interactive API documentation is available at `http://localhost:17991/api/docs`.

```bash
curl -X POST http://localhost:17991/api/analyze \
  -H 'Content-Type: application/json' \
  -d '{"resource":"192.0.2.10","start":"2026-08-31T20:55:00Z","end":"2026-08-31T21:55:00Z","projects":["ris","routeviews"],"mode":"auto"}'
```

## Operational boundaries

- BGPStream provides public control-plane observations, not packet-path proof.
- A missing update is not proof of uninterrupted reachability.
- Correlate findings with MTR, traceroute, packet captures, FortiGate logs, provider telemetry and ticket timestamps.
- The service has no authentication in this POC. Bind it to a trusted management network or place it behind an authenticated reverse proxy before shared deployment.
- Query windows are limited to seven days and each live query has a 90-second execution limit.
- The container runs as unprivileged UID `10001` and is intended to remain read-only except for the Compose `/tmp` tmpfs.
- The BGPStream base image is pinned by digest. Updating that digest is an explicit dependency-maintenance change and should be validated by the container CI gate.

## Validation

Core local validation:

```bash
pytest -q
python -m compileall -q app tests scripts
node --check app/static/app.js
python scripts/validate_repository.py
```

Optional local checks matching CI:

```bash
python -m pip install ruff==0.12.8 pip-audit==2.9.0
ruff check app tests scripts
pip-audit -r requirements.txt
docker compose config -q
docker build -t bgp-incident-analyzer .
```

For deployment validation, confirm that `docker compose up -d --build` completes and that `GET /api/health` on port `17991` returns `{"status":"ok"}`.

SVG files in `docs/images/` are the editable sources. PNG files are generated from them for consistent GitHub rendering:

```bash
npm ci
npm run render:diagrams
```

## CI/CD

The primary GitHub Actions workflow runs on pull requests, pushes to `main`, and manual dispatch. It uses read-only repository permissions, cancellation of superseded runs, and explicit job timeouts.

The workflow is split into four non-overlapping validation jobs:

- **Quality:** Python compilation, Ruff linting, JavaScript syntax, repository policy validation, and deterministic SVG-to-PNG comparison.
- **Tests:** FastAPI and analyzer unit tests covering API validation, BGPReader parsing, severity classification, and timeline aggregation.
- **Container:** Compose validation, Docker build, non-root UID verification, `/api/health` smoke test, and `/api/docs` smoke test on port `17991`.
- **Security:** dependency vulnerability auditing with `pip-audit` against the exactly pinned Python requirements.

CI performs validation only. It does not publish images or deploy this experimental POC.

## Maintenance

This project is currently maintained as an experimental proof of concept. Use GitHub Issues for reproducible defects and enhancement proposals. Report suspected security vulnerabilities using the private process in [SECURITY.md](SECURITY.md).

Dependency updates are managed through Dependabot for both Python and npm ecosystems. Material changes should use a branch and pull request and must preserve the distinction between live evidence and demonstration data.

## License

No open-source license is currently granted. Public visibility does not grant permission to copy, modify, or redistribute the code. Add an explicit license before encouraging external reuse or promoting the project beyond the current POC status.
