# Changelog

## 0.4.5 — background rendering verification

- Added image and color backdrop rendering tests against the native Cairo renderer.
- Added simulated GNOME Shell lifecycle checks for background layering and local image opacity.
- Added a Background settings screenshot, while keeping README examples fixed at 9:41 AM.
- No new configuration keys; feature remains compatible with v0.4.4 settings.

**Test the image picker and wallpapers on a physical GNOME 50 / Wayland machine before public GNOME Extensions submission.**


## 0.4.4 — customizable backgrounds

- Added local PNG/JPEG/WebP backgrounds, solid colors, opacity, fit modes, and dark overlay in GTK and GNOME Preferences.
- Kept classic black as the default with local-only image references; limit inputs to 16 MiB.
- Synced documentation screenshots to a fixed 9:41 AM while preserving the actual clock at runtime.
- Updated tests and GitHub Actions screenshot workflow.

**GNOME Shell image loading still needs manual validation on a physical GNOME 50/Wayland desktop.**


## 0.4.3 — documentation sync release

- Updated all three clock-format preview images to the same sample time: **9:41 AM / 9:41 / 09:41**.
- Regenerated the 1920×1080 renderer examples and synchronized the release tag with the current README.
- No runtime application behavior changed from v0.4.2.


## 0.4.2 — release candidate

- Replaced the blurry, window-captured fullscreen README image with three crisp 1920×1080 renders of the real Cairo/Pango clock for 12-hour, 24-hour and zero-padded 24-hour formats.
- Show all three clock modes side-by-side in README using one consistent 9:41 AM sample time; retain native GTK Settings screenshots.
- Added deterministic, pixel-checked rendering in CI and automatic cleanup of older project GitHub releases after successful publication.
- Reduced temporary Actions artifact retention.

**Still requires manual testing** on a physical Ubuntu GNOME 50 / Wayland desktop.

## 0.4.1 — release candidate

- Added MIT LICENSE for independently written project code.
- Added subtle luan-thnh signature in GTK settings.
- Captured actual fullscreen GTK Preview for the README gallery.
- Automated prerelease publishing in GitHub Actions after successful builds.

**Still requires manual validation** on a real GNOME 50 / Wayland desktop before submission to GNOME Extensions.

## 0.4.0 — release candidate

- Reorganized source, historical evidence, and English-language documentation; removed the tracked prebuilt Debian package from the source tree.
- Redesigned GTK settings with a live preview, theme-aware CSS, grouped controls, and Appearance / Screensaver navigation.
- Added independent GNOME-native extension Preferences (no dependency on the Debian desktop application).
- Added a standalone extension ZIP build, source checks, and dual-artifact CI packaging.
- Documented the GNOME Extensions review process and reasons Flathub is not appropriate for a shell extension.

**Not yet verified** on a physical GNOME 50 session; public release is blocked on maintainer licensing, code review, and manual integration testing.

## 0.3.2 — historical

- Updated the clock animation to use frame clocks and repaired fullscreen preview integration.
- Historical measurements and comparison evidence are preserved under `research/evidence/`.
