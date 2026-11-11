# Installation and troubleshooting

## Supported system

- Intended target: Ubuntu 26.04, GNOME Shell 50, Wayland.
- A running GNOME desktop is necessary for idle activation. X11, other shells and GNOME versions are **not claimed supported**.
- The standalone GTK app uses Python 3, PyGObject/GTK 3 and Cairo; package dependencies are listed in `scripts/build-deb.sh`.

## Install the extension only

```bash
sudo apt install zip libglib2.0-bin
./scripts/build-extension.sh
gnome-extensions install --force dist/fliqlo-ubuntu@luan-thnh-v0.4.0.zip
```

Log out and in, enable **Fliqlo Ubuntu** in the GNOME Extensions app, and open its Preferences. Set the idle delay shorter than the screen blank timeout in GNOME Settings. If the extension isn't visible, check `gnome-extensions list` and `gnome-extensions info fliqlo-ubuntu@luan-thnh`.

## Install the native application

```bash
sudo apt install dpkg-dev libglib2.0-bin
./scripts/build-deb.sh
sudo apt install ./dist/fliqlo-ubuntu_0.4.0_all.deb
```

On GNOME Wayland, **log out and back in** after installation, upgrade, or removal. Launch **Fliqlo Ubuntu** from the app list. Select **Screensaver → Enable** if the extension is not already enabled. GNOME's own lock and power settings always win.

## Optional font import

In the desktop app, open **Appearance → Typography → Import…** and choose a supported OTF, Windows ZIP / SCR or macOS DMG that you own. A font is validated and stored in `${XDG_DATA_HOME:-$HOME/.local/share}/fonts/fliqlo-ubuntu/Fliqlo.otf`, without executing Windows code. DMG support needs `7zip`; fontconfig must be installed. Re-login may be needed to load the new font in GNOME Shell.

The extension's standalone Preferences can select any **already installed** font family, but cannot import files. That feature is intentionally limited to the optional desktop application.

## Troubleshooting

- **No idle clock:** verify the extension is enabled, wait past the configured delay, confirm the session is unlocked and check GNOME's screen blank timeout.
- **No extension after installing:** log out and in; check that `gnome-shell --version` reports the supported major version.
- **Settings unavailable:** run `./run.sh` from the checkout, or reinstall the Debian package for its compiled GSettings schema.
- **Using both installation methods:** avoid duplicate system/user extensions with the same UUID; remove the duplicate and re-login.
- **Animation disabled:** enable **Flip animation** in Appearance; GNOME's other animation settings are not changed.

## Remove

For an extension installed in your user profile:

```bash
gnome-extensions disable fliqlo-ubuntu@luan-thnh
gnome-extensions uninstall fliqlo-ubuntu@luan-thnh
```

For the `.deb` package:

```bash
gnome-extensions disable fliqlo-ubuntu@luan-thnh
sudo apt remove fliqlo-ubuntu
```

Remove the imported font manually only if you no longer need it. To reset personal configuration, set `GSETTINGS_SCHEMA_DIR` to the extension schema directory before calling `gsettings` (the directory differs between user and system installation). For a system `.deb` installation:

```bash
GSETTINGS_SCHEMA_DIR=/usr/share/gnome-shell/extensions/fliqlo-ubuntu@luan-thnh/schemas \
  gsettings reset-recursively org.gnome.shell.extensions.fliqlo-ubuntu
```
