// Cinematic slides: full-screen pictures on the top screen. BG2 becomes a 512x256 8bpp bitmap holding a
// 384x256 slide, moved with its affine matrix for a slow "Ken Burns" pan/zoom while the dialogue runs on the
// canvas (BG3) above it. Transitions use the master brightness and window 0 (iris and wipe).
#include "cine.h"
#include "gfx.h"
#include "canvas.h"
#include "fs.h"
#include "input.h"
#include "audio.h"
#include "dialog.h"
#include "portrait.h"
#include "save.h"
#include "ui.h"
#include "world.h"
#include "scenes.h"
#include "gen/font_data.h"

#define SW 384
#define SH 256
#define BAR 14                      // letterbox bar height

static bool active, skipping, shown;
static void letterbox(void);
static int motion, t;
static const int dur = 720;         // a full pan/zoom lasts 12 s, then the picture holds still
static s32 s0, s1, cx0, cx1, cy0, cy1; // scale in 1/256 texel per pixel, centre in pixels
static char title[48];
static u16 saved_backdrop;
static u8 *buf;

bool cine_active(void) { return active; }
bool cine_skipping(void) { return active && skipping; }

static s32 lerp(s32 a, s32 b, int k) { return a + (b - a) * k / 4096; }

static void apply(void)
{
    int k = t >= dur ? 4096 : (t * 4096) / dur;
    k = (k * k / 4096) * (3 * 4096 - 2 * k) / 4096; // smoothstep
    s32 s = lerp(s0, s1, k);
    s32 cx = lerp(cx0, cx1, k), cy = lerp(cy0, cy1, k);
    // keep the window inside the picture
    s32 hw = 128 * s / 256, hh = 96 * s / 256;
    cx = CLAMP(cx, hw, SW - hw);
    cy = CLAMP(cy, hh, SH - hh);
    // Queue the transform for frame_wait()'s bgUpdate() during VBlank.
    // Writing affine reference registers here (before waiting for VBlank) resets
    // the DS scanline accumulator mid-frame and makes the slide jump while typing.
    bgSet(g_bg_main[2], 0, s, s, cx << 8, cy << 8, 128 << 8, 96 << 8);
}

static void hook(void)
{
    if (!active)
        return;
    if (g_kdown & KEY_START)
        skipping = true;
    if (shown) {
        if (t < dur)
            t++;
        apply();
    }
}

static void set_motion(int m)
{
    motion = m;
    t = 0;
    const s32 FIT = 341, ONE = 256; // FIT shows the full picture height
    s0 = s1 = 288;
    cx0 = cx1 = SW / 2;
    cy0 = cy1 = SH / 2;
    switch (m) {
    case MOT_ZOOM_IN: s0 = FIT; s1 = 230; cy1 = SH / 2 - 10; break;
    case MOT_ZOOM_OUT: s0 = 230; s1 = FIT; cy0 = SH / 2 - 10; break;
    case MOT_PAN_RIGHT: s0 = s1 = ONE; cx0 = 128; cx1 = SW - 128; break;
    case MOT_PAN_LEFT: s0 = s1 = ONE; cx0 = SW - 128; cx1 = 128; break;
    case MOT_TILT_UP: s0 = s1 = 240; cy0 = SH - 90; cy1 = 90; break;
    case MOT_TILT_DOWN: s0 = s1 = 240; cy0 = 90; cy1 = SH - 90; break;
    default: s0 = 300; s1 = 280; break; // still: a barely perceptible push-in
    }
}

static void bg2_bitmap(void)
{
    g_bg_main[2] = bgInit(2, BgType_Bmp8, BgSize_B8_512x256, 0, 0);
    bgSetPriority(g_bg_main[2], 3);
    bgWrapOff(g_bg_main[2]);
    bgHide(g_bg_main[0]);
    bgHide(g_bg_main[1]);
}

void cine_letterbox(void)
{
    if (active)
        letterbox();
}

static void letterbox(void)
{
    canvas_rect(&g_top, 0, 0, 256, BAR, C_INK);
    canvas_rect(&g_top, 0, 192 - BAR, 256, BAR, C_INK);
}

static void bottom_panel(void)
{
    ui_backdrop(&g_bot);
    ui_panel(&g_bot, 16, 54, 224, 70, true);
    ui_text_in(&g_bot, &font_small, 16, 60, 224, 16, "— CINÉMATIQUE —", C_GOLD_D, C_INK, 0);
    ui_text_wrapped(&g_bot, &font_main, 24, 78, 208, title, C_GOLD, C_INK);
    ui_text_in(&g_bot, &font_small, 0, 160, 256, 14, "A : suivant    START : passer", C_BTN_LO, C_INK, 0);
}

// Load slides/<name>.sld (or the _alex/_max variant for the player's gender) into the bitmap.
static bool load(const char *name)
{
    char path[64];
    u32 size = 0;
    u8 *f = NULL;
    snprintf(path, sizeof path, "slides/%s_%s.sld", name, g_save.player_gender ? "max" : "alex");
    f = fs_try_load(path, &size);
    if (!f) {
        snprintf(path, sizeof path, "slides/%s.sld", name);
        f = fs_try_load(path, &size);
    }
    if (!f || memcmp(f, "SLD1", 4) != 0) {
        free(f);
        return false;
    }
    int ncol = f[8] | (f[9] << 8);
    const u16 *pal = (const u16 *)(f + 12);
    const u8 *lz = f + ((12 + ncol * 2 + 3) & ~3); // the BIOS decompressor wants 4-byte aligned data
    if (!buf)
        buf = malloc(SW * SH);
    if (!buf) {
        free(f);
        return false;
    }
    decompress(lz, buf, LZ77);
    // DMA reads main RAM directly: push the CPU-written data out of the cache first
    DC_FlushRange(f, size);
    DC_FlushRange(buf, SW * SH);
    dmaCopy(pal, &BG_PALETTE[1], ncol * 2);
    u16 *vram = (u16 *)BG_BMP_RAM(0);
    for (int y = 0; y < SH; y++)
        dmaCopy(buf + y * SW, vram + y * 256, SW);
    free(f);
    return true;
}

static void win_rect(int x0, int y0, int x1, int y1)
{
    x0 = CLAMP(x0, 0, 255);
    x1 = CLAMP(x1, 0, 256);
    y0 = CLAMP(y0, 0, 191);
    y1 = CLAMP(y1, 0, 192);
    if (x1 <= x0 || y1 <= y0) {
        x0 = x1 = 0;
        y0 = y1 = 0;
    }
    WIN0_X0 = x0;
    WIN0_X1 = x1 == 256 ? 255 : x1;
    WIN0_Y0 = y0;
    WIN0_Y1 = y1 == 192 ? 191 : y1;
}

// amount 0 = fully open, 16 = closed
static void iris(int amount, bool wipe)
{
    if (wipe) {
        int x = 256 * amount / 16;
        win_rect(x, 0, 256, 192);
    } else {
        int hw = 128 * (16 - amount) / 16, hh = 96 * (16 - amount) / 16;
        win_rect(128 - hw, 96 - hh, 128 + hw, 96 + hh);
    }
}

static void win_on(bool on)
{
    if (on) {
        REG_DISPCNT |= DISPLAY_WIN0_ON;
        WIN_IN = (WIN_IN & 0xFF00) | 0x1F;   // inside: everything
        WIN_OUT = (WIN_OUT & 0xFF00) | 0x08; // outside: only the canvas (letterbox, dialogue)
    } else {
        REG_DISPCNT &= ~DISPLAY_WIN0_ON;
    }
}

static void wait_frames(int n)
{
    for (int i = 0; i < n && !skipping; i++)
        frame_wait();
}

void cine_begin(const char *ttl)
{
    if (active)
        return;
    portrait_hide_all();
    dlg_close();
    gfx_fade_out(20, false);
    loading_screen(120); // Two seconds at 60 fps, plus the loading screen's fades.
    active = true;
    skipping = false;
    shown = false;
    snprintf(title, sizeof title, "%s", ttl ? ttl : "");
    frame_hook_add(hook);
    REG_DISPCNT &= ~DISPLAY_SPR_ACTIVE;
    saved_backdrop = BG_PALETTE[0];
    BG_PALETTE[0] = 0;
    canvas_clear(&g_top, 0);
    bg2_bitmap();
    dmaFillWords(0, BG_BMP_RAM(0), 512 * 256);
    letterbox();
    ui_bottom_push();
    bottom_panel();
    frame_wait();
    gfx_brightness(true, 0);
}

void cine_slide(const char *name, int mot, int tr)
{
    if (!active)
        cine_begin(NULL);
    if (skipping)
        return;
    dlg_close();
    letterbox();
    bool first = !shown;
    // out
    if (!first) {
        switch (tr) {
        case TR_FLASH:
            for (int i = 1; i <= 4; i++) { gfx_brightness(false, i * 4); frame_wait(); }
            break;
        case TR_IRIS:
        case TR_WIPE:
            win_on(true);
            for (int i = 0; i <= 16; i++) { iris(i, tr == TR_WIPE); frame_wait(); }
            break;
        case TR_CUT:
            break;
        default:
            for (int i = 1; i <= 16; i++) { gfx_brightness(false, -i); frame_wait(); }
            break;
        }
    } else if (tr == TR_IRIS || tr == TR_WIPE) {
        win_on(true);
        iris(16, tr == TR_WIPE);
    }
    shown = false;
    if (!load(name))
        dmaFillWords(0, BG_BMP_RAM(0), 512 * 256);
    set_motion(mot);
    shown = true;
    apply();
    frame_wait();
    // in
    switch (tr) {
    case TR_FLASH:
        for (int i = 16; i >= 0; i -= 2) { gfx_brightness(false, i); frame_wait(); }
        break;
    case TR_IRIS:
    case TR_WIPE:
        if (first)
            gfx_brightness(false, 0);
        for (int i = 16; i >= 0; i--) { iris(i, tr == TR_WIPE); frame_wait(); }
        win_on(false);
        break;
    case TR_CUT:
        gfx_brightness(false, 0);
        break;
    default:
        for (int i = 16; i >= 0; i--) { gfx_brightness(false, -i); frame_wait(); }
        break;
    }
    gfx_brightness(false, 0);
}

static void card_ornament(int y)
{
    canvas_hline(&g_top, 48, y, 160, C_GOLD_D);
    canvas_hline(&g_top, 64, y + 2, 128, C_GOLD);
    canvas_text(&g_top, &font_small, 124, y - 5, "★", C_GOLD, C_INK);
}

void cine_card(const char *ttl, const char *sub)
{
    if (!active)
        cine_begin(NULL);
    if (skipping)
        return;
    dlg_close();
    if (shown)
        for (int i = 1; i <= 16; i++) { gfx_brightness(false, -i); frame_wait(); }
    shown = false;
    dmaFillWords(0, BG_BMP_RAM(0), 512 * 256);
    snprintf(title, sizeof title, "%s%s%s", ttl, sub && sub[0] ? " — " : "", sub ? sub : "");
    bottom_panel();
    canvas_clear(&g_top, 0);
    card_ornament(66);
    ui_text_in(&g_top, &font_main, 0, 76, 256, 22, ttl, C_GOLD, C_INK, 0);
    if (sub && sub[0])
        ui_text_in(&g_top, &font_small, 0, 100, 256, 16, sub, C_BTN_MID, C_INK, 0);
    card_ornament(122);
    frame_wait();
    for (int i = 16; i >= 0; i--) { gfx_brightness(false, -i); frame_wait(); }
    for (int i = 0; i < 150 && !skipping; i++) {
        frame_wait();
        if (i > 20 && input_confirm())
            break;
    }
    for (int i = 1; i <= 16; i++) { gfx_brightness(false, -i); frame_wait(); }
    canvas_clear(&g_top, 0);
    letterbox();
    frame_wait();
}

void cine_end(void)
{
    if (!active)
        return;
    dlg_close();
    if (shown || skipping)
        gfx_fade_out(20, false);
    win_on(false);
    shown = false;
    frame_hook_remove(hook);
    active = false;
    skipping = false;
    free(buf);
    buf = NULL;
    canvas_clear(&g_top, 0);
    BG_PALETTE[0] = saved_backdrop;
    gfx_bg2_tiles();
    bgShow(g_bg_main[0]);
    bgShow(g_bg_main[1]);
    REG_DISPCNT |= DISPLAY_SPR_ACTIVE;
    ui_bottom_pop();
    world_refresh();
    world_redraw_bottom();
    gfx_fade_in(20, false);
}
