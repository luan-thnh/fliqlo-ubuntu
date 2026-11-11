// Values come from the supplied Windows renderer; public format IDs stay stable.
export const FLIP_MS = 330;
export function parts(date, format) {
    const hour = date.getHours();
    return {hours: format === 0 ? String(hour % 12 || 12)
        : format === 1 ? String(hour) : String(hour).padStart(2, '0'),
    minutes: String(date.getMinutes()).padStart(2, '0'),
    period: format === 0 ? (hour < 12 ? 'AM' : 'PM') : ''};
}
export function geometry(width, height, scale) {
    const vertical = width < height;
    const unit = Math.min(width / (vertical ? 700 : 1350), height / (vertical ? 1350 : 700)) * Math.max(50, Math.min(100, scale)) / 100;
    const side = 600 * unit, gap = 50 * unit;
    return {side, gap, x: (width - (vertical ? side : side * 2 + gap)) / 2,
        y: (height - (vertical ? side * 2 + gap : side)) / 2, vertical};
}
export function idleAllowed(enabled, locked, greeter, sessionActive) {
    return enabled && !locked && !greeter && sessionActive;
}
export function digitIndent(value) {
    return value === '1' ? -7.5 : value === '11' ? 12 : value.endsWith('1') ? 24 : 0;
}
export function ease(value, outgoing = false) {
    const [x1, x2] = outgoing ? [0, .58] : [.42, 1];
    let low = 0, high = 1;
    for (let i = 0; i < 24; i++) {
        const t = (low + high) / 2;
        const x = 3 * (1 - t) ** 2 * t * x1 + 3 * (1 - t) * t ** 2 * x2 + t ** 3;
        if (x < value) low = t; else high = t;
    }
    const t = (low + high) / 2;
    return 3 * (1 - t) * t * t + t ** 3;
}
function rounded(cr, x, y, width, height, radius) {
    cr.newSubPath();
    cr.arc(x + width - radius, y + radius, radius, -Math.PI / 2, 0);
    cr.arc(x + width - radius, y + height - radius, radius, 0, Math.PI / 2);
    cr.arc(x + radius, y + height - radius, radius, Math.PI / 2, Math.PI);
    cr.arc(x + radius, y + radius, radius, Math.PI, Math.PI * 1.5);
    cr.closePath();
}
function hexRgb(value, fallback) {
    if (typeof value !== 'string' || !/^#[0-9a-f]{6}$/i.test(value)) return fallback;
    return [1, 3, 5].map(position => parseInt(value.slice(position, position + 2), 16) / 255);
}
function card(cr, value, period, options, offset, brightness, Cairo) {
    if (options.background) {
        for (const [inset, top, bottom] of [[0, 22, 12], [1, 17, 11]]) {
            const gradient = new Cairo.LinearGradient(0, offset + inset, 0, offset + 600 - inset);
            if (options.flapColorsEnabled) {
                const rgb = hexRgb(options.flapBackgroundColor, [0.09, 0.09, 0.09]);
                gradient.addColorStopRGB(0, ...rgb.map(c => Math.min(1, c * brightness * (inset ? 1.02 : 1.10))));
                gradient.addColorStopRGB(1, ...rgb.map(c => Math.min(1, c * brightness * (inset ? .79 : .85))));
            } else {
                gradient.addColorStopRGB(0, ...Array(3).fill(top / 255 * brightness));
                gradient.addColorStopRGB(1, ...Array(3).fill(bottom / 255 * brightness));
            }
            rounded(cr, inset, offset + inset, 600 - inset * 2, 600 - inset * 2, 50 - inset);
            cr.setSource(gradient); cr.fill();
        }
    }
    const original = ['Fliqlo', 'Fliqlo Bold'].includes(options.font);
    const squeeze = original ? 1 : .64;
    if (options.flapColorsEnabled) {
        const digits = hexRgb(options.flapDigitColor, [1, 1, 1]);
        cr.setSourceRGBA(...digits.map(c => c * brightness), .95);
    } else {
        cr.setSourceRGBA(brightness, brightness, brightness, .711);
    }
    text(cr, value, 600, options.font, 300 + digitIndent(value), offset + 523, squeeze, true, Cairo);
    if (period) text(cr, period, 60, options.font, 38, offset + (period === 'AM' ? 122.4 : 522.4), squeeze, false, Cairo);
}
function text(cr, value, size, family, x, baseline, squeeze, centered, api) {
    const {Pango, PangoCairo} = api;
    const layout = PangoCairo.create_layout(cr), font = new Pango.FontDescription();
    font.set_family(family); font.set_weight(family === 'Fliqlo' ? Pango.Weight.NORMAL : Pango.Weight.BOLD); font.set_absolute_size(size * Pango.SCALE);
    layout.set_font_description(font); layout.set_text(value, -1);
    const width = layout.get_size()[0] / Pango.SCALE;
    cr.save(); cr.translate(x, baseline); cr.scale(squeeze, 1);
    cr.moveTo(centered ? -width / 2 : 0, -layout.get_baseline() / Pango.SCALE);
    PangoCairo.show_layout(cr, layout); cr.restore();
}

function half(cr, value, period, bottom, factor, options, light, Cairo) {
    if (factor < .00001) return;
    if (factor < .999999) {projectHalf(cr, value, period, bottom, factor, options, light, Cairo); return;}
    cr.save();
    const pivot = bottom ? 303 : 299;
    cr.translate(0, pivot); cr.scale(1, factor); cr.translate(0, -pivot);
    cr.rectangle(0, bottom ? 303 : -1, 600, 298); cr.clip();
    cr.setSourceRGB(0, 0, 0); cr.paint();
    const brightness = options.brightness / 100 * light;
    if (brightness > 1) cr.pushGroup();
    const drawBrightness = Math.min(1, brightness);
    card(cr, value, period, options, bottom ? 1 : -1, drawBrightness, Cairo);
    const border = options.background ? (bottom ? 21 : 8) / 255 * drawBrightness : 0;
    cr.setSourceRGB(border, border, border); cr.rectangle(0, bottom ? 303 : 296, 600, 1); cr.fill();
    if (brightness > 1) {cr.popGroupToSource(); cr.paint(); cr.setOperator(Cairo.Operator.ADD); cr.paintWithAlpha(brightness - 1);}
    cr.restore();
}
function projectHalf(cr, value, period, bottom, factor, options, light, api) {
    const unit = options.unit ?? 1, phase = options.yPhase ?? 0;
    const pivot = bottom ? 303 : 299, origin = bottom ? 303 : -1;
    const sine = Math.sqrt(Math.max(0, 1 - factor * factor)) * (bottom ? 1 : -1);
    const surface = new api.ImageSurface(api.Format.ARGB32, Math.ceil(600 * unit), Math.ceil(298 * unit));
    const texture = new api.Context(surface);
    texture.scale(unit, unit); texture.translate(0, -origin);
    half(texture, value, period, bottom, 1, options, light, api);
    texture.$dispose();
    const project = y => 300 + (pivot - 300 + (y - pivot) * factor) / (1 - (y - pivot) * sine / 4000);
    for (let row = Math.floor(project(origin) * unit + phase); row < Math.ceil(project(origin + 298) * unit + phase); row++) {
        const screenY = (row - phase + .5) / unit;
        const relative = (screenY - pivot) / (factor + (screenY - 300) * sine / 4000);
        const sourceY = pivot + relative;
        if (sourceY < origin || sourceY > origin + 298) continue;
        const perspective = 1 / (1 - relative * sine / 4000);
        cr.save(); cr.translate(300 * (1 - perspective), (row - phase) / unit);
        cr.scale(perspective / unit, 1 / unit);
        cr.setSourceSurface(surface, 0, -(sourceY - origin) * unit + .5);
        cr.rectangle(0, 0, 600 * unit, 1); cr.fill(); cr.restore();
    }
    surface.finish();
}

export function paint(cr, width, height, current, previous, progress, options, Cairo) {
    if (options.transparentBackdrop) {
        cr.setOperator(Cairo.Operator.CLEAR);
        cr.paint();
        cr.setOperator(Cairo.Operator.OVER);
    } else {
        cr.setSourceRGB(0, 0, 0);
        cr.paint();
    }
    const {side, gap, x, y, vertical} = geometry(width, height, options.scale);
    ['hours', 'minutes'].forEach((key, index) => {
        cr.save(); cr.translate(x + (vertical ? 0 : index * (side + gap)), y + (vertical ? index * (side + gap) : 0)); cr.scale(side / 600, side / 600);
        // Match the native rounded-card mask, including the black backing
        // and projected flip animation, so no square corners show through.
        rounded(cr, 0, 0, 600, 600, 50);
        cr.clip();
        const frameOptions = {...options, unit: side / 600, yPhase: (y + (vertical ? index * (side + gap) : 0)) % 1};
        const period = index === 0 ? current.period : '';
        const changed = previous && (previous[key] !== current[key] || (index === 0 && previous.period !== period));
        if (!changed || progress >= 1) {
            half(cr, current[key], period, false, 1, frameOptions, 1, Cairo);
            half(cr, current[key], period, true, 1, frameOptions, 1, Cairo);
        } else {
            const oldPeriod = index === 0 ? previous.period : '';
            const t = Math.min(1, Math.max(0, progress * 2));
            const oldLight = progress < .5 ? (t <= .66 ? 1 : 1 - .5 * ease((t - .66) / .34, true)) : .5 - .4 * ease(progress * 2 - 1, true);
            half(cr, current[key], period, false, 1, frameOptions, .1 + .9 * ease(t), Cairo);
            half(cr, previous[key], oldPeriod, true, 1, frameOptions, oldLight, Cairo);
            if (progress < .5) {
                const eased = ease(t);
                half(cr, previous[key], oldPeriod, false, Math.cos(eased * Math.PI / 2), frameOptions, 1 - .6 * eased, Cairo);
            } else {
                const eased = ease(progress * 2 - 1, true);
                half(cr, current[key], period, true, Math.sin(eased * Math.PI / 2), frameOptions, 2 - eased, Cairo);
            }
        }
        cr.setSourceRGB(0, 0, 0); cr.rectangle(0, 297, 600, 6); cr.fill();
        cr.restore();
    });
}
