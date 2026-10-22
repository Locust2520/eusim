#!/usr/bin/env python3
"""Collect every English (source language) string the player can see into assets/i18n/catalog.json.

Sources: script strings, on-screen C string literals, game data and map names.
Each entry has a stable id, English source text and source context. Translations live in
assets/i18n/<code>*.txt as id/text lines (French included); tools/mklang.py validates placeholders.
"""
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'i18n', 'catalog.json')

# literals that are identifiers, asset names, magic numbers or proper names: never translated
C_SKIP = {'neutral', 'happy', 'angry', 'surprised', 'worried', 'sulk', 'schuman', 'alex', 'max', 'oliver', 'orban',
          'putin', 'xi', 'trump', 'vdl', 'intro', 'title', 'ending', 'minigame', 'evolution', 'encounter',
          'victory_trainer', 'victory_wild', 'battle_trainer', 'battle_legend', 'battle_wild', 'SLD1', 'ICN1',
          'BGI1', 'BMP8', 'MAP1', 'UESU', 'SCR1', 'LNG1', 'scripts.bin', '%s.probe', '%s.tmp', '/eusim', '(trump)',
          'EUL1', 'EUN2', 'EU Simulator %.12s',
          'Oliver', 'Alex', 'Max', 'EU SIMULATOR', 'Zz', 'z', 'OK', 'Eurodex', 'EXP', 'FATAL ERROR',
          '%s_slot%d.sav', 'sd:/eusim', 'fat:/eusim', '-Wformat-nonliteral', 'P', 'R', 'M', '…', '0,3 l', 'EURO', 'C'}
C_SKIP_FILES = {'source/keyboard.c': {13, 14, 15, 16}, 'source/lang.c': None, 'source/compat.c': None, 'source/langpick.c': None,
                'source/mg_langs.c': None, 'source/note_render.c': None, 'source/mg_greek.c': None}


def c_strings():
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, 'source', '*.c'))):
        rel = os.path.relpath(f, ROOT)
        if rel in C_SKIP_FILES and C_SKIP_FILES[rel] is None:
            continue
        for i, line in enumerate(open(f, encoding='utf-8'), 1):
            st = line.strip()
            if st.startswith(('//', '#include', 'fatal(', '_Static_assert(')) or i in C_SKIP_FILES.get(rel, set()):
                continue
            for m in re.finditer(r'"((?:[^"\\]|\\.)*)"', line):
                s = m.group(1)
                if s in C_SKIP:
                    continue
                if re.fullmatch(r'[.a-z]+', s) and set(s) <= set('.kwbrgacyopmdlest'):
                    continue  # pixel-art rows
                if re.fullmatch(r'[.KQRBNPkqrbnp]{8}', s):
                    continue  # chess board rows (Budapest mini-game)
                if re.fullmatch(r'[a-z][a-z0-9_]*', s) or s == 'ADS1':
                    continue  # identifiers (music/file names, magic numbers)
                words = re.sub(r'%[-0-9.]*l?[a-z]', '', s)
                if not re.search(r'[A-Za-zÀ-ÿ]', words):
                    continue
                if re.search(r'\.(spr|bgi|bmp8|sld|sng|txt|sav|cfg|bin)$', s) or \
                        s.startswith(('ui/', 'portraits/', 'text/', 'slides/', 'music/', 'creatures/', 'maps/',
                                      'lang/', 'nitro:', 'sd:', 'fat:', '%s/', '%s_', '\\x')):
                    continue
                s = bytes(s, 'utf-8').decode('unicode_escape').encode('latin-1').decode('utf-8') \
                    if '\\' in s else s
                out.append((s, f'{rel}:{i}'))
    return out


def script_strings():
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, 'assets', 'scripts', '*.evs'))):
        rel = os.path.relpath(f, ROOT)
        for i, line in enumerate(open(f, encoding='utf-8'), 1):
            st = line.strip()
            if not st or st.startswith(('#', ';')):
                continue
            cmd = st.split()[0]
            if cmd in ('move',):
                continue
            for m in re.finditer(r'"((?:[^"\\]|\\.)*)"', st):
                s = m.group(1)
                if not re.search(r'[A-Za-zÀ-ÿ]', s) or s == '-':
                    continue
                out.append((s.replace('\\n', '\n').replace('\\f', '\f'), f'{rel}:{i}'))
    return out


def data_strings():
    out = []
    D = os.path.join(ROOT, 'data')
    types = json.load(open(os.path.join(D, 'types.json'), encoding='utf-8'))
    for n in types['names']:
        out.append((n, 'type'))
    for m in json.load(open(os.path.join(D, 'moves.json'), encoding='utf-8')):
        out.append((m['name'], 'move name'))
        out.append((m['desc'], f"move {m['name']}"))
    for s in json.load(open(os.path.join(D, 'species.json'), encoding='utf-8')):
        out.append((s['name'], f"Euromon name (category: {s['category']})"))
        out.append((s['category'], f"species category ({s['name']})"))
        out.append((s['dex'], f"dex entry of the Euromon {s['name']}"))
    for it in json.load(open(os.path.join(D, 'items.json'), encoding='utf-8')):
        out.append((it['name'], 'item name'))
        out.append((it['desc'], f"item {it['name']}"))
    for t in json.load(open(os.path.join(D, 'trainers.json'), encoding='utf-8')):
        out.append((t['cls'], 'trainer class'))
        for k in ('intro', 'defeat', 'win'):
            if t.get(k):
                out.append((t[k], f"trainer {t['cls']} {t['name']} ({k})"))
    return out


def map_names():
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, 'assets', 'maps', '*.map'))):
        for line in open(f, encoding='utf-8'):
            if line.startswith('name '):
                out.append((line[5:].strip(), 'map name'))
    return out


def main():
    # ids are stable: existing entries keep theirs, new strings are appended, vanished ones are flagged
    old = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else []
    by_text = {e['en']: e for e in old}
    cat = list(old)
    for e in cat:
        e['used'] = False
    for s, ctx in c_strings() + script_strings() + data_strings() + map_names():
        if not s.strip() or s in C_SKIP:
            continue
        e = by_text.get(s)
        if e is None:
            e = {'id': len(cat), 'en': s, 'ctx': ctx}
            by_text[s] = e
            cat.append(e)
        e['used'] = True
        e['ctx'] = e.get('ctx') or ctx
    json.dump(cat, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    used = [e for e in cat if e['used']]
    print('catalogue', len(used), 'strings', sum(len(e['en']) for e in used), 'chars')
    # compact listing for translators: id<TAB>text (\n and \f escaped)
    with open(os.path.join(ROOT, 'assets', 'i18n', 'catalog.txt'), 'w', encoding='utf-8') as f:
        for e in used:
            f.write(f"{e['id']}\t{e['en']}".replace('\n', '\\n').replace('\f', '\\f') + '\n')


if __name__ == '__main__':
    main()
