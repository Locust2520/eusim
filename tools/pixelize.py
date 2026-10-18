"""Turn a 1024px AI 'pixel art' image on a magenta-ish background into a true low-res sprite.

pixelize(path, (w, h), colors, fit=...) -> PIL 'P' image, index 0 = transparent.
The background is removed by flood-filling magenta/pink pixels connected to the image border,
so pink clothes inside the character survive.
"""
from collections import deque

import numpy as np
from PIL import Image


def magenta_like(a):
    a = a.astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return (r > 120) & (b > 90) & (g < np.minimum(r, b) - 50) & (abs(r - b) < 140)


def background_mask(rgb):
    m = magenta_like(rgb)
    h, w = m.shape
    bg = np.zeros_like(m)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if m[y, x] and not bg[y, x]:
                bg[y, x] = True
                q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if m[y, x] and not bg[y, x]:
                bg[y, x] = True
                q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and m[ny, nx] and not bg[ny, nx]:
                bg[ny, nx] = True
                q.append((ny, nx))
    return bg


def _quantize(small_rgb, opaque, colors):
    pix = small_rgb[opaque]
    tmp = Image.fromarray(pix.reshape(1, -1, 3).astype('uint8'))
    q = tmp.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = q.getpalette()[:colors * 3]
    idx = np.zeros(opaque.shape, dtype='uint8')
    idx[opaque] = np.array(q).reshape(-1) + 1
    return idx, pal


def pixelize(path, size, colors=31, fit='full', margin=0, crop=None, bg_full=False):
    """fit='full': resize the whole image to size.
       fit='bbox': crop to the opaque bounding box, keep aspect, bottom-centre into size with margin."""
    im = Image.open(path).convert('RGB')
    if crop:
        im = im.crop(crop)
    arr = np.array(im)
    bg = np.zeros(arr.shape[:2], bool) if bg_full else background_mask(arr)
    w, h = size
    if fit == 'bbox':
        ys, xs = np.where(~bg)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        bw, bh = x1 - x0, y1 - y0
        s = min((w - 2 * margin) / bw, (h - 2 * margin) / bh)
        tw, th = max(1, round(bw * s)), max(1, round(bh * s))
        sub = im.crop((x0, y0, x1, y1)).resize((tw, th), Image.BOX)
        subm = Image.fromarray((~bg[y0:y1, x0:x1] * 255).astype('uint8')).resize((tw, th), Image.BOX)
        canvas = np.zeros((h, w, 3), 'uint8')
        mask = np.zeros((h, w), bool)
        ox = (w - tw) // 2
        oy = h - margin - th
        canvas[oy:oy + th, ox:ox + tw] = np.array(sub)
        mask[oy:oy + th, ox:ox + tw] = np.array(subm) > 127
        small, opaque = canvas, mask
    else:
        small = np.array(im.resize((w, h), Image.BOX))
        m = Image.fromarray((~bg * 255).astype('uint8')).resize((w, h), Image.BOX)
        opaque = np.array(m) > 127
    if not opaque.any():
        raise ValueError('empty sprite ' + path)
    idx, pal = _quantize(small, opaque, colors)
    out = Image.fromarray(idx, 'P')
    out.putpalette([255, 0, 255] + pal + [0] * (768 - 3 - len(pal)))
    return out


def add_outline(img, rgb=(24, 16, 32)):
    """Add a 1px dark outline around the opaque area, using (or adding) a palette entry."""
    a = np.array(img)
    pal = img.getpalette()
    m = a > 0
    o = np.zeros_like(m)
    o[1:, :] |= m[:-1, :]
    o[:-1, :] |= m[1:, :]
    o[:, 1:] |= m[:, :-1]
    o[:, :-1] |= m[:, 1:]
    used = int(a.max())
    idx = used + 1
    if idx > 255:
        return img
    pal[idx * 3:idx * 3 + 3] = list(rgb)
    a[o & ~m] = idx
    r = Image.fromarray(a, 'P')
    r.putpalette(pal)
    return r


def to_rgb15(pal, n):
    out = []
    for i in range(n):
        r, g, b = pal[i * 3:i * 3 + 3]
        out.append((r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10))
    return out


if __name__ == '__main__':
    import sys
    src, w, h, c, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    fit = sys.argv[6] if len(sys.argv) > 6 else 'full'
    p = pixelize(src, (w, h), c, fit=fit, margin=2)
    p.save(out)
    p.convert('RGB').resize((w * 4, h * 4), Image.NEAREST).save(out.replace('.png', '_x4.png'))
