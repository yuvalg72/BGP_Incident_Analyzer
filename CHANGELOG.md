# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.2.0] - 2026-09-04

### Changed

- Corrected bare-IP targeting so IPv4/IPv6 host input uses a BGPStream `prefix any` filter instead of being treated as an exact `/32` or `/128`; RIPEstat is now display enrichment rather than a prerequisite for correct live targeting.
- Explicit CIDR input now uses BGPStream `prefix more` semantics so exact and more-specific update visibility remains intentional and testable.
- Isolated the fixed demonstration dataset from live query identity so Demo and Auto fallback can no longer present `192.0.2.0/24` events as if they were evidence for the requested resource.
- Made withdrawal/announcement findings chronology-neutral and stopped describing event counts as unique peers or asserting recovery ordering that was not proven by the selected window.
- Corrected the browser footer from `v1.0` to `v0.2.0`, clarified local BGPReader readiness wording, and made the 500-row browser event-table limit visible while preserving full JSON export.
- Added regression tests and repository validation for host/prefix filter semantics, demo isolation, UI version consistency, POC decision checkpoint, and event-table disclosure.
- Added a POC decision checkpoint of `31/10/2026` before any `1.0.0` designation.
- Aligned the release candidate with the project's intended lifecycle as a hardened public proof of concept and set the application/API version to `0.2.0` instead of presenting the project as a production-style `1.x` release.
- Licensed the project's first-party source code and documentation under Apache License 2.0, with the canonical license text in `LICENSE`, repository `NOTICE`, third-party attribution in `THIRD_PARTY_NOTICES.md`, and a retained CAIDA BGPStream BSD license copy under `LICENSES/`.
- Added machine-readable Apache-2.0 metadata to the Node package and OCI container image, copied licensing materials into the built container, documented contribution and binary-distribution licensing boundaries, and added deterministic license validation to CI.
- Changed the default application port from 8080 to 17991, with a configurable host-side Compose port.
- Hardened the container to run as unprivileged UID 10001 and rebased it on CAIDA's official BGPStream 2.3.0 image with a pinned manifest digest.
- Made Docker Compose bind to `127.0.0.1` by default, added init-based subprocess reaping, dropped Linux capabilities, preserved `no-new-privileges`, and kept the filesystem read-only except for `/tmp`.
- Added separate liveness (`/api/health`) and BGPReader runtime readiness (`/api/ready`) endpoints and switched the container health check to readiness.
- Added strict timezone-aware API validation, duplicate-project rejection, unknown-field rejection, and safe default construction for project selections.
- Changed the default query mode from Auto fallback to Live only so operational analysis fails closed instead of silently substituting demonstration evidence.
- Added browser security headers including CSP, frame blocking, no-sniff, no-referrer and restrictive permissions policy.
- Limited live analysis with bounded query timeout and event-count controls, and added subprocess cleanup on timeout, event-limit abort and request cancellation.
- Corrected BGPReader parsing so only announcement and withdrawal elements are accepted; RIB and state elements are no longer eligible for withdrawal accounting.
- Upgraded FastAPI to 0.141.1, Pydantic to 2.13.5, explicitly pinned Starlette 1.6.0, preserved Uvicorn 0.52.4, and upgraded pytest to 9.1.1 after dependency auditing.
- Moved pytest out of the production dependency set into `requirements-dev.txt` so the runtime image contains only application dependencies.
- Expanded CI into separate quality, test, container, and dependency-security jobs.
- Added Docker build, non-root runtime, BGPStream readiness, liveness, API documentation and security-header smoke tests.
- Added Ruff linting and `pip-audit` dependency vulnerability checks.
- Expanded API and analyzer tests to cover strict validation, BGPReader parsing, state/RIB rejection, event limits, timeout cleanup, severity classification and timeline aggregation.
- Extended deterministic repository validation to enforce port consistency, CI controls, dependency pinning, pinned CAIDA base image, loopback exposure, readiness checks, container hardening, POC lifecycle/version consistency and static UI metadata.
- Added a pull request template with validation, security, risk, rollback, and licensing gates.

## [0.1.0] - 2026-09-01

### Added

- Initial FastAPI web application for BGP incident analysis.
- CAIDA BGPStream integration through `bgpreader` with RIPE RIS and Route Views filters.
- Demonstration fallback dataset and explicit live/demo source labeling.
- Announcement, withdrawal, origin-ASN, AS-path, collector and timeline summaries.
- Browser interface with JSON export and incident-summary copy action.
- Docker and Docker Compose deployment.
- Architecture and analysis-flow documentation with SVG and PNG diagrams.
- Initial tests, CI, dependency automation, security policy and contribution guidance.
