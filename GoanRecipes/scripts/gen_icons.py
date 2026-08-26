#!/usr/bin/env python3
"""Generates the app icon, Android adaptive icon, and splash image as flat PNGs
using only the standard library (no Pillow/cairosvg available in this environment).

Run: python3 scripts/gen_icons.py
Regenerates the files under ../assets/.
"""
import math
import os
import struct
import zlib

SIZE = 1024
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")

PRIMARY = (0xC1, 0x44, 0x0E, 255)       # chilli red
PRIMARY_DARK = (0x8F, 0x32, 0x09, 255)  # deep curry brown
CREAM = (0xFF, 0xF6, 0xE9, 255)         # rice cream
GOLD = (0xD9, 0xA4, 0x41, 255)          # turmeric gold
GREEN = (0x1E, 0x7B, 0x5A, 255)         # curry leaf green


def new_canvas(bg=None):
    if bg is None:
        return [[(0, 0, 0, 0)] * SIZE for _ in range(SIZE)]
    return [[bg] * SIZE for _ in range(SIZE)]


def blend(dst, src):
    """Alpha-composite src over dst."""
    sa = src[3] / 255.0
    if sa <= 0:
        return dst
    if sa >= 1:
        return src
    da = dst[3] / 255.0
    out_a = sa + da * (1 - sa)
    if out_a == 0:
        return (0, 0, 0, 0)
    r = (src[0] * sa + dst[0] * da * (1 - sa)) / out_a
    g = (src[1] * sa + dst[1] * da * (1 - sa)) / out_a
    b = (src[2] * sa + dst[2] * da * (1 - sa)) / out_a
    return (int(r), int(g), int(b), int(out_a * 255))


def fill_circle(canvas, cx, cy, r, color, feather=1.5):
    x0, x1 = max(0, int(cx - r - feather)), min(SIZE - 1, int(cx + r + feather))
    y0, y1 = max(0, int(cy - r - feather)), min(SIZE - 1, int(cy + r + feather))
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            d = math.hypot(x - cx, y - cy) - r
            if d <= 0:
                canvas[y][x] = blend(canvas[y][x], color)
            elif d <= feather:
                a = int(color[3] * (1 - d / feather))
                canvas[y][x] = blend(canvas[y][x], (color[0], color[1], color[2], a))


def fill_ring(canvas, cx, cy, r_outer, r_inner, color, feather=1.5):
    x0, x1 = max(0, int(cx - r_outer - feather)), min(SIZE - 1, int(cx + r_outer + feather))
    y0, y1 = max(0, int(cy - r_outer - feather)), min(SIZE - 1, int(cy + r_outer + feather))
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            d = math.hypot(x - cx, y - cy)
            outer = d - r_outer
            inner = r_inner - d
            if outer <= 0 and inner <= 0:
                canvas[y][x] = blend(canvas[y][x], color)
            elif outer <= feather and inner <= 0:
                a = int(color[3] * (1 - outer / feather))
                canvas[y][x] = blend(canvas[y][x], (color[0], color[1], color[2], max(a, 0)))


def draw_steam_wisp(canvas, base_x, base_y, height, amplitude, color, thickness):
    steps = 200
    for i in range(steps):
        t = i / steps
        y = base_y - t * height
        x = base_x + math.sin(t * math.pi * 2.1) * amplitude * t
        r = thickness * (1 - 0.5 * t)
        a = color[3] * (1 - t) ** 0.6
        fill_circle(canvas, x, y, r, (color[0], color[1], color[2], int(a)), feather=1.0)


def draw_bowl_mark(canvas, transparent_bg, scale=1.0, offset_y=None):
    """Draws the Goan Kitchen mark (curry bowl + steam) centered on canvas.

    The steam rises above the bowl, so the whole mark's visual centroid sits
    above the bowl's own center; offset_y nudges the bowl down by 0.3*R so
    the combined mark (bowl + steam) balances in the middle of the canvas.
    """
    R = 300 * scale
    if offset_y is None:
        offset_y = 0.3 * R
    cx, cy = SIZE / 2, SIZE / 2 + offset_y
    steam_color = (*PRIMARY_DARK[:3], 110)

    # steam wisps rising above the bowl
    draw_steam_wisp(canvas, cx - R * 0.5, cy - R * 0.7, R * 0.9, R * 0.16, steam_color, R * 0.07)
    draw_steam_wisp(canvas, cx, cy - R * 0.78, R * 1.05, R * 0.15, steam_color, R * 0.08)
    draw_steam_wisp(canvas, cx + R * 0.5, cy - R * 0.7, R * 0.9, R * 0.16, steam_color, R * 0.07)

    # bowl rim (deep curry disc)
    fill_circle(canvas, cx, cy, R, PRIMARY_DARK)
    # bowl interior (curry gravy)
    fill_circle(canvas, cx, cy, R * 0.84, PRIMARY)
    # subtle inner shading ring near the rim
    fill_ring(canvas, cx, cy, R * 0.84, R * 0.68, (*PRIMARY_DARK[:3], 90))
    # turmeric garnish
    fill_circle(canvas, cx - R * 0.16, cy - R * 0.02, R * 0.17, GOLD)
    fill_circle(canvas, cx + R * 0.24, cy + R * 0.26, R * 0.11, GOLD)
    # curry leaf accents
    fill_circle(canvas, cx + R * 0.08, cy - R * 0.22, R * 0.075, GREEN)
    fill_circle(canvas, cx - R * 0.32, cy + R * 0.28, R * 0.065, GREEN)


def write_png(path, canvas):
    height = len(canvas)
    width = len(canvas[0])
    raw = bytearray()
    for row in canvas:
        raw.append(0)  # filter type 0 (none)
        for px in row:
            raw.extend(px)

    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    idat = zlib.compress(bytes(raw), 9)
    with open(path, "wb") as f:
        f.write(sig)
        f.write(chunk(b"IHDR", ihdr))
        f.write(chunk(b"IDAT", idat))
        f.write(chunk(b"IEND", b""))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # Primary app icon: solid warm cream background, full mark.
    icon = new_canvas(bg=CREAM)
    draw_bowl_mark(icon, transparent_bg=False, scale=1.0)
    write_png(os.path.join(OUT_DIR, "icon.png"), icon)

    # Android adaptive icon foreground: transparent bg, mark kept inside the
    # ~66% safe zone so it isn't clipped by launcher masks (circle/squircle/etc).
    adaptive = new_canvas(bg=None)
    draw_bowl_mark(adaptive, transparent_bg=True, scale=0.72)
    write_png(os.path.join(OUT_DIR, "adaptive-icon.png"), adaptive)

    # Splash icon: transparent bg, slightly smaller, composited over the
    # app.json splash backgroundColor at runtime.
    splash = new_canvas(bg=None)
    draw_bowl_mark(splash, transparent_bg=True, scale=0.85)
    write_png(os.path.join(OUT_DIR, "splash-icon.png"), splash)

    # Favicon for the web build.
    fav = new_canvas(bg=CREAM)
    draw_bowl_mark(fav, transparent_bg=False, scale=1.0)
    write_png(os.path.join(OUT_DIR, "favicon.png"), fav)

    print("Wrote icon.png, adaptive-icon.png, splash-icon.png, favicon.png to", OUT_DIR)


if __name__ == "__main__":
    main()
