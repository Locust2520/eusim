// Options screen and the scrolling text viewer used for credits / sources.
#include "scenes.h"
#include "canvas.h"
#include "gfx.h"
#include "ui.h"
#include "lang.h"
#include "input.h"
#include "audio.h"
#include "save.h"
#include "fs.h"
#include "dialog.h"
#include "gen/font_data.h"

#define NOPT 6
#define OPT_Y(i) (30 + (i) * 21)
#define OPT_H 20

void scene_options(bool in_game)
{
    static const char *const labels[NOPT] = {"Langue", "Vitesse du texte", "Son du texte", "Volume musique",
                                             "Animations de combat", "Prénom"};
    static const char *const speeds[3] = {"Lente", "Normale", "Rapide"};
    int sel = 0;
    int count = in_game ? NOPT : NOPT - 1;
    bool redraw = true;
    ui_bottom_push();
    while (1) {
        if (redraw) {
            ui_backdrop(&g_bot);
            ui_header(&g_bot, 40, 4, 176, "Options");
            for (int i = 0; i < count; i++) {
                int y = OPT_Y(i);
                canvas_frame(&g_bot, 6, y, 244, OPT_H + 1, i == sel ? FRAME_SELECT : FRAME_MENU);
                ui_text_in(&g_bot, &font_main, 10, y, 120, OPT_H, labels[i], C_BLUE, 0, -1);
                char val[48];
                if (i == 0)
                    snprintf(val, sizeof val, "%s", g_langs[g_lang].name);
                else if (i == 1)
                    snprintf(val, sizeof val, "%s", tr(speeds[g_save.opt_text_speed]));
                else if (i == 2)
                    snprintf(val, sizeof val, "%s", tr(g_save.opt_text_mute ? "Non" : "Oui"));
                else if (i == 3) {
                    val[0] = 0;
                    for (int k = 0; k < 4; k++)
                        strcat(val, k < g_save.opt_music ? "★" : "·");
                } else if (i == 4)
                    snprintf(val, sizeof val, "%s", tr(g_save.opt_battle_anim ? "Oui" : "Non"));
                else
                    snprintf(val, sizeof val, "%s", g_save.player_name);
                ui_text_in(&g_bot, &font_main, 150, y, 74, OPT_H, val, C_TEXT, C_SHADOW, 0);
                if (i > 0 && i < 5) {
                    ui_button(&g_bot, 130, y + 4, 18, 16, "◀", BTN_DARK, &font_small);
                    ui_button(&g_bot, 226, y + 4, 18, 16, "▶", BTN_DARK, &font_small);
                } else
                    ui_button(&g_bot, 226, y + 4, 18, 16, "▶", BTN_DARK, &font_small);
            }
            ui_button(&g_bot, 72, 162, 112, 26, "Retour", BTN_DARK, &font_main);
            redraw = false;
        }
        frame_wait();
        int delta = 0;
        if (g_krep & KEY_UP) { sel = (sel + count - 1) % count; redraw = true; sfx_play(SFX_CURSOR); }
        if (g_krep & KEY_DOWN) { sel = (sel + 1) % count; redraw = true; sfx_play(SFX_CURSOR); }
        if (g_krep & KEY_LEFT) delta = -1;
        if (g_krep & (KEY_RIGHT | KEY_A)) delta = 1;
        for (int i = 0; i < count; i++) {
            int y = OPT_Y(i);
            if (touch_in(126, y, 50, OPT_H)) { sel = i; delta = -1; }
            if (touch_in(200, y, 50, OPT_H)) { sel = i; delta = 1; }
            if ((i == 0 || i == 5) && touch_in(6, y, 244, OPT_H)) { sel = i; delta = 1; }
        }
        if (delta) {
            sfx_play(SFX_SELECT);
            if (sel == 0) {
                ui_bottom_push();
                int li = lang_picker(g_lang);
                ui_bottom_pop();
                if (li != g_lang) {
                    lang_set(li);
                    save_lang_store(li);
                }
            } else if (sel == 1)
                g_save.opt_text_speed = CLAMP(g_save.opt_text_speed + delta, 0, 2);
            else if (sel == 2)
                g_save.opt_text_mute = !g_save.opt_text_mute;
            else if (sel == 3) {
                g_save.opt_music = CLAMP(g_save.opt_music + delta, 0, 4);
                music_set_volume(g_save.opt_music * 110 / 4);
            } else if (sel == 4)
                g_save.opt_battle_anim = !g_save.opt_battle_anim;
            else {
                keyboard_input("Ton prénom (10 lettres max.) :", g_save.player_name, sizeof g_save.player_name, 10);
                redraw = true;
                continue;
            }
            redraw = true;
        }
        if ((g_kdown & (KEY_B | KEY_START)) || touch_in(72, 162, 112, 26)) {
            sfx_play(SFX_CANCEL);
            break;
        }
    }
    ui_bottom_pop();
}

// ---------------------------------------------------------------- text viewer
// File format: UTF-8 lines. "# Title" = section title (gold), "" = blank, else wrapped text.
static void viewer(const char *path, const char *title)
{
    u32 size;
    char *txt = lang_load_text(path, &size);
    if (!txt)
        return;
    txt = realloc(txt, size + 1);
    txt[size] = 0;
    // pre-wrap into display lines
    #define MAXL 1500
    static const char *lstart[MAXL];
    static u16 llen[MAXL];
    static u8 lkind[MAXL];
    int n = 0;
    char *s = txt;
    while (*s && n < MAXL) {
        char *e = strchr(s, '\n');
        if (!e)
            e = s + strlen(s);
        int kind = 0;
        if (s[0] == '#') {
            kind = 1;
            s += 2;
        }
        int len = e - s;
        if (len == 0) {
            lstart[n] = s;
            llen[n] = 0;
            lkind[n++] = 0;
        }
        while (len > 0 && n < MAXL) {
            int take = len, last_sp = -1, k = 0;
            while (k < len && font_width_n(&font_small, s, k + 1) <= 228) {
                if (s[k] == ' ')
                    last_sp = k;
                k++;
            }
            take = k;
            if (k < len && last_sp > 0)
                take = last_sp;
            lstart[n] = s;
            llen[n] = take;
            lkind[n++] = kind;
            s += take;
            len -= take;
            while (len > 0 && *s == ' ') {
                s++;
                len--;
            }
        }
        s = (*e) ? e + 1 : e;
    }
    int per = 14, top = 0;
    bool redraw = true;
    ui_bottom_push();
    canvas_clear(&g_top, 0);
    ui_backdrop(&g_top);
    ui_panel(&g_top, 16, 66, 224, 60, false);
    ui_text_in(&g_top, &font_main, 16, 72, 224, 24, title, C_BLUE, C_SHADOW, 0);
    ui_text_in(&g_top, &font_small, 16, 98, 224, 18, "↑↓ / stylet : défiler    B : retour", C_BTN_SH, 0, 0);
    int drag_y = -1;
    while (1) {
        if (redraw) {
            canvas_clear(&g_bot, C_WHITE);
            canvas_rect(&g_bot, 0, 0, 256, 2, C_GOLD);
            canvas_rect(&g_bot, 0, 190, 256, 2, C_GOLD);
            for (int i = 0; i < per && top + i < n; i++) {
                int li = top + i;
                canvas_text_n(&g_bot, &font_small, 10, 4 + i * 13, lstart[li], llen[li],
                              lkind[li] ? C_BLUE : C_TEXT, lkind[li] ? C_SHADOW : 0);
            }
            ui_scrollbar(&g_bot, 243, 4, 184, n, per, top);
            redraw = false;
        }
        frame_wait();
        int old = top;
        if (g_krep & KEY_DOWN) top++;
        if (g_krep & KEY_UP) top--;
        if (g_krep & KEY_RIGHT) top += per;
        if (g_krep & KEY_LEFT) top -= per;
        int f = ui_scrollbar_drag(243, 4, 184, n, per);
        if (f >= 0) {
            top = f;
            drag_y = -1;
        } else if (g_touch_held) {
            if (drag_y >= 0) {
                int d = (drag_y - g_touch_y) / 6;
                if (d) {
                    top += d;
                    drag_y = g_touch_y;
                }
            } else
                drag_y = g_touch_y;
        } else
            drag_y = -1;
        top = CLAMP(top, 0, MAX(0, n - per));
        if (top != old)
            redraw = true;
        if (g_kdown & (KEY_B | KEY_START | KEY_A)) {
            sfx_play(SFX_CANCEL);
            break;
        }
    }
    free(txt);
    canvas_clear(&g_top, 0);
    ui_bottom_pop();
}

void scene_credits(void)
{
    static const char *const opts[3] = {"Crédits", "Sources des faits", "Retour"};
    while (1) {
        int c = dlg_choice(opts, 3, true);
        if (c == 0)
            viewer("text/credits.txt", "Crédits");
        else if (c == 1)
            viewer("text/sources.txt", "Sources des faits");
        else
            break;
    }
}

void viewer_open(const char *path, const char *title) { viewer(path, title); }
