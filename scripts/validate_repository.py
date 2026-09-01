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
    ".gitignore",
    ".gitattributes",
    ".editorconfig",
    ".github/dependabot.yml",
    ".github/pull_request_template.md",
    ".github/workflows/ci.yml",
    "Dockerfile",
    "docker-compose.yml",
    "requirements.txt",
    "package.json",
    "package-lock.json",
    "pytest.ini",
    "tests/test_app.py",
    "tests/test_analyzer.py",
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
]:
    if marker not in dockerfile:
        fail(f"Dockerfile hardening marker missing: {marker}")

compose = read("docker-compose.yml")
expected_mapping = f"${{BGP_ANALYZER_PORT:-{EXPECTED_PORT}}}:{EXPECTED_PORT}"
if expected_mapping not in compose:
    fail("docker-compose.yml does not use the expected configurable host-port mapping")

workflow = read(".github/workflows/ci.yml")
for job in ["quality", "tests", "container", "security"]:
    if f"  {job}:\n" not in workflow:
        fail(f"CI job is missing: {job}")
for marker in ["contents: read", "cancel-in-progress: true", "timeout-minutes:"]:
    if marker not in workflow:
        fail(f"CI control is missing: {marker}")

requirements = [
    line.strip()
    for line in read("requirements.txt").splitlines()
    if line.strip() and not line.lstrip().startswith("#")
]
for requirement in requirements:
    if "==" not in requirement:
        fail(f"Python dependency is not exactly pinned: {requirement}")

index = read("app/static/index.html")
for marker in [
    '<html lang="en" dir="ltr">',
    '<meta name="viewport"',
    '<meta name="description"',
    '<title>BGP Incident Analyzer</title>',
    'class="skip-link"',
]:
    if marker not in index:
        fail(f"static UI accessibility/metadata marker missing: {marker}")

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
    f"port={EXPECTED_PORT}, pinned CAIDA BGPStream 2.3.0 base, 4 CI jobs, "
    f"{len(requirements)} pinned Python dependencies, {len(svgs)} SVG/PNG pairs"
)
