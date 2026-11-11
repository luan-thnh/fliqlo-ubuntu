import sys
import unittest
from datetime import datetime
from tempfile import TemporaryDirectory
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'native'))
from model import clock_parts, geometry, digit_indent, ease, FLIP_SECONDS
from render import paint
import cairo
from gi.repository import GdkPixbuf


class ClockTests(unittest.TestCase):
    def test_formats(self):
        self.assertEqual(clock_parts(datetime(2026, 1, 1, 0), 0), ('12', '00', 'AM'))
        self.assertEqual(clock_parts(datetime(2026, 1, 1, 12), 0), ('12', '00', 'PM'))
        self.assertEqual(clock_parts(datetime(2026, 1, 1, 3, 9), 1), ('3', '09', ''))
        self.assertEqual(clock_parts(datetime(2026, 1, 1, 3, 9), 2), ('03', '09', ''))
        self.assertEqual(clock_parts(datetime(2026, 1, 1, 23, 59), 2), ('23', '59', ''))

    def test_monitor_bounds(self):
        for width, height in [(1920, 1080), (3840, 2160), (1080, 1920), (640, 360)]:
            for scale in (25, 100, 150):
                side, gap, x, y, vertical = geometry(width, height, scale)
                self.assertGreaterEqual(min(x, y), 0)
                self.assertLessEqual(x + (side if vertical else side * 2 + gap), width)
                self.assertLessEqual(y + (side * 2 + gap if vertical else side), height)

    def test_reference_values(self):
        self.assertEqual(geometry(1350, 700, 100), (600, 50, 50, 50, False))
        self.assertEqual(geometry(700, 1350, 100), (600, 50, 50, 50, True))
        self.assertEqual(FLIP_SECONDS, .330)
        self.assertEqual([digit_indent(v) for v in ('1', '11', '01', '21', '12')], [-7.5, 12, 24, 24, 0])
        self.assertAlmostEqual(ease(.5), 1 - ease(.5, True), places=6)

    def test_color_and_local_image_backdrop(self):
        base = dict(scale=100, brightness=100, background=True, font='DejaVu Sans')
        canvas = cairo.ImageSurface(cairo.FORMAT_ARGB32, 640, 360)
        options = dict(base, background_mode=1, background_color='#f03050',
                       background_dim=0)
        paint(cairo.Context(canvas), 640, 360, ('9', '41', 'AM'), None, 1, options)
        canvas.flush()
        pixel = canvas.get_data()
        self.assertGreater(pixel[2], 180)  # RGB red, little-endian ARGB32
        self.assertLess(pixel[1], 100)

        with TemporaryDirectory() as folder:
            source = cairo.ImageSurface(cairo.FORMAT_ARGB32, 40, 40)
            ctx = cairo.Context(source)
            ctx.set_source_rgb(0.05, 0.65, 0.15)
            ctx.paint()
            filename = Path(folder) / 'sample.png'
            source.write_to_png(str(filename))
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(str(filename))
            options = dict(base, background_mode=2, background_pixbuf=pixbuf,
                           background_fit=0, background_opacity=100, background_dim=0)
            canvas = cairo.ImageSurface(cairo.FORMAT_ARGB32, 640, 360)
            paint(cairo.Context(canvas), 640, 360, ('9', '41', 'AM'), None, 1, options)
            canvas.flush()
            pixel = canvas.get_data()
            self.assertGreater(pixel[1], pixel[2])  # Green dominant
            self.assertGreater(pixel[1], pixel[0])

    def test_custom_card_and_digit_colors(self):
        base = dict(scale=100, brightness=100, background=True,
                    font='DejaVu Sans')
        def rendered(options):
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 640, 360)
            paint(cairo.Context(surface), 640, 360,
                  ('9', '41', 'AM'), None, 1, dict(base, **options))
            surface.flush()
            return bytes(surface.get_data())
        classic = rendered({})
        ocean = rendered(dict(flap_colors_enabled=True,
                             flap_background_color='#173a56',
                             flap_digit_color='#d5f1ff'))
        rose = rendered(dict(flap_colors_enabled=True,
                            flap_background_color='#572c43',
                            flap_digit_color='#ffdeee'))
        assert classic != ocean != rose
        # Sample away from the glyphs on the first flap: card really changes.
        index = (80 * 640 + 66) * 4
        assert ocean[index:index + 3] != rose[index:index + 3]
        # An invalid color falls back safely instead of corrupting the image.
        invalid = rendered(dict(flap_colors_enabled=True,
                                flap_background_color='url(file://unsafe)',
                                flap_digit_color='not-a-color'))
        self.assertTrue(any(invalid))

    def test_rounded_card_corners_reveal_the_actual_backdrop(self):
        # Regression for bright custom cards showing rectangular black corners.
        # Each pixel in the extreme corner is outside the rounded card and
        # must match the surrounding backdrop, even during animated flips.
        width, height = 640, 360
        side, gap, x, y, vertical = geometry(width, height, 100)
        self.assertFalse(vertical)
        base = dict(scale=100, brightness=100, background=True,
                    font='DejaVu Sans', flap_colors_enabled=True,
                    flap_background_color='#e8ddc9',
                    flap_digit_color='#283347', background_mode=1,
                    background_color='#b9c6cf', background_dim=0)

        def sample(data, px, py):
            offset = (int(py) * width + int(px)) * 4
            return bytes(data[offset:offset + 4])

        for progress in (1, 0.25, 0.75):
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
            context = cairo.Context(surface)
            paint(context, width, height, ('9', '41', 'AM'),
                  ('8', '40', 'AM') if progress < 1 else None,
                  progress, base)
            surface.flush()
            data = surface.get_data()
            reference = sample(data, 2, 2)  # Entirely outside any clock card
            for card_left in (x, x + side + gap):
                for px in (card_left + 2, card_left + side - 3):
                    for py in (y + 2, y + side - 3):
                        self.assertEqual(sample(data, px, py), reference,
                            f'Exposed square corner at progress={progress}, {px}, {py}')
            # Control pixel: center of the flap is a different color.
            self.assertNotEqual(sample(data, x + side / 2, y + 10), reference)

    def test_cairo_animation(self):
        for progress in (0, .25, .5, .75, 1):
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 640, 360)
            paint(cairo.Context(surface), 640, 360, ('12', '00', 'PM'), ('11', '59', 'AM'), progress,
                  dict(scale=100, brightness=100, background=True, font='DejaVu Sans'))
            self.assertTrue(any(surface.get_data()))


if __name__ == '__main__':
    unittest.main()
