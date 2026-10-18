#pragma once
#include <nds/ndstypes.h>

typedef struct {
    u16 code;  // Unicode code point
    u8 w;      // bitmap width
    u8 adv;    // advance
    u8 y;      // top offset inside the line box
    u8 h;      // bitmap rows
    u8 lsb;    // left side bearing
    u16 off;   // offset into bits[]
} FontGlyph;

typedef struct {
    const FontGlyph *glyphs;
    const u16 *bits;
    u16 count;
    u8 line_h;
} Font;

const FontGlyph *font_glyph(const Font *f, u32 code);
// Decode one UTF-8 code point; advances *s.
u32 utf8_next(const char **s);
// Width in pixels of a string (stops at '\n' or end).
extern int g_text_track;
int font_width(const Font *f, const char *s);
int font_width_n(const Font *f, const char *s, int nbytes);
