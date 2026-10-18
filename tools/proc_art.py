#!/usr/bin/env python3
"""Procedural pixel art: title screen, loading screen, UI sprites."""
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NITRO = os.path.join(ROOT, 'nitrofs')
FONTS = os.path.join(ROOT, 'assets/fonts')
PREVIEW = os.path.join(ROOT, 'build/preview')

import mkgfx  # noqa: E402

GOLD = [(255, 248, 176), (255, 228, 96), (255, 204, 0), (232, 160, 0), (184, 112, 0)]
NAVY = (12, 20, 64)


def star_points(cx, cy, r_out, r_in, rot=-math.pi / 2):
    pts = []
    for i in range(10):
        r = r_out if i % 2 == 0 else r_in
        a = rot + i * math.pi / 5
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def draw_star_sprite(size=16, colors=GOLD, outline=(120, 72, 0)):
    s = 8
    big = Image.new('RGBA', (size * s, size * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    c = size * s / 2
    d.polygon(star_points(c, c + s * 0.5, size * s * 0.48, size * s * 0.2), fill=outline)
    d.polygon(star_points(c, c + s * 0.5, size * s * 0.40, size * s * 0.16), fill=colors[2])
    d.polygon(star_points(c - s * 0.6, c - s * 0.2, size * s * 0.22, size * s * 0.09), fill=colors[1])
    d.ellipse([c - s * 2.2, c - s * 2.6, c - s * 0.6, c - s * 1.0], fill=colors[0])
    img = big.resize((size, size), Image.NEAREST)
    return img


def logo_image():
    """'EU SIMULATOR' logo, gold letters, navy outline, drop shadow."""
    font = ImageFont.truetype(os.path.join(FONTS, 'Jersey10-Regular.ttf'), 20)
    def render(text, scale, letter_gap=0):
        if letter_gap:
            # Space visible glyphs before scaling: the font's default advances
            # let adjacent letters (especially O/R) merge at this pixel size.
            glyphs = [render(char, 1) for char in text]
            im = Image.new('L', (sum(g.width for g in glyphs) +
                                 letter_gap * (len(glyphs) - 1),
                                 max(g.height for g in glyphs)), 0)
            x = 0
            for glyph in glyphs:
                im.paste(glyph, (x, 0))
                x += glyph.width + letter_gap
        else:
            tw = int(font.getlength(text)) + 4
            im = Image.new('L', (tw, 24), 0)
            ImageDraw.Draw(im).text((2, 0), text, font=font, fill=255)
            im = im.point(lambda v: 255 if v > 100 else 0)
        bb = im.getbbox()
        im = im.crop(bb)
        if text == 'O':
            # A wider, rectangular counter stays open after the 2px outline
            # at the SIMULATOR row's 2x scale, matching the cover lettering.
            im = Image.new('L', (10, 11), 255)
            draw = ImageDraw.Draw(im)
            draw.rectangle((3, 3, 6, 7), fill=0)
            for corner in ((0, 0), (9, 0), (0, 10), (9, 10)):
                draw.point(corner, fill=0)
        return im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    eu = render('EU', 4)
    sim = render('SIMULATOR', 2, letter_gap=2)
    W = max(eu.width, sim.width) + 12
    H = eu.height + sim.height + 16
    mask = Image.new('L', (W, H), 0)
    mask.paste(eu, ((W - eu.width) // 2, 2))
    mask.paste(sim, ((W - sim.width) // 2, eu.height + 10))
    m = np.array(mask) > 0
    out = np.zeros((H, W, 4), 'uint8')
    # outline 2px + shadow
    def dil(a, r):
        o = a.copy()
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                o |= np.roll(np.roll(a, dy, 0), dx, 1)
        return o
    shadow = np.roll(np.roll(dil(m, 2), 3, 0), 2, 1)
    out[shadow] = (4, 8, 32, 255)
    ol = dil(m, 2)
    out[ol] = (*NAVY, 255)
    ol1 = dil(m, 1)
    out[ol1 & ~m] = (40, 64, 160, 255)
    # gold vertical gradient per letter row band
    ys, xs = np.where(m)
    top = {}
    for y in range(H):
        pass
    for y, x in zip(ys, xs):
        # gradient relative to the word block
        if y < eu.height + 6:
            t = (y - 2) / max(1, eu.height)
        else:
            t = (y - eu.height - 10) / max(1, sim.height)
        k = min(4, max(0, int(t * 5)))
        out[y, x] = (*GOLD[k], 255)
    # highlight line on top edge of letters
    edge = m & ~np.roll(m, 1, 0)
    out[edge] = (255, 255, 230, 255)
    return Image.fromarray(out, 'RGBA')


def title_top_bg():
    """Night sky over the Brussels European quarter (silhouettes), 256x192."""
    W, H = 256, 192
    im = Image.new('RGB', (W, H))
    d = ImageDraw.Draw(im)
    sky = [(8, 12, 48), (16, 24, 80), (32, 36, 112), (64, 48, 128), (112, 64, 136), (168, 88, 120), (216, 128, 112)]
    band_h = [44, 28, 22, 18, 14, 12, 54]
    y = 0
    for i, (c, bh) in enumerate(zip(sky, band_h)):
        d.rectangle([0, y, W, y + bh], fill=c)
        # dithered transition
        if i + 1 < len(sky):
            for x in range(0, W, 2):
                d.point((x + (y // 2) % 2, y + bh - 1), fill=sky[i + 1])
                d.point((x + 1 - (y // 2) % 2, y + bh - 2), fill=sky[i + 1]) if (x // 2) % 2 else None
        y += bh
    rnd = random.Random(7)
    for _ in range(70):
        x, yy = rnd.randrange(W), rnd.randrange(100)
        d.point((x, yy), fill=(200, 210, 255) if rnd.random() < 0.7 else (255, 230, 150))
    far = (40, 32, 88)
    near = (16, 12, 44)
    nearer = (8, 6, 24)
    # far skyline blocks
    x = 0
    while x < W:
        w = rnd.randrange(10, 26)
        h = rnd.randrange(14, 34)
        d.rectangle([x, 160 - h, x + w, 192], fill=far)
        x += w + rnd.randrange(0, 4)
    # Atomium (left)
    ax, ay = 40, 112
    pts = [(0, 0), (-14, 12), (14, 12), (0, 24), (-14, -12 + 24 + 12), (14, 36), (0, 48), (-14, 24 + 12 - 24), (14, 0)]
    nodes = [(ax, ay), (ax - 15, ay + 13), (ax + 15, ay + 13), (ax, ay + 26), (ax - 15, ay + 39), (ax + 15, ay + 39),
             (ax, ay + 52), (ax - 15, ay + 13 + 26 - 26), (ax + 15, ay + 13)]
    nodes = [(ax, ay), (ax - 15, ay + 13), (ax + 15, ay + 13), (ax, ay + 26), (ax - 15, ay + 39), (ax + 15, ay + 39), (ax, ay + 52)]
    for a in nodes:
        for b in nodes:
            if a < b and math.dist(a, b) < 30:
                d.line([a, b], fill=near, width=2)
    for (nx, ny) in nodes:
        d.ellipse([nx - 6, ny - 6, nx + 6, ny + 6], fill=near)
        d.ellipse([nx - 4, ny - 5, nx - 1, ny - 2], fill=(56, 48, 104))
    d.rectangle([ax - 2, ay + 52, ax + 2, 192], fill=near)
    # Berlaymont (centre-right): wide low cross building with louvers
    bx, by = 120, 128
    d.rectangle([bx, by, bx + 96, 192], fill=near)
    d.rectangle([bx + 34, by - 14, bx + 62, 192], fill=near)
    for yy in range(by + 4, 186, 4):
        d.line([(bx + 2, yy), (bx + 94, yy)], fill=(36, 32, 84))
    for yy in range(by - 10, 186, 4):
        d.line([(bx + 36, yy), (bx + 60, yy)], fill=(44, 40, 96))
    # lit windows
    for _ in range(40):
        wx, wy = rnd.randrange(bx + 3, bx + 93), rnd.randrange(by + 4, 186)
        if (wy - by) % 4 == 2:
            d.point((wx, wy), fill=(255, 220, 120))
    # flags row foreground
    for i in range(9):
        fx = 8 + i * 30
        d.line([(fx, 150), (fx, 192)], fill=nearer, width=1)
        d.rectangle([fx + 1, 150, fx + 13, 158], fill=(0, 51, 153))
        for k in range(6):
            a = k * math.pi / 3
            d.point((fx + 7 + 3 * math.cos(a), 154 + 3 * math.sin(a)), fill=(255, 204, 0))
    d.rectangle([0, 182, W, 192], fill=nearer)
    return im


def title_layers():
    """Title screen split in layers: sky (BG2), drifting stars (BG0, 256x256 seamless), skyline (BG1)."""
    full = title_top_bg()
    W, H = 256, 192
    # sky: pure gradient part of the full image without the stars and silhouettes
    sky = Image.new('RGB', (W, H))
    d = ImageDraw.Draw(sky)
    cols = [(6, 10, 40), (10, 16, 58), (18, 24, 80), (34, 34, 108), (62, 46, 126), (108, 62, 134), (160, 84, 122), (210, 122, 112)]
    hs = [30, 24, 22, 20, 18, 16, 14, 48]
    y = 0
    for i, (c, h) in enumerate(zip(cols, hs)):
        d.rectangle([0, y, W, y + h], fill=c)
        if i + 1 < len(cols):
            nxt = cols[i + 1]
            for x in range(W):
                if (x + y) % 2 == 0:
                    d.point((x, y + h - 1), fill=nxt)
                if (x * 3 + y) % 4 == 0:
                    d.point((x, y + h - 2), fill=nxt)
        y += h
    # skyline: take the silhouettes of the full image (everything darker than the sky below y=100)
    import numpy as np
    a = np.array(full).astype(int)
    s = np.array(sky).astype(int)
    sk = np.zeros((H, W, 4), 'uint8')
    diff = np.abs(a - s).sum(axis=2)
    yy = np.arange(H)[:, None].repeat(W, 1)
    mask = (diff > 30) & (yy >= 96)
    sk[mask, :3] = a[mask]
    sk[mask, 3] = 255
    skyline = Image.fromarray(sk, 'RGBA')
    # stars layer, seamless 256x256 with a few bright twinkles and many faint ones
    st = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    rnd = random.Random(42)
    for _ in range(110):
        x, yv = rnd.randrange(256), rnd.randrange(256)
        c = rnd.choice([(150, 160, 220), (200, 210, 255), (255, 236, 170), (120, 130, 190)])
        st.putpixel((x, yv), c + (255,))
    for _ in range(14):
        x, yv = rnd.randrange(2, 254), rnd.randrange(2, 254)
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            st.putpixel((x + dx, yv + dy), (255, 255, 230, 255) if (dx, dy) == (0, 0) else (190, 200, 255, 255))
    # AI art (assets/art/ui, see tools/postprocess_images.py) replaces the drawn sky and skyline when present
    ai_sky = os.path.join(ROOT, 'assets/art/ui/title_sky.png')
    ai_line = os.path.join(ROOT, 'assets/art/ui/title_skyline.png')
    # (the AI sky is not used: with the skyline and the star layer it would exceed the 1024 BG tiles)
    if os.path.exists(ai_line):
        src = np.array(Image.open(ai_line).convert('RGB').resize((W, 171), Image.BOX)).astype(int)
        r, g, b = src[..., 0], src[..., 1], src[..., 2]
        bg = (r > 120) & (b > 90) & (g < np.minimum(r, b) - 50)
        sk = np.zeros((H, W, 4), 'uint8')
        sk[H - 171:, :, :3] = src
        sk[H - 171:, :, 3] = np.where(bg, 0, 255)
        skyline = Image.fromarray(sk, 'RGBA')
    return sky, st, skyline


def beam_sprite():
    """Searchlight beam, 32x64: narrow at the bottom, wide and faint at the top (drawn semi-transparent)."""
    im = Image.new('RGBA', (32, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for yv in range(64):
        half = 1 + (63 - yv) * 15 // 63
        c = (255, 255, 236) if yv > 40 else (255, 248, 210) if yv > 16 else (236, 232, 200)
        d.line([(16 - half, yv), (15 + half, yv)], fill=c + (255,))
    return im


def bottom_pattern():
    """Bottom title/menus backdrop tile pattern: deep blue with small stars (seamless 256x256)."""
    W, H = 256, 256
    im = Image.new('RGB', (W, H), (0, 40, 120))
    d = ImageDraw.Draw(im)
    for y in range(0, H, 16):
        for x in range(0, W, 16):
            if (x // 16 + y // 16) % 2 == 0:
                d.rectangle([x, y, x + 15, y + 15], fill=(0, 46, 136))
    for y in range(4, H, 32):
        for x in range(4, W, 32):
            ox = 16 if (y // 32) % 2 else 0
            cx, cy = (x + ox) % W, y
            d.point((cx + 3, cy + 1), fill=(255, 204, 0))
            d.line([(cx + 2, cy + 2), (cx + 4, cy + 2)], fill=(255, 204, 0))
            d.point((cx + 3, cy + 3), fill=(255, 204, 0))
    return im


def sofa_sprite():
    im = Image.new('RGBA', (32, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([2, 2, 29, 9], fill=(150, 40, 40))
    d.rectangle([0, 6, 31, 13], fill=(180, 52, 52))
    d.rectangle([4, 8, 27, 11], fill=(210, 80, 72))
    d.rectangle([1, 13, 3, 15], fill=(60, 30, 20))
    d.rectangle([28, 13, 30, 15], fill=(60, 30, 20))
    d.line([(2, 2), (29, 2)], fill=(200, 90, 90))
    return im


def battle_bg(kind):
    """256x192 battle backdrop with two platforms (foe top-right, ally bottom-left)."""
    W, H = 256, 192
    im = Image.new('RGB', (W, H))
    d = ImageDraw.Draw(im)
    if kind == 'grass':
        sky = [(150, 208, 248), (176, 220, 248), (200, 232, 248)]
        ground = (120, 200, 96); g2 = (96, 176, 80); plat = (176, 216, 120); plat2 = (136, 184, 96)
    elif kind == 'indoor':
        sky = [(212, 204, 188), (224, 216, 200), (232, 226, 212)]
        ground = (176, 140, 96); g2 = (156, 120, 80); plat = (64, 96, 176); plat2 = (40, 64, 140)
    elif kind == 'hemicycle':
        sky = [(40, 56, 120), (56, 72, 140), (72, 88, 160)]
        ground = (48, 72, 160); g2 = (36, 56, 136); plat = (200, 160, 80); plat2 = (160, 120, 56)
    elif kind == 'city':
        sky = [(176, 200, 232), (196, 212, 236), (216, 224, 240)]
        ground = (168, 168, 176); g2 = (148, 148, 160); plat = (200, 200, 208); plat2 = (150, 150, 160)
    else:  # night
        sky = [(16, 20, 56), (28, 32, 80), (48, 40, 96)]
        ground = (40, 56, 72); g2 = (28, 40, 56); plat = (88, 96, 120); plat2 = (60, 66, 90)
    bands = [40, 30, 30]
    y = 0
    for c, bh in zip(sky, bands):
        d.rectangle([0, y, W, y + bh], fill=c)
        y += bh
    d.rectangle([0, 100, W, H], fill=ground)
    for yy in range(104, H, 6):
        d.line([(0, yy), (W, yy)], fill=g2)
    if kind == 'grass':
        for x in range(0, W, 24):
            d.ellipse([x - 10, 82, x + 26, 108], fill=(80, 160, 72))
        rnd = random.Random(2)
        for _ in range(5):
            cx, cy = rnd.randrange(W), rnd.randrange(10, 60)
            d.ellipse([cx - 14, cy - 5, cx + 14, cy + 5], fill=(248, 248, 255))
    elif kind == 'indoor':
        for x in range(8, W, 48):
            d.rectangle([x, 20, x + 30, 60], fill=(120, 160, 200)); d.rectangle([x + 2, 22, x + 28, 58], fill=(180, 210, 240))
        d.rectangle([0, 92, W, 100], fill=(140, 110, 80))
    elif kind == 'hemicycle':
        for r in range(6):
            d.arc([-40 - r * 30, 30 - r * 6, W + 40 + r * 30, 220 + r * 10], 190, 350, fill=(70 + r * 12, 90 + r * 10, 170), width=6)
        for k in range(12):
            a = math.pi + k * math.pi / 11
            d.point((128 + 70 * math.cos(a), 40 + 20 * math.sin(a) + 30), fill=(255, 204, 0))
    elif kind == 'city':
        rnd = random.Random(4)
        x = 0
        while x < W:
            w = rnd.randrange(16, 34); h = rnd.randrange(30, 70)
            d.rectangle([x, 100 - h, x + w, 100], fill=(140, 150, 170))
            for wy in range(100 - h + 4, 96, 6):
                for wx in range(x + 3, x + w - 3, 5):
                    d.point((wx, wy), fill=(230, 230, 180))
            x += w + 2
    else:
        rnd = random.Random(9)
        for _ in range(50):
            d.point((rnd.randrange(W), rnd.randrange(90)), fill=(220, 220, 255))
        d.ellipse([200, 14, 222, 36], fill=(250, 240, 200))
    # platforms
    d.ellipse([136, 70, 252, 102], fill=plat2); d.ellipse([140, 70, 248, 98], fill=plat)
    d.ellipse([4, 150, 136, 190], fill=plat2); d.ellipse([8, 150, 132, 186], fill=plat)
    return im


def preview(name, im, scale=2):
    os.makedirs(PREVIEW, exist_ok=True)
    im.convert('RGBA').resize((im.width * scale, im.height * scale), Image.NEAREST).save(os.path.join(PREVIEW, name + '.png'))


def sprite_sheet_rgba(frames, path, bpp=8, maxc=255):
    """frames: list of RGBA images same size -> .spr with shared palette"""
    w, h = frames[0].size
    strip = Image.new('RGBA', (w, h * len(frames)))
    for i, f in enumerate(frames):
        strip.paste(f, (0, i * h))
    idx, pal = mkgfx.quantize_rgb(strip, maxc if bpp == 8 else 15)
    fr = [idx[i * h:(i + 1) * h] for i in range(len(frames))]
    mkgfx.write_spr(path, fr, [0] + [mkgfx.rgb15(*c) for c in pal], bpp, w, h)


def main():
    out_ui = os.path.join(NITRO, 'ui')
    os.makedirs(out_ui, exist_ok=True)
    stamp = os.path.join(out_ui, 'title_top.bgi')
    if not os.path.exists(stamp) or os.path.getmtime(__file__) > os.path.getmtime(stamp):
        top = title_top_bg()
        idx, pal = mkgfx.quantize_rgb(top, 120)
        mkgfx.write_bg(stamp, idx, pal, 1)
        preview('title_top', top)
        bot = bottom_pattern()
        idx, pal = mkgfx.quantize_rgb(bot, 16)
        mkgfx.write_bg(os.path.join(out_ui, 'pattern.bgi'), idx, pal, 1)
        logo = logo_image()
        idx, pal = mkgfx.quantize_rgb(logo, 31)
        mkgfx.write_bmp8(os.path.join(out_ui, 'logo.bmp8'), idx, pal)
        preview('logo', logo)
        stars = [draw_star_sprite(16)]
        # dim trail star and highlighted star
        dim = draw_star_sprite(16, colors=[(200, 180, 120), (180, 150, 60), (150, 120, 20), (120, 90, 10), (90, 60, 0)], outline=(70, 40, 0))
        bright = draw_star_sprite(16, colors=[(255, 255, 255), (255, 255, 200), (255, 240, 120), (255, 200, 60), (220, 140, 0)], outline=(160, 96, 0))
        sofa = sofa_sprite()
        sofa_pad = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
        sprite_sheet_rgba([stars[0], dim, bright], os.path.join(out_ui, 'stars.spr'))
        s32 = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
        s32.paste(sofa, (0, 16))
        sprite_sheet_rgba([s32], os.path.join(out_ui, 'sofa.spr'))
        preview('star', stars[0], 4)
    stamp2 = os.path.join(out_ui, 'title_sky.bgi')
    if not os.path.exists(stamp2) or os.path.getmtime(__file__) > os.path.getmtime(stamp2):
        sky, st, skyline = title_layers()
        idx, pal = mkgfx.quantize_rgb(sky, 40)
        mkgfx.write_bg(stamp2, idx, pal, 1)
        idx, pal = mkgfx.quantize_rgb(st, 8)
        mkgfx.write_bg(os.path.join(out_ui, 'title_stars.bgi'), idx, pal, 41)
        idx, pal = mkgfx.quantize_rgb(skyline, 100)
        mkgfx.write_bg(os.path.join(out_ui, 'title_skyline.bgi'), idx, pal, 50)
        sprite_sheet_rgba([beam_sprite()], os.path.join(out_ui, 'beam.spr'))
        comp = sky.convert('RGBA')
        comp.alpha_composite(st.crop((0, 0, 256, 192)))
        comp.alpha_composite(skyline)
        preview('title_layers', comp)
    for kind in ('grass', 'indoor', 'hemicycle', 'city', 'night'):
        path = os.path.join(out_ui, f'bt_{kind}.bgi')
        if not os.path.exists(path) or os.path.getmtime(__file__) > os.path.getmtime(path):
            ai = os.path.join(ROOT, f'assets/art/ui/bt_{kind}.png')
            if os.path.exists(ai):
                im = Image.open(ai).convert('RGB').resize((256, 192), Image.BOX)
                idx, pal = mkgfx.quantize_rgb(im, 160)
            else:
                im = battle_bg(kind)
                idx, pal = mkgfx.quantize_rgb(im, 60)
            mkgfx.write_bg(path, idx, pal, 1)
            preview('bt_' + kind, im)


if __name__ == '__main__':
    main()
