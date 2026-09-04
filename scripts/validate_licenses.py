# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_LICENSE = "Apache-2.0"
EXPECTED_BASE_IMAGE = (
    "caida/bgpstream:2.3.0@sha256:"
    "d808116911c107926451f882295d85c80940285791ff38c7e6999976d355e3d4"
)
EXPECTED_PYTHON_RUNTIME = {
    "fastapi": ("FastAPI", "0.141.1", "MIT"),
    "starlette": ("Starlette", "1.6.0", "BSD-3-Clause"),
    "uvicorn": ("Uvicorn", "0.52.4", "BSD-3-Clause"),
    "httpx": ("HTTPX", "0.28.1", "BSD-3-Clause"),
    "pydantic": ("Pydantic", "2.13.5", "MIT"),
}
REQUIRED = [
    "LICENSE",
    "NOTICE",
    "THIRD_PARTY_NOTICES.md",
    "LICENSES/CAIDA-BGPStream-BSD-2-Clause.txt",
    "docs/licensing.md",
    "requirements.txt",
]


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    raise SystemExit(1)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def normalize_whitespace(value: str) -> str:
    return " ".join(value.split())


def runtime_requirements() -> dict[str, str]:
    found: dict[str, str] = {}
    for raw_line in read("requirements.txt").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "==" not in line:
            fail(f"runtime dependency is not exactly pinned: {line}")
        package_spec, version = line.split("==", 1)
        package = package_spec.split("[", 1)[0].strip().lower()
        if package in found:
            fail(f"duplicate runtime dependency: {package}")
        found[package] = version.strip()
    return found


for path in REQUIRED:
    if not (ROOT / path).is_file():
        fail(f"missing licensing file: {path}")

apache = read("LICENSE")
for marker in [
    "Apache License",
    "Version 2.0, January 2004",
    "2. Grant of Copyright License.",
    "3. Grant of Patent License.",
    "4. Redistribution.",
    "END OF TERMS AND CONDITIONS",
    "APPENDIX: How to apply the Apache License to your work.",
]:
    if marker not in apache:
        fail(f"Apache-2.0 license marker missing: {marker}")

caida = read("LICENSES/CAIDA-BGPStream-BSD-2-Clause.txt")
for marker in [
    "Copyright (C) 2014 The Regents of the University of California.",
    "Redistribution and use in source and binary forms",
    'THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"',
]:
    if marker not in caida:
        fail(f"CAIDA BSD notice marker missing: {marker}")

notice = normalize_whitespace(read("NOTICE"))
for marker in [
    "BGP Incident Analyzer",
    "CAIDA BGPStream",
    "The Regents of the University of California",
    "THIRD_PARTY_NOTICES.md",
]:
    if marker not in notice:
        fail(f"NOTICE marker missing: {marker}")

third_party = read("THIRD_PARTY_NOTICES.md")
for marker in [EXPECTED_BASE_IMAGE, "BSD-2-Clause", "libwandio", "LGPL v3"]:
    if marker not in third_party:
        fail(f"third-party notice marker missing: {marker}")

requirements = runtime_requirements()
if set(requirements) != set(EXPECTED_PYTHON_RUNTIME):
    missing = sorted(set(EXPECTED_PYTHON_RUNTIME) - set(requirements))
    unexpected = sorted(set(requirements) - set(EXPECTED_PYTHON_RUNTIME))
    details = []
    if missing:
        details.append("missing=" + ",".join(missing))
    if unexpected:
        details.append("unexpected=" + ",".join(unexpected))
    fail(
        "runtime dependency set changed; review third-party licensing and update "
        "the license validator (" + "; ".join(details) + ")"
    )

for package, (display_name, expected_version, license_id) in EXPECTED_PYTHON_RUNTIME.items():
    actual_version = requirements[package]
    if actual_version != expected_version:
        fail(
            f"runtime dependency {package} changed from {expected_version} to "
            f"{actual_version}; re-verify its license before updating notices"
        )
    marker = f"| {display_name} | {actual_version} | {license_id} |"
    if marker not in third_party:
        fail(f"third-party dependency row missing or stale: {marker}")

licensing_doc = read("docs/licensing.md")
for marker in [
    "Apache-2.0",
    "Container distribution boundary",
    "LGPL",
    "THIRD_PARTY_NOTICES.md",
    "Section 5",
]:
    if marker not in licensing_doc:
        fail(f"licensing documentation marker missing: {marker}")

readme = read("README.md")
for marker in ["Apache License 2.0", "THIRD_PARTY_NOTICES.md", "docs/licensing.md"]:
    if marker not in readme:
        fail(f"README licensing marker missing: {marker}")

contributing = read("CONTRIBUTING.md")
for marker in ["Apache License 2.0", "Section 5", "THIRD_PARTY_NOTICES.md"]:
    if marker not in contributing:
        fail(f"contribution licensing marker missing: {marker}")

package = json.loads(read("package.json"))
if package.get("license") != EXPECTED_LICENSE:
    fail("package.json license must be Apache-2.0")

lock = json.loads(read("package-lock.json"))
missing_node_licenses = sorted(
    name
    for name, metadata in lock.get("packages", {}).items()
    if name and isinstance(metadata, dict) and not metadata.get("license")
)
if missing_node_licenses:
    fail(
        "package-lock.json is missing published license metadata for: "
        + ", ".join(missing_node_licenses)
    )

dockerfile = read("Dockerfile")
for marker in [
    'org.opencontainers.image.licenses="Apache-2.0"',
    'org.opencontainers.image.source="https://github.com/yuvalg72/BGP_Incident_Analyzer"',
    "COPY LICENSE NOTICE THIRD_PARTY_NOTICES.md /usr/share/licenses/bgp-incident-analyzer/",
    "COPY LICENSES /usr/share/licenses/bgp-incident-analyzer/LICENSES",
]:
    if marker not in dockerfile:
        fail(f"Dockerfile licensing marker missing: {marker}")

print(
    "License validation passed: Apache-2.0 project license, CAIDA notice, "
    "runtime dependency notices, machine-readable package/container metadata, "
    "and distribution documentation are aligned"
)
