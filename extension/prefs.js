// Generated with AI for personal use.
// Do NOT upload to extensions.gnome.org (EGO) unless you understand JavaScript
// and can maintain this code.
import Adw from 'gi://Adw';
import Gio from 'gi://Gio';
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
