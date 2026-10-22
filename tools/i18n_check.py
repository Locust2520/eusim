#!/usr/bin/env python3
"""Check one translation file without building anything (safe to run in parallel).

usage: i18n_check.py <code> <file> [first_id]
Reports: unknown or unused ids, placeholder/printf mismatches with the English source, empty lines,
and the ids >= first_id that the file does not translate.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mklang  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    code, path = sys.argv[1], sys.argv[2]
    first = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    cat = json.load(open(os.path.join(ROOT, 'assets', 'i18n', 'catalog.json'), encoding='utf-8'))
    used = {e['id']: e for e in cat if e.get('used', True)}
    tr = mklang.load_file(path, code)
    errors = 0
    for i, t in sorted(tr.items()):
        if i not in used:
            print(f'#{i}: not a current catalogue id')
            errors += 1
            continue
        if not t.strip():
            print(f'#{i}: empty translation')
            errors += 1
            continue
        err = mklang.check(used[i]['en'], t)
        if err:
            print(f'#{i}: {err}: {used[i]["en"]!r} -> {t!r}')
            errors += 1
    missing = [i for i in sorted(used) if i >= first and i not in tr] if first else []
    for i in missing:
        print(f'#{i}: missing: {used[i]["en"]!r}')
    print(f'{code}: {len(tr)} lines, {errors} errors, {len(missing)} missing (ids >= {first})')
    sys.exit(1 if errors or missing else 0)


if __name__ == '__main__':
    main()
