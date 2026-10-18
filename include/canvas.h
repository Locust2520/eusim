#pragma once
#include "common.h"
#include "font.h"

// An 8bpp 256x192 software framebuffer mirrored to a BG3 bitmap. Index 0 = transparent.
typedef struct {
    u8 *px;          // 256*192
    u16 *vram;       // bitmap in VRAM (256 px stride)
    int dirty_y0, dirty_y1; // dirty row range [y0, y1)
} Canvas;

extern Canvas g_top, g_bot;

void canvas_init(void);
void canvas_flush(Canvas *c);   // copy dirty rows to VRAM (call in vblank)
void canvas_dirty(Canvas *c, int y0, int y1);

void canvas_clear(Canvas *c, u8 col);
void canvas_rect(Canvas *c, int x, int y, int w, int h, u8 col);
void canvas_hline(Canvas *c, int x, int y, int w, u8 col);
void canvas_vline(Canvas *c, int x, int y, int h, u8 col);
void canvas_box(Canvas *c, int x, int y, int w, int h, u8 col); // outline
void canvas_pixel(Canvas *c, int x, int y, u8 col);
// Draw a string; returns its width. shadow=0 for none. Handles '\n' (line feed by font line height).
int canvas_text(Canvas *c, const Font *f, int x, int y, const char *s, u8 col, u8 shadow);
int canvas_text_n(Canvas *c, const Font *f, int x, int y, const char *s, int nbytes, u8 col, u8 shadow);
void canvas_text_center(Canvas *c, const Font *f, int cx, int y, const char *s, u8 col, u8 shadow);
void canvas_text_right(Canvas *c, const Font *f, int rx, int y, const char *s, u8 col, u8 shadow);
// Blit an 8bpp image (index 0 transparent). add = palette offset added to non-zero pixels.
void canvas_blit(Canvas *c, int x, int y, int w, int h, const u8 *src, int add);
void canvas_blit_scaled2(Canvas *c, int x, int y, int w, int h, const u8 *src, int add);

// UI widgets
typedef enum { FRAME_DIALOG, FRAME_MENU, FRAME_DARK, FRAME_GOLD, FRAME_SELECT } FrameStyle;
void canvas_dialog_corners(Canvas *c, int x, int y, int w, int h);
void canvas_checker(Canvas *c, int x, int y, int w, int h, u8 a, u8 b, int size);
void canvas_frame(Canvas *c, int x, int y, int w, int h, FrameStyle st);
void canvas_bar(Canvas *c, int x, int y, int w, int h, int val, int max, u8 col);
