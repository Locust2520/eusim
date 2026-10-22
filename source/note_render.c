// Specimen banknotes: line engraving, guilloche paper, numerals, foil stripe and SPECIMEN overprint.
// Nothing printed on the note is translated: real euro banknotes carry the same text in every country
// (EURO in Latin, Greek and Cyrillic letters, the ECB's initials in the EU languages).
#include "note_render.h"
#include "gen/font_data.h"

const int note_values[NOTE_DENOMS] = {5, 10, 20, 50, 100, 200};

// palette offsets from NOTE_PAL
enum { P_RAMP = 0, P_TINT = 16, P_FOIL = 20, P_EU = 26, P_STAR, P_RED, P_BLACK, P_WHITE, P_GREY = 32 };
#define C(o) ((u8)(NOTE_PAL + (o)))

// dominant colours of today's notes (grey, red, blue, orange, green, yellow-brown) and a lighter companion tint
static const u8 base_rgb[NOTE_DENOMS][3] = {
    {118, 128, 136}, {200, 62, 58}, {50, 96, 186}, {228, 126, 38}, {56, 150, 82}, {196, 148, 48}};
static const u8 tint_rgb[NOTE_DENOMS][3] = {
    {176, 214, 200}, {246, 196, 120}, {200, 176, 236}, {248, 222, 120}, {150, 214, 222}, {236, 180, 132}};
static const u8 card_w[NOTE_DENOMS] = {194, 206, 215, 227, 238, 248};
static const u8 card_h[NOTE_DENOMS] = {100, 109, 117, 125, 125, 125};

static u16 rgb15(int r, int g, int b) { return (r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10); }
static int mix(int a, int b, int t) { return a + (b - a) * t / 100; }

void note_palette(u16 *out, int denom)
{
    static const u8 ink[3] = {18, 22, 46};
    static const u8 foil[6][3] = {{214, 218, 226}, {242, 242, 248}, {246, 226, 150}, {206, 232, 240},
                                  {232, 196, 232}, {150, 156, 176}};
    denom = CLAMP(denom, 0, NOTE_DENOMS - 1);
    const u8 *b = base_rgb[denom], *t = tint_rgb[denom];
    for (int i = 0; i < 16; i++) {
        int c[3];
        for (int k = 0; k < 3; k++)
            c[k] = i <= 8 ? mix(250, b[k], 6 + i * 94 / 8) : mix(b[k], ink[k], (i - 8) * 80 / 7);
        out[P_RAMP + i] = rgb15(c[0], c[1], c[2]);
    }
    for (int i = 0; i < 4; i++)
        out[P_TINT + i] = rgb15(mix(250, t[0], 30 + i * 22), mix(250, t[1], 30 + i * 22), mix(250, t[2], 30 + i * 22));
    for (int i = 0; i < 6; i++)
        out[P_FOIL + i] = rgb15(foil[i][0], foil[i][1], foil[i][2]);
    out[P_EU] = rgb15(0, 51, 153);
    out[P_STAR] = rgb15(255, 204, 0);
    out[P_RED] = rgb15(214, 40, 40);
    out[P_BLACK] = rgb15(16, 16, 24);
    out[P_WHITE] = rgb15(252, 252, 248);
    out[31] = rgb15(96, 100, 116);
    for (int i = 0; i < 16; i++)
        out[P_GREY + i] = rgb15(252 - i * 16, 252 - i * 16, 250 - i * 15);
}

void note_card_size(int denom, int *w, int *h)
{
    denom = CLAMP(denom, 0, NOTE_DENOMS - 1);
    *w = card_w[denom];
    *h = card_h[denom];
}

bool note_art_parse(NoteArt *art, const u8 *blob, u32 size)
{
    if (!blob || size < 10 || memcmp(blob, "NART", 4) != 0)
        return false;
    art->count = blob[4] | (blob[5] << 8);
    art->w = blob[6] | (blob[7] << 8);
    art->h = blob[8] | (blob[9] << 8);
    art->px = blob + 10;
    return art->count >= ART_COUNT && !(art->w & 1) && size >= 10 + (u32)(art->count * art->w * art->h / 2);
}

// ---------------------------------------------------------------- integer maths
// sine of a (1/256 turns), -256..256 (Bhaskara's approximation, exact enough for patterns)
static int isin(int a)
{
    a &= 255;
    int x = a & 127, p = x * (128 - x);
    int v = 1024 * p / (20480 - p);
    return a < 128 ? v : -v;
}

static int isqrt(int n)
{
    if (n <= 0)
        return 0;
    int r = 0, bit = 1 << 30;
    while (bit > n)
        bit >>= 2;
    while (bit) {
        if (n >= r + bit) {
            n -= r + bit;
            r = (r >> 1) + bit;
        } else
            r >>= 1;
        bit >>= 2;
    }
    return r;
}

static inline void put(Canvas *c, int x, int y, u8 col)
{
    if ((unsigned)x < 256 && (unsigned)y < 192)
        c->px[y * 256 + x] = col;
}

static int nibble(const u8 *px, int w, int x, int y)
{
    const u8 *p = px + (y * w + x) / 2;
    return (x & 1) ? *p >> 4 : *p & 15;
}

// ---------------------------------------------------------------- paper and frame
static void guilloche(Canvas *c, int x0, int y0, int w, int h, bool back)
{
    int cx = back ? w / 4 : w * 3 / 4, cy = h / 2;
    for (int y = 0; y < h; y++)
        for (int x = 0; x < w; x++) {
            u8 col = C(P_RAMP);
            int wave = (y * 16 + isin(x * 6 + (back ? 64 : 0)) * 40 / 256) & 63;
            int diag = ((x + y) * 11 + isin(y * 5) * 30 / 256) & 63;
            int dx = x - cx, dy = y - cy;
            int r = isqrt(dx * dx + dy * dy);
            int rp = r * 16 + (isin(dx * 12) + isin(dy * 12)) * 24 / 256;
            if (r < h * 2 / 5 && (rp & 63) < 9)
                col = C(P_TINT + (r < h / 6 ? 3 : 2));
            else if (wave < 5)
                col = C(P_RAMP + 2);
            else if (diag < 4)
                col = C(P_TINT + 1);
            if (x < 6 || y < 6 || x >= w - 6 || y >= h - 6)
                col = ((x + y) & 3) ? C(P_RAMP + 3) : C(P_RAMP + 5);
            put(c, x0 + x, y0 + y, col);
        }
    for (int x = 0; x < w; x++) {
        put(c, x0 + x, y0, C(P_RAMP + 13));
        put(c, x0 + x, y0 + h - 1, C(P_RAMP + 13));
        put(c, x0 + x, y0 + 6, C(P_RAMP + 9));
        put(c, x0 + x, y0 + h - 7, C(P_RAMP + 9));
    }
    for (int y = 0; y < h; y++) {
        put(c, x0, y0 + y, C(P_RAMP + 13));
        put(c, x0 + w - 1, y0 + y, C(P_RAMP + 13));
        if (y >= 6 && y < h - 6) {
            put(c, x0 + 6, y0 + y, C(P_RAMP + 9));
            put(c, x0 + w - 7, y0 + y, C(P_RAMP + 9));
        }
    }
}

// ---------------------------------------------------------------- engraving
// Tones become wavy horizontal lines whose thickness follows the darkness, with a cross-hatch in the shadows;
// contours are cut where the tone changes, so that light subjects (a white stork…) still read.
static void engrave_art(Canvas *c, int x0, int y0, const NoteArt *a, int img, int strength, int y_end)
{
    const u8 *px = a->px + img * (a->w * a->h / 2);
    for (int y = 0; y < a->h && y0 + y < y_end; y++)
        for (int x = 0; x < a->w; x++) {
            int v = nibble(px, a->w, x, y);
            int d = MIN(15, (v * 3 / 2 + (v > 0)) * strength / 100);
            int edge = 0;
            if (x + 1 < a->w)
                edge += abs(nibble(px, a->w, x + 1, y) - v);
            if (y + 1 < a->h)
                edge += abs(nibble(px, a->w, x, y + 1) - v);
            int col = -1;
            if (d) {
                int ph = (y * 16 + isin(x * 7) * 24 / 256) & 63;
                if (ph < 8 + d * 52 / 15)
                    col = 5 + d * 10 / 15;
                if (d >= 11 && ((x * 16 + y * 9) & 63) < (d - 10) * 10)
                    col = 15;
            }
            if (edge * strength >= 4 * 100)
                col = strength >= 100 ? 14 : 9;
            if (col >= 0)
                put(c, x0 + x, y0 + y, C(P_RAMP + col));
        }
}

// Portraits: lines curving around the face, as on the engraved portraits of banknotes, inside an oval vignette.
void note_engrave_face(Canvas *c, int x0, int y0, const u8 *px4, int scale)
{
    int w = NOTE_W * scale, h = NOTE_H * scale;
    int cx = w / 2, cy = h * 42 / 100;
    for (int y = 0; y < h; y++)
        for (int x = 0; x < w; x++) {
            int sx = x / scale, sy = y / scale;
            int d = nibble(px4, NOTE_W, sx, sy);
            int ex = sx * 2 - NOTE_W + 1, ey = sy * 2 - NOTE_H + 1;
            int e = ex * ex * 100 / (NOTE_W * NOTE_W) + ey * ey * 100 / (NOTE_H * NOTE_H);
            if (e > 100)
                continue;
            if (e > 64)
                d = d * (100 - e) / 36;
            if (d <= 0)
                continue;
            int dx = x - cx, dy = y - cy;
            int r = isqrt(dx * dx * 4 + dy * dy * 3) * 8 / scale;
            int ph = (r * 2 + isin(dx * 9 / scale) * 10 / 256) % 48;
            if (ph < 0)
                ph += 48;
            int col = -1;
            if (ph < d * 44 / 15)
                col = 5 + d * 10 / 15;
            if (d >= 10 && ((x * 16 + y * 12) & 47) < (d - 9) * 8)
                col = 15;
            if (col >= 0)
                put(c, x0 + x, y0 + y, C(P_RAMP + col));
        }
}

// ---------------------------------------------------------------- lettering
// Text is first rendered into a scratch canvas (1 = ink) and cropped to its ink, then stamped scaled and
// rotated with an outline.
static Canvas scratch;
static int mask_x0, mask_y0;

static void text_mask(const Font *f, const char *s, int *w, int *h)
{
    memset(scratch.px, 0, 256 * 40);
    canvas_text_n(&scratch, f, 0, 0, s, strlen(s), 1, 0);
    int x0 = 256, y0 = 40, x1 = 0, y1 = 0;
    for (int y = 0; y < 40; y++)
        for (int x = 0; x < 256; x++)
            if (scratch.px[y * 256 + x]) {
                x0 = MIN(x0, x); x1 = MAX(x1, x + 1);
                y0 = MIN(y0, y); y1 = MAX(y1, y + 1);
            }
    mask_x0 = x0;
    mask_y0 = y0;
    *w = MAX(0, x1 - x0);
    *h = MAX(0, y1 - y0);
}

static bool mask_at(int x, int y, int w, int h)
{
    return x >= 0 && y >= 0 && x < w && y < h && scratch.px[(y + mask_y0) * 256 + x + mask_x0];
}

static void stamp(Canvas *c, int cx, int cy, int mw, int mh, int scale, int angle, u8 fill, u8 edge)
{
    int cs = isin(angle + 64), sn = isin(angle);
    int hw = mw * scale / 2, hh = mh * scale / 2;
    int rad = isqrt(hw * hw + hh * hh) + 2;
    for (int pass = edge ? 0 : 1; pass < 2; pass++)
        for (int y = -rad; y <= rad; y++)
            for (int x = -rad; x <= rad; x++) {
                int u = (x * cs + y * sn) / 256 + hw, v = (-x * sn + y * cs) / 256 + hh;
                bool in = mask_at(u / scale, v / scale, mw, mh) && u >= 0 && v >= 0;
                if (pass == 1) {
                    if (in)
                        put(c, cx + x, cy + y, fill);
                } else if (in || mask_at((u + 1) / scale, v / scale, mw, mh) || (u > 0 && mask_at((u - 1) / scale, v / scale, mw, mh)) ||
                           mask_at(u / scale, (v + 1) / scale, mw, mh) || (v > 0 && mask_at(u / scale, (v - 1) / scale, mw, mh)))
                    put(c, cx + x, cy + y, edge);
            }
}

static void text(Canvas *c, const Font *f, int x, int y, const char *s, u8 col)
{
    canvas_text_n(c, f, x, y, s, strlen(s), col, 0);
}

static void eu_flag(Canvas *c, int x, int y, int w, int h)
{
    for (int j = 0; j < h; j++)
        for (int i = 0; i < w; i++)
            put(c, x + i, y + j, C(P_EU));
    int r = h * 3 / 8;
    for (int k = 0; k < 12; k++) {
        int a = k * 256 / 12;
        put(c, x + w / 2 + isin(a + 64) * r / 256, y + h / 2 + isin(a) * r / 256, C(P_STAR));
    }
}

static void star_ring(Canvas *c, int cx, int cy, int r, u8 col)
{
    for (int k = 0; k < 12; k++) {
        int a = k * 256 / 12, sx = cx + isin(a + 64) * r / 256, sy = cy + isin(a) * r / 256;
        put(c, sx, sy, col);
        put(c, sx - 1, sy, col);
        put(c, sx + 1, sy, col);
        put(c, sx, sy - 1, col);
        put(c, sx, sy + 1, col);
    }
}

static void foil_stripe(Canvas *c, int x0, int y0, int w, int h, const SaveExtra *n)
{
    for (int y = 0; y < h; y++)
        for (int x = 0; x < w; x++) {
            int k = (x * 3 + y * 2 + isin(y * 6) / 32 + 64) / 7;
            put(c, x0 + x, y0 + y, C(P_FOIL + k % 5));
        }
    for (int y = 0; y < h; y++) {
        put(c, x0 - 1, y0 + y, C(P_RAMP + 10));
        put(c, x0 + w, y0 + y, C(P_RAMP + 10));
    }
    int cy = y0 + h / 2;
    if (n->note_theme == NOTE_BIRDS) {
        // the "portrait window": the bearer's face in the foil, as Europa's portrait in today's notes
        for (int y = 0; y < 40; y++)
            for (int x = 0; x < 32 && x < w - 2; x++) {
                int ex = x * 2 - 31, ey = y * 2 - 39;
                if (ex * ex * 100 / (32 * 32) + ey * ey * 100 / (40 * 40) > 100)
                    continue;
                int d = (nibble(n->note_px, NOTE_W, x * 2, y * 2) + nibble(n->note_px, NOTE_W, x * 2 + 1, y * 2 + 1)) / 2;
                if (d > 4)
                    put(c, x0 + 1 + (x * (w - 2)) / 32, cy - 20 + y, d > 10 ? C(P_RAMP + 13) : C(P_FOIL + 5));
            }
    } else {
        star_ring(c, x0 + w / 2, cy, w / 2 - 2, C(P_FOIL + 5));
    }
}

static void signature(Canvas *c, int x0, int y0, int w, u32 seed)
{
    int px = x0, py = y0;
    for (int t = 0; t < w * 2; t++) {
        int x = x0 + t / 2;
        int y = y0 + isin(t * 13 + (int)(seed & 63)) * 4 / 256 + isin(t * 5 + (int)(seed >> 8 & 63)) * 2 / 256;
        int sx = x < px ? 1 : -1, sy = y < py ? 1 : -1;
        while (px != x || py != y) {   // continuous stroke
            put(c, px, py, C(P_RAMP + 14));
            if (px != x) px -= sx;
            if (py != y) py -= sy;
        }
    }
}

// ---------------------------------------------------------------- the note
void note_draw(Canvas *c, int x, int y, const SaveExtra *n, const NoteArt *art, bool back)
{
    int dn = CLAMP(n->note_denom, 0, NOTE_DENOMS - 1), w, h;
    note_card_size(dn, &w, &h);
    scratch.px = malloc(256 * 192);
    if (!scratch.px)
        return;
    guilloche(c, x, y, w, h, back);
    char val[8];
    snprintf(val, sizeof val, "%d", note_values[dn]);
    int foil_x = x + w * 68 / 100, foil_w = 16;
    int right = foil_x + foil_w + 3, right_w = x + w - 7 - right;
    if (!back) {
        eu_flag(c, x + 9, y + 9, 17, 12);
        char serial[16];
        snprintf(serial, sizeof serial, "Y%c%010lu", 'A' + (int)(n->note_serial % 26), (unsigned long)n->note_serial);
        text(c, &font_small, x + 30, y + 9, serial, C(P_RAMP + 12));
        if (n->note_theme == NOTE_CULTURE)
            note_engrave_face(c, x + 14, y + h - NOTE_H - 8, n->note_px, 1);
        else if (art)
            engrave_art(c, x + 8, y + h - art->h - 8, art, ART_BIRD + dn, 100, y + h - 7);
        foil_stripe(c, foil_x, y + 7, foil_w, h - 14, n);
        int vw, vh;
        text_mask(&font_main, val, &vw, &vh);
        int sc = CLAMP(MIN((right_w - 2) / MAX(1, vw), (h - 64) / MAX(1, vh)), 1, 3);
        stamp(c, right + right_w / 2, y + 11 + vh * sc / 2, vw, vh, sc, 0, C(P_RAMP + 9), C(P_RAMP + 15));
        int ty = y + 15 + vh * sc;
        text(c, &font_small, right + 1, ty, "EURO", C(P_RAMP + 13));
        text(c, &font_small, right + 1, ty + 9, "ΕΥΡΩ", C(P_RAMP + 13));
        text(c, &font_small, right + 1, ty + 18, "ЕВРО", C(P_RAMP + 13));
        signature(c, right + 1, y + h - 16, MIN(right_w - 2, 40), n->note_serial);
    } else {
        if (art) {
            engrave_art(c, x + w - art->w - 9, y + (h - art->h) / 2, art, ART_MAP, 40, y + h - 7);
            engrave_art(c, x + 9, y + MAX(27, h - art->h - 8), art,
                        (n->note_theme == NOTE_BIRDS ? ART_INSTITUTION : ART_CULTURE) + dn, 100, y + h - 7);
        }
        text(c, &font_small, x + 9, y + 8, "BCE ECB ЕЦБ EZB EKP", C(P_RAMP + 12));
        text(c, &font_small, x + 9, y + 17, "EKT EKB BĊE EBC ESB", C(P_RAMP + 12));
        int vw, vh;
        text_mask(&font_main, val, &vw, &vh);
        int sc = CLAMP((w / 3) / MAX(1, vw), 1, 3);
        stamp(c, x + w - 10 - vw * sc / 2, y + 10 + vh * sc / 2, vw, vh, sc, 0, C(P_RAMP + 9), C(P_RAMP + 15));
        static const char euro3[] = "EURO ΕΥΡΩ ЕВРО";
        text(c, &font_small, x + w - 9 - font_width_n(&font_small, euro3, strlen(euro3)), y + h - 18, euro3, C(P_RAMP + 13));
    }
    // overprint: this note is not legal tender (and could never be mistaken for one)
    int sw, sh;
    text_mask(&font_main, "SPECIMEN", &sw, &sh);
    stamp(c, x + w * 3 / 5, y + h * 7 / 10, sw, sh, 2, -12, C(P_RED), C(P_WHITE));
    free(scratch.px);
    scratch.px = NULL;
    canvas_dirty(c, y, y + h);
}
