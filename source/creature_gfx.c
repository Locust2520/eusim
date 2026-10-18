#include "creature_gfx.h"
#include "gfx.h"
#include "fs.h"

static u8 *icons;      // "ICN1" u16 n u16 ncol pal[ncol] pixels[n][32*32]
static int icon_n, icon_ncol;
static const u16 *icon_pal;
static const u8 *icon_px;

static void icons_load(void)
{
    if (icons)
        return;
    u32 size;
    icons = fs_try_load("creatures/icons.bin", &size);
    if (!icons)
        return;
    icon_n = icons[4] | (icons[5] << 8);
    icon_ncol = icons[6] | (icons[7] << 8);
    icon_pal = (const u16 *)(icons + 8);
    icon_px = icons + 8 + icon_ncol * 2;
}

void creature_icon_draw(Canvas *c, int sp, int x, int y)
{
    icons_load();
    if (!icons || sp < 0 || sp >= icon_n)
        return;
    u16 *pal = (c == &g_bot) ? BG_PALETTE_SUB : BG_PALETTE;
    for (int i = 1; i <= icon_ncol && i < 32; i++)
        pal[C_DYN - 1 + i] = icon_pal[i];
    canvas_blit(c, x, y - 4, 32, 32, icon_px + sp * 1024, C_DYN - 1);
}

bool creature_sheet_load(SpriteSheet *s, int sp, bool back)
{
    char path[40];
    snprintf(path, sizeof path, "creatures/%c%d.spr", back ? 'b' : 'f', sp);
    return sheet_load(s, path);
}

void creature_big_draw(Canvas *c, int sp, int x, int y)
{
    SpriteSheet s;
    if (!creature_sheet_load(&s, sp, false))
        return;
    u16 *pal = (c == &g_bot) ? BG_PALETTE_SUB : BG_PALETTE;
    int n = MIN(s.ncolors, 32);
    for (int i = 1; i < n; i++)
        pal[C_DYN - 1 + i] = s.pal[i];
    // de-tile the 64x64 8bpp frame
    const u8 *f = sheet_frame(&s, 0);
    static u8 lin[64 * 64];
    for (int t = 0; t < 64; t++) {
        int tx = (t % 8) * 8, ty = (t / 8) * 8;
        for (int k = 0; k < 64; k++)
            lin[(ty + k / 8) * 64 + tx + k % 8] = f[t * 64 + k];
    }
    canvas_blit(c, x, y, 64, 64, lin, C_DYN - 1);
    sheet_free(&s);
}
