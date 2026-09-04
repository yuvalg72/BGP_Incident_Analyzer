from __future__ import annotations

import struct
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / "docs" / "images"
EXPECTED_PORT = "17991"
EXPECTED_BGPSTREAM_BASE = (
    "FROM caida/bgpstream:2.3.0@sha256:"
    "d808116911c107926451f882295d85c80940285791ff38c7e6999976d355e3d4"
)
REQUIRED = [
    "README.md",
    "SECURITY.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "NOTICE",
    "THIRD_PARTY_NOTICES.md",
    "LICENSES/CAIDA-BGPStream-BSD-2-Clause.txt",
    ".gitignore",
    ".gitattributes",
    ".editorconfig",
    ".github/dependabot.yml",
    ".github/pull_request_template.md",
    ".github/workflows/ci.yml",
    "Dockerfile",
    "docker-compose.yml",
    "requirements.txt",
    "requirements-dev.txt",
    "package.json",
    "package-lock.json",
    "pytest.ini",
    "app/main.py",
    "app/analyzer.py",
    "app/static/index.html",
    "app/static/app.js",
    "tests/test_app.py",
    "tests/test_analyzer.py",
    "docs/architecture.md",
    "docs/licensing.md",
    "scripts/validate_licenses.py",
]


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    raise SystemExit(1)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


for required in REQUIRED:
    if not (ROOT / required).is_file():
        fail(f"missing required file: {required}")

readme = read("README.md")
for heading in [
    "Project status",
    "Quick start",
    "Architecture",
    "Success criteria",
    "Operational boundaries",
    "Validation",
    "CI/CD",
    "Maintenance",
    "License",
]:
    if heading.lower() not in readme.lower():
        fail(f"README does not document: {heading}")

for path in ["README.md", "Dockerfile", "docker-compose.yml", ".github/workflows/ci.yml"]:
    content = read(path)
    if "8080" in content:
        fail(f"legacy port 8080 remains in {path}")
    if EXPECTED_PORT not in content:
        fail(f"expected port {EXPECTED_PORT} is not documented in {path}")

dockerfile = read("Dockerfile")
for marker in [
    EXPECTED_BGPSTREAM_BASE,
    f"EXPOSE {EXPECTED_PORT}",
    "USER appuser",
    "--uid 10001 appuser",
    "/api/ready",
    "--no-server-header",
    'org.opencontainers.image.licenses="Apache-2.0"',
    "COPY LICENSE NOTICE THIRD_PARTY_NOTICES.md /usr/share/licenses/bgp-incident-analyzer/",
]:
    if marker not in dockerfile:
        fail(f"Dockerfile hardening/licensing marker missing: {marker}")

compose = read("docker-compose.yml")
expected_mapping = (
    f"${{BGP_ANALYZER_BIND:-127.0.0.1}}:"
    f"${{BGP_ANALYZER_PORT:-{EXPECTED_PORT}}}:{EXPECTED_PORT}"
)
if expected_mapping not in compose:
    fail("docker-compose.yml does not use the loopback-safe configurable port mapping")
for marker in [
    "init: true",
    "no-new-privileges:true",
    "cap_drop:",
    "- ALL",
    "read_only: true",
    "BGP_ANALYZER_QUERY_TIMEOUT_SECONDS",
    "BGP_ANALYZER_MAX_EVENTS",
]:
    if marker not in compose:
        fail(f"docker-compose.yml hardening marker missing: {marker}")

main = read("app/main.py")
for marker in [
    'ConfigDict(extra="forbid")',
    'Field(\n        default_factory=lambda: ["ris", "routeviews"]',
    '"/api/ready"',
    '"Content-Security-Policy"',
    '"Cache-Control", "no-store"',
    'mode: Literal["auto", "live", "demo"] = "live"',
]:
    if marker not in main:
        fail(f"application safety marker missing: {marker}")

analyzer = read("app/analyzer.py")
for marker in [
    "BGP_ANALYZER_QUERY_TIMEOUT_SECONDS",
    "BGP_ANALYZER_MAX_EVENTS",
    'fields[1] not in {"A", "W"}',
    "_EventLimitExceeded",
    "except asyncio.CancelledError:",
]:
    if marker not in analyzer:
        fail(f"analyzer safety marker missing: {marker}")

workflow = read(".github/workflows/ci.yml")
for job in ["quality", "tests", "container", "security"]:
    if f"  {job}:\n" not in workflow:
        fail(f"CI job is missing: {job}")
for marker in [
    "contents: read",
    "cancel-in-progress: true",
    "timeout-minutes:",
    "/api/ready",
    "x-content-type-options: nosniff",
    "python scripts/validate_licenses.py",
]:
    if marker not in workflow:
        fail(f"CI control is missing: {marker}")

runtime_requirements = [
    line.strip()
    for line in read("requirements.txt").splitlines()
    if line.strip() and not line.lstrip().startswith("#")
]
for requirement in runtime_requirements:
    if "==" not in requirement:
        fail(f"Runtime Python dependency is not exactly pinned: {requirement}")

dev_requirements = [
    line.strip()
    for line in read("requirements-dev.txt").splitlines()
    if line.strip() and not line.lstrip().startswith("#")
]
if "-r requirements.txt" not in dev_requirements:
    fail("requirements-dev.txt must include the runtime requirements")
for requirement in dev_requirements:
    if requirement.startswith("-r "):
        continue
    if "==" not in requirement:
        fail(f"Development Python dependency is not exactly pinned: {requirement}")

index = read("app/static/index.html")
for marker in [
    '<html lang="en" dir="ltr">',
    '<meta name="viewport"',
    '<meta name="description"',
    '<title>BGP Incident Analyzer</title>',
    'class="skip-link"',
    'id="source-state-text"',
    '<option value="live">Live only</option><option value="auto">Auto fallback</option>',
]:
    if marker not in index:
        fail(f"static UI accessibility/metadata marker missing: {marker}")

app_js = read("app/static/app.js")
for marker in ["refreshReadiness", 'fetch("/api/ready"', "textContent"]:
    if marker not in app_js:
        fail(f"static UI readiness/safety marker missing: {marker}")

svgs = sorted(IMAGES.glob("*.svg"))
if not svgs:
    fail("no SVG diagrams found")

for svg in svgs:
    try:
        root = ET.parse(svg).getroot()
    except ET.ParseError as exc:
        fail(f"invalid SVG {svg.name}: {exc}")
    if not root.findall("{http://www.w3.org/2000/svg}title"):
        fail(f"SVG lacks accessible title: {svg.name}")
    png = svg.with_suffix(".png")
    if not png.is_file():
        fail(f"missing PNG render for {svg.name}")
    data = png.read_bytes()[:24]
    if len(data) != 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        fail(f"invalid PNG signature: {png.name}")
    width, height = struct.unpack(">II", data[16:24])
    if width < 1000 or height < 500:
        fail(f"PNG render is unexpectedly small: {png.name} ({width}x{height})")
    if f"docs/images/{png.name}" not in readme:
        fail(f"README does not display {png.name}")

print(
    "Repository validation passed: "
    f"port={EXPECTED_PORT}, loopback-safe Compose bind, pinned CAIDA BGPStream 2.3.0 base, "
    f"Apache-2.0 licensing gate, 4 CI jobs, {len(runtime_requirements)} runtime dependencies "
    f"plus pinned dev tooling, {len(svgs)} SVG/PNG pairs"
)
