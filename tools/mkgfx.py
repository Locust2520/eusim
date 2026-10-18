#!/usr/bin/env python3
"""Convert art (assets/art, procedural art) into DS formats in nitrofs/.

.spr  : "SPR\\1" bpp fw fh 0 | u16 nframes | u16 ncolors | u16 pal[ncolors] | frames (1D tile order)
.img  : "IMG\\1" w/8 h/8 ncolors 0 | u16 pal[ncolors] | u16 map[(w/8)*(h/8)] | u16 ntiles | tiles 8bpp
        (deduplicated 8x8 tiles incl. flips; palette indices start at 1, written at load-time offset)
"""
import os
import struct
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import pixelize  # noqa: E402

NITRO = os.path.join(ROOT, 'nitrofs')


def newer(srcs, dst):
    if not os.path.exists(dst):
        return True
    t = os.path.getmtime(dst)
    return any(os.path.getmtime(s) > t for s in srcs if os.path.exists(s))


def rgb15(r, g, b):
    return (r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10)


def tiles_1d(idx, x0, y0, w, h):
    """Return list of 8x8 tiles (row-major tiles) of region as uint8 arrays."""
    out = []
    for ty in range(h // 8):
        for tx in range(w // 8):
            out.append(idx[y0 + ty * 8:y0 + ty * 8 + 8, x0 + tx * 8:x0 + tx * 8 + 8])
    return out


def pack_tiles(tiles, bpp):
    b = bytearray()
    for t in tiles:
        flat = t.reshape(-1)
        if bpp == 8:
            b += bytes(flat.astype('uint8'))
        else:
            for i in range(0, 64, 2):
                b.append((int(flat[i]) & 15) | ((int(flat[i + 1]) & 15) << 4))
    return bytes(b)


def write_spr(path, frames, pal15, bpp, fw, fh, extra=0):
    """frames: list of index arrays (fh x fw)"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = bytearray(b'SPR\x01')
    data += struct.pack('<BBBBHH', bpp, fw, fh, extra, len(frames), len(pal15))
    data += struct.pack(f'<{len(pal15)}H', *pal15)
    for f in frames:
        data += pack_tiles(tiles_1d(f, 0, 0, fw, fh), bpp)
    open(path, 'wb').write(data)


def pal_of(img, n):
    p = img.getpalette()
    out = [0]
    for i in range(1, n + 1):
        out.append(rgb15(*p[i * 3:i * 3 + 3]))
    return out


# ------------------------------------------------------------------ BG images & bitmaps
def quantize_rgb(img, ncolors, keep_transparent=False):
    """img RGB(A) -> (index array with 1..n, palette list of rgb tuples). Pixels with alpha<128 -> 0."""
    img = img.convert('RGBA')
    a = np.array(img)
    opaque = a[..., 3] >= 128
    rgb = a[..., :3]
    pix = rgb[opaque]
    if len(pix) == 0:
        return np.zeros(a.shape[:2], 'uint8'), []
    uniq = np.unique(pix.reshape(-1, 3), axis=0)
    if len(uniq) <= ncolors:
        pal = [tuple(int(v) for v in c) for c in uniq]
        lut = {c: i + 1 for i, c in enumerate(pal)}
        idx = np.zeros(a.shape[:2], 'uint8')
        ys, xs = np.where(opaque)
        for y, x in zip(ys, xs):
            idx[y, x] = lut[tuple(int(v) for v in rgb[y, x])]
        return idx, pal
    tmp = Image.fromarray(pix.reshape(1, -1, 3).astype('uint8'))
    q = tmp.quantize(colors=ncolors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    p = q.getpalette()
    pal = [tuple(p[i * 3:i * 3 + 3]) for i in range(ncolors)]
    idx = np.zeros(a.shape[:2], 'uint8')
    idx[opaque] = np.array(q).reshape(-1) + 1
    return idx, pal


def write_bmp8(path, idx, pal):
    """Canvas bitmap: 'BMP8' u16 w u16 h u16 ncol | pal | pixels (0 = transparent, 1..n)"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    h, w = idx.shape
    d = bytearray(b'BMP8') + struct.pack('<HHH', w, h, len(pal))
    d += struct.pack(f'<{len(pal)}H', *[rgb15(*c) for c in pal])
    d += bytes(idx.astype('uint8').reshape(-1))
    open(path, 'wb').write(d)


def write_bg(path, idx, pal, pal_base):
    """Tiled 8bpp BG: 'BGI1' u16 wt u16 ht u16 ncol u16 pal_base | pal | u16 ntiles | tiles | u16 map[wt*ht]
    Pixel values are stored already offset by pal_base-1 (index 1 -> pal_base)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    h, w = idx.shape
    wt, ht = w // 8, h // 8
    off = np.where(idx > 0, idx.astype(int) + pal_base - 1, 0).astype('uint8')
    tiles, lut, mp = [], {}, []
    for ty in range(ht):
        for tx in range(wt):
            t = off[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            found = None
            for fl, tt in ((0, t), (1, t[:, ::-1]), (2, t[::-1, :]), (3, t[::-1, ::-1])):
                k = tt.tobytes()
                if k in lut:
                    found = (lut[k], fl)
                    break
            if found is None:
                lut[t.tobytes()] = len(tiles)
                tiles.append(t)
                found = (len(tiles) - 1, 0)
            ti, fl = found
            mp.append(ti | ((fl & 1) << 10) | ((fl >> 1) << 11))
    d = bytearray(b'BGI1') + struct.pack('<HHHH', wt, ht, len(pal), pal_base)
    d += struct.pack(f'<{len(pal)}H', *[rgb15(*c) for c in pal])
    d += struct.pack('<H', len(tiles))
    for t in tiles:
        d += bytes(t.reshape(-1))
    d += struct.pack(f'<{len(mp)}H', *mp)
    open(path, 'wb').write(d)
    return len(tiles)


# ------------------------------------------------------------------ portraits
# Checked by eye on every portrait (the automatic guess below is wrong for about a third of them).
FACING = {
    'alex': 1, 'bardella': 0, 'barnier': 2, 'bayrou': 0, 'berlusconi': 2, 'borrell': 2, 'bourla': 2, 'breton': 2,
    'cantiniere': 1, 'costa': 2, 'delors': 2, 'draghi': 2, 'erdogan': 2, 'farage': 2, 'johnson': 1, 'juncker': 2,
    'kaili': 1, 'kallas': 2, 'lagarde': 1, 'lepen': 1, 'macron': 2, 'magyar': 1, 'max': 1, 'meloni': 1,
    'merkel': 2, 'merz': 1, 'metsola': 1, 'michel': 2, 'monnet': 2, 'musk': 1, 'oliver': 1, 'orban': 2,
    'panzeri': 1, 'putin': 0, 'rutte': 0, 'sanchez': 2, 'schauble': 1, 'scholz': 1, 'schulz': 2, 'schuman': 1,
    'selmayr': 2, 'timmermans': 2, 'trump': 1, 'tsipras': 2, 'tusk': 0, 'vance': 0, 'varoufakis': 1, 'vdl': 1,
    'veil': 1, 'verhofstadt': 1, 'vestager': 2, 'xi': 0, 'zelensky': 0,
}


def portrait_facing(path):
    """0 = front, 1 = turned towards the viewer's right, 2 = towards the left."""
    who = os.path.basename(path).rsplit('_', 1)[0]
    if who in FACING:
        return FACING[who]
    if not os.path.exists(path):
        return 0
    a = np.array(Image.open(path).convert('RGB')).astype(int)
    bg = pixelize.background_mask(a.astype('uint8'))
    H, W = bg.shape
    top = slice(int(H * 0.15), int(H * 0.6))
    fg = ~bg[top]
    r, g, b = a[top][..., 0], a[top][..., 1], a[top][..., 2]
    skin = fg & (r > 140) & (r > g + 15) & (g > b) & (r - b > 40)
    ys, xs = np.where(fg)
    sy, sx = np.where(skin)
    if len(sx) < 50:
        return 0
    d = (sx.mean() - xs.mean()) / W
    return 1 if d > 0.008 else 2 if d < -0.008 else 0


def build_portraits():
    src = os.path.join(ROOT, 'assets/art/portraits')
    if not os.path.isdir(src):
        return
    n = 0
    for f in sorted(os.listdir(src)):
        if not f.endswith('.png'):
            continue
        out = os.path.join(NITRO, 'portraits', f[:-4] + '.spr')
        if not newer([os.path.join(src, f), __file__, pixelize.__file__], out):
            continue
        img = pixelize.pixelize(os.path.join(src, f), (96, 96), colors=40)
        facing = portrait_facing(os.path.join(src, f.rsplit('_', 1)[0] + '_neutral.png'))
        a = np.array(img)
        ncol = int(a.max())
        frames = [a[y * 32:(y + 1) * 32, x * 32:(x + 1) * 32] for y in range(3) for x in range(3)]
        write_spr(out, frames, pal_of(img, ncol), 8, 32, 32, facing)
        n += 1
    # characters without a photo-based portrait: use their chibi sprite, scaled x3 (retro "mugshot")
    import proc_chars
    have = {f.rsplit('_', 1)[0] for f in os.listdir(src) if f.endswith('.png')}
    for c in proc_chars.CAST:
        if c.name in have:
            continue
        out = os.path.join(NITRO, 'portraits', c.name + '_neutral.spr')
        if not newer([proc_chars.__file__, __file__], out):
            continue
        fr = proc_chars.compose(c, 'down', 0).crop((0, 0, 32, 32)).resize((96, 96), Image.NEAREST)
        idx, pal = quantize_rgb(fr, 31)
        frames = [idx[y * 32:(y + 1) * 32, x * 32:(x + 1) * 32] for y in range(3) for x in range(3)]
        write_spr(out, frames, [0] + [rgb15(*p) for p in pal], 8, 32, 32, 0)
        n += 1
    if n:
        print('portraits', n)


def main():
    build_portraits()
    import proc_art
    proc_art.main()


if __name__ == '__main__':
    main()
