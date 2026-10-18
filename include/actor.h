#pragma once
#include "common.h"

#define MAX_ACTORS 40
#define PLAYER 0

enum { MOVE_STILL, MOVE_LOOK, MOVE_WANDER, MOVE_WALK_H, MOVE_WALK_V, MOVE_SPIN };
enum { EMOTE_NONE, EMOTE_EXCL, EMOTE_QUESTION, EMOTE_DOTS, EMOTE_HEART, EMOTE_ANGER, EMOTE_SWEAT, EMOTE_NOTE, EMOTE_IDEA };

typedef struct {
    bool active, visible;
    int sprite;        // character sprite id (chars/<id>.spr)
    int slot;          // loaded sheet slot
    int x, y;          // pixel position of the tile top-left
    int tx, ty;        // tile position (destination while moving)
    int dir;
    int step_frames;   // frames remaining in current step
    int speed;         // pixels per frame (1, 2 or 4)
    int anim, walkphase;
    int cur_frame;     // frame currently in VRAM
    u16 *gfx;
    int npc_index;     // index in map npc defs (-1 = player / scripted)
    int move, home_x, home_y, timer;
    u16 script, trainer;
    u8 range;
    int emote, emote_t;
    bool frozen, jumping;
    int jump_t;
    bool ghost;        // translucent / passes through
} Actor;

extern Actor g_actors[MAX_ACTORS];

void actors_reset(void);
int actor_spawn(int sprite, int tx, int ty, int dir);  // returns index
void actor_remove(int i);
void actor_set_sprite(int i, int sprite);
bool actor_moving(int i);
// Start a step in a direction. Returns false if blocked (turns anyway).
bool actor_step(int i, int dir, int speed, bool check_collision);
void actor_jump(int i, int dir);       // ledge jump (2 tiles)
void actor_face(int i, int dir);
int actor_at(int tx, int ty, int except);  // actor index occupying tile or -1
void actors_update(void);              // advance movement/animation
void actors_render(void);              // write OAM (call after camera update)
void actor_emote(int i, int emote, int frames);
void actors_hide_all(void);
bool tile_walkable_for(int i, int tx, int ty, int dir);
