#!/usr/bin/env python3
"""Render the Fliqlo Ubuntu product film with six non-overlapping 1080p scenes.

Pillow/NumPy + FFmpeg. Deterministic 24 fps timeline. Each scene has its own
typography zone, so transitions never superimpose two headlines. All artwork
and ambient audio are generated here; no third-party footage or music.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import shutil
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'media'
W, H, FPS, SECONDS = 1920, 1080, 24, 20
BOUNDS = (0.0, 3.2, 6.8, 10.6, 13.9, 17.1, 20.0)
FONT_REGULAR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
INK, WHITE, MUTED, ACCENT = '#080b12', '#f2f5ff', '#9ca9c0', '#b9c6fa'
PALETTES = (
    ('OCEAN', '#163d5d', '#def3ff', '#0d2338'),
    ('ROSE', '#643149', '#ffe1ef', '#2c1524'),
    ('IVORY', '#e9ddc9', '#2c384b', '#a7b7c9'),
)


@lru_cache(maxsize=64)
def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR, int(size))


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def rgb(value):
    if isinstance(value, tuple):
        return value
    return tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))


def tint(color, factor):
    return tuple(max(0, min(255, round(c * factor))) for c in rgb(color))


def text(image, value, at, size, color=WHITE, bold=False, anchor='mm', max_width=None):
    draw = ImageDraw.Draw(image)
    face = font(size, bold)
    if max_width is not None and draw.textbbox((0, 0), value, font=face)[2] > max_width:
        raise ValueError(f'Text overflow at {size}px: {value!r}, max {max_width}')
    draw.text(tuple(map(int, at)), value, fill=rgb(color), font=face, anchor=anchor)


def rounded(image, rect, radius, color, outline=None, width=1):
    ImageDraw.Draw(image).rounded_rectangle(tuple(round(v) for v in rect),
        radius=radius, fill=rgb(color),
        outline=rgb(outline) if outline else None, width=width)


@lru_cache(maxsize=10)
def background(kind='charcoal'):
    top, bottom = {
        'charcoal': ('#0d111c', '#07090f'),
        'navy': ('#141a2c', '#080b14'),
        'blue': ('#101d31', '#090d17'),
    }[kind]
    a, b = np.array(rgb(top), dtype=np.float32), np.array(rgb(bottom), dtype=np.float32)
    ys = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    pixels = np.broadcast_to(a[None, None, :] * (1 - ys) + b[None, None, :] * ys,
                              (H, W, 3)).astype(np.uint8).copy()
    xs = np.linspace(-1, 1, W, dtype=np.float32)[None, :, None]
    pixels = np.clip(pixels * (1 - np.abs(xs) * .14), 0, 255).astype(np.uint8)
    return Image.fromarray(pixels, 'RGB')


def brand(image, y=76):
    rounded(image, (110, y - 19, 155, y + 26), 12, '#242b3d')
    ImageDraw.Draw(image).line((111, y + 4, 154, y + 4), fill='#070b16', width=3)
    text(image, '9', (132, y + 4), 21, bold=True)
    text(image, 'FLIQLO / UBUNTU', (177, y + 6), 22, '#b6c3e1',
         bold=True, anchor='lm', max_width=330)


def clock_card(value, width, height, card_color='#18191d',
               digit_color='#e5e5e7', period=''):
    """Clip the full split-flap card, including gradients and digits."""
    cw, ch = int(width), int(height)
    face = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
    mask = Image.new('L', (cw, ch), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, cw - 1, ch - 1),
        radius=round(min(cw, ch) * .09), fill=255)
    draw = ImageDraw.Draw(face)
    draw.rectangle((0, 0, cw, ch / 2), fill=(*tint(card_color, 1.15), 255))
    draw.rectangle((0, ch / 2, cw, ch), fill=(*tint(card_color, .86), 255))
    inset = max(3, round(cw * .014))
    draw.line((inset, round(ch * .5), cw - inset, round(ch * .5)),
              fill=(0, 0, 0, 230), width=max(3, int(ch * .012)))
    size = int(ch * .73)
    while size > 24:
        bounds = draw.textbbox((0, 0), str(value), font=font(size, True))
        if bounds[2] - bounds[0] <= cw * .86 and bounds[3] - bounds[1] <= ch * .76:
            break
        size -= 4
    draw.text((cw / 2, ch / 2), str(value), font=font(size, True),
              anchor='mm', fill=(*rgb(digit_color), 255))
    if period:
        draw.text((cw * .11, ch * .10), period, font=font(int(ch * .09), True),
                  anchor='la', fill=(*rgb(digit_color), 225))
    face.putalpha(mask)
    return face


def clock(image, x, y, card_w, card_h, mode='classic', minute='41', period='AM'):
    colors = {
        'classic': ('#17181b', '#e5e5e8'),
        'ocean': ('#163d5d', '#def3ff'),
        'rose': ('#643149', '#ffe1ef'),
        'ivory': ('#e9ddc9', '#2c384b'),
        'forest': ('#1d4d40', '#d7ffe8'),
    }
    card_color, digit_color = colors[mode]
    gap = round(card_w * .075)
    for i, value in enumerate(('09', minute)):
        face = clock_card(value, card_w, card_h, card_color, digit_color,
                          period if i == 0 else '')
        image.paste(face, (int(x + i * (card_w + gap)), int(y)), face)


def label(image, value, y):
    text(image, value, (W // 2, y), 21, ACCENT, bold=True, max_width=1450)


def intro(t):
    img = background('navy').copy()
    brand(img)
    label(img, 'A NEW MOMENT FOR YOUR DESKTOP', 240)
    text(img, 'TIME,', (W // 2, 413), 133, WHITE, True, max_width=1480)
    text(img, 'BEAUTIFULLY', (W // 2, 555), 119, ACCENT, True, max_width=1600)
    text(img, 'CONSIDERED.', (W // 2, 700), 119, WHITE, True, max_width=1600)
    text(img, 'THE FLIP-CLOCK EXPERIENCE FOR UBUNTU',
         (W // 2, 871), 29, MUTED, max_width=1350)
    return img


def focus(t):
    img = background('charcoal').copy()
    brand(img)
    label(img, '01  /  THE ESSENTIALS', 178)
    text(img, 'THE CLASSIC FLIP-CLOCK FEEL.',
         (W // 2, 268), 71, bold=True, max_width=1580)
    card_w = 430
    x = (W - (2 * card_w + round(card_w * .075))) // 2
    clock(img, x, 352, card_w, 430, minute='40' if t < 5.35 else '41')
    text(img, 'SMOOTH. QUIET. UNMISTAKABLE.',
         (W // 2, 925), 25, MUTED, max_width=1350)
    return img


def color_showcase(t):
    img = background('navy').copy()
    brand(img)
    label(img, '02  /  YOUR PALETTE', 155)
    text(img, 'COLOR THE MOMENT.',
         (W // 2, 245), 78, WHITE, True, max_width=1460)
    for i, (name, card_color, digit_color, wall) in enumerate(PALETTES):
        x = 138 + i * 558
        rounded(img, (x, 354, x + 528, 776), 28, wall, outline='#36445e', width=3)
        clock(img, x + 49, 428, 201, 210, mode=name.lower(), period='')
        text(img, name, (x + 264, 717), 30, WHITE, True, max_width=430)
        rounded(img, (x + 210, 740, x + 318, 745), 2, ACCENT)
    text(img, 'CUSTOM CARDS. CUSTOM DIGITS. NO COMPROMISE.',
         (W // 2, 939), 24, MUTED, max_width=1500)
    return img


@lru_cache(maxsize=2)
def abstract_wallpaper():
    """Original abstract wallpaper illustration, not a user's personal image."""
    sw, sh = 1440, 580
    yy, xx = np.mgrid[0:sh, 0:sw]
    fade = xx / sw
    pixels = np.zeros((sh, sw, 3), dtype=np.float32)
    for channel, (v1, v2) in enumerate(((31, 91), (54, 65), (85, 119))):
        pixels[:, :, channel] = v1 * (1 - fade) + v2 * fade
    for cx, cy, rad, add in (
        (340, 160, 310, (33, 40, 67)),
        (1080, 420, 390, (5, 56, 34)),
        (790, 50, 290, (33, 15, 54)),
    ):
        intensity = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * rad * rad))
        for channel in range(3):
            pixels[:, :, channel] += intensity * add[channel]
    wall = Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8), 'RGB')
    draw = ImageDraw.Draw(wall, 'RGBA')
    draw.ellipse((-300, 380, 1000, 1100), fill=(11, 24, 37, 70))
    draw.ellipse((600, 420, 2050, 1300), fill=(15, 30, 38, 70))
    return wall


def wallpaper(t):
    img = background('charcoal').copy()
    brand(img)
    label(img, '03  /  YOUR BACKGROUND', 144)
    text(img, 'YOUR SPACE. YOUR STYLE.',
         (W // 2, 230), 70, WHITE, True, max_width=1560)
    x, y = 245, 312
    rounded(img, (x - 4, y - 4, x + 1444, y + 584), 30,
            '#202a39', outline='#5c6d90', width=3)
    layer = abstract_wallpaper().convert('RGBA')
    layer.alpha_composite(Image.new('RGBA', (1440, 580), (0, 0, 0, 85)))
    mask = Image.new('L', (1440, 580), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 1439, 579), radius=28, fill=255)
    img.paste(layer.convert('RGB'), (x, y), mask)
    clock(img, 580, 382, 347, 347, mode='classic', period='')
    text(img, 'YOUR IMAGES  /  YOUR COLORS  /  YOUR CONTROL',
         (W // 2, 958), 24, MUTED, max_width=1460)
    return img


def switch(image, x, y, active=True):
    rounded(image, (x, y, x + 92, y + 49), 25,
            '#7899f0' if active else '#3a4152')
    cx = x + (65 if active else 27)
    ImageDraw.Draw(image).ellipse((cx - 18, y + 6, cx + 18, y + 42),
                                 fill=(249, 250, 255))


def settings(t):
    img = background('blue').copy()
    brand(img)
    label(img, '04  /  SETTINGS, SIMPLIFIED', 162)
    # Headline (x: 135..860) and illustration (x: 1005..1779) do not overlap.
    text(img, 'MAKE IT', (135, 393), 88, WHITE, True,
         anchor='la', max_width=700)
    text(img, 'YOURS.', (135, 508), 104, ACCENT, True,
         anchor='la', max_width=700)
    text(img, 'COLORS  /  BACKDROPS  /  ANIMATION',
         (138, 680), 25, MUTED, anchor='la', max_width=730)
    text(img, 'Native GTK preferences.',
         (138, 765), 32, WHITE, anchor='la', max_width=730)
    x, y = 1005, 205
    rounded(img, (x, y, x + 774, y + 663), 29,
            '#e6e9ef', outline='#8393a6', width=3)
    rounded(img, (x + 22, y + 20, x + 752, y + 74), 12, '#d0d6e0')
    text(img, 'Appearance', (x + 385, y + 47), 25,
         '#233247', True, max_width=400)
    rounded(img, (x + 40, y + 118, x + 734, y + 600), 19, '#f8f9fc')
    rows = (
        ('Custom clock colors', 'toggle'),
        ('Card background', 'swatch1'),
        ('Digit color', 'swatch2'),
        ('Background photo', 'swatch3'),
        ('Auto-change photos', 'toggle'),
    )
    for i, (name, kind) in enumerate(rows):
        yy = y + 159 + i * 90
        text(img, name, (x + 74, yy + 14), 25,
             '#263344', anchor='lm', max_width=455)
        if kind == 'toggle':
            switch(img, x + 602, yy - 13)
        else:
            color = {'swatch1': '#173a56',
                     'swatch2': '#d5f1ff', 'swatch3': '#7384b8'}[kind]
            rounded(img, (x + 603, yy - 18, x + 689, yy + 41),
                    13, color, outline='#91a0af', width=2)
    rounded(img, (x + 502, y + 621, x + 717, y + 652), 11, '#d3dae6')
    text(img, 'Reset colors', (x + 609, y + 637), 17,
         '#334157', bold=True, max_width=200)
    return img


def outro(t):
    img = background('navy').copy()
    clock(img, 684, 185, 258, 258, mode='classic', period='')
    text(img, 'FLIQLO UBUNTU',
         (W // 2, 645), 107, WHITE, True, max_width=1660)
    text(img, 'TIME, BEAUTIFULLY CONSIDERED.',
         (W // 2, 754), 39, ACCENT, max_width=1420)
    rounded(img, (512, 847, 1408, 925), 27,
            '#212c42', outline='#536481', width=2)
    text(img, 'github.com/luan-thnh/fliqlo-ubuntu',
         (W // 2, 884), 32, WHITE, max_width=810)
    return img


SCENES = (intro, focus, color_showcase, wallpaper, settings, outro)


def scene_at(t):
    index = min(len(SCENES) - 1,
                max(0, int(np.searchsorted(BOUNDS, t, side='right') - 1)))
    image = SCENES[index](t)
    start, end = BOUNDS[index], BOUNDS[index + 1]
    fade = min(1.0, (t - start) / .36, (end - t) / .32)
    fade = max(0.0, min(1.0, fade))
    # Fade through charcoal at boundaries, never crossfade two text overlays.
    if fade < 1:
        image = Image.blend(Image.new('RGB', (W, H), rgb(INK)),
                            image, smooth(fade))
    return image


def soundtrack(path):
    sr = 24000
    n = int(sr * SECONDS)
    t = np.arange(n, dtype=np.float64) / sr
    data = np.zeros(n, dtype=np.float64)
    for pitch, amplitude in ((110, .016), (164.81, .012),
                             (220, .006), (329.63, .004)):
        data += amplitude * np.sin(2 * np.pi * pitch * t)
    data *= np.maximum(0, np.sin(np.pi * t / SECONDS) ** .65)
    for when in (4.8, 5.35, 7.5, 10.8, 14.2, 17.5):
        start = int(when * sr)
        times = np.arange(int(.095 * sr)) / sr
        data[start:start + len(times)] += (
            .028 * np.sin(2 * np.pi * 158 * times) * np.exp(-times * 51))
    with wave.open(str(path), 'wb') as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(sr)
        out.writeframes((np.clip(data, -1, 1) * 32767).astype(np.int16).tobytes())


def ffmpeg_binary():
    existing = shutil.which('ffmpeg')
    if existing:
        return existing
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def verify_storyboard():
    sheet = Image.new('RGB', (1920, 720), rgb(INK))
    for index in range(len(SCENES)):
        t = (BOUNDS[index] + BOUNDS[index + 1]) / 2
        thumbnail = scene_at(t).resize((640, 360), Image.Resampling.LANCZOS)
        sheet.paste(thumbnail, ((index % 3) * 640, (index // 3) * 360))
    sheet.save(OUT / 'fliqlo-ubuntu-storyboard.jpg',
               quality=87, optimize=True)
    return scene_at((BOUNDS[1] + BOUNDS[2]) / 2)


def render():
    OUT.mkdir(parents=True, exist_ok=True)
    poster = verify_storyboard()
    poster.save(OUT / 'fliqlo-ubuntu-poster.jpg',
                quality=91, optimize=True)
    sound = OUT / 'film-audio.tmp.wav'
    silent = OUT / 'film-video.tmp.mp4'
    soundtrack(sound)
    command = [ffmpeg_binary(), '-hide_banner', '-loglevel', 'error', '-y',
               '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
               '-r', str(FPS), '-i', '-', '-an', '-c:v', 'libx264',
               '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p',
               '-movflags', '+faststart', str(silent)]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    try:
        for frame in range(SECONDS * FPS):
            process.stdin.write(scene_at(frame / FPS).tobytes())
    finally:
        process.stdin.close()
    if process.wait():
        raise RuntimeError('FFmpeg video encoder failed')
    final = OUT / 'fliqlo-ubuntu-teaser.mp4'
    subprocess.run([ffmpeg_binary(), '-hide_banner', '-loglevel', 'error',
        '-y', '-i', str(silent), '-i', str(sound), '-c:v', 'copy',
        '-c:a', 'aac', '-b:a', '112k', '-movflags', '+faststart',
        '-shortest', str(final)], check=True)
    sound.unlink()
    silent.unlink()
    assert final.stat().st_size > 100_000
    print(f'Rendered {W}x{H}, {FPS} fps, {SECONDS}s, {final.stat().st_size:,} bytes')


if __name__ == '__main__':
    render()
