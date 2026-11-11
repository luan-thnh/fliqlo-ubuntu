#!/usr/bin/env python3
"""Capture actual native GTK screens on an X11 display (for example via xvfb-run).

This runs the application's widgets and uses GDK window capture.
"""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import cairo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "native"))

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gio, GLib, Gtk
from app import Preferences, settings
os.environ.setdefault('GSETTINGS_BACKEND', 'memory')

ASSETS = ROOT / "docs" / "assets"
CASE_DARK_ONLY = os.environ.get("FLIQLO_SCREENSHOT_DARK") == "1"
CASES = ([("appearance-dark.png", "appearance", True)] if CASE_DARK_ONLY else [
    ("appearance-light.png", "appearance", False),
    ("appearance-clock-face.png", "appearance", False),
    ("appearance-background.png", "appearance", False),
    ("screensaver-light.png", "screensaver", False),
])

def demo_photos(folder):
    """Create original, temporary abstract backgrounds solely for the README screenshot."""
    paths = []
    palettes = [
        ((0.08, 0.18, 0.28), (0.24, 0.40, 0.52)),
        ((0.22, 0.12, 0.27), (0.53, 0.31, 0.43)),
        ((0.07, 0.26, 0.24), (0.25, 0.47, 0.36)),
    ]
    for index, (start, end) in enumerate(palettes):
        surface = cairo.ImageSurface(cairo.FORMAT_RGB24, 480, 280)
        cr = cairo.Context(surface)
        gradient = cairo.LinearGradient(0, 0, 480, 280)
        gradient.add_color_stop_rgb(0, *start)
        gradient.add_color_stop_rgb(1, *end)
        cr.set_source(gradient)
        cr.paint()
        cr.set_source_rgba(1, 1, 1, 0.12)
        cr.arc(350 - 45 * index, 110 + 12 * index, 75 + 8 * index, 0, 6.2831853)
        cr.fill()
        path = folder / f'demo-{index + 1}.png'
        surface.write_to_png(str(path))
        paths.append(Gio.File.new_for_path(str(path)).get_uri())
    return paths


def main():
    subprocess.run(["glib-compile-schemas", "--strict", str(ROOT / "extension" / "schemas")], check=True)
    ASSETS.mkdir(parents=True, exist_ok=True)
    temporary = tempfile.TemporaryDirectory(prefix='fliqlo-screenshot-')
    sample_photos = demo_photos(Path(temporary.name))
    application = Gtk.Application(
        application_id="io.github.luan_thnh.FliqloUbuntu.Screenshot",
        flags=Gio.ApplicationFlags.NON_UNIQUE,
    )

    def activate(app):
        theme = Gtk.Settings.get_default()
        theme.set_property("gtk-application-prefer-dark-theme", CASE_DARK_ONLY)
        os.environ['FLIQLO_DEMO_TIME'] = '09:41'
        config = settings()
        window = Preferences(app, config)
        window.set_size_request(680, 760)
        window.resize(680, 760)
        window.present()

        def capture(index):
            if index >= len(CASES):
                print("Captured all GTK settings screenshots", flush=True)
                app.quit()
                return GLib.SOURCE_REMOVE

            filename, page, dark = CASES[index]
            theme.set_property("gtk-application-prefer-dark-theme", dark)
            theme.set_property("gtk-theme-name", "Adwaita-dark" if dark else "Adwaita")
            if filename == 'appearance-clock-face.png':
                config.set_boolean('flap-colors-enabled', True)
                config.set_string('flap-background-color', '#173a56')
                config.set_string('flap-digit-color', '#d5f1ff')
                config.set_int('background-mode', 1)
                config.set_string('background-color', '#071a2b')
            else:
                config.set_boolean('flap-colors-enabled', False)
            if filename == 'appearance-background.png':
                config.set_strv('background-image-uris', sample_photos)
                config.set_int('background-selected-index', 1)
                config.set_string('background-image-uri', sample_photos[1])
                config.set_int('background-mode', 2)
            elif config.get_int('background-mode') == 2:
                config.set_int('background-mode', 0)
            window.pages.set_visible_child_name(page)
            if page == 'appearance':
                scroller = window.pages.get_child_by_name('appearance')
                adjustment = scroller.get_vadjustment()
                # Scroll down just for the Background settings screenshot.
                if filename == 'appearance-background.png':
                    GLib.idle_add(lambda: adjustment.set_value(
                        max(0, adjustment.get_upper() - adjustment.get_page_size())) or False)
                elif filename == 'appearance-clock-face.png':
                    GLib.idle_add(lambda: adjustment.set_value(
                        min(240, max(0, adjustment.get_upper() - adjustment.get_page_size()))) or False)
                else:
                    adjustment.set_value(0)
            window.queue_draw()

            def snapshot():
                surface = window.get_window()
                if surface is None:
                    raise RuntimeError("GTK window has not been realized")
                pixels = Gdk.pixbuf_get_from_window(
                    surface, 0, 0, window.get_allocated_width(),
                    window.get_allocated_height(),
                )
                if pixels is None:
                    raise RuntimeError("GDK returned no pixels; run under X11/Xvfb")
                target = ASSETS / filename
                pixels.savev(str(target), "png", [], [])
                print(
                    f"Captured {target.relative_to(ROOT)} ({pixels.get_width()}x{pixels.get_height()})",
                    flush=True,
                )
                GLib.timeout_add(200, capture, index + 1)
                return GLib.SOURCE_REMOVE

            GLib.timeout_add(1100, snapshot)
            return GLib.SOURCE_REMOVE

        GLib.timeout_add(1600, capture, 0)

    application.connect("activate", activate)
    try:
        return application.run(sys.argv[:1])
    finally:
        temporary.cleanup()

if __name__ == "__main__":
    sys.exit(main())
