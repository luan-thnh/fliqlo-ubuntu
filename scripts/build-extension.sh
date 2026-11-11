#!/bin/sh
# Build a standalone GNOME Shell extension (no GTK app or external scripts).
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
VERSION=$(cat "$ROOT/VERSION")
UUID=fliqlo-ubuntu@luan-thnh
OUT=${1:-"$ROOT/dist"}
mkdir -p "$OUT"
OUT=$(CDPATH= cd -- "$OUT" && pwd)
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT HUP INT TERM
mkdir -p "$STAGE/schemas"
cp "$ROOT"/extension/*.js "$ROOT/extension/metadata.json" "$STAGE/"
cp "$ROOT"/extension/schemas/*.xml "$STAGE/schemas/"
glib-compile-schemas --strict "$STAGE/schemas"
# The archive root must contain metadata.json and extension.js for EGO.
(cd "$STAGE" && zip -q -X -r "$OUT/${UUID}-v${VERSION}.zip" .)
sha256sum "$OUT/${UUID}-v${VERSION}.zip" > "$OUT/${UUID}-v${VERSION}.zip.sha256"
printf 'Built %s\n' "$OUT/${UUID}-v${VERSION}.zip"
