#include "portrait.h"
#include "sprite.h"
#include "fs.h"
#include "canvas.h"
#include "gfx.h"
#include "gen/font_data.h"

typedef struct {
    bool loaded, hiding;
    char who[20];
    char expr[12];
    u16 *gfx[9];
    int x, tx, shake;
    u16 pal[256];
    int ncol;
    bool dim;
    u8 facing;
    bool away;           // sulking: turned away from the other speaker
    const char *emote;   // shown when the expression art is missing
    int emote_drawn_x;
} Portrait;

static Portrait pt[2];
static int base_y = 38;

static void upload_pal(int side)
{
    Portrait *p = &pt[side];
    u16 tmp[256];
    for (int i = 0; i < p->ncol; i++) {
        u16 c = p->pal[i];
        if (p->dim) {
            int r = (c & 31) * 5 / 8, g = ((c >> 5) & 31) * 5 / 8, b = ((c >> 10) & 31) * 5 / 8;
            c = r | (g << 5) | (b << 10);
        }
        tmp[i] = c;
    }
    spr_ext_pal(false, side == 0 ? PAL_PORTRAIT_L : PAL_PORTRAIT_R, tmp, p->ncol);
}

static bool load_into(int side, const char *who, const char *expr)
{
    Portrait *p = &pt[side];
    char path[64];
    SpriteSheet s;
    // "sulk" = pouting art if any, else the angry/neutral art turned away from the conversation
    p->away = !strcmp(expr, "sulk");
    snprintf(path, sizeof(path), "portraits/%s_%s.spr", who, expr);
    if (p->away && !fs_exists(path))
        snprintf(path, sizeof(path), "portraits/%s_angry.spr", who);
    p->emote = NULL;
    if (!sheet_load(&s, path)) {
        snprintf(path, sizeof(path), "portraits/%s_neutral.spr", who);
        if (!sheet_load(&s, path))
            return false;
        // no art for this expression: a little speech bubble emote instead
        if (!strcmp(expr, "happy")) p->emote = "♥";
        else if (!strcmp(expr, "angry")) p->emote = "#!";
        else if (!strcmp(expr, "surprised")) p->emote = "!?";
        else if (!strcmp(expr, "worried")) p->emote = "…";
        else if (!strcmp(expr, "sulk")) p->emote = "~";
    }
    if (!p->loaded) {
        for (int i = 0; i < 9; i++)
            p->gfx[i] = spr_alloc(false, SpriteSize_32x32, SpriteColorFormat_256Color);
        p->loaded = true;
    }
    for (int i = 0; i < 9; i++)
        spr_upload(p->gfx[i], sheet_frame(&s, i), 1024);
    p->ncol = s.ncolors;
    p->facing = s.extra;
    memcpy(p->pal, s.pal, sizeof(u16) * s.ncolors);
    sheet_free(&s);
    strncpy(p->who, who, sizeof(p->who) - 1);
    strncpy(p->expr, expr, sizeof(p->expr) - 1);
    upload_pal(side);
    return true;
}

static void place(int side)
{
    Portrait *p = &pt[side];
    int sx = p->x + (p->shake ? ((p->shake & 2) ? 2 : -2) : 0);
    // portraits face the centre of the screen: left side looks right, right side looks left
    bool flip = (side == SIDE_LEFT && p->facing == 2) || (side == SIDE_RIGHT && p->facing == 1);
    if (p->away && p->facing)
        flip = !flip;
    for (int i = 0; i < 9; i++) {
        int id = OAM_PORTRAIT + side * 9 + i;
        int col = i % 3;
        if (flip)
            col = 2 - col;
        int x = sx + col * 32, y = base_y + (i / 3) * 32;
        spr_set(false, id, x, y, SpriteSize_32x32, SpriteColorFormat_256Color, p->gfx[i],
                side == 0 ? PAL_PORTRAIT_L : PAL_PORTRAIT_R, 1, flip);
    }
}

void portrait_show(int side, const char *who, const char *expr)
{
    Portrait *p = &pt[side];
    bool was = p->loaded && !p->hiding;
    bool same = was && strcmp(p->who, who) == 0;
    if (!load_into(side, who, expr ? expr : "neutral"))
        return;
    p->hiding = false;
    p->tx = side == 0 ? 6 : 256 - 96 - 6;
    if (!same)
        p->x = side == 0 ? -100 : 260;
    place(side);
}

void portrait_expr(int side, const char *expr)
{
    Portrait *p = &pt[side];
    if (!p->loaded || strcmp(p->expr, expr) == 0)
        return;
    load_into(side, p->who, expr);
}

void portrait_hide(int side)
{
    Portrait *p = &pt[side];
    if (!p->loaded)
        return;
    p->hiding = true;
    p->tx = side == 0 ? -100 : 260;
}

void portrait_hide_all(void)
{
    portrait_hide(0);
    portrait_hide(1);
    while (portrait_busy())
        frame_wait();
}

void portrait_focus(int side)
{
    for (int s = 0; s < 2; s++) {
        bool d = (side >= 0 && s != side);
        if (pt[s].loaded && pt[s].dim != d) {
            pt[s].dim = d;
            upload_pal(s);
        }
    }
}

bool portrait_busy(void)
{
    for (int s = 0; s < 2; s++)
        if (pt[s].loaded && pt[s].x != pt[s].tx)
            return true;
    return false;
}

const char *portrait_who(int side)
{
    return (pt[side].loaded && !pt[side].hiding) ? pt[side].who : NULL;
}

void portrait_set_y(int y) { base_y = y; }

void portrait_shake(int side, int frames)
{
    pt[side].shake = frames;
}

static void draw_emote(int s)
{
    Portrait *p = &pt[s];
    int bx = (s == 0) ? 84 : 256 - 96 - 6 - 14;
    int by = base_y - 6;
    if (p->emote_drawn_x) {
        canvas_rect(&g_top, p->emote_drawn_x, by, 26, 20, 0);
        p->emote_drawn_x = 0;
    }
    if (p->emote && p->loaded && !p->hiding && p->x == p->tx) {
        canvas_frame(&g_top, bx, by, 26, 20, FRAME_MENU);
        canvas_text_center(&g_top, &font_main, bx + 13, by + 2, p->emote, C_RED, 0);
        p->emote_drawn_x = bx;
    }
}

void portrait_update(void)
{
    for (int s = 0; s < 2; s++) {
        Portrait *p = &pt[s];
        bool want = p->emote && p->loaded && !p->hiding && p->x == p->tx;
        if (want != (p->emote_drawn_x != 0) || (want && (g_frame & 63) == 0))
            draw_emote(s);
        if (!p->loaded)
            continue;
        if (p->x != p->tx) {
            int d = p->tx - p->x;
            int step = d / 4;
            if (step == 0)
                step = d > 0 ? 1 : -1;
            p->x += step;
        }
        if (p->shake > 0)
            p->shake--;
        if (p->hiding && p->x == p->tx) {
            for (int i = 0; i < 9; i++) {
                spr_hide(false, OAM_PORTRAIT + s * 9 + i);
                spr_free(false, p->gfx[i]);
                p->gfx[i] = NULL;
            }
            p->loaded = false;
            p->hiding = false;
            p->dim = false;
            continue;
        }
        place(s);
    }
}
