"""Visual check helper; original files stay in the caller-selected scratch directory."""
import ctypes
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'native'))
from assets import windows_font, windows_html

mode, directory = sys.argv[1], Path(sys.argv[2])
if mode == 'extract':
    directory.mkdir(parents=True, exist_ok=True)
    source = Path(sys.argv[3])
    (directory / 'reference.html').write_text(windows_html(source))
    (directory / 'reference.otf').write_bytes(windows_font(source))
elif mode == 'render':
    import cairo
    from render import paint
    from model import clock_parts
    from datetime import datetime
    fontconfig = ctypes.CDLL('libfontconfig.so.1')
    fontconfig.FcConfigGetCurrent.restype = ctypes.c_void_p
    fontconfig.FcConfigAppFontAddFile.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    assert fontconfig.FcConfigAppFontAddFile(fontconfig.FcConfigGetCurrent(), str(directory / 'reference.otf').encode())
    cases = json.loads((directory / 'cases.json').read_text())
    for i, case in enumerate(cases):
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, case['width'], case['height'])
        previous = clock_parts(datetime(2026, 1, 1, case['previous']['hour'], case['previous']['minute']), case['format']) if 'previous' in case else None
        paint(cairo.Context(surface), case['width'], case['height'],
            clock_parts(datetime(2026, 1, 1, case['hour'], case['minute']), case['format']), previous, case.get('progress', 1),
            dict(scale=case['scale'], brightness=case['brightness'], background=case['background'], font='Fliqlo Bold'))
        surface.write_to_png(str(directory / f'native-{i}.png'))
elif mode == 'compare':
    from PIL import Image, ImageChops, ImageStat, ImageFilter
    cases = json.loads((directory / 'cases.json').read_text())
    prefix = sys.argv[3] if len(sys.argv) > 3 else 'native'
    results = []
    root = Path(__file__).resolve().parents[1]
    source_hashes = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [root / 'native/model.py', root / 'native/render.py', root / 'extension/clock.js']}
    html_sha256 = hashlib.sha256((directory / 'reference.html').read_bytes()).hexdigest()
    for i, case in enumerate(cases):
        source = Image.open(directory / f'original-{i}.png').convert('RGB')
        native = Image.open(directory / f'{prefix}-{i}.png').convert('RGB')
        difference = ImageChops.difference(source, native)
        pixels = list(difference.getdata())
        active = sum(max(a) > 2 or max(b) > 2 for a, b in zip(source.getdata(), native.getdata()))
        bad = sum(max(pixel) > 10 for pixel in pixels)
        mae = sum(ImageStat.Stat(difference).mean) / 3
        # Permit one pixel of rasterizer edge variation, while retaining raw errors.
        fringe = ImageChops.lighter(
            ImageChops.lighter(ImageChops.subtract(native, source.filter(ImageFilter.MaxFilter(3))),
                              ImageChops.subtract(source.filter(ImageFilter.MinFilter(3)), native)),
            ImageChops.lighter(ImageChops.subtract(source, native.filter(ImageFilter.MaxFilter(3))),
                              ImageChops.subtract(native.filter(ImageFilter.MinFilter(3)), source)))
        structural = sum(max(pixel) > 10 for pixel in fringe.getdata())
        results.append(dict(case=case, structural_pixels_over_10=structural, fraction_structural_of_active=structural / max(1, active), mean_absolute_error_0_255=mae,
            pixels_over_10=bad, active_pixels=active, fraction_over_10_of_active=bad / max(1, active)))
        assert structural / max(1, active) < .002 and mae < 2, f'Visual mismatch, case {i}: {results[-1]}'
    (directory / ('report.json' if prefix == 'native' else f'report-{prefix}.json')).write_text(json.dumps(dict(
        renderer=prefix, reference_html_sha256=html_sha256, implementation_sha256=source_hashes, scope='Static frames and explicitly paused animation frames of recovered Windows HTML in Linux Chromium vs Cairo/Pango, same local font; not Windows runtime or GNOME session equivalence.',
        threshold=dict(channel_difference=10, edge_tolerance_pixels=1, max_structural_fraction_of_active_pixels=.002, max_mean_absolute_error=2), results=results), indent=2))
    print(f'{len(results)} visual comparisons passed; worst structural mismatch after 1 px edge tolerance: {max(r["fraction_structural_of_active"] for r in results):.4%}')
else:
    raise ValueError('Unknown mode')
