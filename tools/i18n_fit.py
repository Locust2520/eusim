#!/usr/bin/env python3
"""Check that translations fit their on-screen boxes (reads files only: safe to run in parallel).

usage: i18n_fit.py <code> <file> [first_id] [-v]
Finds the fixed-size text boxes in source/*.c (ui_text_in, ui_button, caption, ui_text_wrapped, mini-game
titles, map names) whose English text is in the catalogue, then measures each translation with the game's
fonts (source/gen/font_data.c) the way ui_text_in does: main font, else the small font, else letter spacing
condensed by up to 2 px per glyph, else cut with "…".
  CUT    the translation is cut on screen: shorten it
  LINES  a wrapped text needs more lines than the English: check the space below it (often fine)
  tight  (-v) it fits only with condensed spacing or the small font
"""
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mklang  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_fonts():
    src = open(os.path.join(ROOT, 'source/gen/font_data.c'), encoding='utf-8').read()
    fonts = {}
    for name, body in re.findall(r'static const FontGlyph (font_\w+)_glyphs\[\] = \{(.*?)\};', src, re.S):
        fonts[name] = {int(cp): int(adv) for cp, _w, adv in re.findall(r'\{(\d+),(\d+),(\d+),', body)}
    return fonts


FONTS = load_fonts()
# a letter the font does not have yet (mkfont adds it at build time): count an average lowercase letter
AVG = {f: round(sum(g.get(c, 0) for c in range(97, 123)) / 26) for f, g in FONTS.items()}


def width(font, s, track=0):
    g = FONTS[font]
    w = 0
    for ch in s.split('\n')[0]:
        w += (g.get(ord(ch), AVG[font])) + track
    return w


def fit(font, w, s, align):
    """mirror of ui_text_in: returns (state, needed px, available px)"""
    if font == 'font_main' and width('font_main', s) > w - 4 and width('font_small', s) <= width('font_main', s):
        font = 'font_small'
    avail = w - 2 if align == 0 else w - 5
    track = 0
    while track > -2 and width(font, s, track) > avail:
        track -= 1
    need = width(font, s, track)
    if need > avail:
        return 'CUT', need, avail, font
    return ('tight' if track or font == 'font_small' else 'ok'), need, avail, font


def wrap_lines(font, w, s):
    """mirror of ui_text_wrapped: number of lines"""
    n_lines = 0
    while s:
        n, sp = 0, -1
        while n < len(s) and s[n] != '\n' and width(font, s[:n + 1]) <= w:
            if s[n] == ' ':
                sp = n
            n += 1
        if n < len(s) and s[n] != '\n' and sp > 0:
            n = sp
        if n == 0 and s[0] != '\n':
            n = 1
        s = s[n:].lstrip(' \n')
        n_lines += 1
    return n_lines


# ---------------------------------------------------------------- C source scan
LIT = re.compile(r'"((?:[^"\\]|\\.)*)"')


def c_unescape(s):
    return re.sub(r'\\(x[0-9a-fA-F]{2}|.)', lambda m: {'n': '\n', 't': '\t', 'f': '\f', '"': '"', '\\': '\\',
                                                       "'": "'"}.get(m.group(1), chr(int(m.group(1)[1:], 16))
                                                                     if m.group(1)[0] == 'x' else m.group(1)), s)


def literals(expr):
    """string literals of an argument; adjacent literals are joined like the C compiler does"""
    out, cur, last = [], None, -1
    for m in LIT.finditer(expr):
        between = expr[last:m.start()] if last >= 0 else None
        if cur is not None and between is not None and between.strip() == '':
            cur += c_unescape(m.group(1))
        else:
            if cur is not None:
                out.append(cur)
            cur = c_unescape(m.group(1))
        last = m.end()
    if cur is not None:
        out.append(cur)
    return out


def split_args(src, i):
    """src[i] is just after '(': returns (args, end index)"""
    args, depth, cur, j = [], 0, '', i
    while j < len(src):
        ch = src[j]
        if ch == '"':
            m = LIT.match(src, j)
            if not m:
                break
            cur += m.group(0)
            j = m.end()
            continue
        if ch == "'":
            k = src.index("'", j + 2 if src[j + 1] == '\\' else j + 1)
            cur += src[j:k + 1]
            j = k + 1
            continue
        if ch in '([{':
            depth += 1
        elif ch in ')]}':
            if depth == 0:
                args.append(cur.strip())
                return args, j
            depth -= 1
        elif ch == ',' and depth == 0:
            args.append(cur.strip())
            cur = ''
            j += 1
            continue
        cur += ch
        j += 1
    return args, j


def array_strings(src, pos, expr):
    """`names[i]` / `food[item].name`: the strings of the closest array definition above the call"""
    m = re.fullmatch(r'(\w+)\s*\[.*\](?:\.(\w+))?', expr)
    if not m:
        return []
    defs = [d for d in re.finditer(r'\b' + m.group(1) + r'\s*\[\w*\]\s*=\s*\{', src) if d.start() < pos]
    if not defs:
        return []
    start = defs[-1].end() - 1
    _, end = split_args(src, start + 1)
    block = src[start:end + 1]
    if m.group(2):   # struct array: the first string of each element
        return [c_unescape(x) for x in re.findall(r'\{\s*"((?:[^"\\]|\\.)*)"', block)]
    return literals(block)


def num(expr):
    return int(expr) if re.fullmatch(r'\d+', expr) else None


def font_of(expr, default='font_main'):
    m = re.search(r'font_(main|small)', expr or '')
    return 'font_' + m.group(1) if m else default


# function: (font arg or fixed font, width arg or fixed width, text arg, align arg or fixed align, kind)
CALLS = {
    'ui_text_in': (1, 4, 6, 9, 'line'),
    'ui_button': (7, 3, 5, 0, 'line'),
    'ui_text_wrapped': (1, 4, 5, 0, 'wrap'),
}


def boxes():
    """English text -> list of (font, width, align, kind, place)"""
    out = {}

    def add(text, font, w, align, kind, place):
        if text.strip():
            out.setdefault(text, []).append((font, w, align, kind, place))

    for path in sorted(glob.glob(os.path.join(ROOT, 'source', '*.c'))):
        src = open(path, encoding='utf-8').read()
        base = os.path.basename(path)
        for m in re.finditer(r'\b(ui_text_in|ui_button|ui_text_wrapped|caption|top_header|mg_intro|intro|'
                             r'mg_top_panel|top_panel)\s*\(', src):
            fn = m.group(1)
            args, _ = split_args(src, m.end())
            line = src.count('\n', 0, m.start()) + 1
            place = f'{base}:{line}'
            if fn in CALLS:
                fa, wa, ta, aa, kind = CALLS[fn]
                if len(args) <= ta or re.match(r'(static\s+)?(void|int|bool)\b', src[src.rfind('\n', 0, m.start()) + 1:m.start()]):
                    continue
                w = num(args[wa])
                if w is None:
                    continue
                font = font_of(args[fa] if len(args) > fa else None)
                align = 1 if fn == 'ui_text_in' and len(args) > aa and args[aa] != '0' else 0
                texts = literals(args[ta]) or array_strings(src, m.start(), args[ta])
                for t in texts:
                    add(t, font, w, align, kind, place)
            elif fn == 'caption' and base == 'note.c' and len(args) == 3:
                for t in literals(args[2]):
                    add(t, 'font_small', 248, 0, 'line', place)
            elif fn == 'top_header' and len(args) >= 1:
                for t in literals(args[0]):
                    add(t, 'font_main', 150, 0, 'line', place)
            elif fn in ('mg_intro', 'intro', 'mg_top_panel', 'top_panel') and len(args) >= 2:
                for t in literals(args[0]):
                    add(t, 'font_main', 239, 0, 'line', place)
                if fn.endswith('top_panel'):
                    for t in literals(args[1]):
                        add(t, 'font_small', 239, 0, 'line', place)
    return out


def main():
    argv = [a for a in sys.argv[1:] if a != '-v']
    verbose = '-v' in sys.argv
    code, path = argv[0], argv[1]
    first = int(argv[2]) if len(argv) > 2 else 0
    cat = json.load(open(os.path.join(ROOT, 'assets', 'i18n', 'catalog.json'), encoding='utf-8'))
    by_en = {}
    for e in cat:
        if e.get('used', True):
            by_en.setdefault(e['en'], e['id'])
    places = boxes()
    # map names: the location banner (world.c) and the town map title (menu.c), main font, at most 248 px
    for e in cat:
        if e.get('used', True) and e.get('ctx') == 'map name':
            places.setdefault(e['en'], []).append(('font_main', 248, 0, 'line', 'map name'))
    tr = mklang.load_file(path, code)
    cut = lines = tight = 0
    for en, where in sorted(places.items(), key=lambda kv: by_en.get(kv[0], 0)):
        i = by_en.get(en)
        if i is None or i < first or i not in tr:
            continue
        t = tr[i]
        seen = set()
        for font, w, align, kind, place in where:
            if (font, w, align, kind) in seen:
                continue
            seen.add((font, w, align, kind))
            if kind == 'wrap':
                ne, nt = wrap_lines(font, w, en), wrap_lines(font, w, t)
                if nt > ne:
                    lines += 1
                    print(f'#{i} LINES {ne} -> {nt} ({font[5:]} {w}px, {place}): {t!r}')
                continue
            for part in t.split('\n'):
                state, need, avail, used = fit(font, w, part, align)
                if state == 'CUT':
                    cut += 1
                    print(f'#{i} CUT {need}px > {avail}px ({font[5:]} box {w}px, {place}): {part!r}  [en {en!r}]')
                elif state == 'tight' and verbose:
                    tight += 1
                    print(f'#{i} tight ({used[5:]} font, {need}/{avail}px, {place}): {part!r}')
    print(f'{os.path.basename(path)}: {cut} cut, {lines} longer wrapped' + (f', {tight} tight' if verbose else ''))
    return 1 if cut else 0


if __name__ == '__main__':
    sys.exit(main())
