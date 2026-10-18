#pragma once
#include "common.h"
#include "canvas.h"
#include "sprite.h"

// Canvas drawing (bottom screen menus). Icons share one 31-colour palette at C_DYN;
// big pictures use C_DYN with their own palette (never shown together with icons).
void creature_icon_draw(Canvas *c, int species, int x, int y);   // 32x32
void creature_big_draw(Canvas *c, int species, int x, int y);    // 64x64
// Battle sprites (main engine, 8bpp, ext palette slot): back = player side
bool creature_sheet_load(SpriteSheet *s, int species, bool back);
