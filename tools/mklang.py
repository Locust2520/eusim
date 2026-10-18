#!/usr/bin/env python3
"""Build nitrofs/lang/<code>.bin from assets/i18n/catalog.json + assets/i18n/<code>.txt.

<code>.txt: one "id<TAB>translation" per line, \\n and \\f written as backslash sequences. Lines starting
with '#' are comments. Each translation is checked against its French source: same printf conversions in
the same order, same {P}/{V0}.. placeholders; a bad line is reported and skipped (French is shown instead).

.bin: 'LNG1', u32 n, n x (u32 fnv1a(French), u32 offset) sorted by hash, then NUL-terminated UTF-8 strings.
"""
import glob
import json
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
I18N = os.path.join(ROOT, 'assets', 'i18n')
OUT = os.path.join(ROOT, 'nitrofs', 'lang')
FMT = re.compile(r'%[-0-9.]*l?[sdux]')
PH = re.compile(r'\{[A-Z][0-9]?\}')


def fnv(b):
    h = 2166136261
    for c in b:
        h = ((h ^ c) * 16777619) & 0xFFFFFFFF
    return h


def unescape(s):
    return s.replace('\\n', '\n').replace('\\f', '\f').replace('\\t', '\t')


def load(code):
    """<code>.txt and/or parts <code>-1.txt, <code>-2.txt…"""
    tr = {}
    paths = sorted(glob.glob(os.path.join(I18N, code + '.txt')) + glob.glob(os.path.join(I18N, code + '-*.txt')))
    for path in paths:
        tr.update(load_file(path, code))
    return tr


def load_file(path, code):
    tr = {}
    for n, line in enumerate(open(path, encoding='utf-8'), 1):
        line = line.rstrip('\n')
        if not line or line.startswith('#'):
            continue
        sep = '\t' if '\t' in line else ' '
        i, _, t = line.partition(sep)
        if not i.isdigit():
            print(f'{os.path.basename(path)}:{n}: expected "<id> <text>"', file=sys.stderr)
            continue
        tr[int(i)] = unescape(t)
    return tr


def check(fr, t):
    if FMT.findall(fr) != FMT.findall(t):
        return 'printf conversions differ'
    if sorted(PH.findall(fr)) != sorted(PH.findall(t)):
        return 'placeholders differ'
    return None


def main():
    cat = json.load(open(os.path.join(I18N, 'catalog.json'), encoding='utf-8'))
    by_id = {e['id']: e for e in cat if e.get('used', True)}
    os.makedirs(OUT, exist_ok=True)
    report = []
    codes = sorted({c for c in (os.path.basename(p)[:-4].split('-')[0] for p in glob.glob(os.path.join(I18N, '*.txt')))
                    if re.fullmatch(r'[a-z]{2}', c)})
    en = load('en') if 'en' in codes else {}
    for code in codes:
        tr = load(code)
        own = len(tr)
        # Unfinished languages: anything not translated yet is shown in English rather than French.
        if code not in ('fr', 'en'):
            for i, t in en.items():
                if i not in tr:
                    tr[i] = t
        entries, bad = [], 0
        for i, t in tr.items():
            e = by_id.get(i)
            if not e or not t.strip():
                continue
            err = check(e['fr'], t)
            if err:
                bad += 1
                print(f'{code} #{i}: {err}: {t!r}', file=sys.stderr)
                continue
            if t != e['fr']:
                entries.append((fnv(e['fr'].encode('utf-8')), t.encode('utf-8') + b'\0'))
        entries.sort()
        hashes = [h for h, _ in entries]
        if len(set(hashes)) != len(hashes):
            print(f'{code}: hash collision', file=sys.stderr)
        blob = bytearray()
        offs = []
        base = 8 + 8 * len(entries)
        for h, s in entries:
            offs.append(base + len(blob))
            blob += s
        out = bytearray(b'LNG1') + struct.pack('<I', len(entries))
        for (h, _), o in zip(entries, offs):
            out += struct.pack('<II', h, o)
        out += blob
        open(os.path.join(OUT, code + '.bin'), 'wb').write(out)
        report.append(f'{code}:{own}/{len(by_id)}' + (f'({bad} bad)' if bad else ''))
    print('lang', ' '.join(report))


def charset():
    """Every character used by any translation (for tools/mkfont.py)."""
    chars = set()
    for path in glob.glob(os.path.join(I18N, '*.txt')):
        chars |= set(open(path, encoding='utf-8').read())
    for path in glob.glob(os.path.join(ROOT, 'assets', 'text', '*', '*.txt')):
        chars |= set(open(path, encoding='utf-8').read())
    return ''.join(sorted(c for c in chars if ord(c) >= 32 and c not in '\t'))


if __name__ == '__main__':
    main()
