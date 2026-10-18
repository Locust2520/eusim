#pragma once
#include "common.h"

void fx_init(void);
void fx_shutdown(void);
void fx_update(void);                       // called every battle frame
void fx_move(int attacker, int type, int cat);  // blocking move animation
void fx_status(int target, int status);
void fx_stat(int target, bool up);
void fx_throw_tampon(int x, int y);         // player sends out (ball lands at x,y)
void fx_throw_ball_to_foe(int x, int y);
void fx_ball_shake(void);
void fx_ball_stars(void);
void fx_clear(void);
void fx_star_transition(void);              // overworld -> battle transition
