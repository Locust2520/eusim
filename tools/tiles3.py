#!/usr/bin/env python3
"""Landmarks of the extended cities (Frankfurt, Athens, Piraeus, Brussels, Strasbourg, London, Budapest, Paris,
Luxembourg) and the ECB banknote studio. Registered into tiles.OBJECTS after tiles2."""
import math

from PIL import ImageDraw

import tiles as T
from tiles import P, Obj, new
from tiles2 import rgb, outline_box, door, beh_grid, label, eu_flag

K = P['k']


def solid(w, h, doors=()):
    return beh_grid(w, h, doors)


def obj(im, w, h, doors=(), above=None):
    return Obj(im, solid(w, h, doors), above, list(doors))


def gable_house(w, h, wall, timber, roof, door_x=None, seed=0, stepped=False):
    """A tall gabled town house seen from the front (half-timbered, or stepped like the Römer)."""
    W, H = w * 16, h * 16
    im = new(W, H)
    d = ImageDraw.Draw(im)
    top = 6
    if stepped:
        steps = 4
        for k in range(steps):   # widest and lowest first: the gable climbs in steps towards the middle
            x0 = k * W // (2 * steps + 2)
            d.rectangle([x0, top + (steps - 1 - k) * 9, W - 1 - x0, H - 1], fill=wall, outline=K)
    else:
        d.polygon([(0, H // 3 + 6), (W // 2, top), (W - 1, H // 3 + 6)], fill=roof, outline=K)
        d.rectangle([2, H // 3 + 6, W - 3, H - 1], fill=wall, outline=K)
    if timber:
        for y in range(H // 3 + 10, H - 16, 14):
            d.line([(3, y), (W - 4, y)], fill=timber, width=2)
        for x in range(4, W - 3, 10):
            d.line([(x, H // 3 + 8), (x, H - 18)], fill=timber, width=2)
        for x in range(4, W - 12, 20):
            for y in range(H // 3 + 10, H - 30, 28):
                d.line([(x, y), (x + 10, y + 14)], fill=timber, width=2)
                d.line([(x + 10, y), (x, y + 14)], fill=timber, width=2)
    for x in range(6, W - 8, 12):          # windows
        for y in range(H // 3 + 12 if not stepped else top + 30, H - 22, 16):
            d.rectangle([x, y, x + 6, y + 8], fill=P['gl3'], outline=K)
            d.point((x + 2, y + 2), fill=P['gl2'])
    d.rectangle([1, H - 14, W - 2, H - 1], fill=rgb('b8705c'), outline=K)   # red sandstone ground floor
    for x in range(4, W - 6, 10):
        d.arc([x, H - 14, x + 8, H - 2], 180, 360, fill=K)
    doors = []
    if door_x is not None:
        door(d, door_x * 16 + 2, H - 16, False, 12)
        doors.append((door_x, h - 1))
    return obj(im, w, h, doors)


# ---------------------------------------------------------------- Frankfurt
def romer():
    """The Römer: Frankfurt's town hall since 1405, three stepped gables on the Römerberg."""
    w, h = 9, 6
    im = new(w * 16, h * 16)
    for k, col in enumerate((rgb('e8d8c0'), rgb('d8c0a8'), rgb('e4ccb0'))):
        part = gable_house(3, h, col, None, None, stepped=True).img
        im.alpha_composite(part, (k * 48, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([52, 54, 91, 58], fill=rgb('8a5838'), outline=K)          # balcony
    for x in range(54, 90, 4):
        d.line([(x, 54), (x, 58)], fill=K)
    label(im, 'ROMER', w * 8, 44, 'rr0')
    return obj(im, w, h)


def fachwerk(variant):
    infill = (rgb('f0e4c8'), rgb('e8d0a0'), rgb('f4dcd0'))[variant % 3]
    return gable_house(4, 6, infill, rgb('6a3c28'), (rgb('a85040'), rgb('8a5048'), rgb('9a4a3a'))[variant % 3])


def justitia():
    """The Justice Fountain: Justitia holds scales and a sword — and, unusually, wears no blindfold."""
    im = new(32, 48)
    d = ImageDraw.Draw(im)
    d.ellipse([1, 34, 30, 46], fill=P['c3'], outline=K)
    d.ellipse([4, 36, 27, 44], fill=P['w1'])
    d.rectangle([13, 14, 18, 38], fill=P['c1'], outline=K)
    d.ellipse([12, 3, 19, 10], fill=P['gold'], outline=K)                 # gilded figure
    d.polygon([(11, 10), (20, 10), (22, 24), (9, 24)], fill=P['gold'], outline=K)
    d.line([(6, 12), (25, 12)], fill=K)                                   # scales
    d.polygon([(4, 16), (8, 16), (6, 13)], fill=P['gold'])
    d.polygon([(23, 16), (27, 16), (25, 13)], fill=P['gold'])
    return Obj(im, ['..', '##', '##'], ['11', '00', '00'])


def paulskirche():
    """The Paulskirche: red sandstone church where the first freely elected German parliament met (1848-49)."""
    w, h = 7, 7
    im = new(w * 16, h * 16)
    d = ImageDraw.Draw(im)
    W, H = w * 16, h * 16
    stone, dark = rgb('c87860'), rgb('9a5848')
    d.rectangle([W // 2 - 10, 0, W // 2 + 10, 56], fill=stone, outline=K)   # tower
    d.polygon([(W // 2 - 10, 8), (W // 2, 0), (W // 2 + 10, 8)], fill=rgb('6a8a7a'), outline=K)
    d.ellipse([W // 2 - 6, 14, W // 2 + 6, 26], fill=P['wh'], outline=K)    # clock
    d.line([(W // 2, 20), (W // 2, 16)], fill=K)
    d.ellipse([2, 34, W - 3, H - 1], fill=stone, outline=K)                  # the oval nave
    d.rectangle([2, 56, W - 3, H - 1], fill=stone, outline=K)
    d.chord([2, 34, W - 3, 80], 180, 360, fill=rgb('6a8a7a'), outline=K)
    for x in range(10, W - 12, 14):
        d.rectangle([x, 64, x + 6, 84], fill=P['gl3'], outline=K)
        d.pieslice([x, 60, x + 6, 68], 180, 360, fill=P['gl3'], outline=K)
    d.line([(2, H - 6), (W - 3, H - 6)], fill=dark)
    door(d, W // 2 - 7, H - 16, False, 14)
    return obj(im, w, h, [(3, h - 1)])


def euro_sculpture():
    """Ottmar Hörl's Euro sign (2001) in front of the former ECB tower, Willy-Brandt-Platz."""
    im = new(48, 64)
    d = ImageDraw.Draw(im)
    d.rectangle([14, 52, 33, 63], fill=P['c3'], outline=K)
    d.line([(23, 40), (23, 52)], fill=K, width=2)
    d.arc([6, 6, 42, 44], 40, 320, fill=P['eu'], width=7)
    d.arc([6, 6, 42, 44], 40, 320, fill=K, width=1)
    d.rectangle([2, 18, 30, 22], fill=P['eu'], outline=K)
    d.rectangle([2, 27, 28, 31], fill=P['eu'], outline=K)
    for k in range(12):                                                  # the arc of stars above
        a = math.pi * (1.1 + 0.8 * k / 11)
        x, y = 24 + 22 * math.cos(a), 26 + 22 * math.sin(a)
        d.rectangle([x - 1, y - 1, x + 1, y + 1], fill=P['gold'])
    return Obj(im, ['...', '.#.', '###', '###'], ['111', '111', '000', '000'])


def boerse():
    """The Frankfurt Stock Exchange (1879): a neo-classical hall."""
    w, h = 8, 5
    im = new(w * 16, h * 16)
    d = ImageDraw.Draw(im)
    W, H = w * 16, h * 16
    stone = rgb('e4dcc8')
    d.polygon([(4, 20), (W // 2, 2), (W - 5, 20)], fill=stone, outline=K)
    d.rectangle([2, 20, W - 3, 26], fill=stone, outline=K)
    for x in range(10, W - 10, 14):
        d.rectangle([x, 26, x + 7, H - 10], fill=P['wl1'], outline=K)
        d.line([(x + 5, 27), (x + 5, H - 10)], fill=P['wl2'])
    d.rectangle([0, H - 10, W - 1, H - 1], fill=P['c3'], outline=K)
    door(d, W // 2 - 7, H - 16, False, 14)
    label(im, 'BORSE', W // 2, 10, 'rg0')
    return obj(im, w, h, [(4, h - 1)])


def bronze_animal(kind):
    """Bull and Bear in front of the Stock Exchange (Reinhard Dachlauer, 1985)."""
    im = new(32, 32)
    d = ImageDraw.Draw(im)
    br, br2 = rgb('7a5a3a'), rgb('a07a50')
    d.rectangle([4, 24, 27, 31], fill=P['c3'], outline=K)
    if kind == 'bull':
        d.ellipse([5, 10, 25, 23], fill=br, outline=K)
        d.ellipse([20, 8, 30, 18], fill=br, outline=K)
        d.line([(22, 8), (20, 3)], fill=br2, width=2)
        d.line([(28, 8), (30, 3)], fill=br2, width=2)
    else:
        d.ellipse([3, 9, 23, 23], fill=br, outline=K)
        d.ellipse([1, 6, 11, 16], fill=br, outline=K)
        d.ellipse([2, 5, 5, 8], fill=br2)
        d.ellipse([7, 5, 10, 8], fill=br2)
    for x in (8, 14, 18, 22):
        d.line([(x, 22), (x, 25)], fill=K, width=2)
    return Obj(im, ['##', '##'], ['11', '00'])


def goethe_haus():
    return gable_house(5, 5, rgb('ece0c8'), None, rgb('808898'), door_x=2)


def tavern(sign='bembel'):
    """An apple-wine tavern in Sachsenhausen: a wreath of pine and a Bembel hang over the door."""
    o = T.building(6, 5, 'rg', 'wl', door_x=3)
    d = ImageDraw.Draw(o.img)
    d.ellipse([60, 40, 76, 56], fill=P['l2'], outline=P['l0'])         # pine wreath
    d.ellipse([64, 44, 72, 52], fill=(0, 0, 0, 0))
    d.ellipse([30, 42, 42, 56], fill=rgb('9aa0b0'), outline=K)         # the Bembel
    d.rectangle([33, 46, 39, 52], fill=P['eu2'])
    d.line([(42, 46), (45, 49)], fill=K)
    return o


def geldmuseum():
    """Money Museum of the Deutsche Bundesbank."""
    o = T.building(7, 5, 'rg', 'wl', door_x=3, glass=True)
    d = ImageDraw.Draw(o.img)
    d.ellipse([46, 12, 66, 32], fill=P['gold'], outline=K)
    d.arc([50, 15, 63, 29], 50, 310, fill=K, width=2)
    d.line([(49, 21), (58, 21)], fill=K)
    d.line([(49, 24), (58, 24)], fill=K)
    return o


def messeturm():
    """The Messeturm, home of the Frankfurt Book Fair grounds, with its pencil-shaped top."""
    im = new(48, 128)
    d = ImageDraw.Draw(im)
    d.rectangle([10, 28, 37, 127], fill=rgb('c88a78'), outline=K)
    for y in range(32, 124, 6):
        d.line([(12, y), (35, y)], fill=P['gl3'])
    d.polygon([(10, 28), (24, 2), (37, 28)], fill=rgb('8a9aa8'), outline=K)
    beh = ['...'] * 6 + ['###', '###']
    above = ['111'] * 6 + ['000', '000']
    return Obj(im, beh, above)


def memorial_stele():
    """Memorial at the Grossmarkthalle (ECB): plain stone with an inscription, no decoration."""
    im = new(16, 32)
    d = ImageDraw.Draw(im)
    d.rectangle([2, 6, 13, 31], fill=rgb('7a7a82'), outline=K)
    for y in range(10, 26, 3):
        d.line([(4, y), (11, y)], fill=rgb('5a5a62'))
    return Obj(im, ['.', '#'], ['1', '0'])


def tavern_table():
    """Long wooden tavern table with a Bembel and two Gerippte glasses."""
    im = new(32, 16)
    d = ImageDraw.Draw(im)
    d.rectangle([1, 4, 30, 11], fill=P['wd1'], outline=K)
    d.line([(2, 5), (29, 5)], fill=P['wd2'])
    for x in (3, 27):
        d.rectangle([x, 11, x + 1, 15], fill=K)
    d.ellipse([12, 0, 19, 8], fill=rgb('9aa0b0'), outline=K)
    d.rectangle([14, 3, 17, 6], fill=P['eu2'])
    for x in (5, 23):
        d.rectangle([x, 2, x + 3, 7], fill=rgb('e6c070'), outline=K)
    return Obj(im, ['##'])

# ---------------------------------------------------------------- Athens
def columns(d, x0, x1, y0, y1, step=10, col=None, shade=None):
    col = col or rgb('f2ecdc')
    shade = shade or rgb('c8bca8')
    for x in range(x0, x1 - 5, step):
        d.rectangle([x, y0, x + 5, y1], fill=col)
        d.line([(x + 4, y0), (x + 4, y1)], fill=shade)
        d.rectangle([x - 1, y0, x + 6, y0 + 1], fill=shade)


def vouli():
    """The Hellenic Parliament on Syntagma Square (the former royal palace, 1843)."""
    w, h = 10, 5
    im = new(w * 16, h * 16)
    d = ImageDraw.Draw(im)
    W, H = w * 16, h * 16
    ochre, shade = rgb('f0d8a0'), rgb('c8ac78')
    d.rectangle([0, 14, W - 1, H - 1], fill=ochre, outline=K)
    d.rectangle([0, 10, W - 1, 14], fill=shade, outline=K)
    for y in (20, 40):
        for x in range(6, W - 6, 10):
            if W // 2 - 26 < x < W // 2 + 20:
                continue
            d.rectangle([x, y, x + 5, y + 10], fill=P['gl3'], outline=K)
    d.polygon([(W // 2 - 28, 18), (W // 2, 4), (W // 2 + 28, 18)], fill=ochre, outline=K)   # portico
    columns(d, W // 2 - 24, W // 2 + 28, 18, H - 6, 9, P['wh'], shade)
    d.rectangle([0, H - 6, W - 1, H - 1], fill=shade, outline=K)
    d.line([(W // 2, 4), (W // 2, -8 + 12)], fill=K)
    for k in range(5):                                       # the Greek flag on the roof
        d.line([(W // 2 + 1, 0 + k), (W // 2 + 12, 0 + k)], fill=P['eu2'] if k % 2 == 0 else P['wh'])
    return obj(im, w, h)


def unknown_soldier():
    """Tomb of the Unknown Soldier: a fallen hoplite carved in the wall below the Parliament."""
    w, h = 6, 2
    im = new(w * 16, h * 16)
    d = ImageDraw.Draw(im)
    W, H = w * 16, h * 16
    d.rectangle([0, 0, W - 1, H - 1], fill=rgb('e8e0d0'), outline=K)
    d.rectangle([10, 8, W - 11, 22], fill=rgb('d8ccb8'))
    d.ellipse([18, 12, 26, 19], fill=rgb('b8ac98'))                      # helmeted head
    d.polygon([(26, 14), (70, 12), (78, 18), (26, 19)], fill=rgb('b8ac98'))
    d.ellipse([46, 10, 58, 20], fill=rgb('a89c88'))                      # shield
    for x in range(8, W - 8, 4):
        d.point((x, 26), fill=rgb('a09080'))
    return obj(im, w, h)


def sentry_box():
    im = new(16, 32)
    d = ImageDraw.Draw(im)
    d.rectangle([1, 4, 14, 31], fill=P['wh'], outline=K)
    for y in range(6, 30, 6):
        d.rectangle([2, y, 13, y + 2], fill=P['eu2'])
    d.polygon([(0, 5), (8, 0), (15, 5)], fill=rgb('8a9aa8'), outline=K)
    d.rectangle([4, 12, 11, 30], fill=rgb('3a3a48'))
    return Obj(im, ['.', '#'], ['1', '0'])


def periptero():
    """A periptero: the Greek street kiosk that sells everything, from newspapers to phone credit."""
    im = new(32, 32)
    d = ImageDraw.Draw(im)
    d.rectangle([2, 8, 29, 31], fill=rgb('3a6a4a'), outline=K)
    d.rectangle([0, 4, 31, 8], fill=rgb('2a5a3a'), outline=K)            # roof
    d.rectangle([4, 10, 27, 22], fill=rgb('f0e8d8'))                    # window full of goods
    for x in range(5, 27, 4):
        d.rectangle([x, 11, x + 2, 15], fill=(rgb('e04040'), rgb('4070d0'), rgb('f0c040'))[x % 3])
        d.rectangle([x, 17, x + 2, 21], fill=(rgb('40a060'), rgb('e08030'), rgb('8040a0'))[x % 3])
    d.rectangle([22, 23, 29, 30], fill=rgb('c8e0f0'), outline=K)        # drinks fridge
    return Obj(im, ['##', '##'], ['11', '00'])


def fountain():
    im = new(48, 32)
    d = ImageDraw.Draw(im)
    d.ellipse([1, 10, 46, 30], fill=P['c3'], outline=K)
    d.ellipse([5, 13, 42, 27], fill=P['w1'])
    d.rectangle([21, 4, 26, 20], fill=P['c1'], outline=K)
    for k in (-1, 1):
        d.line([(24, 4), (24 + k * 10, 10), (24 + k * 14, 18)], fill=P['w3'])
    return Obj(im, ['###', '###'])


def orange_tree():
    """Bitter orange trees line the streets of Athens; the fruit is too sour to eat, but makes good marmalade."""
    base = T.tree_round(1)
    im = base.copy()
    d = ImageDraw.Draw(im)
    for (x, y) in ((8, 6), (18, 4), (22, 12), (12, 14), (25, 8), (6, 12)):
        d.ellipse([x, y, x + 3, y + 3], fill=rgb('f09020'), outline=rgb('c06010'))
    return Obj(im, ['##', '##'], ['11', '00'], oy=1)


def metro_entrance():
    """Entrance of the Athens metro (the M of Attiko Metro)."""
    im = new(32, 32)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 10, 31, 31], fill=P['c3'], outline=K)
    for y in range(14, 30, 4):
        d.rectangle([4, y, 27, y + 2], fill=P['c1'])
        d.line([(4, y + 3), (27, y + 3)], fill=rgb('8a8a90'))
    d.rectangle([10, 0, 21, 10], fill=P['eu2'], outline=K)
    d.line([(12, 8), (12, 2), (15, 5), (18, 2), (18, 8)], fill=P['wh'])
    return Obj(im, ['##', '##'], ['11', '00'])


def bank_greece():
    """The Bank of Greece (1938), on Panepistimiou Street."""
    w, h = 5, 4
    im = new(w * 16, h * 16)
    d = ImageDraw.Draw(im)
    W, H = w * 16, h * 16
    stone = rgb('e0d8c8')
    d.rectangle([0, 8, W - 1, H - 1], fill=stone, outline=K)
    d.rectangle([0, 4, W - 1, 10], fill=rgb('c8beac'), outline=K)
    columns(d, 6, W - 6, 12, H - 18, 12)
    d.rectangle([0, H - 18, W - 1, H - 1], fill=stone, outline=K)
    for x in range(6, W - 8, 12):
        if abs(x - W // 2 + 3) > 8:
            d.rectangle([x, H - 14, x + 6, H - 6], fill=P['gl3'], outline=K)
    door(d, W // 2 - 7, H - 16, False, 14)
    return obj(im, w, h, [(2, h - 1)])


def cycladic(variant):
    """Anafiotika: white cube houses with blue doors, built by builders from the island of Anafi."""
    w, h = 3, 3
    im = new(w * 16, h * 16)
    d = ImageDraw.Draw(im)
    W, H = w * 16, h * 16
    d.rectangle([1, 6 + variant * 4, W - 2, H - 1], fill=rgb('fafaf6'), outline=K)
    d.rectangle([4, 2 + variant * 4, W - 14, 8 + variant * 4], fill=rgb('fafaf6'), outline=K)
    blue = rgb('2a6ad0')
    d.rectangle([W - 18, H - 16, W - 8, H - 1], fill=blue, outline=K)
    d.rectangle([8, H - 26, 16, H - 18], fill=blue, outline=K)
    if variant:
        for (x, y) in ((2, 18), (5, 22), (3, 26), (7, 20)):            # bougainvillea
            d.ellipse([x, y, x + 4, y + 4], fill=P['fp'])
    return obj(im, w, h)


def market_stall(variant):
    """A stall of the Monastiraki flea market."""
    im = new(32, 32)
    d = ImageDraw.Draw(im)
    stripe = (P['fr'], P['eu2'])[variant]
    for x in range(0, 32, 6):
        d.rectangle([x, 2, x + 2, 9], fill=stripe)
        d.rectangle([x + 3, 2, x + 5, 9], fill=P['wh'])
    d.line([(0, 9), (31, 9)], fill=K)
    d.rectangle([2, 18, 29, 25], fill=P['wd1'], outline=K)
    if variant == 0:                                                  # blue "mati" eyes against the evil eye
        for x in range(5, 28, 6):
            d.ellipse([x, 12, x + 4, 16], fill=P['eu2'], outline=K)
            d.point((x + 2, 14), fill=P['wh'])
    else:                                                             # old records, copper pots, books
        for x in range(4, 28, 5):
            d.rectangle([x, 13, x + 3, 17], fill=(rgb('c07030'), rgb('303040'), rgb('a04040'))[x % 3])
    d.rectangle([3, 25, 4, 31], fill=K)
    d.rectangle([27, 25, 28, 31], fill=K)
    return Obj(im, ['##', '##'], ['11', '00'])


def acropolis_museum():
    """The Acropolis Museum (2009): its top floor is turned to align with the Parthenon."""
    w, h = 7, 4
    im = new(w * 16, h * 16)
    d = ImageDraw.Draw(im)
    W, H = w * 16, h * 16
    d.rectangle([10, 2, W - 11, 24], fill=P['gl0'], outline=K)                # tilted glass gallery
    for x in range(14, W - 12, 6):
        d.line([(x, 3), (x - 2, 23)], fill=P['gl1'])
    d.rectangle([0, 24, W - 1, H - 1], fill=rgb('c8c4bc'), outline=K)
    for y in range(28, H - 4, 6):
        d.line([(1, y), (W - 2, y)], fill=rgb('aaa69e'))
    door(d, W // 2 - 7, H - 16, True, 14)
    return obj(im, w, h, [(3, h - 1)])


def zappeion():
    """The Zappeion: Greece signed its accession to the European Communities here on 28 May 1979."""
    w, h = 7, 4
    im = new(w * 16, h * 16)
    d = ImageDraw.Draw(im)
    W, H = w * 16, h * 16
    stone = rgb('f0e8d8')
    d.rectangle([0, 14, W - 1, H - 1], fill=stone, outline=K)
    d.polygon([(W // 2 - 26, 16), (W // 2, 2), (W // 2 + 26, 16)], fill=stone, outline=K)
    columns(d, W // 2 - 24, W // 2 + 26, 16, H - 6, 8)
    for x in list(range(6, W // 2 - 30, 10)) + list(range(W // 2 + 32, W - 6, 10)):
        d.rectangle([x, 26, x + 5, 38], fill=P['gl3'], outline=K)
    d.rectangle([0, H - 6, W - 1, H - 1], fill=rgb('c8bca8'), outline=K)
    return obj(im, w, h)


def stadium():
    """The Panathenaic Stadium: the only stadium built entirely of marble; the first modern Olympics, 1896."""
    w, h = 8, 5
    im = new(w * 16, h * 16)
    d = ImageDraw.Draw(im)
    W, H = w * 16, h * 16
    marble = rgb('f4f0e8')
    d.rectangle([0, 0, W - 1, H - 1], fill=marble, outline=K)
    for k in range(0, 24, 4):                                       # tiers around the horseshoe
        d.rectangle([k, k, W - 1 - k, H - 1], outline=rgb('c8c0b0'))
    d.rectangle([24, 24, W - 25, H - 1], fill=rgb('c86a50'))         # the track
    d.rectangle([32, 32, W - 33, H - 1], fill=P['g1'])
    d.chord([24, 8, W - 25, 40], 180, 360, fill=rgb('c86a50'))
    d.chord([32, 16, W - 33, 48], 180, 360, fill=P['g1'])
    return obj(im, w, h)


def odeon():
    """The Odeon of Herodes Atticus (161 AD), below the Acropolis, where a young Maria Callas sang in 1944."""
    w, h = 6, 4
    im = new(w * 16, h * 16)
    d = ImageDraw.Draw(im)
    W, H = w * 16, h * 16
    stone = rgb('d8c0a0')
    d.rectangle([0, 0, W - 1, H - 1], fill=stone, outline=K)
    for row, y in enumerate((6, 26, 46)):
        for x in range(4, W - 10, 13):
            d.rectangle([x, y + 4, x + 8, y + 16], fill=rgb('5a4a3a'))
            d.pieslice([x, y, x + 8, y + 8], 180, 360, fill=rgb('5a4a3a'))
    return obj(im, w, h)


def cafe_table():
    """A kafeneio table with two iced frappés."""
    im = new(32, 16)
    d = ImageDraw.Draw(im)
    d.ellipse([6, 2, 25, 9], fill=P['wh'], outline=K)
    d.line([(15, 9), (15, 15)], fill=K)
    for x in (9, 19):
        d.rectangle([x, 0, x + 3, 6], fill=rgb('c8a070'), outline=K)
        d.rectangle([x, 0, x + 3, 1], fill=P['wh'])
        d.line([(x + 3, 0), (x + 5, -1)], fill=P['fr'])
    d.rectangle([0, 6, 4, 14], fill=P['wd0'], outline=K)
    d.rectangle([27, 6, 31, 14], fill=P['wd0'], outline=K)
    return Obj(im, ['##'])


def cat(variant):
    im = new()
    d = ImageDraw.Draw(im)
    col = (rgb('e09040'), rgb('505058'), rgb('f0f0f0'))[variant % 3]
    d.ellipse([3, 8, 12, 14], fill=col, outline=K)
    d.ellipse([9, 4, 15, 10], fill=col, outline=K)
    d.polygon([(10, 5), (10, 2), (12, 5)], fill=col, outline=K)
    d.polygon([(13, 5), (14, 2), (15, 6)], fill=col, outline=K)
    d.line([(3, 10), (0, 6)], fill=K, width=2)
    d.point((12, 7), fill=K)
    return Obj(im, ['#'])



def frieze(real):
    """Parthenon frieze slab in the Acropolis Museum: honey-coloured original, or white plaster cast where the
    original is in London."""
    im = new(32, 16)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 1, 31, 14], fill=rgb('e8c890') if real else rgb('fbfbf8'), outline=K)
    shade = rgb('b89860') if real else rgb('d8d8d4')
    for x in (4, 14, 23):                       # riders and horses in low relief
        d.ellipse([x, 4, x + 7, 10], fill=shade)
        d.line([(x + 2, 10), (x + 1, 13)], fill=shade)
        d.line([(x + 6, 10), (x + 7, 13)], fill=shade)
    return Obj(im, ['##'])

# ---------------------------------------------------------------- Piraeus
def piraeus_station():
    """Piraeus station (1929), terminus of Line 1, the Athens–Piraeus railway opened in 1869."""
    w, h = 8, 5
    im = new(w * 16, h * 16)
    d = ImageDraw.Draw(im)
    W, H = w * 16, h * 16
    stone = rgb('e8dcc4')
    d.rectangle([0, 12, W - 1, H - 1], fill=stone, outline=K)
    d.chord([20, 0, W - 21, 60], 180, 360, fill=P['gl0'], outline=K)       # the great glazed arch
    for k in range(-4, 5):
        x = W // 2 + k * 9
        d.line([(x, 30 - int(28 * math.sqrt(max(0, 1 - ((x - W // 2) / 44) ** 2)))), (x, 30)], fill=P['mt1'])
    d.rectangle([20, 30, W - 21, H - 1], fill=P['gl1'], outline=K)
    for x in range(24, W - 22, 8):
        d.line([(x, 31), (x, H - 2)], fill=P['mt1'])
    columns(d, 4, 18, 22, H - 2, 7, stone, rgb('c0b49c'))
    columns(d, W - 18, W - 2, 22, H - 2, 7, stone, rgb('c0b49c'))
    door(d, W // 2 - 7, H - 16, True, 14)
    return obj(im, w, h)


def gantry_crane():
    """A ship-to-shore container crane: legs on the quay, the boom reaching over the ship."""
    w, h = 5, 7
    im = new(w * 16, h * 16)
    d = ImageDraw.Draw(im)
    W, H = w * 16, h * 16
    blue, dark = rgb('3a78c0'), rgb('24508a')
    for x in (6, W - 26):
        d.rectangle([x, 20, x + 5, H - 1], fill=blue, outline=K)
    d.rectangle([0, 18, W - 1, 26], fill=blue, outline=K)                 # boom
    d.line([(8, 18), (W // 2, 2), (W - 8, 18)], fill=dark, width=2)
    d.rectangle([W // 2 - 8, 26, W // 2 + 4, 34], fill=rgb('f0c020'), outline=K)   # trolley cabin
    d.line([(W // 2 - 2, 34), (W // 2 - 2, 60)], fill=K)
    d.rectangle([W // 2 - 10, 60, W // 2 + 6, 70], fill=rgb('c03030'), outline=K)  # container on the spreader
    beh = ['.....'] * 5 + ['#...#', '#...#']
    above = ['11111'] * 5 + ['00000', '00000']
    return Obj(im, beh, above)


def ferry():
    """A ferry for the islands."""
    w, h = 10, 4
    im = new(w * 16, h * 16)
    d = ImageDraw.Draw(im)
    W, H = w * 16, h * 16
    d.polygon([(0, 30), (W - 1, 30), (W - 14, H - 2), (8, H - 2)], fill=P['wh'], outline=K)
    d.rectangle([2, 40, W - 8, 44], fill=P['eu2'])
    d.rectangle([24, 12, W - 30, 30], fill=P['wh'], outline=K)
    for x in range(28, W - 34, 8):
        d.rectangle([x, 18, x + 4, 22], fill=P['gl3'])
    d.rectangle([W - 50, 2, W - 38, 12], fill=P['fr'], outline=K)        # funnel
    d.rectangle([W - 50, 2, W - 38, 4], fill=K)
    return Obj(im, ['#' * w] * h)


def taverna():
    """A fish taverna at Mikrolimano."""
    o = T.building(4, 3, 'rb', 'wl', door_x=None)
    d = ImageDraw.Draw(o.img)
    for x in range(0, 64, 8):
        d.rectangle([x, 20, x + 3, 26], fill=P['eu2'])
        d.rectangle([x + 4, 20, x + 7, 26], fill=P['wh'])
    d.line([(0, 26), (63, 26)], fill=K)
    return o


def ancient_wall():
    """A fragment of the Long Walls that Themistocles had built to protect Piraeus, Athens' port."""
    im = new(64, 16)
    d = ImageDraw.Draw(im)
    for row, y in enumerate((2, 8)):
        for x in range(-((row * 8) % 16), 64, 16):
            d.rectangle([x + 1, y, x + 14, y + 5], fill=rgb('c8b08c'), outline=rgb('8a7458'))
    return Obj(im, ['####'])


# ---------------------------------------------------------------- ECB studio
def intaglio_press():
    im = new(48, 32)
    d = ImageDraw.Draw(im)
    d.rectangle([2, 14, 45, 26], fill=rgb('5a5e6a'), outline=K)
    d.rectangle([6, 10, 41, 14], fill=P['mt1'], outline=K)               # the plate bed
    d.ellipse([16, 0, 32, 16], fill=P['mt0'], outline=K)                 # big wheel
    for k in range(6):
        a = k * math.pi / 3
        d.line([(24, 8), (24 + 9 * math.cos(a), 8 + 9 * math.sin(a))], fill=K)
    d.rectangle([4, 26, 8, 31], fill=K)
    d.rectangle([39, 26, 43, 31], fill=K)
    return Obj(im, ['###', '###'])


def design_board(kind):
    """An easel with one of the finalist designs pinned on it."""
    im = new(32, 32)
    d = ImageDraw.Draw(im)
    d.line([(8, 20), (4, 31)], fill=P['wd0'], width=2)
    d.line([(24, 20), (28, 31)], fill=P['wd0'], width=2)
    d.rectangle([2, 2, 29, 21], fill=P['wh'], outline=K)
    col = {'culture': rgb('4060b0'), 'birds': rgb('3a9a60'), 'jury': rgb('a08040')}[kind]
    d.rectangle([4, 6, 27, 18], fill=col, outline=K)
    if kind == 'culture':
        d.ellipse([7, 8, 15, 17], fill=P['wh'])
    elif kind == 'birds':
        d.polygon([(7, 14), (14, 9), (20, 11), (26, 9), (19, 15)], fill=P['wh'])
    else:
        for y in (8, 11, 14):
            d.line([(7, y), (24, y)], fill=P['wh'])
    return Obj(im, ['##', '##'], ['11', '00'])


def europa_painting():
    """Europa in a gilded frame: her portrait comes from a Greek vase over 2,000 years old (Louvre) and appears
    in the watermark of today's euro notes. Behind it: the studio's secret door."""
    im = new(32, 32)
    d = ImageDraw.Draw(im)
    d.rectangle([1, 1, 30, 30], fill=P['gold'], outline=K)
    d.rectangle([4, 4, 27, 27], fill=rgb('2a3a5a'))
    d.ellipse([10, 7, 21, 19], fill=rgb('e0b890'))                       # profile in the vase-painting style
    d.pieslice([8, 5, 23, 17], 180, 360, fill=rgb('3a2a20'))
    d.rectangle([10, 18, 21, 27], fill=rgb('b04a30'))
    return Obj(im, ['##', '##'])


def fence_vertical():
    """Chain-link fence seen side-on, for north-south runs."""
    im = new()
    d = ImageDraw.Draw(im)
    d.rectangle([6, 0, 9, 15], fill=P['mt0'], outline=K)
    for y in range(-8, 16, 4):
        d.line([(3, y), (12, y + 8)], fill=P['mt1'])
        d.line([(3, y + 8), (12, y)], fill=P['mt1'])
    d.rectangle([7, 0, 8, 15], fill=P['mt2'])
    return im


def register():
    T.TILES['fence_v'] = T.Tile(fence_vertical(), T.B_SOLID)
    O = T.OBJECTS
    O['romer'] = romer()
    for i in range(3):
        O[f'fachwerk_{i}'] = fachwerk(i)
    O['justitia'] = justitia()
    O['paulskirche'] = paulskirche()
    O['euro_sculpture'] = euro_sculpture()
    O['boerse'] = boerse()
    O['bull'] = bronze_animal('bull')
    O['bear'] = bronze_animal('bear')
    O['goethe_haus'] = goethe_haus()
    O['tavern'] = tavern()
    O['geldmuseum'] = geldmuseum()
    O['tavern_table'] = tavern_table()
    O['messeturm'] = messeturm()
    O['memorial'] = memorial_stele()
    O['intaglio_press'] = intaglio_press()
    for k in ('culture', 'birds', 'jury'):
        O['board_' + k] = design_board(k)
    O['europa_painting'] = europa_painting()
    O['vouli'] = vouli()
    O['unknown_soldier'] = unknown_soldier()
    O['sentry_box'] = sentry_box()
    O['periptero'] = periptero()
    O['fountain'] = fountain()
    O['orange_tree'] = orange_tree()
    O['metro_entrance'] = metro_entrance()
    O['bank_greece'] = bank_greece()
    O['cycladic_0'] = cycladic(0)
    O['cycladic_1'] = cycladic(1)
    O['stall_0'] = market_stall(0)
    O['stall_1'] = market_stall(1)
    O['acropolis_museum'] = acropolis_museum()
    O['zappeion'] = zappeion()
    O['stadium'] = stadium()
    O['odeon'] = odeon()
    O['cafe_table'] = cafe_table()
    for i in range(3):
        O[f'cat_{i}'] = cat(i)
    O['piraeus_station'] = piraeus_station()
    O['gantry_crane'] = gantry_crane()
    O['ferry'] = ferry()
    O['taverna'] = taverna()
    O['ancient_wall'] = ancient_wall()
    O['frieze_real'] = frieze(True)
    O['frieze_cast'] = frieze(False)
