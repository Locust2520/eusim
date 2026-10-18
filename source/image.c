#include "image.h"
#include "gfx.h"
#include "fs.h"

int bgi_load(bool sub, int layer, const char *path, int tile_base_index)
{
    u32 size;
    u8 *d = fs_try_load(path, &size);
    if (!d)
        return -1;
    if (memcmp(d, "BGI1", 4) != 0) {
        free(d);
        return -1;
    }
    int wt = d[4] | (d[5] << 8);
    int ht = d[6] | (d[7] << 8);
    int ncol = d[8] | (d[9] << 8);
    int pal_base = d[10] | (d[11] << 8);
    const u8 *p = d + 12;
    u16 *palette = sub ? BG_PALETTE_SUB : BG_PALETTE;
    for (int i = 0; i < ncol; i++)
        palette[pal_base + i] = p[i * 2] | (p[i * 2 + 1] << 8);
    p += ncol * 2;
    int ntiles = p[0] | (p[1] << 8);
    p += 2;
    u16 *tiles = sub ? SUB_TILES : MAIN_TILES;
    DC_FlushRange(p, ntiles * 64);
    dmaCopy(p, (u8 *)tiles + tile_base_index * 64, ntiles * 64);
    p += ntiles * 64;
    const u16 *map = (const u16 *)p; // may be unaligned: copy bytewise
    int *bgs = sub ? g_bg_sub : g_bg_main;
    u16 *dst = (u16 *)bgGetMapPtr(bgs[layer]);
    // text BG 512x512 (main BG0/BG1) is 64 wide in 4 screen blocks; others 32 wide
    bool text64 = !sub && layer < 2;
    int mapw = (!sub && layer == 2) ? 64 : 32;
    for (int y = 0; y < ht; y++) {
        for (int x = 0; x < wt; x++) {
            const u8 *e = (const u8 *)&map[y * wt + x];
            u16 v = e[0] | (e[1] << 8);
            u16 t = (v & 0x3FF) + tile_base_index;
            u16 ent = t | (v & 0x0C00);
            int idx;
            if (text64) {
                int blk = (x >= 32 ? 1 : 0) + (y >= 32 ? 2 : 0);
                idx = blk * 1024 + (y & 31) * 32 + (x & 31);
            } else {
                idx = y * mapw + x;
            }
            if (x < 64 && y < 64)
                dst[idx] = ent;
        }
    }
    free(d);
    return ntiles;
}

bool bmp_load(Bitmap *b, const char *path)
{
    memset(b, 0, sizeof(*b));
    u32 size;
    u8 *d = fs_try_load(path, &size);
    if (!d)
        return false;
    if (memcmp(d, "BMP8", 4) != 0) {
        free(d);
        return false;
    }
    b->w = d[4] | (d[5] << 8);
    b->h = d[6] | (d[7] << 8);
    b->ncol = d[8] | (d[9] << 8);
    const u8 *p = d + 10;
    for (int i = 0; i < b->ncol && i < 256; i++)
        b->pal[i] = p[i * 2] | (p[i * 2 + 1] << 8);
    p += b->ncol * 2;
    b->px = malloc(b->w * b->h);
    memcpy(b->px, p, b->w * b->h);
    free(d);
    return true;
}

void bmp_free(Bitmap *b)
{
    if (b->px)
        free(b->px);
    b->px = NULL;
}

void bmp_draw(Canvas *c, const Bitmap *b, int x, int y, int pal_base)
{
    u16 *palette = (c == &g_bot) ? BG_PALETTE_SUB : BG_PALETTE;
    for (int i = 0; i < b->ncol; i++)
        palette[pal_base + i] = b->pal[i];
    canvas_blit(c, x, y, b->w, b->h, b->px, pal_base - 1);
}
