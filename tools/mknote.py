#!/usr/bin/env python3
"""Artwork for the specimen banknotes of the ECB studio (Frankfurt).

Every picture is a 4-bit "darkness" map (0 = bare paper, 15 = full ink) that the game engraves at run time
(source/note.c turns tones into line hatching, as on real banknotes). Outputs:
  nitrofs/ui/note_art.bin       'NART', u16 count, u16 w, u16 h, then count images (4 bpp, low nibble = left pixel)
  nitrofs/ui/note_face_<g>.bin  the official portrait of Alex / Max, NOTE_W x NOTE_H, same packing
  build/preview/note_art.png    contact sheet for checking
Image order (ART_* in source/note.c): 6 birds, 6 EU institutions, 6 cultural spaces, the map of Europe —
the motifs of the ten finalist designs of the next euro banknotes (ECB design contest, 2026).
"""
import json
import math
import os
import struct

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'nitrofs', 'ui')
W, H = 112, 72          # stored size
S = 4                   # drawing scale
NOTE_W, NOTE_H = 64, 80


def canvas():
    im = Image.new('L', (W * S, H * S), 0)
    return im, ImageDraw.Draw(im)


def P(*pts):
    return [(x * S, y * S) for x, y in pts]


def ell(d, cx, cy, rx, ry, v, outline=None):
    d.ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S], fill=v, outline=outline, width=S)


def poly(d, pts, v, outline=None):
    d.polygon(P(*pts), fill=v, outline=outline)


def line(d, pts, v, w=1):
    d.line(P(*pts), fill=v, width=int(w * S), joint='curve')


def rect(d, x0, y0, x1, y1, v, outline=None):
    d.rectangle([x0 * S, y0 * S, x1 * S - 1, y1 * S - 1], fill=v, outline=outline, width=S if outline is not None else 0)


def water(d, y0, y1, v=70, step=3):
    for k, y in enumerate(range(y0, y1, step)):
        for x in range(-4 + (k % 2) * 3, W, 7):
            line(d, [(x, y), (x + 3, y - 0.6), (x + 5, y)], v, 0.6)


def finish(im):
    im = im.filter(ImageFilter.GaussianBlur(S * 0.35)).resize((W, H), Image.LANCZOS)
    return [[min(15, (v + 8) // 16) for v in row] for row in
            [list(im.tobytes())[y * W:(y + 1) * W] for y in range(H)]]


# ---------------------------------------------------------------- birds (front of the "rivers and birds" notes)
def wallcreeper():
    """5 euros: a wallcreeper on a cliff by a mountain spring."""
    im, d = canvas()
    poly(d, [(0, 0), (46, 0), (40, 18), (48, 34), (38, 52), (44, 72), (0, 72)], 120)
    for y in range(4, 72, 7):
        line(d, [(2, y), (14, y + 2), (26, y - 1), (36, y + 1)], 175, 0.7)
    line(d, [(40, 8), (36, 30), (41, 50), (37, 70)], 200, 1)
    for k in range(5):                                  # the spring
        line(d, [(44 + k, 20), (47 + k, 45), (44 + k * 2, 72)], 50, 0.6)
    # wings spread like a butterfly: grey with a crimson (mid-tone) band and white spots
    for sgn in (-1, 1):
        cx = 72
        poly(d, [(cx, 32), (cx + sgn * 26, 14), (cx + sgn * 36, 22), (cx + sgn * 32, 40), (cx + sgn * 14, 46)], 140)
        poly(d, [(cx + sgn * 6, 32), (cx + sgn * 26, 20), (cx + sgn * 32, 27), (cx + sgn * 24, 38)], 90)
        for (dx, dy) in ((28, 30), (31, 25), (24, 34)):
            ell(d, cx + sgn * dx, dy, 1.6, 1.4, 0)
        for k in range(4):                              # primaries
            line(d, [(cx + sgn * (20 + k * 4), 18 + k), (cx + sgn * (30 + k * 2), 24 + k * 4)], 200, 0.5)
    ell(d, 72, 36, 6, 12, 150)                          # body
    ell(d, 72, 23, 4.5, 4.5, 165)                       # head
    ell(d, 73, 22, 1, 1, 255)
    line(d, [(72, 19), (70, 12), (66, 7)], 220, 0.9)    # long thin curved bill
    poly(d, [(68, 46), (76, 46), (74, 56), (70, 56)], 175)
    return im


def kingfisher():
    """10 euros: a kingfisher on a branch above a waterfall pool."""
    im, d = canvas()
    for k in range(8):                                  # waterfall on the right
        line(d, [(84 + k * 3, 0), (86 + k * 3, 40), (82 + k * 4, 52)], 60, 0.8)
    water(d, 52, 72, 80)
    line(d, [(0, 40), (30, 36), (60, 41), (80, 38)], 210, 2.2)
    line(d, [(30, 36), (24, 26), (20, 18)], 210, 1.2)
    ell(d, 46, 26, 10, 9, 110)                           # back (bright blue -> mid tone)
    poly(d, [(36, 30), (56, 30), (50, 40), (40, 40)], 70)  # orange breast (light)
    ell(d, 56, 18, 7, 7, 120)                            # big head
    poly(d, [(61, 16), (80, 18), (61, 21)], 230)         # dagger bill
    ell(d, 58, 17, 1.4, 1.4, 255)
    poly(d, [(52, 20), (60, 21), (55, 24)], 20)          # white cheek patch
    poly(d, [(35, 27), (24, 34), (26, 36), (37, 32)], 150)  # short tail
    line(d, [(44, 39), (44, 37)], 230, 0.8)
    line(d, [(49, 39), (49, 37)], 230, 0.8)
    ell(d, 70, 58, 5, 1.6, 140)                          # a fish below
    return im


def bee_eater():
    """20 euros: a bee-eater colony on a sandy riverbank in a confined valley."""
    im, d = canvas()
    poly(d, [(0, 30), (40, 24), (112, 28), (112, 56), (0, 56)], 40)   # sandy bank
    for (x, y) in ((10, 38), (22, 44), (34, 36), (48, 46), (62, 38), (76, 44), (90, 36), (102, 46)):
        ell(d, x, y, 2.6, 2, 230)                         # nest burrows
    water(d, 58, 72, 75)
    line(d, [(0, 18), (112, 16)], 200, 0.7)               # a wire / branch
    for k, x in enumerate((26, 60, 92)):
        y = 12 - (k % 2) * 2
        poly(d, [(x - 6, y + 2), (x + 4, y - 2), (x + 6, y + 3), (x - 2, y + 6)], 120)   # slender body
        line(d, [(x - 6, y + 4), (x - 18, y + 9)], 150, 1.2)                           # long tail
        line(d, [(x - 17, y + 8), (x - 21, y + 10)], 150, 0.5)
        ell(d, x + 6, y - 1, 3.2, 3, 110)
        line(d, [(x + 8, y - 2), (x + 15, y + 1)], 230, 0.7)                            # curved bill
        line(d, [(x + 3, y - 1), (x + 9, y - 1)], 240, 0.7)                             # eye stripe
        line(d, [(x, y + 5), (x, y + 6)], 220, 0.5)
    ell(d, 44, 6, 2, 1.2, 160)                            # a bee
    line(d, [(43, 5), (44, 3)], 100, 0.4)
    return im


def white_stork():
    """50 euros: a white stork by a meandering river."""
    im, d = canvas()
    line(d, [(0, 60), (20, 52), (40, 62), (64, 54), (90, 64), (112, 58)], 80, 4)   # meander
    line(d, [(0, 66), (24, 60), (46, 70), (70, 62), (112, 68)], 60, 2)
    for x in range(0, 112, 5):                                                     # meadow grass
        line(d, [(x, 50), (x + 1, 46)], 90, 0.5)
    ell(d, 52, 30, 13, 8, 25, 200)                         # white body
    poly(d, [(40, 30), (62, 26), (66, 34), (44, 37)], 230) # black flight feathers
    line(d, [(60, 26), (66, 16), (68, 8)], 200, 2.8)       # neck outline
    line(d, [(60, 26), (66, 16), (68, 8)], 30, 1.8)        # long neck
    ell(d, 68, 7, 3, 2.6, 30)
    line(d, [(70, 7), (84, 12)], 150, 1.1)                 # long red bill (mid tone)
    ell(d, 69, 6, 0.7, 0.7, 255)
    line(d, [(50, 37), (50, 54)], 150, 0.9)                # legs (one raised)
    line(d, [(54, 37), (56, 44), (52, 47)], 150, 0.9)
    line(d, [(47, 54), (53, 54)], 150, 0.8)
    return im


def avocet():
    """100 euros: an avocet in the shallows of a river mouth."""
    im, d = canvas()
    water(d, 46, 72, 60, 2)
    line(d, [(0, 44), (112, 42)], 130, 0.8)                # horizon: estuary
    line(d, [(70, 40), (90, 37), (112, 38)], 160, 1.4)     # far shore
    ell(d, 50, 28, 14, 6, 20, 210)                          # white body
    poly(d, [(38, 25), (58, 22), (62, 26), (44, 29)], 235)  # black wing bars
    poly(d, [(40, 31), (52, 30), (50, 33)], 235)
    line(d, [(60, 25), (66, 16), (68, 12)], 200, 2.2)       # neck outline
    line(d, [(60, 25), (66, 16), (68, 12)], 25, 1.2)        # neck
    ell(d, 69, 10, 3, 2.6, 235)                             # black cap
    line(d, [(71, 11), (78, 12), (84, 9)], 235, 0.6)        # upturned bill
    line(d, [(48, 33), (46, 47)], 120, 0.7)                 # long blue-grey legs
    line(d, [(53, 33), (55, 47)], 120, 0.7)
    for k in range(3):                                      # reflection
        line(d, [(44 + k * 2, 52 + k * 3), (58 - k * 2, 52 + k * 3)], 110, 0.6)
    return im


def gannet():
    """200 euros: a northern gannet over the open sea."""
    im, d = canvas()
    water(d, 48, 72, 90, 3)
    poly(d, [(84, 48), (92, 30), (100, 26), (112, 32), (112, 48)], 140)   # sea stack
    for k in range(4):
        line(d, [(94 + k * 4, 30 + k), (92 + k * 4, 48)], 200, 0.5)
    # long narrow wings with black tips
    poly(d, [(46, 24), (8, 14), (4, 17), (40, 30)], 25, 210)
    poly(d, [(8, 14), (2, 13), (4, 17)], 240)
    poly(d, [(58, 24), (96, 10), (100, 13), (62, 30)], 25, 210)
    poly(d, [(96, 10), (104, 9), (100, 13)], 240)
    ell(d, 52, 27, 10, 4.5, 20, 210)                         # cigar body
    poly(d, [(42, 26), (34, 23), (34, 30)], 30)              # pointed tail
    ell(d, 63, 26, 3.4, 3, 70)                               # yellowish head
    poly(d, [(66, 25), (73, 27), (66, 28)], 160)             # dagger bill
    ell(d, 64, 25, 0.6, 0.6, 255)
    return im


# ---------------------------------------------------------------- EU institutions (back of the bird notes)
def parliament():
    im, d = canvas()
    d.chord([20 * S, 6 * S, 92 * S, 58 * S], 180, 360, fill=60, outline=200, width=S)   # glass vault (Brussels)
    for k in range(-5, 6):
        x = 56 + k * 6
        top = 32 - 26 * math.sqrt(max(0, 1 - ((x - 56) / 36) ** 2))
        line(d, [(x, top), (x, 32)], 150, 0.5)
    rect(d, 24, 32, 88, 64, 90, 200)
    for y in range(36, 62, 4):
        line(d, [(25, y), (87, y)], 140, 0.5)
    for x0 in (4, 88):
        rect(d, x0, 40, x0 + 20, 64, 120, 200)
        for y in range(44, 62, 6):
            for x in range(x0 + 3, x0 + 18, 5):
                rect(d, x, y, x + 3, y + 4, 200)
    rect(d, 50, 54, 62, 64, 220)
    line(d, [(0, 65), (112, 65)], 200, 1)
    return im


def commission():
    im, d = canvas()
    rect(d, 12, 14, 100, 64, 70, 210)                         # Berlaymont front wing
    rect(d, 40, 6, 72, 14, 110, 210)
    for y in range(18, 62, 3):
        line(d, [(13, y), (99, y)], 150 if y % 6 else 190, 0.5)  # louvres
    for x in range(20, 100, 10):
        line(d, [(x, 15), (x, 58)], 120, 0.4)
    rect(d, 44, 56, 68, 64, 200)
    for x in (30, 40, 72, 82):                                # flags
        line(d, [(x, 66), (x, 48)], 220, 0.5)
        rect(d, x, 48, x + 5, 52, 120)
    line(d, [(0, 66), (112, 66)], 200, 1)
    return im


def ecb():
    im, d = canvas()
    poly(d, [(26, 64), (30, 2), (52, 6), (50, 64)], 80, 210)   # two twisted glass towers
    poly(d, [(60, 64), (62, 10), (86, 4), (86, 64)], 100, 210)
    for y in range(8, 62, 4):
        line(d, [(30, y), (50, y + 1)], 140, 0.4)
        line(d, [(62, y + 2), (86, y)], 150, 0.4)
    rect(d, 50, 20, 62, 64, 40, 200)                          # atrium
    for y in range(22, 62, 8):
        line(d, [(50, y), (62, y + 4)], 170, 0.6)
    rect(d, 4, 50, 108, 64, 120, 200)                         # Grossmarkthalle (market hall)
    for x in range(8, 106, 6):
        rect(d, x, 54, x + 3, 62, 200)
    line(d, [(0, 65), (112, 65)], 200, 1)
    return im


def cjue():
    im, d = canvas()
    for x0 in (8, 30):                                       # two golden towers
        rect(d, x0, 4, x0 + 16, 64, 90, 210)
        for y in range(8, 62, 4):
            line(d, [(x0 + 1, y), (x0 + 15, y)], 150, 0.4)
    rect(d, 52, 34, 108, 64, 50, 210)                         # main building with ring
    line(d, [(52, 34), (108, 34)], 220, 1.2)
    for x in range(56, 106, 6):
        line(d, [(x, 36), (x, 62)], 190, 0.6)
    rect(d, 74, 54, 86, 64, 200)
    line(d, [(0, 65), (112, 65)], 200, 1)
    return im


def council():
    im, d = canvas()
    rect(d, 10, 8, 102, 64, 40, 200)                          # glass cube made of old window frames
    for y in range(10, 64, 6):
        for x in range(10 + (y % 12 == 4) * 4, 102, 8):
            rect(d, x, y, x + 7, y + 5, None, 120)
    ell(d, 56, 34, 18, 26, 150, 230)                          # the "lantern" (the egg)
    ell(d, 56, 34, 12, 20, 100)
    for k in range(-2, 3):
        line(d, [(56 + k * 6, 10), (56 + k * 7, 58)], 190, 0.4)
    line(d, [(0, 65), (112, 65)], 200, 1)
    return im


def court_auditors():
    im, d = canvas()
    for i, (x0, top) in enumerate(((6, 26), (40, 14), (76, 22))):   # three Kirchberg blocks
        rect(d, x0, top, x0 + 32, 64, 70 + i * 25, 210)
        for y in range(top + 3, 62, 5):
            for x in range(x0 + 3, x0 + 30, 5):
                rect(d, x, y, x + 3, y + 3, 190)
    line(d, [(36, 40), (42, 40)], 200, 1.5)                    # footbridges
    line(d, [(72, 40), (78, 40)], 200, 1.5)
    rect(d, 50, 56, 62, 64, 230)
    line(d, [(0, 65), (112, 65)], 200, 1)
    return im


# ---------------------------------------------------------------- cultural spaces (back of the culture notes)
def figure(d, x, y, h=18, v=200, arms='down', head=None):
    r = h / 7
    ell(d, x, y - h + r, r, r * 1.1, head if head is not None else v)
    poly(d, [(x - r * 1.3, y - h + 2.2 * r), (x + r * 1.3, y - h + 2.2 * r), (x + r * 1.1, y - h * 0.42),
             (x - r * 1.1, y - h * 0.42)], v)
    line(d, [(x - r * 0.6, y - h * 0.42), (x - r * 0.8, y)], v, r * 0.7)
    line(d, [(x + r * 0.6, y - h * 0.42), (x + r * 0.8, y)], v, r * 0.7)
    if arms == 'up':
        line(d, [(x - r * 1.2, y - h + 2.5 * r), (x - r * 2.6, y - h + 0.6 * r)], v, r * 0.5)
        line(d, [(x + r * 1.2, y - h + 2.5 * r), (x + r * 2.6, y - h + 0.6 * r)], v, r * 0.5)
    elif arms == 'down':
        line(d, [(x - r * 1.3, y - h + 2.5 * r), (x - r * 1.6, y - h * 0.5)], v, r * 0.5)
        line(d, [(x + r * 1.3, y - h + 2.5 * r), (x + r * 1.6, y - h * 0.5)], v, r * 0.5)


def street_performers():
    im, d = canvas()
    rect(d, 0, 0, 112, 40, 30)                                # house fronts
    for x in range(4, 112, 14):
        rect(d, x, 8, x + 8, 18, 110)
        rect(d, x, 24, x + 8, 34, 110)
    rect(d, 0, 58, 112, 72, 60)                               # cobbles
    figure(d, 40, 58, 26, 190)
    poly(d, [(36, 44), (48, 40), (52, 48), (40, 52)], 120)    # guitar
    line(d, [(48, 42), (58, 34)], 210, 0.8)
    figure(d, 66, 58, 26, 170, 'up')                          # juggler
    for k, (bx, by) in enumerate(((58, 24), (66, 18), (75, 24))):
        ell(d, bx, by, 1.6, 1.6, 230)
    for x in (12, 20, 92, 102):                               # passers-by
        figure(d, x, 64, 20, 120)
    return im


def choir():
    im, d = canvas()
    rect(d, 0, 60, 112, 72, 80)
    for row, (y, n) in enumerate(((30, 9), (42, 10), (54, 11))):
        for k in range(n):
            x = 8 + k * (96 / (n - 1))
            ell(d, x, y, 3.6, 4, 150 - row * 10)
            ell(d, x, y + 1.6, 0.9, 1.1, 240)                  # singing mouths
            rect(d, x - 4, y + 4, x + 4, y + 10, 210 - row * 20)
    figure(d, 56, 72, 16, 230, 'up')                           # conductor
    for x, y in ((20, 10), (40, 6), (72, 8), (92, 12)):        # music notes
        ell(d, x, y + 4, 2, 1.5, 200)
        line(d, [(x + 1.8, y + 4), (x + 1.8, y - 3), (x + 5, y - 1)], 200, 0.6)
    return im


def school():
    im, d = canvas()
    rect(d, 6, 4, 70, 36, 210, 120)                           # blackboard
    for y, txt in ((10, 28), (17, 40), (24, 22), (30, 34)):
        line(d, [(12, y), (12 + txt, y)], 40, 0.6)
    ell(d, 54, 22, 7, 7, None, 40)                            # a little atom
    ell(d, 54, 22, 2, 7, None, 40)
    figure(d, 84, 46, 30, 170, 'down')                        # the teacher
    line(d, [(80, 26), (68, 20)], 170, 1.2)
    for row, y in enumerate((56, 70)):
        for x in range(12, 76, 16):
            figure(d, x + row * 6, y, 14, 140)
            rect(d, x - 7 + row * 6, y - 4, x + 7 + row * 6, y - 2, 220)
    return im


def library():
    im, d = canvas()
    for x0 in (2, 74):                                         # bookshelves
        rect(d, x0, 2, x0 + 36, 70, 200)
        for y in range(4, 68, 11):
            for k in range(14):
                hh = 7 + (k * 7 + y) % 3
                rect(d, x0 + 2 + k * 2.4, y + 9 - hh, x0 + 4 + k * 2.4, y + 9, 60 + (k * 37 + y) % 90)
    rect(d, 42, 48, 72, 52, 220)                               # reading table
    line(d, [(46, 52), (46, 66)], 220, 1)
    line(d, [(68, 52), (68, 66)], 220, 1)
    figure(d, 56, 50, 18, 160)
    poly(d, [(50, 44), (57, 42), (62, 44), (57, 46)], 40)      # open book
    figure(d, 80, 70, 13, 130, 'up')                           # child reaching a shelf
    return im


def street_art():
    im, d = canvas()
    rect(d, 4, 4, 108, 52, 70, 220)                           # wall with a mural
    ell(d, 30, 26, 18, 16, 170)
    ell(d, 30, 26, 9, 8, 40)
    poly(d, [(52, 46), (70, 8), (90, 46)], 140)
    poly(d, [(62, 30), (80, 30), (71, 46)], 220)
    for x in range(10, 104, 9):
        line(d, [(x, 48), (x + 5, 40)], 200, 0.7)
    for x, h, arms in ((14, 18, 'down'), (28, 13, 'up'), (54, 19, 'down'), (78, 12, 'down'), (96, 18, 'down')):
        figure(d, x, 72, h, 190, arms)
    return im


def tree_square():
    im, d = canvas()
    rect(d, 0, 50, 112, 72, 40)
    for x in (10, 34, 78, 102):                               # plane trees
        line(d, [(x, 56), (x, 30)], 200, 2.2)
        ell(d, x, 22, 13, 13, 150)
        for k in range(6):
            ell(d, x - 8 + k * 3, 16 + (k % 3) * 5, 3, 3, 200)
    ell(d, 56, 54, 13, 4, 120, 210)                           # fountain
    line(d, [(56, 54), (56, 40)], 200, 1.2)
    for k in (-1, 1):
        line(d, [(56, 40), (56 + k * 6, 44), (56 + k * 9, 52)], 90, 0.6)
    rect(d, 18, 60, 32, 62, 220)                              # bench
    figure(d, 40, 70, 15, 170)
    figure(d, 70, 70, 11, 150, 'up')
    figure(d, 88, 70, 16, 180)
    return im


def europe_map():
    im, d = canvas()
    EU = {'Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Cyprus', 'Czechia', 'Czech Rep.', 'Denmark', 'Estonia',
          'Finland', 'France', 'Germany', 'Greece', 'Hungary', 'Ireland', 'Italy', 'Latvia', 'Lithuania',
          'Luxembourg', 'Malta', 'Netherlands', 'Poland', 'Portugal', 'Romania', 'Slovakia', 'Slovenia', 'Spain',
          'Sweden'}
    gj = json.load(open(os.path.join(ROOT, 'assets', 'geo', 'ne110.geojson'), encoding='utf-8'))
    def pr(lon, lat):
        return ((lon + 24) / 70 * W * S, (72 - lat) / 38 * H * S)
    for f in gj['features']:
        name = f['properties'].get('NAME') or f['properties'].get('ADMIN')
        g = f['geometry']
        polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
        for p in polys:
            pts = [pr(x, y) for x, y in p[0]]
            if all(x < -50 or x > W * S + 50 or y < -50 or y > H * S + 50 for x, y in pts):
                continue
            eu = name in EU or f['properties'].get('ADMIN') in EU
            d.polygon(pts, fill=150 if eu else 60, outline=230)
    return im


ARTS = [wallcreeper, kingfisher, bee_eater, white_stork, avocet, gannet,
        parliament, commission, ecb, cjue, council, court_auditors,
        street_performers, choir, school, library, street_art, tree_square, europe_map]


def pack(rows):
    out = bytearray()
    for row in rows:
        for x in range(0, len(row), 2):
            out.append((row[x] & 15) | ((row[x + 1] & 15) << 4))
    return bytes(out)


def face(gender):
    src = Image.open(os.path.join(ROOT, 'assets', 'art', 'portraits', f'{gender}_neutral.png')).convert('RGB')
    crop = src.crop((96, 24, 336, 324)).resize((NOTE_W, NOTE_H), Image.LANCZOS)
    rows = []
    for y in range(NOTE_H):
        row = []
        for x in range(NOTE_W):
            r, g, b = crop.getpixel((x, y))
            if r > 200 and b > 200 and g < 90:          # magenta background = paper
                row.append(0)
                continue
            lum = (r * 77 + g * 150 + b * 29) >> 8
            row.append(max(1, min(15, (255 - lum) * 17 // 256 + 1)))
        rows.append(row)
    return rows


def main():
    os.makedirs(OUT, exist_ok=True)
    out = os.path.join(OUT, 'note_art.bin')
    if os.path.exists(out) and os.path.getmtime(out) > os.path.getmtime(__file__):
        return
    images = [finish(f()) for f in ARTS]
    blob = bytearray(b'NART') + struct.pack('<HHH', len(images), W, H)
    for rows in images:
        blob += pack(rows)
    open(out, 'wb').write(blob)
    faces = {g: face(g) for g in ('alex', 'max')}
    for g, rows in faces.items():
        open(os.path.join(OUT, f'note_face_{g}.bin'), 'wb').write(pack(rows))
    sheet = Image.new('L', (W * 4 + 5 * 4, H * 5 + 6 * 4 + NOTE_H + 4), 255)
    for i, rows in enumerate(images):
        im = Image.new('L', (W, H))
        im.putdata([255 - v * 17 for row in rows for v in row])
        sheet.paste(im, (4 + (i % 4) * (W + 4), 4 + (i // 4) * (H + 4)))
    for k, rows in enumerate(faces.values()):
        im = Image.new('L', (NOTE_W, NOTE_H))
        im.putdata([255 - v * 17 for row in rows for v in row])
        sheet.paste(im, (4 + k * (NOTE_W + 8), 4 + 5 * (H + 4)))
    os.makedirs(os.path.join(ROOT, 'build', 'preview'), exist_ok=True)
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save(os.path.join(ROOT, 'build', 'preview', 'note_art.png'))
    print('note art', len(images), 'pictures')


if __name__ == '__main__':
    main()
