#!/usr/bin/env python3
"""Generate real Cairo/Pango flip-clock color previews, all at a fixed 9:41 AM.

All backgrounds and colors are original project demo combinations. The source
is generated, not a screenshot from GNOME Shell. Reproducible in CI.
"""
from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'native'))

import cairo
from model import clock_parts
from render import paint

OUT = ROOT / 'docs' / 'assets'
WIDTH, HEIGHT = 1600, 900
SAMPLE = clock_parts(datetime(2026, 1, 1, 9, 41), 0)

# Filename, custom card color, numeral color, surrounding background
THEMES = [
    ('theme-classic.png', None, None, None),
    ('theme-ocean.png', '#173a56', '#d5f1ff', '#071a2b'),
    ('theme-rose.png', '#572c43', '#ffdeee', '#241520'),
    ('theme-ivory.png', '#e8ddc9', '#283347', '#b9c6cf'),
    ('theme-forest.png', '#194d40', '#d4ffe8', '#09241d'),
    ('theme-amber.png', '#634222', '#ffdf9e', '#22160e'),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for filename, card, digits, backdrop in THEMES:
        options = {'scale': 100, 'brightness': 100, 'background': True,
                   'font': 'DejaVu Sans'}
        if card is not None:
            options.update(flap_colors_enabled=True,
                           flap_background_color=card,
                           flap_digit_color=digits,
                           background_mode=1,
                           background_color=backdrop,
                           background_dim=0)
        surface = cairo.ImageSurface(cairo.FORMAT_RGB24, WIDTH, HEIGHT)
        cr = cairo.Context(surface)
        cr.set_antialias(cairo.ANTIALIAS_BEST)
        paint(cr, WIDTH, HEIGHT, SAMPLE, None, 1, options)
        surface.flush()
        path = OUT / filename
        surface.write_to_png(str(path))
        print('Created %s (%s x %s)' % (path.relative_to(ROOT), WIDTH, HEIGHT))


if __name__ == '__main__':
    main()
