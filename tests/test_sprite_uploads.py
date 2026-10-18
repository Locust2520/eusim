"""Exercise production sprite uploads with different CPU-cache and DMA views."""
import unittest

from test_progression import function, run_c


PREAMBLE = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
#define COPY_MODE_HWORD 0
static u8 stale_ram[4096];
static int cpu_copies, dma_copies;
static void swiCopy(const void *src, void *dst, int flags) {
    assert(flags > 0 && flags <= 2048);
    cpu_copies++;
    memcpy(dst, src, flags * sizeof(u16));
}
// Model an ARM9 write still in cache: DMA sees older main RAM contents.
static void dmaCopy(const void *src, void *dst, u32 bytes) {
    dma_copies++;
    memcpy(dst, stale_ram, bytes);
}
static void dmaFillHalfWords(u16 value, void *dst, u32 bytes) {
    u16 *pixels = dst;
    for (u32 i = 0; i < bytes / 2; i++) pixels[i] = value;
}
'''


class SpriteUploadTests(unittest.TestCase):
    def test_cpu_upload_reads_fresh_pixels_for_all_sprite_sizes(self):
        run_c(PREAMBLE + function('source/sprite.c', 'void spr_upload(') + r'''
int main(void) {
    u16 source[2048], video[2050];
    const int sizes[] = {128, 256, 512, 1024, 2048, 4096};
    memset(stale_ram, 0x77, sizeof(stale_ram));
    for (int k = 0; k < 6; k++) {
        int bytes = sizes[k];
        for (int i = 0; i < 2048; i++) source[i] = (i % 3) ? 0 : 0x0102;
        memset(video, 0x55, sizeof(video));
        spr_upload(video + 1, source, bytes);
        assert(!memcmp(video + 1, source, bytes));
        assert(video[0] == 0x5555 && video[bytes / 2 + 1] == 0x5555);
    }
    assert(cpu_copies == 6 && dma_copies == 0);
}
''')

    def test_battle_loads_front_back_shiny_and_replacement_without_stale_pixels(self):
        run_c(PREAMBLE + r'''
enum { PAL_BATTLE_FOE = 3, PAL_BATTLE_ALLY = 4 };
typedef struct { int species; bool shiny; } Mon;
typedef struct { int ncolors; u16 pal[256]; const u8 *data; } SpriteSheet;
static struct { Mon *mon; } side[2];
static SpriteSheet sh_foe, sh_ally;
static u16 *gfx_foe, *gfx_ally;
static u8 art[2][4096];
static u16 palettes[2][4];
static int missing;
static void sheet_free(SpriteSheet *sheet) { memset(sheet, 0, sizeof(*sheet)); }
static bool creature_sheet_load(SpriteSheet *sheet, int species, bool back) {
    if (missing) return false;
    sheet->ncolors = 4;
    sheet->pal[0] = 0; sheet->pal[1] = 0x1234;
    sheet->pal[2] = 0x4321; sheet->pal[3] = 0x7fff;
    sheet->data = art[back ? 0 : 1];
    return true;
}
static const u8 *sheet_frame(SpriteSheet *sheet, int frame) { return sheet->data; }
static void spr_ext_pal(bool sub, int slot, const u16 *pal, int count) {
    assert(count == 4);
    memcpy(palettes[slot == PAL_BATTLE_FOE ? 1 : 0], pal, count * 2);
}
''' + function('source/sprite.c', 'void spr_upload(') + '\n' +
              function('source/battle.c', 'static void load_mon_gfx(int s)') + r'''
int main(void) {
    u16 front[2048], back[2048];
    Mon ally = {1, false}, foe = {2, false};
    side[0].mon = &ally; side[1].mon = &foe;
    gfx_ally = back; gfx_foe = front;
    memset(stale_ram, 0x77, sizeof(stale_ram));
    for (int generation = 0; generation < 3; generation++) {
        for (int s = 0; s < 2; s++) {
            // Transparent pixels change too: leftover traces must be erased.
            for (int i = 0; i < 4096; i++)
                art[s][i] = ((i + generation) % 7) ? 0 : 1 + (i + s) % 3;
            side[s].mon->shiny = generation == 1;
            load_mon_gfx(s);
        }
        assert(!memcmp(front, art[1], 4096));
        assert(!memcmp(back, art[0], 4096));
        u16 color = 0x1234;
        u16 expected = generation == 1
            ? ((color >> 5) & 31) | (((color >> 10) & 31) << 5) | ((color & 31) << 10)
            : color;
        assert(palettes[0][1] == expected && palettes[1][1] == expected);
    }
    assert(cpu_copies == 6 && dma_copies == 0);
    missing = 1; load_mon_gfx(0); load_mon_gfx(1);
    for (int i = 0; i < 2048; i++) assert(front[i] == 0 && back[i] == 0);
}
''')


if __name__ == '__main__':
    unittest.main()
