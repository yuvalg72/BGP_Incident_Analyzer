from __future__ import annotations

import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / "docs" / "images"
REQUIRED = [
    "README.md", "SECURITY.md", "CHANGELOG.md", ".gitignore",
    ".gitattributes", ".editorconfig", "Dockerfile", "docker-compose.yml",
]


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    raise SystemExit(1)


for required in REQUIRED:
    if not (ROOT / required).is_file():
        fail(f"missing required file: {required}")

readme = (ROOT / "README.md").read_text(encoding="utf-8")
for heading in ["Project status", "Quick start", "Architecture", "Success criteria", "Operational boundaries", "Validation", "Maintenance"]:
    if heading.lower() not in readme.lower():
        fail(f"README does not document: {heading}")

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

print(f"Repository validation passed: {len(svgs)} SVG/PNG pairs checked")

