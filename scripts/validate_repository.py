from __future__ import annotations

import json
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / "docs" / "images"
EXPECTED_PORT = "17991"
EXPECTED_APP_VERSION = "0.2.0"
EXPECTED_POC_DECISION_DATE = "31/10/2026"
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
    "POC decision checkpoint",
    "Operational boundaries",
    "Validation",
    "CI/CD",
    "Maintenance",
    "License",
]:
    if heading.lower() not in readme.lower():
        fail(f"README does not document: {heading}")

for marker in [
    "proof of concept",
    "the project remains in the `0.x` lifecycle",
    "not presented as a production-ready managed product",
    EXPECTED_POC_DECISION_DATE,
    "prefix any",
    "prefix more",
    "demonstration dataset always uses",
    "first 500 matching events",
]:
    if marker not in readme.lower():
        fail(f"README POC/runtime marker missing: {marker}")

security = read("SECURITY.md")
for marker in [
    "proof of concept",
    "`0.x` line",
    "not presented as a production-ready managed product",
]:
    if marker not in security.lower():
        fail(f"SECURITY.md POC lifecycle marker missing: {marker}")

# Production-facing sources must not advertise the current POC as v1.0.
# Tests may intentionally contain the legacy string in a negative assertion.
for path in ["app/main.py", "app/static/index.html"]:
    content = read(path)
    if "APP_VERSION = \"1.0.0\"" in content or "BGP Incident Analyzer v1.0" in content:
        fail(f"current-version 1.0 marker remains in {path}")

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
    f'APP_VERSION = "{EXPECTED_APP_VERSION}"',
    'ConfigDict(extra="forbid")',
    'Field(\n        default_factory=lambda: ["ris", "routeviews"]',
    '"/api/ready"',
    '"Content-Security-Policy"',
    '"Cache-Control", "no-store"',
    'mode: Literal["auto", "live", "demo"] = "live"',
    "DEMO_PREFIX",
    "_attach_query_context",
]:
    if marker not in main:
        fail(f"application safety/version marker missing: {marker}")

tests = read("tests/test_app.py")
if f'"version": "{EXPECTED_APP_VERSION}"' not in tests:
    fail("API tests do not assert the expected POC application version")
for marker in [
    "test_demo_analysis_is_never_labeled_as_requested_prefix",
    "test_auto_fallback_keeps_demo_prefix_distinct",
    "BGP Incident Analyzer v0.2.0",
    'assert "BGP Incident Analyzer v1.0" not in response.text',
]:
    if marker not in tests:
        fail(f"API regression coverage marker missing: {marker}")

changelog = read("CHANGELOG.md")
for marker in ["proof of concept", f"[{EXPECTED_APP_VERSION}]", EXPECTED_POC_DECISION_DATE]:
    if marker not in changelog.lower():
        fail(f"CHANGELOG POC/version marker missing: {marker}")

analyzer = read("app/analyzer.py")
for marker in [
    "BGP_ANALYZER_QUERY_TIMEOUT_SECONDS",
    "BGP_ANALYZER_MAX_EVENTS",
    'fields[1] not in {"A", "W"}',
    "_EventLimitExceeded",
    "except asyncio.CancelledError:",
    "class ResourceTarget",
    'bgp_filter=f"prefix any {host_prefix}"',
    'bgp_filter=f"prefix more {canonical}"',
    '"-f",',
]:
    if marker not in analyzer:
        fail(f"analyzer safety/filter marker missing: {marker}")
if '"-k",' in analyzer:
    fail("legacy exact/more-specific -k prefix targeting remains in app/analyzer.py")

analyzer_tests = read("tests/test_analyzer.py")
for marker in [
    "test_parse_resource_bare_ip_uses_prefix_any_not_host_exact",
    "prefix any 8.8.8.8/32",
    "test_collect_live_uses_bgpstream_filter_expression",
    "test_summarize_mixed_updates_does_not_claim_recovery_order",
]:
    if marker not in analyzer_tests:
        fail(f"analyzer regression coverage marker missing: {marker}")

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

package = json.loads(read("package.json"))
if package.get("license") != "Apache-2.0":
    fail("package.json license metadata is not Apache-2.0")

index = read("app/static/index.html")
for marker in [
    '<html lang="en" dir="ltr">',
    '<meta name="viewport"',
    '<meta name="description"',
    '<title>BGP Incident Analyzer</title>',
    'class="skip-link"',
    'id="source-state-text"',
    '<option value="live">Live only</option><option value="auto">Auto fallback</option>',
    f"BGP Incident Analyzer v{EXPECTED_APP_VERSION}",
    'id="event-count-note"',
]:
    if marker not in index:
        fail(f"static UI accessibility/version marker missing: {marker}")

app_js = read("app/static/app.js")
for marker in [
    "refreshReadiness",
    'fetch("/api/ready"',
    "textContent",
    "EVENT_TABLE_LIMIT = 500",
    "BGPReader runtime ready",
    "Export JSON includes all collected events",
]:
    if marker not in app_js:
        fail(f"static UI readiness/disclosure marker missing: {marker}")

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
    f"status=hardened-public-POC, version={EXPECTED_APP_VERSION}, port={EXPECTED_PORT}, "
    f"decision-checkpoint={EXPECTED_POC_DECISION_DATE}, host-safe BGPStream filters, "
    f"loopback-safe Compose bind, pinned CAIDA BGPStream 2.3.0 base, "
    f"Apache-2.0 licensing gate, 4 CI jobs, {len(runtime_requirements)} runtime dependencies "
    f"plus pinned dev tooling, {len(svgs)} SVG/PNG pairs"
)
