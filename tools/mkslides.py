#!/usr/bin/env python3
"""Compile cinematic slides into nitrofs/slides/<name>.sld.

The slide list comes from tools/image_manifest.py (SCENES). For each slide, the AI picture
assets/art/slides/<name>.png (384x256, made by postprocess_images.py) is used when present; otherwise a
procedural placeholder is composed from the game's own art: a sky, a landmark drawn by tiles2.py and the
pixel portraits of the cast, facing each other.

.sld format: 'SLD1', u16 w, u16 h, u16 ncolors, u16 0, ncolors x RGB15 (palette indices 1..n), LZ77 (LZ10)
compressed w*h bytes of palette indices, starting at the next 4-byte boundary.
"""
import glob
import os
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import image_manifest as IM  # noqa: E402
import mkgfx  # noqa: E402
import pixelize  # noqa: E402
import tiles as T  # noqa: E402

W, H = 384, 256
MAXCOL = 174  # palette index 175 is the UI checkerboard grey
OUT = os.path.join(ROOT, 'nitrofs', 'slides')
ART = os.path.join(ROOT, 'assets', 'art', 'slides')

SKIES = {  # top, horizon
    'day': ((92, 150, 228), (196, 224, 248)), 'dusk': ((52, 44, 112), (248, 150, 90)),
    'night': ((8, 12, 40), (40, 56, 110)), 'dawn': ((60, 80, 150), (250, 196, 150)),
    'sepia': ((96, 70, 44), (220, 190, 140)), 'rain': ((70, 78, 92), (150, 158, 170)),
    'snow': ((150, 170, 200), (232, 238, 248)), 'purple': ((24, 8, 40), (90, 40, 110)),
}
GROUNDS = {'grass': (88, 160, 72), 'pave': (150, 150, 160), 'water': (60, 110, 200), 'snow': (236, 240, 248),
           'parquet': (150, 100, 60), 'carpet': (150, 40, 50), 'marble': (220, 214, 200), 'dark': (40, 30, 50)}
INDOOR = {'office': ((214, 206, 186), 'parquet'), 'gold': ((200, 160, 80), 'carpet'),
          'red': ((120, 30, 40), 'marble'), 'salon': ((150, 110, 70), 'parquet'), 'dark': ((40, 30, 60), 'dark')}

# scene -> (sky or 'indoor:<kind>', ground, landmark object, {slide number: (sky, ground, landmark)} overrides)
PLACE = {
    's00_prologue': ('indoor:salon', None, None, {3: ('dusk', 'grass', None), 4: ('night', 'water', None)}),
    's01_reveil': ('dawn', 'pave', 'berlaymont', {1: ('indoor:office', None, None), 3: ('day', 'pave', 'parlement_bxl')}),
    's02_labo': ('indoor:office', None, None, {}),
    's03_luxembourg': ('day', 'grass', 'cjue', {}),
    's04_schengen': ('dusk', 'water', 'boat', {}),
    's05_bce': ('night', 'pave', 'bce_tower', {}),
    's06_strasbourg': ('day', 'pave', 'louise_weiss', {}),
    's07_athenes': ('dusk', 'grass', 'acropole', {}),
    's08_brexit': ('rain', 'pave', 'westminster', {1: ('rain', 'pave', 'big_ben'), 4: ('indoor:dark', None, None)}),
    's09_budapest': ('night', 'water', 'parliament_bud', {}),
    's10_qatargate': ('dawn', 'pave', 'parlement_bxl', {2: ('indoor:dark', None, None)}),
    's11_dgcomp': ('indoor:office', None, None, {}),
    's12_tour': ('purple', 'dark', None, {}),
    's13_paris': ('dusk', 'grass', 'eiffel', {2: ('day', 'pave', 'sorbonne')}),
    's14_sofagate': ('indoor:gold', None, None, {}),
    's15_conseil': ('night', 'pave', 'europa', {2: ('indoor:office', None, None), 3: ('indoor:office', None, None)}),
    's16_champion': ('dusk', 'pave', 'berlaymont', {2: ('indoor:office', None, None)}),
    's17_puissances': ('day', 'water', 'container_red', {2: ('indoor:office', None, None)}),
    's18_anvers': ('day', 'pave', 'golf_flag', {}),
    's19_varsovie': ('indoor:red', None, None, {3: ('snow', 'snow', 'palac_kultury')}),
    's20_piree': ('day', 'water', 'container_blue', {}),
    's21_gtout': ('indoor:red', None, None, {}),
    's22_fin': ('night', 'pave', 'atomium', {2: ('indoor:gold', None, None), 5: ('night', 'water', None)}),
    's23_legendes': ('dusk', 'pave', 'campidoglio', {2: ('night', 'water', 'house_brick'), 3: ('dawn', 'water', 'jeronimos')}),
}


def lerp(a, b, k):
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


def backdrop(sky, ground):
    im = Image.new('RGB', (W, H))
    d = ImageDraw.Draw(im)
    if sky.startswith('indoor:'):
        wall, floor = INDOOR[sky[7:]]
        for y in range(H):
            d.line([(0, y), (W, y)], fill=lerp(wall, tuple(c * 3 // 4 for c in wall), y / H))
        for x in range(0, W, 48):  # wall panels
            d.rectangle([x + 6, 30, x + 42, 150], outline=tuple(c * 5 // 6 for c in wall))
        d.rectangle([0, 176, W, H], fill=GROUNDS[floor])
        for x in range(0, W, 24):
            d.line([(x, 176), (x - 30, H)], fill=tuple(c * 4 // 5 for c in GROUNDS[floor]))
        return im
    top, hor = SKIES[sky]
    for y in range(184):
        d.line([(0, y), (W, y)], fill=lerp(top, hor, (y / 184) ** 1.4))
    if sky in ('night', 'purple', 'dusk'):
        rng = np.random.default_rng(len(sky))
        for _ in range(70):
            x, y = int(rng.integers(0, W)), int(rng.integers(0, 120))
            d.point((x, y), fill=(255, 250, 220))
    g = GROUNDS[ground or 'grass']
    d.rectangle([0, 184, W, H], fill=g)
    d.line([(0, 184), (W, 184)], fill=tuple(c * 3 // 4 for c in g))
    if sky == 'rain':
        for x in range(-200, W, 9):
            d.line([(x, 0), (x + 60, 184)], fill=(170, 176, 190))
    return im


def paste_landmark(im, name):
    if not name or name not in T.OBJECTS:
        return
    o = T.OBJECTS[name].img
    k = 2 if o.height * 2 <= 176 else 1
    o = o.resize((o.width * k, o.height * k), Image.NEAREST)
    if o.width > W:
        o = o.crop(((o.width - W) // 2, 0, (o.width + W) // 2, o.height))
    im.paste(o, ((W - o.width) // 2, 188 - o.height), o)


_bust_cache = {}


def bust(who):
    if who in _bust_cache:
        return _bust_cache[who]
    src = os.path.join(ROOT, 'assets/art/portraits', who + '_neutral.png')
    b = None
    if not os.path.exists(src):
        # no portrait yet: the character's overworld chibi, scaled up (like the in-game mugshots)
        import proc_chars
        for c in proc_chars.CAST:
            if c.name == who or (who in ('alex', 'max') and c.name == ('player_f' if who == 'alex' else 'player_m')):
                fr = proc_chars.compose(c, 'down', 0).crop((0, 0, 32, 32)).convert('RGBA').resize((128, 128), Image.NEAREST)
                b = fr, 0
        _bust_cache[who] = b
        return b
    if os.path.exists(src):
        p = pixelize.pixelize(src, (96, 96), colors=40)
        a = np.array(p.convert('RGBA'))
        a[np.array(p) == 0, 3] = 0
        b = Image.fromarray(a).resize((144, 144), Image.NEAREST), mkgfx.portrait_facing(src)
    _bust_cache[who] = b
    return b


def paste_cast(im, cast):
    people = [c for c in cast if bust(c)][:4]
    n = len(people)
    if not n:
        return
    xs = {1: [W // 2], 2: [W // 2 - 80, W // 2 + 80], 3: [W // 2 - 110, W // 2, W // 2 + 110],
          4: [W // 2 - 120, W // 2 - 40, W // 2 + 40, W // 2 + 120]}[n]
    for i, who in enumerate(people):
        img, facing = bust(who)
        # face the centre of the frame: left half looks right, right half looks left
        on_left = xs[i] < W // 2
        if (on_left and facing == 2) or (not on_left and facing == 1):
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        shadow = Image.new('RGBA', img.size, (0, 0, 0, 0))
        shadow.putalpha(img.getchannel('A').point(lambda v: 90 if v else 0))
        im.paste((10, 10, 20), (xs[i] - 72 + 4, H - 144 - 6 + 4), shadow)
        im.paste(img, (xs[i] - 72, H - 144 - 6), img)


def placeholder(scene, shot, cast):
    sky, ground, mark, over = PLACE.get(scene, ('day', 'grass', None, {}))
    if shot in over:
        sky, ground, mark = over[shot]
    im = backdrop(sky, ground)
    paste_landmark(im, mark)
    paste_cast(im, cast)
    return im


def lz10(data):
    """GBA/DS BIOS LZ77 (type 0x10) compressor, greedy with a 3-byte hash chain."""
    out = bytearray(struct.pack('<I', 0x10 | (len(data) << 8)))
    n = len(data)
    i = 0
    chains = {}
    while i < n:
        flag_pos = len(out)
        out.append(0)
        flags = 0
        for bit in range(8):
            if i >= n:
                break
            best_len, best_disp = 0, 0
            if i + 3 <= n:
                key = data[i:i + 3]
                for j in reversed(chains.get(key, [])[-48:]):
                    disp = i - j
                    if disp > 4096:
                        break
                    if disp < 2:  # keep disp >= 2: safe for VRAM-style decoders too
                        continue
                    ln = 3
                    while ln < 18 and i + ln < n and data[j + ln] == data[i + ln]:
                        ln += 1
                    if ln > best_len:
                        best_len, best_disp = ln, disp
                        if ln == 18:
                            break
            if best_len >= 3:
                flags |= 0x80 >> bit
                v = ((best_len - 3) << 12) | (best_disp - 1)
                out += bytes(((v >> 8) & 0xFF, v & 0xFF))
                step = best_len
            else:
                out.append(data[i])
                step = 1
            for k in range(i, min(i + step, n - 2)):
                chains.setdefault(data[k:k + 3], []).append(k)
            i += step
        out[flag_pos] = flags
    while len(out) % 4:
        out.append(0)
    return bytes(out)


def encode(im):
    im = im.convert('RGB').resize((W, H), Image.NEAREST) if im.size != (W, H) else im.convert('RGB')
    # DS colours are 15-bit: quantise after snapping so no two palette entries collapse
    a = (np.array(im) & 0xF8).astype('uint8')
    q = Image.fromarray(a).quantize(colors=MAXCOL, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = q.getpalette()[:MAXCOL * 3]
    idx = np.array(q).astype('uint8')
    ncol = int(idx.max()) + 1
    pix = (idx + 1).astype('uint8').tobytes()
    out = bytearray(b'SLD1') + struct.pack('<HHHH', W, H, ncol, 0)
    for c in range(ncol):
        r, g, b = pal[c * 3:c * 3 + 3]
        out += struct.pack('<H', (r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10))
    while len(out) % 4:
        out += b'\0'
    out += lz10(pix)
    return bytes(out)


def main():
    T.build_registry()
    os.makedirs(OUT, exist_ok=True)
    deps = [__file__, os.path.join(ROOT, 'tools/image_manifest.py'), os.path.join(ROOT, 'tools/tiles2.py')]
    dep_t = max(os.path.getmtime(p) for p in deps)
    made = ai = 0
    names = []
    for sid, fr, shots in IM.SCENES:
        for i, (shot, cam, motion, cast, prompt, uses_player) in enumerate(shots, 1):
            for v in (['alex', 'max'] if uses_player else [None]):
                name = f'{sid}_{i:02d}_{shot}' + (f'_{v}' if v else '')
                names.append(name)
                src = os.path.join(ART, name + '.png')
                dst = os.path.join(OUT, name + '.sld')
                srcs = [src] if os.path.exists(src) else []
                newest = max([dep_t] + [os.path.getmtime(s) for s in srcs])
                if os.path.exists(dst) and os.path.getmtime(dst) >= newest:
                    continue
                if srcs:
                    im = Image.open(src)
                    ai += 1
                else:
                    im = placeholder(sid, i, cast + ([v] if v else []))
                open(dst, 'wb').write(encode(im))
                made += 1
                im.convert('RGB').save(os.path.join(ROOT, 'build', 'preview', 'slide_' + name + '.png')) \
                    if os.path.isdir(os.path.join(ROOT, 'build', 'preview')) else None
    # drop slides that no longer exist in the plan
    for f in glob.glob(os.path.join(OUT, '*.sld')):
        if os.path.basename(f)[:-4] not in names:
            os.remove(f)
    print('slides', len(names), 'rebuilt', made, 'from AI art', ai)


if __name__ == '__main__':
    main()
