#include <string.h>
#include "ui.h"
#include "lang.h"
#include "gfx.h"
#include "input.h"
#include "save.h"
#include "gen/font_data.h"
#include "gen/mona_icons.h"

int ui_font_cap_top(const Font *f) { return f == &font_main ? 3 : 2; }
int ui_font_cap_h(const Font *f) { return f == &font_main ? 11 : 9; }

// vertical gradient in three bands with a dithered seam between bands (retro look)
void ui_gradient(Canvas *c, int x, int y, int w, int h, u8 top, u8 mid, u8 bottom)
{
    if (w <= 0 || h <= 0)
        return;
    int b1 = h / 3, b2 = (2 * h) / 3;
    for (int j = 0; j < h; j++) {
        u8 col = j < b1 ? top : j < b2 ? mid : bottom;
        int py = y + j;
        if ((unsigned)py >= 192)
            continue;
        u8 *line = c->px + py * 256;
        bool seam = (j == b1 - 1) || (j == b2 - 1);
        u8 next = j < b1 ? mid : bottom;
        for (int i = 0; i < w; i++) {
            int px = x + i;
            if ((unsigned)px >= 256)
                continue;
            line[px] = (seam && ((i + j) & 1)) ? next : col;
        }
    }
    canvas_dirty(c, y, y + h);
}

static void rounded_rect(Canvas *c, int x, int y, int w, int h, u8 col)
{
    canvas_rect(c, x + 2, y, w - 4, h, col);
    canvas_rect(c, x + 1, y + 1, w - 2, h - 2, col);
    canvas_rect(c, x, y + 2, w, h - 4, col);
}

void ui_text_in(Canvas *c, const Font *f, int x, int y, int w, int h, const char *s, u8 col, u8 shadow, int align)
{
    s = tr(s);
    // too long for the box (translations vary a lot in length): fall back to the small font
    if (f == &font_main && font_width(f, s) > w - 4 && font_width(&font_small, s) <= font_width(f, s))
        f = &font_small;
    // still too long: condense the letter spacing a little, then cut with an ellipsis
    int avail = align == 0 ? w - 2 : w - 5;
    int track = 0;
    while (track > -2 && font_width(f, s) > avail) {
        track--;
        g_text_track = track;
    }
    int n = strlen(s);
    if (font_width(f, s) > avail) {
        int ew = font_width(f, "…");
        while (n > 0 && font_width_n(f, s, n) + ew > avail) {
            n--;
            while (n > 0 && (s[n] & 0xC0) == 0x80)
                n--;
        }
    }
    bool cut = n < (int)strlen(s);
    int ty = y + (h - ui_font_cap_h(f)) / 2 - ui_font_cap_top(f);
    int tw = font_width_n(f, s, n) + (cut ? font_width(f, "…") : 0);
    int tx = align == 0 ? x + (w - tw) / 2 : align < 0 ? x + 4 : x + w - tw - 4;
    if (tx < x + 1)
        tx = x + 1;
    int ew2 = canvas_text_n(c, f, tx, ty, s, n, col, shadow);
    if (cut)
        canvas_text_n(c, f, tx + ew2, ty, "…", 8, col, shadow);
    g_text_track = 0;
}

void ui_button(Canvas *c, int x, int y, int w, int h, const char *label, BtnStyle st, const Font *f)
{
    u8 hi, mid, lo, edge, txt, sh;
    int press = 0;
    switch (st) {
    case BTN_SELECTED: hi = C_GLD_HI; mid = C_GLD_MID; lo = C_GOLD; edge = C_GOLD_D; txt = C_INK; sh = C_GLD_HI; break;
    case BTN_PRESSED: hi = C_GLD_MID; mid = C_GOLD; lo = C_GLD_LO; edge = C_GOLD_D; txt = C_INK; sh = C_GLD_HI; press = 1; break;
    case BTN_DARK: hi = C_NAVY2; mid = C_BLUE_D; lo = C_NAVY1; edge = C_INK; txt = C_GOLD; sh = C_INK; break;
    case BTN_RED: hi = C_RED_HI; mid = C_RED; lo = C_RED_D; edge = C_INK; txt = C_WHITE; sh = C_RED_D; break;
    case BTN_GREEN: hi = C_GREEN_HI; mid = C_GREEN; lo = C_TYPE0 + 5; edge = C_INK; txt = C_INK; sh = C_GREEN_HI; break;
    case BTN_DISABLED: hi = C_LGREY; mid = C_LGREY; lo = C_MGREY; edge = C_DGREY; txt = C_MGREY; sh = 0; break;
    default: hi = C_BTN_HI; mid = C_BTN_MID; lo = C_BTN_LO; edge = C_INK; txt = C_INK; sh = C_BTN_HI; break;
    }
    // drop shadow
    if (!press)
        rounded_rect(c, x + 2, y + 2, w, h, C_INK);
    x += press;
    y += press;
    rounded_rect(c, x, y, w, h, edge);
    ui_gradient(c, x + 2, y + 2, w - 4, h - 4, hi, mid, lo);
    // bevel: top highlight, bottom shadow
    canvas_hline(c, x + 3, y + 2, w - 6, C_WHITE);
    canvas_hline(c, x + 3, y + h - 3, w - 6, st == BTN_NORMAL ? C_BTN_SH : edge);
    canvas_vline(c, x + 2, y + 3, h - 6, st == BTN_DARK ? C_NAVY2 : C_WHITE);
    if (label && label[0])
        ui_text_in(c, f ? f : &font_main, x, y, w, h, label, txt, sh, 0);
    if (st == BTN_SELECTED || st == BTN_PRESSED)
        ui_target_corners(c, x, y, w, h);
}

// "Lock-on" brackets on the four corners of the selected button (drawn inside its own area, so redrawing
// the button unselected erases them).
void ui_target_corners(Canvas *c, int x, int y, int w, int h)
{
    const int L = MIN(10, MIN(w, h) / 2 - 1);
    int cx[4] = {x, x + w - 1, x, x + w - 1}, cy[4] = {y, y, y + h - 1, y + h - 1};
    int sx[4] = {1, -1, 1, -1}, sy[4] = {1, 1, -1, -1};
    static const u8 band[4] = {C_WHITE, C_RED, C_RED, C_INK}; // outer edge -> inside
    for (int k = 0; k < 4; k++)
        for (int t = 0; t < 4; t++)
            for (int i = t; i < L; i++) {
                u8 col = (t == 3 && i < 4) ? C_RED : band[t];
                if (t == 3 && i == L - 1)
                    continue;
                canvas_rect(c, cx[k] + sx[k] * i, cy[k] + sy[k] * t, 1, 1, i == L - 1 ? C_INK : col);
                canvas_rect(c, cx[k] + sx[k] * t, cy[k] + sy[k] * i, 1, 1, i == L - 1 ? C_INK : col);
            }
}

static const char *const icons[ICON_COUNT][12] = {
    {"....aaaa....", "...aaaaaa...", "..aakaakaa..", "..aaaaaaaa..", "..aakkkkaa..", "...aaaaaa...",
     "....bbbb....", "..bbbbbbbb..", ".bbbbbbbbbb.", ".bbbbbbbbbb.", ".bbb....bbb.", "............"},
    {"....kkkk....", "...k....k...", "..kkkkkkkkk.", ".krrrrrrrrk.", ".krrrraarrk.", ".krrraaaark.",
     ".krrrraarrk.", ".krrrrrrrrk.", ".krrrrrrrrk.", ".kkkkkkkkkk.", "............", "............"},
    {".kkkkkkkkkk.", ".krrrrrrrrk.", ".krwwwwwwrk.", ".krwbbbbwrk.", ".krwwwwwwrk.", ".krrrrrrrrk.",
     ".krarrbrrrk.", ".krrrrrrrrk.", ".kkkkkkkkkk.", "............", "............", "............"},
    {"kkkkkkkkkkkk", "kggbbbbgggbk", "kggbbbgggbbk", "kgbbbggggbbk", "kgbbggrggbbk", "kbbbgggggbbk",
     "kbbbbggbbbbk", "kbbbbbbbbbbk", "kkkkkkkkkkkk", "............", "............", "............"},
    {".kkkkkkkkkk.", ".kwwwwwwwwk.", ".kwkkkkkkwk.", ".kwwwwwwwwk.", ".kwkkkkkwwk.", ".kwwwwwwwwk.",
     ".kwkkkkwwwk.", ".kwwwwwwrrk.", ".kwwwwwwrrk.", ".kkkkkkkkkk.", "............", "............"},
    {"....kkkk....", "..kkwwwwkk..", ".kwwkkkkwwk.", ".kwkk..kkwk.", "kwwk....kwwk", "kwwk....kwwk",
     ".kwkk..kkwk.", ".kwwkkkkwwk.", "..kkwwwwkk..", "....kkkk....", "............", "............"},
    {"..........kk", ".........kwk", "........kwk.", ".......kwk..", "..kk..kwk...", "...kkkwk....",
     "....kkk.....", "...kkkkk....", "..kk..kk....", ".kk.........", "............", "............"},
    {"......kk....", ".....kaak...", "....kaak....", "...kkkkkk...", "..k.kaak.k..", "....kaak....",
     "...kk..kk...", "..kk....kk..", ".kk......kk.", "............", "............", "............"},
    {".....aa.....", ".....aa.....", "....aaaa....", "aaaaaaaaaaaa", ".aaaaaaaaaa.", "..aaaaaaaa..",
     "...aaaaaa...", "..aaa..aaa..", ".aaa....aaa.", ".aa......aa.", "............", "............"},
};

void ui_icon(Canvas *c, int x, int y, int icon, int scale)
{
    if (icon < 0 || icon >= ICON_COUNT)
        return;
    int mona = -1;
    switch (icon) {
    case ICON_TEAM: mona = 0; break;
    case ICON_BAG: mona = 1; break;
    case ICON_SAVE: mona = 2; break;
    case ICON_OPTIONS: mona = 3; break;
    case ICON_RUN: mona = g_save.player_gender == 0 ? 4 : 5; break;
    }
    if (mona >= 0) {
        // All Mona icons share one palette so drawing one preserves the others.
        gfx_bg_pal(c == &g_bot, C_DYN, mona_icon_palette, MONA_ICON_COLORS);
        for (int yy = 0; yy < 12; yy++)
            for (int xx = 0; xx < 12; xx++) {
                u8 pixel = mona_icon_pixels[mona][yy * 12 + xx];
                if (pixel)
                    canvas_rect(c, x + xx * scale, y + yy * scale, scale, scale, C_DYN + pixel - 1);
            }
        return;
    }
    for (int yy = 0; yy < 12; yy++)
        for (int xx = 0; xx < 12; xx++) {
            u8 col = 0;
            switch (icons[icon][yy][xx]) {
            case 'k': col = C_INK; break;
            case 'a': col = C_GOLD; break;
            case 'b': col = C_BLUE; break;
            case 'r': col = C_RED; break;
            case 'w': col = C_WHITE; break;
            case 'g': col = C_GREEN; break;
            }
            if (col)
                canvas_rect(c, x + xx * scale, y + yy * scale, scale, scale, col);
        }
}

void ui_button_icon(Canvas *c, int x, int y, int w, int h, const char *label, BtnStyle st, int icon)
{
    ui_button(c, x, y, w, h, NULL, st, NULL);
    int press = st == BTN_PRESSED;
    int isz = 24;
    ui_icon(c, x + 8 + press, y + (h - isz) / 2 + press, icon, 2);
    u8 txt = st == BTN_DARK ? C_GOLD : C_INK;
    u8 sh = st == BTN_DARK ? C_INK : (st == BTN_SELECTED ? C_GLD_HI : C_BTN_HI);
    ui_text_in(c, &font_main, x + 36 + press, y + press, w - 40, h, label, txt, sh, -1);
}

void ui_panel(Canvas *c, int x, int y, int w, int h, bool dark)
{
    rounded_rect(c, x + 2, y + 2, w, h, C_INK);
    rounded_rect(c, x, y, w, h, dark ? C_GOLD_D : C_INK);
    if (dark) {
        ui_gradient(c, x + 2, y + 2, w - 4, h - 4, C_NAVY2, C_BLUE_D, C_NAVY1);
        canvas_hline(c, x + 3, y + 2, w - 6, C_GOLD);
    } else {
        canvas_rect(c, x + 2, y + 2, w - 4, h - 4, C_WHITE);
        canvas_hline(c, x + 3, y + 2, w - 6, C_BTN_MID);
        canvas_hline(c, x + 3, y + h - 3, w - 6, C_BTN_LO);
    }
}

void ui_header(Canvas *c, int x, int y, int w, const char *text)
{
    text = tr(text);
    ui_panel(c, x, y, w, 22, true);
    ui_text_in(c, &font_main, x, y, w, 22, text, C_GOLD, C_INK, 0);
}

void ui_backdrop(Canvas *c)
{
    // navy gradient filling the whole screen, with a faint grid of gold dots (EU stars)
    for (int y = 0; y < 192; y++) {
        u8 col = y < 64 ? C_NAVY1 : y < 128 ? C_BLUE_D : C_NAVY2;
        memset(c->px + y * 256, col, 256);
        if (y == 63 || y == 127)
            for (int x = (y & 1); x < 256; x += 2)
                c->px[y * 256 + x] = y < 64 ? C_BLUE_D : C_NAVY2;
    }
    // subtle tone-on-tone star crosses: a texture, not stray pixels
    for (int y = 8; y < 192; y += 24)
        for (int x = ((y / 24) & 1) * 12 + 6; x < 256; x += 24) {
            u8 col = y < 64 ? C_BLUE_D : C_NAVY1;
            c->px[y * 256 + x] = col;
            if (x > 0) c->px[y * 256 + x - 1] = col;
            if (x < 255) c->px[y * 256 + x + 1] = col;
            if (y > 0) c->px[(y - 1) * 256 + x] = col;
            if (y < 191) c->px[(y + 1) * 256 + x] = col;
        }
    canvas_dirty(c, 0, 192);
}

void ui_backdrop_rect(Canvas *c, int x, int y, int w, int h)
{
    // repaint part of the standard backdrop (same pattern as ui_backdrop)
    for (int j = y; j < y + h; j++) {
        if ((unsigned)j >= 192)
            continue;
        u8 col = j < 64 ? C_NAVY1 : j < 128 ? C_BLUE_D : C_NAVY2;
        for (int i = x; i < x + w; i++) {
            if ((unsigned)i >= 256)
                continue;
            u8 v = col;
            if ((j == 63 || j == 127) && ((i ^ j) & 1) == 0)
                v = j < 64 ? C_BLUE_D : C_NAVY2;
            int sx = ((j + 1) / 24) * 24 + 8, ox = ((sx / 24) & 1) * 12 + 6;
            int dy = j - sx, dx = ((i - ox) % 24 + 24) % 24;
            if (dx > 12)
                dx -= 24;
            if ((dy == 0 && dx >= -1 && dx <= 1) || (dx == 0 && (dy == -1 || dy == 1)))
                v = sx < 64 ? C_BLUE_D : C_NAVY1;
            c->px[j * 256 + i] = v;
        }
    }
    canvas_dirty(c, y, y + h);
}

int ui_text_wrapped(Canvas *c, const Font *f, int x, int y, int w, const char *s, u8 col, u8 shadow)
{
    s = tr(s);
    char line[96];
    while (*s) {
        int n = 0, sp = -1;
        while (s[n] && s[n] != '\n' && font_width_n(f, s, n + 1) <= w) {
            if (s[n] == ' ')
                sp = n;
            n++;
        }
        if (s[n] && s[n] != '\n' && sp > 0)
            n = sp;
        if (n == 0 && s[0] != '\n')
            n = 1;
        memcpy(line, s, MIN(n, 95));
        line[MIN(n, 95)] = 0;
        int lw = font_width(f, line);
        canvas_text(c, f, x + (w - lw) / 2, y, line, col, shadow);
        s += n;
        while (*s == ' ' || *s == '\n')
            s++;
        y += f->line_h;
    }
    return y;
}

// ---------------------------------------------------------------- scrollbar (stylus only)
// A track on the right of a long list with a gold thumb sized to the visible part. Dragging the thumb (or
// tapping the track) scrolls the list; the D-pad keeps moving the selection as before.
void ui_scrollbar(Canvas *c, int x, int y, int h, int total, int vis, int first)
{
    canvas_rect(c, x + 1, y, SB_W - 2, h, C_INK);
    canvas_rect(c, x, y + 1, SB_W, h - 2, C_INK);
    canvas_rect(c, x + 1, y + 1, SB_W - 2, h - 2, C_NAVY1);
    for (int j = y + 3; j < y + h - 3; j += 4)
        canvas_rect(c, x + SB_W / 2, j, 1, 1, C_NAVY2);
    if (total <= vis)
        return;
    int th = MAX(12, (h - 2) * vis / total);
    int ty = y + 1 + (h - 2 - th) * first / (total - vis);
    canvas_rect(c, x + 2, ty, SB_W - 4, th, C_GOLD_D);
    canvas_rect(c, x + 1, ty + 1, SB_W - 2, th - 2, C_GOLD_D);
    canvas_rect(c, x + 2, ty + 1, SB_W - 4, th - 2, C_GLD_MID);
    canvas_rect(c, x + 2, ty + 1, 1, th - 2, C_GLD_HI);
    canvas_rect(c, x + 2, ty + 1, SB_W - 4, 1, C_GLD_HI);
    for (int k = -1; k <= 1; k++)
        canvas_rect(c, x + 3, ty + th / 2 + k * 2, SB_W - 6, 1, C_GOLD_D);
}

int ui_scrollbar_drag(int x, int y, int h, int total, int vis)
{
    static bool dragging;
    if (total <= vis) {
        dragging = false;
        return -1;
    }
    if (g_touch_down && g_touch_x >= x - 6 && g_touch_x < x + SB_W + 4 && g_touch_y >= y - 4 && g_touch_y < y + h + 4)
        dragging = true;
    if (!g_touch_held && !g_touch_down)
        dragging = false;
    if (!dragging)
        return -1;
    int th = MAX(12, (h - 2) * vis / total);
    int span = h - 2 - th;
    int f = span > 0 ? ((g_touch_y - y - 1 - th / 2) * (total - vis) + span / 2) / span : 0;
    return CLAMP(f, 0, total - vis);
}
