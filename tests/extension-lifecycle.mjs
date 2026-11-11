// Shell lifecycle simulation; this does not replace a GNOME 50 / Wayland session test.
import {api} from './drawing-api.mjs';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const load = async path => import(`data:text/javascript;base64,${Buffer.from(readFileSync(new URL(path, import.meta.url), 'utf8')).toString('base64')}`);
const {parts, paint, idleAllowed, FLIP_MS} = await load('../extension/clock.js');
class Signals {
    constructor() {this.signals = new Map(); this.next = 1;}
    connect(name, callback) {const id = this.next++; this.signals.set(id, {name, callback}); return id;}
    disconnect(id) {this.signals.delete(id);}
    emit(name, ...args) {for (const signal of [...this.signals.values()]) if (signal.name === name) signal.callback(this, ...args);}
}
class Actor extends Signals {
    constructor(props) {super(); Object.assign(this, props); this.children = [];}
    add_child(child) {this.children.push(child);}
    destroy() {this.destroyed = true; this.signals.clear();}
    set_cursor_type() {}
    queue_repaint() {this.repainted = true;}
}
const config = new Signals();
config.values = {'idle-enabled': true, 'idle-seconds': 120, scale: 100, brightness: 100,
    'flip-animation': true, background: true, 'multiple-displays': true, 'time-format': 0, 'font-family': 'DejaVu Sans'};
config.get_boolean = config.get_int = config.get_string = key => config.values[key];
const idleWatches = new Map(); let nextWatch = 1;
const idle = {add_idle_watch(ms, cb) {const id = nextWatch++; idleWatches.set(id, {ms, cb}); return id;}, remove_watch(id) {idleWatches.delete(id);}};
const timers = new Map(); let nextTimer = 1;
const GLib = {PRIORITY_DEFAULT: 0, SOURCE_REMOVE: false, SOURCE_CONTINUE: true,
    timeout_add(_priority, _interval, cb) {const id = nextTimer++; timers.set(id, cb); return id;},
    Source: {remove(id) {timers.delete(id);}}};
const session = Object.assign(new Signals(), {currentMode: 'ubuntu', parentMode: 'user', isLocked: false, isGreeter: false});
const layout = Object.assign(new Signals(), {primaryIndex: 0,
    monitors: [{x: 0, y: 0, width: 1920, height: 1080, index: 0}, {x: 1920, y: 0, width: 1920, height: 1080, index: 1}]});
const roots = new Set(); let grabs = 0; let failGrab = false;
layout.addTopChrome = actor => roots.add(actor);
layout.removeChrome = actor => roots.delete(actor);
const Main = {sessionMode: session, layoutManager: layout,
    pushModal() {if (failGrab) throw Error('simulated grab failure'); grabs++; return {is_revoked: () => false};},
    popModal() {grabs--;}};
const global = {backend: {get_core_idle_monitor: () => idle}, stage: {width: 3840, height: 1080}};
const St = {Widget: Actor, DrawingArea: Actor, Settings: {get: () => ({enable_animations: false})}};
class Timeline extends Signals {
    static new_for_actor(actor, duration) {const timeline = new Timeline(); timeline.duration = duration; return timeline;}
    start() {this.playing = true;}
    stop() {this.playing = false;}
    get_elapsed_time() {return this.elapsed;}
    advance(elapsed) {
        if (!this.playing) return;
        this.elapsed = elapsed;
        this.emit('new-frame');
        if (elapsed >= this.duration) {this.playing = false; this.emit('completed');}
    }
}
const Clutter = {Timeline, FixedLayout: class {}, CursorType: {NONE: 0}, EVENT_STOP: true, EventType: {KEY_PRESS: 1, BUTTON_PRESS: 2, MOTION: 3, TOUCH_BEGIN: 4, SCROLL: 5}};
const Shell = {ActionMode: {NORMAL: 1}};
class Extension {getSettings() {return config;}}
const source = readFileSync(new URL('../extension/extension.js', import.meta.url), 'utf8')
    .replace(/^import .*;\n/gm, '').replace('export default class FliqloExtension', 'class FliqloExtension');
const quietConsole = {error() {}};
const Factory = new Function('Clutter', 'GLib', 'Shell', 'St', 'Extension', 'Main', 'idleAllowed', 'parts', 'paint', 'global', 'console', 'Cairo', 'Pango', 'PangoCairo', 'FLIP_MS', `${source}\nreturn FliqloExtension;`);
const Fliqlo = Factory(Clutter, GLib, Shell, St, Extension, Main, idleAllowed, parts, paint, global, quietConsole, api, api.Pango, api.PangoCairo, FLIP_MS);
const ext = new Fliqlo();
ext.enable();
assert.equal(idleWatches.size, 1, 'Ubuntu child session must arm idle');
assert.equal([...idleWatches.values()][0].ms, 120000);
[...idleWatches.values()][0].cb();
assert.equal(roots.size, 1); assert.equal(grabs, 1); assert.equal(ext._areas.length, 2);
// Exercise the live minute-change timer with desktop animations OFF.
ext._current = {hours:'0', minutes:'99', period:''};
timers.get(ext._tick)();
assert.equal(ext._progress, 0, 'per-app flip stays enabled when desktop effects are off');
const timeline = ext._animation;
assert(timeline.playing);
assert.equal(timers.size, 1, 'animation must not add a competing high-priority timeout');
timeline.advance(100);
assert.equal(ext._progress, 100 / FLIP_MS);
assert(ext._areas.every(area => area.repainted));
timeline.advance(FLIP_MS);
assert.equal(ext._progress, 1);
assert.equal(ext._animation, null);
config.values['flip-animation'] = false;
ext._current = {hours:'0', minutes:'99', period:''};
timers.get(ext._tick)();
assert.equal(ext._progress, 1, 'explicit reduced-motion choice disables flips');
config.values['flip-animation'] = true;
ext._current = {hours:'0', minutes:'99', period:''};
timers.get(ext._tick)();
const interrupted = ext._animation;
assert(interrupted.playing);
ext._root.emit('captured-event', {type: () => Clutter.EventType.MOTION});
assert.equal(roots.size, 0, 'first user input must dismiss the screensaver');
assert(!interrupted.playing, 'dismissing an active flip must stop its frame-clock timeline');
[...idleWatches.values()][0].cb();
session.isLocked = true; session.currentMode = 'unlock-dialog'; session.emit('updated');
assert.equal(roots.size, 0); assert.equal(timers.size, 0); assert.equal(grabs, 0); assert.equal(idleWatches.size, 0);
config.emit('changed', 'preview-token'); assert.equal(roots.size, 0, 'preview must never cover the lock screen');
session.isLocked = false; session.currentMode = 'ubuntu'; session.emit('updated');
config.values['multiple-displays'] = false;
config.emit('changed', 'multiple-displays');
[...idleWatches.values()][0].cb(); assert.equal(ext._areas.length, 1);
layout.emit('monitors-changed'); assert.equal(roots.size, 0); assert.equal(grabs, 0);
failGrab = true; config.emit('changed', 'preview-token');
assert.equal(roots.size, 0, 'failed activation must clean up its overlay');
failGrab = false;
config.values['idle-enabled'] = false; config.emit('changed', 'idle-enabled');
assert.equal(idleWatches.size, 0);
config.emit('changed', 'preview-token'); assert.equal(roots.size, 1, 'manual preview works when auto activation is off');
ext.disable();
assert.equal(roots.size + grabs + timers.size + idleWatches.size, 0);
assert.equal(config.signals.size + layout.signals.size + session.signals.size, 0);
console.log('Shell simulation: Ubuntu session, idle activation, multi-monitor, lock dismissal, failed grab, settings changes and disable cleanup passed.');
