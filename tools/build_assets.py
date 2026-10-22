#!/usr/bin/env python3
"""Build all generated assets into nitrofs/ and source/gen/."""
import os, subprocess, sys, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
os.chdir(ROOT)

def newer(src, dst):
    return not os.path.exists(dst) or os.path.getmtime(src) > os.path.getmtime(dst)

def main():
    os.makedirs('nitrofs/music', exist_ok=True)
    import mkfont
    stale = newer('tools/mkfont.py', 'source/gen/font_data.c') or any(
        newer(f, 'source/gen/font_data.c') for f in glob.glob('assets/i18n/*.txt'))
    if stale:
        mkfont.main()
    import mml
    import shutil
    for f in glob.glob('assets/music/*.mml'):
        out = 'nitrofs/music/' + os.path.basename(f)[:-4] + '.sng'
        if newer(f, out) or newer('tools/mml.py', out):
            open(out, 'wb').write(mml.compile_file(f))
    if os.path.exists('assets/music/aliases.txt'):
        for line in open('assets/music/aliases.txt'):
            a, b = line.split()
            shutil.copy(f'nitrofs/music/{b}.sng', f'nitrofs/music/{a}.sng')
    import shutil
    os.makedirs('nitrofs/text', exist_ok=True)
    for f in glob.glob('assets/text/*.txt'):
        shutil.copy(f, 'nitrofs/text/')
    for f in glob.glob('assets/text/*/*.txt'):  # translations: assets/text/<code>/credits.txt
        d = os.path.join('nitrofs/text', os.path.basename(os.path.dirname(f)))
        os.makedirs(d, exist_ok=True)
        shutil.copy(f, d)
    for mod in ['mapgen', 'proc_europe', 'mknote', 'mkgfx', 'mkmona', 'proc_chars', 'mkdata', 'proc_creatures', 'mkscripts', 'mkmaps', 'mkslides', 'i18n_extract', 'mklang', 'mkstream']:
        if os.path.exists(f'tools/{mod}.py'):
            __import__(mod).main()

if __name__ == '__main__':
    main()
