// Save slot picker (3 slots), shown on the touch screen.
#include "scenes.h"
#include "lang.h"
#include "canvas.h"
#include "gfx.h"
#include "input.h"
#include "audio.h"
#include "dialog.h"
#include "save.h"
#include "ui.h"
#include "gen/font_data.h"

#define CARD_X 12
#define CARD_W 232
#define CARD_H 44
#define CARD_Y(i) (30 + (i) * 50)

static void draw_card(int i, const SlotInfo *si, BtnStyle st)
{
    int y = CARD_Y(i);
    ui_button(&g_bot, CARD_X, y, CARD_W, CARD_H, NULL, st, NULL);
    int p = st == BTN_PRESSED;
    u8 ink = st == BTN_DISABLED ? C_MGREY : C_INK;
    char buf[48];
    snprintf(buf, sizeof buf, "%d", i + 1);
    ui_panel(&g_bot, CARD_X + 6 + p, y + 8 + p, 26, 28, true);
    ui_text_in(&g_bot, &font_main, CARD_X + 6 + p, y + 8 + p, 26, 28, buf, C_GOLD, C_INK, 0);
    if (!si->used) {
        ui_text_in(&g_bot, &font_main, CARD_X + 40 + p, y + p, CARD_W - 48, CARD_H, "— Empty slot —", ink, 0, -1);
        return;
    }
    canvas_text(&g_bot, &font_main, CARD_X + 42 + p, y + 4 + p, si->name, ink, 0);
    u32 secs = si->play_frames / 60;
    snprintf(buf, sizeof buf, "%lu h %02lu", (unsigned long)(secs / 3600), (unsigned long)((secs / 60) % 60));
    canvas_text_right(&g_bot, &font_small, CARD_X + CARD_W - 10 + p, y + 6 + p, buf, ink, 0);
    for (int b = 0; b < 8; b++)
        canvas_text(&g_bot, &font_small, CARD_X + 42 + b * 10 + p, y + 25 + p, "★",
                    (si->badges >> b) & 1 ? C_GOLD_D : C_LGREY, 0);
    snprintf(buf, sizeof buf, T("Eurodex: %d"), si->dex);
    canvas_text_right(&g_bot, &font_small, CARD_X + CARD_W - 10 + p, y + 25 + p, buf, ink, 0);
}

// mode 0 = continue (only used slots), 1 = new game, 2 = save
int slot_picker(int mode)
{
    SlotInfo si[SAVE_SLOTS];
    for (int i = 0; i < SAVE_SLOTS; i++)
        save_slot_info(i, &si[i]);
    int sel = mode == 2 ? g_save_slot : 0;
    if (mode == 0)
        while (sel < SAVE_SLOTS && !si[sel].used)
            sel++;
    if (sel >= SAVE_SLOTS)
        return -1;
    ui_bottom_push();
    bool redraw = true;
    int result = -1;
    static const char *const titles[3] = {"Continue: choose a game", "New game: slot",
                                          "Save to…"};
    while (1) {
        if (redraw) {
            ui_backdrop(&g_bot);
            ui_header(&g_bot, 8, 4, 240, titles[mode]);
            for (int i = 0; i < SAVE_SLOTS; i++) {
                BtnStyle st = (mode == 0 && !si[i].used) ? BTN_DISABLED : i == sel ? BTN_SELECTED : BTN_NORMAL;
                draw_card(i, &si[i], st);
            }
            ui_text_in(&g_bot, &font_small, 0, 178, 256, 13, "A: choose   B: back", C_BTN_LO, C_INK, 0);
            redraw = false;
        }
        frame_wait();
        int old = sel;
        if (g_krep & KEY_DOWN)
            do sel = (sel + 1) % SAVE_SLOTS; while (mode == 0 && !si[sel].used);
        if (g_krep & KEY_UP)
            do sel = (sel + SAVE_SLOTS - 1) % SAVE_SLOTS; while (mode == 0 && !si[sel].used);
        if (old != sel) {
            sfx_play(SFX_CURSOR);
            redraw = true;
        }
        int pick = -1;
        if (g_kdown & KEY_A)
            pick = sel;
        for (int i = 0; i < SAVE_SLOTS; i++)
            if (touch_in(CARD_X, CARD_Y(i), CARD_W, CARD_H))
                pick = i;
        if (pick >= 0 && mode == 0 && !si[pick].used) {
            sfx_play(SFX_ERROR);
            pick = -1;
        }
        if (pick >= 0) {
            draw_card(pick, &si[pick], BTN_PRESSED);
            sfx_play(SFX_SELECT);
            for (int k = 0; k < 6; k++)
                frame_wait();
            if (mode != 0 && si[pick].used && (mode == 1 || pick != g_save_slot)) {
                dlg_say_nowait("", "This slot already contains a game. Overwrite it?");
                bool yes = dlg_yesno();
                dlg_close();
                if (!yes) {
                    redraw = true;
                    continue;
                }
            }
            result = pick;
            break;
        }
        if (g_kdown & KEY_B) {
            sfx_play(SFX_CANCEL);
            break;
        }
    }
    ui_bottom_pop();
    return result;
}
