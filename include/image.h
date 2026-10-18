#pragma once
#include "common.h"
#include "canvas.h"

// Load a tiled background (.bgi) into a text/ext-rot BG layer.
// layer: 0,1,2. tile_base_index: first tile slot to use in the 8bpp tile area (>= 1: tile 0 must stay blank).
// Returns number of tiles used, or -1 if missing.
int bgi_load(bool sub, int layer, const char *path, int tile_base_index);

// Canvas bitmaps (.bmp8): load, then blit with a palette base (colours written at pal_base..).
typedef struct {
    u16 w, h, ncol;
    u16 pal[256];
    u8 *px;
} Bitmap;

bool bmp_load(Bitmap *b, const char *path);
void bmp_free(Bitmap *b);
// Writes palette to BG palette at pal_base (main or sub) and blits with index offset pal_base-1
void bmp_draw(Canvas *c, const Bitmap *b, int x, int y, int pal_base);
