#!/usr/bin/env python3
"""List catalogue entries a language has not translated (helps spot omissions)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mklang
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cat = [e for e in json.load(open(os.path.join(ROOT, 'assets/i18n/catalog.json'), encoding='utf-8')) if e.get('used', True)]
for code in sys.argv[1:]:
    tr = mklang.load(code)
    miss = [e for e in cat if e['id'] not in tr]
    print(code, len(miss), ' | '.join(f"{e['id']}:{e['en'][:22]}" for e in miss))
