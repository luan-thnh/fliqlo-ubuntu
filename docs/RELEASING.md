# Publishing checklist

**Preparation only. GitHub release candidates may be published automatically as pre-releases; no upload to extensions.gnome.org has been performed.**

## 1. Resolve publication blockers

- [x] Add the MIT source license for original code. **Still verify provenance and contributor permissions** before public publication; the license does not cover original Fliqlo assets.
- [ ] Verify repository ownership and that `https://github.com/luan-thnh/fliqlo-ubuntu` is the correct intended public URL; do not change its visibility without owner consent.
- [ ] Manually review and understand every extension JavaScript file, especially generated/modified code; only the maintainer can remove the AI-assisted development warning after genuine review.
- [ ] Verify branding and trademark disclaimers; no Fliqlo proprietary font, executable or copied UI assets in the upload.
- [ ] Test the GNOME extension and native Preferences on a real Ubuntu 26.04 / GNOME 50 Wayland session, including shell logs, suspend, lock/unlock, and monitors.

## 2. Build

```bash
./scripts/check.sh
./scripts/build-extension.sh
./scripts/build-deb.sh
python3 scripts/release-audit.py
```

The extension ZIP is root-layout (`metadata.json`, `extension.js`, `prefs.js`, `clock.js`, `schemas/…`); it contains no Python desktop app or bundled binaries. The Debian package supplies the optional GTK app and installs the system extension.

## 3. GNOME Extensions — primary channel

1. Confirm `metadata.json` contains a valid UUID, stable and actually tested GNOME Shell version, description, settings schema and accessible repository URL.
2. Install and test the **ZIP** locally without the `.deb`, including `gnome-extensions prefs fliqlo-ubuntu@luan-thnh`.
3. Read the official review guidelines: https://gjs.guide/extensions/review-guidelines/review-guidelines.html and the maintainership guidance at https://gjs.guide/extensions/review-guidelines/best-practices.html.
4. Submit the ZIP using your GNOME Extensions account at https://extensions.gnome.org/upload/; reviewers decide acceptance and may request changes.
5. When approved, document the GNOME Extensions page and track actual supported GNOME releases.

## 4. GitHub Releases — automated pre-release

- On a successful `main` build, the CI release job publishes a pre-release for the version in `VERSION` (currently `v0.4.6`), including `.deb`, standalone extension ZIP, and SHA256 checksum files.
- The release job skips re-uploading existing tags. After successfully publishing the current version it deletes older versioned GitHub Releases and their tags so only the latest project release remains. Bump `VERSION` for each subsequent release; verify the generated assets and release page.
- Do not commit generated `.deb` packages to the source repository; attach them to GitHub Releases.
- Record release notes, screenshots of the *actual new UI*, tested Ubuntu/GNOME versions, known limitations, and uninstall steps.

## 5. Flathub — not an extension distribution channel

Flathub explicitly rejects shell/window-manager/desktop-environment extensions; the GNOME Shell component should **not** be submitted as a Flatpak. A future *standalone application* could be evaluated separately, but it must have substantial standalone functionality, comply with sandbox restrictions, and pass Flathub review. See https://docs.flathub.org/docs/for-app-authors/requirements.
