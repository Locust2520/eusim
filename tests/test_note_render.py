"""Specimen banknote renderer (source/note_render.c) on the host: every value, theme and side.

Also writes build/preview/notes/*.png for visual checks.
"""
import json
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_progression import ROOT
from test_browser_save import code

PRELUDE = r'''
#include <assert.h>
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef uint8_t u8; typedef int8_t s8; typedef uint16_t u16; typedef int16_t s16;
typedef uint32_t u32; typedef int32_t s32; typedef volatile u16 vu16;
#define ARRAY_LEN(a) ((int)(sizeof(a)/sizeof((a)[0])))
#define MIN(a, b) ((a) < (b) ? (a) : (b))
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define CLAMP(v, lo, hi) ((v) < (lo) ? (lo) : (v) > (hi) ? (hi) : (v))
#define DC_FlushRange(...) ((void)0)
#define dmaCopyWords(...) ((void)0)
#define bgGetGfxPtr(...) NULL
int g_bg_main[4], g_bg_sub[4];
static const char *tr(const char *s) { return s; }
'''


def font_data():
    src = (ROOT / 'source/gen/font_data.c').read_text()
    return '\n'.join(l for l in src.splitlines() if not l.startswith('#include'))


class NoteRenderTests(unittest.TestCase):
    def test_every_value_theme_and_side(self):
        out_dir = ROOT / 'build/preview/notes'
        out_dir.mkdir(parents=True, exist_ok=True)
        art = (ROOT / 'nitrofs/ui/note_art.bin').read_bytes()
        face = (ROOT / 'nitrofs/ui/note_face_alex.bin').read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            d = Path(directory)
            (d / 'art.bin').write_bytes(art)
            (d / 'face.bin').write_bytes(face)
            src = d / 'test.c'
            src.write_text(PRELUDE + code('include/save.h') + code('include/font.h') + code('include/canvas.h') +
                           code('include/gen/font_data.h') + code('include/gfx.h') + code('include/note_render.h') + font_data() +
                           code('source/font.c') + code('source/canvas.c') + code('source/note_render.c') + r'''
void ui_target_corners(Canvas *c, int x, int y, int w, int h) {}
static u8 *load(const char *p, u32 *n) { FILE *f = fopen(p, "rb"); fseek(f, 0, SEEK_END); *n = ftell(f); rewind(f);
    u8 *b = malloc(*n); assert(fread(b, 1, *n, f) == *n); fclose(f); return b; }
int main(int argc, char **argv) {
    static u8 px[256 * 192];
    Canvas c = {px, NULL, 0, 0};
    u32 n, fn; u8 *blob = load(argv[1], &n), *face = load(argv[2], &fn);
    NoteArt art; assert(note_art_parse(&art, blob, n) && art.count >= ART_COUNT);
    assert(!note_art_parse(&art, blob, 9));
    SaveExtra e; memset(&e, 0, sizeof e); memcpy(e.note_px, face, sizeof e.note_px);
    note_art_parse(&art, blob, n);
    FILE *out = fopen(argv[3], "wb");
    for (int theme = 0; theme < 2; theme++)
        for (int dn = 0; dn < NOTE_DENOMS; dn++)
            for (int back = 0; back < 2; back++) {
                memset(px, 0, sizeof px);
                e.note_theme = theme; e.note_denom = dn; e.note_serial = 123456789u + dn;
                int w, h; note_card_size(dn, &w, &h);
                int x = (256 - w) / 2, y = (192 - h) / 2;
                note_draw(&c, x, y, &e, &art, back);
                for (int yy = 0; yy < 192; yy++)          // nothing drawn outside the card
                    for (int xx = 0; xx < 256; xx++)
                        if ((xx < x || yy < y || xx >= x + w || yy >= y + h) && px[yy * 256 + xx]) {
                            fprintf(stderr, "outside the card: (%d,%d) card (%d,%d %dx%d) theme %d value %d back %d colour %d\n",
                                    xx, yy, x, y, w, h, theme, dn, back, px[yy * 256 + xx]);
                            abort();
                        }
                u16 pal[NOTE_PAL_N]; note_palette(pal, dn);
                fwrite(pal, 2, NOTE_PAL_N, out); fwrite(px, 1, sizeof px, out);
            }
    fclose(out);
    return 0;
}
''')
            binary = d / 'test'
            subprocess.run(['cc', '-std=c11', '-O2', '-w', str(src), '-o', str(binary)], check=True)
            subprocess.run([str(binary), str(d / 'art.bin'), str(d / 'face.bin'), str(d / 'out.bin')], check=True)
            raw = (d / 'out.bin').read_bytes()
        from PIL import Image
        frame = 96 + 256 * 192
        sheet = Image.new('RGB', (256 * 4, 192 * 6))
        for k in range(24):
            pal = struct.unpack('<48H', raw[k * frame:k * frame + 96])
            px = raw[k * frame + 96:(k + 1) * frame]
            rgb = bytearray()
            red_seen = foil_seen = False
            for v in px:
                if v == 0:
                    rgb += b'\x20\x28\x50'
                    continue
                c = pal[v - 1]
                rgb += bytes(((c & 31) << 3, (c >> 5 & 31) << 3, (c >> 10 & 31) << 3))
                red_seen |= v == 1 + 28
                foil_seen |= 21 <= v <= 26
            self.assertTrue(red_seen, f'SPECIMEN overprint missing on note {k}')
            if k % 2 == 0:
                self.assertTrue(foil_seen, f'foil stripe missing on note {k}')
            im = Image.frombytes('RGB', (256, 192), bytes(rgb))
            sheet.paste(im, ((k % 4) * 256, (k // 4) * 192))
            theme, dn, back = k // 12, (k // 2) % 6, k % 2
            im.save(out_dir / f"{['culture', 'birds'][theme]}_{[5, 10, 20, 50, 100, 200][dn]}_{['front', 'back'][back]}.png")
        sheet.save(out_dir / 'all.png')


if __name__ == '__main__':
    unittest.main()
