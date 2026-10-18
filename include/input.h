#pragma once
#include "common.h"

extern u32 g_kdown, g_kheld, g_kup, g_krep;   // pressed this frame / held / released / pressed+autorepeat
extern touchPosition g_touch;
extern bool g_touch_down, g_touch_held, g_touch_up;
extern int g_touch_x, g_touch_y;            // last valid position

void input_update(void);
// True if the stylus was tapped (pressed) inside the rectangle this frame
bool touch_in(int x, int y, int w, int h);
// True if the stylus was released inside the rect (button behaviour)
bool touch_released_in(int x, int y, int w, int h);
// Any confirmation: A or tap anywhere (for dialogs)
bool input_confirm(void);
