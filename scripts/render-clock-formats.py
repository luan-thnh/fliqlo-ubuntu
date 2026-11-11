#!/usr/bin/env python3
"""Render deterministic, full-resolution clock formats using the real GTK clock renderer.

These images use native Cairo/Pango vector text and avoid screenshot resizing/blur.
They are documentation previews, not screenshots of the entire GNOME desktop.
"""
from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "native"))

import cairo
from model import clock_parts
from render import paint

ASSETS = ROOT / "docs" / "assets"
WIDTH, HEIGHT = 1920, 1080
SAMPLE = datetime(2026, 1, 1, 0, 0)
OPTIONS = {
    "scale": 100,
    "brightness": 100,
    "background": True,
    "font": "DejaVu Sans",
}
CASES = [
    ("clock-format-12h.png", 0, ("12", "00", "AM")),
    ("clock-format-24h-short.png", 1, ("0", "00", "")),
    ("clock-format-24h-padded.png", 2, ("00", "00", "")),
]


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    for filename, format_id, expected in CASES:
        current = clock_parts(SAMPLE, format_id)
        if current != expected:
            raise AssertionError(f"Wrong time for mode {format_id}: {current!r}")
        surface = cairo.ImageSurface(cairo.FORMAT_RGB24, WIDTH, HEIGHT)
        cr = cairo.Context(surface)
        cr.set_antialias(cairo.ANTIALIAS_BEST)
        paint(cr, WIDTH, HEIGHT, current, None, 1, OPTIONS)
        surface.flush()
        path = ASSETS / filename
        surface.write_to_png(str(path))
        print(f"Rendered {path.relative_to(ROOT)} ({WIDTH}x{HEIGHT}, mode {format_id})")


if __name__ == "__main__":
    main()
