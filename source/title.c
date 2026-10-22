// Title screen: layered night sky over Brussels (drifting stars, skyline), sweeping searchlights,
// gold logo with the 12 orbiting EU stars, and a retro button menu on the touch screen.
#include "scenes.h"
#include "gfx.h"
#include "canvas.h"
#include "image.h"
#include "input.h"
#include "audio.h"
#include "sprite.h"
#include "save.h"
#include "dialog.h"
#include "ui.h"
#include "gen/font_data.h"

static SpriteSheet stars, beam;
static u16 *star_gfx[3], *beam_gfx;

#define BEAM_OAM 20
#define BEAMS 3

static void assets_load(void)
{
    sheet_load(&stars, "ui/stars.spr");
    sheet_load(&beam, "ui/beam.spr");
    spr_ext_pal(false, PAL_MISC, stars.pal, stars.ncolors);
    spr_ext_pal(false, PAL_FX_LOAD, beam.pal, beam.ncolors);
    for (int i = 0; i < 3; i++) {
        star_gfx[i] = spr_alloc(false, SpriteSize_16x16, SpriteColorFormat_256Color);
        spr_upload(star_gfx[i], sheet_frame(&stars, i), 256);
    }
    beam_gfx = spr_alloc(false, SpriteSize_32x64, SpriteColorFormat_256Color);
    spr_upload(beam_gfx, sheet_frame(&beam, 0), 2048);
}

static void assets_free(void)
{
    for (int i = 0; i < 3; i++)
        spr_free(false, star_gfx[i]);
    spr_free(false, beam_gfx);
    sheet_free(&stars);
    sheet_free(&beam);
}

// duplicate the first 32x32 screen block of a 512x512 text BG into the 3 others (seamless wrap)
static void bg_tile4(int layer)
{
    u16 *m = (u16 *)bgGetMapPtr(g_bg_main[layer]);
    for (int b = 1; b < 4; b++)
        dmaCopy(m, m + b * 1024, 2048);
}

static const char *const items[4] = {"New game", "Continue", "Options", "Credits & sources"};
static const int item_icon[4] = {ICON_STAR, ICON_SAVE, ICON_OPTIONS, ICON_DEX};
#define MENU_X 24
#define MENU_W 208
#define MENU_Y(i) (42 + (i) * 30)
#define MENU_H 30

static void draw_menu(int sel, bool has_save, int pressed)
{
    ui_backdrop(&g_bot);
    ui_header(&g_bot, 40, 4, 176, "Main menu");
    canvas_frame(&g_bot, MENU_X - 6, MENU_Y(0) - 8, MENU_W + 12, 4 * MENU_H + 16, FRAME_DIALOG);
    for (int i = 0; i < 4; i++) {
        int y = MENU_Y(i);
        bool off = i == 1 && !has_save;
        if (i == sel)
            canvas_rect(&g_bot, MENU_X, y + 1, MENU_W, MENU_H - 2, pressed == i ? C_GLD_HI : C_BTN_HI);
        if (i == sel)
            canvas_text(&g_bot, &font_small, MENU_X + 4 + (pressed == i ? 2 : 0), y + 8, "▶", C_RED, 0);
        ui_icon(&g_bot, MENU_X + 18, y + (MENU_H - 24) / 2, item_icon[i], 2);
        ui_text_in(&g_bot, &font_main, MENU_X + 48, y, MENU_W - 52, MENU_H, items[i], off ? C_MGREY : C_INK,
                   off ? 0 : C_SHADOW, -1);
    }
    ui_text_in(&g_bot, &font_small, 0, 176, 256, 14, "Unofficial parody · v1.0.1", C_BTN_LO, C_INK, 0);
}

static void draw_press_start(bool on)
{
    ui_backdrop(&g_bot);
    ui_panel(&g_bot, 28, 24, 200, 64, true);
    ui_text_in(&g_bot, &font_main, 28, 30, 200, 20, "EU SIMULATOR", C_GOLD, C_INK, 0);
    ui_text_in(&g_bot, &font_small, 28, 54, 200, 16, "The internship of your life", C_BTN_MID, C_INK, 0);
    if (on)
        ui_button(&g_bot, 48, 110, 160, 30, "PRESS START", BTN_SELECTED, &font_main);
    ui_text_in(&g_bot, &font_small, 0, 176, 256, 14, "Unofficial parody · v1.0.1", C_BTN_LO, C_INK, 0);
}

int scene_title(void)
{
    gfx_brightness(false, -16);
    gfx_brightness(true, -16);
    gfx_clear_scene(false);
    gfx_clear_scene(true);
    canvas_clear(&g_top, 0);
    canvas_clear(&g_bot, 0);
    int t1 = bgi_load(false, 2, "ui/title_sky.bgi", 1);
    int t2 = bgi_load(false, 0, "ui/title_stars.bgi", 1 + t1);
    bgi_load(false, 1, "ui/title_skyline.bgi", 1 + t1 + t2);
    bg_tile4(0);
    Bitmap logo;
    bmp_load(&logo, "ui/logo.bmp8");
    bmp_draw(&g_top, &logo, (256 - logo.w) / 2, 10, C_DYN);
    bmp_free(&logo);
    assets_load();
    // semi-transparent searchlights
    REG_BLDCNT = BLEND_ALPHA | BLEND_DST_BG0 | BLEND_DST_BG2 | BLEND_DST_BACKDROP;
    REG_BLDALPHA = 7 | (12 << 8);
    music_play("title");

    bool has_save = save_exists();
    int sel = has_save ? 1 : 0;
    bool menu = false;
    int t = 0;
    int result = -1;
    draw_press_start(true);
    for (int i = 16; i >= 0; i -= 2) {
        gfx_brightness(false, -i);
        gfx_brightness(true, -i);
        frame_wait();
    }
    static const int beam_x[BEAMS] = {44, 132, 214};
    while (result < 0) {
        t++;
        // drifting star field + gently bobbing skyline-free sky
        bgSetScroll(g_bg_main[0], t / 3, (t / 7) & 255);
        // 12 orbiting EU stars around the logo
        int ang = t * 96;
        oamRotateScale(&oamMain, 0, (t * 300) & 0xFFFF, intToFixed(1, 8), intToFixed(1, 8));
        for (int i = 0; i < 12; i++) {
            int a = ang + i * 65536 / 12;
            int x = 128 + (sinLerp(a) * 104 >> 12) - 8;
            int y = 46 + (cosLerp(a) * 28 >> 12) - 8;
            int frame = ((t / 6) % 12 == i) ? 2 : 0;
            oamSet(&oamMain, i, x, y, 0, PAL_MISC, SpriteSize_16x16, SpriteColorFormat_256Color,
                   star_gfx[frame], 0, false, false, false, false, false);
        }
        // searchlights sweeping the sky (pivot at their base, behind the skyline)
        for (int b = 0; b < BEAMS; b++) {
            int deg = (sinLerp((t * (60 + b * 23) + b * 9000) & 0xFFFF) * 32) >> 12; // -32..32 degrees
            int a16 = (deg * 65536 / 360) & 0xFFFF;
            oamRotateScale(&oamMain, 1 + b, -(int)(s16)a16, intToFixed(1, 8), 128); // stretched 2x vertically
            int bx = beam_x[b], by = 176;
            int cx = bx + ((sinLerp(a16) * 64) >> 12);
            int cy = by - ((cosLerp(a16) * 64) >> 12);
            oamSet(&oamMain, BEAM_OAM + b, cx - 32, cy - 64, 2, PAL_FX_LOAD, SpriteSize_32x64,
                   SpriteColorFormat_256Color, beam_gfx, 1 + b, true, false, false, false, false);
            oamSetBlendMode(&oamMain, BEAM_OAM + b, SpriteMode_Blended);
        }
        // falling twinkles
        for (int k = 0; k < 4; k++) {
            int ph = (t + k * 47) % 180;
            int x = (k * 67 + 30) % 240;
            oamSet(&oamMain, 12 + k, x, ph - 16, 1, PAL_MISC, SpriteSize_16x16, SpriteColorFormat_256Color,
                   star_gfx[1], 0, false, ph > 120, false, false, false);
        }

        if (!menu) {
            if ((t % 20) == 0) {
                int ph = (t / 20) % 4;
                ui_button(&g_bot, 48, 110, 160, 30, "PRESS START", ph == 0 ? BTN_NORMAL : BTN_SELECTED, &font_main);
            }
            if (g_kdown & (KEY_START | KEY_A) || g_touch_down) {
                sfx_play(SFX_SELECT);
                menu = true;
                draw_menu(sel, has_save, -1);
            }
        } else {
            int old = sel;
            if (g_krep & KEY_DOWN)
                sel = (sel + 1) % 4;
            if (g_krep & KEY_UP)
                sel = (sel + 3) % 4;
            if (!has_save && sel == 1)
                sel = (g_krep & KEY_UP) ? 0 : 2;
            if (sel != old) {
                sfx_play(SFX_CURSOR);
                draw_menu(sel, has_save, -1);
            }
            int pick = -1;
            if (g_kdown & (KEY_A | KEY_START))
                pick = sel;
            for (int i = 0; i < 4; i++)
                if (touch_in(MENU_X, MENU_Y(i), MENU_W, MENU_H))
                    pick = i;
            if (pick == 1 && !has_save) {
                sfx_play(SFX_ERROR);
                pick = -1;
            }
            if (pick >= 0) {
                sel = pick;
                draw_menu(sel, has_save, pick);
                sfx_play(SFX_SELECT);
                for (int k = 0; k < 6; k++)
                    frame_wait();
                result = pick;
            }
            if (g_kdown & KEY_B) {
                menu = false;
                sfx_play(SFX_CANCEL);
                draw_press_start(true);
            }
        }
        frame_wait();
    }
    if (result == 0 || result == 1)
        music_fade_out(40);
    gfx_fade_out(24, false);
    for (int i = 0; i < 24; i++)
        oamClearSprite(&oamMain, i);
    oamUpdate(&oamMain);
    REG_BLDCNT = 0;
    assets_free();
    canvas_clear(&g_top, 0);
    canvas_clear(&g_bot, 0);
    gfx_clear_scene(false);
    gfx_clear_scene(true);
    return result;
}
