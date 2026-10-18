// On-screen keyboard (bottom screen) for naming: touch or d-pad.
#include "scenes.h"
#include "canvas.h"
#include "gfx.h"
#include "ui.h"
#include "input.h"
#include "audio.h"
#include "dialog.h"
#include "gen/font_data.h"

static const char *const rows_upper[4] = {"AZERTYUIOP", "QSDFGHJKLM", "WXCVBNÉÈÀÇ", "-'.ÔÏÜÖÄ "};
static const char *const rows_lower[4] = {"azertyuiop", "qsdfghjklm", "wxcvbnéèàç", "-'.ôïüöä "};

#define KX 8
#define KY 64
#define KW 24
#define KH 22

// get the n-th UTF-8 character of a row into buf
static int row_char(const char *row, int n, char *buf)
{
    const char *s = row;
    for (int i = 0; *s; i++) {
        const char *st = s;
        utf8_next(&s);
        if (i == n) {
            int l = s - st;
            memcpy(buf, st, l);
            buf[l] = 0;
            return l;
        }
    }
    buf[0] = 0;
    return 0;
}

static int row_len(const char *row)
{
    int n = 0;
    const char *s = row;
    while (*s) {
        utf8_next(&s);
        n++;
    }
    return n;
}

static void draw(const char *prompt, const char *name, int cx, int cy, bool upper)
{
    ui_backdrop(&g_bot);
    canvas_frame(&g_bot, 4, 3, 248, 54, FRAME_DIALOG);
    canvas_text(&g_bot, &font_small, 14, 6, prompt, C_BLUE, 0);
    canvas_rect(&g_bot, 13, 24, 230, 25, C_BTN_LO);
    canvas_rect(&g_bot, 14, 25, 228, 23, C_PANEL);
    int w = canvas_text(&g_bot, &font_main, 18, 27, name, C_TEXT, C_SHADOW);
    if ((g_frame / 16) % 2 == 0)
        canvas_rect(&g_bot, 19 + w, 30, 2, 13, C_BLUE);
    const char *const *rows = upper ? rows_upper : rows_lower;
    for (int r = 0; r < 4; r++) {
        int n = row_len(rows[r]);
        for (int c = 0; c < n; c++) {
            char ch[8];
            row_char(rows[r], c, ch);
            int x = KX + c * KW, y = KY + r * KH;
            bool sel = (cx == c && cy == r);
            canvas_frame(&g_bot, x, y, KW - 2, KH - 2, sel ? FRAME_SELECT : FRAME_MENU);
            ui_text_in(&g_bot, &font_main, x, y, KW - 3, KH - 3, ch[0] == ' ' ? "_" : ch, C_TEXT, 0, 0);
        }
    }
    // special keys row
    static const char *const sp[3] = {"Maj/min", "Effacer", "OK"};
    for (int i = 0; i < 3; i++) {
        int x = 8 + i * 82, y = KY + 4 * KH + 4;
        bool sel = (cy == 4 && cx == i);
        canvas_frame(&g_bot, x, y, 78, 24, sel ? FRAME_SELECT : (i == 2 ? FRAME_DARK : FRAME_MENU));
        ui_text_in(&g_bot, &font_main, x, y, 77, 23, sp[i], i == 2 && !sel ? C_GOLD : C_TEXT, 0, 0);
    }
}

static void backspace(char *s)
{
    int n = strlen(s);
    if (!n)
        return;
    n--;
    while (n > 0 && ((u8)s[n] & 0xC0) == 0x80)
        n--;
    s[n] = 0;
}

static int utf8_count(const char *s)
{
    int n = 0;
    while (*s) {
        utf8_next(&s);
        n++;
    }
    return n;
}

bool keyboard_input(const char *prompt, char *out, size_t capacity, int maxlen)
{
    if (!capacity)
        return false;
    ui_bottom_push();
    char name[48];
    strncpy(name, out, sizeof(name) - 1);
    name[sizeof(name) - 1] = 0;
    int cx = 0, cy = 0;
    bool upper = true;
    int blink = -1;
    while (1) {
        int b = (g_frame / 16) % 2;
        if (b != blink) {
            draw(prompt, name, cx, cy, upper);
            blink = b;
        }
        frame_wait();
        bool redraw = false;
        int act = -2; // -2 none, -1 char, 0 shift, 1 del, 2 ok
        char typed[8] = {0};
        const char *const *rows = upper ? rows_upper : rows_lower;
        if (g_krep & KEY_RIGHT) { cx++; redraw = true; }
        if (g_krep & KEY_LEFT) { cx--; redraw = true; }
        if (g_krep & KEY_DOWN) { cy = (cy + 1) % 5; redraw = true; }
        if (g_krep & KEY_UP) { cy = (cy + 4) % 5; redraw = true; }
        int rl = cy < 4 ? row_len(rows[cy]) : 3;
        if (cx < 0) cx = rl - 1;
        if (cx >= rl) cx = cy < 4 ? 0 : (cx >= 3 ? 0 : cx);
        if (cx >= rl) cx = rl - 1;
        if (redraw)
            sfx_play(SFX_CURSOR);
        if (g_kdown & KEY_A) {
            if (cy < 4) {
                row_char(rows[cy], cx, typed);
                act = -1;
            } else
                act = cx;
        }
        if (g_kdown & KEY_B)
            act = 1;
        if (g_kdown & KEY_START)
            act = 2;
        if (g_kdown & KEY_SELECT)
            act = 0;
        if (g_touch_down) {
            for (int r = 0; r < 4; r++) {
                int n = row_len(rows[r]);
                for (int c = 0; c < n; c++)
                    if (touch_in(KX + c * KW, KY + r * KH, KW - 2, KH - 2)) {
                        cx = c;
                        cy = r;
                        row_char(rows[r], c, typed);
                        act = -1;
                    }
            }
            for (int i = 0; i < 3; i++)
                if (touch_in(8 + i * 82, KY + 4 * KH + 4, 78, 24)) {
                    cx = i;
                    cy = 4;
                    act = i;
                }
        }
        if (act == -1) {
            size_t bytes = strlen(name) + strlen(typed);
            if (utf8_count(name) < maxlen && bytes < sizeof(name) && bytes < capacity) {
                strcat(name, typed);
                sfx_play(SFX_BLIP);
                if (upper && utf8_count(name) == 1)
                    upper = false;
            } else
                sfx_play(SFX_ERROR);
            redraw = true;
        } else if (act == 0) {
            upper = !upper;
            sfx_play(SFX_SELECT);
            redraw = true;
        } else if (act == 1) {
            backspace(name);
            sfx_play(SFX_CANCEL);
            redraw = true;
        } else if (act == 2) {
            // trim spaces
            while (strlen(name) && name[strlen(name) - 1] == ' ')
                name[strlen(name) - 1] = 0;
            if (strlen(name) == 0) {
                sfx_play(SFX_ERROR);
            } else {
                sfx_play(SFX_SELECT);
                strcpy(out, name);
                ui_bottom_pop();
                return true;
            }
        }
        if (redraw)
            blink = -1;
    }
}
