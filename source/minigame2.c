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
             "Syntagma Square, the Tomb of the Unknown Soldier. Move in time with the Evzones: STEP, KICK, STOMP when "
             "each sign reaches the line. 24 moves, slowly and solemnly. 4 mistakes allowed.");
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
        char buf[32];
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
             "Rush hour at the kiosk! Each customer asks in Greek: tap what they want. I'll whisper the meaning for "
             "the first ones. 15 customers in 60 seconds!");
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
             "Load three ships before noon! Move the crane with the stylus or ←/→, drop with A or a tap. Heavy (H) "
             "never on top of lighter, refrigerated (white) only on the two powered columns (plugs), and keep the ship level!");
    dyn_palette(pal, 8);
    int ship = 0, strikes = 0, frames = 100 * 60;
    bool lost = false;
    while (ship < 3 && !lost && frames > 0) {
        int stack[BAYS][TIERS], height[BAYS] = {0}, count = 8 + ship * 2, placed = 0, trolley = 2;
        int limit = 5 - ship;   // allowed weight imbalance between port and starboard
        memset(stack, 0, sizeof stack);
        int load = 0, kind = 0;   // kind: 1 light, 2 medium, 3 heavy, 4 reefer (weight 2)
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
                        canvas_text_n(&g_bot, &font_small, bx + 11, y + 3, "H", 1, C_WHITE, 0);
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
            if (kind == 3) canvas_text_n(&g_bot, &font_small, tx + 11, 29, "H", 1, C_WHITE, 0);
            if (kind == 4) snow_icon(tx + 10, 30, C_BLUE);
            if (frames % 10 == 0) {
                canvas_clear(&g_top, C_NAVY1);
                char buf[48];
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
                load++;
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

// ================================================================ placeholders (implemented city by city)
int mg_tapis(void) { return mg_outro(true, "", ""); }
int mg_cigognes(void) { return mg_outro(true, "", ""); }
int mg_douane(void) { return mg_outro(true, "", ""); }
int mg_echecs(void) { return mg_outro(true, "", ""); }
int mg_schuman(void) { return mg_outro(true, "", ""); }
int mg_casemates(void) { return mg_outro(true, "", ""); }
