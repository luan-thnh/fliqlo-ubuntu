"""GTK smoke test with Xvfb and an in-memory GSettings backend."""
import os
os.environ['GSETTINGS_BACKEND'] = 'memory'
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'native'))
from app import App, Preferences, settings, Clock
from gi.repository import Gtk, GLib

app = App()
app.register(None)
config = settings()
window = Preferences(app, config)
errors = []

def widgets(root):
    yield root
    if isinstance(root, Gtk.Container):
        for child in root.get_children():
            yield from widgets(child)

def check():
    try:
        control = window.controls
        assert {'time-format', 'scale', 'brightness', 'background',
                'flip-animation', 'idle-enabled', 'multiple-displays', 'idle-seconds'} <= control.keys()
        control['time-format'].set_active(2)
        assert config.get_int('time-format') == 2
        control['background'].set_active(False)
        assert not config.get_boolean('background')
        control['background'].set_active(True)
        control['scale'].set_value(75)
        assert config.get_int('scale') == 75
        config.set_int('scale', 100)
        assert control['scale'].get_value() == 100
        control['idle-seconds'].set_value(240)
        assert config.get_int('idle-seconds') == 240
        window.pages.set_visible_child_name('screensaver')
        assert window.pages.get_visible_child_name() == 'screensaver'
        window.pages.set_visible_child_name('appearance')
        clock = next(w for w in widgets(window) if isinstance(w, Clock))
        assert clock.current[0].isdigit()
        assert {'background-mode', 'background-color', 'background-opacity',
                'background-fit', 'background-dim'} <= control.keys()
        control['background-mode'].set_active(1)
        assert config.get_int('background-mode') == 1
        config.set_string('background-color', '#264466')
        control['background-opacity'].set_value(70)
        assert config.get_int('background-opacity') == 70
        control['background-fit'].set_active(1)
        assert config.get_int('background-fit') == 1
        config.set_int('background-mode', 0)
        assert {'background-slideshow', 'background-slideshow-seconds'} <= control.keys()
        control['background-slideshow'].set_active(True)
        assert config.get_boolean('background-slideshow')
        config.set_strv('background-image-uris', ['file:///tmp/a.png', 'file:///tmp/b.png'])
        config.set_int('background-selected-index', 1)
        assert len(window.gallery.get_children()) == 2
        window._remove_backdrop(0)
        assert config.get_strv('background-image-uris') == ['file:///tmp/b.png']
        window.clear_backdrop(None)
        assert not config.get_strv('background-image-uris')
        assert {'flap-colors-enabled', 'flap-background-color',
                'flap-digit-color'} <= control.keys()
        control['flap-colors-enabled'].set_active(True)
        assert config.get_boolean('flap-colors-enabled')
        config.set_string('flap-background-color', '#173a56')
        config.set_string('flap-digit-color', '#d5f1ff')
        assert config.get_string('flap-digit-color') == '#d5f1ff'
        window.reset_clock_colors(None)
        assert not config.get_boolean('flap-colors-enabled')
        config.set_boolean('flap-colors-enabled', True)
        config.set_int('background-mode', 1)
        config.set_strv('background-image-uris', ['file:///tmp/retained.png'])
        window.reset_appearance(None)
        assert config.get_int('background-mode') == 0
        assert not config.get_boolean('flap-colors-enabled')
        assert config.get_strv('background-image-uris') == ['file:///tmp/retained.png']
        config.set_int('brightness', 50)
        config.set_int('brightness', 100)
        window.preview(None)
        preview = next(w for w in Gtk.Window.list_toplevels() if w.get_title() == 'Fliqlo — Preview')
        preview.destroy()
        window.refresh_status()
        assert window.status.get_text()  # Graceful fallback without GNOME Shell.
        window.destroy()
    except Exception as error:
        errors.append(error)
    Gtk.main_quit()
    return GLib.SOURCE_REMOVE

GLib.timeout_add(300, check)
Gtk.main()
if errors:
    raise errors[0]
print('GTK: navigation, settings, preview, GNOME status, and cleanup passed.')
