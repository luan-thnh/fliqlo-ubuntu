// Generated with AI for personal use.
// Do NOT upload to extensions.gnome.org (EGO) unless you understand JavaScript
// and can maintain this code.
import Adw from 'gi://Adw';
import Gio from 'gi://Gio';
import Gdk from 'gi://Gdk';
import Gtk from 'gi://Gtk';
import {ExtensionPreferences} from 'resource:///org/gnome/Shell/Extensions/js/extensions/prefs.js';

// Native preferences work without the standalone Debian settings application.
export default class FliqloPreferences extends ExtensionPreferences {
    fillPreferencesWindow(window) {
        const settings = this.getSettings();

        const appearance = new Adw.PreferencesPage({
            title: 'Appearance',
            icon_name: 'preferences-desktop-display-symbolic',
        });
        const display = new Adw.PreferencesGroup({
            title: 'Display',
            description: 'Changes are saved automatically and appear in the next preview.',
        });
        const timeFormat = new Adw.ComboRow({
            title: 'Time format',
            model: Gtk.StringList.new(['12-hour (AM/PM)', '24-hour (0–23)', '24-hour (00–23)']),
        });
        settings.bind('time-format', timeFormat, 'selected', Gio.SettingsBindFlags.DEFAULT);
        display.add(timeFormat);
        for (const [key, title] of [['scale', 'Clock size (%)'], ['brightness', 'Brightness (%)']]) {
            const row = new Adw.SpinRow({
                title,
                adjustment: new Gtk.Adjustment({
                    lower: 50, upper: 100, step_increment: 1, page_increment: 10,
                }),
            });
            settings.bind(key, row, 'value', Gio.SettingsBindFlags.DEFAULT);
            display.add(row);
        }
        this._addSwitch(display, settings, 'background', 'Show flaps',
            'Keep the split-card background visible.');
        this._addSwitch(display, settings, 'flip-animation', 'Flip animation',
            'Animate the digits when the minute changes.');
        appearance.add(display);

        const background = new Adw.PreferencesGroup({
            title: 'Background',
            description: 'Use the classic black backdrop, a solid color, or a local image. Images are not uploaded.',
        });
        const mode = new Adw.ComboRow({
            title: 'Backdrop',
            subtitle: 'Keep classic black, pick a color, or use a photo.',
            model: Gtk.StringList.new(['None (black)', 'Solid color', 'Image']),
        });
        settings.bind('background-mode', mode, 'selected', Gio.SettingsBindFlags.DEFAULT);
        background.add(mode);

        const colorRow = new Adw.ActionRow({title: 'Solid color'});
        const colorDialog = new Gtk.ColorDialog();
        const colorButton = new Gtk.ColorDialogButton({dialog: colorDialog, valign: Gtk.Align.CENTER});
        const rgba = new Gdk.RGBA();
        rgba.parse(settings.get_string('background-color'));
        colorButton.set_rgba(rgba);
        colorButton.connect('notify::rgba', button => {
            const c = button.get_rgba();
            const hex = '#' + [c.red, c.green, c.blue].map(channel =>
                Math.round(channel * 255).toString(16).padStart(2, '0')).join('');
            if (hex !== settings.get_string('background-color'))
                settings.set_string('background-color', hex);
        });
        colorRow.add_suffix(colorButton);
        background.add(colorRow);

        const imageRow = new Adw.ActionRow({
            title: 'Image',
            subtitle: 'Local PNG, JPEG or WebP, up to 16 MiB.',
        });
        const choose = new Gtk.Button({label: 'Choose…', valign: Gtk.Align.CENTER});
        choose.connect('clicked', () => {
            const dialog = new Gtk.FileDialog({title: 'Choose a background image'});
            const filter = new Gtk.FileFilter();
            filter.set_name('Images');
            for (const mime of ['image/png', 'image/jpeg', 'image/webp'])
                filter.add_mime_type(mime);
            const filters = new Gio.ListStore({item_type: Gtk.FileFilter});
            filters.append(filter);
            dialog.set_filters(filters);
            dialog.open(window, null, (picker, result) => {
                try {
                    const file = picker.open_finish(result);
                    if (!file) return;
                    const info = file.query_info('standard::size,standard::type',
                        Gio.FileQueryInfoFlags.NONE, null);
                    if (info.get_file_type() !== Gio.FileType.REGULAR ||
                        info.get_size() > 16 * 1024 * 1024)
                        throw new Error('Please select a local image under 16 MiB.');
                    settings.set_string('background-image-uri', file.get_uri());
                    settings.set_int('background-mode', 2);
                } catch (error) {
                    if (!error.matches?.(Gio.IOErrorEnum, Gio.IOErrorEnum.CANCELLED))
                        console.warn('Fliqlo Ubuntu: invalid image selection', error);
                }
            });
        });
        imageRow.add_suffix(choose);
        const clear = new Gtk.Button({label: 'Clear', valign: Gtk.Align.CENTER});
        clear.connect('clicked', () => {
            settings.set_string('background-image-uri', '');
            settings.set_int('background-mode', 0);
        });
        imageRow.add_suffix(clear);
        background.add(imageRow);
        for (const [key, title, subtitle, max] of [
            ['background-opacity', 'Image opacity (%)', 'Blend the photo with black.', 100],
            ['background-dim', 'Dark overlay (%)', 'Keep the digits readable.', 90],
        ]) {
            const row = new Adw.SpinRow({title, subtitle,
                adjustment: new Gtk.Adjustment({
                    lower: 0, upper: max, step_increment: 5, page_increment: 10,
                }),
            });
            settings.bind(key, row, 'value', Gio.SettingsBindFlags.DEFAULT);
            background.add(row);
        }
        const fit = new Adw.ComboRow({
            title: 'Image fit',
            model: Gtk.StringList.new(['Cover', 'Contain', 'Stretch', 'Center']),
        });
        settings.bind('background-fit', fit, 'selected', Gio.SettingsBindFlags.DEFAULT);
        background.add(fit);
        const syncSensitive = () => {
            const value = settings.get_int('background-mode');
            colorRow.set_sensitive(value === 1);
            imageRow.set_sensitive(value === 2);
            fit.set_sensitive(value === 2);
        };
        settings.connect('changed::background-mode', syncSensitive);
        syncSensitive();
        appearance.add(background);

        const typography = new Adw.PreferencesGroup({title: 'Typography'});
        const font = new Adw.EntryRow({title: 'Clock font family'});
        settings.bind('font-family', font, 'text', Gio.SettingsBindFlags.DEFAULT);
        typography.add(font);
        const fontNote = new Adw.ActionRow({
            title: 'Custom Fliqlo font',
            subtitle: 'For a licensed font you already own, import it with the optional desktop app. Otherwise use any installed font family.',
        });
        typography.add(fontNote);
        appearance.add(typography);
        window.add(appearance);

        const screensaver = new Adw.PreferencesPage({
            title: 'Screensaver',
            icon_name: 'preferences-desktop-screensaver-symbolic',
        });
        const integration = new Adw.PreferencesGroup({
            title: 'GNOME integration',
            description: 'The clock appears while your session is unlocked. GNOME lock and power settings remain in control.',
        });
        this._addSwitch(integration, settings, 'idle-enabled', 'Start when idle',
            'Show the clock automatically while inactive.');
        this._addSwitch(integration, settings, 'multiple-displays', 'All displays',
            'Otherwise use the primary monitor.');
        const idle = new Adw.SpinRow({
            title: 'Idle delay (seconds)',
            subtitle: 'Use a delay shorter than the screen blank timeout.',
            adjustment: new Gtk.Adjustment({
                lower: 10, upper: 7200, step_increment: 10, page_increment: 60,
            }),
        });
        settings.bind('idle-seconds', idle, 'value', Gio.SettingsBindFlags.DEFAULT);
        integration.add(idle);
        screensaver.add(integration);

        const actions = new Adw.PreferencesGroup({title: 'Preview'});
        const preview = new Adw.ActionRow({
            title: 'Fullscreen preview',
            subtitle: 'Move the pointer or press a key to close the clock.',
        });
        const previewButton = new Gtk.Button({
            label: 'Preview',
            valign: Gtk.Align.CENTER,
        });
        previewButton.add_css_class('suggested-action');
        previewButton.connect('clicked', () => {
            const value = settings.get_int('preview-token');
            settings.set_int('preview-token', value >= 2147483646 ? 0 : value + 1);
        });
        preview.add_suffix(previewButton);
        actions.add(preview);
        screensaver.add(actions);
        window.add(screensaver);
    }

    _addSwitch(group, settings, key, title, subtitle) {
        const row = new Adw.SwitchRow({title, subtitle});
        settings.bind(key, row, 'active', Gio.SettingsBindFlags.DEFAULT);
        group.add(row);
    }
}
