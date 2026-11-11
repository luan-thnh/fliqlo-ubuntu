import Cairo from 'cairo';
import Pango from 'gi://Pango';
import PangoCairo from 'gi://PangoCairo';
import Clutter from 'gi://Clutter';
import GLib from 'gi://GLib';
import Gio from 'gi://Gio';
import Shell from 'gi://Shell';
import St from 'gi://St';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import {idleAllowed, parts, paint, FLIP_MS} from './clock.js';

export default class FliqloExtension extends Extension {
    enable() {
        this._settings = this.getSettings();
        this._idle = global.backend.get_core_idle_monitor();
        this._root = null;
        this._watch = 0;
        this._tick = 0;
        this._animation = 0;
        this._settingsId = this._settings.connect('changed', (_settings, key) => {
            if (key === 'preview-token') {
                this._show();
                return;
            }
            this._hide();
            this._schedule();
        });
        this._sessionId = Main.sessionMode.connect('updated', () => {
            this._hide();
            this._schedule();
        });
        this._monitorId = Main.layoutManager.connect('monitors-changed', () => this._hide());
        this._schedule();
    }

    _allowed() {
        return idleAllowed(true, Main.sessionMode.isLocked, Main.sessionMode.isGreeter,
            (Main.sessionMode.currentMode === 'user' || Main.sessionMode.parentMode === 'user'));
    }

    _schedule() {
        if (this._watch) this._idle.remove_watch(this._watch);
        this._watch = 0;
        if (!this._settings.get_boolean('idle-enabled') || !this._allowed()) return;
        this._watch = this._idle.add_idle_watch(this._settings.get_int('idle-seconds') * 1000,
            () => this._show());
    }

    _show() {
        if (this._root || !this._allowed()) return;
        try {
            this._present();
        } catch (error) {
            this._hide();
            console.error('Fliqlo Ubuntu: cannot show screensaver', error);
        }
    }

    _photos() {
        const images = this._settings.get_strv('background-image-uris').slice(0, 20);
        const legacy = this._settings.get_string('background-image-uri');
        return images.length ? images : (legacy ? [legacy] : []);
    }

    _setImageLayer(layer, uri) {
        // The user-selected URI is never evaluated as CSS unless strictly local and safe.
        if (!/^file:\/\/\/[A-Za-z0-9._~%/-]+$/i.test(uri) ||
            !/\.(png|jpe?g|webp)$/i.test(uri)) {
            layer.set_style('background-image: none;');
            return;
        }
        try {
            const file = Gio.File.new_for_uri(uri);
            const info = file.query_info('standard::size,standard::type',
                Gio.FileQueryInfoFlags.NONE, null);
            if (info.get_file_type() !== Gio.FileType.REGULAR ||
                info.get_size() > 16 * 1024 * 1024) {
                layer.set_style('background-image: none;');
                return;
            }
            const fit = ['cover', 'contain', '100% 100%', 'auto'][
                Math.max(0, Math.min(3, this._settings.get_int('background-fit')))];
            layer.set_style(`background-image: url("${uri}"); background-size: ${fit}; background-repeat: no-repeat; background-position: center;`);
        } catch (error) {
            console.warn('Fliqlo Ubuntu: invalid custom background', error);
            layer.set_style('background-image: none;');
        }
    }

    _addBackdrop(monitor, mode) {
        if (mode === 0) return;
        const position = {x: monitor.x, y: monitor.y, width: monitor.width, height: monitor.height};
        const dim = Math.max(0, Math.min(90, this._settings.get_int('background-dim')));

        if (mode === 1) {
            const color = this._settings.get_string('background-color');
            if (/^#[0-9a-fA-F]{6}$/.test(color))
                this._root.add_child(new St.Widget({...position, style: `background-color: ${color};`}));
        } else if (mode === 2) {
            const layer = new St.Widget({...position,
                opacity: Math.round(Math.max(0, Math.min(100,
                    this._settings.get_int('background-opacity'))) * 255 / 100)});
            this._setImageLayer(layer, this._imageLibrary[this._imageIndex] || '');
            this._root.add_child(layer);
            this._imageLayers.push(layer);
        }
        if (dim > 0)
            this._root.add_child(new St.Widget({...position,
                style: `background-color: rgba(0,0,0,${dim / 100});`}));
    }

    _present() {
        this._root = new St.Widget({reactive: true, can_focus: true,
            layout_manager: new Clutter.FixedLayout(),
            style: 'background-color: black;', x: 0, y: 0,
            width: global.stage.width, height: global.stage.height});
        Main.layoutManager.addTopChrome(this._root, {trackFullscreen: false});
        this._areas = [];
        this._imageLayers = [];
        this._imageLibrary = this._photos();
        this._imageIndex = Math.max(0, Math.min(
            this._settings.get_int('background-selected-index'), this._imageLibrary.length - 1));
        this._nextSlide = GLib.get_monotonic_time() +
            this._settings.get_int('background-slideshow-seconds') * 1000000;
        const backdropMode = this._settings.get_int('background-mode');
        const options = {
            scale: this._settings.get_int('scale'),
            brightness: this._settings.get_int('brightness'),
            background: this._settings.get_boolean('background'),
            flapColorsEnabled: this._settings.get_boolean('flap-colors-enabled'),
            flapBackgroundColor: this._settings.get_string('flap-background-color'),
            flapDigitColor: this._settings.get_string('flap-digit-color'),
            font: this._settings.get_string('font-family'),
            transparentBackdrop: backdropMode !== 0,
        };
        this._current = parts(new Date(), this._settings.get_int('time-format'));
        this._previous = null;
        this._progress = 1;
        for (const monitor of Main.layoutManager.monitors) {
            if (!this._settings.get_boolean('multiple-displays') &&
                monitor.index !== Main.layoutManager.primaryIndex) continue;
            this._addBackdrop(monitor, backdropMode);
            const area = new St.DrawingArea({x: monitor.x, y: monitor.y,
                width: monitor.width, height: monitor.height});
            area.connect('repaint', () => {
                const cr = area.get_context();
                try {
                    const [width, height] = area.get_surface_size();
                    const progress = this._progress;
                    paint(cr, width, height, this._current, this._previous, progress, options, {LinearGradient: Cairo.LinearGradient, Operator: Cairo.Operator, ImageSurface: Cairo.ImageSurface, Format: Cairo.Format, Context: Cairo.Context, Pango, PangoCairo});
                } finally {
                    cr.$dispose();
                }
            });
            this._root.add_child(area);
            this._areas.push(area);
        }
        this._root.connect('captured-event', (_actor, event) => {
            if ([Clutter.EventType.KEY_PRESS, Clutter.EventType.BUTTON_PRESS,
                Clutter.EventType.MOTION, Clutter.EventType.TOUCH_BEGIN,
                Clutter.EventType.SCROLL].includes(event.type())) this._hide();
            return Clutter.EVENT_STOP;
        });
        this._grab = Main.pushModal(this._root, {actionMode: Shell.ActionMode.NORMAL});
        if (this._grab.is_revoked()) {
            this._hide();
            return;
        }
        this._tick = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 250, () => {
            if (this._settings.get_int('background-mode') === 2 &&
                this._settings.get_boolean('background-slideshow') &&
                this._imageLibrary.length > 1 && GLib.get_monotonic_time() >= this._nextSlide) {
                this._imageIndex = (this._imageIndex + 1) % this._imageLibrary.length;
                for (const layer of this._imageLayers)
                    this._setImageLayer(layer, this._imageLibrary[this._imageIndex]);
                this._nextSlide = GLib.get_monotonic_time() +
                    this._settings.get_int('background-slideshow-seconds') * 1000000;
            }
            const next = parts(new Date(), this._settings.get_int('time-format'));
            if (JSON.stringify(next) !== JSON.stringify(this._current)) {
                this._previous = this._current;
                this._current = next;
                if (!this._settings.get_boolean('flip-animation')) {
                    this._progress = 1;
                    this._areas.forEach(area => area.queue_repaint());
                } else {
                    this._progress = 0;
                    const timeline = Clutter.Timeline.new_for_actor(this._root, FLIP_MS);
                    this._animation = timeline;
                    timeline.connect('new-frame', animation => {
                        this._progress = animation.get_elapsed_time() / FLIP_MS;
                        this._areas.forEach(area => area.queue_repaint());
                    });
                    timeline.connect('completed', () => {
                        this._progress = 1;
                        this._animation = null;
                    });
                    timeline.start();
                }
            }
            return GLib.SOURCE_CONTINUE;
        });
        this._root.set_cursor_type(Clutter.CursorType.NONE);
    }

    _hide() {
        if (this._animation) this._animation.stop();
        this._animation = null;
        if (this._tick) GLib.Source.remove(this._tick);
        this._tick = 0;
        if (this._grab) {
            Main.popModal(this._grab);
            this._grab = null;
        }
        if (this._root) {
            Main.layoutManager.removeChrome(this._root);
            this._root.destroy();
            this._root = null;
        }
        this._areas = [];
        this._imageLayers = [];
        this._imageLibrary = [];
    }

    disable() {
        this._hide();
        if (this._watch) this._idle.remove_watch(this._watch);
        this._watch = 0;
        this._settings.disconnect(this._settingsId);
        Main.sessionMode.disconnect(this._sessionId);
        Main.layoutManager.disconnect(this._monitorId);
        this._settings = null;
        this._idle = null;
    }
}
