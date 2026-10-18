#!/usr/bin/env python3
"""Rasterize the game fonts into DS bitmap fonts: Handjet (main text, on its element grid) and
Galmuri 9 (small text, at its native pixel size). Pixelify Sans + hand-drawn digits are the old fallback. Outputs source/gen/font_data.c + include/gen/font_data.h.

Glyph format: rows of u16 bitmasks (bit 15 = leftmost pixel), top-aligned to the line box.
"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TTF = os.path.join(ROOT, 'assets/fonts/PixelifySans.ttf')
HANDJET = os.path.join(ROOT, 'assets/fonts/Handjet.ttf')
# small text: Galmuri 9 (OFL, Lee Minseo), a pixel font drawn for this size; Galmuri 11 fills its few gaps
GALMURI9 = os.path.join(ROOT, 'assets/fonts/Galmuri9.ttf')
GALMURI11 = os.path.join(ROOT, 'assets/fonts/Galmuri11.ttf')

CHARS = ''.join(chr(c) for c in range(32, 127))
CHARS += 'ÀÂÄÆÇÈÉÊËÎÏÔÖŒÙÛÜŸàâäæçèéêëîïôöœùûüÿ«»€’‘“”…–—°·×÷¡¿ñÑáíóúÁÍÓÚãõÃÕåÅøØßłŁńśźżŚŻőűŐŰšŠčČžŽřŘěĚğĞşŞıİăĂțȚșȘ'
# all 24 EU languages: Latin-1, Latin Extended-A, Romanian comma letters, Greek, Cyrillic, typographic quotes
CHARS += ''.join(chr(c) for c in range(0xA0, 0x180)) + 'ȘșȚț'
CHARS += ''.join(chr(c) for c in range(0x384, 0x3CF) if c not in (0x38B, 0x38D, 0x3A2))
CHARS += ''.join(chr(c) for c in range(0x400, 0x460))
CHARS += '„‚‹›•№'
try:  # plus anything the translations use
    import sys as _s
    _s.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import mklang as _ml
    CHARS += _ml.charset()
except Exception:
    pass

# digits: 6 wide, height = cap height (8 for size 13, 7 for size 11)
DIGITS13 = {
 '0': ['.####.', '##..##', '##..##', '##.###', '###.##', '##..##', '##..##', '.####.'],
 '1': ['..##..', '.###..', '..##..', '..##..', '..##..', '..##..', '..##..', '.####.'],
 '2': ['.####.', '##..##', '....##', '...##.', '..##..', '.##...', '##....', '######'],
 '3': ['.####.', '##..##', '....##', '..###.', '....##', '....##', '##..##', '.####.'],
 '4': ['...##.', '..###.', '.#.##.', '#..##.', '######', '...##.', '...##.', '...##.'],
 '5': ['######', '##....', '#####.', '....##', '....##', '....##', '##..##', '.####.'],
 '6': ['..###.', '.##...', '##....', '#####.', '##..##', '##..##', '##..##', '.####.'],
 '7': ['######', '....##', '...##.', '...##.', '..##..', '..##..', '.##...', '.##...'],
 '8': ['.####.', '##..##', '##..##', '.####.', '##..##', '##..##', '##..##', '.####.'],
 '9': ['.####.', '##..##', '##..##', '##..##', '.#####', '....##', '...##.', '.###..'],
}
DIGITS11 = {
 '0': ['.###.', '#...#', '#..##', '#.#.#', '##..#', '#...#', '.###.'],
 '1': ['..#..', '.##..', '..#..', '..#..', '..#..', '..#..', '.###.'],
 '2': ['.###.', '#...#', '....#', '...#.', '..#..', '.#...', '#####'],
 '3': ['.###.', '#...#', '....#', '..##.', '....#', '#...#', '.###.'],
 '4': ['...#.', '..##.', '.#.#.', '#..#.', '#####', '...#.', '...#.'],
 '5': ['#####', '#....', '####.', '....#', '....#', '#...#', '.###.'],
 '6': ['..##.', '.#...', '#....', '####.', '#...#', '#...#', '.###.'],
 '7': ['#####', '....#', '...#.', '..#..', '..#..', '.#...', '.#...'],
 '8': ['.###.', '#...#', '#...#', '.###.', '#...#', '#...#', '.###.'],
 '9': ['.###.', '#...#', '#...#', '.####', '....#', '...#.', '.##..'],
}

# Icons (real code points + private-use aliases)
ICONS = {
 '▶': ['#.....', '##....', '###...', '####..', '###...', '##....', '#.....'],
 '◀': ['.....#', '....##', '...###', '..####', '...###', '....##', '.....#'],
 '▼': ['#######', '.#####.', '..###..', '...#...'],
 '▲': ['...#...', '..###..', '.#####.', '#######'],
 '↑': ['..#..', '.###.', '#####', '..#..', '..#..', '..#..'],
 '↓': ['..#..', '..#..', '..#..', '#####', '.###.', '..#..'],
 '★': ['....#....', '...###...', '#########', '.#######.', '..#####..', '.##...##.', '##.....##'],
 '♥': ['.##.##.', '#######', '#######', '.#####.', '..###..', '...#...'],
 '♪': ['..###', '..#.#', '..#..', '..#..', '###..', '###..'],
 '♂': ['...###', '....##', '.###.#', '#...#.', '#...#.', '#...#.', '.###..'],
 '♀': ['.###.', '#...#', '#...#', '.###.', '..#..', '#####', '..#..'],
 '✓': ['......#', '.....##', '#...##.', '##.##..', '.###...', '..#....'],
 '×': ['#...#', '.#.#.', '..#..', '.#.#.', '#...#'],
 '': ['#.....', '##....', '###...', '####..', '###...', '##....', '#.....'],          # ▶ cursor
 '': ['#######', '.#####.', '..###..', '...#...'],                                     # ▼ next page
 '': ['..#..', '.###.', '#####', '..#..', '..#..'],                                     # ↑
 '': ['..#..', '..#..', '#####', '.###.', '..#..'],                                     # ↓
 '': ['....#....', '...###...', '#########', '.#######.', '..#####..', '.##...##.', '##.....##'],  # ★
 '': ['.##.##.', '#######', '#######', '.#####.', '..###..', '...#...'],                 # ♥
}


def build(size, digits, line_h, top_pad):
    font = ImageFont.truetype(TTF, size)
    asc, desc = font.getmetrics()
    glyphs = []
    cap_top = font.getbbox('H')[1]
    for ch in dict.fromkeys(CHARS + ''.join(ICONS)):
        if ch in digits or ch in ICONS:
            rows = digits[ch] if ch in digits else ICONS[ch]
            w = len(rows[0])
            bm = [[c == '#' for c in r] for r in rows]
            if ch in digits:
                y0 = cap_top + top_pad
            else:
                y0 = cap_top + top_pad + (8 - len(rows)) // 2
            adv = w + 1
            glyphs.append((ch, w, adv, y0, bm))
            continue
        bbox = font.getbbox(ch)
        adv = int(round(font.getlength(ch)))
        if ch == ' ':
            glyphs.append((ch, 0, max(3, adv), 0, []))
            continue
        img = Image.new('1', (32, 32), 0)
        d = ImageDraw.Draw(img)
        d.fontmode = '1'
        d.text((4, 4 + top_pad), ch, font=font, fill=1)
        bb = img.getbbox()
        if not bb:
            glyphs.append((ch, 0, adv, 0, []))
            continue
        x0, y0, x1, y1 = bb
        w = x1 - x0
        bm = [[img.getpixel((x, y)) == 1 for x in range(x0, x1)] for y in range(y0, y1)]
        lsb = x0 - 4
        adv = max(adv, w + max(0, lsb) + 1)
        glyphs.append((ch, w, adv, y0 - 4, bm, lsb))
    return glyphs, line_h


def build_handjet(px, threshold, line_h, element_grid=False):
    """Rasterize Handjet (OFL). element_grid: 17 px/em so each Handjet element is exactly one pixel."""
    import numpy as np
    K = 8
    font = ImageFont.truetype(HANDJET, px * K)
    asc = font.getbbox('É')[1]
    glyphs = []
    for ch in dict.fromkeys(CHARS + ''.join(ICONS)):
        if ch in ICONS:
            rows = ICONS[ch]
            bm = [[c == '#' for c in r] for r in rows]
            cap_top = (font.getbbox('H')[1] - asc) // K + 1
            y0 = cap_top + max(0, (11 - len(rows)) // 2) if element_grid else cap_top + max(0, (8 - len(rows)) // 2)
            glyphs.append((ch, len(rows[0]), len(rows[0]) + 1, y0, bm))
            continue
        adv = int(font.getlength(ch) / K + 0.5)
        if ch == ' ':
            glyphs.append((ch, 0, max(3, adv), 0, []))
            continue
        W = px * K * 3
        im = Image.new('L', (W, px * K * 2), 0)
        ImageDraw.Draw(im).text((K * 4, -asc + K * 2), ch, font=font, fill=255)
        a = np.array(im).astype(float)
        h2, w2 = a.shape[0] // K, a.shape[1] // K
        if element_grid:
            m = a[K // 2::K, K // 2::K][:h2, :w2] > 100
        else:
            m = a[:h2 * K, :w2 * K].reshape(h2, K, w2, K).mean(axis=(1, 3)) > threshold
        ys, xs = np.where(m)
        if len(xs) == 0:
            glyphs.append((ch, 0, adv, 0, []))
            continue
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        bm = [[bool(m[y, x]) for x in range(x0, x1)] for y in range(y0, y1)]
        lsb = x0 - 4
        adv = max(adv, (x1 - x0) + max(0, lsb) + 1)
        glyphs.append((ch, x1 - x0, adv, y0 - 2, bm, max(0, lsb)))
    return glyphs, line_h


def build_pixel(path, px, line_h, top_pad=2, fallback=None):
    """Rasterize a pixel font at its native size (1 font pixel = 1 screen pixel, no smoothing).
    fallback = (path, px) for code points the main font lacks; glyphs share the same baseline."""
    from fontTools.ttLib import TTFont
    fonts = [(ImageFont.truetype(path, px), TTFont(path).getBestCmap())]
    if fallback:
        fonts.append((ImageFont.truetype(fallback[0], fallback[1]), TTFont(fallback[0]).getBestCmap()))
    cap_h = -fonts[0][0].getbbox('H', anchor='ls')[1]
    base = top_pad + cap_h
    glyphs = []
    for ch in dict.fromkeys(CHARS + ''.join(ICONS)):
        if ch in ICONS:
            rows = ICONS[ch]
            bm = [[c == '#' for c in r] for r in rows]
            glyphs.append((ch, len(rows[0]), len(rows[0]) + 1, max(0, base - cap_h // 2 - len(rows) // 2), bm))
            continue
        if ch == 'ᵉ':   # superscript e (1ᵉʳ, XVIIIᵉ): not in Galmuri
            rows = ['.#.', '###', '#..', '.##']
            glyphs.append((ch, 3, 4, base - cap_h, [[c == '#' for c in r] for r in rows]))
            continue
        font = next((f for f, cm in fonts if ord(ch) in cm), None)
        if font is None:
            continue   # Handjet-only symbols fall back at run time to nothing; none are used in small text
        adv = int(round(font.getlength(ch)))
        if ch == ' ':
            glyphs.append((ch, 0, max(3, adv), 0, []))
            continue
        img = Image.new('1', (48, 40), 0)
        d = ImageDraw.Draw(img)
        d.fontmode = '1'
        d.text((8, 8 + base), ch, font=font, fill=1, anchor='ls')
        bb = img.getbbox()
        if not bb:
            glyphs.append((ch, 0, adv, 0, []))
            continue
        x0, y0, x1, y1 = bb
        bm = [[img.getpixel((x, y)) == 1 for x in range(x0, x1)] for y in range(y0, y1)]
        lsb = x0 - 8
        adv = max(adv, (x1 - x0) + max(0, lsb) + 1)
        glyphs.append((ch, x1 - x0, adv, max(0, y0 - 8), bm, max(0, lsb)))
    return glyphs, line_h


def emit(name, glyphs, line_h, out_c, out_h):
    glyphs = sorted(glyphs, key=lambda g: ord(g[0]))
    data = []
    recs = []
    for g in glyphs:
        ch, w, adv, y0, bm = g[:5]
        lsb = g[5] if len(g) > 5 else 0
        off = len(data)
        for row in bm:
            v = 0
            for i, b in enumerate(row):
                if b:
                    v |= 1 << (15 - i)
            data.append(v)
        recs.append((ord(ch), w, adv, max(0, y0), len(bm), off, max(0, lsb)))
    out_c.append(f'static const u16 {name}_bits[] = {{' + ','.join(str(v) for v in data) + '};')
    out_c.append(f'static const FontGlyph {name}_glyphs[] = {{')
    for r in recs:
        out_c.append('  {%d,%d,%d,%d,%d,%d,%d},' % (r[0], r[1], r[2], r[3], r[4], r[6], r[5]))
    out_c.append('};')
    out_c.append(f'const Font {name} = {{ {name}_glyphs, {name}_bits, {len(recs)}, {line_h} }};')
    out_h.append(f'extern const Font {name};')


def main():
    out_c = ['// Generated by tools/mkfont.py from Handjet and Galmuri (SIL OFL 1.1). Do not edit.',
             '#include "font.h"']
    out_h = ['#pragma once', '#include "font.h"']
    g, lh = build_handjet(17, 0, 18, element_grid=True)
    emit('font_main', g, lh, out_c, out_h)
    g, lh = build_pixel(GALMURI9, 10, 13, fallback=(GALMURI11, 12))
    emit('font_small', g, lh, out_c, out_h)
    os.makedirs(os.path.join(ROOT, 'source/gen'), exist_ok=True)
    os.makedirs(os.path.join(ROOT, 'include/gen'), exist_ok=True)
    open(os.path.join(ROOT, 'source/gen/font_data.c'), 'w').write('\n'.join(out_c) + '\n')
    open(os.path.join(ROOT, 'include/gen/font_data.h'), 'w').write('\n'.join(out_h) + '\n')


if __name__ == '__main__':
    main()
