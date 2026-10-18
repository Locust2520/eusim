#pragma once
#include "common.h"
enum { BATTLE_LOST, BATTLE_WON, BATTLE_FLED, BATTLE_CAUGHT };
bool battle_trainer(int trainer);       // true if won
int battle_wild(int species, int level); // BATTLE_*
int battle_multiplayer(void);        // friendly two-player debate, current relay session
