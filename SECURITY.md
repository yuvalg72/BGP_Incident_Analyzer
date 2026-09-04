# Security Policy

## Supported status

The 1.x line is a self-hosted operational application. The default Docker Compose configuration binds to `127.0.0.1` and is designed to be placed behind normal management-plane controls.

The application does not include built-in user authentication. Do not expose its application port directly to an untrusted network. Internet-facing deployment requires an authenticated reverse proxy, TLS, request rate limiting and host/network firewall restrictions.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Report it privately through GitHub's private vulnerability reporting feature when available, or contact the repository owner directly through their verified GitHub profile.

Include the affected version, reproduction steps, impact, and any suggested mitigation. Do not include real credentials, customer information, production IP addressing, raw configurations or private incident evidence.

## Deployment boundary

- Keep the default loopback bind unless a specific management interface is required.
- Restrict outbound access to the data sources required for BGP analysis.
- Treat `GET /api/health` as liveness and `GET /api/ready` as live-analysis readiness.
- Preserve the application query timeout and event-count limits unless a tested operational requirement justifies a bounded override.
- Keep the container non-root, read-only, capability-free and protected by `no-new-privileges`.
- Terminate TLS and enforce authentication/rate limiting at the reverse proxy for shared access.
