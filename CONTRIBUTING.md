# Contributing

This repository is maintained as a self-hosted BGP incident-analysis application. Keep changes focused on reproducibility, routing-evidence quality, operator usability, security, deployment safety or documentation accuracy.

## Before opening a pull request

1. Do not include customer identifiers, production IP addressing, credentials, raw configurations or incident evidence.
2. Use documentation-only IP ranges and private-use ASNs in tests and examples.
3. Run the validation commands documented in `README.md`.
4. Regenerate PNG diagrams after changing an SVG source.
5. Describe operator impact, security implications, tests performed and remaining limitations.
6. Add deterministic regression coverage for parser, validation, timeout, limit, fallback or deployment behavior changes.

## Change scope

- Keep live data access read-only.
- Preserve the visible distinction between live and demonstration results.
- Do not present control-plane observations as proof of packet forwarding.
- Preserve loopback-only default exposure unless a change has a documented security rationale.
- Do not weaken query bounds, container isolation or browser security headers without explicit justification and tests.

Use GitHub Issues for reproducible defects and bounded enhancement proposals. Follow `SECURITY.md` for suspected vulnerabilities.
