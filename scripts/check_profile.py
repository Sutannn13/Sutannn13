#!/usr/bin/env python3
"""Lightweight self-check verifying README asset links, APNG headers, and hygiene."""

from __future__ import annotations

import re
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"


def main() -> None:
    md = README.read_text(encoding="utf-8")
    assert "\u2014" not in md, "Em dash found in README.md"

    # Every relative asset referenced in README must exist and be non-empty
    refs = sorted(set(re.findall(r"\./assets/[A-Za-z0-9._/-]+", md)))
    assert refs, "No ./assets references found in README.md"
    for ref in refs:
        p = ROOT / ref.lstrip("./")
        assert p.is_file() and p.stat().st_size > 0, f"Missing or empty asset: {ref}"

    # Verify APNG animation header (acTL) on both 3D hero banners
    for name in ("hero-dark.png", "hero-light.png"):
        raw = (ROOT / "assets" / name).read_bytes()
        assert raw[:8] == b"\x89PNG\r\n\x1a\n", f"{name}: invalid PNG signature"
        assert b"acTL" in raw[:128], f"{name}: missing APNG acTL chunk"
        idx = raw.index(b"acTL")
        frames, plays = struct.unpack(">II", raw[idx + 4:idx + 12])
        assert frames >= 24 and plays == 0, f"{name}: unexpected APNG frames={frames} plays={plays}"
        assert len(raw) < 4_500_000, f"{name}: exceeds 4.5MB GitHub fast-load budget ({len(raw)} bytes)"

    # Verify all authored SVGs are valid XML, honor prefers-reduced-motion, and avoid em dashes
    for svg in sorted((ROOT / "assets").glob("*.svg")):
        txt = svg.read_text(encoding="utf-8")
        ET.fromstring(txt)
        assert "prefers-reduced-motion" in txt, f"{svg.name}: missing prefers-reduced-motion rule"
        if not svg.name.startswith("snake-"):
            assert "\u2014" not in txt, f"{svg.name}: em dash found"

    print(f"PASS: verified {len(refs)} README assets, 2 animated 3D APNG heroes, and all SVG guards.")


if __name__ == "__main__":
    main()
