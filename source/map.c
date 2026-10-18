// Map loading and rendering: 3 BG layers (BG2 ground, BG0 objects-below, BG1 objects-above),
// 64x64-tile wrap-around window, redrawn when the camera crosses a metatile boundary.
#include "map.h"
#include "gfx.h"
#include "fs.h"

const s8 dir_dx[4] = {0, 0, -1, 1};
const s8 dir_dy[4] = {1, -1, 0, 0};

Map g_map;
int g_cam_x, g_cam_y;
static int drawn_cx = -9999, drawn_cy = -9999;

#define WATER_IDX 188

void map_free(void)
{
    if (g_map.data)
        free(g_map.data);
    memset(&g_map, 0, sizeof(g_map));
}

bool map_load(int id)
{
    map_free();
    char path[32];
    snprintf(path, sizeof path, "maps/%d.bin", id);
    u32 size;
    u8 *d = fs_try_load(path, &size);
    if (!d)
        return false;
    if (memcmp(d, "MAP1", 4) != 0)
        fatal("Bad map %d", id);
    Map *m = &g_map;
    m->data = d;
    m->id = id;
    const u16 *h = (const u16 *)(d + 4);
    m->w = h[0];
    m->h = h[1];
    m->nmeta = h[2];
    m->ntiles = h[3];
    m->ncol = h[4];
    m->flags = d[14];
    m->city = d[15];
    memcpy(m->music, d + 16, 16);
    memcpy(m->name, d + 32, 48);
    const u16 *h2 = (const u16 *)(d + 80);
    m->enc_table = h2[0];
    m->onload = h2[1];
    m->bgcolor = h2[2];
    m->nwarps = h2[3];
    m->nnpcs = h2[4];
    m->nsigns = h2[5];
    m->ntrigs = h2[6];
    m->nitems = h2[7];
    const u8 *p = d + 96;
    const u16 *pal = (const u16 *)p;
    p += m->ncol * 2;
    const u8 *tiles = p;
    p += m->ntiles * 64;
    m->meta = (const Meta *)p;
    p += m->nmeta * sizeof(Meta);
    m->cells = (const Cell *)p;
    p += m->w * m->h * sizeof(Cell);
    m->warps = (const Warp *)p;
    p += m->nwarps * sizeof(Warp);
    m->npcs = (const NpcDef *)p;
    p += m->nnpcs * sizeof(NpcDef);
    m->signs = (const Sign *)p;
    p += m->nsigns * sizeof(Sign);
    m->trigs = (const Trigger *)p;
    p += m->ntrigs * sizeof(Trigger);
    m->items = (const ItemDef *)p;

    // upload palette (1..191) and tiles
    for (int i = 1; i < m->ncol && i < 192; i++)
        if (i < 175 || i >= 188)   // 175..187 are fixed UI shades
            BG_PALETTE[i] = pal[i];
    BG_PALETTE[0] = m->bgcolor;
    for (int k = 0; k < 4; k++)
        m->water_pal[k] = (WATER_IDX + k < m->ncol) ? pal[WATER_IDX + k] : 0;
    DC_FlushRange(tiles, m->ntiles * 64);
    dmaCopy(tiles, MAIN_TILES, m->ntiles * 64);
    drawn_cx = drawn_cy = -9999;
    return true;
}

int map_behavior(int x, int y)
{
    if (x < 0 || y < 0 || x >= g_map.w || y >= g_map.h)
        return B_SOLID;
    const Cell *c = &g_map.cells[y * g_map.w + x];
    if (c->o)
        return g_map.meta[c->o].beh;
    return g_map.meta[c->g].beh;
}

const Warp *map_warp_at(int x, int y)
{
    for (int i = 0; i < g_map.nwarps; i++)
        if (g_map.warps[i].x == x && g_map.warps[i].y == y)
            return &g_map.warps[i];
    return NULL;
}

const Sign *map_sign_at(int x, int y)
{
    for (int i = 0; i < g_map.nsigns; i++)
        if (g_map.signs[i].x == x && g_map.signs[i].y == y)
            return &g_map.signs[i];
    return NULL;
}

static inline int text64_index(int tx, int ty)
{
    tx &= 63;
    ty &= 63;
    return ((tx >> 5) + ((ty >> 5) << 1)) * 1024 + (ty & 31) * 32 + (tx & 31);
}

static void draw_cell(int cx, int cy)
{
    u16 *m0 = MAIN_MAP0, *m1 = MAIN_MAP1, *m2 = MAIN_MAP2;
    int tx = cx * 2, ty = cy * 2;
    const Meta *g = NULL, *o = NULL;
    if (cx >= 0 && cy >= 0 && cx < g_map.w && cy < g_map.h) {
        const Cell *c = &g_map.cells[cy * g_map.w + cx];
        g = &g_map.meta[c->g];
        o = c->o ? &g_map.meta[c->o] : NULL;
    }
    for (int q = 0; q < 4; q++) {
        int x = tx + (q & 1), y = ty + (q >> 1);
        u16 lo = g ? g->lower[q] : 0;
        u16 ob = o ? o->lower[q] : 0;
        u16 up = o && o->upper[q] ? o->upper[q] : (g ? g->upper[q] : 0);
        m2[(y & 63) * 64 + (x & 63)] = lo;
        int i = text64_index(x, y);
        m0[i] = ob;
        m1[i] = up;
    }
}

static void draw_window(int cx0, int cy0)
{
    for (int cy = cy0 - 1; cy < cy0 + 14; cy++)
        for (int cx = cx0 - 1; cx < cx0 + 18; cx++)
            draw_cell(cx, cy);
    drawn_cx = cx0;
    drawn_cy = cy0;
}

void map_draw_all(void)
{
    drawn_cx = drawn_cy = -9999;
    map_set_camera(g_cam_x, g_cam_y);
}

void map_set_camera(int x, int y)
{
    int mw = g_map.w * 16, mh = g_map.h * 16;
    if (mw <= 256)
        x = -(256 - mw) / 2;
    else
        x = CLAMP(x, 0, mw - 256);
    if (mh <= 192)
        y = -(192 - mh) / 2;
    else
        y = CLAMP(y, 0, mh - 192);
    g_cam_x = x;
    g_cam_y = y;
    int cx = (x >= 0 ? x / 16 : (x - 15) / 16), cy = (y >= 0 ? y / 16 : (y - 15) / 16);
    if (cx != drawn_cx || cy != drawn_cy) {
        // incremental: only redraw if moved by one cell, else full
        draw_window(cx, cy);
    }
    // BG coordinates wrap at 512; negative scroll works via masking
    bgSetScroll(g_bg_main[0], x & 511, y & 511);
    bgSetScroll(g_bg_main[1], x & 511, y & 511);
    bgSetScroll(g_bg_main[2], x & 511, y & 511);
}

void map_animate(void)
{
    // water: cycle the 4 reserved colours every 12 frames
    if (!g_map.data || g_map.ncol <= WATER_IDX)
        return;
    if (g_frame % 12 == 0) {
        int k = (g_frame / 12) & 3;
        for (int i = 0; i < 4; i++)
            BG_PALETTE[WATER_IDX + i] = g_map.water_pal[(i + k) & 3];
    }
}
