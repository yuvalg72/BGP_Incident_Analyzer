# Contributing

This repository is maintained as a self-hosted BGP incident-analysis application. Keep changes focused on reproducibility, routing-evidence quality, operator usability, security, deployment safety or documentation accuracy.

## Before opening a pull request

1. Do not include customer identifiers, production IP addressing, credentials, raw configurations or incident evidence.
2. Use documentation-only IP ranges and private-use ASNs in tests and examples.
3. Run the validation commands documented in `README.md`, including `python scripts/validate_licenses.py`.
4. Regenerate PNG diagrams after changing an SVG source.
5. Describe operator impact, security implications, tests performed and remaining limitations.
6. Add deterministic regression coverage for parser, validation, timeout, limit, fallback or deployment behavior changes.
7. Identify any new third-party code, dependency, asset, dataset or generated artifact and update `THIRD_PARTY_NOTICES.md` when its license or attribution requires it.

## Change scope

- Keep live data access read-only.
- Preserve the visible distinction between live and demonstration results.
- Do not present control-plane observations as proof of packet forwarding.
- Preserve loopback-only default exposure unless a change has a documented security rationale.
- Do not weaken query bounds, container isolation or browser security headers without explicit justification and tests.

## Licensing of contributions

BGP Incident Analyzer is licensed under the Apache License 2.0. Unless you explicitly state otherwise, any contribution intentionally submitted for inclusion in this repository is provided under Apache License 2.0 Section 5, without additional terms or conditions.

Only submit material that you have the right to contribute. Do not remove existing copyright, attribution, patent or license notices from third-party material. If a change incorporates third-party material or changes the dependency/distribution boundary, preserve its original license terms and update `NOTICE`, `THIRD_PARTY_NOTICES.md`, `LICENSES/`, or `docs/licensing.md` as applicable.

A pull request that cannot establish a compatible and reviewable licensing basis is not release-ready even if its functional tests pass.

Use GitHub Issues for reproducible defects and bounded enhancement proposals. Follow `SECURITY.md` for suspected vulnerabilities.
