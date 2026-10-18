#pragma once
#include "common.h"

void world_new_game(void);   // set starting position and state
void world_run(void);        // overworld main loop (returns to title on quit)

// used by scripts
void world_wait(int frames);
void world_warp(int map, int x, int y, int dir, bool fade);
int world_actor_by_name(u16 hash);       // 0 player, -1 not found
void world_move_actor(int actor, const char *path, bool wait);
void world_face_actor(int actor, int dir);  // dir 4 = toward player, 5 = player toward actor
void world_spawn(u16 name, int sprite, int x, int y, int dir);
void world_despawn(u16 name);
void world_give_mon(int species, int level);
void world_heal_party(void);
bool world_battle_trainer(int trainer, bool nolose);
bool world_battle_wild(int species, int level, bool scripted);
void world_fanfare(const char *song);
void world_screenshake(int frames);
int world_minigame(int id);
void world_badge_ceremony(int badge);
void world_loading(int frames);
void world_special(int id, int arg);
void world_redraw_bottom(void);
void world_refresh(void);
void world_blackout(void);
void trainer_encounter(int actor, bool spotted);    // re-setup graphics after a full-screen scene (battle, menu)
void train_menu(void);
void world_map_tour(void);
