"""Clock math derived from the supplied Windows renderer; format IDs stay stable."""
FLIP_SECONDS = .330


def clock_parts(date, time_format):
    hour = date.hour
    hours = str(hour % 12 or 12) if time_format == 0 else str(hour)
    if time_format == 2:
        hours = hours.zfill(2)
    return hours, f'{date.minute:02}', ('AM' if hour < 12 else 'PM') if time_format == 0 else ''


def geometry(width, height, scale):
    vertical = width < height
    unit = min(width / (700 if vertical else 1350), height / (1350 if vertical else 700)) * max(50, min(100, scale)) / 100
    side, gap = 600 * unit, 50 * unit
    return side, gap, (width - (side if vertical else side * 2 + gap)) / 2, (height - (side * 2 + gap if vertical else side)) / 2, vertical


def digit_indent(value):
    if value == '1':
        return -7.5
    if value == '11':
        return 12
    return 24 if value.endswith('1') else 0


def ease(value, outgoing=False):
    # CSS ease-in (.42,0,1,1), ease-out (0,0,.58,1).
    x1, x2 = (0, .58) if outgoing else (.42, 1)
    low, high = 0., 1.
    for _ in range(24):
        t = (low + high) / 2
        x = 3 * (1 - t) ** 2 * t * x1 + 3 * (1 - t) * t ** 2 * x2 + t ** 3
        if x < value:
            low = t
        else:
            high = t
    t = (low + high) / 2
    return 3 * (1 - t) * t * t + t ** 3
