#include "canvas.h"
#include "lang.h"
#include "gfx.h"

Canvas g_top, g_bot;
static u8 top_px[256 * 192] __attribute__((aligned(32)));
static u8 bot_px[256 * 192] __attribute__((aligned(32)));

void canvas_init(void)
{
    g_top.px = top_px;
    g_top.vram = (u16 *)bgGetGfxPtr(g_bg_main[3]);
    g_bot.px = bot_px;
    g_bot.vram = (u16 *)bgGetGfxPtr(g_bg_sub[3]);
    canvas_clear(&g_top, 0);
    canvas_clear(&g_bot, 0);
    canvas_flush(&g_top);
    canvas_flush(&g_bot);
}

void canvas_dirty(Canvas *c, int y0, int y1)
{
    y0 = CLAMP(y0, 0, 192);
    y1 = CLAMP(y1, 0, 192);
    if (y0 >= y1)
        return;
    if (c->dirty_y1 <= c->dirty_y0) {
        c->dirty_y0 = y0;
        c->dirty_y1 = y1;
    } else {
        if (y0 < c->dirty_y0)
            c->dirty_y0 = y0;
        if (y1 > c->dirty_y1)
            c->dirty_y1 = y1;
    }
}

void canvas_flush(Canvas *c)
{
    if (c->dirty_y1 <= c->dirty_y0)
        return;
    int y0 = c->dirty_y0, y1 = c->dirty_y1;
    u8 *src = c->px + y0 * 256;
    int bytes = (y1 - y0) * 256;
    DC_FlushRange(src, bytes);
    dmaCopyWords(3, src, (u8 *)c->vram + y0 * 256, bytes);
    c->dirty_y0 = c->dirty_y1 = 0;
}

void canvas_clear(Canvas *c, u8 col)
{
    memset(c->px, col, 256 * 192);
    canvas_dirty(c, 0, 192);
}

void canvas_rect(Canvas *c, int x, int y, int w, int h, u8 col)
{
    if (x < 0) { w += x; x = 0; }
    if (y < 0) { h += y; y = 0; }
    if (x + w > 256) w = 256 - x;
    if (y + h > 192) h = 192 - y;
    if (w <= 0 || h <= 0)
        return;
    for (int j = 0; j < h; j++)
        memset(c->px + (y + j) * 256 + x, col, w);
    canvas_dirty(c, y, y + h);
}

void canvas_hline(Canvas *c, int x, int y, int w, u8 col) { canvas_rect(c, x, y, w, 1, col); }
void canvas_vline(Canvas *c, int x, int y, int h, u8 col) { canvas_rect(c, x, y, 1, h, col); }

void canvas_box(Canvas *c, int x, int y, int w, int h, u8 col)
{
    canvas_hline(c, x, y, w, col);
    canvas_hline(c, x, y + h - 1, w, col);
    canvas_vline(c, x, y, h, col);
    canvas_vline(c, x + w - 1, y, h, col);
}

void canvas_pixel(Canvas *c, int x, int y, u8 col)
{
    if ((unsigned)x < 256 && (unsigned)y < 192) {
        c->px[y * 256 + x] = col;
        canvas_dirty(c, y, y + 1);
    }
}

static void draw_glyph(Canvas *c, const Font *f, const FontGlyph *g, int x, int y, u8 col)
{
    const u16 *b = f->bits + g->off;
    int gx = x + g->lsb;
    for (int j = 0; j < g->h; j++) {
        int py = y + g->y + j;
        if ((unsigned)py >= 192)
            continue;
        u16 row = b[j];
        u8 *line = c->px + py * 256;
        for (int i = 0; i < g->w; i++) {
            if (row & (0x8000 >> i)) {
                int px = gx + i;
                if ((unsigned)px < 256)
                    line[px] = col;
            }
        }
    }
}

int canvas_text_n(Canvas *c, const Font *f, int x, int y, const char *s, int nbytes, u8 col, u8 shadow)
{
    const char *end = s + nbytes;
    int x0 = x, maxw = 0;
    int y0 = y;
    while (*s && s < end) {
        if (*s == '\n') {
            s++;
            maxw = MAX(maxw, x - x0);
            x = x0;
            y += f->line_h;
            continue;
        }
        u32 code = utf8_next(&s);
        const FontGlyph *g = font_glyph(f, code);
        if (!g)
            continue;
        if (shadow) {
            draw_glyph(c, f, g, x + 1, y, shadow);
            draw_glyph(c, f, g, x, y + 1, shadow);
            draw_glyph(c, f, g, x + 1, y + 1, shadow);
        }
        draw_glyph(c, f, g, x, y, col);
        x += g->adv + g_text_track;
    }
    canvas_dirty(c, y0, y + f->line_h + 1);
    return MAX(maxw, x - x0);
}

int canvas_text(Canvas *c, const Font *f, int x, int y, const char *s, u8 col, u8 shadow)
{
    s = tr(s);
    return canvas_text_n(c, f, x, y, s, 1 << 30, col, shadow);
}

void canvas_text_center(Canvas *c, const Font *f, int cx, int y, const char *s, u8 col, u8 shadow)
{
    s = tr(s);
    canvas_text(c, f, cx - font_width(f, s) / 2, y, s, col, shadow);
}

void canvas_text_right(Canvas *c, const Font *f, int rx, int y, const char *s, u8 col, u8 shadow)
{
    s = tr(s);
    canvas_text(c, f, rx - font_width(f, s), y, s, col, shadow);
}

void canvas_blit(Canvas *c, int x, int y, int w, int h, const u8 *src, int add)
{
    for (int j = 0; j < h; j++) {
        int py = y + j;
        if ((unsigned)py >= 192)
            continue;
        const u8 *s = src + j * w;
        u8 *d = c->px + py * 256;
        for (int i = 0; i < w; i++) {
            u8 v = s[i];
            int px = x + i;
            if (v && (unsigned)px < 256)
                d[px] = v + add;
        }
    }
    canvas_dirty(c, y, y + h);
}

void canvas_blit_scaled2(Canvas *c, int x, int y, int w, int h, const u8 *src, int add)
{
    for (int j = 0; j < h * 2; j++) {
        int py = y + j;
        if ((unsigned)py >= 192)
            continue;
        const u8 *s = src + (j >> 1) * w;
        u8 *d = c->px + py * 256;
        for (int i = 0; i < w * 2; i++) {
            u8 v = s[i >> 1];
            int px = x + i;
            if (v && (unsigned)px < 256)
                d[px] = v + add;
        }
    }
    canvas_dirty(c, y, y + h * 2);
}

static void frame_round(Canvas *c, int x, int y, int w, int h, u8 col)
{
    canvas_rect(c, x + 2, y, w - 4, h, col);
    canvas_rect(c, x + 1, y + 1, w - 2, h - 2, col);
    canvas_rect(c, x, y + 2, w, h - 4, col);
}

static void frame_grad(Canvas *c, int x, int y, int w, int h, u8 top, u8 mid, u8 bot)
{
    // three bands with a dithered seam (same look as ui_gradient)
    int b1 = h / 3, b2 = (2 * h) / 3;
    for (int j = 0; j < h; j++) {
        int py = y + j;
        if ((unsigned)py >= 192)
            continue;
        u8 col = j < b1 ? top : j < b2 ? mid : bot;
        u8 nxt = j < b1 ? mid : bot;
        bool seam = j == b1 - 1 || j == b2 - 1;
        u8 *line = c->px + py * 256;
        for (int i = 0; i < w; i++) {
            int px = x + i;
            if ((unsigned)px < 256)
                line[px] = (seam && ((i + j) & 1)) ? nxt : col;
        }
    }
    canvas_dirty(c, y, y + h);
}

// Retro bevelled panels; everything stays inside (x, y, w, h), drop shadow included.
void canvas_frame(Canvas *c, int x, int y, int w, int h, FrameStyle st)
{
    if (w < 8 || h < 8)
        return;
    int bw = w - 1, bh = h - 1;
    frame_round(c, x + 1, y + 1, bw, bh, C_INK); // drop shadow
    switch (st) {
    case FRAME_MENU:
        frame_round(c, x, y, bw, bh, C_BTN_SH);
        frame_grad(c, x + 2, y + 2, bw - 4, bh - 4, C_WHITE, C_BTN_HI, C_BTN_MID);
        canvas_hline(c, x + 3, y + 1, bw - 6, C_BTN_LO);
        canvas_hline(c, x + 3, y + bh - 3, bw - 6, C_BTN_LO);
        canvas_vline(c, x + 2, y + 3, bh - 6, C_WHITE);
        break;
    case FRAME_GOLD:
    case FRAME_SELECT:
        frame_round(c, x, y, bw, bh, C_GOLD_D);
        frame_grad(c, x + 2, y + 2, bw - 4, bh - 4, C_GLD_HI, C_GLD_HI, C_GLD_MID);
        canvas_hline(c, x + 3, y + 1, bw - 6, C_GOLD);
        canvas_hline(c, x + 3, y + bh - 3, bw - 6, C_GLD_LO);
        canvas_vline(c, x + 2, y + 3, bh - 6, C_WHITE);
        if (st == FRAME_SELECT) {
            extern void ui_target_corners(Canvas *, int, int, int, int);
            ui_target_corners(c, x, y, bw, bh);
        }
        break;
    case FRAME_DARK:
        frame_round(c, x, y, bw, bh, C_INK);
        frame_grad(c, x + 2, y + 2, bw - 4, bh - 4, C_NAVY2, C_BLUE_D, C_NAVY1);
        canvas_hline(c, x + 3, y + 1, bw - 6, C_GOLD_D);
        canvas_hline(c, x + 3, y + 2, bw - 6, C_NAVY2);
        break;
    default: { // FRAME_DIALOG: white card, rounded, blue band with a gold hairline and jewelled corners
        frame_round(c, x, y, bw, bh, C_INK);
        frame_round(c, x + 1, y + 1, bw - 2, bh - 2, C_BLUE);
        canvas_hline(c, x + 4, y + 2, bw - 8, C_GOLD);
        canvas_hline(c, x + 4, y + bh - 3, bw - 8, C_GOLD_D);
        canvas_vline(c, x + 2, y + 4, bh - 8, C_GOLD);
        canvas_vline(c, x + bw - 3, y + 4, bh - 8, C_GOLD_D);
        canvas_rect(c, x + 3, y + 3, bw - 6, bh - 6, C_WHITE);
        canvas_dialog_corners(c, x, y, w, h);
        // jewels on the four corners: a gold diamond with a white glint
        int px[4] = {x + 2, x + bw - 3, x + 2, x + bw - 3}, py[4] = {y + 2, y + 2, y + bh - 3, y + bh - 3};
        for (int k = 0; k < 4; k++) {
            canvas_rect(c, px[k] - 1, py[k], 3, 1, C_GOLD);
            canvas_rect(c, px[k], py[k] - 1, 1, 3, C_GOLD);
            canvas_rect(c, px[k] - 2, py[k], 1, 1, C_GOLD_D);
            canvas_rect(c, px[k] + 2, py[k], 1, 1, C_GOLD_D);
            canvas_rect(c, px[k], py[k] - 2, 1, 1, C_GOLD_D);
            canvas_rect(c, px[k], py[k] + 2, 1, 1, C_GOLD_D);
            canvas_rect(c, px[k], py[k], 1, 1, C_WHITE);
        }
        break;
    }
    }
}

// Rounded inner corners of the dialog card (redrawn after the text area is cleared)
void canvas_dialog_corners(Canvas *c, int x, int y, int w, int h)
{
    int bw = w - 1, bh = h - 1;
    int ix0 = x + 3, iy0 = y + 3, ix1 = x + bw - 4, iy1 = y + bh - 4;
    canvas_rect(c, ix0, iy0, 2, 1, C_BLUE);
    canvas_rect(c, ix0, iy0, 1, 2, C_BLUE);
    canvas_rect(c, ix1 - 1, iy0, 2, 1, C_BLUE);
    canvas_rect(c, ix1, iy0, 1, 2, C_BLUE);
    canvas_rect(c, ix0, iy1, 2, 1, C_BLUE);
    canvas_rect(c, ix0, iy1 - 1, 1, 2, C_BLUE);
    canvas_rect(c, ix1 - 1, iy1, 2, 1, C_BLUE);
    canvas_rect(c, ix1, iy1 - 1, 1, 2, C_BLUE);
}

// Checkerboard in absolute screen coordinates (so partial redraws line up)
void canvas_checker(Canvas *c, int x, int y, int w, int h, u8 a, u8 b, int size)
{
    for (int j = MAX(y, 0); j < MIN(y + h, 192); j++) {
        u8 *line = c->px + j * 256;
        int row = (j / size) & 1;
        for (int i = MAX(x, 0); i < MIN(x + w, 256); i++)
            line[i] = (((i / size) & 1) ^ row) ? b : a;
    }
    canvas_dirty(c, y, y + h);
}

void canvas_bar(Canvas *c, int x, int y, int w, int h, int val, int max, u8 col)
{
    canvas_rect(c, x, y, w, h, C_DGREY);
    int fw = max > 0 ? (val * (w - 2) + max - 1) / max : 0;
    fw = CLAMP(fw, 0, w - 2);
    canvas_rect(c, x + 1, y + 1, w - 2, h - 2, C_LGREY);
    if (fw > 0)
        canvas_rect(c, x + 1, y + 1, fw, h - 2, col);
}
