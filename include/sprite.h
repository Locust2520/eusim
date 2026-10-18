#pragma once
#include "common.h"

// OAM id ranges (per engine)
enum {
    OAM_UI = 0,          // 0..15  cursors, icons, arrows
    OAM_PORTRAIT = 16,   // 16..33 two portraits of 3x3 32x32 sprites
    OAM_BATTLE = 34,     // 34..49 battle creatures / trainer sprites / effects
    OAM_WORLD = 50,      // 50..119 overworld actors
    OAM_FX = 120,        // 120..127 transient effects
};

// Ext palette slots (8bpp sprites, 16 slots of 256 colours)
enum {
    PAL_UI = 0,
    PAL_PORTRAIT_L = 1,
    PAL_PORTRAIT_R = 2,
    PAL_BATTLE_FOE = 3,
    PAL_BATTLE_ALLY = 4,
    PAL_BATTLE_FX = 5,
    PAL_TRAINER = 6,
    PAL_MISC = 7,
    PAL_FX_LOAD = 8,   // 8, 9
    PAL_ACTOR8 = 10,   // spare 8bpp slots 10..15
};

// Upload a palette into an 8bpp extended palette slot.
void spr_ext_pal(bool sub, int slot, const u16 *pal, int count);
// Upload 16 colours into the standard OBJ palette bank (for 4bpp sprites).
void spr_pal16(bool sub, int bank, const u16 *pal);
// Allocate/free sprite graphics (libnds allocator)
u16 *spr_alloc(bool sub, SpriteSize size, SpriteColorFormat fmt);
void spr_free(bool sub, u16 *gfx);
// Copy pixels to sprite VRAM through the CPU (cache/TCM-safe, halfword writes).
void spr_upload(u16 *dst, const void *src, u32 bytes);
// Show/position an OAM entry
void spr_set(bool sub, int id, int x, int y, SpriteSize size, SpriteColorFormat fmt, u16 *gfx,
             int palette, int priority, bool hflip);
void spr_hide(bool sub, int id);
void spr_hide_range(bool sub, int from, int to);
void spr_move(bool sub, int id, int x, int y);

// Generic sprite sheet loaded from NitroFS (.spr, built by tools/mkgfx.py)
typedef struct {
    u8 bpp;          // 4 or 8
    u8 extra;        // free byte (portraits: facing 0 front, 1 right, 2 left)
    u8 fw, fh;       // frame size in pixels
    u16 nframes;
    u16 ncolors;
    u16 pal[256];
    u8 *data;        // frames in 1D tile order, frame_bytes each
    u32 frame_bytes;
} SpriteSheet;

bool sheet_load(SpriteSheet *s, const char *path);
void sheet_free(SpriteSheet *s);
const u8 *sheet_frame(const SpriteSheet *s, int frame);
SpriteSize sprite_size_for(int w, int h);
