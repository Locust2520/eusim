#!/usr/bin/env python3
"""Procedural pixel-art tile library for EU Simulator (16x16 metatiles, Pokémon-DS-like look).

Registry:
  TILES[name]   = Tile(img 16x16 RGBA, beh)             ground / simple cells
  OBJECTS[name] = Obj(img (w*16,h*16) RGBA, beh grid, above grid, doors)
Behaviours (must match world.h):
"""
import math
import random

from PIL import Image, ImageDraw

B_WALK, B_SOLID, B_WATER, B_GRASS, B_LEDGE_D, B_DOOR, B_COUNTER, B_CARPET, B_WARP_EDGE, \
    B_LEDGE_L, B_LEDGE_R, B_STAIRS, B_PC, B_HEAL, B_SHOP = range(15)

TILES = {}
OBJECTS = {}
RAW = {}  # ungraded ground images, for tiles derived later (soft edges)


class Tile:
    def __init__(self, img, beh=B_WALK, above=False):
        self.img = img
        self.beh = beh
        self.above = above


class Obj:
    def __init__(self, img, beh, above=None, doors=(), oy=0):
        self.img = img
        self.w = img.width // 16
        self.oy = oy              # extra rows drawn above the anchor cell (over actors), e.g. tree crowns
        self.h = img.height // 16 - oy
        self.beh = beh            # list of rows (strings) of behaviour chars
        self.above = above        # list of rows: '1' = drawn above actors
        self.doors = list(doors)  # (cx, cy) cells relative to object


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


# ---------------------------------------------------------------- palette
# Soft, hue-shifted ramps in the spirit of the Gen 4/5 games: shadows lean towards blue/teal,
# lights towards a warm yellow, and outlines are a dark navy rather than black.
P = {
    # grass
    'gd': rgb('3f8a72'), 'g0': rgb('58b090'), 'g1': rgb('70d0a8'), 'g2': rgb('8ce0b4'), 'g3': rgb('c4f0b0'),
    # tall dossier grass
    't0': rgb('287058'), 't1': rgb('348a64'), 't2': rgb('4ca86c'), 't3': rgb('84cc70'),
    'pw': rgb('fcf8ec'), 'pg': rgb('b8bcd0'),
    # dirt path
    'd0': rgb('dcc08c'), 'd1': rgb('e8d498'), 'd2': rgb('f6e8b8'), 'd3': rgb('c0ac90'),
    # pavement (Brussels grey cobbles)
    'c0': rgb('d0d0c8'), 'c1': rgb('dcdad0'), 'c2': rgb('ecead8'), 'c3': rgb('bcbec4'),
    # asphalt
    'a0': rgb('8890a4'), 'a1': rgb('949cae'), 'ay': rgb('f4d460'), 'aw': rgb('ecebe4'),
    # water (animated colours w0..w3 are palette-cycled)
    'w0': rgb('4898e0'), 'w1': rgb('58b0f0'), 'w2': rgb('80c8f8'), 'w3': rgb('c8ecff'), 'wd': rgb('3878c0'),
    # sand
    's0': rgb('f0e4b0'), 's1': rgb('f8f0c4'), 's2': rgb('dcc8a0'),
    # tree
    'l0': rgb('234a4e'), 'l1': rgb('2e7050'), 'l2': rgb('46944c'), 'l3': rgb('72b852'), 'l4': rgb('b4dc6c'),
    'tk': rgb('9a6844'), 'tk2': rgb('634048'),
    # outlines / shadows
    'k': rgb('304048'), 'sh': (40, 56, 110, 80),
    # flowers
    'fr': rgb('e84858'), 'fy': rgb('f8d44c'), 'fw': rgb('fffcf0'), 'fb': rgb('7090f0'), 'fp': rgb('f088c0'),
    # walls/roofs (3 = warm highlight)
    'rr0': rgb('a85868'), 'rr1': rgb('d87078'), 'rr2': rgb('e88890'), 'rr3': rgb('f8b8a8'),
    'rb0': rgb('405890'), 'rb1': rgb('5878c0'), 'rb2': rgb('78a0e0'), 'rb3': rgb('b0d0f8'),
    'rg0': rgb('586880'), 'rg1': rgb('7888a0'), 'rg2': rgb('98a8c0'), 'rg3': rgb('c8d4e0'),
    'wl0': rgb('ece4d2'), 'wl1': rgb('fcf8e6'), 'wl2': rgb('c4bcbc'), 'wl3': rgb('a09cb0'),
    'br0': rgb('b06a4c'), 'br1': rgb('cc845c'), 'br2': rgb('884650'),
    'gl0': rgb('50a8e8'), 'gl1': rgb('88d0f8'), 'gl2': rgb('d8f4ff'), 'gl3': rgb('3878b8'),
    'wd0': rgb('8a5838'), 'wd1': rgb('b07848'), 'wd2': rgb('d4a46c'), 'wd3': rgb('ecd09a'),
    'eu': rgb('17389a'), 'eu2': rgb('2852b8'), 'gold': rgb('ffd040'),
    'mt0': rgb('8090a8'), 'mt1': rgb('a8b4cc'), 'mt2': rgb('d4dcea'),
    'wh': rgb('fffcf2'), 'bk': rgb('1c2034'), 'gr': rgb('848aa0'),
    # interiors
    'fl0': rgb('c8945c'), 'fl1': rgb('dcb078'), 'fl2': rgb('a47658'), 'fl3': rgb('eccc94'),
    'cp0': rgb('2c4aa0'), 'cp1': rgb('3c5cb8'), 'cp2': rgb('22357e'),
    'cr0': rgb('a03048'), 'cr1': rgb('c04a54'),
    'ti0': rgb('ecebe6'), 'ti1': rgb('cccdda'),
    'iw0': rgb('f0e8d6'), 'iw1': rgb('d8d0cc'), 'iw2': rgb('b2aab6'),
}
TRANSP = (0, 0, 0, 0)


def new(w=16, h=16, fill=TRANSP):
    return Image.new('RGBA', (w, h), fill)


def art(rows, legend, base=None):
    """ASCII art -> image. legend maps char -> palette key or RGBA; '.' transparent."""
    h = len(rows)
    w = max(len(r) for r in rows)
    im = base.copy() if base else new(w, h)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch in legend:
                c = legend[ch]
                c = P[c] if isinstance(c, str) else c
                if c[3] == 255:
                    im.putpixel((x, y), c)
                elif c[3] > 0:
                    under = im.getpixel((x, y))
                    a = c[3] / 255
                    mix = tuple(int(under[i] * (1 - a) + c[i] * a) for i in range(3)) + (255,)
                    im.putpixel((x, y), mix)
    return im


def noise_fill(im, keys, weights, seed, box=None):
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box or (0, 0, im.width, im.height)
    for y in range(y0, y1):
        for x in range(x0, x1):
            im.putpixel((x, y), P[rnd.choices(keys, weights)[0]])
    return im


def paste(dst, src, x, y):
    dst.alpha_composite(src, (x, y))
    return dst


# ---------------------------------------------------------------- ground
def _tuft(im, x, y, light='g3', dark='g0'):
    """Little two-blade grass tuft, lit from the top-left."""
    for (dx, dy, c) in ((0, 0, light), (2, 0, light), (0, 1, dark), (1, 1, dark), (2, 1, dark), (3, 0, dark)):
        if 0 <= x + dx < 16 and 0 <= y + dy < 16:
            im.putpixel((x + dx, y + dy), P[c])


def grass(seed=1, deco=True, kind=None):
    """kind: None/'plain', 'tuft', 'tufts', 'blossom' (tiny white/yellow flowers), 'clover'."""
    im = new(fill=P['g1'])
    rnd = random.Random(seed * 31 + 7)
    # soft mottling: a few lighter specks
    for _ in range(4):
        x, y = rnd.randrange(16), rnd.randrange(16)
        im.putpixel((x, y), P['g2'])
        im.putpixel(((x + 1) % 16, y), P['g2'])
    kind = kind or ('tuft' if deco else 'plain')
    if kind in ('tuft', 'tufts'):
        _tuft(im, rnd.randrange(1, 11), rnd.randrange(2, 13))
    if kind == 'tufts':
        _tuft(im, rnd.randrange(1, 11), rnd.randrange(2, 13))
    if kind == 'blossom':
        for (x, y, c) in ((3, 4, 'fw'), (11, 9, 'fy'), (6, 12, 'fw')):
            im.putpixel((x, y), P[c])
            im.putpixel((x, y + 1), P['g0'])
    if kind == 'clover':
        for (x, y) in ((4, 5), (10, 11)):
            for (dx, dy) in ((0, 0), (1, 0), (0, 1), (-1, 1), (1, 1)):
                im.putpixel((x + dx, y + dy), P['g2'] if dy == 0 else P['g0'])
            im.putpixel((x, y), P['g3'])
    return im


def flowers(c1='fr', c2='fy', seed=3):
    import oss_art
    k = {'fr': 3, 'fy': 2, 'fp': 0, 'fb': 1}.get(c1, 3)
    im = grass(seed, deco=False)
    im.alpha_composite(oss_art.flower(k))
    return im


def tall_dossiers(seed=5):
    """Tall grass with sheets of paper sticking out: wild Euromons hide here."""
    im = new(fill=P['t1'])
    blade = art(['..a...a.',
                 '.aba.aba',
                 'abbbaabb',
                 'bbcbbbcb',
                 'bcccbccc',
                 'cccdcccd',
                 'ccdddcdd',
                 'dddddddd'], {'a': 't3', 'b': 't2', 'c': 't1', 'd': 't0'})
    for (x, y) in ((0, 0), (8, 0), (4, 8), (-4, 8), (12, 8)):
        paste(im, blade, x, y)
    # a sheet of paper peeking out between the blades
    sheet = art(['www', 'wgw', 'www'], {'w': 'pw', 'g': 'pg'})
    paste(im, sheet, 10 if seed % 2 else 2, 4)
    return im


def path_tile(seed=7):
    im = new(fill=P['d1'])
    rnd = random.Random(seed)
    for _ in range(7):
        x, y = rnd.randrange(16), rnd.randrange(16)
        im.putpixel((x, y), P['d2'])
        im.putpixel(((x + 1) % 16, y), P['d2'])
    for _ in range(4):
        x, y = rnd.randrange(16), rnd.randrange(16)
        im.putpixel((x, y), P['d0'])
    for (x, y) in ((4, 10), (11, 4), (13, 13)):  # pebbles, lit from the top-left
        im.putpixel((x, y), P['d3'])
        im.putpixel((x + 1, y), P['d3'])
        im.putpixel((x, y - 1), P['wh'])
        im.putpixel((x + 1, y - 1), P['d2'])
    return im


def soft_edge(base, mask, seed=0, rim='d0', fill=None):
    """Grass creeping over the edges of a path/sand tile. mask: set of 'n','s','e','w' (grass on that side),
    plus 'NE','NW','SE','SW' for inner corners."""
    im = base.copy()
    g = fill or grass(seed + 60, deco=False)
    rnd = random.Random(seed)
    wav = [2, 3, 3, 2, 2, 3, 2, 2, 3, 3, 2, 2, 3, 2, 3, 2]

    def put(x, y, c):
        if 0 <= x < 16 and 0 <= y < 16:
            im.putpixel((x, y), c)

    for i in range(16):
        d = wav[(i + seed) % 16]
        for side in mask:
            if side not in ('n', 's', 'e', 'w'):
                continue
            for k in range(d):
                x, y = {'n': (i, k), 's': (i, 15 - k), 'w': (k, i), 'e': (15 - k, i)}[side]
                put(x, y, g.getpixel((x, y)))
            # darker rim of earth under the grass, bright grass lip
            x, y = {'n': (i, d), 's': (i, 15 - d), 'w': (d, i), 'e': (15 - d, i)}[side]
            put(x, y, P[rim])
            x, y = {'n': (i, d - 1), 's': (i, 16 - d), 'w': (d - 1, i), 'e': (16 - d, i)}[side]
            put(x, y, P['g2'] if side in ('n', 'w') else P['g0'])
    for c in mask:
        if c in ('NE', 'NW', 'SE', 'SW'):
            cx = 15 if 'E' in c else 0
            cy = 0 if 'N' in c else 15
            for y in range(16):
                for x in range(16):
                    if abs(x - cx) + abs(y - cy) < 3:
                        put(x, y, g.getpixel((x, y)))
                    elif abs(x - cx) + abs(y - cy) == 3:
                        put(x, y, P[rim])
    return im


def cobbles(seed=11):
    """Rounded paving stones, lit from the top-left, joints in a cool grey."""
    im = new(fill=P['c3'])
    for row in range(4):
        off = 2 if row % 2 else 0
        for col in range(-1, 4):
            x0, y0 = col * 4 + off, row * 4
            for y in range(3):
                for x in range(3):
                    X, Y = x0 + x, y0 + y
                    if not (0 <= X < 16):
                        continue
                    c = 'c1'
                    if (x, y) == (0, 0):
                        c = 'c2'
                    elif x == 2 and y == 2:
                        c = 'c0'
                    elif (x == 2 or y == 2) and (x + y) > 2:
                        c = 'c0'
                    im.putpixel((X, Y), P[c])
    rnd = random.Random(seed)
    for _ in range(3):
        x, y = rnd.randrange(16), rnd.randrange(16)
        if im.getpixel((x, y))[:3] == P['c1'][:3]:
            im.putpixel((x, y), P['c0'])
    return im


def asphalt(lines=None):
    im = new(fill=P['a1'])
    rnd = random.Random(13)
    for _ in range(14):
        im.putpixel((rnd.randrange(16), rnd.randrange(16)), P['a0'])
    for _ in range(4):
        im.putpixel((rnd.randrange(16), rnd.randrange(16)), P['c0'])
    d = ImageDraw.Draw(im)
    if lines == 'h':
        d.rectangle([2, 7, 9, 8], fill=P['aw'])
    if lines == 'v':
        d.rectangle([7, 2, 8, 9], fill=P['aw'])
    if lines == 'zebra':
        for x in range(0, 16, 4):
            d.rectangle([x, 0, x + 1, 15], fill=P['aw'])
    return im


def sand(seed=17):
    im = new(fill=P['s1'])
    rnd = random.Random(seed)
    for _ in range(10):
        im.putpixel((rnd.randrange(16), rnd.randrange(16)), P['s0'])
    for _ in range(3):
        x, y = rnd.randrange(15), rnd.randrange(1, 16)
        im.putpixel((x, y), P['s2'])
        im.putpixel((x + 1, y - 1), P['fw'])
    return im


def water(frame=0):
    """Water uses w0..w3, palette-cycled in game: soft wave arcs and a few glints."""
    im = new(fill=P['w1'])
    for (x0, y0) in ((1, 2), (9, 6), (3, 10), (11, 13)):
        for k, c in enumerate(('w2', 'w2', 'w2', 'w3', 'w2')):
            im.putpixel(((x0 + k) % 16, y0 - (1 if 0 < k < 4 else 0)), P[c])
        im.putpixel(((x0 + 1) % 16, (y0 + 1) % 16), P['w0'])
        im.putpixel(((x0 + 2) % 16, (y0 + 1) % 16), P['w0'])
        im.putpixel(((x0 + 3) % 16, (y0 + 1) % 16), P['w0'])
    return im


def shore(side):
    """Water with a grass bank and a sandy lip on one or more sides: side in 'n','s','e','w','ne',..."""
    im = water()
    g = grass(23, deco=False)

    def bank(coords_fn):
        for i in range(16):
            for k in range(6):
                x, y = coords_fn(i, k)
                if k < 3:
                    c = g.getpixel((x, y))
                elif k == 3:
                    c = P['g0']
                elif k == 4:
                    c = P['s1']
                else:
                    c = P['w3'] if i % 5 < 3 else P['wd']
                im.putpixel((x, y), c)
    if 'n' in side:
        bank(lambda i, k: (i, k))
    if 's' in side:
        bank(lambda i, k: (i, 15 - k))
    if 'w' in side:
        bank(lambda i, k: (k, i))
    if 'e' in side:
        bank(lambda i, k: (15 - k, i))
    return im


def ledge():
    im = grass(21, deco=False)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 9, 15, 9], fill=P['g2'])
    d.rectangle([0, 10, 15, 12], fill=P['g0'])
    d.rectangle([0, 13, 15, 13], fill=P['gd'])
    for x in range(0, 16, 4):
        d.line([(x + 1, 10), (x + 2, 11)], fill=P['gd'])
    return im


def edge_curb(side):
    """Pavement with a grass border."""
    im = cobbles()
    g = grass(29, deco=False)
    d = ImageDraw.Draw(im)
    if side == 'n':
        im.paste(g.crop((0, 0, 16, 3)), (0, 0))
        d.line([(0, 3), (15, 3)], fill=P['c2'])
        d.line([(0, 4), (15, 4)], fill=P['c3'])
    if side == 's':
        im.paste(g.crop((0, 13, 16, 16)), (0, 13))
        d.line([(0, 12), (15, 12)], fill=P['c3'])
    return im


# ---------------------------------------------------------------- objects
def tree_round(seed=0):
    """Deciduous tree, 2 cells wide: crown overhangs the cell above (see Obj.oy). Art: Tuxemon (CC BY-SA)."""
    import oss_art
    return oss_art.tree(('round', 'round2', 'round')[seed % 3])


def tree_pine(seed=0):
    import oss_art
    return oss_art.tree(('pine', 'pine2', 'pine_dark')[seed % 3])


def hedge():
    import oss_art
    im = new()
    b = oss_art.bush()
    im.alpha_composite(b)
    return im


def fence_h():
    """White picket fence, shaded in cool blue-grey."""
    im = new()
    d = ImageDraw.Draw(im)
    d.rectangle([0, 6, 15, 7], fill=P['wl1'])
    d.line([(0, 8), (15, 8)], fill=P['wl3'])
    d.rectangle([0, 11, 15, 11], fill=P['wl1'])
    d.line([(0, 12), (15, 12)], fill=P['wl3'])
    for x in (2, 10):
        d.rectangle([x - 1, 3, x + 2, 15], fill=P['k'])
        d.rectangle([x, 3, x + 1, 14], fill=P['wl1'])
        d.line([(x + 1, 4), (x + 1, 14)], fill=P['wl2'])
        im.putpixel((x - 1, 3), TRANSP)
        im.putpixel((x + 2, 3), TRANSP)
    return im


def lamp():
    im = new(16, 32)
    d = ImageDraw.Draw(im)
    d.rectangle([7, 6, 8, 29], fill=P['k'])
    d.rectangle([5, 29, 10, 31], fill=P['k'])
    d.rectangle([4, 2, 11, 6], fill=P['k'])
    d.rectangle([5, 3, 10, 5], fill=P['gold'])
    d.line([(6, 3), (9, 3)], fill=P['fw'])
    return im


def bench():
    im = new(32, 16)
    d = ImageDraw.Draw(im)
    d.rectangle([2, 3, 29, 5], fill=P['wd1'])
    d.rectangle([2, 7, 29, 10], fill=P['wd2'])
    d.line([(2, 10), (29, 10)], fill=P['wd0'])
    for x in (4, 26):
        d.rectangle([x, 10, x + 1, 14], fill=P['k'])
    return im


def sign_post(color='wood'):
    im = new()
    d = ImageDraw.Draw(im)
    if color == 'wood':
        d.rectangle([7, 9, 8, 15], fill=P['wd0'])
        d.rectangle([1, 2, 14, 10], fill=P['wd0'])
        d.rectangle([2, 3, 13, 9], fill=P['wd2'])
        d.line([(3, 5), (12, 5)], fill=P['wd0'])
        d.line([(3, 7), (10, 7)], fill=P['wd0'])
    else:
        d.rectangle([7, 9, 8, 15], fill=P['mt0'])
        d.rectangle([1, 2, 14, 10], fill=P['eu'])
        d.rectangle([2, 3, 13, 9], fill=P['eu2'])
        for k in range(6):
            a = k * math.pi / 3
            im.putpixel((int(7.5 + 3 * math.cos(a)), int(6 + 2.5 * math.sin(a))), P['gold'])
    return im


def flagpole():
    im = new(16, 32)
    d = ImageDraw.Draw(im)
    d.rectangle([3, 1, 3, 30], fill=P['mt1'])
    d.rectangle([2, 30, 5, 31], fill=P['mt0'])
    d.rectangle([4, 2, 15, 10], fill=P['eu'])
    for k in range(12):
        a = k * math.pi / 6
        im.putpixel((int(9.5 + 3.4 * math.cos(a)), int(6 + 3 * math.sin(a))), P['gold'])
    return im


def mailbox():
    im = new()
    d = ImageDraw.Draw(im)
    d.rectangle([7, 8, 8, 15], fill=P['k'])
    d.rectangle([3, 3, 12, 9], fill=P['fr'])
    d.rectangle([4, 4, 11, 5], fill=P['rr2'])
    return im


def rock():
    import oss_art
    return oss_art.rock(1)


def statue():
    """Robert Schuman statue-ish bust on a plinth (16x32)."""
    im = new(16, 32)
    d = ImageDraw.Draw(im)
    d.rectangle([2, 18, 13, 31], fill=P['c3'])
    d.rectangle([3, 18, 12, 29], fill=P['c1'])
    d.rectangle([4, 10, 11, 18], fill=P['c0'])
    d.ellipse([5, 3, 10, 10], fill=P['c1'])
    d.line([(4, 22), (11, 22)], fill=P['c3'])
    return im


# ---------------------------------------------------------------- buildings
def _window(d, x, y, w=9, h=10, glass=('gl1', 'gl2', 'gl0')):
    """Framed window with a cool glass gradient and a diagonal glint, sill below."""
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=P['k'])
    d.rectangle([x + 1, y + 1, x + w - 2, y + h - 2], fill=P[glass[0]])
    d.rectangle([x + 1, y + h // 2, x + w - 2, y + h - 2], fill=P[glass[2]])
    d.line([(x + 2, y + 3), (x + 4, y + 1)], fill=P[glass[1]])
    d.line([(x + 2, y + 5), (x + 6, y + 1)], fill=P[glass[1]])
    d.line([(x + w // 2, y + 1), (x + w // 2, y + h - 2)], fill=P['wl1'])
    d.line([(x - 1, y + h), (x + w, y + h)], fill=P['wl1'])
    d.line([(x - 1, y + h + 1), (x + w, y + h + 1)], fill=P['wl3'])


def building(w, h, roof='rr', wall='wl', door_x=None, windows='normal', label=None, label_col=None, glass=False,
             door_gap=12):
    """Generic Gen-4-style building: shingled roof on top rows, facade bottom 2 rows. w,h in cells."""
    W, H = w * 16, h * 16
    im = new(W, H)
    d = ImageDraw.Draw(im)
    roof_h = (h - 2) * 16 + 4
    r0, r1, r2 = P[roof + '0'], P[roof + '1'], P[roof + '2']
    r3 = P.get(roof + '3', r2)
    # roof: rows of shingles, lighter towards the ridge, a warm highlight on the ridge itself
    d.rectangle([0, 0, W - 1, roof_h], fill=r1)
    for y in range(4, roof_h - 3, 4):
        band = r2 if y < roof_h * 0.45 else r1
        d.rectangle([1, y - 3, W - 2, y - 1], fill=band)
        d.line([(1, y), (W - 2, y)], fill=r0)
        off = 0 if (y // 4) % 2 else 3
        for x in range(1 + off, W - 1, 6):
            d.point((x, y - 1), fill=r0)
            d.point((x + 1, y - 3), fill=r3 if band == r2 else r2)
    d.rectangle([1, 1, W - 2, 2], fill=r3)
    d.line([(1, 3), (W - 2, 3)], fill=r2)
    # eave: dark underside, roof slightly wider than the wall
    d.rectangle([0, roof_h - 3, W - 1, roof_h - 1], fill=r0)
    d.line([(0, roof_h - 3), (W - 1, roof_h - 3)], fill=r1)
    d.line([(0, roof_h), (W - 1, roof_h)], fill=P['k'])
    d.line([(0, 0), (0, roof_h)], fill=P['k'])
    d.line([(W - 1, 0), (W - 1, roof_h)], fill=P['k'])
    d.line([(0, 0), (W - 1, 0)], fill=P['k'])
    # facade
    fy = roof_h + 1
    if glass:
        d.rectangle([1, fy, W - 2, H - 1], fill=P['gl0'])
        for y in range(fy + 1, H - 2, 5):
            d.line([(1, y), (W - 2, y)], fill=P['gl1'])
            d.line([(1, y + 1), (W - 2, y + 1)], fill=P['gl2'] if y == fy + 1 else P['gl1'])
        for x in range(4, W - 2, 8):
            d.line([(x, fy + 1), (x, H - 3)], fill=P['gl3'])
        d.rectangle([1, fy, W - 2, fy + 1], fill=P['gl3'])
    else:
        w0, w1, w2 = P[wall + '0'], P[wall + '1'], P[wall + '2']
        w3 = P.get(wall + '3', w2)
        d.rectangle([1, fy, W - 2, H - 1], fill=w0)
        # cool shadow under the eave, warm light lower on the wall
        d.rectangle([1, fy, W - 2, fy + 2], fill=w3)
        d.line([(1, fy + 3), (W - 2, fy + 3)], fill=w2)
        d.line([(1, fy + 9), (W - 2, fy + 9)], fill=w1)
        d.rectangle([1, H - 3, W - 2, H - 1], fill=w2)
        d.line([(1, H - 3), (W - 2, H - 3)], fill=w3)
        if wall == 'br':
            for y in range(fy + 4, H - 3, 3):
                for x in range(1 + (y % 2) * 3, W - 2, 6):
                    d.point((x, y), fill=P['br2'])
        if windows == 'normal':
            for x in range(6, W - 8, 16):
                if door_x is not None and abs(x + 4 - (door_x * 16 + 8)) < door_gap:
                    continue
                _window(d, x, fy + 5)
    d.line([(0, fy), (0, H - 1)], fill=P['k'])
    d.line([(W - 1, fy), (W - 1, H - 1)], fill=P['k'])
    doors = []
    if door_x is not None:
        x = door_x * 16
        d.rectangle([x + 1, H - 16, x + 14, H - 1], fill=P['k'])
        d.rectangle([x + 2, H - 15, x + 13, H - 2], fill=P['wl1'] if not glass else P['mt2'])
        d.rectangle([x + 3, H - 14, x + 12, H - 2], fill=P['gl1'] if glass else P['wd1'])
        if glass:
            d.line([(x + 4, H - 12), (x + 6, H - 14)], fill=P['gl2'])
            d.line([(x + 7, H - 14), (x + 7, H - 2)], fill=P['mt1'])
        else:
            d.rectangle([x + 4, H - 13, x + 6, H - 9], fill=P['wd0'])
            d.rectangle([x + 9, H - 13, x + 11, H - 9], fill=P['wd0'])
            d.line([(x + 3, H - 14), (x + 12, H - 14)], fill=P['wd2'])
            d.point((x + 10, H - 7), fill=P['gold'])
        d.line([(x + 1, H - 1), (x + 14, H - 1)], fill=P['c1'])
        doors.append((door_x, h - 1))
    if label:
        lw = sign_width(label)
        lx = (W - lw) // 2
        ly = roof_h - 10
        d.rectangle([lx, ly, lx + lw, ly + 8], fill=P['k'])
        d.rectangle([lx + 1, ly + 1, lx + lw - 1, ly + 7], fill=P[label_col or 'eu'])
        _tiny_text(im, lx + 3, ly + 2, label, P['wh'])
    beh = ['#' * w for _ in range(h)]
    if door_x is not None:
        r = list(beh[h - 1])
        r[door_x] = 'D'
        beh[h - 1] = ''.join(r)
    return Obj(im, beh, None, doors)


# 3x5 tiny font for signs on buildings
_TINY = {
    'A': '010101111101101', 'B': '110101110101110', 'C': '011100100100011', 'D': '110101101101110',
    'E': '111100110100111', 'F': '111100110100100', 'G': '011100101101011', 'H': '101101111101101',
    'I': '111010010010111', 'J': '001001001101010', 'K': '101101110101101', 'L': '100100100100111',
    'M': '101111111101101', 'N': '110101101101101', 'O': '010101101101010', 'P': '110101110100100',
    'Q': '010101101110011', 'R': '110101110101101', 'S': '011100010001110', 'T': '111010010010010',
    'U': '101101101101111', 'V': '101101101101010', 'W': '101101111111101', 'X': '101101010101101',
    'Y': '101101010010010', 'Z': '111001010100111', ' ': '000000000000000', '-': '000000111000000',
    'É': '010111110100111', '€': '011100111100011', '.': '000000000000010', "'": '010010000000000',
}


# Generic signs are pictograms, so the town reads the same in every language (proper names stay text).
_PICTO = {
    'CANTINE': ['.1.1...', '11111..', '1111111', '11111.1', '.111...'],     # steaming cup
    'BOUTIQUE': ['..111..', '.1...1.', '1111111', '1111111', '1111111'],    # shopping bag
    'ARENE': ['1.111.1', '1111111', '.11111.', '..111..', '.11111.'],       # trophy
    'GARE': ['.11111.', '1.....1', '1111111', '1.111.1', '.1...1.'],        # train
}


def sign_width(text):
    return 12 if text.upper() in _PICTO else len(text) * 4 + 6


def _tiny_text(im, x, y, text, col):
    pic = _PICTO.get(text.upper())
    if pic:
        for r, row in enumerate(pic):
            for k, b in enumerate(row):
                if b == '1':
                    im.putpixel((x + k, y + r), col)
        return
    for ch in text.upper():
        g = _TINY.get(ch, _TINY[' '])
        for k, b in enumerate(g):
            if b == '1':
                im.putpixel((x + k % 3, y + k // 3 - 1 if False else y + k // 3), col)
        x += 4


# ---------------------------------------------------------------- interiors
def floor_wood():
    """Warm parquet: planks lit on their top edge, cool joints."""
    im = new(fill=P['fl1'])
    d = ImageDraw.Draw(im)
    for y in range(0, 16, 4):
        d.line([(0, y), (15, y)], fill=P['fl3'])
        d.line([(0, y + 3), (15, y + 3)], fill=P['fl2'])
        off = 0 if (y // 4) % 2 else 8
        d.line([(off, y), (off, y + 3)], fill=P['fl2'])
        d.point(((off + 4) % 16, y + 2), fill=P['fl0'])
        d.point(((off + 11) % 16, y + 1), fill=P['fl0'])
    return im


def floor_tiles():
    im = new(fill=P['ti0'])
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 7, 7], fill=P['ti1'])
    d.rectangle([8, 8, 15, 15], fill=P['ti1'])
    for (x, y) in ((0, 0), (8, 0), (0, 8), (8, 8)):
        d.line([(x, y + 7), (x + 7, y + 7)], fill=P['iw2'])
        d.point((x + 1, y + 1), fill=P['wh'])
    return im


def carpet(c='cp'):
    """Soft carpet: a fine woven texture and a small repeating motif."""
    im = new(fill=P[c + '0'])
    for y in range(16):
        for x in range(16):
            if (x + 2 * y) % 5 == 0:
                im.putpixel((x, y), P[c + '1'])
    d = ImageDraw.Draw(im)
    for (x, y) in ((3, 3), (11, 11)):
        d.point((x, y - 1), fill=P[c + '1'])
        d.point((x - 1, y), fill=P[c + '1'])
        d.point((x + 1, y), fill=P[c + '1'])
        d.point((x, y + 1), fill=P[c + '1'])
        d.point((x, y), fill=P['gold'] if c == 'cp' else P[c + '1'])
    return im


def wall_interior(top=False):
    im = new(fill=P['iw0'])
    d = ImageDraw.Draw(im)
    if top:
        d.rectangle([0, 0, 15, 15], fill=P['iw1'])
        d.line([(0, 14), (15, 14)], fill=P['iw0'])
        d.line([(0, 15), (15, 15)], fill=P['iw2'])
    else:
        # light upper wall with a cool shadow line, wooden wainscot below
        d.line([(0, 0), (15, 0)], fill=P['iw2'])
        d.line([(0, 1), (15, 1)], fill=P['iw1'])
        d.rectangle([0, 9, 15, 15], fill=P['wd1'])
        d.line([(0, 9), (15, 9)], fill=P['wd3'])
        d.line([(0, 10), (15, 10)], fill=P['wd2'])
        for x in (0, 8):
            d.rectangle([x + 1, 11, x + 6, 14], fill=P['wd2'])
            d.line([(x + 1, 14), (x + 6, 14)], fill=P['wd0'])
            d.line([(x + 6, 11), (x + 6, 14)], fill=P['wd0'])
        d.line([(0, 15), (15, 15)], fill=P['wd0'])
    return im


def window_interior():
    im = wall_interior()
    d = ImageDraw.Draw(im)
    d.rectangle([2, 1, 13, 9], fill=P['k'])
    d.rectangle([3, 2, 12, 8], fill=P['gl1'])
    d.line([(7, 2), (7, 8)], fill=P['wh'])
    d.point((4, 3), fill=P['gl2'])
    return im


def desk():
    im = new(32, 16)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 3, 31, 12], fill=P['k'])
    d.rectangle([1, 4, 30, 8], fill=P['wd2'])
    d.line([(1, 4), (30, 4)], fill=P['wd3'])
    d.rectangle([1, 9, 30, 11], fill=P['wd0'])
    d.rectangle([1, 12, 4, 15], fill=P['k'])
    d.rectangle([2, 12, 3, 14], fill=P['wd0'])
    d.rectangle([27, 12, 30, 15], fill=P['k'])
    d.rectangle([28, 12, 29, 14], fill=P['wd0'])
    # papers + computer
    d.rectangle([4, 4, 10, 7], fill=P['pw'])
    d.line([(5, 5), (9, 5)], fill=P['pg'])
    d.rectangle([17, 0, 27, 7], fill=P['k'])
    d.rectangle([18, 1, 26, 5], fill=P['gl0'])
    d.line([(19, 2), (21, 2)], fill=P['gl2'])
    d.rectangle([21, 7, 23, 8], fill=P['mt0'])
    return im


def counter():
    im = new()
    d = ImageDraw.Draw(im)
    d.rectangle([0, 3, 15, 15], fill=P['wd0'])
    d.rectangle([0, 3, 15, 7], fill=P['wd2'])
    d.line([(0, 8), (15, 8)], fill=P['k'])
    return im


def bookshelf():
    im = new(16, 32)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 15, 31], fill=P['wd0'])
    d.rectangle([1, 1, 14, 30], fill=P['wd1'])
    rnd = random.Random(4)
    for sy in (2, 10, 18):
        d.line([(1, sy + 7), (14, sy + 7)], fill=P['wd0'])
        x = 2
        while x < 13:
            w = rnd.choice([1, 2])
            col = rnd.choice(['fr', 'fb', 'fy', 'l2', 'eu', 'wh', 'rr0'])
            d.rectangle([x, sy + 1, x + w - 1, sy + 6], fill=P[col])
            x += w + 1
    return im


def plant():
    im = new(16, 32)
    d = ImageDraw.Draw(im)
    d.rectangle([4, 22, 11, 30], fill=P['br1'])
    d.rectangle([4, 22, 11, 23], fill=P['br2'])
    for (cx, cy, r) in ((8, 14, 6), (5, 10, 4), (11, 9, 4), (8, 6, 4)):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=P['l1'])
        d.ellipse([cx - r + 1, cy - r + 1, cx, cy], fill=P['l2'])
    return im


def jukebox():
    """Retro jukebox for the player's studio (music room bonus)."""
    im = new(16, 32)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 2, 15, 31], radius=6, fill=P['k'])
    d.rounded_rectangle([1, 3, 14, 30], radius=5, fill=P['wd1'])
    d.rounded_rectangle([3, 5, 12, 14], radius=4, fill=P['gl2'])    # glass dome
    d.arc([3, 5, 12, 14], 180, 360, fill=P['fy'])
    for i, col in enumerate(('fr', 'fy', 'l2', 'fb', 'fp')):         # bubble lights
        d.point((2 + i * 3 if i < 5 else 13, 16), fill=P[col])
    d.rectangle([2, 15, 13, 17], outline=P['gold'])
    d.rectangle([3, 19, 12, 27], fill=P['wd0'])                      # speaker grille
    for y in range(20, 27, 2):
        d.line([(4, y), (11, y)], fill=P['br2'])
    d.line([(1, 29), (14, 29)], fill=P['gold'])
    return im


def pc_terminal():
    """'Archives' terminal (Pokémon PC)."""
    im = new(16, 32)
    d = ImageDraw.Draw(im)
    d.rectangle([1, 10, 14, 31], fill=P['mt0'])
    d.rectangle([2, 11, 13, 30], fill=P['mt1'])
    d.rectangle([2, 0, 13, 11], fill=P['k'])
    d.rectangle([3, 1, 12, 9], fill=P['eu'])
    for k in range(6):
        a = k * math.pi / 3
        im.putpixel((int(7.5 + 3 * math.cos(a)), int(5 + 2.6 * math.sin(a))), P['gold'])
    d.rectangle([4, 14, 11, 16], fill=P['k'])
    return im


def doormat():
    im = floor_wood()
    d = ImageDraw.Draw(im)
    d.rectangle([1, 4, 14, 13], fill=P['cr0'])
    d.rectangle([2, 5, 13, 12], fill=P['cr1'])
    return im


def stairs():
    im = new(fill=P['iw2'])
    d = ImageDraw.Draw(im)
    for y in range(0, 16, 4):
        d.rectangle([0, y, 15, y + 2], fill=P['fl1'])
        d.line([(0, y + 3), (15, y + 3)], fill=P['fl2'])
    return im


def sofa():
    im = new(32, 16)
    d = ImageDraw.Draw(im)
    d.rectangle([1, 1, 30, 9], fill=P['rr0'])
    d.rectangle([0, 6, 31, 14], fill=P['rr1'])
    d.rectangle([3, 8, 28, 11], fill=P['rr2'])
    d.rectangle([1, 14, 2, 15], fill=P['k'])
    d.rectangle([29, 14, 30, 15], fill=P['k'])
    return im


def chair():
    im = new()
    d = ImageDraw.Draw(im)
    d.rectangle([3, 1, 12, 8], fill=P['k'])
    d.rectangle([4, 2, 11, 7], fill=P['cp1'])
    d.rectangle([3, 8, 12, 11], fill=P['k'])
    d.rectangle([7, 11, 8, 14], fill=P['k'])
    d.line([(4, 15), (11, 15)], fill=P['k'])
    return im


def hemicycle_seat():
    im = carpet('cp')
    d = ImageDraw.Draw(im)
    d.rectangle([1, 2, 14, 9], fill=P['k'])
    d.rectangle([2, 3, 13, 8], fill=P['cp2'])
    d.rectangle([2, 10, 13, 13], fill=P['wd1'])
    d.point((7, 11), fill=P['gold'])
    return im


def heal_counter():
    """Cantine counter with a coffee machine (healing)."""
    im = new(48, 16)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 4, 47, 15], fill=P['wd0'])
    d.rectangle([0, 4, 47, 8], fill=P['wl1'])
    d.line([(0, 9), (47, 9)], fill=P['k'])
    d.rectangle([20, 0, 27, 7], fill=P['k'])
    d.rectangle([21, 1, 26, 4], fill=P['fr'])
    d.rectangle([5, 1, 10, 5], fill=P['fy'])
    d.rectangle([36, 2, 42, 6], fill=P['wh'])
    return im


# ---------------------------------------------------------------- registry
def build_registry():
    TILES.clear()
    OBJECTS.clear()
    for i, kind in enumerate(('tuft', 'plain', 'tufts', 'plain', 'blossom', 'clover')):
        TILES[f'grass{i}'] = Tile(grass(i + 1, kind=kind))
    TILES['grass'] = TILES['grass0']
    TILES['flowers_r'] = Tile(flowers('fr', 'fw', 3))
    TILES['flowers_y'] = Tile(flowers('fy', 'fb', 4))
    TILES['flowers_p'] = Tile(flowers('fp', 'fw', 6))
    TILES['dossiers'] = Tile(tall_dossiers(), B_GRASS)
    TILES['path'] = Tile(path_tile())
    TILES['pave'] = Tile(cobbles())
    TILES['curb_n'] = Tile(edge_curb('n'))
    TILES['curb_s'] = Tile(edge_curb('s'))
    TILES['road'] = Tile(asphalt())
    TILES['road_h'] = Tile(asphalt('h'))
    TILES['road_v'] = Tile(asphalt('v'))
    TILES['zebra'] = Tile(asphalt('zebra'))
    TILES['sand'] = Tile(sand())
    TILES['water'] = Tile(water(), B_WATER)
    for s in ('n', 's', 'e', 'w', 'ne', 'nw', 'se', 'sw'):
        TILES['shore_' + s] = Tile(shore(s), B_WATER)
    TILES['ledge'] = Tile(ledge(), B_LEDGE_D)
    TILES['hedge'] = Tile(hedge(), B_SOLID)
    TILES['fence'] = Tile(fence_h(), B_SOLID)
    TILES['rock'] = Tile(rock(), B_SOLID)
    TILES['mailbox'] = Tile(mailbox(), B_SOLID)
    TILES['sign'] = Tile(sign_post('wood'), B_SOLID)
    TILES['sign_eu'] = Tile(sign_post('eu'), B_SOLID)
    # interiors
    TILES['floor'] = Tile(floor_wood())
    TILES['tiles'] = Tile(floor_tiles())
    TILES['carpet'] = Tile(carpet('cp'))
    TILES['carpet_enc'] = Tile(carpet('cp'), B_CARPET)
    TILES['carpet_red'] = Tile(carpet('cr'))
    TILES['wall'] = Tile(wall_interior(), B_SOLID)
    TILES['wall_top'] = Tile(wall_interior(True), B_SOLID)
    TILES['window'] = Tile(window_interior(), B_SOLID)
    TILES['counter'] = Tile(counter(), B_COUNTER)
    TILES['doormat'] = Tile(doormat(), B_WARP_EDGE)
    TILES['stairs'] = Tile(stairs(), B_STAIRS)
    TILES['chair'] = Tile(chair(), B_SOLID)
    TILES['seat'] = Tile(hemicycle_seat(), B_SOLID)
    TILES['void'] = Tile(new(fill=(0, 0, 0, 255)), B_SOLID)

    def obj(name, img, beh, above=None, doors=()):
        OBJECTS[name] = Obj(img, beh, above, doors)

    for i in range(3):
        OBJECTS[f'tree{i}'] = Obj(tree_round(i), ['##', '##'], ['11', '00'], oy=1)
        OBJECTS[f'pine{i}'] = Obj(tree_pine(i), ['##', '##'], ['11', '00'], oy=1)
    OBJECTS['tree'] = Obj(tree_round(0), ['##', '##'], ['11', '00'], oy=1)
    OBJECTS['pine'] = Obj(tree_pine(0), ['##', '##'], ['11', '00'], oy=1)
    obj('lamp', lamp(), ['.', '#'], ['1', '0'])
    obj('flag', flagpole(), ['.', '#'], ['1', '0'])
    obj('statue', statue(), ['#', '#'], ['1', '0'])
    obj('bench', bench(), ['##'])
    obj('desk', desk(), ['##'])
    obj('bookshelf', bookshelf(), ['#', '#'])
    obj('plant', plant(), ['#', '#'], ['1', '0'])
    obj('pc', pc_terminal(), ['#', 'P'])
    obj('jukebox', jukebox(), ['#', '#'], ['1', '0'])
    obj('sofa', sofa(), ['##'])
    obj('heal_counter', heal_counter(), ['HHH'])
    # buildings
    OBJECTS['house_red'] = building(5, 4, 'rr', 'wl', door_x=2)
    OBJECTS['house_blue'] = building(5, 4, 'rb', 'wl', door_x=2)
    OBJECTS['house_grey'] = building(6, 4, 'rg', 'br', door_x=3)
    OBJECTS['cantine'] = building(6, 4, 'rr', 'wl', door_x=3, label='CANTINE', label_col='fr')
    OBJECTS['boutique'] = building(5, 4, 'rb', 'wl', door_x=2, label='BOUTIQUE', label_col='eu')
    OBJECTS['office'] = building(7, 5, 'rg', 'wl', door_x=3, glass=True)
    import tiles2
    import tiles3
    tiles2.register()
    tiles3.register()
    _grade_all()
    return TILES, OBJECTS


# ---------------------------------------------------------------- colour grade
_GRADE = {}


def grade_rgb(c):
    """Bright, comfortable grading in the spirit of the reference screenshots (SoulSilver, B/W, PMD):
    a little more saturation, shadows nudged towards blue-teal, lights towards a warm yellow, no pure black."""
    if c in _GRADE:
        return _GRADE[c]
    r, g, b = c
    L = (0.3 * r + 0.59 * g + 0.11 * b) / 255
    r, g, b = (L * 255 + (v - L * 255) * 1.06 for v in (r, g, b))
    t = max(0.0, (0.4 - L) / 0.4)
    r, g, b = r - 6 * t, g + 2 * t, b + 14 * t
    u = max(0.0, (L - 0.65) / 0.35)
    r, g, b = r + 6 * u, g + 5 * u, b - 10 * u
    r, g, b = (v * 0.94 + 18 for v in (r, g, b))   # lift the darks: softer contrast overall
    out = tuple(max(0, min(255, int(round(v)))) for v in (r, g, b))
    _GRADE[c] = out
    return out


def grade(im):
    import numpy as np
    a = np.array(im.convert('RGBA'))
    flat = a[..., :3].reshape(-1, 3)
    cols, inv = np.unique(flat, axis=0, return_inverse=True)
    mapped = np.array([grade_rgb(tuple(int(v) for v in c)) for c in cols], dtype='uint8')
    a[..., :3] = mapped[inv.reshape(-1)].reshape(a.shape[:2] + (3,))
    return Image.fromarray(a, 'RGBA')


def _grade_all():
    seen = set()
    for n, t in TILES.items():
        if id(t) in seen:
            RAW[n] = RAW[next(k for k, v in TILES.items() if v is t)]
            continue
        seen.add(id(t))
        RAW[n] = t.img
        t.img = grade(t.img)
    for o in OBJECTS.values():
        if id(o) not in seen:
            seen.add(id(o))
            o.img = grade(o.img)
    # the cycled water colours must match what the tiles now contain
    for k in ('w0', 'w1', 'w2', 'w3'):
        P[k] = grade_rgb(P[k][:3]) + (255,)
        _GRADE[P[k][:3]] = P[k][:3]   # tiles drawn later with these (auto shores) keep them as they are


BEH_CHARS = {'.': B_WALK, '#': B_SOLID, 'D': B_DOOR, 'C': B_COUNTER, 'P': B_PC, 'H': B_HEAL, 'S': B_SHOP,
             'W': B_WATER, 'G': B_GRASS}


if __name__ == '__main__':
    import os
    build_registry()
    os.makedirs('/tmp/tiles', exist_ok=True)
    # contact sheet
    items = list(TILES.items())
    W = 16 * 12
    sheet = Image.new('RGBA', (W, 16 * ((len(items) + 11) // 12)), (255, 0, 255, 255))
    for i, (n, t) in enumerate(items):
        sheet.alpha_composite(t.img, ((i % 12) * 16, (i // 12) * 16))
    sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save('/tmp/tiles/tiles.png')
    x = 0
    ob = Image.new('RGBA', (900, 120), (90, 160, 90, 255))
    for n, o in OBJECTS.items():
        if x + o.img.width > 900:
            break
        ob.alpha_composite(o.img, (x, 0))
        x += o.img.width + 4
    ob.resize((ob.width * 2, ob.height * 2), Image.NEAREST).save('/tmp/tiles/objects.png')
