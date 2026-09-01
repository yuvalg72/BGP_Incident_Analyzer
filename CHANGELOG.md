# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changed

- Changed the default application port from 8080 to 17991, with a configurable host-side Compose port.
- Hardened the container to run as an unprivileged UID 10001 user.
- Rebased the application container on CAIDA's official BGPStream 2.3.0 image and pinned the manifest digest to avoid base-image tag drift.
- Upgraded FastAPI to 0.141.1, explicitly pinned Starlette 1.6.0, and upgraded pytest to 9.1.1 after dependency auditing identified known vulnerabilities in the previous dependency set.
- Expanded CI into separate quality, test, container, and dependency-security jobs.
- Added Docker build, non-root runtime, health endpoint, and API documentation smoke tests.
- Added Ruff linting and `pip-audit` dependency vulnerability checks.
- Expanded API and analyzer tests to cover input validation, BGPReader parsing, severity classification, and timeline aggregation.
- Extended deterministic repository validation to enforce the port, CI job set, pinned dependencies, pinned CAIDA base image, container hardening, and static UI metadata.
- Added a pull request template with validation, security, risk, and rollback gates.

## [0.1.0] - 2026-09-01

### Added

- FastAPI-based BGP incident analysis API.
- Responsive operational web interface.
- RIPE RIS and Route Views selection through BGPStream.
- Live, demonstration, and automatic fallback modes.
- Timeline, AS-path visibility, raw event evidence, summary copy, and JSON export.
- Docker and Docker Compose deployment.
- Automated API tests and GitHub Actions validation.
- Architecture and analysis workflow diagrams in SVG and generated PNG formats.
- Deterministic repository and diagram validation.
