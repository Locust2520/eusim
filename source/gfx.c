#include "gfx.h"
#include "canvas.h"

int g_bg_main[4];
int g_bg_sub[4];

static const u16 ui_palette[32] = {
    RGB8(248, 248, 248), // C_WHITE
    RGB8(56, 56, 64),    // C_TEXT
    RGB8(200, 200, 208), // C_SHADOW
    RGB8(216, 216, 224), // C_LGREY
    RGB8(152, 152, 168), // C_MGREY
    RGB8(88, 88, 104),   // C_DGREY
    RGB8(0, 51, 153),    // C_BLUE
    RGB8(64, 112, 216),  // C_BLUE_L
    RGB8(0, 24, 88),     // C_BLUE_D
    RGB8(255, 204, 0),   // C_GOLD
    RGB8(200, 144, 0),   // C_GOLD_D
    RGB8(224, 56, 48),   // C_RED
    RGB8(144, 24, 24),   // C_RED_D
    RGB8(72, 200, 88),   // C_GREEN
    RGB8(248, 208, 48),  // C_YELLOW
    RGB8(232, 240, 255), // C_PANEL
    // 16 type colours (order of enum Type in data.h)
    RGB8(168, 168, 152), // TECHNO
    RGB8(64, 104, 224),  // FEDERAL
    RGB8(176, 64, 48),   // SOUVERAIN
    RGB8(240, 192, 32),  // LIBERAL
    RGB8(232, 72, 88),   // SOCIAL
    RGB8(80, 184, 72),   // VERT
    RGB8(136, 104, 72),  // INDUSTRIE
    RGB8(248, 136, 32),  // ENERGIE
    RGB8(112, 88, 176),  // JURIDIQUE
    RGB8(216, 176, 64),  // MONETAIRE
    RGB8(152, 192, 64),  // AGRICOLE
    RGB8(64, 192, 216),  // NUMERIQUE
    RGB8(96, 160, 160),  // DIPLO
    RGB8(48, 48, 64),    // LOBBY
    RGB8(232, 104, 168), // POPULISTE
    RGB8(120, 96, 160),  // FANTOME
};

static const u16 ui_extra[12] = {
    RGB8(244, 248, 255), // C_BTN_HI
    RGB8(206, 222, 250), // C_BTN_MID
    RGB8(156, 184, 236), // C_BTN_LO
    RGB8(40, 64, 140),   // C_BTN_SH
    RGB8(255, 246, 184), // C_GLD_HI
    RGB8(250, 208, 72),  // C_GLD_MID
    RGB8(206, 146, 16),  // C_GLD_LO
    RGB8(14, 30, 92),    // C_NAVY1
    RGB8(26, 52, 132),   // C_NAVY2
    RGB8(255, 132, 116), // C_RED_HI
    RGB8(160, 240, 160), // C_GREEN_HI
    RGB8(26, 30, 50),    // C_INK
};

void gfx_set_ui_palette(void)
{
    dmaCopy(ui_extra, &BG_PALETTE[176], sizeof(ui_extra));
    BG_PALETTE[C_CHECK] = BG_PALETTE_SUB[C_CHECK] = RGB8(234, 236, 242); // dialog box checkerboard
    dmaCopy(ui_extra, &BG_PALETTE_SUB[176], sizeof(ui_extra));
    dmaCopy(ui_palette, &BG_PALETTE[192], sizeof(ui_palette));
    dmaCopy(ui_palette, &BG_PALETTE_SUB[192], sizeof(ui_palette));
}

void gfx_bg_pal(bool sub, int index, const u16 *pal, int count)
{
    u16 *dst = sub ? BG_PALETTE_SUB : BG_PALETTE;
    for (int i = 0; i < count; i++)
        dst[index + i] = pal[i];
}

void gfx_init(void)
{
    powerOn(POWER_ALL_2D);
    lcdMainOnTop();

    vramSetBankA(VRAM_A_MAIN_BG_0x06000000);
    vramSetBankB(VRAM_B_MAIN_BG_0x06020000);
    vramSetBankC(VRAM_C_SUB_BG_0x06200000);
    vramSetBankD(VRAM_D_SUB_SPRITE);
    vramSetBankE(VRAM_E_MAIN_SPRITE);
    vramSetBankF(VRAM_F_SPRITE_EXT_PALETTE);
    vramSetBankI(VRAM_I_SUB_SPRITE_EXT_PALETTE);

    videoSetMode(MODE_5_2D);
    videoSetModeSub(MODE_5_2D);

    // Main: BG0/BG1 text 8bpp 64x64 (map layers), BG2 ext-rot tiles (backdrop), BG3 8bpp bitmap canvas.
    g_bg_main[0] = bgInit(0, BgType_Text8bpp, BgSize_T_512x512, 0, 2);
    g_bg_main[1] = bgInit(1, BgType_Text8bpp, BgSize_T_512x512, 4, 2);
    g_bg_main[2] = bgInit(2, BgType_ExRotation, BgSize_ER_512x512, 8, 2);
    g_bg_main[3] = bgInit(3, BgType_Bmp8, BgSize_B8_256x256, 8, 0); // bitmap base 8 = 128KB
    bgSetPriority(g_bg_main[3], 0);
    bgSetPriority(g_bg_main[0], 2);
    bgSetPriority(g_bg_main[1], 1);
    bgSetPriority(g_bg_main[2], 3);

    // Sub: BG0/BG1 text 8bpp 32x32, BG2 ext-rot, BG3 bitmap canvas.
    g_bg_sub[0] = bgInitSub(0, BgType_Text8bpp, BgSize_T_256x256, 0, 1);
    g_bg_sub[1] = bgInitSub(1, BgType_Text8bpp, BgSize_T_256x256, 1, 1);
    g_bg_sub[2] = bgInitSub(2, BgType_ExRotation, BgSize_ER_256x256, 2, 1);
    g_bg_sub[3] = bgInitSub(3, BgType_Bmp8, BgSize_B8_256x256, 4, 0); // 64KB
    bgSetPriority(g_bg_sub[3], 0);
    bgSetPriority(g_bg_sub[0], 2);
    bgSetPriority(g_bg_sub[1], 1);
    bgSetPriority(g_bg_sub[2], 3);

    bgWrapOn(g_bg_main[2]);
    bgWrapOn(g_bg_sub[2]);

    oamInit(&oamMain, SpriteMapping_1D_128, true);
    oamInit(&oamSub, SpriteMapping_1D_128, true);

    gfx_clear_scene(false);
    gfx_clear_scene(true);
    BG_PALETTE[0] = RGB8(0, 0, 0);
    BG_PALETTE_SUB[0] = RGB8(0, 0, 0);
    gfx_set_ui_palette();
    canvas_init();
}

void gfx_clear_scene(bool sub)
{
    if (sub) {
        dmaFillWords(0, SUB_MAP0, 2048);
        dmaFillWords(0, SUB_MAP1, 2048);
        dmaFillWords(0, SUB_MAP2, 2048);
        dmaFillWords(0, SUB_TILES, 64);
    } else {
        dmaFillWords(0, MAIN_MAP0, 8192);
        dmaFillWords(0, MAIN_MAP1, 8192);
        dmaFillWords(0, MAIN_MAP2, 8192);
        dmaFillWords(0, MAIN_TILES, 64);
    }
    int *bg = sub ? g_bg_sub : g_bg_main;
    for (int i = 0; i < 3; i++) {
        bgSetScroll(bg[i], 0, 0);
    }
    bgSetRotateScale(bg[2], 0, intToFixed(1, 8), intToFixed(1, 8));
    bgUpdate();
}

void gfx_bg2_tiles(void)
{
    // back to the tiled ext-rotation map layer (after a cinematic used BG2 as a bitmap)
    g_bg_main[2] = bgInit(2, BgType_ExRotation, BgSize_ER_512x512, 8, 2);
    bgSetPriority(g_bg_main[2], 3);
    bgWrapOn(g_bg_main[2]);
    bgSetRotateScale(g_bg_main[2], 0, intToFixed(1, 8), intToFixed(1, 8));
    bgSetScroll(g_bg_main[2], 0, 0);
    bgUpdate();
}

void gfx_brightness(bool sub, int level)
{
    level = CLAMP(level, -16, 16);
    u16 v = 0;
    if (level > 0)
        v = (1 << 14) | level;
    else if (level < 0)
        v = (2 << 14) | (-level);
    if (sub)
        REG_MASTER_BRIGHT_SUB = v;
    else
        REG_MASTER_BRIGHT = v;
}

void gfx_fade_out(int frames, bool white)
{
    for (int i = 1; i <= frames; i++) {
        int l = (16 * i) / frames;
        gfx_brightness(false, white ? l : -l);
        gfx_brightness(true, white ? l : -l);
        frame_wait();
    }
}

void gfx_fade_in(int frames, bool white)
{
    for (int i = frames - 1; i >= 0; i--) {
        int l = (16 * i) / frames;
        gfx_brightness(false, white ? l : -l);
        gfx_brightness(true, white ? l : -l);
        frame_wait();
    }
}
