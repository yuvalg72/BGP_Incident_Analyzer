# Architecture

## System boundary

BGP Incident Analyzer is a read-only analysis service. It queries public BGP control-plane observations and does not connect to routers, FortiGate devices, customer environments, or routing sessions.

![BGP Incident Analyzer architecture](images/architecture.png)

[Open the scalable SVG version](images/architecture.svg)

## Components

| Component | Responsibility | Trust boundary |
| --- | --- | --- |
| Browser workspace | Collect query parameters and render evidence | Treat all displayed data as untrusted text |
| FastAPI service | Validate requests, enforce query bounds, orchestrate collection and summarize events | Trusted application process |
| RIPEstat | Resolve an IP address to its covering prefix | External public API |
| CAIDA BGPStream | Retrieve RIPE RIS and Route Views update records through `bgpreader` | External public data source and subprocess |
| Demo dataset | Keep the interface testable when live collection is unavailable | Documentation-only addresses and private-use ASNs |

## Analysis workflow

![BGP incident analysis workflow](images/analysis-flow.png)

[Open the scalable SVG version](images/analysis-flow.svg)

## Runtime and failure boundaries

- `GET /api/health` is a liveness check for the FastAPI process.
- `GET /api/ready` additionally verifies that `bgpreader` is available for live analysis.
- Live queries are limited to a seven-day request window, a bounded execution timeout, and a bounded parsed-event count.
- Timeout, event-limit abort, or request cancellation terminates and reaps the `bgpreader` subprocess rather than allowing orphaned work to continue.
- Only BGP announcement (`A`) and withdrawal (`W`) elements are accepted for analysis. RIB and state elements are ignored rather than being classified as withdrawals.
- Auto mode may visibly fall back to the demonstration dataset when the live source is unavailable. Live-only mode returns an error instead.

## Security boundary

- Docker Compose binds the application to `127.0.0.1` by default. Binding to another address is an explicit deployment decision.
- The application has no built-in user authentication. Shared or Internet-facing access requires an authenticated reverse proxy, TLS, request rate limiting, and firewall restrictions.
- The container runs as UID `10001`, drops all Linux capabilities, enables `no-new-privileges`, uses a read-only root filesystem, and receives only a temporary `/tmp` filesystem.
- Browser responses apply a restrictive Content Security Policy, frame blocking, MIME sniffing protection, no-referrer behavior, and a restrictive permissions policy.
- Outbound network access is required for RIPEstat and CAIDA BGPStream data sources and should be restricted at the deployment layer where practical.
- Query results are operational control-plane evidence, not authoritative proof of packet forwarding.
- No customer identifiers, credentials, private configurations, or production logs are stored in this repository.

## Deployment responsibilities

The repository provides a hardened self-hosted application container, but it does not provide a complete Internet edge. Operators exposing the service beyond localhost or a trusted management network remain responsible for identity, TLS certificate lifecycle, reverse-proxy configuration, rate limiting, centralized logging, host patching, monitoring, backup of exported evidence if required, and incident-response procedures.
