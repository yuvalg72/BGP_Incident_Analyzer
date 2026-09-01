# Architecture

## System boundary

BGP Incident Analyzer is a read-only analysis service. It queries public BGP control-plane observations and does not connect to routers, FortiGate devices, customer environments, or routing sessions.

![BGP Incident Analyzer architecture](images/architecture.png)

[Open the scalable SVG version](images/architecture.svg)

## Components

| Component | Responsibility | Trust boundary |
| --- | --- | --- |
| Browser workspace | Collect query parameters and render evidence | Treat all displayed data as untrusted text |
| FastAPI service | Validate requests, orchestrate collection and summarize events | Trusted application process |
| RIPEstat | Resolve an IP address to its covering prefix | External public API |
| CAIDA BGPStream | Retrieve RIPE RIS and Route Views records | External public data source |
| Demo dataset | Keep the interface testable when live collection is unavailable | Documentation-only addresses and private-use ASNs |

## Analysis workflow

![BGP incident analysis workflow](images/analysis-flow.png)

[Open the scalable SVG version](images/analysis-flow.svg)

## Security assumptions

- The service runs on a trusted management network or behind an authenticated reverse proxy.
- Outbound HTTPS is permitted only to required public data sources.
- Query results are operational evidence, not authoritative proof of packet forwarding.
- No customer identifiers, credentials, private configurations or production logs are stored in this repository.

## Production hardening backlog

Before production use, add authentication and authorization, structured audit logging, rate limiting, persistent evidence storage, deployment-specific TLS, dependency scanning, and an operational backup and recovery design.

