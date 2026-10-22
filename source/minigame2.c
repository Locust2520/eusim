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
             "Before touching the printing plate, prove you can spot a fake! Check each note the ECB's way: FEEL the raised print, LOOK at it against the light, TILT it. Judge 10 notes, one mistake allowed.");
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
            char buf[160];
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
             "In a Sachsenhausen tavern, pour apple wine from the Bembel into each glass up to the line! Hold the stylus (or A) to tilt the jug, let go to stop, then serve with the button. 8 glasses, 2 spills allowed.");
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
                    "Eight perfect glasses! Here in Frankfurt they call apple wine “Ebbelwoi”.",
                    "Too many spilt glasses… The tavern keeper lends you a cloth.");
}

// ================================================================ Athens: the changing of the guard
// Two Evzones of the Presidential Guard mirror each other in slow motion: steps, a high kick, the clogs striking
// the ground. Icons scroll towards the line; tap (or press) the matching move as each one arrives.
enum { MV_STEP, MV_KICK, MV_STOMP };

static void evzone_figure(int cx, int y, int pose, bool mirror)
{
    int s = mirror ? -1 : 1;
    disc(&g_top, cx, y + 8, 6, C_DYN + 2);                               // face
    canvas_rect(&g_top, cx - 5, y - 2, 11, 7, C_DYN + 0);                // red fez
    canvas_rect(&g_top, cx + s * 6, y, 2, 10, C_DYN + 4);               // tassel
    canvas_rect(&g_top, cx - 8, y + 15, 17, 18, C_DYN + 1);              // white shirt with wide sleeves
    canvas_rect(&g_top, cx - 6, y + 17, 13, 12, C_DYN + 3);              // dark vest
    int xs[4] = {cx - 14, cx + 14, cx + 9, cx - 9}, ys[4] = {y + 52, y + 52, y + 31, y + 31};
    fill_poly(&g_top, xs, ys, 4, C_DYN + 1);                             // fustanella
    for (int k = -12; k <= 12; k += 3)
        canvas_vline(&g_top, cx + k, y + 36 + abs(k) / 3, 15 - abs(k) / 3, C_DYN + 5);
    int lift = pose == MV_KICK ? 22 : pose == MV_STEP ? 8 : 0;
    canvas_rect(&g_top, cx - 6, y + 52, 4, 20, C_DYN + 1);                // standing leg
    canvas_rect(&g_top, cx - 7, y + 70, 7, 5, C_DYN + 0);                 // red clog
    canvas_rect(&g_top, cx - 9, y + 71, 3, 3, C_DYN + 4);                 // black pompom
    canvas_rect(&g_top, cx + 2 + (pose == MV_KICK ? s * 6 : 0), y + 52 - lift, 4, 20, C_DYN + 1);
    canvas_rect(&g_top, cx + 1 + (pose == MV_KICK ? s * 8 : 0), y + 70 - lift, 7, 5, C_DYN + 0);
    canvas_rect(&g_top, cx + 7 + (pose == MV_KICK ? s * 8 : 0), y + 71 - lift, 3, 3, C_DYN + 4);
    if (pose == MV_STOMP)
        for (int k = 0; k < 3; k++)
            canvas_hline(&g_top, cx - 10 + k * 7, y + 78, 4, C_YELLOW);
}

int mg_evzones(void)
{
    static const u16 pal[6] = {RGB8(200, 32, 32), RGB8(248, 248, 244), RGB8(236, 196, 160), RGB8(40, 48, 90),
                               RGB8(20, 20, 24), RGB8(210, 210, 220)};
    mg_intro("The changing of the guard",
             "Syntagma Square, the Tomb of the Unknown Soldier. Move in time with the Evzones: STEP, KICK, STOMP when each sign reaches the line. 24 moves, slowly and solemnly. 4 mistakes allowed.");
    dyn_palette(pal, 6);
    static const char *const names[3] = {"Step", "Kick", "Stomp"};
    int moves[24];
    for (int i = 0; i < 24; i++)   // the guard's phrase: step, step, kick… then the stomp
        moves[i] = (i % 4 == 3) ? MV_STOMP : (i % 4 == 2) ? MV_KICK : MV_STEP;
    for (int i = 0; i < 6; i++) {  // a few variations so it doesn't get mechanical
        int k = rng_range(24);
        if (moves[k] == MV_STEP)
            moves[k] = MV_KICK;
    }
    const int beat = 42, hit_x = 40;
    int frame = 0, next = 0, hits = 0, misses = 0, pose = MV_STEP;
    bool judged[24] = {0};
    while (next < 24 && misses <= 4) {
        canvas_clear(&g_top, C_NAVY1);
        canvas_rect(&g_top, 0, 150, 256, 42, C_DYN + 5);                // marble
        evzone_figure(84, 66, pose, false);
        evzone_figure(172, 66, pose, true);
        char buf[96];
        snprintf(buf, sizeof buf, T("Moves: %d / 24 · mistakes: %d"), hits, misses);
        ui_text_in(&g_top, &font_small, 0, 4, 256, 14, buf, C_WHITE, 0, 1);
        ui_backdrop(&g_bot);
        canvas_rect(&g_bot, 0, 30, 256, 40, C_NAVY2);
        canvas_rect(&g_bot, hit_x - 2, 26, 4, 48, C_GOLD);
        for (int i = next; i < 24; i++) {
            int x = hit_x + (i * beat + 120 - frame) * 2;
            if (x > 256)
                break;
            if (x < -30)
                continue;
            BtnStyle st = moves[i] == MV_STEP ? BTN_NORMAL : moves[i] == MV_KICK ? BTN_SELECTED : BTN_RED;
            ui_button(&g_bot, x - 22, 34, 44, 32, names[moves[i]], st, &font_small);
        }
        for (int b = 0; b < 3; b++)
            ui_button(&g_bot, 6 + b * 83, 110, 78, 60, names[b], b == 0 ? BTN_NORMAL : b == 1 ? BTN_SELECTED : BTN_RED, &font_main);
        ui_text_in(&g_bot, &font_small, 0, 176, 256, 14, "←: step · →: kick · A/↓: stomp", C_PANEL, 0, 1);
        frame_wait();
        frame++;
        int press = -1;
        for (int b = 0; b < 3; b++)
            if (touch_in(6 + b * 83, 110, 78, 60))
                press = b;
        if (g_kdown & KEY_LEFT) press = MV_STEP;
        if (g_kdown & KEY_RIGHT) press = MV_KICK;
        if (g_kdown & (KEY_A | KEY_DOWN)) press = MV_STOMP;
        int due = next * beat + 120;
        if (press >= 0) {
            if (abs(frame - due) <= 12 && press == moves[next]) {
                hits++;
                pose = press;
                judged[next] = true;
                sfx_play(press == MV_STOMP ? SFX_STAMP : SFX_BLIP);
                next++;
            } else {
                misses++;
                sfx_play(SFX_BUMP);
            }
        }
        if (next < 24 && !judged[next] && frame > due + 12) {
            misses++;
            sfx_play(SFX_ERROR);
            next++;
        }
    }
    return mg_outro(misses <= 4,
                    "Perfectly in step! The Evzones change guard every hour, day and night, in every weather.",
                    "Out of step… The Evzones train for months before their first guard duty.");
}

// ================================================================ Athens: the periptero
// A customer asks in Greek; tap what they want. The meaning is whispered for the first customers only.
extern const char *const mg_greek_orders[8][2];
extern const char *const mg_greek_thanks[3];

static void kiosk_item(int i, int x, int y)
{
    switch (i) {
    case 0:   // frappé in a tall glass with a straw
        canvas_rect(&g_bot, x + 10, y + 4, 10, 16, C_DYN + 0);
        canvas_rect(&g_bot, x + 10, y + 4, 10, 4, C_WHITE);
        canvas_vline(&g_bot, x + 18, y, 6, C_RED);
        break;
    case 1:   // bottle of water
        canvas_rect(&g_bot, x + 11, y + 2, 8, 18, C_DYN + 1);
        canvas_rect(&g_bot, x + 13, y, 4, 3, C_BLUE);
        break;
    case 2:   // newspaper
        canvas_rect(&g_bot, x + 4, y + 4, 22, 16, C_WHITE);
        for (int k = 0; k < 4; k++)
            canvas_hline(&g_bot, x + 6, y + 8 + k * 3, 18, C_MGREY);
        break;
    case 3:   // koulouri, the sesame bread ring
        disc(&g_bot, x + 15, y + 11, 9, C_DYN + 2);
        disc(&g_bot, x + 15, y + 11, 4, C_NAVY2);
        break;
    case 4:   // komboloi, worry beads
        for (int k = 0; k < 8; k++)
            disc(&g_bot, x + 15 + (cosLerp(k * 4096) * 7 >> 12), y + 10 + (sinLerp(k * 4096) * 7 >> 12), 2, C_DYN + 3);
        canvas_vline(&g_bot, x + 15, y + 17, 6, C_DYN + 3);
        break;
    case 5:   // mati, the blue eye
        disc(&g_bot, x + 15, y + 11, 8, C_BLUE);
        disc(&g_bot, x + 15, y + 11, 5, C_WHITE);
        disc(&g_bot, x + 15, y + 11, 2, C_TEXT);
        break;
    case 6:   // bus ticket
        canvas_rect(&g_bot, x + 3, y + 6, 24, 12, C_DYN + 4);
        canvas_hline(&g_bot, x + 6, y + 10, 12, C_WHITE);
        break;
    default:  // chewing gum
        canvas_rect(&g_bot, x + 6, y + 6, 18, 10, C_GREEN);
        canvas_hline(&g_bot, x + 6, y + 10, 18, C_WHITE);
        break;
    }
}

int mg_periptero(void)
{
    static const u16 pal[5] = {RGB8(196, 150, 96), RGB8(170, 214, 240), RGB8(200, 150, 80), RGB8(150, 60, 40),
                               RGB8(240, 200, 60)};
    static const char *const items_en[8] = {"Frappé", "Water", "Newspaper", "Koulouri", "Worry beads", "Mati",
                                            "Bus ticket", "Chewing gum"};
    static const char *const meaning[8] = {"(A frappé, please!)", "(A water, please!)", "(A newspaper, please!)",
                                           "(A koulouri, the sesame bread ring, please!)", "(Worry beads, please!)",
                                           "(A little evil-eye charm, please!)", "(A ticket, please!)",
                                           "(Chewing gum, please!)"};
    mg_intro("The periptero",
             "Rush hour at the kiosk! Each customer asks in Greek: tap what they want. I'll whisper the meaning for the first ones. 15 customers in 60 seconds!");
    dyn_palette(pal, 5);
    int served = 0, frames = 60 * 60, goal = 15, want = -1, mood = 0;
    while (frames > 0 && served < goal) {
        if (want < 0) {
            want = rng_range(8);
            mood = 0;
        }
        canvas_clear(&g_top, C_NAVY1);
        disc(&g_top, 52, 92, 26, C_DYN + 2);                            // customer
        disc(&g_top, 44, 86, 3, C_TEXT);
        disc(&g_top, 60, 86, 3, C_TEXT);
        canvas_hline(&g_top, 44, mood < 0 ? 104 : 102, 16, C_TEXT);
        canvas_rect(&g_top, 26, 120, 52, 40, C_BLUE_L);
        canvas_frame(&g_top, 96, 60, 152, 72, FRAME_DIALOG);           // speech bubble
        const char *gr = mg_greek_orders[want][0], *lat = mg_greek_orders[want][1];
        const Font *gf = font_width_n(&font_main, gr, strlen(gr)) <= 140 ? &font_main : &font_small;
        canvas_text_n(&g_top, gf, 104, gf == &font_main ? 66 : 70, gr, strlen(gr), C_TEXT, 0);
        canvas_text_n(&g_top, &font_small, 104, 88, lat, strlen(lat), C_BLUE, 0);
        if (served < 6)
            ui_text_wrapped(&g_top, &font_small, 104, 102, 140, meaning[want], C_DGREY, 0);
        top_header("The periptero", frames / 60, served, goal);
        ui_backdrop(&g_bot);
        for (int i = 0; i < 8; i++) {
            int x = 4 + (i % 4) * 63, y = 8 + (i / 4) * 88;
            ui_button(&g_bot, x, y, 59, 84, "", BTN_NORMAL, &font_small);
            kiosk_item(i, x + 14, y + 14);
            ui_text_in(&g_bot, &font_small, x + 2, y + 58, 55, 22, items_en[i], C_TEXT, 0, 1);
        }
        frame_wait();
        frames--;
        for (int i = 0; i < 8; i++)
            if (touch_released_in(4 + (i % 4) * 63, 8 + (i / 4) * 88, 59, 84)) {
                if (i == want) {
                    served++;
                    sfx_play(SFX_COIN);
                    const char *t = mg_greek_thanks[rng_range(3)];
                    canvas_frame(&g_top, 96, 140, 152, 30, FRAME_DIALOG);
                    canvas_text_n(&g_top, &font_main, 106, 146, t, strlen(t), C_GREEN, 0);
                    for (int k = 0; k < 20; k++)
                        frame_wait();
                    frames -= 20;
                    want = -1;
                } else {
                    sfx_play(SFX_ERROR);
                    mood = -1;
                    frames -= 120;
                }
            }
    }
    return mg_outro(served >= goal, "Fifteen happy customers! Ευχαριστώ (efcharistó) means thank you.",
                    "The queue reaches the next street… Σιγά σιγά (sigá sigá): slowly, slowly.");
}

// ================================================================ Piraeus: loading the container ship
// Heavy containers never go on top of lighter ones, refrigerated ones must sit on the two powered columns,
// and the ship must stay level: watch the heel gauge.
#define BAYS 6
#define TIERS 4

static void plug_icon(int x, int y, u8 col)
{
    canvas_rect(&g_bot, x + 2, y, 2, 3, col);
    canvas_rect(&g_bot, x + 6, y, 2, 3, col);
    canvas_rect(&g_bot, x, y + 3, 10, 5, col);
    canvas_rect(&g_bot, x + 4, y + 8, 2, 3, col);
}

// the "heavy" letter, centred on a 28-px container; each language picks its own letter, named in the rules
static void heavy_mark(int x, int y)
{
    const char *h = tr("H");
    canvas_text(&g_bot, &font_small, x + (28 - font_width(&font_small, h)) / 2, y, h, C_WHITE, 0);
}

static void snow_icon(int x, int y, u8 col)
{
    canvas_hline(&g_bot, x, y + 4, 9, col);
    canvas_vline(&g_bot, x + 4, y, 9, col);
    for (int k = 1; k < 4; k++) {
        canvas_pixel(&g_bot, x + 4 - k, y + 4 - k, col);
        canvas_pixel(&g_bot, x + 4 + k, y + 4 + k, col);
        canvas_pixel(&g_bot, x + 4 - k, y + 4 + k, col);
        canvas_pixel(&g_bot, x + 4 + k, y + 4 - k, col);
    }
}

int mg_conteneurs(void)
{
    static const u16 pal[8] = {RGB8(60, 140, 210), RGB8(30, 90, 160), RGB8(200, 60, 50), RGB8(230, 160, 40),
                               RGB8(80, 170, 90), RGB8(240, 244, 248), RGB8(60, 60, 70), RGB8(240, 200, 40)};
    enum { SEA, SEA_D, HEAVY, MEDIUM, LIGHT, REEFER, HULL, CRANE };
    mg_intro("The port of Piraeus",
             "Load three ships before noon! Move the crane with the stylus or ←/→, drop with A or a tap. Heavy (H) never on top of lighter, refrigerated (white) only on the two powered columns (plugs), and keep the ship level!");
    dyn_palette(pal, 8);
    int ship = 0, strikes = 0, frames = 100 * 60;
    bool lost = false;
    while (ship < 3 && !lost && frames > 0) {
        int stack[BAYS][TIERS], height[BAYS] = {0}, count = 8 + ship * 2, placed = 0, trolley = 2;
        int limit = 5 - ship;   // allowed weight imbalance between port and starboard
        memset(stack, 0, sizeof stack);
        int kind = 0;   // kind: 1 light, 2 medium, 3 heavy, 4 reefer (weight 2)
        while (placed < count && !lost && frames > 0) {
            if (!kind)
                kind = 1 + rng_range(4);
            int left = 0, right = 0;
            for (int b = 0; b < BAYS; b++)
                for (int t = 0; t < height[b]; t++) {
                    int w = stack[b][t] == 4 ? 2 : stack[b][t];
                    if (b < BAYS / 2) left += w * (BAYS / 2 - b);
                    else right += w * (b - BAYS / 2 + 1);
                }
            int heel = right - left;
            // draw
            canvas_clear(&g_bot, C_DYN + SEA);
            canvas_rect(&g_bot, 0, 0, 256, 40, C_NAVY2);
            int sx = 128, sy = 150;
            int hull_x[4] = {24, 232, 216, 40}, hull_y[4] = {120 + heel, 120 - heel, 160, 160};
            fill_poly(&g_bot, hull_x, hull_y, 4, C_DYN + HULL);
            for (int b = 0; b < BAYS; b++) {
                int bx = 40 + b * 30;
                if (b == 0 || b == BAYS - 1)
                    plug_icon(bx + 9, 126, C_DYN + CRANE);
                for (int t = 0; t < height[b]; t++) {
                    int k = stack[b][t];
                    int y = 104 - t * 18 + (heel * (128 - bx)) / 104;
                    u8 col = k == 3 ? C_DYN + HEAVY : k == 2 ? C_DYN + MEDIUM : k == 1 ? C_DYN + LIGHT : C_DYN + REEFER;
                    canvas_rect(&g_bot, bx, y, 28, 17, col);
                    canvas_box(&g_bot, bx, y, 28, 17, C_TEXT);
                    if (k == 3)
                        heavy_mark(bx, y + 3);
                    if (k == 4)
                        snow_icon(bx + 10, y + 4, C_BLUE);
                }
            }
            (void)sx; (void)sy;
            int tx = 40 + trolley * 30;
            canvas_rect(&g_bot, 0, 6, 256, 6, C_DYN + CRANE);                          // crane boom
            canvas_rect(&g_bot, tx + 6, 4, 16, 10, C_DYN + HULL);                      // trolley
            canvas_vline(&g_bot, tx + 14, 14, 12, C_TEXT);
            u8 col = kind == 3 ? C_DYN + HEAVY : kind == 2 ? C_DYN + MEDIUM : kind == 1 ? C_DYN + LIGHT : C_DYN + REEFER;
            canvas_rect(&g_bot, tx, 26, 28, 17, col);
            canvas_box(&g_bot, tx, 26, 28, 17, C_TEXT);
            if (kind == 3) heavy_mark(tx, 29);
            if (kind == 4) snow_icon(tx + 10, 30, C_BLUE);
            if (frames % 10 == 0) {
                canvas_clear(&g_top, C_NAVY1);
                char buf[96];
                snprintf(buf, sizeof buf, T("Ship %d/3 · containers %d/%d"), ship + 1, placed, count);
                ui_text_in(&g_top, &font_main, 0, 36, 256, 22, buf, C_WHITE, C_BLUE_D, 1);
                snprintf(buf, sizeof buf, T("Time: %d s · mistakes: %d/3"), frames / 60, strikes);
                ui_text_in(&g_top, &font_small, 0, 62, 256, 14, buf, C_PANEL, 0, 1);
                ui_text_in(&g_top, &font_small, 0, 96, 256, 14, "Heel", C_WHITE, 0, 1);   // gauge
                canvas_rect(&g_top, 48, 112, 160, 14, C_NAVY2);
                canvas_rect(&g_top, 128 - limit * 12, 112, limit * 24, 14, C_GREEN);
                canvas_rect(&g_top, 127 + CLAMP(heel, -10, 10) * 12, 108, 3, 22, abs(heel) > limit ? C_RED : C_WHITE);
            }
            frame_wait();
            frames--;
            int old = trolley;
            if (g_krep & KEY_LEFT) trolley = MAX(0, trolley - 1);
            if (g_krep & KEY_RIGHT) trolley = MIN(BAYS - 1, trolley + 1);
            if (g_touch_held && g_touch_y < 100)
                trolley = CLAMP((g_touch_x - 40) / 30, 0, BAYS - 1);
            if (trolley != old)
                sfx_play(SFX_CURSOR);
            bool drop = (g_kdown & KEY_A) || (g_touch_up && g_touch_y >= 100);
            if (drop) {
                if (height[trolley] >= TIERS) {
                    sfx_play(SFX_BUMP);
                    continue;
                }
                bool wrong = (kind == 4 && trolley != 0 && trolley != BAYS - 1);
                if (height[trolley] > 0) {
                    int below = stack[trolley][height[trolley] - 1];
                    int wb = below == 4 ? 2 : below, wk = kind == 4 ? 2 : kind;
                    if (wk > wb)
                        wrong = true;   // heavier on top of lighter
                }
                stack[trolley][height[trolley]++] = kind;
                placed++;
                kind = 0;
                sfx_play(wrong ? SFX_ERROR : SFX_STAMP);
                if (wrong && ++strikes >= 3)
                    lost = true;
                int l2 = 0, r2 = 0;
                for (int b = 0; b < BAYS; b++)
                    for (int t = 0; t < height[b]; t++) {
                        int w = stack[b][t] == 4 ? 2 : stack[b][t];
                        if (b < BAYS / 2) l2 += w * (BAYS / 2 - b);
                        else r2 += w * (b - BAYS / 2 + 1);
                    }
                if (abs(r2 - l2) > limit * 2) {
                    lost = true;    // capsizing risk: the harbour master stops the loading
                    sfx_play(SFX_ALARM);
                }
            }
        }
        if (!lost && placed >= count) {
            ship++;
            sfx_play(SFX_LEVELUP);
            for (int i = 0; i < 40; i++)
                frame_wait();
        }
    }
    return mg_outro(ship >= 3,
                    "Three ships loaded and level! Piraeus is one of the largest container ports in the Mediterranean.",
                    "The harbour master stops the loading: the ship is not safe. Restack and try again!");
}

// ================================================================ Brussels: the flower carpet
// Every two years in August, a carpet of begonias covers the Grand-Place (the first in 1971).
// Copy the design shown on the top screen, flower by flower.
#define CW 12
#define CH 8
static const char *const carpets[3][CH] = {
    {"yyyyyyyyyyyy", "yrrryyyyrrry", "yrwrryyrrwry", "yrrrrrrrrrry", "yyrrrrrrrryy", "yyyrrrrrryyy", "yyyyyrryyyyy", "yyyyyyyyyyyy"},
    {"oooooooooooo", "oyyywwwwyyyo", "oywwwrrwwwyo", "owwrrrrrrwwo", "owwrrrrrrwwo", "oywwwrrwwwyo", "oyyywwwwyyyo", "oooooooooooo"},
    {"rrrrrrrrrrrr", "ryyyyyyyyyyr", "ryrrwwwwrryr", "rywwoooowwyr", "rywwoooowwyr", "ryrrwwwwrryr", "ryyyyyyyyyyr", "rrrrrrrrrrrr"},
};

static int flower_col(char c)
{
    switch (c) {
    case 'r': return C_DYN + 0;
    case 'y': return C_DYN + 1;
    case 'w': return C_DYN + 2;
    default: return C_DYN + 3;
    }
}

int mg_tapis(void)
{
    static const u16 pal[5] = {RGB8(220, 40, 60), RGB8(250, 210, 50), RGB8(250, 250, 244), RGB8(240, 130, 40),
                               RGB8(60, 120, 70)};
    static const char cols[4] = {'r', 'y', 'w', 'o'};
    static const char *const names[4] = {"Red", "Yellow", "White", "Orange"};
    mg_intro("The flower carpet",
             "Copy the carpet of begonias shown on the top screen: pick a colour, then tap or drag over the squares. Press Done when it matches. Three carpets in 90 seconds!");
    dyn_palette(pal, 5);
    int done = 0, frames = 90 * 60, sel = 0;
    while (done < 3 && frames > 0) {
        char grid[CH][CW];
        memset(grid, 'y', sizeof grid);
        bool redraw = true;
        while (frames > 0) {
            if (redraw) {
                canvas_clear(&g_top, C_NAVY1);
                for (int y = 0; y < CH; y++)
                    for (int x = 0; x < CW; x++)
                        canvas_rect(&g_top, 32 + x * 16, 36 + y * 16, 15, 15, flower_col(carpets[done][y][x]));
                ui_text_in(&g_top, &font_small, 0, 176, 256, 14, "The design", C_PANEL, 0, 1);
                ui_backdrop(&g_bot);
                canvas_rect(&g_bot, 8, 4, CW * 20, CH * 16, C_DYN + 4);
                for (int y = 0; y < CH; y++)
                    for (int x = 0; x < CW; x++) {
                        disc(&g_bot, 18 + x * 20, 12 + y * 16, 6, flower_col(grid[y][x]));
                        canvas_pixel(&g_bot, 18 + x * 20, 12 + y * 16, C_DYN + 4);
                    }
                for (int i = 0; i < 4; i++)
                    ui_button(&g_bot, 4 + i * 50, 140, 48, 46, names[i], i == sel ? BTN_SELECTED : BTN_NORMAL, &font_small);
                ui_button(&g_bot, 206, 140, 46, 46, "Done", BTN_GREEN, &font_small);
                redraw = false;
            }
            if (frames % 15 == 0)
                top_header("The flower carpet", frames / 60, done, 3);
            frame_wait();
            frames--;
            if (g_touch_held && g_touch_y < 4 + CH * 16 && g_touch_x >= 8 && g_touch_x < 8 + CW * 20) {
                int x = (g_touch_x - 8) / 20, y = (g_touch_y - 4) / 16;
                if (grid[y][x] != cols[sel]) {
                    grid[y][x] = cols[sel];
                    disc(&g_bot, 18 + x * 20, 12 + y * 16, 6, flower_col(cols[sel]));
                    sfx_play(SFX_BLIP);
                }
            }
            for (int i = 0; i < 4; i++)
                if (touch_released_in(4 + i * 50, 140, 48, 46) && sel != i) {
                    sel = i;
                    redraw = true;
                    sfx_play(SFX_CURSOR);
                }
            if (g_kdown & KEY_L) { sel = (sel + 3) % 4; redraw = true; }
            if (g_kdown & KEY_R) { sel = (sel + 1) % 4; redraw = true; }
            if (touch_released_in(206, 140, 46, 46) || (g_kdown & KEY_START)) {
                int ok = 0;
                for (int y = 0; y < CH; y++)
                    for (int x = 0; x < CW; x++)
                        ok += grid[y][x] == carpets[done][y][x];
                if (ok * 100 >= CW * CH * 92) {
                    sfx_play(SFX_LEVELUP);
                    done++;
                    break;
                }
                sfx_play(SFX_ERROR);
                frames -= 180;
            }
        }
    }
    return mg_outro(done >= 3, "Three carpets of begonias! Belgium grows most of the world's tuberous begonias, around Ghent.",
                    "The tourists are arriving and the carpet is not finished… Next time!");
}

// ================================================================ Strasbourg: the storks
// Guide each stork to an empty nest on the roofs of the Petite France, away from the power lines.
int mg_cigognes(void)
{
    static const u16 pal[6] = {RGB8(140, 200, 240), RGB8(200, 80, 60), RGB8(240, 220, 190), RGB8(110, 76, 50),
                               RGB8(250, 250, 250), RGB8(40, 40, 50)};
    enum { SKY, ROOF, WALL, NEST, STORK, WIRE };
    mg_intro("The storks of Alsace",
             "The storks are back from Africa! Guide each one to an empty nest: slide the stylus up and down (or ↑/↓) and fly low over a free nest to land. Avoid the power lines. 10 storks, 3 losses allowed.");
    dyn_palette(pal, 6);
    static const int nest_x[5] = {60, 104, 148, 192, 236}, nest_y[5] = {130, 116, 138, 112, 126};
    bool full[5] = {0};
    int landed = 0, lost = 0, goal = 10;
    while (landed < goal && lost < 3) {
        int wy[3], wx0[3], wx1[3];
        for (int i = 0; i < 3; i++) {
            wy[i] = 50 + rng_range(70);
            wx0[i] = 40 + rng_range(120);
            wx1[i] = wx0[i] + 40 + rng_range(50);
        }
        if (full[0] && full[1] && full[2] && full[3] && full[4])
            memset(full, 0, sizeof full);   // the young ones have left: the nests are free again
        int sx = 0, sy = 40 + rng_range(40);   // in 1/16 px for x
        bool done = false;
        while (!done) {
            int target = g_touch_held ? g_touch_y : sy + ((g_kheld & KEY_DOWN) ? 3 : 0) - ((g_kheld & KEY_UP) ? 3 : 0);
            sy += CLAMP(target - sy, -2, 2);
            sy = CLAMP(sy, 12, 150);
            sx += 22;
            int x = sx / 16;
            canvas_clear(&g_bot, C_DYN + SKY);
            for (int k = 0; k < 5; k++) {   // roofs and nests
                int xs[3] = {nest_x[k] - 22, nest_x[k], nest_x[k] + 22}, ys[3] = {192, nest_y[k] + 6, 192};
                fill_poly(&g_bot, xs, ys, 3, C_DYN + ROOF);
                canvas_rect(&g_bot, nest_x[k] - 9, nest_y[k], 18, 6, C_DYN + NEST);
                if (full[k])
                    disc(&g_bot, nest_x[k], nest_y[k] - 4, 5, C_DYN + STORK);
            }
            for (int i = 0; i < 3; i++)
                canvas_hline(&g_bot, wx0[i], wy[i], wx1[i] - wx0[i], C_DYN + WIRE);
            disc(&g_bot, x, sy, 5, C_DYN + STORK);   // the stork: white body, black wings, red bill
            canvas_rect(&g_bot, x - 9, sy - 2, 7, 3, C_DYN + WIRE);
            canvas_rect(&g_bot, x + 4, sy - 2, 6, 2, C_DYN + ROOF);
            if (g_frame % 10 == 0) {
                canvas_clear(&g_top, C_NAVY1);
                char buf[96];
                snprintf(buf, sizeof buf, T("Storks home: %d / %d · lost: %d / 3"), landed, goal, lost);
                ui_text_in(&g_top, &font_main, 0, 80, 256, 22, buf, C_WHITE, C_BLUE_D, 1);
            }
            frame_wait();
            for (int i = 0; i < 3; i++)
                if (x >= wx0[i] && x <= wx1[i] && abs(sy - wy[i]) < 4) {
                    sfx_play(SFX_ERROR);
                    lost++;
                    done = true;
                }
            for (int k = 0; k < 5 && !done; k++)
                if (!full[k] && abs(x - nest_x[k]) < 7 && abs(sy - (nest_y[k] - 4)) < 7) {
                    full[k] = true;
                    landed++;
                    sfx_play(SFX_LEVELUP);
                    done = true;
                }
            if (!done && x > 262) {
                lost++;
                sfx_play(SFX_BUMP);
                done = true;
            }
        }
    }
    return mg_outro(landed >= goal, "Ten storks in their nests! In Alsace, a stork on your roof is said to bring luck.",
                    "Too many storks flew on to the next village… They'll be back next spring.");
}

// ================================================================ London: post-Brexit customs
// Since 2021, travellers from the UK may not bring meat or dairy into the EU, nor most fresh fruit without a
// plant-health certificate (bananas, pineapples, coconuts and dates are the exceptions).
int mg_douane(void)
{
    static const struct { const char *name; bool banned; } food[10] = {
        {"Ham sandwich", true}, {"Cheese", true}, {"Milk", true}, {"Salami", true}, {"Apple", true},
        {"Banana", false}, {"Chocolate bar", false}, {"Crisps", false}, {"Biscuits", false}, {"Water", false}};
    mg_intro("EU customs",
             "The ferry has docked! Check each lunchbox: CONFISCATE meat, dairy and most fruit, LET THROUGH the rest. Watch out: a banana is allowed, an apple is not. 20 boxes in 50 seconds, 2 mistakes allowed.");
    int checked = 0, mistakes = 0, frames = 50 * 60, goal = 20;
    while (checked < goal && mistakes <= 2 && frames > 0) {
        int item = rng_range(10);
        int slide = 0;
        int verdict = -1;
        while (verdict < 0 && frames > 0) {
            slide = MIN(slide + 8, 64);
            canvas_clear(&g_top, C_NAVY1);
            ui_text_in(&g_top, &font_small, 8, 40, 240, 14, "Meat, dairy, most fruit: confiscate.", C_RED_HI, 0, 1);
            ui_text_in(&g_top, &font_small, 8, 56, 240, 14, "Bananas, sweets, crisps, water: let through.", C_GREEN_HI, 0, 1);
            top_header("EU customs", frames / 60, checked, goal);
            ui_backdrop(&g_bot);
            canvas_rect(&g_bot, 0, 60, 256, 50, C_DGREY);                     // the conveyor belt
            for (int x = (g_frame * 2) % 16; x < 256; x += 16)
                canvas_vline(&g_bot, x, 60, 50, C_MGREY);
            int bx = 64 + 64 - slide;
            canvas_rect(&g_bot, bx, 54, 128, 56, C_BLUE_L);                  // the open lunchbox
            canvas_box(&g_bot, bx, 54, 128, 56, C_TEXT);
            ui_text_in(&g_bot, &font_main, bx + 4, 70, 120, 24, food[item].name, C_TEXT, C_WHITE, 1);
            ui_button(&g_bot, 8, 128, 116, 56, "Let through", BTN_GREEN, &font_main);
            ui_button(&g_bot, 132, 128, 116, 56, "Confiscate", BTN_RED, &font_main);
            frame_wait();
            frames--;
            if (touch_released_in(8, 128, 116, 56) || (g_kdown & KEY_A))
                verdict = 0;
            if (touch_released_in(132, 128, 116, 56) || (g_kdown & KEY_B))
                verdict = 1;
        }
        if (verdict < 0)
            break;
        checked++;
        if ((verdict == 1) == food[item].banned)
            sfx_play(verdict ? SFX_STAMP : SFX_SELECT);
        else {
            mistakes++;
            sfx_play(SFX_ERROR);
        }
    }
    return mg_outro(checked >= goal && mistakes <= 2,
                    "All the lunchboxes checked! Within the EU's single market, food travels freely; at its borders, it is checked.",
                    "A salami slipped through… or a banana was wrongly seized. Rules first, sandwich later!");
}

// ================================================================ Budapest: chess in the baths
// Three positions, white to play and checkmate in one move.
static const struct {
    const char *rows[8];   // rank 8 first; uppercase = white, lowercase = black
    int moves[2][4];       // accepted mating moves: from file, from rank, to file, to rank (0-based; -1 = none)
} puzzles[3] = {
    {{"......k.", ".....ppp", "........", "........", "........", "........", "........", "R.....K."},
     {{0, 0, 0, 7}, {-1, -1, -1, -1}}},                                      // back-rank mate: Ra8#
    {{".......k", "........", "......K.", "........", "........", "........", "........", "Q......."},
     {{0, 0, 0, 7}, {0, 0, 6, 6}}},                                          // Qa8# or Qg7#
    {{"......rk", "......pp", "........", "......N.", "........", "........", "........", "K......."},
     {{6, 4, 5, 6}, {-1, -1, -1, -1}}},                                      // smothered mate: Nf7#
};

static void board_draw(int p, int sel_f, int sel_r)
{
    for (int r = 0; r < 8; r++)
        for (int f = 0; f < 8; f++) {
            int x = 48 + f * 20, y = 12 + (7 - r) * 20;
            u8 col = (f + r) % 2 ? C_LGREY : C_MGREY;
            if (f == sel_f && r == sel_r)
                col = C_YELLOW;
            canvas_rect(&g_bot, x, y, 20, 20, col);
            char pc = puzzles[p].rows[7 - r][f];
            if (pc == '.')
                continue;
            bool white = pc >= 'A' && pc <= 'Z';
            disc(&g_bot, x + 10, y + 10, 8, white ? C_WHITE : C_TEXT);
            char letter[2] = {(char)(white ? pc : pc - 32), 0};
            canvas_text_n(&g_bot, &font_small, x + 7, y + 5, letter, 1, white ? C_TEXT : C_WHITE, 0);
        }
    for (int f = 0; f < 8; f++) {
        char c[2] = {(char)('a' + f), 0};
        canvas_text_n(&g_bot, &font_small, 55 + f * 20, 174, c, 1, C_PANEL, 0);
    }
}

int mg_echecs(void)
{
    mg_intro("Chess in the baths",
             "Széchenyi baths: the players lean over a board floating in the steam. White to play: find the move that checkmates at once. Tap a white piece, then its square. Three positions in 90 seconds!");
    int solved = 0, frames = 90 * 60;
    while (solved < 3 && frames > 0) {
        int sel_f = -1, sel_r = -1;
        bool redraw = true;
        while (frames > 0) {
            if (redraw) {
                ui_backdrop(&g_bot);
                board_draw(solved, sel_f, sel_r);
                canvas_clear(&g_top, C_NAVY1);
                ui_text_in(&g_top, &font_main, 0, 60, 256, 22, "White to play and mate in one", C_GOLD, C_BLUE_D, 1);
                ui_text_in(&g_top, &font_small, 0, 90, 256, 14, "K king · Q queen · R rook · B bishop · N knight · P pawn",
                           C_PANEL, 0, 1);
                redraw = false;
            }
            if (frames % 15 == 0)
                top_header("Chess in the baths", frames / 60, solved, 3);
            frame_wait();
            frames--;
            if (!g_touch_up || g_touch_x < 48 || g_touch_x >= 208 || g_touch_y < 12 || g_touch_y >= 172)
                continue;
            int f = (g_touch_x - 48) / 20, r = 7 - (g_touch_y - 12) / 20;
            char pc = puzzles[solved].rows[7 - r][f];
            if (pc >= 'A' && pc <= 'Z') {
                sel_f = f;
                sel_r = r;
                sfx_play(SFX_CURSOR);
                redraw = true;
            } else if (sel_f >= 0) {
                bool mate = false;
                for (int k = 0; k < 2; k++) {
                    const int *m = puzzles[solved].moves[k];
                    mate |= m[0] == sel_f && m[1] == sel_r && m[2] == f && m[3] == r;
                }
                if (mate) {
                    sfx_play(SFX_LEVELUP);
                    solved++;
                    break;
                }
                sfx_play(SFX_ERROR);
                frames -= 600;
                sel_f = sel_r = -1;
                redraw = true;
            }
        }
    }
    return mg_outro(solved >= 3, "Three checkmates! In the baths, they say the loser has to get out of the water first.",
                    "The water went cold before the mate… Look for the move that leaves the king no square at all.");
}

// ================================================================ Paris: the Schuman Declaration
// Put the sentences of the declaration of 9 May 1950 (official English text, abridged) back in order.
int mg_schuman(void)
{
    static const char *const parts[6] = {
        "World peace cannot be safeguarded",
        "without creative efforts proportionate to the dangers which threaten it.",
        "Europe will not be made all at once, or according to a single plan.",
        "Built through concrete achievements which first create a de facto solidarity.",
        "Franco-German coal and steel will be placed under a common High Authority…",
        "…so that war between France and Germany becomes materially impossible."};
    mg_intro("The Schuman Declaration",
             "9 May 1950, Salon de l'Horloge. The pages of Robert Schuman's declaration are mixed up! Tap the sentences in the right order before the press conference. 60 seconds.");
    int order[6] = {0, 1, 2, 3, 4, 5};
    shuffle_ints:
    for (int i = 5; i > 0; i--) {
        int j = rng_range(i + 1), t = order[i];
        order[i] = order[j];
        order[j] = t;
    }
    if (order[0] == 0 && order[1] == 1)
        goto shuffle_ints;
    int next = 0, frames = 60 * 60;
    bool redraw = true;
    while (next < 6 && frames > 0) {
        if (redraw) {
            canvas_clear(&g_top, C_PANEL);
            int y = 30;
            for (int i = 0; i < next; i++)
                y = ui_text_wrapped(&g_top, &font_small, 10, y, 236, parts[i], C_TEXT, 0) + 2;
            ui_backdrop(&g_bot);
            for (int k = 0; k < 6; k++) {
                int i = order[k], by = 1 + k * 32;
                if (i < next)
                    continue;
                ui_panel(&g_bot, 2, by, 252, 31, false);
                ui_text_wrapped(&g_bot, &font_small, 6, by + 3, 244, parts[i], C_TEXT, 0);
            }
            redraw = false;
        }
        if (frames % 15 == 0)
            top_header("The Schuman Declaration", frames / 60, next, 6);
        frame_wait();
        frames--;
        for (int k = 0; k < 6; k++) {
            int i = order[k], by = 1 + k * 32;
            if (i < next || !touch_released_in(2, by, 252, 31))
                continue;
            if (i == next) {
                next++;
                sfx_play(SFX_PAPER);
            } else {
                sfx_play(SFX_ERROR);
                frames -= 300;
            }
            redraw = true;
        }
    }
    return mg_outro(next >= 6,
                    "The declaration is ready! The European Coal and Steel Community followed in 1951. Every 9 May is Europe Day.",
                    "The journalists are waiting and the pages are still in a mess… Peace first, then concrete achievements!");
}

// ================================================================ Luxembourg: the Bock casemates
// Find the lost visitor in the dark galleries, then the way out, before the torch burns down.
#define MZW 15
#define MZH 11
static const s8 step_dx[4] = {0, 0, -1, 1}, step_dy[4] = {1, -1, 0, 0};

int mg_casemates(void)
{
    static const u16 pal[4] = {RGB8(20, 18, 16), RGB8(120, 100, 76), RGB8(170, 146, 110), RGB8(250, 220, 120)};
    enum { DARK, ROCK, FLOOR, LIGHT };
    mg_intro("The Bock casemates",
             "The galleries are dark and the torch is burning down. Find the lost visitor, then the exit! Move with the +Control Pad, or tap next to your character. 75 seconds.");
    dyn_palette(pal, 4);
    static u8 maze[MZH][MZW];
    static u8 seen[MZH][MZW];
    memset(maze, 1, sizeof maze);
    memset(seen, 0, sizeof seen);
    // depth-first maze on the odd cells
    int stack[(MZW / 2) * (MZH / 2) + 2][2], sp = 0;
    stack[sp][0] = 1; stack[sp][1] = 1; sp++;
    maze[1][1] = 0;
    while (sp) {
        int cx = stack[sp - 1][0], cy = stack[sp - 1][1];
        int dirs[4] = {0, 1, 2, 3}, opts = 0, pick[4];
        for (int k = 0; k < 4; k++) {
            int nx = cx + step_dx[dirs[k]] * 2, ny = cy + step_dy[dirs[k]] * 2;
            if (nx > 0 && ny > 0 && nx < MZW - 1 && ny < MZH - 1 && maze[ny][nx])
                pick[opts++] = k;
        }
        if (!opts) {
            sp--;
            continue;
        }
        int k = pick[rng_range(opts)];
        int nx = cx + step_dx[k] * 2, ny = cy + step_dy[k] * 2;
        maze[cy + step_dy[k]][cx + step_dx[k]] = 0;
        maze[ny][nx] = 0;
        stack[sp][0] = nx; stack[sp][1] = ny; sp++;
    }
    int px = 1, py = 1, vx = MZW - 2, vy = 1, ex = MZW - 2, ey = MZH - 2;
    bool found = false, out = false;
    int frames = 75 * 60;
    while (!out && frames > 0) {
        int radius = 1 + frames * 3 / (75 * 60);   // the torch burns down: 3 cells, then 2, then 1
        for (int y = 0; y < MZH; y++)
            for (int x = 0; x < MZW; x++)
                if (abs(x - px) + abs(y - py) <= radius + 1)
                    seen[y][x] = 1;
        canvas_clear(&g_bot, C_DYN + DARK);
        for (int y = 0; y < MZH; y++)
            for (int x = 0; x < MZW; x++) {
                int d = abs(x - px) + abs(y - py);
                if (d > radius + 1)
                    continue;
                u8 col = maze[y][x] ? C_DYN + ROCK : (d <= radius ? C_DYN + LIGHT : C_DYN + FLOOR);
                canvas_rect(&g_bot, 8 + x * 16, 8 + y * 16, 16, 16, col);
            }
        if (abs(ex - px) + abs(ey - py) <= radius + 1)
            canvas_rect(&g_bot, 8 + ex * 16 + 3, 8 + ey * 16 + 2, 10, 14, C_GREEN);
        if (!found && abs(vx - px) + abs(vy - py) <= radius + 1)
            disc(&g_bot, 8 + vx * 16 + 8, 8 + vy * 16 + 8, 5, C_BLUE_L);
        disc(&g_bot, 8 + px * 16 + 8, 8 + py * 16 + 8, 5, C_RED);
        if (frames % 10 == 0) {   // the explored galleries
            canvas_clear(&g_top, C_NAVY1);
            for (int y = 0; y < MZH; y++)
                for (int x = 0; x < MZW; x++)
                    if (seen[y][x])
                        canvas_rect(&g_top, 68 + x * 8, 50 + y * 8, 8, 8, maze[y][x] ? C_DGREY : C_LGREY);
            canvas_rect(&g_top, 68 + px * 8 + 2, 50 + py * 8 + 2, 4, 4, C_RED);
            ui_text_in(&g_top, &font_small, 0, 150, 256, 14, found ? "The visitor follows you: now the exit!"
                                                                    : "Somewhere in the dark, someone is calling…",
                       C_PANEL, 0, 1);
            top_header("The Bock casemates", frames / 60, found ? 1 : 0, 1);
        }
        frame_wait();
        frames--;
        int dx = 0, dy = 0;
        if (g_krep & KEY_LEFT) dx = -1;
        else if (g_krep & KEY_RIGHT) dx = 1;
        else if (g_krep & KEY_UP) dy = -1;
        else if (g_krep & KEY_DOWN) dy = 1;
        if (g_touch_down) {
            int tx = (g_touch_x - 8) / 16 - px, ty = (g_touch_y - 8) / 16 - py;
            if (abs(tx) > abs(ty)) dx = tx > 0 ? 1 : -1;
            else if (ty) dy = ty > 0 ? 1 : -1;
        }
        if ((dx || dy) && !maze[py + dy][px + dx]) {
            px += dx;
            py += dy;
            sfx_play(SFX_BLIP);
        }
        if (!found && px == vx && py == vy) {
            found = true;
            sfx_play(SFX_SELECT);
        }
        if (found && px == ex && py == ey)
            out = true;
    }
    return mg_outro(out, "Out in the daylight, with the visitor! Up to 35,000 people sheltered in these galleries during the bombings.",
                    "The torch went out… The guide follows your voice and leads you both out.");
}
