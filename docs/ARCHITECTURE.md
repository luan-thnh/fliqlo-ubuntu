# Architecture

```text
GNOME session (Wayland)
  └─ GNOME Shell extension (extension/extension.js)
       ├─ idle-monitor and session state → show/hide screensaver
       ├─ Clutter timeline → 330 ms flip animation
       ├─ Cairo/Pango renderer (extension/clock.js)
       └─ GSettings ↔ extension/prefs.js (libadwaita Preferences)

Optional GTK desktop application (native/app.py)
  ├─ GSettings ↔ same schema
  ├─ Cairo/Pango drawing area (native/render.py)
  ├─ fullscreen preview (local fallback or Shell request)
  └─ local font import (native/assets.py)
```

## Shared contract

`extension/schemas/org.gnome.shell.extensions.fliqlo-ubuntu.gschema.xml` defines time format, clock size, brightness, flap display, flip animation, display selection, idle delay, font family, and preview token. The extension and native app must remain compatible with that schema. New preferences must have a sane default and an appropriate test.

## Important boundaries

- The extension owns idle activation; the Python app is optional and **must not be started as an invisible daemon**.
- Native UI styling is isolated in `native/style.css` and uses GTK theme colors for light/dark adaptation.
- The screensaver deliberately yields to GNOME screen lock and blanking. Do not bypass locking or change system power/lock settings.
- External Fliqlo fonts/assets are never included in builds. Imported files are validated locally and kept in the user's profile.
- Avoid background networking, telemetry, or extra subprocesses in the extension; maintain GNOME Extensions review compliance.
