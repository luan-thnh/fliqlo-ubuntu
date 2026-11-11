#!/usr/bin/python3
"""Preferences and fullscreen preview for the GNOME/Wayland screensaver."""
from datetime import datetime
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
import time

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_foreign('cairo')
from gi.repository import Gdk, Gio, GLib, Gtk
from model import clock_parts, FLIP_SECONDS
from render import paint
from assets import windows_font

UUID = 'fliqlo-ubuntu@luan-thnh'
SCHEMA = 'org.gnome.shell.extensions.fliqlo-ubuntu'
ROOT = Path(__file__).resolve().parent
SCHEMAS = (ROOT.parent / 'extension/schemas' if (ROOT.parent / 'extension').exists()
           else ROOT.parent / 'gnome-shell/extensions' / UUID / 'schemas')


def settings():
    source = Gio.SettingsSchemaSource.new_from_directory(str(SCHEMAS),
        Gio.SettingsSchemaSource.get_default(), False)
    schema = source.lookup(SCHEMA, True)
    if schema is None:
        raise RuntimeError('GSettings schema not found. Reinstall the .deb package or run ./run.sh.')
    return Gio.Settings.new_full(schema, None, None)


def extension_info():
    try:
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        result = bus.call_sync('org.gnome.Shell', '/org/gnome/Shell',
            'org.gnome.Shell.Extensions', 'GetExtensionInfo', GLib.Variant('(s)', (UUID,)),
            GLib.VariantType.new('(a{sv})'), Gio.DBusCallFlags.NONE, 1500, None)
        return result.unpack()[0]
    except GLib.Error:
        return {}


class Clock(Gtk.DrawingArea):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.current = clock_parts(datetime.now(), config.get_int('time-format'))
        self.previous = None
        self.started = 0
        self.progress = 1
        self.animation = 0
        self.connect('draw', self.draw_clock)
        self.tick = GLib.timeout_add(250, self.tick_clock)
        self.changed = config.connect('changed', self.on_setting)
        self.connect('destroy', self.cleanup)

    def on_setting(self, *_args):
        if self.animation:
            self.remove_tick_callback(self.animation)
            self.animation = 0
        self.progress = 1
        self.current = clock_parts(datetime.now(), self.config.get_int('time-format'))
        self.previous = None
        self.queue_draw()

    def cleanup(self, *_args):
        GLib.source_remove(self.tick)
        if self.animation:
            self.remove_tick_callback(self.animation)
        self.config.disconnect(self.changed)

    def tick_clock(self):
        current = clock_parts(datetime.now(), self.config.get_int('time-format'))
        if current != self.current:
            self.previous, self.current = self.current, current
            self.started = GLib.get_monotonic_time()
            self.progress = 0
            if not self.config.get_boolean('flip-animation'):
                self.progress = 1
                self.queue_draw()
            elif not self.animation:
                self.animation = self.add_tick_callback(self.frame)
        return GLib.SOURCE_CONTINUE

    def frame(self, _widget, frame_clock):
        self.progress = max(0, min(1, (frame_clock.get_frame_time() - self.started) / (FLIP_SECONDS * 1000000)))
        self.queue_draw()
        if self.progress >= 1:
            self.animation = 0
            return GLib.SOURCE_REMOVE
        return GLib.SOURCE_CONTINUE

    def draw_clock(self, _widget, cr):
        options = {key: self.config.get_int(key) for key in ('scale', 'brightness')}
        options.update(background=self.config.get_boolean('background'), font=self.config.get_string('font-family'))
        progress = self.progress
        paint(cr, self.get_allocated_width(), self.get_allocated_height(),
              self.current, self.previous, progress, options)
        return False


class Preferences(Gtk.ApplicationWindow):
    """Compact, theme-aware GTK preferences with a live clock preview."""

    def __init__(self, app, config):
        super().__init__(application=app, title='Fliqlo Ubuntu')
        self.config = config
        self.controls = {}
        self.set_default_size(680, 760)
        self.set_size_request(510, 520)
        self._install_styles()
        self.get_style_context().add_class('fliqlo-window')

        header = Gtk.HeaderBar(title='Fliqlo Ubuntu', subtitle='Flip clock screensaver',
                               show_close_button=True)
        header.get_style_context().add_class('fliqlo-header')
        preview_button = Gtk.Button(label='⤢  Preview')
        preview_button.get_style_context().add_class('suggested-action')
        preview_button.set_tooltip_text('Open a fullscreen preview · Esc or move the pointer to close')
        preview_button.connect('clicked', self.preview)
        header.pack_end(preview_button)
        self.set_titlebar(header)

        layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(layout)

        hero = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=11)
        hero.set_margin_top(18)
        hero.set_margin_start(22)
        hero.set_margin_end(22)
        hero.set_margin_bottom(12)
        layout.pack_start(hero, False, False, 0)

        frame = Gtk.Frame()
        frame.get_style_context().add_class('clock-preview')
        frame.set_shadow_type(Gtk.ShadowType.NONE)
        clock = Clock(config)
        clock.set_size_request(0, 172)
        frame.add(clock)
        hero.pack_start(frame, False, False, 0)

        banner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=9)
        banner.get_style_context().add_class('status-banner')
        self.status = Gtk.Label(xalign=0, wrap=True, selectable=True)
        self.status.set_hexpand(True)
        self.status.get_style_context().add_class('status-text')
        banner.pack_start(self.status, True, True, 0)
        hero.pack_start(banner, False, False, 0)

        navigation = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        navigation.set_halign(Gtk.Align.CENTER)
        navigation.set_margin_bottom(6)
        layout.pack_start(navigation, False, False, 0)
        self.pages = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE,
                               transition_duration=170)
        self.pages.set_vexpand(True)
        nav = Gtk.StackSwitcher(stack=self.pages)
        nav.get_style_context().add_class('fliqlo-nav')
        navigation.pack_start(nav, False, False, 0)

        self.pages.add_titled(self._appearance_page(), 'appearance', 'Appearance')
        self.pages.add_titled(self._screensaver_page(), 'screensaver', 'Screensaver')
        layout.pack_start(self.pages, True, True, 0)

        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        footer.get_style_context().add_class('fliqlo-footer')
        footer.set_margin_start(22)
        footer.set_margin_end(22)
        footer.set_margin_top(7)
        footer.set_margin_bottom(12)
        footer_label = Gtk.Label(label='Changes are saved automatically.', xalign=0)
        footer_label.get_style_context().add_class('dim-label')
        footer.pack_start(footer_label, True, True, 0)
        signature = Gtk.Label(label='luan-thnh')
        signature.get_style_context().add_class('creator-signature')
        signature.set_tooltip_text('Created by luan-thnh')
        footer.pack_end(signature, False, False, 0)
        layout.pack_end(footer, False, False, 0)

        self.refresh_status()
        self.show_all()
        # Focus the navigation rather than a scale to avoid stealing scrolling.
        nav.grab_focus()

    @staticmethod
    def _install_styles():
        css_file = Path(__file__).resolve().with_name('style.css')
        provider = Gtk.CssProvider()
        provider.load_from_path(str(css_file))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    @staticmethod
    def _text(title, subtitle=None):
        column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        title_label = Gtk.Label(label=title, xalign=0)
        title_label.get_style_context().add_class('setting-title')
        column.pack_start(title_label, False, False, 0)
        if subtitle:
            desc = Gtk.Label(label=subtitle, xalign=0, wrap=True)
            desc.set_max_width_chars(58)
            desc.get_style_context().add_class('dim-label')
            desc.get_style_context().add_class('setting-description')
            column.pack_start(desc, False, False, 0)
        return column

    def _row(self, title, subtitle=None, widget=None):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=18)
        box.get_style_context().add_class('setting-row')
        box.pack_start(self._text(title, subtitle), True, True, 0)
        if widget:
            widget.set_valign(Gtk.Align.CENTER)
            box.pack_end(widget, False, False, 0)
        return box

    def _section(self, title, rows, description=None):
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        heading = Gtk.Label(label=title, xalign=0)
        heading.get_style_context().add_class('section-title')
        section.pack_start(heading, False, False, 0)
        if description:
            note = Gtk.Label(label=description, xalign=0, wrap=True)
            note.get_style_context().add_class('dim-label')
            section.pack_start(note, False, False, 0)
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        card.get_style_context().add_class('settings-card')
        for index, row in enumerate(rows):
            if index:
                card.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)
            card.pack_start(row, False, False, 0)
        section.pack_start(card, False, False, 0)
        return section

    def _switch(self, key):
        toggle = Gtk.Switch()
        toggle.set_halign(Gtk.Align.END)
        self.config.bind(key, toggle, 'active', Gio.SettingsBindFlags.DEFAULT)
        self.controls[key] = toggle
        return toggle

    def _scale(self, key):
        control = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 50, 100, 1)
        control.set_size_request(168, -1)
        control.set_draw_value(True)
        control.set_value_pos(Gtk.PositionType.RIGHT)
        control.set_digits(0)
        self.config.bind(key, control.get_adjustment(), 'value', Gio.SettingsBindFlags.DEFAULT)
        self.controls[key] = control
        return control

    @staticmethod
    def _action(text, callback):
        button = Gtk.Button(label=text)
        button.connect('clicked', callback)
        return button

    def _page(self):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        body.set_margin_start(22)
        body.set_margin_end(22)
        body.set_margin_top(12)
        body.set_margin_bottom(22)
        scroll.add(body)
        return scroll, body

    def _appearance_page(self):
        scroll, body = self._page()
        format_ = Gtk.ComboBoxText()
        for value in ('12-hour (AM/PM)', '24-hour (0–23)', '24-hour (00–23)'):
            format_.append_text(value)
        format_.set_size_request(178, -1)
        self.config.bind('time-format', format_, 'active', Gio.SettingsBindFlags.DEFAULT)
        self.controls['time-format'] = format_
        body.pack_start(self._section('Display', [
            self._row('Time format', widget=format_),
            self._row('Clock size', widget=self._scale('scale')),
            self._row('Brightness', widget=self._scale('brightness')),
            self._row('Show flaps', 'Keep the split-card background visible.', self._switch('background')),
            self._row('Flip animation', 'Animate the digits when the minute changes.',
                      self._switch('flip-animation')),
        ]), False, False, 0)

        fonts = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        fonts.pack_start(self._action('Import…', self.import_font), False, False, 0)
        reset = self._action('↶', self.reset_font)
        reset.set_tooltip_text('Use the default system font')
        fonts.pack_start(reset, False, False, 0)
        body.pack_start(self._section('Typography', [
            self._row('Clock font', 'Import an OTF font or a Fliqlo package you own.', fonts),
        ]), False, False, 0)
        return scroll

    def _screensaver_page(self):
        scroll, body = self._page()
        idle = Gtk.SpinButton.new_with_range(10, 7200, 10)
        idle.set_numeric(True)
        self.config.bind('idle-seconds', idle.get_adjustment(), 'value', Gio.SettingsBindFlags.DEFAULT)
        self.controls['idle-seconds'] = idle
        body.pack_start(self._section('GNOME integration', [
            self._row('Shell extension', 'Required to start the clock automatically.',
                      self._action('Enable', self.enable_extension)),
            self._row('Start when idle', 'Show the clock while the session is unlocked.',
                      self._switch('idle-enabled')),
            self._row('All displays', 'Otherwise, show the clock only on the primary display.',
                      self._switch('multiple-displays')),
            self._row('Idle delay (seconds)', 'Keep this shorter than the screen blank timeout.', idle),
        ]), False, False, 0)
        body.pack_start(self._section('Privacy & power', [
            self._row('Your lock screen stays in control',
                      'The clock gives way when GNOME locks or turns off the display.',
                      self._action('Power Settings', self.open_power)),
        ]), False, False, 0)
        return scroll

    def refresh_status(self):
        info = extension_info()
        state = info.get('state')
        if state == 1:
            message = '✓ GNOME extension is enabled. The clock will appear when idle.'
        elif state == 3:
            message = 'Extension error: ' + str(info.get('error', 'Check GNOME Shell logs.'))
        elif state == 4:
            message = 'Unsupported GNOME Shell version. This release targets GNOME 50 (Ubuntu 26.04).'
        elif info:
            message = 'Extension is disabled. Open the Screensaver tab and select Enable.'
        else:
            message = 'If you just installed it, log out and log back in, then enable the extension.'
        self.status.set_text(message)

    def enable_extension(self, _button):
        try:
            result = subprocess.run(['gnome-extensions', 'enable', UUID], capture_output=True, text=True, timeout=5)
            if result.returncode:
                self.status.set_text('GNOME could not enable the extension. Log out and back in, then try again.\n' + result.stderr.strip())
            else:
                self.refresh_status()
        except (OSError, subprocess.TimeoutExpired) as error:
            self.status.set_text(str(error))

    def preview(self, _button):
        if extension_info().get('state') == 1:
            value = self.config.get_int('preview-token')
            self.config.set_int('preview-token', (value + 1) % 2147483647)
        else:
            window = Gtk.Window(title='Fliqlo — Preview')
            window.set_application(self.get_application())
            window.add(Clock(self.config))
            window.fullscreen()
            window.add_events(Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.BUTTON_PRESS_MASK)
            start = time.monotonic()
            def dismiss(*_args):
                if time.monotonic() - start > .3:
                    window.destroy()
                return True
            for event in ('key-press-event', 'button-press-event', 'motion-notify-event'):
                window.connect(event, dismiss)
            window.show_all()
            display = window.get_display()
            window.get_window().set_cursor(Gdk.Cursor.new_for_display(display, Gdk.CursorType.BLANK_CURSOR))

    def reset_font(self, _button):
        self.config.set_string('font-family', 'DejaVu Sans')

    def open_power(self, _button):
        try:
            Gio.Subprocess.new(['gnome-control-center', 'power'], Gio.SubprocessFlags.NONE)
        except GLib.Error as error:
            self.status.set_text(error.message)

    def import_font(self, _button):
        chooser = Gtk.FileChooserDialog(title='Choose a ZIP, SCR, DMG or OTF file', parent=self,
            action=Gtk.FileChooserAction.OPEN)
        chooser.add_buttons('Cancel', Gtk.ResponseType.CANCEL, 'Import', Gtk.ResponseType.OK)
        filter_ = Gtk.FileFilter()
        filter_.set_name('Fliqlo ZIP / SCR / DMG / OTF')
        filter_.add_pattern('*.dmg')
        filter_.add_pattern('*.otf')
        filter_.add_pattern('*.zip')
        filter_.add_pattern('*.scr')
        chooser.add_filter(filter_)
        selected = chooser.get_filename() if chooser.run() == Gtk.ResponseType.OK else None
        chooser.destroy()
        if not selected:
            return
        try:
            path = Path(selected)
            if path.suffix.lower() in ('.zip', '.scr'):
                data = windows_font(path)
            elif path.suffix.lower() == '.dmg':
                seven = shutil.which('7zz') or shutil.which('7z')
                if not seven:
                    raise ValueError('7zip is required to read DMG files: sudo apt install 7zip')
                with tempfile.TemporaryFile() as extracted:
                    result = subprocess.run([seven, 'x', '-so', str(path),
                        'Fliqlo.saver/Contents/Resources/Fliqlo.otf'], stdout=extracted,
                        stderr=subprocess.PIPE, timeout=30)
                    extracted.seek(0, 2)
                    if result.returncode or extracted.tell() > 1024 * 1024:
                        raise ValueError('Cannot extract a Fliqlo font from this DMG.')
                    extracted.seek(0)
                    data = extracted.read()
            else:
                if path.stat().st_size > 1024 * 1024:
                    raise ValueError('The font is larger than 1 MiB.')
                data = path.read_bytes()
            if data[:4] != b'OTTO':
                raise ValueError('The file is not a supported OpenType font.')
            # Validate before replacing an existing local font.
            with tempfile.TemporaryDirectory() as temporary:
                candidate = Path(temporary) / 'Fliqlo.otf'
                candidate.write_bytes(data)
                family = subprocess.run(['fc-scan', '--format', '%{family}', str(candidate)],
                    capture_output=True, text=True, timeout=5)
                families = {name.strip() for name in family.stdout.split(',')}
                font_family = 'Fliqlo Bold' if 'Fliqlo Bold' in families else 'Fliqlo' if 'Fliqlo' in families else None
                if family.returncode or font_family is None:
                    raise ValueError('The selected font is not a Fliqlo font.')
            directory = Path(GLib.get_user_data_dir()) / 'fonts/fliqlo-ubuntu'
            directory.mkdir(parents=True, exist_ok=True)
            pending = directory / 'Fliqlo.otf.tmp'
            pending.write_bytes(data)
            os.replace(pending, directory / 'Fliqlo.otf')
            subprocess.run(['fc-cache', '-f', str(directory)], check=True, timeout=15,
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            self.config.set_string('font-family', font_family)
            self.status.set_text('Font imported for this account. Log out and back in to refresh GNOME fonts.')
        except (OSError, ValueError, RuntimeError, zipfile.BadZipFile, subprocess.SubprocessError) as error:
            self.status.set_text('Unable to import the font: ' + str(error))


class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='io.github.luan_thnh.FliqloUbuntu', flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self):
        if self.get_active_window():
            self.get_active_window().present()
        else:
            Preferences(self, settings())


if __name__ == '__main__':
    sys.exit(App().run(sys.argv))
