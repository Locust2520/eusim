#!/usr/bin/env python3
"""Procedural Euromon sprites: 64x64 front/back (8bpp <=31 colours) + 32x32 icons (shared palette).

Every creature is built from a body plan (shape), a palette (colour word + type accent), an evolution
stage (size/extra features), a face and a species-specific prop. Pixel art is drawn directly at 64x64
with aliased shapes, then shaded (light from the top-left) and outlined with a darker tone.
"""
import json
import math
import os
import random
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

COLORS = {
    'green': (88, 184, 80), 'black': (72, 72, 88), 'orange': (240, 136, 48), 'grey': (150, 156, 170),
    'yellow': (248, 208, 56), 'cyan': (72, 200, 224), 'brown': (168, 112, 64), 'red': (224, 72, 64),
    'white': (232, 232, 240), 'tan': (216, 168, 104), 'blue': (72, 120, 224), 'pink': (240, 128, 176),
    'beige': (224, 196, 150), 'gold': (240, 192, 48), 'olive': (140, 150, 60), 'teal': (64, 168, 160),
    'purple': (150, 96, 200), 'navy': (48, 64, 140), 'lavender': (184, 168, 232), 'bronze': (184, 128, 72),
    'silver': (196, 204, 216), 'marble': (236, 228, 214),
}
TYPE_ACCENT = {
    'TECHNO': (90, 100, 130), 'FEDERAL': (255, 204, 0), 'SOUVERAIN': (176, 48, 48), 'LIBERAL': (240, 192, 32),
    'SOCIAL': (232, 72, 88), 'VERT': (60, 160, 60), 'INDUSTRIE': (110, 90, 70), 'ENERGIE': (255, 220, 40),
    'JURIDIQUE': (112, 72, 176), 'MONETAIRE': (232, 184, 48), 'AGRICOLE': (150, 190, 60), 'NUMERIQUE': (64, 200, 240),
    'DIPLO': (90, 170, 170), 'LOBBY': (210, 170, 40), 'POPULISTE': (230, 90, 160), 'FANTOME': (130, 100, 190),
}
EU_BLUE = (0, 51, 153)
GOLD = (255, 204, 0)
W, H = 64, 64


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def mix(a, b, t):
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


class FillDraw:
    """ImageDraw proxy that fills shapes with 255 unless told otherwise (mask drawing)."""

    def __init__(self, d):
        self.d = d

    def __getattr__(self, name):
        fn = getattr(self.d, name)

        def call(*a, **k):
            if name in ('ellipse', 'rectangle', 'rounded_rectangle', 'polygon', 'pieslice', 'chord') and 'fill' not in k:
                k['fill'] = 255
            if name in ('line', 'arc') and 'fill' not in k:
                k['fill'] = 255
            return fn(*a, **k)
        return call


class Canvas:
    """Layered drawing: each part is a mask with a base colour; shading applied per part."""

    def __init__(self):
        self.img = Image.new('RGBA', (W, H), (0, 0, 0, 0))

    def part(self, draw_fn, color, shading=True, outline=True, light=(-1, -1)):
        m = Image.new('L', (W, H), 0)
        draw_fn(FillDraw(ImageDraw.Draw(m)))
        mask = np.array(m) > 127
        if not mask.any():
            return
        out = np.array(self.img)
        ys, xs = np.where(mask)
        # distance-ish shading: compare with mask shifted towards the light
        hi = mask & ~np.roll(np.roll(mask, 2, 0), 2, 1)        # top-left rim
        lo = mask & ~np.roll(np.roll(mask, -3, 0), -2, 1)      # bottom-right rim
        base = np.array(color + (255,), dtype=np.uint8)
        out[mask] = base
        if shading:
            out[lo] = np.array(shade(color, 0.72) + (255,), dtype=np.uint8)
            out[hi & ~lo] = np.array(mix(color, (255, 255, 255), 0.35) + (255,), dtype=np.uint8)
        if outline:
            ol = np.zeros_like(mask)
            ol[1:, :] |= mask[:-1, :]
            ol[:-1, :] |= mask[1:, :]
            ol[:, 1:] |= mask[:, :-1]
            ol[:, :-1] |= mask[:, 1:]
            ol &= ~mask
            # don't draw outline over already-opaque pixels of OTHER parts drawn before? keep outlines crisp:
            out[ol] = np.array(shade(color, 0.38) + (255,), dtype=np.uint8)
        self.img = Image.fromarray(out, 'RGBA')

    def flat(self, draw_fn, color):
        d = ImageDraw.Draw(self.img)
        draw_fn(d, color + (255,))


# ---------------------------------------------------------------- face
def eyes(c, cx, cy, sep, size=4, mood='happy', pupil=(24, 24, 40)):
    for sx in (-1, 1):
        ex = cx + sx * sep
        c.part(lambda d, ex=ex: d.ellipse([ex - size, cy - size - 1, ex + size, cy + size]), (250, 250, 255),
               shading=False)
        ps = max(2, size - 1)
        c.flat(lambda d, col, ex=ex: d.ellipse([ex - ps + 1 + sx, cy - ps + 1, ex + ps - 1 + sx, cy + ps - 1], fill=col),
               pupil)
        c.flat(lambda d, col, ex=ex: d.rectangle([ex - 1 + sx, cy - 2, ex + sx, cy - 1], fill=col), (255, 255, 255))
        if mood == 'angry':
            c.flat(lambda d, col, ex=ex: d.line([(ex - size, cy - size - 3 - (sx < 0) * 0), (ex + size, cy - size - 1)]
                                              if sx < 0 else [(ex - size, cy - size - 1), (ex + size, cy - size - 3)],
                                              fill=col, width=2), (30, 20, 30))


def mouth(c, cx, cy, style='smile', w=5):
    col = (60, 24, 32)
    if style == 'smile':
        c.flat(lambda d, k: d.arc([cx - w, cy - w // 2 - 2, cx + w, cy + w // 2], 20, 160, fill=k, width=1), col)
    elif style == 'open':
        c.flat(lambda d, k: d.ellipse([cx - w // 2 - 1, cy - 2, cx + w // 2 + 1, cy + 3], fill=k), col)
        c.flat(lambda d, k: d.rectangle([cx - 1, cy + 1, cx + 1, cy + 2], fill=k), (230, 90, 100))
    elif style == 'grin':
        c.flat(lambda d, k: d.rectangle([cx - w, cy - 1, cx + w, cy + 2], fill=k), col)
        c.flat(lambda d, k: d.line([(cx - w + 1, cy), (cx + w - 1, cy)], fill=k), (250, 250, 250))
    elif style == 'flat':
        c.flat(lambda d, k: d.line([(cx - w + 1, cy), (cx + w - 1, cy)], fill=k, width=1), col)
    elif style == 'fang':
        c.flat(lambda d, k: d.arc([cx - w, cy - w // 2 - 2, cx + w, cy + w // 2], 20, 160, fill=k, width=1), col)
        c.flat(lambda d, k: d.polygon([(cx - 3, cy + 1), (cx - 1, cy + 1), (cx - 2, cy + 4)], fill=k), (255, 255, 255))


# ---------------------------------------------------------------- body plans
def plan_blob(c, col, s, rnd, sp):
    r = int(20 * s)
    cx, cy = 32, 62 - r
    c.part(lambda d: d.ellipse([cx - r, cy - r + 2, cx + r, cy + r]), col)
    # little feet
    for fx in (-r // 2, r // 2):
        c.part(lambda d, fx=fx: d.ellipse([cx + fx - 5, cy + r - 5, cx + fx + 5, cy + r + 1]), shade(col, 0.85))
    return {'face': (cx, cy - r // 4), 'sep': max(5, r // 3), 'top': cy - r + 2, 'cx': cx, 'r': r}


def plan_biped(c, col, s, rnd, sp):
    bh = int(22 * s)
    bw = int(16 * s)
    cx, by = 32, 60
    # legs
    for lx in (-bw // 2, bw // 2 - 4):
        c.part(lambda d, lx=lx: d.rectangle([cx + lx, by - 8, cx + lx + 5, by]), shade(col, 0.8))
    c.part(lambda d: d.ellipse([cx - bw, by - bh - 6, cx + bw, by - 4]), col)
    hr = int(14 * s)
    hy = by - bh - hr + 4
    # arms
    for ax in (-1, 1):
        c.part(lambda d, ax=ax: d.ellipse([cx + ax * (bw + 2) - 4, by - bh + 2, cx + ax * (bw + 2) + 4, by - bh + 14]),
               shade(col, 0.9))
    c.part(lambda d: d.ellipse([cx - hr, hy - hr, cx + hr, hy + hr]), col)
    return {'face': (cx, hy + 1), 'sep': max(4, hr // 2 - 1), 'top': hy - hr, 'cx': cx, 'r': hr}


def plan_humanoid(c, col, s, rnd, sp, suit=(40, 48, 80)):
    cx, by = 32, 62
    h = int(30 * s)
    bw = int(12 * s)
    for lx in (-bw // 2 - 1, bw // 2 - 3):
        c.part(lambda d, lx=lx: d.rectangle([cx + lx, by - 10, cx + lx + 4, by]), shade(suit, 0.7))
    c.part(lambda d: d.rounded_rectangle([cx - bw, by - h, cx + bw, by - 8], radius=5), suit)
    # shirt + tie
    c.part(lambda d: d.polygon([(cx - 3, by - h), (cx + 3, by - h), (cx, by - h + 8)]), (240, 240, 240), outline=False)
    c.part(lambda d: d.polygon([(cx - 1, by - h + 3), (cx + 1, by - h + 3), (cx + 2, by - h + 12), (cx, by - h + 14),
                                (cx - 2, by - h + 12)]), col, outline=False)
    hr = int(12 * s) + 2
    hy = by - h - hr + 3
    c.part(lambda d: d.ellipse([cx - hr, hy - hr, cx + hr, hy + hr]), col)
    for ax in (-1, 1):
        c.part(lambda d, ax=ax: d.rounded_rectangle([cx + ax * (bw + 1) - 3, by - h + 2, cx + ax * (bw + 1) + 3, by - h + 18],
                                                    radius=2), suit)
    return {'face': (cx, hy + 1), 'sep': max(4, hr // 2), 'top': hy - hr, 'cx': cx, 'r': hr}


def plan_quadruped(c, col, s, rnd, sp):
    bw, bh = int(24 * s), int(13 * s)
    cx, by = 30, 58
    for lx in (-bw + 3, -bw + 10, bw - 12, bw - 5):
        c.part(lambda d, lx=lx: d.rectangle([cx + lx, by - 6, cx + lx + 4, by + 2]), shade(col, 0.78))
    # tail
    c.part(lambda d: d.polygon([(cx - bw + 2, by - bh), (cx - bw - 8, by - bh - 10), (cx - bw - 4, by - bh - 2)]),
           shade(col, 0.9))
    c.part(lambda d: d.ellipse([cx - bw, by - 2 * bh - 2, cx + bw, by]), col)
    hr = int(12 * s) + 1
    hx, hy = cx + bw - 4, by - 2 * bh - hr // 2 + 2
    # ears
    for ex in (-hr + 3, hr - 6):
        c.part(lambda d, ex=ex: d.polygon([(hx + ex, hy - hr + 4), (hx + ex + 3, hy - hr - 5), (hx + ex + 6, hy - hr + 4)]),
               shade(col, 0.9))
    c.part(lambda d: d.ellipse([hx - hr, hy - hr, hx + hr, hy + hr]), col)
    return {'face': (hx, hy + 1), 'sep': max(4, hr // 2 - 1), 'top': hy - hr, 'cx': hx, 'r': hr}


def plan_flyer(c, col, s, rnd, sp):
    r = int(15 * s)
    cx, cy = 32, 40
    wing = mix(col, (255, 255, 255), 0.3)
    for sx in (-1, 1):
        c.part(lambda d, sx=sx: d.polygon([(cx + sx * (r - 4), cy - 2), (cx + sx * (r + 18 * s), cy - 16 * s),
                                           (cx + sx * (r + 14 * s), cy + 2), (cx + sx * (r + 6), cy + 8)]), wing)
    c.part(lambda d: d.ellipse([cx - r, cy - r, cx + r, cy + r]), col)
    # beak/tail
    c.part(lambda d: d.polygon([(cx - 4, cy + r - 2), (cx + 4, cy + r - 2), (cx, cy + r + 6)]), shade(col, 0.8))
    return {'face': (cx, cy - 2), 'sep': max(4, r // 2 - 1), 'top': cy - r, 'cx': cx, 'r': r}


def plan_object(c, col, s, rnd, sp):
    w, h = int(22 * s), int(26 * s)
    cx, by = 32, 60
    c.part(lambda d: d.rounded_rectangle([cx - w, by - h * 2 + 8, cx + w, by], radius=max(3, int(6 * s))), col)
    # stubby feet
    for fx in (-w + 4, w - 9):
        c.part(lambda d, fx=fx: d.rectangle([cx + fx, by - 2, cx + fx + 5, by + 2]), shade(col, 0.6))
    top = by - h * 2 + 8
    return {'face': (cx, top + int(h * 0.7)), 'sep': max(5, w // 2 - 1), 'top': top, 'cx': cx, 'r': w}


def plan_serpent(c, col, s, rnd, sp):
    pts = []
    for i in range(14):
        t = i / 13
        x = 12 + 40 * t
        y = 54 - 26 * t + math.sin(t * math.pi * 2.2) * 8 * s
        pts.append((x, y))
    thick = int(7 * s) + 2
    for i, (x, y) in enumerate(pts):
        r = thick - 2 + int(2 * math.sin(i / 13 * math.pi))
        c.part(lambda d, x=x, y=y, r=r: d.ellipse([x - r, y - r, x + r, y + r]), col if i % 3 else shade(col, 0.92),
               outline=(i == 0))
    hx, hy = pts[-1]
    hr = thick + 3
    c.part(lambda d: d.ellipse([hx - hr, hy - hr, hx + hr, hy + hr]), col)
    return {'face': (int(hx), int(hy)), 'sep': max(3, hr // 2), 'top': int(hy - hr), 'cx': int(hx), 'r': hr}


def plan_insect(c, col, s, rnd, sp):
    cx = 32
    segs = [(cx, 52, int(12 * s)), (cx, 40, int(10 * s)), (cx, 28, int(11 * s))]
    for i, (x, y, r) in enumerate(segs[:2]):
        for sx in (-1, 1):
            c.part(lambda d, sx=sx, y=y, r=r: d.line([(x + sx * r, y), (x + sx * (r + 8), y + 6)], fill=255, width=2),
                   shade(col, 0.5), shading=False, outline=False)
    for x, y, r in segs:
        c.part(lambda d, x=x, y=y, r=r: d.ellipse([x - r, y - r, x + r, y + r]), col)
    x, y, r = segs[2]
    for sx in (-1, 1):
        c.part(lambda d, sx=sx: d.line([(x + sx * 4, y - r + 2), (x + sx * 10, y - r - 8)], fill=255, width=1),
               shade(col, 0.4), shading=False, outline=False)
    return {'face': (x, y + 1), 'sep': max(4, r // 2), 'top': y - r - 8, 'cx': x, 'r': r}


PLANS = {'blob': plan_blob, 'biped': plan_biped, 'humanoid': plan_humanoid, 'quadruped': plan_quadruped,
         'flyer': plan_flyer, 'object': plan_object, 'serpent': plan_serpent, 'insect': plan_insect,
         'fish': plan_flyer, 'tree': plan_biped}


# ---------------------------------------------------------------- props (species specific decorations)
def star(d, cx, cy, r, fill):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.45
        a = -math.pi / 2 + i * math.pi / 5
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=fill)


def euro_sign(c, cx, cy, col=(120, 80, 0)):
    c.flat(lambda d, k: d.arc([cx - 5, cy - 6, cx + 5, cy + 6], 45, 315, fill=k, width=2), col)
    c.flat(lambda d, k: d.line([(cx - 7, cy - 1), (cx + 1, cy - 1)], fill=k), col)
    c.flat(lambda d, k: d.line([(cx - 7, cy + 2), (cx + 1, cy + 2)], fill=k), col)


def eu_ring(c, cx, cy, r, n=12):
    for i in range(n):
        a = i * 2 * math.pi / n
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        c.flat(lambda d, k, x=x, y=y: star(d, x, y, 2.6, k), GOLD)


def prop(c, sp, info, stage, col):
    sid = sp['id']
    fx, fy = info['face']
    top, cx, r = info['top'], info['cx'], info['r']
    acc = TYPE_ACCENT[sp['types'][0]]
    if sid in ('tampono', 'paraphor', 'ratifix'):
        c.part(lambda d: d.rounded_rectangle([cx - 5, top - 14, cx + 5, top + 2], radius=4), (150, 96, 50))
        c.part(lambda d: d.ellipse([cx - 7, top - 20, cx + 7, top - 8]), (176, 112, 60))
        c.part(lambda d: d.rectangle([cx - r + 2, info['face'][1] + 10, cx + r - 2, info['face'][1] + 14]), (200, 40, 40))
        if stage >= 2:
            eu_ring(c, cx, top - 14, 9, 6 if stage == 2 else 12)
    elif sid in ('cookiz', 'consentor'):
        rnd = random.Random(3)
        for _ in range(7):
            x, y = cx + rnd.randint(-r + 4, r - 4), fy + rnd.randint(-r + 2, r - 2)
            if abs(y - fy) > 5:
                c.flat(lambda d, k, x=x, y=y: d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=k), (90, 50, 30))
        if sid == 'consentor':
            c.part(lambda d: d.rectangle([cx - 14, top - 10, cx + 14, top - 2]), (250, 250, 250))
            c.flat(lambda d, k: d.text((cx - 10, top - 11), "OK", fill=k), (40, 120, 40))
    elif sid in ('eurolo', 'eurozone', 'mica', 'cryptou'):
        euro_sign(c, cx, fy + 9 if sid != 'cryptou' else fy + 9)
        if sid == 'eurozone':
            eu_ring(c, cx, fy, r + 4)
    elif sid == 'usbece':
        c.part(lambda d: d.rounded_rectangle([12, 48, 22, 58], radius=2), (200, 200, 210))
        c.flat(lambda d, k: d.rectangle([15, 51, 19, 55], fill=k), (40, 40, 50))
    elif sid in ('courbana',):
        pass
    elif sid in ('schengeon', 'schumark', 'spitzen', 'neutralis', 'cecagon', 'ratifix', 'romulus', 'lisbonia',
                 'maastrichtor', 'nobelix', 'constitutio'):
        eu_ring(c, cx, top + 2, 10 + stage * 2, 12)
    elif sid in ('lobbyrax', 'lobbyron', 'lobbyzilla', 'valisette', 'diesgate'):
        bx = 46
        c.part(lambda d: d.rounded_rectangle([bx, 42, bx + 14, 54], radius=2), (90, 56, 30))
        c.flat(lambda d, k: d.rectangle([bx + 5, 39, bx + 9, 42], fill=k), (40, 30, 20))
        c.flat(lambda d, k: d.rectangle([bx + 6, 47, bx + 8, 49], fill=k), GOLD)
        if stage >= 2:
            c.part(lambda d: d.polygon([(cx - 8, top + 1), (cx + 8, top + 1), (cx, top - 9)]), (30, 30, 40))
    elif sid in ('sacabillet',):
        c.part(lambda d: d.polygon([(cx - 6, top + 2), (cx + 6, top + 2), (cx + 3, top - 6), (cx - 3, top - 6)]), (140, 110, 60))
        euro_sign(c, cx, fy + 10, (30, 110, 40))
    elif sid in ('eolion', 'offshorion'):
        for i in range(3):
            a = i * 2 * math.pi / 3 - math.pi / 2
            c.part(lambda d, a=a: d.line([(cx, top - 6), (cx + 13 * math.cos(a), top - 6 + 13 * math.sin(a))], fill=255,
                                         width=3), (250, 250, 250), shading=False)
        c.part(lambda d: d.ellipse([cx - 3, top - 9, cx + 3, top - 3]), (200, 200, 210))
    elif sid in ('solario',):
        for x in range(cx - r + 4, cx + r - 4, 6):
            c.flat(lambda d, k, x=x: d.line([(x, top + 4), (x, top + 20)], fill=k), (200, 230, 255))
    elif sid in ('atomino', 'euratome', 'fissionix', 'atomiom'):
        for k in range(2 + min(stage, 2)):
            a = k * math.pi / (2 + stage)
            c.flat(lambda d, col_, a=a: d.ellipse([cx - r - 6, fy - 5, cx + r + 6, fy + 5], outline=col_), (255, 255, 255))
        c.flat(lambda d, k: d.ellipse([cx + r + 2, fy - 2, cx + r + 6, fy + 2], fill=k), (60, 220, 255))
    elif sid in ('charbonnet', 'hautfourno', 'cecagon'):
        c.part(lambda d: d.rectangle([cx + 4, top - 10, cx + 9, top + 2]), (90, 80, 80))
        c.flat(lambda d, k: d.ellipse([cx + 2, top - 18, cx + 12, top - 10], fill=k), (180, 180, 190))
    elif sid in ('verdeal', 'fit55', 'neutralis', 'agrikolo', 'pactor', 'megapac'):
        c.part(lambda d: d.polygon([(cx, top - 10), (cx - 7, top + 1), (cx, top - 2)]), (70, 180, 60))
        c.part(lambda d: d.polygon([(cx, top - 10), (cx + 8, top - 2), (cx, top)]), (100, 210, 80))
    elif sid in ('vetoad', 'vetoadmax'):
        c.part(lambda d: d.rounded_rectangle([cx - 11, top - 12, cx + 11, top - 2], radius=2), (200, 40, 40))
        c.flat(lambda d, k: d.text((cx - 10, top - 13), "NON", fill=k), (255, 255, 255))
    elif sid in ('brexitt', 'frontierex'):
        c.part(lambda d: d.rectangle([cx - 10, top - 10, cx + 10, top - 2]), (20, 40, 120))
        c.flat(lambda d, k: d.line([(cx - 10, top - 6), (cx + 10, top - 6)], fill=k, width=2), (230, 40, 50))
        c.flat(lambda d, k: d.line([(cx, top - 10), (cx, top - 2)], fill=k, width=2), (230, 40, 50))
    elif sid in ('tarifaux', 'tarifator'):
        c.part(lambda d: d.rectangle([cx - 13, top - 14, cx + 13, top - 2]), (250, 250, 240))
        c.flat(lambda d, k: d.text((cx - 11, top - 15), "25%", fill=k), (200, 30, 30))
    elif sid in ('pandiplo',):
        for ex in (-1, 1):
            c.flat(lambda d, k, ex=ex: d.ellipse([fx + ex * info['sep'] - 6, fy - 6, fx + ex * info['sep'] + 6, fy + 5], fill=k),
                   (30, 30, 40))
    elif sid in ('censourson',):
        c.part(lambda d: d.rectangle([cx - r, fy - 5, cx + r, fy + 3]), (20, 20, 20), shading=False)
    elif sid in ('assistome', 'emploifictif', 'changheure', 'pailleplast', 'manneken'):
        pass
    elif sid in ('glyphosaure',):
        for i in range(4):
            c.part(lambda d, i=i: d.polygon([(10 + i * 8, 44 - i * 2), (14 + i * 8, 34 - i * 2), (18 + i * 8, 44 - i * 2)]),
                   (150, 170, 70))
    elif sid in ('tracteuron',):
        for wx, wr in ((18, 10), (46, 7)):
            c.part(lambda d, wx=wx, wr=wr: d.ellipse([wx - wr, 58 - 2 * wr, wx + wr, 58]), (40, 40, 40))
            c.flat(lambda d, k, wx=wx, wr=wr: d.ellipse([wx - 3, 58 - wr - 3, wx + 3, 58 - wr + 3], fill=k), (230, 200, 60))
    elif sid in ('roamy', 'roamfree'):
        c.flat(lambda d, k: d.arc([cx - 10, top - 12, cx + 10, top + 8], 200, 340, fill=k, width=2), (255, 255, 255))
        c.flat(lambda d, k: d.arc([cx - 6, top - 6, cx + 6, top + 6], 200, 340, fill=k, width=2), (255, 255, 255))
    elif sid in ('erasmouse', 'erasmusplus', 'stagion', 'contractuel', 'titularis'):
        c.flat(lambda d, k: d.line([(cx - 6, top + 12), (cx, top + 20), (cx + 6, top + 12)], fill=k), (40, 80, 200))
        c.part(lambda d: d.rectangle([cx - 3, top + 20, cx + 3, top + 25]), (250, 250, 250))
        if sid in ('erasmusplus', 'titularis'):
            c.part(lambda d: d.polygon([(cx - 10, top + 1), (cx + 10, top + 1), (cx, top - 6)]), (30, 30, 50))
    elif sid in ('fromajus', 'appellatio'):
        rnd = random.Random(5)
        for _ in range(6):
            x, y = cx + rnd.randint(-r + 5, r - 5), fy + rnd.randint(-r + 4, r - 4)
            if abs(y - fy) > 5:
                c.flat(lambda d, k, x=x, y=y: d.ellipse([x - 2, y - 2, x + 2, y + 1], fill=k), shade(col, 0.75))
    elif sid in ('populo', 'tribun', 'demagogor', 'sondagex'):
        c.part(lambda d: d.polygon([(46, 30), (58, 24), (58, 40), (46, 34)]), (230, 230, 240))
    elif sid in ('trollbot', 'botfarm', 'algoritmo', 'iact', 'fakeon'):
        c.flat(lambda d, k: d.rectangle([cx - 2, top - 8, cx + 2, top], fill=k), (60, 60, 70))
        c.flat(lambda d, k: d.ellipse([cx - 3, top - 12, cx + 3, top - 6], fill=k), (255, 60, 60))
    elif sid in ('gazoduc',):
        c.part(lambda d: d.rectangle([40, 8, 50, 14]), (190, 40, 40))
    elif sid in ('troikat',):
        for ex in (-14, 14):
            c.part(lambda d, ex=ex: d.ellipse([info['cx'] + ex - 7, top - 4, info['cx'] + ex + 7, top + 10]), col)
    elif sid in ('trilogon',):
        for ex in (-16, 16):
            c.part(lambda d, ex=ex: d.ellipse([cx + ex - 8, fy - 14, cx + ex + 8, fy + 2]), shade(col, 0.95))
    elif sid in ('draghizord',):
        c.part(lambda d: d.rectangle([cx - 12, top + 2, cx + 12, top + 6]), (30, 30, 40))
    elif sid in ('bouchatach',):
        c.part(lambda d: d.rounded_rectangle([cx - 8, top - 8, cx + 8, top + 2], radius=2), (240, 240, 250))
        c.flat(lambda d, k: d.line([(cx + 8, top - 3), (cx + 14, top + 6)], fill=k, width=2), (240, 240, 250))
    elif sid in ('interpreton',):
        c.part(lambda d: d.arc([cx - 13, top - 2, cx + 13, top + 20], 180, 360, fill=255, width=2), (40, 40, 40),
               shading=False)
        for ex in (-13, 11):
            c.part(lambda d, ex=ex: d.rectangle([cx + ex, top + 8, cx + ex + 3, top + 14]), (40, 40, 40))
    elif sid in ('transhumon', 'transhumax', 'archivor', 'paperasse_mon'):
        c.flat(lambda d, k: d.rectangle([cx - r + 3, top + 4, cx + r - 3, top + 6], fill=k), shade(col, 0.6))
    elif sid in ('pralinou',):
        c.flat(lambda d, k: d.arc([cx - r + 3, top + 2, cx + r - 3, top + 14], 200, 340, fill=k, width=2), (240, 220, 200))
    elif sid in ('frituron',):
        for i in range(-2, 3):
            c.part(lambda d, i=i: d.rectangle([cx + i * 5 - 2, top - 10 + abs(i) * 2, cx + i * 5 + 2, top + 4]), (250, 210, 80))
    elif sid in ('atomiom',):
        pass
    elif sid in ('inflaton', 'hyperflaton', 'spreadon', 'plafonnor'):
        c.flat(lambda d, k: d.line([(cx - 8, fy + 14), (cx, fy + 8), (cx + 4, fy + 12), (cx + 10, fy + 2)], fill=k, width=2),
               (220, 40, 40))
    elif sid in ('austerix',):
        c.flat(lambda d, k: d.rectangle([cx - r, fy + 12, cx + r, fy + 15], fill=k), (90, 60, 30))
    elif sid in ('terrara',):
        for i in range(5):
            a = i * 1.3
            x, y = cx + int(r * 0.6 * math.cos(a)), fy + int(r * 0.6 * math.sin(a)) + 8
            c.flat(lambda d, k, x=x, y=y: d.polygon([(x, y - 3), (x + 3, y), (x, y + 3), (x - 3, y)], fill=k), (210, 160, 255))
    elif sid in ('pigeonix', 'pigeon_lux'):
        c.flat(lambda d, k: d.rectangle([cx - r + 4, fy + 6, cx + r - 4, fy + 8], fill=k), (90, 160, 120))
    elif sid in ('bruxellair',):
        for i in range(5):
            c.flat(lambda d, k, i=i: d.line([(18 + i * 7, 54), (16 + i * 7, 60)], fill=k), (80, 140, 230))
    elif sid in ('dejeunix',):
        c.part(lambda d: d.ellipse([cx - 12, top - 4, cx + 12, top + 4]), (250, 250, 250))
    elif sid in ('mercosaur',):
        for i in range(4):
            c.part(lambda d, i=i: d.polygon([(14 + i * 7, 30), (17 + i * 7, 22), (20 + i * 7, 30)]), (230, 200, 60))
    if stage == 3 and sid not in ('constitutio',):
        # final forms: little cape/crown accent in type colour
        c.part(lambda d: d.polygon([(cx - 6, top + 1), (cx - 3, top - 5), (cx, top), (cx + 3, top - 5), (cx + 6, top + 1)]),
               acc)


# ---------------------------------------------------------------- build
def stage_of(sp, species):
    by_into = {s['evo']['into']: s for s in species if s.get('evo')}
    st = 1
    cur = sp['id']
    while cur in by_into:
        st += 1
        cur = by_into[cur]['id']
    has_next = bool(sp.get('evo'))
    total = sum(sp['base'])
    if st == 1 and not has_next:
        st = 2 if total >= 400 else 1
        if total >= 580:
            st = 3
    return st


def scale_for(stage, total):
    return {1: 0.68, 2: 0.86, 3: 1.0}[stage] * (1.05 if total >= 580 else 1.0)


def draw_creature(sp, species, back=False):
    c = Canvas()
    rnd = random.Random(sp['num'] * 7919)
    col = COLORS.get(sp.get('color', 'grey'), (150, 150, 160))
    stage = stage_of(sp, species)
    s = scale_for(stage, sum(sp['base']))
    shape = sp.get('shape', 'blob')
    if shape == 'humanoid':
        suit = {'LOBBY': (30, 30, 36), 'FANTOME': (190, 180, 230), 'TECHNO': (50, 60, 90), 'SOCIAL': (60, 90, 170)}.get(
            sp['types'][0], (40, 48, 80))
        info = plan_humanoid(c, col if sp['types'][0] != 'FANTOME' else (225, 220, 250), s, rnd, sp, suit)
    else:
        info = PLANS.get(shape, plan_blob)(c, col, s, rnd, sp)
    if not back:
        prop(c, sp, info, stage, col)
        mood = 'angry' if sp['types'][0] in ('POPULISTE', 'SOUVERAIN', 'LOBBY') or stage == 3 else 'happy'
        fx, fy = info['face']
        sz = 4 if s > 0.8 else 3
        if sp['id'] == 'censourson':
            pass
        else:
            eyes(c, fx, fy, info['sep'], sz, mood)
        style = {'POPULISTE': 'open', 'LOBBY': 'grin', 'SOUVERAIN': 'flat', 'FANTOME': 'fang', 'TECHNO': 'flat'}.get(
            sp['types'][0], 'smile')
        if stage == 1:
            style = 'smile' if style != 'fang' else style
        mouth(c, fx, fy + sz + 4, style, 3 + int(s * 2))
    img = c.img
    if sp['types'][0] == 'FANTOME' or (len(sp['types']) > 1 and sp['types'][1] == 'FANTOME'):
        a = np.array(img)
        a[..., :3] = (a[..., :3] * 0.8 + np.array([200, 190, 255]) * 0.2).astype(np.uint8)
        img = Image.fromarray(a, 'RGBA')
    if back:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
        a = np.array(img)
        a[..., :3] = (a[..., :3] * 0.85).astype(np.uint8)
        img = Image.fromarray(a, 'RGBA')
        # bigger and cut at the bottom (seen from behind, closer to the camera)
        img = img.resize((80, 80), Image.NEAREST).crop((8, 4, 72, 68))
    return img


def main():
    import mkgfx
    species = json.load(open(os.path.join(ROOT, 'data/species.json'), encoding='utf-8'))
    species.sort(key=lambda s: s['num'])
    out = os.path.join(ROOT, 'nitrofs/creatures')
    os.makedirs(out, exist_ok=True)
    stamp = os.path.join(out, '_stamp')
    srcs = [__file__, os.path.join(ROOT, 'data/species.json')]
    if os.path.exists(stamp) and all(os.path.getmtime(s) < os.path.getmtime(stamp) for s in srcs):
        return
    icons = []
    for i, sp in enumerate(species):
        for back in (False, True):
            img = draw_creature(sp, species, back)
            idx, pal = mkgfx.quantize_rgb(img, 31)
            mkgfx.write_spr(os.path.join(out, f"{'b' if back else 'f'}{i}.spr"), [idx],
                            [0] + [mkgfx.rgb15(*p) for p in pal], 8, 64, 64)
            if not back:
                icons.append(draw_creature(sp, species).resize((32, 32), Image.BOX))
    # icons: shared 31-colour palette
    sheet = Image.new('RGBA', (32, 32 * len(icons)))
    for i, ic in enumerate(icons):
        a = np.array(ic)
        a[..., 3] = np.where(a[..., 3] > 100, 255, 0)
        sheet.paste(Image.fromarray(a, 'RGBA'), (0, 32 * i))
    idx, pal = mkgfx.quantize_rgb(sheet, 31)
    d = bytearray(b'ICN1') + struct.pack('<HH', len(icons), len(pal) + 1)
    d += struct.pack('<H', 0) + b''.join(struct.pack('<H', mkgfx.rgb15(*p)) for p in pal)
    d += bytes(idx.astype('uint8').reshape(-1))
    open(os.path.join(out, 'icons.bin'), 'wb').write(d)
    open(stamp, 'w').write('ok')
    print('creatures', len(species))


def preview():
    species = json.load(open(os.path.join(ROOT, 'data/species.json'), encoding='utf-8'))
    species.sort(key=lambda s: s['num'])
    cols = 10
    sheet = Image.new('RGBA', (cols * 66, ((len(species) + cols - 1) // cols) * 66), (120, 170, 120, 255))
    for i, sp in enumerate(species):
        sheet.alpha_composite(draw_creature(sp, species), ((i % cols) * 66 + 1, (i // cols) * 66 + 1))
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save('/tmp/creatures.png')
    b = Image.new('RGBA', (66 * 10, 66), (120, 170, 120, 255))
    for i in range(10):
        b.alpha_composite(draw_creature(species[i], species, True), (i * 66, 1))
    b.resize((b.width * 2, b.height * 2), Image.NEAREST).save('/tmp/creatures_back.png')


if __name__ == '__main__':
    preview()
