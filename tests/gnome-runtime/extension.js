// Do not enable in a normal desktop session. The test container is disposable.
import GLib from 'gi://GLib';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';
export default class TestHarness extends Extension {
    enable() {
        if (GLib.getenv('FLIQLO_RUNTIME_TEST') !== '1') throw Error('Requires an isolated FLIQLO_RUNTIME_TEST=1 session');
        this._previous = global.context.unsafe_mode;
        global.context.unsafe_mode = true;
    }
    disable() {
        global.context.unsafe_mode = this._previous;
    }
}
