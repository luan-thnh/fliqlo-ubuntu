# Fliqlo Ubuntu

**A clean flip-clock screensaver for GNOME on Wayland.**

An independent, open-source-ready implementation of a split-flap clock for Ubuntu. It uses a GNOME Shell extension for idle activation and an optional native GTK app for setup, font import, and fullscreen preview. No browser, Node.js, or background server is required at runtime.

> **Status:** Pre-release 0.4.0 · GNOME Shell **50** / Ubuntu **26.04** target · Maintainer review and license selection required before public extension submission. Not affiliated with Fliqlo or its creator.

## Screenshots

Real screenshots captured from the **v0.4.0 native GTK application** in an Ubuntu Xvfb session. The GNOME Shell extension's Preferences screen may differ.

| Appearance · Light | Screensaver · Light | Appearance · Dark |
| :---: | :---: | :---: |
| ![GTK appearance settings with a live flip-clock preview](docs/assets/appearance-light.png) | ![GTK screensaver settings with idle and monitor controls](docs/assets/screensaver-light.png) | ![GTK appearance settings in dark mode](docs/assets/appearance-dark.png) |

## Highlights

- Split-flap clock with a 330 ms flip transition and an optional reduced-motion mode.
- Automatic activation while idle, with GNOME's existing lock screen and power policies preserved.
- Native GTK settings with live preview, light/dark theme support, and clear Appearance / Screensaver navigation.
- Extension-native Preferences: edit settings without installing the standalone app.
- 12-hour and two 24-hour formats, adjustable size and brightness, and multi-monitor support.
- Optional import of a font from a file **you legally possess**; proprietary Fliqlo assets are not distributed.

## Install

### GNOME extension (standalone)

Requires GNOME Shell 50 and `glib-compile-schemas` to build the archive:

```bash
sudo apt install libglib2.0-bin zip
./scripts/build-extension.sh
# Archive in dist/fliqlo-ubuntu@luan-thnh-v0.4.0.zip
```

Install the generated archive with the GNOME Extensions app, or use the CLI:

```bash
gnome-extensions install --force dist/fliqlo-ubuntu@luan-thnh-v0.4.0.zip
```

**Log out and back in** on Wayland, then enable the extension in GNOME Extensions. Open **Preferences** to configure it. The standalone app is not required for the screensaver itself.

### Native desktop app + extension (Debian package)

```bash
sudo apt install dpkg-dev libglib2.0-bin
./scripts/build-deb.sh
sudo apt install ./dist/fliqlo-ubuntu_0.4.0_all.deb
```

Log out and back in, open **Fliqlo Ubuntu**, then use **Screensaver → Enable**. Avoid installing both a user-level extension archive and a system-level `.deb` for the same UUID: GNOME may use the user-installed copy instead of the package copy.

See [Installation](docs/INSTALLATION.md) for dependencies, troubleshooting, uninstall instructions, and the live preview.

## Developer quick start

```bash
./run.sh                         # GTK preferences / preview (Ubuntu with GTK 3 dependencies)
node tests/clock.mjs             # Clock logic
node tests/extension-lifecycle.mjs
./scripts/check.sh               # Static checks / tests available on your machine
./scripts/build-extension.sh     # GNOME Extensions release archive
./scripts/build-deb.sh           # Ubuntu .deb package
```

| Directory | Purpose |
| --- | --- |
| [`extension/`](extension/) | GNOME Shell extension, independent Preferences, GSettings schema |
| [`native/`](native/) | Optional GTK desktop settings, clock preview, font import |
| [`packaging/`](packaging/) | Desktop entry and icon |
| [`scripts/`](scripts/) | Build, checks, and reference-comparison tools |
| [`tests/`](tests/) | Clock rendering, lifecycle, and UI tests |
| [`docs/`](docs/) | Installation, architecture, development, and release guides |
| [`research/evidence/`](research/evidence/) | Archived implementation analysis and measurements |

## Compatibility and limitations

The existing rendering code and animation were evaluated on a GNOME 50.1 / Wayland headless environment in the earlier release. Version 0.4.0 changes settings and packaging; it still needs **manual testing** on an actual GNOME 50 desktop, including GPU, HiDPI, multimonitor, extension Preferences, and suspend/lock behavior. It does not replace GNOME's security-sensitive lock screen or inhibit display sleep.

This project is an **independent reimplementation**. It does not ship proprietary Fliqlo binaries, fonts, HTML, or media; see [Third-party acknowledgements](THIRD_PARTY.md). **A source-code license has not yet been selected by the maintainer.** Choose an OSI-approved license and verify that all contributions can be licensed under it **before publishing**. Until then, do not describe the repository as officially licensed open source.

## Documentation

[Installation](docs/INSTALLATION.md) · [Architecture](docs/ARCHITECTURE.md) · [Development and tests](docs/DEVELOPMENT.md) · [Publishing checklist](docs/RELEASING.md) · [Historical research](research/evidence/ANALYSIS.md)

## Acknowledgements

The original **Fliqlo** screensaver was created by Yuji Adachi / 9031: https://fliqlo.com/. This project is unofficial and not endorsed by the original author.
