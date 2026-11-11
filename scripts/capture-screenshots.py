#!/usr/bin/env python3
"""Capture actual native GTK screens on an X11 display (for example via xvfb-run).

This runs the application's widgets and uses GDK window capture.
"""
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "native"))

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gio, GLib, Gtk
from app import Preferences, settings

ASSETS = ROOT / "docs" / "assets"
CASE_DARK_ONLY = os.environ.get("FLIQLO_SCREENSHOT_DARK") == "1"
CASES = ([("appearance-dark.png", "appearance", True)] if CASE_DARK_ONLY else [
    ("appearance-light.png", "appearance", False),
    ("screensaver-light.png", "screensaver", False),
    ("preview-fullscreen.png", "preview", False),
])

def update_readme():
    readme = ROOT / "README.md"
    content = readme.read_text(encoding="utf-8")
    gallery = """## Screenshots

Screenshots captured from the **native GTK app on Ubuntu with Xvfb**. The GNOME Shell extension's Preferences may look different.

<p align="center">
  <img src="docs/assets/preview-fullscreen.png" width="880" alt="Real fullscreen flip-clock preview from the native GTK app">
</p>
<p align="center"><sub>Fullscreen preview — available via the Preview button in the app.</sub></p>

| Appearance · Light | Screensaver · Light | Appearance · Dark |
| :---: | :---: | :---: |
| ![GTK appearance controls and clock preview](docs/assets/appearance-light.png) | ![GTK idle and monitor settings](docs/assets/screensaver-light.png) | ![GTK appearance settings in dark mode](docs/assets/appearance-dark.png) |

"""
    start = content.find("## Screenshots\n")
    if start >= 0:
        end = content.find("## Highlights\n", start)
        if end < 0:
            raise RuntimeError("Cannot locate the end of existing screenshot section")
        content = content[:start] + gallery + content[end:]
    else:
        if "## Highlights\n" not in content:
            raise RuntimeError("Missing README Highlights anchor")
        content = content.replace("## Highlights\n", gallery + "## Highlights\n", 1)
    readme.write_text(content, encoding="utf-8")

def main():
    subprocess.run(["glib-compile-schemas", "--strict", str(ROOT / "extension" / "schemas")], check=True)
    ASSETS.mkdir(parents=True, exist_ok=True)
    application = Gtk.Application(
        application_id="io.github.luan_thnh.FliqloUbuntu.Screenshot",
        flags=Gio.ApplicationFlags.NON_UNIQUE,
    )

    def activate(app):
        theme = Gtk.Settings.get_default()
        theme.set_property("gtk-application-prefer-dark-theme", CASE_DARK_ONLY)
        window = Preferences(app, settings())
        window.set_size_request(680, 760)
        window.resize(680, 760)
        window.present()

        def capture(index):
            if index >= len(CASES):
                update_readme()
                print("Captured all screenshots; updated README.md", flush=True)
                app.quit()
                return GLib.SOURCE_REMOVE

            filename, page, dark = CASES[index]
            theme.set_property("gtk-application-prefer-dark-theme", dark)
            theme.set_property("gtk-theme-name", "Adwaita-dark" if dark else "Adwaita")
            if page == "preview":
                window.pages.set_visible_child_name("appearance")
                window.preview(None)  # Exercise the real fullscreen Preview action.
            else:
                window.pages.set_visible_child_name(page)
            window.queue_draw()

            def snapshot():
                preview_window = None
                if page == "preview":
                    preview_window = next((w for w in app.get_windows()
                                           if w is not window and w.get_title() == "Fliqlo — Preview"), None)
                    if preview_window is None:
                        raise RuntimeError("Preview action did not open a fullscreen window")
                target_window = preview_window or window
                surface = target_window.get_window()
                if surface is None:
                    raise RuntimeError("GTK window has not been realized")
                pixels = Gdk.pixbuf_get_from_window(
                    surface, 0, 0, target_window.get_allocated_width(),
                    target_window.get_allocated_height(),
                )
                if pixels is None:
                    raise RuntimeError("GDK returned no pixels; run under X11/Xvfb")
                target = ASSETS / filename
                pixels.savev(str(target), "png", [], [])
                print(
                    f"Captured {target.relative_to(ROOT)} ({pixels.get_width()}x{pixels.get_height()})",
                    flush=True,
                )
                if preview_window is not None:
                    preview_window.destroy()
                GLib.timeout_add(200, capture, index + 1)
                return GLib.SOURCE_REMOVE

            GLib.timeout_add(1100, snapshot)
            return GLib.SOURCE_REMOVE

        GLib.timeout_add(1600, capture, 0)

    application.connect("activate", activate)
    return application.run(sys.argv[:1])

if __name__ == "__main__":
    sys.exit(main())
