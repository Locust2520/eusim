// Overworld actors (player + NPCs): 32x32 4bpp sprites, one VRAM frame slot each,
// sheets shared per sprite id, palette bank per sheet, y-sorted OAM.
#include "actor.h"
#include "map.h"
#include "sprite.h"
#include "audio.h"

Actor g_actors[MAX_ACTORS];

#define MAX_SHEETS 14
typedef struct {
    int sprite;
    SpriteSheet sheet;
    int refs;
} SheetSlot;
static SheetSlot sheets[MAX_SHEETS];

// emote sprites (16x16, 4bpp, bank 15) are generated in code
static u16 *emote_gfx[9];
static bool emotes_ready;

static const u16 emote_pal[16] = {
    0, RGB15(4, 4, 6), RGB15(31, 31, 31), RGB15(31, 6, 6), RGB15(31, 24, 0), RGB15(6, 16, 31),
    RGB15(31, 14, 22), RGB15(20, 20, 24), RGB15(31, 31, 31), 0, 0, 0, 0, 0, 0, 0};

// 16x16 emote bitmaps: '.'=0 'k'=1 'w'=2 'r'=3 'y'=4 'b'=5 'p'=6 'g'=7
static const char *const emote_art[9][16] = {
    {0},
    {"....kkkkkkk.....", "...kwwwwwwwk....", "..kwwwwrwwwwk...", "..kwwwwrwwwwk...", "..kwwwwrwwwwk...",
     "..kwwwwrwwwwk...", "..kwwwwrwwwwk...", "..kwwwwwwwwwk...", "..kwwwwrwwwwk...", "...kwwwwwwwk....",
     "....kkwwkkk.....", "......kwk.......", ".......k........", "................", "................", "................"},
    {"....kkkkkkk.....", "...kwwwwwwwk....", "..kwwwbbbwwwk...", "..kwwbwwwbwwk...", "..kwwwwwwbwwk...",
     "..kwwwwwbwwwk...", "..kwwwwbwwwwk...", "..kwwwwwwwwwk...", "..kwwwwbwwwwk...", "...kwwwwwwwk....",
     "....kkwwkkk.....", "......kwk.......", ".......k........", "................", "................", "................"},
    {"................", "....kkkkkkk.....", "...kwwwwwwwk....", "..kwwwwwwwwwk...", "..kwwwwwwwwwk...",
     "..kwkkwkkwkkwk..", "..kwkkwkkwkkwk..", "..kwwwwwwwwwk...", "...kwwwwwwwk....", "....kkwwkkk.....",
     "......kwk.......", ".......k........", "................", "................", "................", "................"},
    {"................", "..kkk...kkk.....", ".kpppk.kpppk....", "kpwppkkpppppk...", "kpppppppppppk...",
     "kpppppppppppk...", ".kpppppppppk....", "..kpppppppk.....", "...kpppppk......", "....kpppk.......",
     ".....kpk........", "......k.........", "................", "................", "................", "................"},
    {"................", "...rr....rr.....", "...rrr..rrr.....", "....rrr.rr......", "rr..........rr..",
     "rrr........rrr..", "................", "................", "rrr........rrr..", "rr..........rr..",
     "....rr.rrr......", "...rrr..rrr.....", "...rr....rr.....", "................", "................", "................"},
    {"........k.......", ".......kbk......", "......kbbbk.....", "......kbbbk.....", ".....kbbwbbk....",
     ".....kbbwbbk....", "....kbbbbbbbk...", "....kbbbbbbbk...", "....kbbbbbbbk...", ".....kbbbbbk....",
     "......kkkkk.....", "................", "................", "................", "................", "................"},
    {"................", "......kkkkk.....", "......kkkkk.....", "......k...k.....", "......k...k.....",
     "......k...k.....", "......k...k.....", "...kkkk.kkkk....", "..kkkkk.kkkk....", "..kkkk..kkk.....",
     "................", "................", "................", "................", "................", "................"},
    {".....kkkkk......", "....kyyyyyk.....", "...kyywyyyyk....", "...kyywyyyyk....", "...kyyyyyyyk....",
     "...kyyyyyyyk....", "....kyyyyyk.....", ".....kyyyk......", ".....kgggk......", ".....kgggk......",
     "......kkk.......", "................", "................", "................", "................", "................"},
};

static void emotes_init(void)
{
    if (emotes_ready)
        return;
    spr_pal16(false, 15, emote_pal);
    for (int e = 1; e < 9; e++) {
        emote_gfx[e] = spr_alloc(false, SpriteSize_16x16, SpriteColorFormat_16Color);
        u8 tiles[128];
        memset(tiles, 0, sizeof tiles);
        for (int y = 0; y < 16; y++) {
            for (int x = 0; x < 16; x++) {
                char ch = emote_art[e][y][x];
                int v = 0;
                switch (ch) {
                case 'k': v = 1; break;
                case 'w': v = 2; break;
                case 'r': v = 3; break;
                case 'y': v = 4; break;
                case 'b': v = 5; break;
                case 'p': v = 6; break;
                case 'g': v = 7; break;
                }
                int tile = (y / 8) * 2 + (x / 8);
                int off = tile * 32 + (y % 8) * 4 + (x % 8) / 2;
                if (x & 1)
                    tiles[off] |= v << 4;
                else
                    tiles[off] |= v;
            }
        }
        spr_upload(emote_gfx[e], tiles, sizeof tiles);
    }
    emotes_ready = true;
}

static int sheet_acquire(int sprite)
{
    for (int i = 0; i < MAX_SHEETS; i++)
        if (sheets[i].refs > 0 && sheets[i].sprite == sprite) {
            sheets[i].refs++;
            return i;
        }
    for (int i = 0; i < MAX_SHEETS; i++)
        if (sheets[i].refs == 0) {
            char path[32];
            snprintf(path, sizeof path, "chars/%d.spr", sprite);
            if (!sheet_load(&sheets[i].sheet, path))
                fatal("Missing sprite %d", sprite);
            sheets[i].sprite = sprite;
            sheets[i].refs = 1;
            spr_pal16(false, i, sheets[i].sheet.pal);
            return i;
        }
    fatal("Too many sprite sheets");
}

static void sheet_release(int slot)
{
    if (slot < 0 || slot >= MAX_SHEETS || sheets[slot].refs <= 0)
        return;
    if (--sheets[slot].refs == 0)
        sheet_free(&sheets[slot].sheet);
}

void actors_reset(void)
{
    for (int i = 0; i < MAX_ACTORS; i++) {
        if (g_actors[i].active) {
            spr_free(false, g_actors[i].gfx);
            sheet_release(g_actors[i].slot);
        }
        memset(&g_actors[i], 0, sizeof(Actor));
    }
    spr_hide_range(false, OAM_WORLD, OAM_FX + 7);
    emotes_init();
}

static void upload_frame(Actor *a, int frame)
{
    if (a->cur_frame == frame)
        return;
    a->cur_frame = frame;
    spr_upload(a->gfx, sheet_frame(&sheets[a->slot].sheet, frame), 512);
}

int actor_spawn(int sprite, int tx, int ty, int dir)
{
    for (int i = 1; i < MAX_ACTORS; i++) {
        if (!g_actors[i].active) {
            Actor *a = &g_actors[i];
            memset(a, 0, sizeof(*a));
            a->active = a->visible = true;
            a->sprite = sprite;
            a->slot = sheet_acquire(sprite);
            a->gfx = spr_alloc(false, SpriteSize_32x32, SpriteColorFormat_16Color);
            a->cur_frame = -1;
            a->tx = tx;
            a->ty = ty;
            a->x = tx * 16;
            a->y = ty * 16;
            a->dir = dir;
            a->speed = 2;
            a->npc_index = -1;
            a->script = a->trainer = 0xFFFF;
            upload_frame(a, dir * 3);
            return i;
        }
    }
    return -1;
}

void actor_set_sprite(int i, int sprite)
{
    Actor *a = &g_actors[i];
    if (!a->active) {
        memset(a, 0, sizeof(*a));
        a->active = a->visible = true;
        a->gfx = spr_alloc(false, SpriteSize_32x32, SpriteColorFormat_16Color);
        a->npc_index = -1;
        a->speed = 2;
        a->script = a->trainer = 0xFFFF;
    } else {
        sheet_release(a->slot);
    }
    a->sprite = sprite;
    a->slot = sheet_acquire(sprite);
    a->cur_frame = -1;
    upload_frame(a, a->dir * 3);
}

void actor_remove(int i)
{
    Actor *a = &g_actors[i];
    if (!a->active)
        return;
    spr_free(false, a->gfx);
    sheet_release(a->slot);
    a->active = false;
}

bool actor_moving(int i)
{
    return g_actors[i].step_frames > 0;
}

int actor_at(int tx, int ty, int except)
{
    for (int i = 0; i < MAX_ACTORS; i++) {
        Actor *a = &g_actors[i];
        if (!a->active || !a->visible || i == except || a->ghost)
            continue;
        if (a->tx == tx && a->ty == ty)
            return i;
        // also the tile it is leaving
        if (a->step_frames > 0 && a->x / 16 == tx && a->y / 16 == ty)
            return i;
    }
    return -1;
}

bool tile_walkable_for(int i, int tx, int ty, int dir)
{
    int b = map_behavior(tx, ty);
    switch (b) {
    case B_WALK: case B_GRASS: case B_CARPET: case B_DOOR: case B_WARP_EDGE: case B_STAIRS:
        break;
    case B_LEDGE_D:
        if (dir != DIR_DOWN)
            return false;
        break;
    default:
        return false;
    }
    if (actor_at(tx, ty, i) >= 0)
        return false;
    return true;
}

void actor_face(int i, int dir)
{
    if (dir < 0 || dir > 3)
        return;
    g_actors[i].dir = dir;
}

bool actor_step(int i, int dir, int speed, bool check)
{
    Actor *a = &g_actors[i];
    a->dir = dir;
    int nx = a->tx + dir_dx[dir], ny = a->ty + dir_dy[dir];
    if (check && !tile_walkable_for(i, nx, ny, dir))
        return false;
    a->tx = nx;
    a->ty = ny;
    a->speed = speed;
    a->step_frames = 16 / speed;
    a->walkphase ^= 1;
    return true;
}

void actor_jump(int i, int dir)
{
    Actor *a = &g_actors[i];
    a->dir = dir;
    a->tx += dir_dx[dir] * 2;
    a->ty += dir_dy[dir] * 2;
    a->speed = 2;
    a->step_frames = 16;
    a->jumping = true;
    a->jump_t = 0;
    sfx_play(SFX_JUMP);
}

void actor_emote(int i, int emote, int frames)
{
    g_actors[i].emote = emote;
    g_actors[i].emote_t = frames;
}

void actors_update(void)
{
    for (int i = 0; i < MAX_ACTORS; i++) {
        Actor *a = &g_actors[i];
        if (!a->active)
            continue;
        if (a->step_frames > 0) {
            a->x += dir_dx[a->dir] * a->speed;
            a->y += dir_dy[a->dir] * a->speed;
            a->step_frames--;
            if (a->jumping)
                a->jump_t++;
            if (a->step_frames == 0) {
                a->x = a->tx * 16;
                a->y = a->ty * 16;
                a->jumping = false;
            }
        }
        if (a->emote_t > 0)
            a->emote_t--;
    }
}

void actors_hide_all(void)
{
    for (int i = OAM_WORLD; i <= OAM_FX + 7; i++)
        spr_hide(false, i);
}

void actors_render(void)
{
    // sort visible actors by y (higher y = in front = lower OAM index)
    int order[MAX_ACTORS], n = 0;
    for (int i = 0; i < MAX_ACTORS; i++)
        if (g_actors[i].active && g_actors[i].visible)
            order[n++] = i;
    for (int a = 1; a < n; a++) {
        int k = order[a], b = a - 1;
        while (b >= 0 && g_actors[order[b]].y < g_actors[k].y) {
            order[b + 1] = order[b];
            b--;
        }
        order[b + 1] = k;
    }
    int oam = OAM_WORLD;
    int emote_oam = OAM_FX;
    for (int k = 0; k < n && oam < OAM_FX; k++) {
        Actor *a = &g_actors[order[k]];
        int frame = a->dir * 3;
        if (a->step_frames > 0) {
            int total = 16 / a->speed;
            int prog = total - a->step_frames;
            if (prog >= total / 4 && prog < total * 3 / 4)
                frame += 1 + a->walkphase;
        }
        upload_frame(a, frame);
        int sx = a->x - g_cam_x - 8;
        int sy = a->y - g_cam_y - 16;
        if (a->jumping) {
            static const s8 arc[17] = {0, 3, 6, 8, 10, 11, 12, 12, 12, 12, 11, 10, 8, 6, 4, 2, 0};
            sy -= arc[CLAMP(a->jump_t, 0, 16)];
        }
        spr_set(false, oam, sx, sy, SpriteSize_32x32, SpriteColorFormat_16Color, a->gfx, a->slot, 2, false);
        oam++;
        if (a->emote && a->emote_t > 0 && emote_oam < OAM_FX + 8) {
            int bob = (a->emote_t / 8) & 1;
            spr_set(false, emote_oam++, sx + 12, sy - 6 - bob, SpriteSize_16x16, SpriteColorFormat_16Color,
                    emote_gfx[a->emote], 15, 0, false);
        }
    }
    for (; oam < OAM_FX; oam++)
        spr_hide(false, oam);
    for (; emote_oam < OAM_FX + 8; emote_oam++)
        spr_hide(false, emote_oam);
}
