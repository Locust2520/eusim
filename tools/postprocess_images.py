#!/usr/bin/env python3
"""Post-process the AI images listed in eusim_images.json so they can be dropped straight into the game.

Usage:
    pip install pillow numpy
    python3 tools/postprocess_images.py eusim_images.json RAW_DIR OUT_DIR
    cd OUT_DIR && zip -r ../eusim_art.zip .

RAW_DIR holds the generator's outputs, one file per manifest entry, named after its "name" field
(pt_schuman_happy.png, cs_s08_brexit_05_adieu_alex.png, ui_bt_grass.png; .png, .jpg and .webp are accepted).
OUT_DIR receives the files at the path given by each entry's "out" field (assets/art/...), plus report.csv.

What happens to each kind of image:
  portrait  1024x1024 on magenta -> background forced to pure #FF00FF (near-magenta noise and anti-aliased
            fringes cleaned), resized to 384x384. The game's build turns it into a 96x96 sprite later.
  slide     1536x1024 scene      -> centre-cropped to exactly 3:2, area-downsampled to 384x256, reduced to
            128 colours without dithering (crisp pixel-art look, the build makes the final DS palette).
  ui        title sky            -> 384x256, 128 colours, like a slide
            title skyline        -> 384x256, magenta background cleaned (it is a transparent overlay)
            battle backgrounds   -> centre-cropped to 4:3, 256x192, 128 colours
            europe map           -> centre-cropped to 4:3, 256x192, 64 colours
report.csv lists every entry with its status (ok / missing / warning) so gaps are easy to spot.
"""
import csv
import json
import os
import sys

import numpy as np
from PIL import Image

MAGENTA = np.array([255, 0, 255])


def find_raw(raw_dir, name):
    for ext in ('.png', '.jpg', '.jpeg', '.webp'):
        p = os.path.join(raw_dir, name + ext)
        if os.path.exists(p):
            return p
    return None


def magenta_like(a):
    """Magenta/pink-ish pixels (the generator rarely gives a perfectly flat #FF00FF)."""
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    return (r > 120) & (b > 90) & (g < np.minimum(r, b) - 50) & (abs(r - b) < 140)


def border_fill(m):
    """Part of mask m connected to the image border (so pink ties or cheeks inside the bust survive)."""
    bg = np.zeros_like(m)
    bg[0, :], bg[-1, :], bg[:, 0], bg[:, -1] = m[0, :], m[-1, :], m[:, 0], m[:, -1]
    while True:
        grow = bg.copy()
        grow[1:, :] |= bg[:-1, :]
        grow[:-1, :] |= bg[1:, :]
        grow[:, 1:] |= bg[:, :-1]
        grow[:, :-1] |= bg[:, 1:]
        grow &= m
        if (grow == bg).all():
            return bg
        bg = grow


def clean_magenta(im, size):
    """Flat #FF00FF background; anti-aliased pink fringes around the subject are absorbed into it."""
    im = im.convert('RGB')
    a = np.array(im.resize(size, Image.BOX))
    m = magenta_like(a)
    edge = np.concatenate([m[0], m[-1], m[:, 0], m[:, -1]]).mean()
    if edge < 0.5:  # the generator sometimes draws a thin frame around the picture: trim it
        w, h = im.size
        k = max(4, w // 40)
        a = np.array(im.crop((k, k, w - k, h - k)).resize(size, Image.BOX))
        m = magenta_like(a)
    bg = border_fill(m)
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    fringe = (r > 110) & (b > 90) & (g < np.minimum(r, b) - 30)
    near = np.zeros_like(bg)
    near[1:, :] |= bg[:-1, :]
    near[:-1, :] |= bg[1:, :]
    near[:, 1:] |= bg[:, :-1]
    near[:, :-1] |= bg[:, 1:]
    bg |= fringe & near
    a[bg] = MAGENTA
    warn = []
    border = np.concatenate([bg[0], bg[-1], bg[:, 0], bg[:, -1]])
    if border.mean() < 0.5:
        warn.append('background is not magenta at the edges')
    if bg.mean() > 0.92:
        warn.append('almost empty image')
    elif bg.mean() < 0.15:
        warn.append('very little background (subject too big or background not magenta)')
    return Image.fromarray(a), warn


def crop_ratio(im, rw, rh):
    w, h = im.size
    if w * rh > h * rw:
        nw = h * rw // rh
        x0 = (w - nw) // 2
        return im.crop((x0, 0, x0 + nw, h))
    nh = w * rh // rw
    y0 = (h - nh) // 2
    return im.crop((0, y0, w, y0 + nh))


def pixel_scene(im, size, colors):
    im = crop_ratio(im.convert('RGB'), size[0], size[1]).resize(size, Image.BOX)
    q = im.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    return q.convert('RGB')


def process(entry, src):
    im = Image.open(src)
    name, cat = entry['name'], entry['category']
    if cat == 'portrait':
        return clean_magenta(im, (384, 384))
    if cat == 'slide':
        return pixel_scene(im, (384, 256), 128), []
    if name == 'ui_title_skyline':
        return clean_magenta(crop_ratio(im.convert('RGB'), 3, 2), (384, 256))
    if name == 'ui_title_sky':
        return pixel_scene(im, (384, 256), 128), []
    if name == 'ui_europe_map':
        return pixel_scene(im, (256, 192), 64), []
    return pixel_scene(im, (256, 192), 128), []


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    manifest, raw_dir, out_dir = sys.argv[1:]
    images = json.load(open(manifest, encoding='utf-8'))['images']
    rows, counts = [], {'ok': 0, 'warning': 0, 'missing': 0, 'error': 0}
    for e in images:
        src = find_raw(raw_dir, e['name'])
        if not src:
            rows.append((e['name'], e['out'], 'missing', ''))
            counts['missing'] += 1
            continue
        try:
            img, warn = process(e, src)
        except Exception as ex:  # a corrupt file should not stop the batch
            rows.append((e['name'], e['out'], 'error', str(ex)))
            counts['error'] += 1
            continue
        dst = os.path.join(out_dir, e['out'])
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        img.save(dst, optimize=True)
        status = 'warning' if warn else 'ok'
        counts[status] += 1
        rows.append((e['name'], e['out'], status, '; '.join(warn)))
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'report.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['name', 'out', 'status', 'note'])
        w.writerows(rows)
    print(f"{len(images)} images: {counts['ok']} ok, {counts['warning']} with warnings, "
          f"{counts['missing']} missing, {counts['error']} errors — see {os.path.join(out_dir, 'report.csv')}")


if __name__ == '__main__':
    main()
