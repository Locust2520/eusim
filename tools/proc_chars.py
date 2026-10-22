#!/usr/bin/env python3
"""Procedural chibi overworld characters (Pokémon-DS-like), 32x32 frames, 4bpp.

Sheet frame order (12): down[stand, stepA, stepB], up[...], left[...], right[...].
Each character = body style + head style + palette + accessories.
"""
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------- body templates (16 wide, rows 12..22)
# O outline, J jacket, T shirt, A tie/accent, S skin (hands), P pants, F shoes, K skirt
BODY = {
    'down': [
        '...OJJTTTTJJO...',
        '..OJJJJTTJJJJO..',
        '.OJJJJJAAJJJJJO.',
        '.OSOJJJAAJJJOSO.',
        '.OSOJJJJJJJJOSO.',
        '..OOJJJJJJJJOO..',
        '...OPPPPPPPPO...',
        '...OPPPOOPPPO...',
        '...OPPO..OPPO...',
        '...OFFO..OFFO...',
        '...OOOO..OOOO...',
    ],
    'up': [
        '...OJJJJJJJJO...',
        '..OJJJJJJJJJJO..',
        '.OJJJJJJJJJJJJO.',
        '.OSOJJJJJJJJOSO.',
        '.OSOJJJJJJJJOSO.',
        '..OOJJJJJJJJOO..',
        '...OPPPPPPPPO...',
        '...OPPPOOPPPO...',
        '...OPPO..OPPO...',
        '...OFFO..OFFO...',
        '...OOOO..OOOO...',
    ],
    'left': [
        '....OJJTJJJO....',
        '....OJJJJJJO....',
        '....OJJJJJJO....',
        '....OJSSJJJO....',
        '....OJSSJJJO....',
        '....OJJJJJJO....',
        '....OPPPPPPO....',
        '....OPPPPPPO....',
        '....OPPOOPPO....',
        '....OFFO.OFFO...',
        '....OOOO.OOOO...',
    ],
}
# leg rows (last 4 rows) for walking frames
LEGS = {
    'down': {
        'A': ['...OPPPOOPPPO...', '...OPPO..OPPO...', '...OFFO..OOOO...', '...OOOO.........'],
        'B': ['...OPPPOOPPPO...', '...OPPO..OPPO...', '...OOOO..OFFO...', '.........OOOO...'],
    },
    'up': {
        'A': ['...OPPPOOPPPO...', '...OPPO..OPPO...', '...OFFO..OOOO...', '...OOOO.........'],
        'B': ['...OPPPOOPPPO...', '...OPPO..OPPO...', '...OOOO..OFFO...', '.........OOOO...'],
    },
    'left': {
        'A': ['....OPPPPPPO....', '...OPPO.OPPO....', '..OFFO...OFFO...', '..OOOO...OOOO...'],
        'B': ['....OPPPPPPO....', '....OPPPPPO.....', '....OFFFFO......', '....OOOOOO......'],
    },
}
SKIRT_ROWS = {
    'down': ['...OKKKKKKKKO...', '..OKKKKKKKKKKO..', '...OSSO..OSSO...', '...OFFO..OFFO...', '...OOOO..OOOO...'],
    'up': ['...OKKKKKKKKO...', '..OKKKKKKKKKKO..', '...OSSO..OSSO...', '...OFFO..OFFO...', '...OOOO..OOOO...'],
    'left': ['....OKKKKKKO....', '...OKKKKKKKKO...', '....OSSO.OSO....', '....OFFO.OFFO...', '....OOOO.OOOO...'],
}

# ---------------------------------------------------------------- heads (rows 0..13, may overlap body)
# H hair, S skin, E eye, M mouth, O outline, G glasses, W white of eye/sclera
HEADS = {
    'short': {
        'down': [
            '.....OOOOOO.....',
            '...OOHHHHHHOO...',
            '..OHHHHHHHHHHO..',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OHSSHSSSSSSSHO.',
            '.OSSSSSSSSSSSSO.',
            '.OSSEESSSSEESSO.',
            '.OSSEESSSSEESSO.',
            '.OSSSSSSSSSSSSO.',
            '..OSSSSMMSSSSO..',
            '...OOSSSSSSOO...',
        ],
        'up': [
            '.....OOOOOO.....',
            '...OOHHHHHHOO...',
            '..OHHHHHHHHHHO..',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OSHHHHHHHHHHSO.',
            '.OSSHHHHHHHHSSO.',
            '..OSSSSSSSSSSO..',
            '...OOSSSSSSOO...',
        ],
        'left': [
            '.....OOOOOO.....',
            '...OOHHHHHHOO...',
            '..OHHHHHHHHHHO..',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OSSSHHHHHHHHHO.',
            '.OSSSSSSHHHHHHO.',
            '.OSESSSSSSHHHHO.',
            '.OSESSSSSSSHHHO.',
            '.OSSSSSSSSSSHHO.',
            '..OMSSSSSSSSSO..',
            '...OOSSSSSSOO...',
        ],
    },
    'long': {
        'down': [
            '.....OOOOOO.....',
            '...OOHHHHHHOO...',
            '..OHHHHHHHHHHO..',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OHHHSSSSSSHHHO.',
            '.OHSSSSSSSSSSHO.',
            '.OHSEESSSSEESHO.',
            '.OHSEESSSSEESHO.',
            '.OHSSSSSSSSSSHO.',
            '.OHHSSSMMSSSHHO.',
            '.OHHOOSSSSOOHHO.',
            '.OHHO......OHHO.',
            '..OO........OO..',
        ],
        'up': [
            '.....OOOOOO.....',
            '...OOHHHHHHOO...',
            '..OHHHHHHHHHHO..',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '..OHHHHHHHHHHO..',
            '...OOOOOOOOOO...',
        ],
        'left': [
            '.....OOOOOO.....',
            '...OOHHHHHHOO...',
            '..OHHHHHHHHHHO..',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OSSSHHHHHHHHHO.',
            '.OSSSSSSHHHHHHO.',
            '.OSESSSSSHHHHHO.',
            '.OSESSSSSHHHHHO.',
            '.OSSSSSSSHHHHHO.',
            '..OMSSSSSHHHHHO.',
            '...OOSSSOHHHHHO.',
            '........OHHHHO..',
            '.........OOOO...',
        ],
    },
    'bob': {
        'down': [
            '.....OOOOOO.....',
            '...OOHHHHHHOO...',
            '..OHHHHHHHHHHO..',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OHHSSSSSSHHHHO.',
            '.OHSSSSSSSSSSHO.',
            '.OHSEESSSSEESHO.',
            '.OHSEESSSSEESHO.',
            '.OHSSSSSSSSSSHO.',
            '.OHHSSSMMSSSHHO.',
            '..OOOSSSSSSOOO..',
        ],
        'up': [
            '.....OOOOOO.....',
            '...OOHHHHHHOO...',
            '..OHHHHHHHHHHO..',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '..OOOSSSSSSOOO..',
        ],
        'left': [
            '.....OOOOOO.....',
            '...OOHHHHHHOO...',
            '..OHHHHHHHHHHO..',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OSSHHHHHHHHHHO.',
            '.OSSSSSSHHHHHHO.',
            '.OSESSSSSHHHHHO.',
            '.OSESSSSSHHHHHO.',
            '.OSSSSSSSHHHHHO.',
            '..OMSSSSSHHHHHO.',
            '...OOSSSSOOOOO..',
        ],
    },
    'bald': {
        'down': [
            '.....OOOOOO.....',
            '...OOSSSSSSOO...',
            '..OSSSSSSSSSSO..',
            '.OSSSSSSSSSSSSO.',
            '.OHSSSSSSSSSSHO.',
            '.OHSSSSSSSSSSHO.',
            '.OSSSSSSSSSSSSO.',
            '.OSSEESSSSEESSO.',
            '.OSSEESSSSEESSO.',
            '.OSSSSSSSSSSSSO.',
            '..OSSSSMMSSSSO..',
            '...OOSSSSSSOO...',
        ],
        'up': [
            '.....OOOOOO.....',
            '...OOSSSSSSOO...',
            '..OSSSSSSSSSSO..',
            '.OSSSSSSSSSSSSO.',
            '.OHSSSSSSSSSSHO.',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OSHHHHHHHHHHSO.',
            '.OSSHHHHHHHHSSO.',
            '..OSSSSSSSSSSO..',
            '...OOSSSSSSOO...',
        ],
        'left': [
            '.....OOOOOO.....',
            '...OOSSSSSSOO...',
            '..OSSSSSSSSSSO..',
            '.OSSSSSSSSSSSSO.',
            '.OSSSSSSSSSSHHO.',
            '.OSSSSSSSSHHHHO.',
            '.OSSSSSSSHHHHHO.',
            '.OSESSSSSSHHHHO.',
            '.OSESSSSSSSHHHO.',
            '.OSSSSSSSSSSHHO.',
            '..OMSSSSSSSSSO..',
            '...OOSSSSSSOO...',
        ],
    },
    'spiky': {
        'down': [
            '..O..O.OO.O..O..',
            '..OHOOHHHHOOHO..',
            '..OHHHHHHHHHHO..',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OHSSHSSHSSHSHO.',
            '.OSSSSSSSSSSSSO.',
            '.OSSEESSSSEESSO.',
            '.OSSEESSSSEESSO.',
            '.OSSSSSSSSSSSSO.',
            '..OSSSSMMSSSSO..',
            '...OOSSSSSSOO...',
        ],
        'up': [
            '..O..O.OO.O..O..',
            '..OHOOHHHHOOHO..',
            '..OHHHHHHHHHHO..',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OSHHHHHHHHHHSO.',
            '.OSSHHHHHHHHSSO.',
            '..OSSSSSSSSSSO..',
            '...OOSSSSSSOO...',
        ],
        'left': [
            '...O.O.OO.O.....',
            '...OHOHHHHOHO...',
            '..OHHHHHHHHHHO..',
            '.OHHHHHHHHHHHHOO',
            '.OHHHHHHHHHHHHHO',
            '.OSSSHHHHHHHHHO.',
            '.OSSSSSSHHHHHHO.',
            '.OSESSSSSSHHHHO.',
            '.OSESSSSSSSHHHO.',
            '.OSSSSSSSSSSHHO.',
            '..OMSSSSSSSSSO..',
            '...OOSSSSSSOO...',
        ],
    },
    'bun': {
        'down': [
            '......OOOO......',
            '.....OHHHHO.....',
            '...OOOHHHHOOO...',
            '..OHHHHHHHHHHO..',
            '.OHHHHHHHHHHHHO.',
            '.OHHSSSSSSSSHHO.',
            '.OHSSSSSSSSSSHO.',
            '.OSSEESSSSEESSO.',
            '.OSSEESSSSEESSO.',
            '.OSSSSSSSSSSSSO.',
            '..OSSSSMMSSSSO..',
            '...OOSSSSSSOO...',
        ],
        'up': [
            '......OOOO......',
            '.....OHHHHO.....',
            '...OOOHHHHOOO...',
            '..OHHHHHHHHHHO..',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OHHHHHHHHHHHHO.',
            '.OSHHHHHHHHHHSO.',
            '.OSSHHHHHHHHSSO.',
            '..OSSSSSSSSSSO..',
            '...OOSSSSSSOO...',
        ],
        'left': [
            '...........OOOO.',
            '.....OOOOOOHHHHO',
            '...OOHHHHHHOHHO.',
            '..OHHHHHHHHHHO..',
            '.OHHHHHHHHHHHHO.',
            '.OSSSHHHHHHHHHO.',
            '.OSSSSSSHHHHHHO.',
            '.OSESSSSSSHHHHO.',
            '.OSESSSSSSSHHHO.',
            '.OSSSSSSSSSSHHO.',
            '..OMSSSSSSSSSO..',
            '...OOSSSSSSOO...',
        ],
    },
}

SKIN = {'light': ('f8d0b0', 'e0a888'), 'pale': ('fce0cc', 'e8b8a0'), 'tan': ('e0a878', 'c08058'),
        'brown': ('b07850', '8a5838'), 'dark': ('7a4a30', '5a3420'), 'orange': ('f0b070', 'd08848')}
HAIR = {'black': ('282830', '404050'), 'brown': ('6a4028', '8a5838'), 'blonde': ('f0d070', 'f8e8a0'),
        'grey': ('a0a0a8', 'c8c8d0'), 'white': ('e8e8f0', 'ffffff'), 'red': ('c05030', 'e07040'),
        'ash': ('c8b890', 'e0d4b0'), 'dkbrown': ('402818', '5a3a24'), 'gold': ('f0c040', 'f8e080'),
        'none': ('000000', '000000')}


def hexc(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def shade(c, f):
    """Darken (f < 1) towards a cool blue, or lighten (f > 1) towards a warm yellow, like hand-picked ramps."""
    r, g, b = c
    if f < 1:
        t = 1 - f
        r, g, b = r * f, g * f + 6 * t, b * f + 70 * t
    else:
        t = f - 1
        r, g, b = r + (255 - r) * t, g + (240 - g) * t, b + (190 - b) * t * 0.6
    return tuple(max(0, min(255, int(v))) for v in (r, g, b))


class Char:
    def __init__(self, name, head='short', skin='light', hair='brown', jacket='303850', shirt='f0f0f0',
                 tie=None, pants='404048', shoes='302020', skirt=None, glasses=False, accessory=None,
                 hair_shadow=None):
        self.name, self.head, self.skin, self.hair = name, head, skin, hair
        self.jacket, self.shirt, self.tie, self.pants, self.shoes = jacket, shirt, tie, pants, shoes
        self.skirt, self.glasses, self.accessory = skirt, glasses, accessory


def palette_for(c):
    s0, s1 = SKIN[c.skin]
    h0, h1 = HAIR[c.hair]
    jac = hexc(c.jacket)
    pal = {
        'O': (36, 34, 62),
        'S': hexc(s0), 's': hexc(s1),
        'H': hexc(h0), 'h': hexc(h1),
        'E': (32, 32, 48),
        'M': shade(hexc(s1), 0.8),
        'J': jac, 'j': shade(jac, 0.72), 'Jl': shade(jac, 1.18),
        'T': hexc(c.shirt),
        'A': hexc(c.tie) if c.tie else hexc(c.shirt),
        'P': hexc(c.pants), 'p': shade(hexc(c.pants), 0.75),
        'F': hexc(c.shoes),
        'K': hexc(c.skirt) if c.skirt else hexc(c.pants),
        'G': (40, 40, 56),
        'W': (250, 250, 250),
        'B': hexc(c.accessory[1]) if c.accessory else (0, 0, 0),
    }
    return pal


def squeeze(row):
    """Narrow a 16-wide template row by 2 pixels (characters looked too wide)."""
    row = row.ljust(16, '.')
    return '.' + row[:2] + row[3:13] + row[14:16] + '.'


def compose(c, d, step):
    """Return 32x32 RGBA frame for direction d ('down','up','left','right') and step (0 stand, 1 A, 2 B)."""
    flip = d == 'right'
    dd = 'left' if flip else d
    rows = [list('.' * 16) for _ in range(24)]
    body = list(BODY[dd])
    if c.skirt:
        sk = SKIRT_ROWS[dd]
        body = body[:6] + sk
    elif step:
        legs = LEGS[dd]['A' if step == 1 else 'B']
        body = body[:7] + legs
    for i, r in enumerate(body):
        rows[12 + i] = list(squeeze(r))
    head = HEADS[c.head][dd]
    for i, r in enumerate(head):
        for x, ch in enumerate(squeeze(r)):
            if ch != '.':
                rows[i][x] = ch
    pal = palette_for(c)
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    bob = 1 if step else 0
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == '.':
                continue
            col = pal.get(ch, (255, 0, 255))
            # simple shading: right/bottom side of jacket & hair darker
            if ch == 'J' and (x >= 11 or y >= 20):
                col = pal['j']
            elif ch == 'J' and r[x - 1] == 'O' and y < 18:
                col = pal['Jl']
            if ch == 'H' and y <= 2 and 4 <= x <= 8:
                col = pal['h']
            if ch == 'S' and dd == 'down' and y < 12 and x >= 11:
                col = pal['s']
            img.putpixel((8 + x, 7 + y - (bob if y < 12 else 0) + 1), col + (255,))
    # glasses
    if c.glasses and dd != 'up':
        g = pal['G'] + (255,)
        if dd == 'down':
            for (x, y) in [(3, 7), (4, 6), (5, 6), (6, 7), (9, 7), (10, 6), (11, 6), (12, 7), (7, 7), (8, 7)]:
                img.putpixel((8 + x, 7 + y - bob + 1), g)
        else:
            for (x, y) in [(3, 6), (4, 6), (5, 7), (2, 7)]:
                img.putpixel((8 + x, 7 + y - bob + 1), g)
    # accessory: backpack/briefcase
    if c.accessory and c.accessory[0] == 'backpack':
        col = pal['B'] + (255,)
        if dd == 'up':
            for y in range(13, 19):
                for x in range(4, 12):
                    img.putpixel((8 + x, 7 + y + 1), col if 4 < x < 11 and 13 < y < 18 else pal['O'] + (255,))
        elif dd == 'left':
            for y in range(13, 18):
                for x in range(10, 13):
                    img.putpixel((8 + x, 7 + y + 1), col)
    if c.accessory and c.accessory[0] == 'briefcase' and dd in ('down', 'left'):
        col = pal['B'] + (255,)
        bx = 13 if dd == 'down' else 6
        for y in range(17, 21):
            for x in range(bx, bx + 4):
                img.putpixel((8 + x - (1 if dd == 'down' else 0), 7 + y + 1), col)
    if flip:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    return img


def sheet(c):
    frames = []
    for d in ('down', 'up', 'left', 'right'):
        for s in (0, 1, 2):
            frames.append(compose(c, d, s))
    return frames


# ---------------------------------------------------------------- cast
CAST = [
    Char('player_f', 'long', 'light', 'brown', jacket='283c78', shirt='f8f8f8', tie='3060d0', pants='3a3a48',
         skirt='283c78', accessory=('backpack', 'c04040')),
    Char('player_m', 'short', 'light', 'dkbrown', jacket='283c78', shirt='f8f8f8', tie='3060d0', pants='3a3a48',
         accessory=('backpack', 'c04040')),
    Char('oliver', 'spiky', 'pale', 'ash', jacket='8a2030', shirt='f0f0f0', tie='203070', pants='303040'),
    Char('schuman', 'bald', 'pale', 'grey', jacket='383838', shirt='f0f0f0', tie='603030', pants='383838', glasses=True),
    Char('monnet', 'bald', 'pale', 'white', jacket='404858', shirt='f0f0f0', tie='403030', pants='404858'),
    Char('stagiaire', 'short', 'tan', 'black', jacket='5070a0', shirt='f0f0f0', pants='303040', accessory=('backpack', '40a060')),
    Char('stagiaire_f', 'bun', 'brown', 'black', jacket='a05080', shirt='f8f8f8', pants='303040', skirt='303048'),
    Char('fonctionnaire', 'short', 'light', 'grey', jacket='505860', shirt='e8e8f0', tie='304080', pants='404850',
         glasses=True, accessory=('briefcase', '6a4028')),
    Char('fonctionnaire_f', 'bob', 'light', 'brown', jacket='6a7080', shirt='f0f0f0', pants='404850', skirt='404858'),
    Char('lobbyiste', 'short', 'light', 'black', jacket='202028', shirt='f8f8f8', tie='c09020', pants='202028',
         accessory=('briefcase', '202020')),
    Char('lobbyiste_f', 'bob', 'pale', 'blonde', jacket='202028', shirt='f8f8f8', pants='202028', skirt='202028',
         accessory=('briefcase', '202020')),
    Char('depute', 'short', 'tan', 'brown', jacket='1e3a8a', shirt='f8f8f8', tie='e0b020', pants='1e2a5a'),
    Char('deputee', 'long', 'light', 'red', jacket='a03040', shirt='f8f8f8', pants='303040', skirt='602030'),
    Char('journaliste', 'spiky', 'brown', 'black', jacket='607048', shirt='f0f0e0', pants='4a4a40', accessory=('backpack', '806040')),
    Char('agent', 'short', 'dark', 'black', jacket='1a1a2a', shirt='e0e0e0', tie='1a1a2a', pants='1a1a2a'),
    Char('cantiniere', 'bun', 'tan', 'brown', jacket='f8f8f8', shirt='f8f8f8', pants='f0f0f0', skirt='e8e8e8'),
    Char('vendeur', 'short', 'light', 'brown', jacket='3070c0', shirt='f8f8f8', pants='303040'),
    Char('agriculteur', 'short', 'tan', 'brown', jacket='3a6a3a', shirt='d0c090', pants='3050a0', shoes='3a2a1a'),
    Char('militant', 'long', 'light', 'blonde', jacket='40a050', shirt='f0f0f0', pants='5a4a3a'),
    Char('touriste', 'short', 'pale', 'red', jacket='e07030', shirt='f8f8f8', pants='c0a070', accessory=('backpack', '3080c0')),
    Char('enfant', 'spiky', 'light', 'blonde', jacket='e04040', shirt='f8f8f8', pants='3050a0'),
    Char('mamie', 'bun', 'pale', 'white', jacket='9060a0', shirt='f0f0f0', pants='605070', skirt='705080'),
    Char('banquier', 'bald', 'light', 'grey', jacket='303040', shirt='f8f8f8', tie='a02020', pants='303040', glasses=True),
    Char('avocat', 'short', 'pale', 'black', jacket='3a3a4a', shirt='f8f8f8', tie='5a2a6a', pants='3a3a4a', glasses=True),
    Char('douanier', 'short', 'tan', 'black', jacket='3a4a6a', shirt='b0c0d0', tie='1a2a4a', pants='2a3a5a'),
    Char('interprete', 'bob', 'brown', 'black', jacket='40706a', shirt='f8f8f8', pants='303040', skirt='305a55'),
    Char('fantome', 'bald', 'pale', 'none', jacket='c8c8e8', shirt='e8e8ff', pants='b0b0d8', shoes='9090c0'),
    # famous characters (overworld)
    Char('juncker', 'short', 'light', 'grey', jacket='283048', shirt='f8f8f8', tie='a02030', pants='283048', glasses=True),
    Char('lagarde', 'short', 'tan', 'white', jacket='f0f0f0', shirt='202020', pants='f0f0f0'),
    Char('metsola', 'long', 'light', 'gold', jacket='203060', shirt='f8f8f8', pants='203060', skirt='203060'),
    Char('varoufakis', 'bald', 'light', 'none', jacket='202020', shirt='303030', pants='303040'),
    Char('farage', 'short', 'light', 'brown', jacket='3a4a6a', shirt='f8f8f8', tie='4060c0', pants='3a3a48'),
    Char('johnson', 'spiky', 'pale', 'blonde', jacket='202838', shirt='f8f8f8', tie='4060c0', pants='202838'),
    Char('orban', 'short', 'light', 'dkbrown', jacket='202a48', shirt='f8f8f8', tie='a02020', pants='202a48'),
    Char('vestager', 'short', 'pale', 'grey', jacket='a0a8b0', shirt='f8f8f8', pants='505860', skirt='505860'),
    Char('macron', 'short', 'light', 'dkbrown', jacket='1a2240', shirt='f8f8f8', tie='1a2240', pants='1a2240'),
    Char('merkel', 'bob', 'light', 'ash', jacket='d04040', shirt='202020', pants='202030'),
    Char('draghi', 'short', 'light', 'grey', jacket='2a2a38', shirt='e8f0f8', tie='3a4a8a', pants='2a2a38'),
    Char('kallas', 'long', 'pale', 'ash', jacket='2a3a6a', shirt='f8f8f8', pants='2a3a6a', skirt='2a3a6a'),
    Char('costa', 'bald', 'brown', 'grey', jacket='303848', shirt='f8f8f8', tie='40a060', pants='303848', glasses=True),
    Char('vdl', 'bob', 'light', 'blonde', jacket='e8a0b8', shirt='f8f0e8', pants='f0e0d0', skirt='e8a0b8'),
    Char('michel', 'bald', 'light', 'dkbrown', jacket='2a3048', shirt='f8f8f8', tie='4a5a9a', pants='2a3048'),
    Char('trump', 'bob', 'orange', 'gold', jacket='1e2a50', shirt='f8f8f8', tie='e02020', pants='1e2a50'),
    Char('putin', 'bald', 'pale', 'ash', jacket='2a2a32', shirt='f8f8f8', tie='6a2a2a', pants='2a2a32'),
    Char('xi', 'short', 'light', 'black', jacket='2a2a3a', shirt='f8f8f8', tie='a02020', pants='2a2a3a'),
    Char('zelensky', 'short', 'light', 'dkbrown', jacket='4a5a3a', shirt='4a5a3a', pants='3a4a2a'),
    Char('musk', 'short', 'light', 'dkbrown', jacket='202020', shirt='202020', pants='303030'),
    Char('erdogan', 'bald', 'tan', 'grey', jacket='2a3048', shirt='f8f8f8', tie='a03030', pants='2a3048'),
    Char('barnier', 'short', 'pale', 'white', jacket='2a3448', shirt='f8f8f8', tie='4a6aba', pants='2a3448'),
    Char('breton', 'spiky', 'pale', 'grey', jacket='303848', shirt='f8f8f8', tie='2a2a5a', pants='303848'),
    Char('lepen', 'long', 'light', 'blonde', jacket='1e2a5a', shirt='f8f8f8', pants='1e2a5a'),
    Char('bardella', 'short', 'light', 'black', jacket='1e2a5a', shirt='f8f8f8', tie='1e2a5a', pants='1e2a5a'),
    Char('bayrou', 'short', 'pale', 'grey', jacket='3a3a48', shirt='f8f8f8', tie='e07020', pants='3a3a48'),
    Char('kaili', 'long', 'light', 'blonde', jacket='202020', shirt='f8f8f8', pants='202020', skirt='202020'),
    Char('selmayr', 'short', 'light', 'brown', jacket='303840', shirt='f8f8f8', tie='303840', pants='303840'),
    Char('delors', 'bald', 'pale', 'grey', jacket='3a3a3a', shirt='f8f8f8', tie='5a2a2a', pants='3a3a3a', glasses=True),
    Char('veil', 'bun', 'pale', 'dkbrown', jacket='6a2a3a', shirt='f8f8f8', pants='3a2a2a', skirt='6a2a3a'),
    Char('schauble', 'bald', 'pale', 'white', jacket='303040', shirt='f8f8f8', tie='4a4a8a', pants='303040', glasses=True),
    Char('rutte', 'short', 'light', 'brown', jacket='283048', shirt='f8f8f8', tie='e07020', pants='283048'),
    Char('vance', 'short', 'light', 'dkbrown', jacket='1e2a50', shirt='f8f8f8', tie='4060c0', pants='1e2a50'),
    Char('lobbychef', 'bald', 'pale', 'black', jacket='101018', shirt='101018', tie='e0b020', pants='101018', glasses=True),
    # city extensions
    Char('graveuse', 'bun', 'tan', 'black', jacket='e8e4dc', shirt='2a3a5a', pants='3a3a48', skirt='4a4a5a', glasses=True),
    Char('wirtin', 'bun', 'light', 'brown', jacket='3a6a3a', shirt='f8f8f8', pants='303040', skirt='2a4a2a'),
]


def main(out_dir=None):
    import mkgfx
    out_dir = out_dir or os.path.join(ROOT, 'nitrofs/chars')
    os.makedirs(out_dir, exist_ok=True)
    ids = {}
    stamp = os.path.join(out_dir, '_stamp')
    rebuild = not os.path.exists(stamp) or os.path.getmtime(__file__) > os.path.getmtime(stamp)
    for i, c in enumerate(CAST):
        ids[c.name] = i
        if not rebuild:
            continue
        frames = sheet(c)
        strip = Image.new('RGBA', (32, 32 * len(frames)))
        for k, f in enumerate(frames):
            strip.paste(f, (0, 32 * k))
        idx, pal = mkgfx.quantize_rgb(strip, 15)
        fr = [idx[k * 32:(k + 1) * 32] for k in range(len(frames))]
        mkgfx.write_spr(os.path.join(out_dir, f'{i}.spr'), fr, [0] + [mkgfx.rgb15(*p) for p in pal], 4, 32, 32)
    if rebuild:
        open(stamp, 'w').write('ok')
    import json
    os.makedirs(os.path.join(ROOT, 'build'), exist_ok=True)
    json.dump(ids, open(os.path.join(ROOT, 'build/sprite_ids.json'), 'w'), indent=0)
    return ids


if __name__ == '__main__':
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    preview = Image.new('RGBA', (32 * 12, 32 * 8), (120, 180, 120, 255))
    for i, c in enumerate(CAST[:8]):
        for k, f in enumerate(sheet(c)):
            preview.alpha_composite(f, (k * 32, i * 32))
    preview.resize((preview.width * 3, preview.height * 3), Image.NEAREST).save('/tmp/chars.png')
    p2 = Image.new('RGBA', (32 * 14, 32 * 5), (120, 180, 120, 255))
    for i, c in enumerate(CAST[8:]):
        if i >= 70:
            break
        p2.alpha_composite(compose(c, 'down', 0), ((i % 14) * 32, (i // 14) * 32))
    p2.resize((p2.width * 3, p2.height * 3), Image.NEAREST).save('/tmp/chars2.png')
