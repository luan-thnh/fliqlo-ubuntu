#!/usr/bin/env python3
"""Build a dependency-free static landing page for GitHub Pages.

Usage:
    python3 scripts/build-website.py

Output: _site/ (HTML/CSS/JS + only the project's public demo assets).
"""
from html.parser import HTMLParser
from pathlib import Path
import shutil
import sys
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "website"
TARGET = ROOT / "_site"
IMAGES = ROOT / "docs" / "assets"
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.local_files = set()
        self.ids = set()
        self.anchors = set()
        self.images_without_alt = []
        self.buttons_without_text = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if data.get("id"):
            self.ids.add(data["id"])
        if tag == "img" and "alt" not in data:
            self.images_without_alt.append(data.get("src", "unknown"))
        for key in ("href", "src"):
            value = data.get(key, "")
            if not value:
                continue
            if value.startswith("#"):
                self.anchors.add(value[1:])
            elif not (value.startswith(("http:", "https:", "mailto:", "data:"))):
                self.local_files.add(value.split("#")[0].split("?")[0].removeprefix("./"))


def build():
    if not re.fullmatch(r"\d+\.\d+\.\d+", VERSION):
        raise ValueError(f"Invalid project version {VERSION!r}")

    if TARGET.exists():
        shutil.rmtree(TARGET)
    TARGET.mkdir()
    (TARGET / "assets").mkdir()

    for filename in ("index.html", "styles.css", "app.js", "favicon.svg"):
        source = SOURCE / filename
        if not source.is_file():
            raise FileNotFoundError(source)
        data = source.read_text(encoding="utf-8")
        if filename == "index.html":
            data = data.replace("__VERSION__", VERSION)
        (TARGET / filename).write_text(data, encoding="utf-8")

    # No external stock photos: all site imagery is generated/captured by this
    # project and checked into docs/assets.
    for image in IMAGES.glob("*.png"):
        shutil.copy2(image, TARGET / "assets" / image.name)
    (TARGET / ".nojekyll").touch()

    html = (TARGET / "index.html").read_text(encoding="utf-8")
    css = (TARGET / "styles.css").read_text(encoding="utf-8")
    js = (TARGET / "app.js").read_text(encoding="utf-8")
    parser = PageParser()
    parser.feed(html)
    missing = sorted(name for name in parser.local_files if not (TARGET / name).is_file())
    dangling = sorted(anchor for anchor in parser.anchors if anchor and anchor not in parser.ids)
    if missing:
        raise AssertionError(f"Missing site assets: {missing}")
    if dangling:
        raise AssertionError(f"Broken in-page anchors: {dangling}")
    if parser.images_without_alt:
        raise AssertionError(f"Missing image alt text: {parser.images_without_alt}")
    if "__VERSION__" in html:
        raise AssertionError("Version placeholder not substituted")
    if "theme-ivory.png" not in html or "appearance-clock-face.png" not in html:
        raise AssertionError("Missing project showcase imagery")
    if not any(word in css for word in ("@media(max-width:680px)", "@media(max-width:900px)")):
        raise AssertionError("Responsive CSS rules not found")
    if "updateClock" not in js or "screenshot-image" not in js:
        raise AssertionError("Interactive previews not found")
    if not (TARGET / ".nojekyll").exists():
        raise AssertionError("Jekyll disable marker not found")
    total = sum(file.stat().st_size for file in TARGET.rglob("*") if file.is_file())
    print(f"Built GitHub Pages site for v{VERSION}: {len(parser.local_files)} local references; "
          f"{total / 1024:.1f} KiB, images={len(list((TARGET / 'assets').glob('*.png')))}")
    print(f"Output directory: {TARGET}")


if __name__ == "__main__":
    try:
        build()
    except Exception as exc:
        print(f"Website build failed: {exc}", file=sys.stderr)
        raise
