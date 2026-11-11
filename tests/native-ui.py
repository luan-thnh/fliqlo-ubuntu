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
