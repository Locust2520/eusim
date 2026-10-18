#include "input.h"

u32 g_kdown, g_kheld, g_kup, g_krep;
touchPosition g_touch;
bool g_touch_down, g_touch_held, g_touch_up;
int g_touch_x, g_touch_y;
static int rep_timer;

void input_update(void)
{
    scanKeys();
    g_kdown = keysDown();
    g_kheld = keysHeld();
    g_kup = keysUp();

    // autorepeat for directions and A
    u32 dirs = g_kheld & (KEY_UP | KEY_DOWN | KEY_LEFT | KEY_RIGHT);
    g_krep = g_kdown & ~KEY_TOUCH;
    if (dirs) {
        if (g_kdown & dirs)
            rep_timer = 18;
        else if (--rep_timer <= 0) {
            g_krep |= dirs;
            rep_timer = 5;
        }
    }

    bool was = g_touch_held;
    g_touch_held = (g_kheld & KEY_TOUCH) != 0;
    if (g_touch_held) {
        touchRead(&g_touch);
        if (g_touch.px || g_touch.py) {
            g_touch_x = g_touch.px;
            g_touch_y = g_touch.py;
        }
    }
    g_touch_down = g_touch_held && !was;
    g_touch_up = !g_touch_held && was;
}

bool touch_in(int x, int y, int w, int h)
{
    return g_touch_down && g_touch_x >= x && g_touch_x < x + w && g_touch_y >= y && g_touch_y < y + h;
}

bool touch_released_in(int x, int y, int w, int h)
{
    return g_touch_up && g_touch_x >= x && g_touch_x < x + w && g_touch_y >= y && g_touch_y < y + h;
}

bool input_confirm(void)
{
    return (g_kdown & (KEY_A | KEY_B)) || g_touch_down;
}
