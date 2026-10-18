#pragma once
#include "common.h"

// Behaviours (must match tools/tiles.py)
enum {
    B_WALK, B_SOLID, B_WATER, B_GRASS, B_LEDGE_D, B_DOOR, B_COUNTER, B_CARPET, B_WARP_EDGE,
    B_LEDGE_L, B_LEDGE_R, B_STAIRS, B_PC, B_HEAL, B_SHOP
};

enum { DIR_DOWN = 0, DIR_UP = 1, DIR_LEFT = 2, DIR_RIGHT = 3, DIR_KEEP = 255 };
extern const s8 dir_dx[4], dir_dy[4];

enum { MAPF_OUTDOOR = 1, MAPF_DARK = 2, MAPF_NOBIKE = 4, MAPF_INDOOR = 8 };

typedef struct { u16 lower[4], upper[4]; u8 beh, pad; } Meta;
typedef struct { u16 g, o; } Cell;
typedef struct { u8 x, y; u16 map; u8 dx, dy, dir, kind; } Warp;
typedef struct { u16 sprite; u8 x, y, dir, move; u16 script, hide, show, trainer; u8 range, pad; u16 name; } NpcDef;
typedef struct { u8 x, y; u16 script; } Sign;
typedef struct { u8 x, y, w, h; u16 script, cflag; u8 cval, pad[3]; } Trigger;
typedef struct { u8 x, y; u16 item, flag, pad; } ItemDef;

typedef struct {
    int id;
    int w, h;
    int flags;
    int city;          // index in europe_cities, 255 none
    char music[16];
    char name[48];
    u16 enc_table, onload, bgcolor;
    int nmeta, ntiles, ncol;
    const Meta *meta;
    const Cell *cells;
    int nwarps, nnpcs, nsigns, ntrigs, nitems;
    const Warp *warps;
    const NpcDef *npcs;
    const Sign *signs;
    const Trigger *trigs;
    const ItemDef *items;
    u8 *data;
    u16 water_pal[4];
} Map;

extern Map g_map;
extern int g_cam_x, g_cam_y;

bool map_load(int id);           // loads data, uploads tiles/palette (screen should be faded)
void map_free(void);
int map_behavior(int x, int y);  // B_SOLID outside
void map_draw_all(void);         // redraw the visible window
void map_set_camera(int cx, int cy); // pixel camera (top-left), clamps, redraws as needed
void map_animate(void);          // per-frame palette cycling
const Warp *map_warp_at(int x, int y);
const Sign *map_sign_at(int x, int y);
