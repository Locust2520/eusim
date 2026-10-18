#!/usr/bin/env python3
"""Open-source pixel art used by the map tiles (see assets/oss/CREDITS.md for authors and licences).

Everything here is cut from the Tuxemon tilesets (assets/oss/tuxemon/), then lightly recoloured so it
sits with the procedural tiles: the colour grade itself is applied to every tile in tiles.grade().
"""
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'assets', 'oss', 'tuxemon')

# shadows in the source are a translucent olive; ours are a translucent blue, like the reference games
SHADOW = (34, 40, 120, 96)

_cache = {}


def sheet(name):
    if name not in _cache:
        _cache[name] = Image.open(os.path.join(SRC, name)).convert('RGBA')
    return _cache[name]


def cut(name, box):
    """Crop (x, y, w, h) from a sheet; translucent shadow pixels are recoloured."""
    x, y, w, h = box
    im = sheet(name).crop((x, y, x + w, y + h))
    a = np.array(im)
    semi = (a[..., 3] > 0) & (a[..., 3] < 255)
    a[semi] = SHADOW
    return Image.fromarray(recolour_greens(a), 'RGBA')


# foliage ramp sampled from the reference shots: teal shadows (B/W), olive-yellow lights (SoulSilver)
FOLIAGE = [(0x1c, 0x50, 0x50), (0x24, 0x68, 0x5c), (0x30, 0x80, 0x5c), (0x48, 0x98, 0x50),
           (0x6c, 0xb0, 0x44), (0x94, 0xc4, 0x44), (0xc0, 0xdc, 0x68)]


def recolour_greens(a):
    """Map the source's saturated greens onto FOLIAGE by brightness."""
    a = a.copy()
    rgb_ = a[..., :3].astype(int)
    green = (a[..., 3] == 255) & (rgb_[..., 1] > rgb_[..., 0] + 20) & (rgb_[..., 1] > rgb_[..., 2] + 10)
    if not green.any():
        return a
    L = (rgb_[..., 0] * 3 + rgb_[..., 1] * 6 + rgb_[..., 2]) / 10
    lo, hi = 45, 205
    idx = np.clip(((L - lo) / (hi - lo) * (len(FOLIAGE) - 1)).round().astype(int), 0, len(FOLIAGE) - 1)
    ramp = np.array(FOLIAGE, dtype='uint8')
    a[..., :3][green] = ramp[idx[green]]
    return a


NATURE = 'core_outdoor_nature.png'


def tree(kind='round'):
    """32x48 tree, transparent background with a soft shadow at the foot."""
    x, y = {'round': (768, 0), 'round2': (800, 0), 'pine': (704, 0), 'pine2': (736, 0),
            'pine_dark': (704, 64), 'autumn': (768, 64),
            'pine_snow': (704, 128), 'round_snow': (768, 128)}[kind]
    return cut(NATURE, (x, y, 32, 48))


def small_tree(k=0):
    """16x32 sapling / shrub."""
    return cut(NATURE, (832, (0, 64)[k], 16, 32))


def bush():
    """16x16 round bush."""
    return cut(NATURE, (832, 48, 16, 16))


def rock(k=0):
    """16x16 boulders: 0 brown, 1 grey."""
    return cut(NATURE, ((656, 0), (656, 64))[k] + (16, 16))


def big_rock(k=0):
    return cut(NATURE, ((672, 32), (672, 96))[k] + (32, 32))


def stump():
    return cut(NATURE, (848, 48, 16, 16))


def flower(k=0, pair=True):
    """16x16 flower tile, transparent background. k: 0 pink, 1 blue, 2 cream, 3 red, 4 violet."""
    rows = [(0, 16), (64, 80), (96, 112), (160, 176), (208, 224)][k]
    return cut(NATURE, (944, rows[1] if pair else rows[0], 16, 16))
