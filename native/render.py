"""600-unit flap geometry and typography recovered from the supplied Windows app."""
import math
import cairo
import gi
gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")
gi.require_foreign("cairo")
from gi.repository import Pango, PangoCairo
from model import geometry, digit_indent, ease


def rounded(cr, x, y, width, height, radius):
    cr.new_sub_path()
    for cx, cy, start in [(x + width - radius, y + radius, -math.pi / 2),
                          (x + width - radius, y + height - radius, 0),
                          (x + radius, y + height - radius, math.pi / 2),
                          (x + radius, y + radius, math.pi)]:
        cr.arc(cx, cy, radius, start, start + math.pi / 2)
    cr.close_path()


def card(cr, value, period, options, offset, brightness):
    if options['background']:
        for inset, top, bottom in [(0, 22, 12), (1, 17, 11)]:
            gradient = cairo.LinearGradient(0, offset + inset, 0, offset + 600 - inset)
            gradient.add_color_stop_rgb(0, *([top / 255 * brightness] * 3))
            gradient.add_color_stop_rgb(1, *([bottom / 255 * brightness] * 3))
            rounded(cr, inset, offset + inset, 600 - inset * 2, 600 - inset * 2, 50 - inset)
            cr.set_source(gradient)
            cr.fill()
    original = options['font'] in ('Fliqlo', 'Fliqlo Bold')
    squeeze = 1 if original else .64
    cr.set_source_rgba(brightness, brightness, brightness, .711)
    text(cr, value, 600, options['font'], 300 + digit_indent(value), offset + 523, squeeze, True)
    if period:
        text(cr, period, 60, options['font'], 38, offset + (122.4 if period == 'AM' else 522.4), squeeze, False)


def text(cr, value, size, family, x, baseline, squeeze, centered):
    layout = PangoCairo.create_layout(cr)
    font = Pango.FontDescription()
    font.set_family(family)
    font.set_weight(Pango.Weight.NORMAL if family == 'Fliqlo' else Pango.Weight.BOLD)
    font.set_absolute_size(size * Pango.SCALE)
    layout.set_font_description(font)
    layout.set_text(value, -1)
    width = layout.get_size()[0] / Pango.SCALE
    cr.save()
    cr.translate(x, baseline)
    cr.scale(squeeze, 1)
    cr.move_to(-width / 2 if centered else 0, -layout.get_baseline() / Pango.SCALE)
    PangoCairo.show_layout(cr, layout)
    cr.restore()


def half(cr, value, period, bottom, factor, options, light=1):
    if factor < .00001:
        return
    if factor < .999999:
        project_half(cr, value, period, bottom, factor, options, light)
        return
    cr.save()
    pivot = 303 if bottom else 299
    cr.translate(0, pivot)
    cr.scale(1, factor)
    cr.translate(0, -pivot)
    cr.rectangle(0, 303 if bottom else -1, 600, 298)
    cr.clip()
    # Opaque black backgrounds prevent alpha from revealing underlying flap text.
    cr.set_source_rgb(0, 0, 0)
    cr.paint()
    brightness = options['brightness'] / 100 * light
    if brightness > 1:
        cr.push_group()
    draw_brightness = min(1, brightness)
    card(cr, value, period, options, 1 if bottom else -1, draw_brightness)
    border = (21 if bottom else 8) / 255 * draw_brightness if options['background'] else 0
    cr.set_source_rgb(border, border, border)
    cr.rectangle(0, 303 if bottom else 296, 600, 1)
    cr.fill()
    if brightness > 1:
        cr.pop_group_to_source()
        cr.paint()
        cr.set_operator(cairo.OPERATOR_ADD)
        cr.paint_with_alpha(brightness - 1)
    cr.restore()


def project_half(cr, value, period, bottom, factor, options, light):
    # Inverse CSS rotateX + perspective(4000), sampled on destination pixel rows.
    unit, phase = options.get('unit', 1), options.get('y_phase', 0)
    pivot, origin = (303, 303) if bottom else (299, -1)
    sine = math.sqrt(max(0, 1 - factor * factor)) * (1 if bottom else -1)
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, math.ceil(600 * unit), math.ceil(298 * unit))
    texture = cairo.Context(surface)
    texture.scale(unit, unit)
    texture.translate(0, -origin)
    half(texture, value, period, bottom, 1, options, light)
    def project(y):
        relative = y - pivot
        return 300 + (pivot - 300 + relative * factor) / (1 - relative * sine / 4000)
    start, end = project(origin), project(origin + 298)
    for row in range(math.floor(start * unit + phase), math.ceil(end * unit + phase)):
        screen_y = (row - phase + .5) / unit
        relative = (screen_y - pivot) / (factor + (screen_y - 300) * sine / 4000)
        source_y = pivot + relative
        if source_y < origin or source_y > origin + 298:
            continue
        perspective = 1 / (1 - relative * sine / 4000)
        cr.save()
        cr.translate(300 * (1 - perspective), (row - phase) / unit)
        cr.scale(perspective / unit, 1 / unit)
        cr.set_source_surface(surface, 0, -(source_y - origin) * unit + .5)
        cr.rectangle(0, 0, 600 * unit, 1)
        cr.fill()
        cr.restore()
    surface.finish()


def paint(cr, width, height, current, previous, progress, options):
    cr.set_source_rgb(0, 0, 0)
    cr.paint()
    side, gap, x, y, vertical = geometry(width, height, options['scale'])
    for index, value in enumerate(current[:2]):
        cr.save()
        cr.translate(x + (0 if vertical else index * (side + gap)), y + (index * (side + gap) if vertical else 0))
        cr.scale(side / 600, side / 600)
        options = dict(options, unit=side / 600, y_phase=(y + (index * (side + gap) if vertical else 0)) % 1)
        period = current[2] if index == 0 else ''
        changed = previous and (previous[index] != value or (index == 0 and previous[2] != period))
        if not changed or progress >= 1:
            half(cr, value, period, False, 1, options)
            half(cr, value, period, True, 1, options)
        else:
            old_period = previous[2] if index == 0 else ''
            t = min(1, max(0, progress * 2))
            top_light = .1 + .9 * ease(t)
            old_light = (1 if t <= .66 else 1 - .5 * ease((t - .66) / .34, True)) if progress < .5 else .5 - .4 * ease(progress * 2 - 1, True)
            half(cr, value, period, False, 1, options, top_light)
            half(cr, previous[index], old_period, True, 1, options, old_light)
            if progress < .5:
                eased = ease(t)
                half(cr, previous[index], old_period, False, math.cos(eased * math.pi / 2), options, 1 - .6 * eased)
            else:
                eased = ease(progress * 2 - 1, True)
                half(cr, value, period, True, math.sin(eased * math.pi / 2), options, 2 - eased)
        cr.set_source_rgb(0, 0, 0)
        cr.rectangle(0, 297, 600, 6)
        cr.fill()
        cr.restore()
