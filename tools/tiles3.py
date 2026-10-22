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


def register():
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
