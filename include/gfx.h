#pragma once
#include "common.h"

// ---- Palette layout (both engines) ----
// BG palette:   1..191 scene art (map tiles, backgrounds), 192..223 fixed UI, 224..255 dynamic UI images
// Canvas (BG3 8bpp bitmap) uses index 0 as transparent.
enum {
    C_TRANSP = 0,
    // extra UI shades (176..187, both engines; maps use 1..175 + water 188..191)
    C_CHECK = 175, C_BTN_HI = 176, C_BTN_MID, C_BTN_LO, C_BTN_SH, C_GLD_HI, C_GLD_MID, C_GLD_LO, C_NAVY1, C_NAVY2, C_RED_HI, C_GREEN_HI, C_INK,
    C_WHITE = 192,
    C_TEXT,        // dark text
    C_SHADOW,      // text shadow on light panels
    C_LGREY,
    C_MGREY,
    C_DGREY,
    C_BLUE,        // EU blue
    C_BLUE_L,
    C_BLUE_D,
    C_GOLD,
    C_GOLD_D,
    C_RED,
    C_RED_D,
    C_GREEN,
    C_YELLOW,
    C_PANEL,       // pale blue panel
    C_TYPE0 = 208, // 16 type colours 208..223
    C_DYN = 224,   // 32 dynamic colours
};


void gfx_init(void);
void gfx_set_ui_palette(void);
// Copy a palette fragment (RGB15) into BG palette of main/sub at index.
void gfx_bg_pal(bool sub, int index, const u16 *pal, int count);
// Fades using master brightness: level -16 (black) .. 0 .. 16 (white)
void gfx_brightness(bool sub, int level);
void gfx_bg2_tiles(void);
void gfx_fade_out(int frames, bool white);
void gfx_fade_in(int frames, bool white);
// Clear the scene BG layers (BG0..BG2) on a screen
void gfx_clear_scene(bool sub);

// VRAM addresses for the layout (see gfx.c)
#define MAIN_MAP0 ((u16 *)BG_MAP_RAM(0))    // BG0 64x64 map (8KB)
#define MAIN_MAP1 ((u16 *)BG_MAP_RAM(4))    // BG1 64x64 map (8KB)
#define MAIN_MAP2 ((u16 *)BG_MAP_RAM(8))    // BG2 64x64 ext-rot map (8KB)
#define MAIN_TILES ((u16 *)BG_TILE_RAM(2))  // 8bpp tiles (64KB, 1024 tiles)
#define SUB_MAP0 ((u16 *)BG_MAP_RAM_SUB(0))
#define SUB_MAP1 ((u16 *)BG_MAP_RAM_SUB(1))
#define SUB_MAP2 ((u16 *)BG_MAP_RAM_SUB(2))
#define SUB_TILES ((u16 *)BG_TILE_RAM_SUB(1)) // 8bpp tiles (48KB, 768 tiles)

extern int g_bg_main[4];
extern int g_bg_sub[4];
