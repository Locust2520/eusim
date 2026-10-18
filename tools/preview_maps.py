#!/usr/bin/env python3
"""Render every map as the DS will show it (after palette reduction) into build/preview/maps/<id>.png,
and report colour/tile budgets. Used for asset QA."""
import glob, os, sys
import numpy as np
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import mkmaps as M  # noqa

out = os.path.join(ROOT, 'build', 'preview', 'maps')
os.makedirs(out, exist_ok=True)
M.T.build_registry()
only = sys.argv[1:]
for path in sorted(glob.glob(os.path.join(ROOT, 'assets', 'maps', '*.map'))):
    m = M.MapSrc(path)
    if only and m.id not in only:
        continue
    ground, obj, reg, doors = M.cell_images(m)
    keys = sorted(reg)
    pal, idx, ncol = M.build_palette([reg[k][0] for k in keys])
    ncols_raw = len({tuple(int(v) for v in px[:3]) for k in keys for px in np.array(reg[k][0]).reshape(-1, 4) if px[3] >= 128})
    def ds(im):
        a = np.array(im).copy()
        o = np.zeros_like(a)
        for y in range(16):
            for x in range(16):
                p = a[y, x]
                if p[3] >= 128:
                    c = pal[idx[tuple(int(v) for v in p[:3])]]
                    o[y, x] = (c[0] & 0xF8, c[1] & 0xF8, c[2] & 0xF8, 255)
        return Image.fromarray(o, 'RGBA')
    cache = {}
    img = Image.new('RGBA', (m.w * 16, m.h * 16), (0, 0, 0, 255))
    for layer in (0, 1, 2):
        for y in range(m.h):
            for x in range(m.w):
                k = ground[y][x] if layer == 0 else obj[y][x]
                if not k:
                    continue
                above = reg[k][2]
                if layer == 1 and above or layer == 2 and not above:
                    continue
                if k not in cache:
                    cache[k] = ds(reg[k][0])
                img.alpha_composite(cache[k], (x * 16, y * 16))
    img.convert('RGB').save(os.path.join(out, m.id + '.png'))
    print(f'{m.id:24s} {m.w}x{m.h} colours {ncols_raw:4d}{" QUANTIZED" if ncols_raw > 178 else ""}')
