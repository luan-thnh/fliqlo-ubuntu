"""Drive the real GTK clock timer through a minute change, including motion settings."""
import os
os.environ['GSETTINGS_BACKEND'] = 'memory'
from pathlib import Path
import sys
from datetime import datetime, timedelta
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'native'))
import app
from gi.repository import Gtk, GLib
from model import clock_parts
Gtk.init(None)
frozen = datetime(2026, 1, 1, 12, 0)
class FixedDateTime:
    @staticmethod
    def now():
        return frozen
app.datetime = FixedDateTime
config = app.settings()
clock = app.Clock(config)
window = Gtk.Window()
window.set_default_size(640, 360)
window.add(clock)
window.show_all()
paint = app.paint
frames, errors = [], []
gtk_settings = Gtk.Settings.get_default()
was_enabled = gtk_settings.get_property('gtk-enable-animations')
gtk_settings.set_property('gtk-enable-animations', False)

def observed(cr, width, height, current, previous, progress, options):
    if previous is not None:
        frames.append(progress)
    return paint(cr, width, height, current, previous, progress, options)
app.paint = observed

def change_minute():
    clock.current = clock_parts(frozen - timedelta(minutes=1), config.get_int('time-format'))
    clock.tick_clock()

def begin():
    config.set_boolean('flip-animation', True)
    change_minute()
    GLib.timeout_add(600, verify_enabled)
    return GLib.SOURCE_REMOVE

def verify_enabled():
    try:
        assert sum(0 < progress < 1 for progress in frames) >= 3, frames
        assert frames[-1] == 1, frames
        frames.clear()
        config.set_boolean('flip-animation', False)
        change_minute()
        GLib.timeout_add(150, verify_disabled)
    except Exception as error:
        errors.append(error)
        Gtk.main_quit()
    return GLib.SOURCE_REMOVE

def verify_disabled():
    try:
        assert frames and all(progress == 1 for progress in frames), frames
    except Exception as error:
        errors.append(error)
    Gtk.main_quit()
    return GLib.SOURCE_REMOVE
GLib.timeout_add(80, begin)
Gtk.main()
app.paint = paint
gtk_settings.set_property('gtk-enable-animations', was_enabled)
window.destroy()
if errors:
    raise errors[0]
print('Live GTK minute rollover: intermediate flip frames despite desktop effects off; explicit motion-off setting respected.')
