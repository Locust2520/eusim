#include "font.h"
#include <stddef.h>

const FontGlyph *font_glyph(const Font *f, u32 code)
{
    int lo = 0, hi = f->count - 1;
    while (lo <= hi) {
        int mid = (lo + hi) >> 1;
        u32 c = f->glyphs[mid].code;
        if (c == code)
            return &f->glyphs[mid];
        if (c < code)
            lo = mid + 1;
        else
            hi = mid - 1;
    }
    if (code != '?')
        return font_glyph(f, '?');
    return NULL;
}

u32 utf8_next(const char **ps)
{
    const unsigned char *s = (const unsigned char *)*ps;
    u32 c = *s++;
    int more = c >= 0xF0 ? 3 : c >= 0xE0 ? 2 : c >= 0xC0 ? 1 : 0;
    if (more) {
        c &= 0x3F >> more;
        for (int i = 0; i < more; i++, s++) {
            // a sequence cut short (a string truncated into a fixed buffer): stop there, never step over the NUL
            if ((*s & 0xC0) != 0x80) {
                *ps = (const char *)s;
                return 0xFFFD;
            }
            c = (c << 6) | (*s & 0x3F);
        }
    }
    *ps = (const char *)s;
    return c;
}

int g_text_track; // extra advance per glyph (negative = condensed), set by ui_text_in

int font_width_n(const Font *f, const char *s, int nbytes)
{
    const char *end = s + nbytes;
    int w = 0;
    while (*s && *s != '\n' && s < end) {
        u32 c = utf8_next(&s);
        const FontGlyph *g = font_glyph(f, c);
        if (g)
            w += g->adv + g_text_track;
    }
    return w;
}

int font_width(const Font *f, const char *s)
{
    return font_width_n(f, s, 1 << 30);
}
