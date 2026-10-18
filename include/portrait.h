#pragma once
#include "common.h"

enum { SIDE_LEFT = 0, SIDE_RIGHT = 1 };

// Character portraits (96x96, 8bpp) for cutscenes, on the top screen above the map.
void portrait_show(int side, const char *who, const char *expr);
void portrait_expr(int side, const char *expr);
void portrait_hide(int side);
void portrait_hide_all(void);
void portrait_focus(int side);       // dim the other portrait (-1 = none)
bool portrait_busy(void);            // sliding
void portrait_update(void);          // per-frame (registered as frame hook)
const char *portrait_who(int side);
void portrait_set_y(int y);          // default 38
void portrait_shake(int side, int frames);
