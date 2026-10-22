#!/usr/bin/env python3
"""Landmark buildings and extra props for EU Simulator maps (registered into tiles.OBJECTS/TILES)."""
import math
import random

from PIL import Image, ImageDraw

import tiles as T
from tiles import P, Obj, Tile, new, B_SOLID, B_WALK, B_WATER, B_GRASS


def rgb(h):
    return T.rgb(h)


K = P['k']


def outline_box(d, box, fill, edge=K):
    d.rectangle(box, fill=edge)
    x0, y0, x1, y1 = box
    d.rectangle([x0 + 1, y0 + 1, x1 - 1, y1 - 1], fill=fill)


def eu_flag(d, x, y, w=12, h=8):
    d.rectangle([x, y, x + w, y + h], fill=P['eu'])
    for k in range(12):
        a = k * math.pi / 6
        d.point((x + w / 2 + (w * 0.3) * math.cos(a), y + h / 2 + (h * 0.32) * math.sin(a)), fill=P['gold'])


def door(d, x, y, glass=True, w=12):
    d.rectangle([x, y, x + w, y + 15], fill=K)
    d.rectangle([x + 1, y + 1, x + w - 1, y + 15], fill=P['gl1'] if glass else P['wd1'])
    d.line([(x + w // 2, y + 1), (x + w // 2, y + 15)], fill=K)
    if glass:
        d.line([(x + 2, y + 3), (x + 4, y + 1)], fill=P['gl2'])


def beh_grid(w, h, doors=(), walk_rows=0):
    rows = []
    for y in range(h):
        r = ['#'] * w
        rows.append(r)
    for (dx, dy) in doors:
        rows[dy][dx] = 'D'
    return [''.join(r) for r in rows]


def label(im, text, cx, y, bg='eu'):
    lw = T.sign_width(text)
    d = ImageDraw.Draw(im)
    d.rectangle([cx - lw // 2, y, cx + lw // 2, y + 8], fill=K)
    d.rectangle([cx - lw // 2 + 1, y + 1, cx + lw // 2 - 1, y + 7], fill=P[bg])
    T._tiny_text(im, cx - lw // 2 + 3, y + 2, text, P['wh'])


# ---------------------------------------------------------------- big landmarks
def berlaymont():
    w, h = 12, 7
    im = new(w * 16, h * 16)
    d = ImageDraw.Draw(im)
    W, H = w * 16, h * 16
    # roof (seen from above): cross shape suggestion
    d.rectangle([0, 0, W - 1, 36], fill=P['rg1'])
    d.rectangle([W // 2 - 26, 0, W // 2 + 26, 36], fill=P['rg2'])
    for x in range(4, W, 12):
        d.rectangle([x, 8, x + 6, 12], fill=P['rg0'])
    d.line([(0, 36), (W, 36)], fill=K)
    # facade glass with louvres
    d.rectangle([0, 37, W - 1, H - 1], fill=P['gl0'])
    for y in range(40, H - 4, 4):
        d.line([(1, y), (W - 2, y)], fill=P['mt2'])
        d.line([(1, y + 1), (W - 2, y + 1)], fill=P['gl3'])
    for x in range(8, W, 16):
        d.line([(x, 37), (x, H - 18)], fill=P['mt1'])
    # entrance canopy
    d.rectangle([W // 2 - 30, H - 22, W // 2 + 30, H - 18], fill=P['mt0'])
    door(d, W // 2 - 7, H - 16, True, 14)
    d.rectangle([0, 0, W - 1, H - 1], outline=K)
    label(im, 'COMMISSION', W // 2, 24)
    return Obj(im, beh_grid(w, h, [(6, h - 1)]), None, [(6, h - 1)])


def parlement_bxl():
    """Paul-Henri Spaak building (Espace Léopold): glass curtain wall under the big barrel-vaulted glass roof
    nicknamed the « Caprice des Dieux », between two lower stone wings."""
    w, h = 10, 6
    im = new(w * 16, h * 16)
    d = ImageDraw.Draw(im)
    W, H = w * 16, h * 16
    # stone side wings
    for x0, x1 in ((0, 25), (W - 26, W - 1)):
        outline_box(d, [x0, 34, x1, H - 1], P['iw1'])
        d.rectangle([x0 + 1, 35, x1 - 1, 38], fill=P['iw0'])
        for y in range(44, H - 6, 10):
            for x in range(x0 + 4, x1 - 3, 6):
                d.rectangle([x, y, x + 3, y + 5], fill=P['gl3'])
                d.point((x, y), fill=P['gl1'])
    # central block: glass curtain wall
    cx0, cx1 = 22, W - 23
    outline_box(d, [cx0, 40, cx1, H - 1], P['gl0'])
    for y in range(44, H - 2, 6):
        d.line([(cx0 + 1, y), (cx1 - 1, y)], fill=P['gl3'])
        d.line([(cx0 + 1, y + 1), (cx1 - 1, y + 1)], fill=P['gl1'])
    for x in range(cx0 + 6, cx1, 8):
        d.line([(x, 41), (x, H - 2)], fill=P['mt1'])
    # the vault: half of an ellipse, glazed, with curved ribs and longitudinal bands
    vx0, vx1, vy0, vy1 = 14, W - 15, 2, 82
    box = [vx0, vy0, vx1, vy1]
    d.chord(box, 180, 360, fill=P['gl1'], outline=K)
    mx, ry = (vx0 + vx1) / 2, (vy1 - vy0) / 2
    rx = (vx1 - vx0) / 2
    cy = vy0 + ry
    for k in range(1, 4):
        f = k / 4
        d.arc([mx - rx, cy - ry * (1 - f * 0.25), mx + rx, cy + ry * (1 - f * 0.25)], 180, 360,
              fill=P['gl2'] if k == 1 else P['gl0'])
    for i in range(-6, 7):
        x = mx + rx * i / 7
        top = cy - ry * math.sqrt(max(0.0, 1 - ((x - mx) / rx) ** 2))
        d.line([(x, top + 1), (x, cy - 1)], fill=P['mt2'] if i % 3 == 0 else P['gl0'])
    d.line([(vx0, cy), (vx1, cy)], fill=K)
    # highlight on the curve
    d.arc([vx0 + 6, vy0 + 4, vx1 - 6, vy1 - 4], 205, 250, fill=P['wh'])
    # cornice between vault and facade
    d.rectangle([cx0 - 2, int(cy) + 1, cx1 + 2, int(cy) + 3], fill=P['mt0'])
    # entrance: glass canopy and doors, EU flag over the door
    d.rectangle([W // 2 - 24, H - 22, W // 2 + 24, H - 19], fill=P['mt0'])
    d.line([(W // 2 - 24, H - 22), (W // 2 + 24, H - 22)], fill=K)
    door(d, W // 2 - 7, H - 16, True, 14)
    eu_flag(d, W // 2 - 6, 48, 12, 8)
    d.rectangle([W // 2 - 6, 48, W // 2 + 6, 56], outline=K)
    return Obj(im, beh_grid(w, h, [(5, h - 1)]), None, [(5, h - 1)])


def louise_weiss():
    w, h = 10, 7
    im = new(w * 16, h * 16)
    d = ImageDraw.Draw(im)
    W, H = w * 16, h * 16
    d.ellipse([10, 0, W - 10, 60], fill=P['rg2'], outline=K)
    d.ellipse([30, 8, W - 30, 50], fill=P['gl1'], outline=P['gl3'])
    d.rectangle([10, 30, W - 10, H - 1], fill=P['gl0'])
    for y in range(34, H - 18, 5):
        d.line([(11, y), (W - 11, y)], fill=P['gl2'])
    d.rectangle([10, 30, W - 10, H - 1], outline=K)
    door(d, W // 2 - 7, H - 16, True, 14)
    label(im, 'HEMICYCLE', W // 2, 64)
    return Obj(im, beh_grid(w, h, [(5, h - 1)]), None, [(5, h - 1)])


def bce_tower():
    w, h = 7, 9
    im = new(w * 16, h * 16)
    d = ImageDraw.Draw(im)
    W, H = w * 16, h * 16
    for (x0, x1, top) in ((6, 52, 0), (56, 104, 10)):
        d.rectangle([x0, top, x1, H - 1], fill=P['gl0'], outline=K)
        for y in range(top + 4, H - 18, 6):
            d.line([(x0 + 2, y), (x1 - 2, y)], fill=P['gl2'])
        for x in range(x0 + 6, x1, 8):
            d.line([(x, top + 2), (x, H - 18)], fill=P['gl3'])
    # big euro sign on top
    d.ellipse([W // 2 - 16, 20, W // 2 + 16, 52], fill=P['eu'], outline=K)
    d.arc([W // 2 - 9, 26, W // 2 + 9, 46], 50, 310, fill=P['gold'], width=3)
    d.line([(W // 2 - 12, 34), (W // 2 + 2, 34)], fill=P['gold'], width=2)
    d.line([(W // 2 - 12, 39), (W // 2 + 2, 39)], fill=P['gold'], width=2)
    door(d, W // 2 - 7, H - 16, True, 14)
    label(im, 'ECB', W // 2, H - 26)
    return Obj(im, beh_grid(w, h, [(3, h - 1)]), None, [(3, h - 1)])


def cjue():
    w, h = 10, 7
    im = new(w * 16, h * 16)
    d = ImageDraw.Draw(im)
    W, H = w * 16, h * 16
    gold = rgb('c8a040')
    for x0 in (4, W - 40):
        d.rectangle([x0, 0, x0 + 36, H - 30], fill=gold, outline=K)
        for y in range(4, H - 32, 5):
            d.line([(x0 + 2, y), (x0 + 34, y)], fill=rgb('a07a28'))
    d.rectangle([0, H - 48, W - 1, H - 1], fill=P['wl0'], outline=K)
    for x in range(8, W - 8, 12):
        d.rectangle([x, H - 40, x + 4, H - 20], fill=P['gl0'])
    door(d, W // 2 - 7, H - 16, True, 14)
    label(im, 'COURT OF JUSTICE', W // 2, H - 47)
    return Obj(im, beh_grid(w, h, [(5, h - 1)]), None, [(5, h - 1)])


def europa_building():
    w, h = 9, 7
    im = new(w * 16, h * 16)
    d = ImageDraw.Draw(im)
    W, H = w * 16, h * 16
    cx = W // 2
    # glass cube over a patchwork of recycled wooden window frames (muted, two-tone)
    d.rectangle([0, 24, W - 1, H - 1], fill=rgb('9cc4e4'), outline=K)
    rnd = random.Random(11)
    tones = [rgb('a87850'), rgb('8a6040'), rgb('c09468'), rgb('7a6a5a'), rgb('b8a890')]
    for y in range(27, H - 20, 7):
        for x in range(3, W - 3, 7):
            c = rnd.choice(tones)
            d.rectangle([x, y, x + 5, y + 5], outline=c)
            d.point((x + 2, y + 2), fill=rgb('d8ecf8'))
    d.line([(1, 25), (W - 2, 25)], fill=rgb('e8f4fc'))
    # ground floor: clear glass band
    d.rectangle([1, H - 19, W - 2, H - 2], fill=rgb('6aa0cc'))
    for x in range(4, W - 4, 10):
        d.line([(x, H - 19), (x, H - 2)], fill=rgb('4a80b0'))
    # the "lantern": a milky egg-shaped vessel seen through the glass
    d.ellipse([cx - 17, 2, cx + 17, 60], fill=rgb('f6e2a8'), outline=K)
    d.ellipse([cx - 12, 7, cx + 10, 54], fill=rgb('fff2cc'))
    for y in range(14, 56, 8):
        hw = int(16 * math.sqrt(max(0.0, 1 - ((y - 31) / 29.0) ** 2)))
        d.line([(cx - hw + 2, y), (cx + hw - 2, y)], fill=rgb('e8cc88'))
    d.line([(cx - 8, 12), (cx - 11, 24)], fill=P['wh'])
    door(d, cx - 7, H - 16, True, 14)
    label(im, 'EUROPEAN COUNCIL', cx, H - 30)
    return Obj(im, beh_grid(w, h, [(4, h - 1)]), None, [(4, h - 1)])

def ramp(key, c):
    """Register a 4-step hue-shifted ramp (dark bluish -> warm light) around colour c as P[key+'0'..'3']."""
    import colorsys
    r, g, b = (v / 255 for v in c[:3])
    h, l, sat = colorsys.rgb_to_hls(r, g, b)

    def mk(dh, dl, ds):
        hh = (h + dh) % 1.0
        rr, gg, bb = colorsys.hls_to_rgb(hh, max(0, min(1, l + dl)), max(0, min(1, sat * ds)))
        return (int(rr * 255), int(gg * 255), int(bb * 255), 255)
    # shadows rotate towards blue (hue 0.62), lights towards yellow (hue 0.15)
    towards = lambda target, k: ((target - h + 0.5) % 1.0 - 0.5) * k
    P[key + '0'] = mk(towards(0.62, 0.18), -0.16, 0.9)
    P[key + '1'] = mk(0, 0, 1)
    P[key + '2'] = mk(towards(0.15, 0.12), 0.1, 0.95)
    P[key + '3'] = mk(towards(0.15, 0.25), 0.2, 0.85)
    if sat > 0.6 and l > 0.45:   # tame acid colours (gold roof)
        for k in '0123':
            r_, g_, b_ = colorsys.rgb_to_hls(*(v / 255 for v in P[key + k][:3]))[::1]
            rr, gg, bb = colorsys.hls_to_rgb(r_, g_, b_ * 0.7)
            P[key + k] = (int(rr * 255), int(gg * 255), int(bb * 255), 255)
    return key


def arena(color='eu', emblem='star'):
    w, h = 7, 5
    key = ramp('ar_' + color, P[color])
    o = T.building(w, h, key, 'wl', door_x=3, door_gap=26)
    im = o.img
    d = ImageDraw.Draw(im)
    W, H = w * 16, h * 16
    # emblem plaque on the roof
    d.rounded_rectangle([W // 2 - 14, 9, W // 2 + 14, 33], radius=3, fill=K)
    d.rounded_rectangle([W // 2 - 13, 10, W // 2 + 13, 32], radius=3, fill=P['wh'])
    d.line([(W // 2 - 11, 31), (W // 2 + 11, 31)], fill=P['wl2'])
    pts = []
    for i in range(10):
        r = 9 if i % 2 == 0 else 4
        a = -math.pi / 2 + i * math.pi / 5
        pts.append((W // 2 + r * math.cos(a), 21 + r * math.sin(a)))
    d.polygon(pts, fill=P['gold'], outline=P['br0'])
    d.point((W // 2 - 2, 17), fill=P['wh'])
    # pillars either side of the door
    for x in (W // 2 - 13, W // 2 + 10):
        d.rectangle([x, 50, x + 3, H - 2], fill=P['wl1'])
        d.line([(x + 3, 50), (x + 3, H - 2)], fill=P['wl3'])
        d.line([(x - 1, 49), (x + 4, 49)], fill=P['wl2'])
    label(im, 'ARENE', W // 2, 39, 'rr0')
    return o


def gare():
    w, h = 8, 5
    im = new(w * 16, h * 16)
    d = ImageDraw.Draw(im)
    W, H = w * 16, h * 16
    # glass-and-iron gable roof, lit from the left
    d.polygon([(0, 31), (W // 2, 0), (W - 1, 31)], fill=K)
    d.polygon([(2, 30), (W // 2, 2), (W // 2, 30)], fill=P['rg2'])
    d.polygon([(W // 2, 2), (W - 3, 30), (W // 2, 30)], fill=P['rg1'])
    for k in range(1, 6):
        y = 2 + k * 5
        half = int((W // 2) * y / 30)
        d.line([(W // 2 - half + 2, y), (W // 2 - 1, y)], fill=P['rg3'])
        d.line([(W // 2 + 1, y), (W // 2 + half - 2, y)], fill=P['rg0'])
    # brick hall with a cool shadow under the eaves
    d.rectangle([0, 30, W - 1, H - 1], fill=K)
    d.rectangle([1, 31, W - 2, H - 1], fill=P['br1'])
    d.rectangle([1, 31, W - 2, 33], fill=P['br2'])
    for y in range(36, H - 3, 3):
        for x in range(2 + (y % 2) * 3, W - 2, 6):
            d.point((x, y), fill=P['br0'])
    d.rectangle([1, H - 3, W - 2, H - 1], fill=P['wl2'])
    # clock
    d.ellipse([W // 2 - 10, 6, W // 2 + 10, 26], fill=K)
    d.ellipse([W // 2 - 9, 7, W // 2 + 9, 25], fill=P['wh'])
    d.arc([W // 2 - 9, 7, W // 2 + 9, 25], 20, 160, fill=P['wl2'])
    d.line([(W // 2, 16), (W // 2, 10)], fill=K)
    d.line([(W // 2, 16), (W // 2 + 5, 16)], fill=K)
    # arched windows
    for x in range(8, W - 8, 20):
        if abs(x + 7 - W // 2) < 12:
            continue
        d.pieslice([x, 38, x + 14, 58], 180, 360, fill=K)
        d.rectangle([x, 48, x + 14, 61], fill=K)
        d.pieslice([x + 1, 39, x + 13, 57], 180, 360, fill=P['gl1'])
        d.rectangle([x + 1, 48, x + 13, 60], fill=P['gl0'])
        d.line([(x + 7, 40), (x + 7, 60)], fill=P['wl1'])
        d.line([(x + 3, 46), (x + 5, 43)], fill=P['gl2'])
        d.line([(x, 62), (x + 14, 62)], fill=P['wl1'])
    door(d, W // 2 - 7, H - 16, True, 14)
    label(im, 'GARE', W // 2, 34, 'rr0')
    return Obj(im, beh_grid(w, h, [(4, h - 1)]), None, [(4, h - 1)])


def atomium():
    w, h = 5, 7
    im = new(w * 16, h * 16)
    d = ImageDraw.Draw(im)
    W, H = w * 16, h * 16
    cx = W // 2
    nodes = [(cx, 10), (cx - 26, 30), (cx + 26, 30), (cx, 46), (cx - 26, 62), (cx + 26, 62), (cx, 80)]
    for a in nodes:
        for b in nodes:
            if a < b and math.dist(a, b) < 40:
                d.line([a, b], fill=P['mt0'], width=3)
    d.line([(cx, 80), (cx, H - 1)], fill=P['mt0'], width=3)
    d.polygon([(cx - 14, H - 1), (cx, 84), (cx + 14, H - 1)], outline=P['mt0'])
    for (x, y) in nodes:
        d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=P['mt2'], outline=K)
        d.ellipse([x - 6, y - 7, x - 1, y - 2], fill=P['wh'])
    beh = ['.....', '.....', '.###.', '.###.', '.###.', '..#..', '..#..']
    above = ['11111', '11111', '10001', '10001', '10001', '11011', '00000']
    return Obj(im, beh, above)


def big_ben():
    w, h = 3, 8
    im = new(w * 16, h * 16)
    d = ImageDraw.Draw(im)
    W, H = w * 16, h * 16
    stone = rgb('d8c088')
    d.polygon([(W // 2, 0), (8, 24), (W - 8, 24)], fill=P['rg1'], outline=K)
    d.rectangle([8, 24, W - 8, H - 1], fill=stone, outline=K)
    d.ellipse([W // 2 - 10, 30, W // 2 + 10, 50], fill=P['wh'], outline=K)
    d.line([(W // 2, 40), (W // 2, 33)], fill=K)
    d.line([(W // 2, 40), (W // 2 + 6, 40)], fill=K)
    for y in range(56, H - 4, 8):
        d.line([(10, y), (W - 10, y)], fill=rgb('b09860'))
    beh = ['...', '...', '...', '.#.', '.#.', '.#.', '###', '###']
    above = ['111', '111', '111', '101', '101', '101', '000', '000']
    return Obj(im, beh, above)


def westminster():
    w, h = 10, 5
    im = new(w * 16, h * 16)
    d = ImageDraw.Draw(im)
    W, H = w * 16, h * 16
    stone = rgb('d8c088')
    d.rectangle([0, 12, W - 1, H - 1], fill=stone, outline=K)
    for x in range(0, W, 10):
        d.polygon([(x, 12), (x + 5, 0), (x + 10, 12)], fill=stone, outline=K)
    for x in range(6, W - 6, 10):
        d.rectangle([x, 22, x + 4, 50], fill=P['gl3'])
    door(d, W // 2 - 7, H - 16, False, 14)
    label(im, 'WESTMINSTER', W // 2, 54, 'rr0')
    return Obj(im, beh_grid(w, h), None, [])


def acropole():
    w, h = 10, 5
    im = new(w * 16, h * 16)
    d = ImageDraw.Draw(im)
    W, H = w * 16, h * 16
    marble, sh = rgb('ece4d4'), rgb('c8bca8')
    d.polygon([(4, 18), (W // 2, 0), (W - 5, 18)], fill=marble, outline=K)
    d.rectangle([2, 18, W - 3, 24], fill=marble, outline=K)
    for x in range(8, W - 8, 14):
        d.rectangle([x, 24, x + 8, H - 10], fill=marble)
        d.line([(x + 6, 24), (x + 6, H - 10)], fill=sh)
        d.rectangle([x, 24, x + 8, H - 10], outline=K)
    d.rectangle([0, H - 10, W - 1, H - 1], fill=sh, outline=K)
    door(d, W // 2 - 7, H - 16, False, 14)
    return Obj(im, beh_grid(w, h), None, [])


def parliament_bud():
    w, h = 12, 6
    im = new(w * 16, h * 16)
    d = ImageDraw.Draw(im)
    W, H = w * 16, h * 16
    cx = W // 2
    stone, stone_d, roof, roof_d = rgb('ece0c8'), rgb('c8b898'), rgb('b04030'), rgb('7a2a20')
    # neo-gothic pinnacles behind the roofline
    for x in list(range(6, cx - 26, 14)) + list(range(cx + 30, W - 4, 14)):
        d.rectangle([x, 22, x + 3, 38], fill=stone_d, outline=K)
        d.polygon([(x - 1, 22), (x + 1, 14), (x + 4, 22)], fill=roof, outline=K)
    # long red roof
    d.rectangle([0, 34, W - 1, 42], fill=roof, outline=K)
    d.line([(1, 35), (W - 2, 35)], fill=rgb('d06050'))
    # facade
    d.rectangle([0, 42, W - 1, H - 1], fill=stone, outline=K)
    d.rectangle([1, H - 6, W - 2, H - 2], fill=stone_d)
    for x in range(6, W - 8, 9):
        if abs(x + 2 - cx) < 12:
            continue
        for y0 in (46, 64):
            d.rectangle([x, y0 + 2, x + 4, y0 + 12], fill=P['gl3'])
            d.point((x + 2, y0 + 1), fill=P['gl3'])
            d.line([(x, y0 + 12), (x + 4, y0 + 12)], fill=stone_d)
    # central drum + ribbed dome with lantern spire (drawn last so nothing cuts it)
    d.rectangle([cx - 20, 22, cx + 20, 44], fill=stone, outline=K)
    for x in range(cx - 16, cx + 17, 8):
        d.rectangle([x - 1, 27, x + 1, 38], fill=P['gl3'])
    d.pieslice([cx - 22, 2, cx + 22, 42], 180, 360, fill=roof, outline=K)
    for k in (-14, -7, 0, 7, 14):
        d.line([(cx + k, 22), (cx + k // 2, 6)], fill=roof_d)
    d.line([(cx - 20, 21), (cx + 20, 21)], fill=K)
    d.rectangle([cx - 2, 0, cx + 2, 4], fill=stone_d, outline=K)
    door(d, cx - 7, H - 16, False, 14)
    label(im, 'ORSZAGHAZ', cx, 46, 'rr0')
    return Obj(im, beh_grid(w, h, [(6, h - 1)]), None, [(6, h - 1)])


def palac_kultury():
    """Warsaw's Palace of Culture and Science: stepped tower with a needle spire."""
    w, h = 12, 7
    im = new(w * 16, h * 16)
    d = ImageDraw.Draw(im)
    W, H = w * 16, h * 16
    cx = W // 2
    st, st_d, st_l = rgb('e4d6b8'), rgb('b8a47e'), rgb('f4ead4')

    def block(x0, y0, x1, y1):
        d.rectangle([x0, y0, x1, y1], fill=st, outline=K)
        d.line([(x0 + 1, y0 + 1), (x1 - 1, y0 + 1)], fill=st_l)
        for x in range(x0 + 4, x1 - 2, 6):
            d.line([(x, y0 + 4), (x, y1 - 2)], fill=st_d)

    def crown(x0, x1, y):
        for x in range(x0 + 1, x1 - 1, 4):
            d.rectangle([x, y - 3, x + 1, y], fill=st_d)

    # needle spire
    d.line([(cx, 0), (cx, 14)], fill=rgb('8a8a90'))
    d.polygon([(cx - 3, 18), (cx, 6), (cx + 3, 18)], fill=st_d, outline=K)
    block(cx - 12, 18, cx + 12, 46)
    crown(cx - 12, cx + 12, 18)
    d.rectangle([cx - 3, 24, cx + 3, 30], fill=rgb('f0f0e0'), outline=K)  # clock
    block(cx - 26, 44, cx + 26, 72)
    crown(cx - 26, cx + 26, 44)
    # wings
    block(2, 80, 52, H - 1)
    block(W - 53, 80, W - 3, H - 1)
    crown(2, 52, 80)
    crown(W - 53, W - 3, 80)
    block(cx - 44, 70, cx + 44, H - 1)
    crown(cx - 44, cx + 44, 70)
    for y in range(52, 70, 6):
        for x in range(cx - 22, cx + 22, 6):
            d.rectangle([x, y, x + 2, y + 3], fill=P['gl3'])
    for y in range(86, H - 18, 7):
        for x in list(range(8, 48, 6)) + list(range(W - 48, W - 8, 6)):
            d.rectangle([x, y, x + 2, y + 3], fill=P['gl3'])
    # portico
    d.rectangle([cx - 14, H - 22, cx + 14, H - 1], fill=st_l, outline=K)
    for x in range(cx - 11, cx + 12, 5):
        d.line([(x, H - 20), (x, H - 2)], fill=st_d)
    door(d, cx - 7, H - 16, False, 14)
    label(im, 'PALAC KULTURY', cx, 74, 'rr0')
    return Obj(im, beh_grid(w, h, [(6, h - 1)]), None, [(6, h - 1)])

def eiffel():
    w, h = 6, 9
    im = new(w * 16, h * 16)
    W, H = w * 16, h * 16
    cx = W // 2
    iron, dk, lt = rgb('9a7458'), rgb('5a4430'), rgb('c09a78')
    px = im.load()
    p1, p2 = 64, 104  # 2nd and 1st platforms
    for y in range(8, H):
        t = (y - 8) / (H - 8)
        hw = int(2 + 44 * t ** 2.2)
        arch = 0
        if y > p2 + 3:  # the big arch between the legs
            r = 22
            dy = (H + 4) - y
            arch = int(math.sqrt(max(0, r * r - dy * dy))) if dy < r else 0
            arch = max(arch, int(hw * 0.45))
        for x in range(cx - hw, cx + hw + 1):
            if not (0 <= x < W):
                continue
            ax = abs(x - cx)
            if y > p2 + 3 and ax < arch:
                continue
            edge = ax >= hw - 1 or (y > p2 + 3 and ax <= arch)
            lattice = ((x + y) % 6 == 0) or ((x - y) % 6 == 0)
            col = dk if edge or lattice else iron
            px[x, y] = col + (255,) if len(col) == 3 else col
    d = ImageDraw.Draw(im)
    d.line([(cx, 0), (cx, 8)], fill=dk)
    d.rectangle([cx - 2, 6, cx + 2, 10], fill=lt, outline=dk)
    for py, extra in ((p1, 3), (p2, 4)):
        t = (py - 8) / (H - 8)
        hw = int(2 + 44 * t ** 2.2) + extra
        d.rectangle([cx - hw, py, cx + hw, py + 3], fill=lt, outline=dk)
    beh = ['......', '......', '......', '......', '......', '......', '#....#', '#....#', '#....#']
    above = ['111111'] * 6 + ['011110', '011110', '000000']
    return Obj(im, beh, above)

def sorbonne():
    w, h = 10, 5
    im = new(w * 16, h * 16)
    d = ImageDraw.Draw(im)
    W, H = w * 16, h * 16
    stone = rgb('e8dcc4')
    d.rectangle([0, 20, W - 1, H - 1], fill=stone, outline=K)
    d.ellipse([W // 2 - 18, 0, W // 2 + 18, 36], fill=P['rg1'], outline=K)
    d.rectangle([W // 2 - 26, 20, W // 2 + 26, H - 1], fill=stone, outline=K)
    d.polygon([(W // 2 - 26, 20), (W // 2, 10), (W // 2 + 26, 20)], fill=stone, outline=K)
    for x in range(W // 2 - 22, W // 2 + 22, 9):
        d.rectangle([x, 24, x + 4, H - 6], fill=rgb('c8bca8'), outline=K)
    for x in list(range(6, W // 2 - 30, 12)) + list(range(W // 2 + 32, W - 8, 12)):
        d.rectangle([x, 30, x + 6, 50], fill=P['gl3'])
    door(d, W // 2 - 7, H - 16, False, 14)
    label(im, 'SORBONNE', W // 2, 54, 'rb0')
    return Obj(im, beh_grid(w, h, [(5, h - 1)]), None, [(5, h - 1)])


def container(color):
    im = new(32, 32)
    d = ImageDraw.Draw(im)
    c = rgb(color)
    d.rectangle([0, 6, 31, 31], fill=c, outline=K)
    d.rectangle([0, 0, 31, 6], fill=tuple(min(255, v + 40) for v in c[:3]) + (255,), outline=K)
    for x in range(3, 31, 4):
        d.line([(x, 8), (x, 29)], fill=tuple(int(v * 0.7) for v in c[:3]) + (255,))
    return Obj(im, ['##', '##'], ['11', '00'])


def golf_flag():
    im = new(16, 32)
    d = ImageDraw.Draw(im)
    d.ellipse([2, 24, 13, 30], fill=rgb('206020'))
    d.ellipse([6, 26, 9, 28], fill=K)
    d.line([(7, 2), (7, 27)], fill=P['wh'])
    d.polygon([(8, 2), (15, 5), (8, 8)], fill=rgb('e02020'))
    return Obj(im, ['.', '#'], ['1', '0'])


def long_table(w=10):
    im = new(w * 16, 32)
    d = ImageDraw.Draw(im)
    W = w * 16
    d.rectangle([0, 6, W - 1, 22], fill=rgb('f4f0e8'), outline=K)
    d.rectangle([0, 22, W - 1, 26], fill=rgb('c8b898'), outline=K)
    for x in (4, W - 8):
        d.rectangle([x, 26, x + 4, 31], fill=rgb('8a6a40'))
    for x in range(20, W - 20, 40):
        d.ellipse([x, 10, x + 10, 16], fill=rgb('d0c8b8'))
    return Obj(im, ['#' * w, '#' * w])


def podium():
    im = new(32, 32)
    d = ImageDraw.Draw(im)
    d.rectangle([4, 8, 27, 31], fill=P['wd1'], outline=K)
    eu_flag(d, 10, 14, 12, 8)
    d.line([(16, 0), (16, 8)], fill=K)
    d.ellipse([13, 0, 19, 4], fill=K)
    return Obj(im, ['##', '##'], ['11', '00'])


def cabinet():
    im = new(16, 32)
    d = ImageDraw.Draw(im)
    d.rectangle([1, 2, 14, 31], fill=P['mt1'], outline=K)
    for y in (6, 14, 22):
        d.rectangle([3, y, 12, y + 6], fill=P['mt2'], outline=P['mt0'])
        d.rectangle([6, y + 2, 9, y + 3], fill=K)
    return Obj(im, ['#', '#'], ['1', '0'])


def server_rack():
    im = new(16, 32)
    d = ImageDraw.Draw(im)
    d.rectangle([1, 0, 14, 31], fill=rgb('282830'), outline=K)
    for y in range(3, 30, 4):
        d.line([(3, y), (12, y)], fill=rgb('484858'))
        d.point((11, y + 1), fill=rgb('40e040') if y % 8 else rgb('e04040'))
    return Obj(im, ['#', '#'], ['1', '0'])


def money_pile():
    im = new(16, 16)
    d = ImageDraw.Draw(im)
    for i, y in enumerate((10, 7, 4)):
        d.rectangle([2 + i, y, 13 - i, y + 4], fill=rgb('68a860'), outline=rgb('305830'))
    return Tile(im, B_SOLID)


def cobweb():
    im = new(16, 16)
    d = ImageDraw.Draw(im)
    for a in range(0, 91, 18):
        r = math.radians(a)
        d.line([(0, 0), (15 * math.cos(r), 15 * math.sin(r))], fill=rgb('d0d0e0'))
    for rr in (5, 10, 14):
        d.arc([-rr, -rr, rr, rr], 0, 90, fill=rgb('c0c0d0'))
    return im


def tractor():
    im = new(32, 32)
    d = ImageDraw.Draw(im)
    d.rectangle([4, 8, 22, 22], fill=rgb('2a8a30'), outline=K)
    d.rectangle([14, 2, 24, 14], fill=P['gl1'], outline=K)
    d.ellipse([0, 16, 16, 31], fill=K)
    d.ellipse([4, 20, 12, 28], fill=rgb('e0c040'))
    d.ellipse([20, 22, 30, 31], fill=K)
    return Obj(im, ['##', '##'], ['11', '00'])


def boat():
    im = new(48, 32)
    d = ImageDraw.Draw(im)
    d.polygon([(0, 14), (47, 14), (40, 30), (6, 30)], fill=P['wh'], outline=K)
    d.rectangle([12, 4, 34, 14], fill=P['eu'], outline=K)
    for x in range(15, 33, 6):
        d.rectangle([x, 7, x + 3, 10], fill=P['gl2'])
    d.line([(4, 22), (44, 22)], fill=P['rr0'], width=2)
    return Obj(im, ['WWW', 'WWW'], ['000', '000'])


def golf_cart():
    im = new(32, 16)
    d = ImageDraw.Draw(im)
    d.rectangle([2, 4, 28, 12], fill=P['wh'], outline=K)
    d.rectangle([4, 0, 26, 3], fill=P['wh'], outline=K)
    d.ellipse([3, 10, 9, 15], fill=K)
    d.ellipse([22, 10, 28, 15], fill=K)
    return Obj(im, ['##'])


def tracks_h():
    im = new(fill=P['d0'])
    d = ImageDraw.Draw(im)
    for x in range(0, 16, 4):
        d.rectangle([x, 3, x + 2, 12], fill=P['wd0'])
    d.line([(0, 5), (15, 5)], fill=P['mt0'])
    d.line([(0, 10), (15, 10)], fill=P['mt0'])
    return im


def red_carpet():
    im = new(fill=P['cr0'])
    d = ImageDraw.Draw(im)
    d.line([(0, 0), (0, 15)], fill=P['gold'])
    d.line([(15, 0), (15, 15)], fill=P['gold'])
    for y in range(2, 16, 4):
        d.point((7, y), fill=P['cr1'])
    return im


def marble_floor():
    im = new(fill=rgb('e8e4dc'))
    d = ImageDraw.Draw(im)
    d.line([(0, 15), (15, 15)], fill=rgb('c8c0b4'))
    d.line([(15, 0), (15, 15)], fill=rgb('c8c0b4'))
    d.line([(3, 4), (8, 9)], fill=rgb('d8d0c4'))
    return im


def dark_floor():
    im = new(fill=rgb('3a3448'))
    d = ImageDraw.Draw(im)
    d.line([(0, 15), (15, 15)], fill=rgb('2a2438'))
    d.point((5, 6), fill=rgb('4a4458'))
    return im


def dock():
    im = new(fill=P['wd1'])
    d = ImageDraw.Draw(im)
    for y in range(0, 16, 4):
        d.line([(0, y + 3), (15, y + 3)], fill=P['wd0'])
    return im


def hemicycle_bench():
    im = new(fill=P['cp0'])
    d = ImageDraw.Draw(im)
    d.rectangle([0, 3, 15, 8], fill=P['wd1'])
    d.line([(0, 8), (15, 8)], fill=K)
    d.rectangle([2, 10, 6, 14], fill=P['cp2'])
    d.rectangle([9, 10, 13, 14], fill=P['cp2'])
    return im


def tall_snow():
    im = new(fill=T.rgb('dfe8f4'))
    d = ImageDraw.Draw(im)
    for row, y0 in ((0, 1), (1, 9)):
        for k in range(4):
            x0 = k * 4 + (2 if row else 0)
            d.polygon([(x0, y0 + 7), (x0 + 2, y0 + 1), (x0 + 4, y0 + 7)], fill=T.rgb('b8c8dc'))
            d.line([(x0, y0 + 7), (x0 + 4, y0 + 7)], fill=T.rgb('98a8c0'))
    return im


def campidoglio():
    """Rome, Palazzo Senatorio on the Capitoline hill (Treaty of Rome, 1957)."""
    w, h = 8, 5
    im = new(w * 16, h * 16)
    d = ImageDraw.Draw(im)
    W, H = w * 16, h * 16
    cx = W // 2
    ochre, ochre_d, trav = rgb('e8c890'), rgb('c09860'), rgb('f2ead8')
    # bell tower
    d.rectangle([cx - 7, 2, cx + 7, 30], fill=ochre, outline=K)
    d.rectangle([cx - 4, 8, cx + 4, 16], fill=rgb('5a4a3a'))
    d.polygon([(cx - 9, 4), (cx, -2), (cx + 9, 4)], fill=ochre_d, outline=K)
    d.rectangle([cx - 9, 28, cx + 9, 31], fill=trav, outline=K)
    # main block with balustrade and statues
    d.rectangle([0, 30, W - 1, H - 1], fill=ochre, outline=K)
    d.rectangle([1, 30, W - 2, 34], fill=trav)
    for x in range(4, W - 2, 6):
        d.line([(x, 31), (x, 33)], fill=ochre_d)
    for x in (6, 30, W - 31, W - 7):
        d.rectangle([x - 1, 24, x + 1, 30], fill=trav, outline=K)
    # giant pilasters + windows
    for x in range(8, W - 6, 16):
        d.rectangle([x, 36, x + 2, H - 18], fill=trav)
    for x in range(14, W - 10, 16):
        d.rectangle([x, 40, x + 5, 50], fill=rgb('6a7898'), outline=K)
        d.polygon([(x - 1, 40), (x + 3, 36), (x + 7, 40)], fill=trav)
    # rusticated base + double staircase
    d.rectangle([1, H - 18, W - 2, H - 2], fill=ochre_d)
    for y in range(H - 16, H - 2, 4):
        d.line([(1, y), (W - 2, y)], fill=ochre)
    d.polygon([(cx - 30, H - 1), (cx - 10, H - 18), (cx - 4, H - 18), (cx - 22, H - 1)], fill=trav, outline=K)
    d.polygon([(cx + 30, H - 1), (cx + 10, H - 18), (cx + 4, H - 18), (cx + 22, H - 1)], fill=trav, outline=K)
    d.rectangle([cx - 5, H - 16, cx + 5, H - 1], fill=rgb('5a4a3a'), outline=K)
    label(im, 'CAMPIDOGLIO', cx, 54, 'rr0')
    return Obj(im, beh_grid(w, h), None, [])


def jeronimos():
    """Lisbon, Mosteiro dos Jeronimos (Treaty of Lisbon, 2007)."""
    w, h = 12, 5
    im = new(w * 16, h * 16)
    d = ImageDraw.Draw(im)
    W, H = w * 16, h * 16
    lime, lime_d, lime_l = rgb('ece4d0'), rgb('c4b898'), rgb('fbf6ea')
    # long cloister wing
    d.rectangle([0, 26, W - 1, H - 1], fill=lime, outline=K)
    d.line([(1, 27), (W - 2, 27)], fill=lime_l)
    for x in range(2, W - 2, 5):
        d.line([(x, 24), (x, 26)], fill=lime_d)  # pinnacles
        d.point((x, 23), fill=K)
    for x in range(8, W - 8, 12):
        if 56 < x < 92:
            continue
        d.rectangle([x, 36, x + 6, 54], fill=rgb('5a6a88'), outline=K)
        d.pieslice([x, 32, x + 6, 40], 180, 360, fill=rgb('5a6a88'), outline=K)
        d.rectangle([x - 2, 58, x + 8, H - 4], fill=lime_d)
        d.pieslice([x - 2, 54, x + 8, 64], 180, 360, fill=lime_d)
    # domed corner tower (right)
    tx = W - 26
    d.rectangle([tx, 6, tx + 20, 30], fill=lime, outline=K)
    d.pieslice([tx, -4, tx + 20, 16], 180, 360, fill=lime_d, outline=K)
    d.rectangle([tx + 7, 12, tx + 13, 24], fill=rgb('5a6a88'), outline=K)
    # ornate manueline portal
    px0 = 62
    d.rectangle([px0, 12, px0 + 28, H - 1], fill=lime_l, outline=K)
    d.polygon([(px0, 12), (px0 + 14, 0), (px0 + 28, 12)], fill=lime_l, outline=K)
    for y in range(16, H - 18, 5):
        d.line([(px0 + 3, y), (px0 + 25, y + 2)], fill=lime_d)
    for x in (px0 + 4, px0 + 24):
        d.line([(x, 14), (x, H - 2)], fill=lime_d)
    d.rectangle([px0 + 8, H - 18, px0 + 20, H - 1], fill=rgb('5a4a3a'), outline=K)
    d.pieslice([px0 + 8, H - 24, px0 + 20, H - 12], 180, 360, fill=rgb('5a4a3a'), outline=K)
    label(im, 'JERONIMOS', 30, 30, 'rr0')
    return Obj(im, beh_grid(w, h), None, [])


def bevel(im, min_run=6):
    """Soft relief on flat-coloured areas: warm light on the top/left edge of each panel,
    a cool shade on its bottom/right edge (only where the panel is wide enough to read)."""
    import numpy as np
    a = np.array(im).astype(int)
    rgb_, al = a[..., :3], a[..., 3]
    H, W = al.shape
    out = a.copy()
    same = lambda y0, x0, y1, x1: (rgb_[y0, x0] == rgb_[y1, x1]).all()
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            if al[y, x] < 255:
                continue
            c = rgb_[y, x]
            up = same(y, x, y - 1, x) and al[y - 1, x] == 255
            dn = same(y, x, y + 1, x) and al[y + 1, x] == 255
            lf = same(y, x, y, x - 1)
            rt = same(y, x, y, x + 1)
            # interior of a big enough flat panel?
            if not (up or dn) or not (lf or rt):
                continue
            row = rgb_[y, max(0, x - min_run):x + min_run]
            if (row == c).all(axis=1).sum() < min_run:
                continue
            L = (0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]) / 255
            if L < 0.18:
                continue
            if not up or not lf:
                out[y, x, :3] = np.clip(c + [18, 16, 4], 0, 255)
            elif not dn or not rt:
                out[y, x, :3] = np.clip(c + [-16, -12, 6], 0, 255)
    return Image.fromarray(out.astype('uint8'), 'RGBA')


def register():
    O = T.OBJECTS
    O['berlaymont'] = berlaymont()
    O['parlement_bxl'] = parlement_bxl()
    O['louise_weiss'] = louise_weiss()
    O['bce_tower'] = bce_tower()
    O['cjue'] = cjue()
    O['europa'] = europa_building()
    O['arena_blue'] = arena('eu')
    O['arena_red'] = arena('rr0')
    O['arena_gold'] = arena('gold')
    O['arena_green'] = arena('l1')
    O['arena_grey'] = arena('rg0')
    O['gare'] = gare()
    O['atomium'] = atomium()
    O['big_ben'] = big_ben()
    O['westminster'] = westminster()
    O['acropole'] = acropole()
    O['parliament_bud'] = parliament_bud()
    O['palac_kultury'] = palac_kultury()
    O['campidoglio'] = campidoglio()
    O['jeronimos'] = jeronimos()
    O['eiffel'] = eiffel()
    O['sorbonne'] = sorbonne()
    for c, n in (('c03030', 'red'), ('3060c0', 'blue'), ('30a050', 'green'), ('e0a020', 'yellow')):
        O['container_' + n] = container(c)
    O['golf_flag'] = golf_flag()
    O['long_table'] = long_table(10)
    O['podium'] = podium()
    O['cabinet'] = cabinet()
    O['server'] = server_rack()
    O['tractor'] = tractor()
    O['boat'] = boat()
    O['golf_cart'] = golf_cart()
    O['house_white'] = T.building(5, 4, 'rb', 'wl', door_x=2)
    O['house_brick'] = T.building(5, 4, 'rr', 'br', door_x=2)
    O['shop_cantine'] = O['cantine']
    for n in ('berlaymont', 'parlement_bxl', 'louise_weiss', 'bce_tower', 'cjue', 'europa', 'big_ben', 'westminster',
              'acropole', 'parliament_bud', 'palac_kultury', 'campidoglio', 'jeronimos', 'sorbonne', 'atomium'):
        O[n].img = bevel(O[n].img)
    TL = T.TILES
    TL['money'] = money_pile()
    TL['cobweb'] = Tile(cobweb(), B_WALK, above=True)
    TL['tracks'] = Tile(tracks_h(), B_SOLID)
    TL['red_carpet'] = Tile(red_carpet())
    TL['marble'] = Tile(marble_floor())
    TL['dark'] = Tile(dark_floor())
    TL['dark_enc'] = Tile(dark_floor(), T.B_CARPET)
    TL['dock'] = Tile(dock())
    TL['bench_row'] = Tile(hemicycle_bench(), B_SOLID)
    TL['golf'] = Tile(T.grass(77, deco=False))
    gr = T.grass(78, deco=False)
    ImageDraw.Draw(gr).rectangle([0, 0, 15, 15], fill=T.rgb('68c050'))
    TL['green'] = Tile(gr)
    snow = new(fill=T.rgb('eef2f8'))
    sd = ImageDraw.Draw(snow)
    for (x, y) in ((2, 3), (9, 1), (13, 7), (5, 11), (11, 13), (1, 14)):
        sd.point((x, y), fill=T.rgb('c8d4e8'))
        sd.point((x + 1, y), fill=T.rgb('dce4f0'))
    sd.point((7, 6), fill=T.rgb('ffffff'))
    TL['snow'] = Tile(snow)
    se = tall_snow()
    TL['snow_enc'] = Tile(se, B_GRASS)
