#!/usr/bin/env python3
"""Compile assets/maps/*.map (text) into nitrofs/maps/<id>.bin + source/gen/maps.h

Map text format
---------------
  name <display name>
  music <song>
  size <w> <h>
  fill <tile>                 default ground tile
  flags outdoor|indoor|dark|nobike ...
  encounters <table|none>
  legend                      then lines: <char> <tile name>
  ground                      then <h> rows of <w> chars (missing -> fill)
  objects                     then lines:
      <obj> <x> <y>                      place object (top-left cell)
      fill <obj> <x> <y> <w> <h>         tile the rect with the object
      tile <tile> <x> <y> [w h]          put a ground tile (rect)
      otile <tile> <x> <y> [w h]         put a tile on the object layer
  events                      then lines:
      warp <x> <y> <map> <dx> <dy> [dir]   (invisible warp, e.g. map edge / doormat)
      door <x> <y> <map> <dx> <dy> [dir]
      npc <name> <sprite> <x> <y> <dir> <move> <script> [hide=FLAG] [show=FLAG] [trainer=ID] [range=N]
      sign <x> <y> <script>
      trigger <x> <y> <w> <h> <script> [if=FLAG] [ifnot=FLAG]
      item <x> <y> <item> <flag>
      onload <script>
"""
import glob
import json
import os
import struct
import sys
from map_ids import ordered_map_sources

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import tiles as T  # noqa: E402

NITRO = os.path.join(ROOT, 'nitrofs')
DIRS = {'down': 0, 'up': 1, 'left': 2, 'right': 3, 'keep': 255}
MOVES = {'still': 0, 'look': 1, 'wander': 2, 'walk_h': 3, 'walk_v': 4, 'spin': 5}
FLAG_OUTDOOR, FLAG_DARK, FLAG_NOBIKE, FLAG_INDOOR = 1, 2, 4, 8
WATER_IDX = 188  # palette indices 188..191 cycle (w0..w3)


class MapSrc:
    def __init__(self, path):
        self.id = os.path.basename(path)[:-4]
        self.path = path
        self.name = self.id
        self.music = ''
        self.w = self.h = 0
        self.fill = 'grass'
        self.flags = 0
        self.enc = 'none'
        self.legend = {}
        self.rows = []
        self.objects = []
        self.events = []
        self.bg = (0, 0, 0)
        self.city = 255
        self.parse()

    def parse(self):
        sec = None
        for ln, raw in enumerate(open(self.path, encoding='utf-8'), 1):
            line = raw.rstrip('\n')
            s = line.split(';')[0].rstrip() if sec != 'ground' else line.rstrip()
            if not s.strip() or s.strip().startswith('#'):
                continue
            head = s.split()[0]
            if head in ('legend', 'ground', 'objects', 'events') and len(s.split()) == 1:
                sec = head
                continue
            if sec is None:
                parts = s.split(None, 1)
                k, v = parts[0], parts[1] if len(parts) > 1 else ''
                if k == 'name':
                    self.name = v
                elif k == 'music':
                    self.music = v
                elif k == 'size':
                    self.w, self.h = map(int, v.split())
                elif k == 'fill':
                    self.fill = v
                elif k == 'flags':
                    for f in v.split():
                        self.flags |= {'outdoor': FLAG_OUTDOOR, 'dark': FLAG_DARK, 'nobike': FLAG_NOBIKE, 'indoor': FLAG_INDOOR}[f]
                elif k == 'encounters':
                    self.enc = v
                elif k == 'city':
                    import proc_europe
                    keys = [c[0] for c in proc_europe.CITIES]
                    self.city = keys.index(v)
                elif k == 'bg':
                    self.bg = tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))
                else:
                    raise SystemExit(f'{self.path}:{ln}: unknown key {k}')
            elif sec == 'legend':
                ch = s.strip()[0]
                self.legend[ch] = s.strip()[1:].strip()
            elif sec == 'ground':
                self.rows.append(s.strip('\n').lstrip(' ') if False else s)
            elif sec == 'objects':
                self.objects.append((ln, s.split()))
            elif sec == 'events':
                self.events.append((ln, s.split()))
        # ground rows: strip a common 2-space indentation if present
        rows = []
        for r in self.rows:
            rows.append(r[2:] if r.startswith('  ') else r)
        self.rows = rows


def cell_images(m):
    """Return ground[h][w] and obj[h][w] as (tile/obj-cell keys) and a dict key->(img16, beh, above)."""
    reg = {}
    ground = [[None] * m.w for _ in range(m.h)]
    obj = [[None] * m.w for _ in range(m.h)]
    doors = []

    def tile_key(name):
        if name not in T.TILES:
            raise SystemExit(f'{m.path}: unknown tile {name}')
        k = 't:' + name
        if k not in reg:
            t = T.TILES[name]
            reg[k] = (t.img, t.beh, t.above)
        return k

    for y in range(m.h):
        row = m.rows[y] if y < len(m.rows) else ''
        for x in range(m.w):
            ch = row[x] if x < len(row) else ' '
            name = m.legend.get(ch, m.fill) if ch != ' ' else m.fill
            ground[y][x] = tile_key(name)

    over = {}  # (x, y) -> [(key, img)]: rows an object draws above its anchor (tree crowns)

    # grass: scatter the variants so the field does not repeat; paths and sand get soft grassy edges
    GRASS = ('grass', 'grass0', 'grass1', 'grass2', 'grass3', 'grass4', 'grass5')
    names = [[k[2:] for k in row] for row in ground]

    def is_grass(x, y):
        return not (0 <= x < m.w and 0 <= y < m.h) or names[y][x] in GRASS or names[y][x].startswith('flowers')

    for y in range(m.h):
        for x in range(m.w):
            n = names[y][x]
            if n == 'grass':
                v = (x * 7 + y * 13 + (x * y) % 5) % 11
                ground[y][x] = tile_key(('grass0', 'grass1', 'grass2', 'grass3', 'grass1', 'grass4', 'grass3',
                                         'grass1', 'grass5', 'grass3', 'grass0')[v])
            elif n == 'water':
                wet = lambda X, Y: not (0 <= X < m.w and 0 <= Y < m.h) or names[Y][X] == 'water' or names[Y][X].startswith('shore')
                mask = ''.join(s for s, (dx, dy) in (('n', (0, -1)), ('s', (0, 1)), ('w', (-1, 0)), ('e', (1, 0))) if not wet(x + dx, y + dy))
                if mask:
                    k = 't:water~' + mask
                    if k not in reg:
                        reg[k] = (T.grade(T.shore(mask)), T.B_WATER, False)
                    ground[y][x] = k
            elif n in ('path', 'sand'):
                ins = lambda X, Y: 0 <= X < m.w and 0 <= Y < m.h and is_grass(X, Y)
                mask = [s for s, (dx, dy) in (('n', (0, -1)), ('s', (0, 1)), ('w', (-1, 0)), ('e', (1, 0))) if ins(x + dx, y + dy)]
                for c, (dx, dy) in (('NE', (1, -1)), ('NW', (-1, -1)), ('SE', (1, 1)), ('SW', (-1, 1))):
                    if ins(x + dx, y + dy) and c[0].lower() not in mask and c[1].lower() not in mask:
                        mask.append(c)
                if mask:
                    k = f't:{n}~' + ''.join(mask)
                    if k not in reg:
                        t = T.TILES[n]
                        reg[k] = (T.grade(T.soft_edge(T.RAW[n], mask, rim='d0' if n == 'path' else 's2')), t.beh, t.above)
                    ground[y][x] = k

    def place_obj(name, ox, oy, ln):
        if name not in T.OBJECTS:
            raise SystemExit(f'{m.path}:{ln}: unknown object {name}')
        o = T.OBJECTS[name]
        top = getattr(o, 'oy', 0)
        for cy in range(-top, 0):
            for cx in range(o.w):
                X, Y = ox + cx, oy + cy
                if 0 <= X < m.w and 0 <= Y < m.h:
                    py = (cy + top) * 16
                    over.setdefault((X, Y), []).append(
                        (f'{name}:{cx}:{cy}', o.img.crop((cx * 16, py, cx * 16 + 16, py + 16))))
        for cy in range(o.h):
            for cx in range(o.w):
                X, Y = ox + cx, oy + cy
                if not (0 <= X < m.w and 0 <= Y < m.h):
                    continue
                k = f'o:{name}:{cx}:{cy}'
                if k not in reg:
                    py = (cy + top) * 16
                    img = o.img.crop((cx * 16, py, cx * 16 + 16, py + 16))
                    bch = o.beh[cy][cx] if o.beh else '#'
                    beh = T.BEH_CHARS.get(bch, T.B_SOLID)
                    above = bool(o.above and o.above[cy][cx] == '1')
                    reg[k] = (img, beh, above)
                obj[Y][X] = k
        for (dx, dy) in o.doors:
            doors.append((ox + dx, oy + dy))

    for ln, a in m.objects:
        if a[0] == 'fill':
            name, x, y, w, h = a[1], int(a[2]), int(a[3]), int(a[4]), int(a[5])
            o = T.OBJECTS[name]
            for yy in range(y, y + h, o.h):
                for xx in range(x, x + w, o.w):
                    place_obj(name, xx, yy, ln)
        elif a[0] in ('tile', 'otile'):
            name, x, y = a[1], int(a[2]), int(a[3])
            w = int(a[4]) if len(a) > 4 else 1
            h = int(a[5]) if len(a) > 5 else 1
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    if a[0] == 'tile':
                        ground[yy][xx] = tile_key(name)
                    else:
                        obj[yy][xx] = tile_key(name)
        else:
            place_obj(a[0], int(a[1]), int(a[2]), ln)
    # crowns overhanging the cell above: drawn over actors, on top of whatever object is there already
    for (X, Y), parts in over.items():
        base = obj[Y][X]
        k = 'v:' + (base or ground[Y][X]) + '|' + '|'.join(p[0] for p in parts)
        if k not in reg:
            img = reg[base][0].copy() if base else Image.new('RGBA', (16, 16), (0, 0, 0, 0))
            if base:
                ba = np.array(img)[..., 3]
                if ((ba > 0) & (ba < 255)).any():
                    img = reg[ground[Y][X]][0].copy()
                    img.alpha_composite(reg[base][0])
            for _, part in parts:
                img.alpha_composite(part)
            beh = reg[base][1] if base else reg[ground[Y][X]][1]
            reg[k] = (img, beh, True)
        obj[Y][X] = k
    # soft shadows (semi-transparent pixels) are blended into the ground they fall on
    for Y in range(m.h):
        for X in range(m.w):
            k = obj[Y][X]
            if not k or reg[k][2]:
                continue
            a = np.array(reg[k][0])[..., 3]
            if not ((a > 0) & (a < 255)).any():
                continue
            mk = 's:' + ground[Y][X] + '|' + k
            if mk not in reg:
                img = reg[ground[Y][X]][0].copy()
                img.alpha_composite(reg[k][0])
                reg[mk] = (img, reg[k][1], False)
            obj[Y][X] = mk
    return ground, obj, reg, doors


def build_palette(images):
    cols = {}
    for im in images:
        a = np.array(im)
        op = a[..., 3] >= 128
        for c in (tuple(int(v) for v in px) for px in a[op][:, :3]):
            cols[c] = cols.get(c, 0) + 1
    water = [T.P[k][:3] for k in ('w0', 'w1', 'w2', 'w3')]
    others = [c for c in cols if c not in water]
    if len(others) > 174:
        # quantize: merge least frequent colours to nearest
        keep = sorted(others, key=lambda c: -cols[c])[:174]
        remap = {}
        ka = np.array(keep, dtype=float)
        for c in others:
            if c in keep:
                continue
            dd = ((ka - np.array(c, float)) ** 2).sum(1)
            remap[c] = keep[int(dd.argmin())]
        others = keep
    else:
        remap = {}
    pal = [None] * 192
    idx = {}
    for i, c in enumerate(others):
        pal[1 + i] = c
        idx[c] = 1 + i
    for k, c in enumerate(water):
        pal[WATER_IDX + k] = c
        idx[c] = WATER_IDX + k
    for c, t in remap.items():
        idx[c] = idx[t]
    n = max(i for i in range(192) if pal[i] is not None) + 1
    return pal, idx, n


def to_index(im, idx):
    a = np.array(im)
    out = np.zeros((16, 16), 'uint8')
    for y in range(16):
        for x in range(16):
            p = a[y, x]
            if p[3] >= 128:
                out[y, x] = idx[tuple(int(v) for v in p[:3])]
    return out


def compile_map(m, map_ids, script_ids, sprite_ids, trainer_ids, item_ids, flag_ids, enc_ids):
    ground, obj, reg, doors = cell_images(m)
    keys = sorted(reg)
    pal, idx, ncol = build_palette([reg[k][0] for k in keys])
    # metatiles: index 0 = empty
    tiles, tlut = [np.zeros((8, 8), 'uint8')], {np.zeros((8, 8), 'uint8').tobytes(): 0}

    def add_tile(t):
        for fl, tt in ((0, t), (1, t[:, ::-1]), (2, t[::-1, :]), (3, t[::-1, ::-1])):
            k = tt.tobytes()
            if k in tlut:
                return tlut[k] | ((fl & 1) << 10) | ((fl >> 1) << 11)
        tlut[t.tobytes()] = len(tiles)
        tiles.append(t)
        return len(tiles) - 1

    metas = [([0] * 4, [0] * 4, 0)]
    mlut = {}
    for k in keys:
        img, beh, above = reg[k]
        ia = to_index(img, idx)
        quads = [add_tile(ia[qy * 8:qy * 8 + 8, qx * 8:qx * 8 + 8].copy()) for qy in (0, 1) for qx in (0, 1)]
        if above:
            metas.append(([0] * 4, quads, beh))
        else:
            metas.append((quads, [0] * 4, beh))
        mlut[k] = len(metas) - 1
    if len(tiles) > 1023:
        raise SystemExit(f'{m.path}: too many unique tiles ({len(tiles)})')
    cells = []
    for y in range(m.h):
        for x in range(m.w):
            g = mlut[ground[y][x]]
            o = mlut[obj[y][x]] if obj[y][x] else 0
            cells.append((g, o))

    def ref(table, name, what, allow_none=True):
        if allow_none and name in ('none', '-', None):
            return 0xFFFF
        if name not in table:
            raise SystemExit(f'{m.path}: unknown {what} {name}')
        return table[name]

    warps, npcs, signs, trigs, items = [], [], [], [], []
    onload = 0xFFFF
    for ln, a in m.events:
        kind = a[0]
        if kind in ('warp', 'door'):
            x, y, dest, dx, dy = int(a[1]), int(a[2]), a[3], int(a[4]), int(a[5])
            d = DIRS[a[6]] if len(a) > 6 else 255
            warps.append(struct.pack('<BBHBBBB', x, y, ref(map_ids, dest, 'map', False), dx, dy, d, 1 if kind == 'door' else 0))
        elif kind == 'npc':
            name, spr, x, y, d, mv, scr = a[1], a[2], int(a[3]), int(a[4]), DIRS[a[5]], MOVES[a[6]], a[7]
            opts = dict(o.split('=') for o in a[8:])
            hide = ref(flag_ids, opts.get('hide'), 'flag')
            show = ref(flag_ids, opts.get('show'), 'flag')
            tr = ref(trainer_ids, opts.get('trainer'), 'trainer')
            rng = int(opts.get('range', 4))
            npcs.append(struct.pack('<HBBBBHHHHBxH', ref(sprite_ids, spr, 'sprite', False), x, y, d, mv,
                                    ref(script_ids, scr, 'script'), hide, show, tr, rng, name_hash(name)))
        elif kind == 'sign':
            signs.append(struct.pack('<BBH', int(a[1]), int(a[2]), ref(script_ids, a[3], 'script', False)))
        elif kind == 'trigger':
            x, y, w, h, scr = int(a[1]), int(a[2]), int(a[3]), int(a[4]), a[5]
            opts = dict(o.split('=') for o in a[6:])
            cf, cv = 0xFFFF, 0
            if 'if' in opts:
                cf, cv = ref(flag_ids, opts['if'], 'flag'), 1
            if 'ifnot' in opts:
                cf, cv = ref(flag_ids, opts['ifnot'], 'flag'), 0
            trigs.append(struct.pack('<BBBBHHB3x', x, y, w, h, ref(script_ids, scr, 'script', False), cf, cv))
        elif kind == 'item':
            items.append(struct.pack('<BBHH2x', int(a[1]), int(a[2]), ref(item_ids, a[3], 'item', False),
                                     ref(flag_ids, a[4], 'flag', False)))
        elif kind == 'onload':
            onload = ref(script_ids, a[1], 'script', False)
        else:
            raise SystemExit(f'{m.path}:{ln}: unknown event {kind}')
    # NPCs and triggers standing inside walls/buildings (catch misplaced events after layout edits)
    def beh_at(x, y):
        if not (0 <= x < m.w and 0 <= y < m.h):
            return None
        g, o = cells[y * m.w + x]
        return metas[o][2] if o else metas[g][2]
    for ln, a in m.events:
        if a[0] == 'npc' and beh_at(int(a[3]), int(a[4])) in (T.B_SOLID, T.B_WATER):
            print(f'warning: {m.path}: npc {a[1]} at ({a[3]}, {a[4]}) is inside a solid tile')
        if a[0] == 'trigger':
            x, y, w, h = int(a[1]), int(a[2]), int(a[3]), int(a[4])
            if all(beh_at(xx, yy) in (T.B_SOLID, T.B_WATER, None) for xx in range(x, x + w) for yy in range(y, y + h)):
                print(f'warning: {m.path}: trigger {a[5]} at ({x}, {y}) is unreachable')
    # doors without explicit event are an error (catch typos early)
    door_pos = {(struct.unpack_from('<BB', w)[0], struct.unpack_from('<BB', w)[1]) for w in warps}
    for dpos in doors:
        if dpos not in door_pos:
            print(f'warning: {m.path}: door at {dpos} has no warp')

    out = bytearray(b'MAP1')
    music = m.music.encode()[:15].ljust(16, b'\0')
    name = m.name.encode('utf-8')[:47].ljust(48, b'\0')
    bg = (m.bg[0] >> 3) | ((m.bg[1] >> 3) << 5) | ((m.bg[2] >> 3) << 10)
    out += struct.pack('<HHHHHBB', m.w, m.h, len(metas), len(tiles), ncol, m.flags, m.city)
    out += music + name
    out += struct.pack('<HHH', ref(enc_ids, m.enc, 'encounter table'), onload, bg)
    out += struct.pack('<HHHHH', len(warps), len(npcs), len(signs), len(trigs), len(items))
    for i in range(ncol):
        c = pal[i] or (0, 0, 0)
        out += struct.pack('<H', (c[0] >> 3) | ((c[1] >> 3) << 5) | ((c[2] >> 3) << 10))
    for t in tiles:
        out += bytes(t.reshape(-1))
    for lo, up, beh in metas:
        out += struct.pack('<8HBB', *lo, *up, beh, 0)
    for g, o in cells:
        out += struct.pack('<HH', g, o)
    for blob in warps + npcs + signs + trigs + items:
        out += blob
    return bytes(out), len(tiles)


def name_hash(s):
    h = 5381
    for ch in s.encode():
        h = (h * 33 + ch) & 0xFFFF
    return h


def load_ids(name):
    p = os.path.join(ROOT, 'build', name + '_ids.json')
    return json.load(open(p)) if os.path.exists(p) else {}


def main():
    T.build_registry()
    srcs = ordered_map_sources(ROOT)
    maps = [MapSrc(p) for p in srcs]
    # Map ids are stored in save files: keep the released order, new maps go at the end.
    order_path = os.path.join(ROOT, 'assets/maps/order.txt')
    order = [l.strip() for l in open(order_path)] if os.path.exists(order_path) else []
    order = [o for o in order if o]
    for m in maps:
        if m.id not in order:
            order.append(m.id)
    open(order_path, 'w').write('\n'.join(order) + '\n')
    rank = {mid: i for i, mid in enumerate(order)}
    maps.sort(key=lambda m: rank[m.id])
    map_ids = {m.id: i for i, m in enumerate(maps)}
    os.makedirs(os.path.join(ROOT, 'build'), exist_ok=True)
    json.dump(map_ids, open(os.path.join(ROOT, 'build/map_ids.json'), 'w'), indent=0)
    script_ids = load_ids('script')
    sprite_ids = load_ids('sprite')
    trainer_ids = load_ids('trainer')
    item_ids = load_ids('item')
    flag_ids = load_ids('flag')
    enc_ids = load_ids('enc')
    os.makedirs(os.path.join(NITRO, 'maps'), exist_ok=True)
    hdr = ['// Generated by tools/mkmaps.py', '#pragma once', f'#define NUM_MAPS {len(maps)}']
    for m in maps:
        data, nt = compile_map(m, map_ids, script_ids, sprite_ids, trainer_ids, item_ids, flag_ids, enc_ids)
        open(os.path.join(NITRO, 'maps', f'{map_ids[m.id]}.bin'), 'wb').write(data)
        hdr.append(f'#define MAP_{m.id.upper()} {map_ids[m.id]}  // {m.name} ({m.w}x{m.h}, {nt} tiles)')
    open(os.path.join(ROOT, 'include/gen/maps.h'), 'w').write('\n'.join(hdr) + '\n')
    print('maps', len(maps))


if __name__ == '__main__':
    main()
