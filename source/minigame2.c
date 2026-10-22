// City mini-games: Frankfurt (ECB studio, apple-wine tavern), Athens, Piraeus, Brussels, Strasbourg, London,
// Budapest, Paris and Luxembourg. Each teaches the fact behind it in its intro or result line.
#include "minigame.h"
#include "minigame_ui.h"
#include "lang.h"
#include "canvas.h"
#include "gfx.h"
#include "ui.h"
#include "input.h"
#include "audio.h"
#include "dialog.h"
#include "gen/font_data.h"

// ---------------------------------------------------------------- shared drawing helpers
static void dyn_palette(const u16 *pal, int n)
{
    gfx_bg_pal(false, C_DYN, pal, n);
    gfx_bg_pal(true, C_DYN, pal, n);
}

// Even-odd scanline fill of a polygon (points in pixels)
static void fill_poly(Canvas *c, const int *xs, const int *ys, int n, u8 col)
{
    int y0 = 192, y1 = 0;
    for (int i = 0; i < n; i++) {
        y0 = MIN(y0, ys[i]);
        y1 = MAX(y1, ys[i]);
    }
    y0 = MAX(0, y0);
    y1 = MIN(191, y1);
    for (int y = y0; y <= y1; y++) {
        int cross[16], k = 0;
        for (int i = 0, j = n - 1; i < n && k < 16; j = i++) {
            if ((ys[i] <= y) != (ys[j] <= y))
                cross[k++] = xs[i] + (y - ys[i]) * (xs[j] - xs[i]) / (ys[j] - ys[i]);
        }
        for (int a = 1; a < k; a++)
            for (int b = a; b > 0 && cross[b - 1] > cross[b]; b--) {
                int t = cross[b];
                cross[b] = cross[b - 1];
                cross[b - 1] = t;
            }
        for (int a = 0; a + 1 < k; a += 2)
            canvas_hline(c, cross[a], y, cross[a + 1] - cross[a] + 1, col);
    }
}

static void disc(Canvas *c, int cx, int cy, int r, u8 col)
{
    for (int y = -r; y <= r; y++) {
        int w = 0;
        while ((w + 1) * (w + 1) + y * y <= r * r)
            w++;
        canvas_hline(c, cx - w, cy + y, w * 2 + 1, col);
    }
}

static void top_header(const char *title, int secs, int score, int goal)
{
    canvas_rect(&g_top, 0, 0, 256, 28, C_NAVY1);
    ui_text_in(&g_top, &font_main, 6, 2, 150, 24, title, C_GOLD, C_BLUE_D, 0);
    char buf[32];
    snprintf(buf, sizeof buf, T("%d s · %d/%d"), secs, score, goal);
    ui_text_in(&g_top, &font_main, 150, 2, 100, 24, buf, secs <= 5 ? C_RED_HI : C_WHITE, C_BLUE_D, 2);
}

// ================================================================ Frankfurt: feel, look, tilt (ECB studio)
// The ECB's own way to check a banknote: feel the raised print, look at it against the light (watermark
// and portrait window), tilt it (the emerald number turns from green to deep blue).
enum { B_PAPER, B_DENOM, B_EMERALD = 7, B_EMERALD_TILT, B_WATER, B_INK, B_RIDGE, B_FOIL, B_FOIL2, B_HOLO, B_SHADE };

static void bill_draw(int denom, int flaw, bool fake, bool feel, bool light, bool tilted)
{
    static const int values[6] = {5, 10, 20, 50, 100, 200};
    const int x = 16, y = 40, w = 224, h = 112;
    u8 paper = light ? C_DYN + B_SHADE : C_DYN + B_PAPER;
    canvas_rect(&g_top, 0, 28, 256, 164, C_NAVY2);
    canvas_rect(&g_top, x, y, w, h, paper);
    canvas_box(&g_top, x, y, w, h, C_DYN + B_INK);
    canvas_rect(&g_top, x + 6, y + 6, 120, h - 12, C_DYN + B_DENOM + denom);
    canvas_rect(&g_top, x + 10, y + 10, 112, h - 20, paper);
    for (int k = 0; k < 112 + h; k += 7)                      // fine printed lines in the note's colour
        for (int t = 0; t < h - 20; t++) {
            int px = x + 10 + k - t;
            if (px >= x + 10 && px < x + 122 && (t + k) % 3)
                canvas_pixel(&g_top, px, y + 10 + t, light ? C_DYN + B_WATER : C_DYN + B_SHADE);
        }
    canvas_rect(&g_top, x + 100, y + 14, 16, 10, C_BLUE);   // the European flag
    for (int k = 0; k < 12; k++)
        canvas_pixel(&g_top, x + 108 + (cosLerp(k * 2731) * 4 >> 12), y + 19 + (sinLerp(k * 2731) * 3 >> 12), C_YELLOW);
    char v[8];
    snprintf(v, sizeof v, "%d", values[denom]);
    canvas_text(&g_top, &font_main, x + 14, y + 10, v, C_DYN + B_DENOM + denom, C_DYN + B_INK);
    // watermark: Europa's portrait, only visible against the light
    if (light && !(fake && flaw == 1)) {
        disc(&g_top, x + 60, y + 52, 15, C_DYN + B_WATER);
        disc(&g_top, x + 60, y + 78, 22, C_DYN + B_WATER);
        canvas_rect(&g_top, x + 38, y + 82, 46, 16, paper);
    }
    // portrait window / foil stripe
    canvas_rect(&g_top, x + 140, y + 4, 24, h - 8, tilted ? C_DYN + B_FOIL2 : C_DYN + B_FOIL);
    if (!(fake && flaw == 2)) {
        disc(&g_top, x + 152, y + 44, 7, C_DYN + B_HOLO);
        disc(&g_top, x + 152, y + 58, 9, C_DYN + B_HOLO);
    }
    // emerald number: green, deep blue when tilted (a fake one stays green)
    u8 em = tilted && !(fake && flaw == 2) ? C_DYN + B_EMERALD_TILT : C_DYN + B_EMERALD;
    canvas_text(&g_top, &font_main, x + 172, y + h - 30, v, em, C_DYN + B_INK);
    canvas_text_n(&g_top, &font_small, x + 172, y + 8, "EURO", 4, C_DYN + B_INK, 0);
    // raised print: ridges on the short edges you can feel with a finger
    if (feel) {
        bool ridges = !(fake && flaw == 0);
        for (int k = 0; k < 5; k++) {
            u8 col = ridges ? C_DYN + B_RIDGE : C_DYN + B_SHADE;
            canvas_hline(&g_top, x + 2, y + 20 + k * 6, 3, col);
            canvas_hline(&g_top, x + w - 5, y + 20 + k * 6, 3, col);
            canvas_hline(&g_top, x + 2, y + h - 20 - k * 6, 3, col);
            canvas_hline(&g_top, x + w - 5, y + h - 20 - k * 6, 3, col);
        }
        ui_text_in(&g_top, &font_small, x, y + h + 6, w, 14,
                   ridges ? "Raised lines on the edges: you can feel them." : "The paper is smooth everywhere…",
                   C_PANEL, 0, 1);
    }
}

static void bill_buttons(bool feel, bool light, bool tilted)
{
    ui_backdrop(&g_bot);
    ui_button(&g_bot, 6, 8, 78, 44, "Feel", feel ? BTN_SELECTED : BTN_NORMAL, &font_main);
    ui_button(&g_bot, 89, 8, 78, 44, "Look", light ? BTN_SELECTED : BTN_NORMAL, &font_main);
    ui_button(&g_bot, 172, 8, 78, 44, "Tilt", tilted ? BTN_SELECTED : BTN_NORMAL, &font_main);
    ui_text_in(&g_bot, &font_small, 6, 56, 244, 14, "Check, then decide:", C_WHITE, 0, 1);
    ui_button(&g_bot, 6, 76, 118, 60, "Genuine", BTN_GREEN, &font_main);
    ui_button(&g_bot, 132, 76, 118, 60, "Counterfeit", BTN_RED, &font_main);
    ui_text_in(&g_bot, &font_small, 6, 146, 244, 40, "L/R: tilt · X: against the light · Y: feel", C_PANEL, 0, 1);
}

int mg_billets(void)
{
    static const u16 pal[16] = {
        RGB8(242, 238, 222), RGB8(150, 156, 164), RGB8(208, 72, 64), RGB8(64, 112, 200), RGB8(236, 140, 52),
        RGB8(72, 164, 96), RGB8(206, 162, 64), RGB8(40, 176, 96), RGB8(40, 70, 190), RGB8(200, 198, 206),
        RGB8(40, 40, 60), RGB8(96, 80, 64), RGB8(214, 220, 232), RGB8(236, 196, 236), RGB8(150, 150, 172),
        RGB8(252, 250, 240)};
    mg_intro("Feel, look, tilt",
             "Before touching the printing plate, prove you can spot a fake! Check each note the ECB's way: FEEL "
             "the raised print, LOOK at it against the light, TILT it. Judge 10 notes, one mistake allowed.");
    dyn_palette(pal, 16);
    int score = 0, mistakes = 0, frames = 75 * 60, goal = 10;
    while (frames > 0 && score < goal && mistakes < 2) {
        int denom = rng_range(6), flaw = rng_range(3);
        bool fake = rng_range(100) < 45, feel = false, light = false, tilted = false, redraw = true;
        int verdict = -1;
        while (verdict < 0 && frames > 0) {
            if (redraw) {
                bill_draw(denom, flaw, fake, feel, light, tilted);
                bill_buttons(feel, light, tilted);
                redraw = false;
            }
            if (frames % 30 == 0)
                top_header("Feel, look, tilt", frames / 60, score, goal);
            frame_wait();
            frames--;
            if (touch_released_in(6, 8, 78, 44) || (g_kdown & KEY_Y)) { feel = !feel; redraw = true; sfx_play(SFX_PAPER); }
            if (touch_released_in(89, 8, 78, 44) || (g_kdown & KEY_X)) { light = !light; redraw = true; sfx_play(SFX_CURSOR); }
            if (touch_released_in(172, 8, 78, 44) || (g_kdown & (KEY_L | KEY_R))) { tilted = !tilted; redraw = true; sfx_play(SFX_WHOOSH); }
            if (touch_released_in(6, 76, 118, 60) || (g_kdown & KEY_A))
                verdict = 0;
            if (touch_released_in(132, 76, 118, 60) || (g_kdown & KEY_B))
                verdict = 1;
        }
        if (verdict < 0)
            break;
        if ((verdict == 1) == fake) {
            score++;
            sfx_play(SFX_STAMP);
        } else {
            mistakes++;
            sfx_play(SFX_ERROR);
            static const char *const why[3] = {"It was %s: the raised print was missing.",
                                               "It was %s: no watermark against the light.",
                                               "It was %s: the number did not change colour."};
            char buf[96];
            if (fake)
                snprintf(buf, sizeof buf, T(why[flaw]), tr("a fake"));
            else
                snprintf(buf, sizeof buf, "%s", tr("It was a genuine note!"));
            ui_text_in(&g_bot, &font_small, 6, 146, 244, 40, buf, C_RED_HI, 0, 1);
            for (int i = 0; i < 70; i++)
                frame_wait();
        }
    }
    return mg_outro(score >= goal && mistakes < 2,
                    "Not one fake got through! In the watermark you saw Europa, from a Greek vase over 2,000 years old.",
                    "A counterfeit slipped past… Feel, look, tilt: the three checks take only a few seconds.");
}

// ================================================================ Frankfurt: the Bembel (apple wine)
// Sachsenhausen taverns pour apple wine (Ebbelwoi) from a grey stoneware jug, the Bembel, into a "Gerippte",
// a glass with a diamond pattern that sits well in the hand.
int mg_bembel(void)
{
    static const u16 pal[10] = {RGB8(150, 96, 56), RGB8(190, 130, 80), RGB8(172, 176, 188), RGB8(70, 96, 170),
                                RGB8(226, 236, 244), RGB8(230, 186, 70), RGB8(250, 220, 120), RGB8(120, 70, 40),
                                RGB8(255, 255, 255), RGB8(196, 210, 226)};
    enum { WOOD, WOOD_L, JUG, JUG_BLUE, GLASS, CIDER, CIDER_L, DARK, WHITE, GLASS_D };
    mg_intro("The Bembel",
             "In a Sachsenhausen tavern, pour apple wine from the Bembel into each glass up to the line! Hold the "
             "stylus (or A) to tilt the jug, let go to stop, then serve with the button. 8 glasses, 2 spills allowed.");
    dyn_palette(pal, 10);
    canvas_clear(&g_top, C_NAVY1);
    ui_text_in(&g_top, &font_main, 8, 60, 240, 22, "Apple-wine tavern, Sachsenhausen", C_GOLD, C_BLUE_D, 1);
    ui_text_wrapped(&g_top, &font_small, 16, 90, 224,
                    "Hold to tilt the Bembel, let go to stop. Serve when the apple wine reaches the line.", C_PANEL, 0);
    const int gx = 92, gy = 92, gw = 48, gh = 80, mark = 64;   // glass, level of the 0.3 l line
    int served = 0, misses = 0, frames = 70 * 60, goal = 8;
    while (frames > 0 && served < goal && misses < 3) {
        int level = 0, tilt = 0;     // level in 1/16 px, tilt 0..80 degrees
        bool done = false;
        while (!done && frames > 0) {
            bool hold = (g_touch_held && !(g_touch_x >= 176 && g_touch_y >= 140)) || (g_kheld & KEY_A);
            tilt = hold ? MIN(80, tilt + 2) : MAX(0, tilt - 4);
            int flow = MAX(0, tilt - 35);
            level += flow * flow / 40;
            canvas_rect(&g_bot, 0, 0, 256, 192, C_NAVY2);
            canvas_rect(&g_bot, 0, 172, 256, 20, C_DYN + WOOD);
            canvas_hline(&g_bot, 0, 172, 256, C_DYN + WOOD_L);
            // the Bembel: a bulbous grey stoneware jug with a handle, pivoting on its base towards the glass
            int a = -tilt * 32768 / 360, cs = cosLerp(a), sn = sinLerp(a), px = 192, py = 76;
            static const int jx[14] = {-14, 14, 21, 24, 21, 13, 10, -9, -13, -24, -19, -22, -24, -21},
                             jy[14] = {0, 0, -8, -22, -36, -46, -52, -52, -50, -56, -46, -34, -22, -8};
            static const int hx[9] = {20, 32, 36, 30, 21, 25, 30, 27, 21}, hy[9] = {-40, -38, -26, -12, -12, -16, -26, -34, -34};
            int xs[14], ys[14];
            for (int i = 0; i < 9; i++) {
                xs[i] = px + ((hx[i] * cs - hy[i] * sn) >> 12);
                ys[i] = py + ((hx[i] * sn + hy[i] * cs) >> 12);
            }
            fill_poly(&g_bot, xs, ys, 9, C_DYN + JUG);
            for (int i = 0; i < 14; i++) {
                xs[i] = px + ((jx[i] * cs - jy[i] * sn) >> 12);
                ys[i] = py + ((jx[i] * sn + jy[i] * cs) >> 12);
            }
            fill_poly(&g_bot, xs, ys, 14, C_DYN + JUG);
            for (int k = 0; k < 4; k++) {     // blue salt-glaze flowers
                int dx = -12 + k * 8, dy = -26 - (k & 1) * 8;
                disc(&g_bot, px + ((dx * cs - dy * sn) >> 12), py + ((dx * sn + dy * cs) >> 12), 2, C_DYN + JUG_BLUE);
            }
            if (flow > 0) {                   // the stream falls from the spout into the glass
                int sx = xs[9], sy = ys[9], tx = gx + gw / 2, ty = gy + gh - MIN(gh, level / 16);
                for (int t = 0; t <= 16; t++) {
                    int lx = sx + (tx - sx) * t / 16, ly = sy + (ty - sy) * t * t / 256;
                    canvas_rect(&g_bot, lx - 1, ly, 2 + flow / 16, 3, C_DYN + CIDER);
                }
            }
            // the Gerippte glass with its diamond pattern and the line
            canvas_rect(&g_bot, gx, gy, gw, gh, C_DYN + GLASS);
            int lv = MIN(gh, level / 16);
            canvas_rect(&g_bot, gx + 2, gy + gh - lv, gw - 4, lv, C_DYN + CIDER);
            for (int yy = gy + 6; yy < gy + gh - 4; yy += 8)
                for (int xx = gx + 4 + ((yy / 8) & 1) * 4; xx < gx + gw - 4; xx += 8)
                    canvas_pixel(&g_bot, xx, yy, C_DYN + GLASS_D);
            canvas_hline(&g_bot, gx - 4, gy + gh - mark, gw + 8, C_DYN + DARK);
            canvas_text_n(&g_bot, &font_small, gx + gw + 6, gy + gh - mark - 5, "0,3 l", 5, C_WHITE, 0);
            ui_button(&g_bot, 176, 140, 76, 30, "Serve", BTN_GREEN, &font_small);
            if (frames % 15 == 0)
                top_header("The Bembel", frames / 60, served, goal);
            frame_wait();
            frames--;
            if (level / 16 > gh) {
                sfx_play(SFX_ERROR);
                misses++;
                done = true;
            } else if (tilt == 0 && (touch_released_in(176, 140, 76, 30) || (g_kdown & (KEY_B | KEY_X)))) {
                int diff = level / 16 - mark;
                if (diff >= -3 && diff <= 4) {
                    served++;
                    sfx_play(SFX_COIN);
                } else {
                    misses++;
                    sfx_play(SFX_ERROR);
                }
                done = true;
            }
        }
    }
    return mg_outro(served >= goal && misses < 3,
                    "Eight perfect glasses! Here in Frankfurt they call apple wine \"Ebbelwoi\".",
                    "Too many spilt glasses… The tavern keeper lends you a cloth.");
}

// ================================================================ placeholders (implemented city by city)
int mg_evzones(void) { return mg_outro(true, "", ""); }
int mg_periptero(void) { return mg_outro(true, "", ""); }
int mg_conteneurs(void) { return mg_outro(true, "", ""); }
int mg_tapis(void) { return mg_outro(true, "", ""); }
int mg_cigognes(void) { return mg_outro(true, "", ""); }
int mg_douane(void) { return mg_outro(true, "", ""); }
int mg_echecs(void) { return mg_outro(true, "", ""); }
int mg_schuman(void) { return mg_outro(true, "", ""); }
int mg_casemates(void) { return mg_outro(true, "", ""); }
