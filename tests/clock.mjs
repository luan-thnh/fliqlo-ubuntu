import assert from 'node:assert/strict';
import {api} from './drawing-api.mjs';
import {readFileSync} from 'node:fs';
const clockSource = readFileSync(new URL('../extension/clock.js', import.meta.url), 'utf8');
const {parts, geometry, idleAllowed, paint, FLIP_MS, digitIndent, ease} = await import(`data:text/javascript;base64,${Buffer.from(clockSource).toString('base64')}`);
const at = (h, m) => new Date(2026, 0, 1, h, m);
assert.deepEqual(parts(at(0, 0), 0), {hours: '12', minutes: '00', period: 'AM'});
assert.deepEqual(parts(at(12, 0), 0), {hours: '12', minutes: '00', period: 'PM'});
assert.equal(parts(at(3, 9), 1).hours, '3');
assert.equal(parts(at(3, 9), 2).hours, '03');
assert.deepEqual(parts(at(23, 59), 2), {hours: '23', minutes: '59', period: ''});
for (const [width, height] of [[1920, 1080], [3840, 2160], [1080, 1920], [640, 360]]) {
    for (const scale of [25, 100, 150]) {
        const {x, y, side, gap, vertical} = geometry(width, height, scale);
        assert(x >= 0 && y >= 0 && x + (vertical ? side : side * 2 + gap) <= width && y + (vertical ? side * 2 + gap : side) <= height);
    }
}
assert(idleAllowed(true, false, false, true));
assert(!idleAllowed(true, true, false, true));
assert(!idleAllowed(true, false, true, true));
assert(!idleAllowed(false, false, false, true));
// Exercise first frame, both flip phases and final frame through Cairo's drawing contract.
const cr = new Proxy({textExtents: value => ({width: value.length * 40, height: 80, xBearing: 0, yBearing: 0})}, {
    get(target, key) { return target[key] ?? (() => {}); },
});
for (const progress of [0, .25, .5, .75, 1]) paint(cr, 1920, 1080,
    parts(at(12, 0), 0), parts(at(11, 59), 0), progress,
    {scale: 100, brightness: 100, background: true, font: 'DejaVu Sans'}, api);
console.log('Clock: time formats, noon/midnight, monitor bounds, lock guards and animation phases passed.');

assert.equal(FLIP_MS, 330);
assert.deepEqual(geometry(700,1350,100), {side:600,gap:50,x:50,y:50,vertical:true});
assert.deepEqual(['1','11','01','21','12'].map(digitIndent), [-7.5,12,24,24,0]);
assert(Math.abs(ease(.5) + ease(.5,true) - 1) < 1e-6);
