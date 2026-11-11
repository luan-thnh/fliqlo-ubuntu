# Development and validation

## Requirements

For development on Ubuntu/Debian:

```bash
sudo apt install python3 python3-gi python3-cairo python3-gi-cairo \
  python3-fonttools python3-brotli python3-pil gir1.2-gtk-3.0 \
  gir1.2-adw-1 gjs libglib2.0-bin dpkg-dev zip xvfb dbus-x11
```

Node.js 22 is used **only for tests**, not by the installed extension or app.

## Run

```bash
./run.sh
./scripts/check.sh
./scripts/build-deb.sh
./scripts/build-extension.sh
```

`./run.sh` compiles the local GSettings schema and launches the GTK app. A system GNOME installation is necessary to test the actual idle-triggered extension. The CI's GTK UI test runs under a virtual X11 display; this does not validate production GNOME Wayland behavior.

## Checks

The project includes tests for clock time formats, monitor layout and drawing; lifecycle simulation; GJS rendering; GTK settings binding and preview; font parsing/import; and the flip transition. See `tests/` for sources. Reference-asset comparison is an optional forensic workflow and requires a legally acquired file; do not commit extracted proprietary assets.

For a source release, review:

1. `node --check` for extension JavaScript and `python3 -m compileall` for Python modules.
2. GSettings XML compilation and extension ZIP contents.
3. GTK preview/screensaver settings on real Ubuntu and GNOME Extensions native preferences.
4. Re-login, lock/unlock, monitor changes and extension enable/disable clean-up.
5. Extension reviewer guidance, attribution and licensing.

## Directory principles

Keep runtime code separate from packaging/scripts, release notes in docs, generated packages in dist (ignored by Git), and research measurements in research/evidence. Never commit `dist/`, caches, proprietary fonts or extracted `.scr`/`.dmg` assets.
