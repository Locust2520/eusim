#pragma once
#include "save.h"
#include "data.h"

void mon_create(Mon *m, int species, int level);
int mon_stat(const Mon *m, int stat);
int mon_max_hp(const Mon *m);
u32 exp_for_level(int growth, int level);
int mon_iv(const Mon *m, int stat);
const char *mon_name(const Mon *m);
// Teach a move: returns slot used, -1 if already known, -2 if 4 moves (caller must ask)
int mon_learn(Mon *m, int move);
void mon_heal(Mon *m);
// Add to party or box; marks dex caught. Returns 0 party, 1 box, -1 full
int party_add(const Mon *m);
void party_heal_all(void);
int party_first_alive(void);
bool party_all_fainted(void);
void dex_seen(int species);
void dex_caught(int species);
bool dex_is_seen(int species);
bool dex_is_caught(int species);
int dex_count_caught(void);
int dex_count_seen(void);
// Items
int bag_count(int item);
void bag_add(int item, int n);
bool bag_take(int item, int n);
