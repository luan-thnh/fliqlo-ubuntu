#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
VERSION=$(cat "$ROOT/VERSION")
OUT=${1:-"$ROOT/dist"}
mkdir -p "$OUT"
OUT=$(CDPATH= cd -- "$OUT" && pwd)
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT HUP INT TERM
EXT="$STAGE/usr/share/gnome-shell/extensions/fliqlo-ubuntu@luan-thnh"
mkdir -p "$STAGE/DEBIAN" "$STAGE/usr/bin" "$STAGE/usr/share/fliqlo-ubuntu" "$EXT/schemas" \
    "$STAGE/usr/share/applications" "$STAGE/usr/share/icons/hicolor/scalable/apps" "$STAGE/usr/share/doc/fliqlo-ubuntu"
cp "$ROOT"/native/*.py "$ROOT/native/style.css" "$STAGE/usr/share/fliqlo-ubuntu/"
cp "$ROOT"/extension/*.js "$ROOT/extension/metadata.json" "$EXT/"
cp "$ROOT"/extension/schemas/*.xml "$EXT/schemas/"
glib-compile-schemas --strict "$EXT/schemas"
cp "$ROOT/packaging/fliqlo-ubuntu.desktop" "$STAGE/usr/share/applications/"
cp "$ROOT/packaging/fliqlo-ubuntu.svg" "$STAGE/usr/share/icons/hicolor/scalable/apps/"
cp "$ROOT/README.md" "$ROOT/LICENSE" "$STAGE/usr/share/doc/fliqlo-ubuntu/"
cp "$ROOT/THIRD_PARTY.md" "$STAGE/usr/share/doc/fliqlo-ubuntu/copyright"
cat > "$STAGE/usr/bin/fliqlo-ubuntu" <<'LAUNCHER'
#!/bin/sh
exec /usr/bin/python3 /usr/share/fliqlo-ubuntu/app.py "$@"
LAUNCHER
cat > "$STAGE/DEBIAN/control" <<CONTROL
Package: fliqlo-ubuntu
Version: $VERSION
Section: gnome
Priority: optional
Architecture: all
Maintainer: luan-thnh <luan-thnh@users.noreply.github.com>
Depends: python3, python3-gi, python3-cairo, python3-gi-cairo, python3-fonttools, python3-brotli, gir1.2-gtk-3.0, gnome-shell (>= 50), gnome-shell (<< 51), gnome-shell-common, gir1.2-adw-1, fontconfig, fonts-dejavu-core
Recommends: 7zip
Homepage: https://github.com/luan-thnh/fliqlo-ubuntu
Description: Flip clock screensaver and preferences for GNOME 50 on Wayland
 Native preferences, fullscreen preview and a GNOME Shell idle extension.
 Preserves the existing screen lock and monitor power settings.
CONTROL
find "$STAGE" -type d -exec chmod 755 {} +
find "$STAGE" -type f -exec chmod 644 {} +
chmod 755 "$STAGE/usr/bin/fliqlo-ubuntu"
dpkg-deb --root-owner-group --build "$STAGE" "$OUT/fliqlo-ubuntu_${VERSION}_all.deb"
(cd "$OUT" && sha256sum "fliqlo-ubuntu_${VERSION}_all.deb" > SHA256SUMS)
