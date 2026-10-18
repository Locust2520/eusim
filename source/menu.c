// Bottom-screen overworld panel and the menus it opens: party, bag, Eurodex, map, save, options.
#include "menu.h"
#include "multiplayer.h"
#include "lang.h"
#include "canvas.h"
#include "gfx.h"
#include "image.h"
#include "input.h"
#include "audio.h"
#include "dialog.h"
#include "ui.h"
#include "save.h"
#include "mon.h"
#include "map.h"
#include "scenes.h"
#include "creature_gfx.h"
#include "world.h"
#include "actor.h"
#include "gen/font_data.h"

static int panel_sel = -1;    // keyboard cursor on panel (-1 = none)
static const char *const panel_labels[6] = {"Équipe", "Sac", "Eurodex", "Carte", "Rapport", "Options"};

#define BTN_X(i) (6 + ((i) % 2) * 124)
#define BTN_Y(i) (47 + ((i) / 2) * 48)
#define BTN_W 118
#define BTN_H 40

static void money_str(char *buf, int n, u32 v)
{
    char tmp[16];
    snprintf(tmp, sizeof tmp, "%lu", (unsigned long)v);
    int l = strlen(tmp), o = 0;
    for (int i = 0; i < l && o < n - 4; i++) {
        buf[o++] = tmp[i];
        if ((l - i - 1) % 3 == 0 && i != l - 1)
            buf[o++] = ' ';
    }
    buf[o] = 0;
    strncat(buf, " €", n - strlen(buf) - 1);
}

static const int panel_icon[6] = {ICON_TEAM, ICON_BAG, ICON_DEX, ICON_MAP, ICON_SAVE, ICON_OPTIONS};

void menu_draw_panel(void)
{
    ui_backdrop(&g_bot);
    ui_panel(&g_bot, 4, 3, 246, 37, true);
    ui_text_in(&g_bot, &font_main, 10, 4, 120, 18, g_save.player_name, C_WHITE, C_INK, -1);
    char buf[32];
    money_str(buf, sizeof buf, g_save.money);
    ui_text_in(&g_bot, &font_main, 120, 4, 128, 18, buf, C_GOLD, C_INK, 1);
    for (int b = 0; b < 8; b++) {
        bool has = g_save.badges & (1 << b);
        canvas_text(&g_bot, &font_small, 14 + b * 11, 22, "★", has ? C_GOLD : C_NAVY2, has ? C_GOLD_D : 0);
    }
    u32 secs = g_save.play_frames / 60;
    snprintf(buf, sizeof buf, "%lu h %02lu", (unsigned long)(secs / 3600), (unsigned long)((secs / 60) % 60));
    ui_text_in(&g_bot, &font_small, 120, 21, 128, 16, buf, C_BTN_LO, C_INK, 1);
    for (int i = 0; i < 6; i++)
        ui_button_icon(&g_bot, BTN_X(i), BTN_Y(i), BTN_W, BTN_H, panel_labels[i], i == panel_sel ? BTN_SELECTED : BTN_NORMAL,
                       panel_icon[i]);
}

int menu_panel_input(void)
{
    for (int i = 0; i < 6; i++)
        if (touch_in(BTN_X(i), BTN_Y(i), BTN_W, BTN_H)) {
            sfx_play(SFX_SELECT);
            panel_sel = i;
            menu_draw_panel();
            frame_wait();
            panel_sel = -1;
            return i;
        }
    if (g_kdown & (KEY_X | KEY_START)) {
        sfx_play(SFX_SELECT);
        panel_sel = 0;
        menu_draw_panel();
        while (1) {
            frame_wait();
            int old = panel_sel;
            if (g_krep & KEY_RIGHT) panel_sel ^= 1;
            if (g_krep & KEY_LEFT) panel_sel ^= 1;
            if (g_krep & KEY_DOWN) panel_sel = (panel_sel + 2) % 6;
            if (g_krep & KEY_UP) panel_sel = (panel_sel + 4) % 6;
            if (old != panel_sel) {
                sfx_play(SFX_CURSOR);
                menu_draw_panel();
            }
            if (g_kdown & KEY_A) {
                int r = panel_sel;
                sfx_play(SFX_SELECT);
                panel_sel = -1;
                menu_draw_panel();
                return r;
            }
            for (int i = 0; i < 6; i++)
                if (touch_in(BTN_X(i), BTN_Y(i), BTN_W, BTN_H)) {
                    panel_sel = -1;
                    return i;
                }
            if (g_kdown & (KEY_B | KEY_X | KEY_START)) {
                sfx_play(SFX_CANCEL);
                panel_sel = -1;
                menu_draw_panel();
                return -1;
            }
        }
    }
    return -1;
}

// ---------------------------------------------------------------- shared widgets
void draw_hp_bar(Canvas *c, int x, int y, int w, int hp, int max)
{
    int pct = max ? hp * 100 / max : 0;
    u8 col = pct > 50 ? C_GREEN : pct > 20 ? C_YELLOW : C_RED;
    canvas_text(c, &font_small, x, y - 2, "PV", C_GOLD_D, 0);
    canvas_bar(c, x + 16, y, w - 16, 6, hp, max, col);
}

static const char *const status_short[6] = {"", "LOB", "SCA", "GEL", "SOM", "BLO"};
static const u8 status_col[6] = {0, C_TYPE0 + 13, C_RED, C_YELLOW, C_MGREY, C_BLUE_L};

void draw_type_badge(Canvas *c, int x, int y, int type)
{
    canvas_rect(c, x + 1, y, 44, 13, C_INK);
    canvas_rect(c, x, y + 1, 46, 11, C_INK);
    canvas_rect(c, x + 1, y + 1, 44, 11, C_TYPE0 + type);
    canvas_hline(c, x + 2, y + 1, 42, C_WHITE);
    ui_text_in(c, &font_small, x, y + 1, 46, 12, type_names[type], C_WHITE, C_INK, 0);
}

// Dual types share the ribbon; single types use its full height.
void draw_type_ribbon(Canvas *c, int x, int y, int w, int h, int type1, int type2)
{
    int first_h = type1 == type2 ? h : (h + 1) / 2;
    canvas_rect(c, x, y, w, first_h, C_TYPE0 + type1);
    if (first_h < h)
        canvas_rect(c, x, y + first_h, w, h - first_h, C_TYPE0 + type2);
}

static void draw_mon_row(int i, int y, bool sel, bool move_src)
{
    Mon *m = &g_save.party[i];
    canvas_frame(&g_bot, 4, y, 248, 29, sel ? FRAME_SELECT : (move_src ? FRAME_DARK : FRAME_MENU));
    draw_type_ribbon(&g_bot, 7, y + 3, 2, 23, species[m->species].type1, species[m->species].type2);
    creature_icon_draw(&g_bot, m->species, 10, y + 2);
    char buf[32];
    canvas_text(&g_bot, &font_main, 42, y + 1, mon_name(m), move_src ? C_WHITE : C_TEXT, move_src ? C_INK : C_SHADOW);
    snprintf(buf, sizeof buf, T("N.%d"), m->level);
    canvas_text_right(&g_bot, &font_small, 150, y + 3, buf, move_src ? C_GOLD : C_BTN_SH, 0);
    int mx = mon_max_hp(m);
    draw_hp_bar(&g_bot, 156, y + 6, 88, m->hp, mx);
    snprintf(buf, sizeof buf, "%d/%d", m->hp, mx);
    canvas_text_right(&g_bot, &font_small, 244, y + 13, buf, move_src ? C_WHITE : C_TEXT, 0);
    if (m->status) {
        canvas_rect(&g_bot, 122, y + 14, 28, 11, status_col[m->status]);
        ui_text_in(&g_bot, &font_small, 122, y + 14, 28, 11, status_short[m->status], C_WHITE, C_INK, 0);
    } else if (m->hp == 0) {
        canvas_rect(&g_bot, 122, y + 14, 28, 11, C_RED_D);
        ui_text_in(&g_bot, &font_small, 122, y + 14, 28, 11, "K.O.", C_WHITE, C_INK, 0);
    }
}

void mon_summary(Mon *m)
{
    ui_bottom_push();
    ui_backdrop(&g_bot);
    canvas_frame(&g_bot, 4, 2, 248, 64, FRAME_MENU);
    creature_big_draw(&g_bot, m->species, 8, 4);
    char buf[64];
    canvas_text(&g_bot, &font_main, 80, 4, mon_name(m), C_TEXT, C_SHADOW);
    snprintf(buf, sizeof buf, T("N.%d   n°%03d"), m->level, species[m->species].num);
    canvas_text(&g_bot, &font_small, 80, 23, buf, C_BTN_SH, 0);
    draw_type_badge(&g_bot, 80, 42, species[m->species].type1);
    if (species[m->species].type2 != species[m->species].type1)
        draw_type_badge(&g_bot, 128, 42, species[m->species].type2);
    static const char *const sn[6] = {"PV", "Argumentation", "Résilience", "Expertise", "Diplomatie", "Réactivité"};
    for (int s = 0; s < 6; s++) {
        int v = s == 0 ? mon_max_hp(m) : mon_stat(m, s);
        if (s == 0)
            canvas_frame(&g_bot, 4, 68, 120, 106, FRAME_DIALOG);
        canvas_text(&g_bot, &font_small, 12, 71 + s * 12, sn[s], C_TEXT, 0);
        if (s == 0)
            snprintf(buf, sizeof buf, "%d/%d", m->hp, v);
        else
            snprintf(buf, sizeof buf, "%d", v);
        canvas_text_right(&g_bot, &font_small, 116, 71 + s * 12, buf, C_BLUE, 0);
    }
    u32 next = exp_for_level(species[m->species].growth, m->level + 1);
    canvas_hline(&g_bot, 10, 143, 106, C_BTN_MID);
    canvas_text(&g_bot, &font_small, 12, 144, "Exp.", C_TEXT, 0);
    snprintf(buf, sizeof buf, "%lu", (unsigned long)m->exp);
    canvas_text_right(&g_bot, &font_small, 116, 144, buf, C_BLUE, 0);
    canvas_text(&g_bot, &font_small, 12, 156, "Suivant", C_TEXT, 0);
    snprintf(buf, sizeof buf, "%lu", (unsigned long)(m->level >= 100 ? 0 : next - m->exp));
    canvas_text_right(&g_bot, &font_small, 116, 156, buf, C_BLUE, 0);
    for (int k = 0; k < 4; k++) {
        int y = 68 + k * 26;
        canvas_frame(&g_bot, 126, y, 126, 25, FRAME_MENU);
        if (m->moves[k] == 0xFFFF) {
            ui_text_in(&g_bot, &font_small, 126, y, 126, 24, "—", C_MGREY, 0, 0);
            continue;
        }
        const MoveData *mv = &moves[m->moves[k]];
        canvas_rect(&g_bot, 130, y + 4, 4, 16, C_TYPE0 + mv->type);
        snprintf(buf, sizeof buf, "%d/%d", m->pp[k], mv->pp);
        ui_text_in(&g_bot, &font_small, 134, y, 246 - font_width(&font_small, buf) - 4 - 134, 24, mv->name, C_TEXT, 0, -1);
        ui_text_in(&g_bot, &font_small, 196, y, 54, 24, buf, m->pp[k] ? C_BTN_SH : C_RED, 0, 1);
    }
    ui_text_in(&g_bot, &font_small, 126, 174, 126, 16, "B : retour", C_BTN_LO, C_INK, 0);
    frame_wait();
    while (!(g_kdown & (KEY_B | KEY_A)) && !g_touch_down)
        frame_wait();
    sfx_play(SFX_CANCEL);
    ui_bottom_pop();
}

// Insert at the selected slot, preserving the order of the other members.
static void party_move(int from, int to)
{
    Mon moved = g_save.party[from];
    while (from < to) {
        g_save.party[from] = g_save.party[from + 1];
        from++;
    }
    while (from > to) {
        g_save.party[from] = g_save.party[from - 1];
        from--;
    }
    g_save.party[to] = moved;
}

// returns selected party index or -1. mode: 0 = browse (summary/reorder), 1 = pick one
int g_party_menu_default = -1;

int party_menu(int mode, const char *prompt)
{
    ui_bottom_push();
    int sel = 0, move_src = -1;
    if (g_party_menu_default >= 0 && g_party_menu_default < g_save.party_count)
        sel = g_party_menu_default;
    g_party_menu_default = -1;
    bool redraw = true;
    int result = -1;
    while (1) {
        if (redraw) {
            ui_backdrop(&g_bot);
            for (int i = 0; i < g_save.party_count; i++)
                draw_mon_row(i, 1 + i * 30, i == sel, i == move_src);
            ui_text_in(&g_bot, &font_small, 0, 180, 256, 12, prompt ? prompt : (move_src >= 0 ? "Déplacer" : "A : choisir   B : retour"), C_GOLD, C_INK, 0);
            redraw = false;
        }
        frame_wait();
        if (g_save.party_count == 0) {
            if (g_kdown & (KEY_B | KEY_A) || g_touch_down)
                break;
            continue;
        }
        int old = sel;
        if (g_krep & KEY_DOWN) sel = (sel + 1) % g_save.party_count;
        if (g_krep & KEY_UP) sel = (sel + g_save.party_count - 1) % g_save.party_count;
        if (old != sel) {
            sfx_play(SFX_CURSOR);
            redraw = true;
        }
        int pick = -1;
        if (g_kdown & KEY_A)
            pick = sel;
        for (int i = 0; i < g_save.party_count; i++)
            if (touch_in(4, 2 + i * 30, 248, 28))
                pick = sel = i;
        if (pick >= 0) {
            sfx_play(SFX_SELECT);
            if (mode == 1) {
                result = pick;
                break;
            }
            if (move_src >= 0) {
                party_move(move_src, pick);
                move_src = -1;
                redraw = true;
                continue;
            }
            static const char *const opts[3] = {"Résumé", "Déplacer", "Retour"};
            int c = dlg_choice(opts, 3, true);
            if (c == 0)
                mon_summary(&g_save.party[pick]);
            else if (c == 1)
                move_src = pick;
            redraw = true;
        }
        if (g_kdown & KEY_B) {
            sfx_play(SFX_CANCEL);
            if (move_src >= 0) {
                move_src = -1;
                redraw = true;
                continue;
            }
            break;
        }
    }
    ui_bottom_pop();
    return result;
}

// ---------------------------------------------------------------- bag
static const char *const pockets[4] = {"Soins", "Tampons", "Combat", "Clés"};

static int pocket_of(int kind)
{
    switch (kind) {
    case IK_BALL: return 1;
    case IK_BATTLE: case IK_EVO: case IK_REPEL: case IK_MISC: return 2;
    case IK_KEY: return 3;
    default: return 0;
    }
}

static bool use_item_field(int it)
{
    const ItemData *d = &items[it];
    if (d->kind == IK_REPEL) {
        g_save.repel = d->param;
        bag_take(it, 1);
        dlg_say("", "Les Euromons sauvages vous laisseront tranquille un moment.");
        dlg_close();
        return true;
    }
    if (d->kind == IK_HEAL || d->kind == IK_STATUS || d->kind == IK_REVIVE || d->kind == IK_PP || d->kind == IK_EVO) {
        int i = party_menu(1, "Sur quel Euromon ?");
        if (i < 0)
            return false;
        Mon *m = &g_save.party[i];
        int mx = mon_max_hp(m);
        bool ok = false;
        char buf[96];
        if (d->kind == IK_HEAL && m->hp > 0 && m->hp < mx) {
            int h = d->param >= 999 ? mx : d->param;
            m->hp = MIN(mx, m->hp + h);
            snprintf(buf, sizeof buf, T("%s récupère des PV."), mon_name(m));
            ok = true;
        } else if (d->kind == IK_STATUS && m->status && m->hp > 0) {
            m->status = 0;
            snprintf(buf, sizeof buf, T("%s va mieux."), mon_name(m));
            ok = true;
        } else if (d->kind == IK_REVIVE && m->hp == 0) {
            m->hp = d->param >= 999 ? mx : mx / 2;
            snprintf(buf, sizeof buf, T("%s reprend du service !"), mon_name(m));
            ok = true;
        } else if (d->kind == IK_PP) {
            for (int k = 0; k < 4; k++)
                if (m->moves[k] != 0xFFFF)
                    m->pp[k] = moves[m->moves[k]].pp;
            snprintf(buf, sizeof buf, T("Les PP de %s sont restaurés."), mon_name(m));
            ok = true;
        } else if (d->kind == IK_EVO) {
            const SpeciesData *s = &species[m->species];
            if (s->evo_item == it) {
                bag_take(it, 1);
                evolve_mon(m, s->evo_into);
                return true;
            }
            snprintf(buf, sizeof buf, T("Ça n'a aucun effet."));
        } else
            snprintf(buf, sizeof buf, T("Ça n'aura aucun effet."));
        if (ok) {
            bag_take(it, 1);
            sfx_play(SFX_HEAL);
        }
        dlg_say("", buf);
        dlg_close();
        return ok;
    }
    dlg_say("", d->kind == IK_KEY ? d->desc : "Ce n'est pas le moment d'utiliser ça.");
    dlg_close();
    return false;
}

// mode 0 = field, 1 = battle (returns item id chosen, -1 cancel)
int bag_menu(int mode)
{
    ui_bottom_push();
    int pocket = 0, sel = 0, scroll = 0;
    bool redraw = true;
    int result = -1;
    int list[NUM_ITEMS];
    while (1) {
        int n = 0;
        for (int i = 0; i < NUM_ITEMS_DEF && i < NUM_ITEMS; i++)
            if (g_save.bag[i] && pocket_of(items[i].kind) == pocket)
                list[n++] = i;
        if (sel >= n)
            sel = MAX(0, n - 1);
        if (sel < scroll)
            scroll = sel;
        if (sel >= scroll + 6)
            scroll = sel - 5;
        if (redraw) {
            ui_backdrop(&g_bot);
            for (int p = 0; p < 4; p++) {
                canvas_frame(&g_bot, 2 + p * 63, 2, 62, 23, p == pocket ? FRAME_SELECT : FRAME_MENU);
                ui_text_in(&g_bot, &font_small, 2 + p * 63, 2, 61, 22, pockets[p], C_TEXT, 0, 0);
            }
            for (int k = 0; k < 6 && scroll + k < n; k++) {
                int it = list[scroll + k];
                int y = 28 + k * 20;
                canvas_frame(&g_bot, 4, y, 236, 19, scroll + k == sel ? FRAME_SELECT : FRAME_MENU);
                ui_text_in(&g_bot, &font_small, 8, y, 190, 19, items[it].name, C_TEXT, 0, -1);
                char buf[8];
                snprintf(buf, sizeof buf, "×%d", g_save.bag[it]);
                if (items[it].kind != IK_KEY)
                    ui_text_in(&g_bot, &font_small, 150, y, 86, 19, buf, C_BLUE, 0, 1);
            }
            if (n > 6)
                ui_scrollbar(&g_bot, 243, 28, 119, n, 6, scroll);
            if (n == 0)
                ui_text_in(&g_bot, &font_main, 0, 60, 256, 60, "(vide)", C_BTN_LO, C_INK, 0);
            canvas_frame(&g_bot, 4, 150, 248, 40, FRAME_DIALOG);
            if (n > 0) {
                // wrap description
                const char *s = items[list[sel]].desc;
                char line[64];
                int y = 153;
                while (*s && y < 182) {
                    int k = 0, sp = -1;
                    while (s[k] && font_width_n(&font_small, s, k + 1) < 232) {
                        if (s[k] == ' ')
                            sp = k;
                        k++;
                    }
                    if (s[k] && sp > 0)
                        k = sp;
                    memcpy(line, s, k);
                    line[k] = 0;
                    canvas_text(&g_bot, &font_small, 12, y, line, C_TEXT, 0);
                    s += k;
                    while (*s == ' ')
                        s++;
                    y += 12;
                }
            }
            redraw = false;
        }
        frame_wait();
        {
            int f = ui_scrollbar_drag(243, 28, 119, n, 6);
            if (f >= 0 && f != scroll) {
                scroll = f;
                sel = CLAMP(sel, scroll, scroll + 5);
                redraw = true;
            }
        }
        int op = pocket, os = sel;
        if (g_krep & KEY_RIGHT) { pocket = (pocket + 1) % 4; sel = scroll = 0; }
        if (g_krep & KEY_LEFT) { pocket = (pocket + 3) % 4; sel = scroll = 0; }
        if (g_krep & KEY_DOWN && n) sel = (sel + 1) % n;
        if (g_krep & KEY_UP && n) sel = (sel + n - 1) % n;
        for (int p = 0; p < 4; p++)
            if (touch_in(2 + p * 63, 2, 61, 22)) { pocket = p; sel = scroll = 0; }
        int pick = -1;
        for (int k = 0; k < 6 && scroll + k < n; k++)
            if (touch_in(4, 28 + k * 20, 236, 19)) {
                if (sel == scroll + k)
                    pick = sel;
                sel = scroll + k;
            }
        if ((g_kdown & KEY_A) && n)
            pick = sel;
        if (op != pocket || os != sel) {
            sfx_play(SFX_CURSOR);
            redraw = true;
        }
        if (pick >= 0) {
            sfx_play(SFX_SELECT);
            if (mode == 1) {
                result = list[pick];
                break;
            }
            static const char *const opts[2] = {"Utiliser", "Retour"};
            if (dlg_choice(opts, 2, true) == 0)
                use_item_field(list[pick]);
            redraw = true;
        }
        if (g_kdown & KEY_B) {
            sfx_play(SFX_CANCEL);
            break;
        }
    }
    ui_bottom_pop();
    return result;
}

// ---------------------------------------------------------------- Eurodex
static void dex_entry(int sp)
{
    ui_bottom_push();
    ui_backdrop(&g_bot);
    const SpeciesData *s = &species[sp];
    bool caught = dex_is_caught(sp);
    canvas_frame(&g_bot, 4, 4, 248, 100, FRAME_MENU);
    creature_big_draw(&g_bot, sp, 10, 10);
    char buf[64];
    snprintf(buf, sizeof buf, "n°%03d  %s", s->num, s->name);
    canvas_text(&g_bot, &font_main, 84, 8, buf, C_TEXT, C_SHADOW);
    canvas_text(&g_bot, &font_small, 84, 28, caught ? s->category : "???", C_BTN_SH, 0);
    if (caught) {
        draw_type_badge(&g_bot, 84, 48, s->type1);
        if (s->type2 != s->type1)
            draw_type_badge(&g_bot, 132, 48, s->type2);
    }
    canvas_frame(&g_bot, 4, 108, 248, 80, FRAME_DIALOG);
    const char *t = caught ? s->dex : "Capturez cet Euromon pour lire sa fiche.";
    char line[80];
    int y = 116;
    while (*t && y < 180) {
        int k = 0, spc = -1;
        while (t[k] && font_width_n(&font_small, t, k + 1) < 228) {
            if (t[k] == ' ')
                spc = k;
            k++;
        }
        if (t[k] && spc > 0)
            k = spc;
        memcpy(line, t, k);
        line[k] = 0;
        canvas_text(&g_bot, &font_small, 14, y, line, C_TEXT, 0);
        t += k;
        while (*t == ' ')
            t++;
        y += 13;
    }
    if (caught)
        sfx_cry(sp);
    frame_wait();
    while (!(g_kdown & (KEY_A | KEY_B)) && !g_touch_down)
        frame_wait();
    sfx_play(SFX_CANCEL);
    ui_bottom_pop();
}

void dex_menu(void)
{
    ui_bottom_push();
    int sel = 0, scroll = 0;
    bool redraw = true;
    while (1) {
        if (sel < scroll) scroll = sel;
        if (sel >= scroll + 8) scroll = sel - 7;
        if (redraw) {
            ui_backdrop(&g_bot);
            char buf[48];
            snprintf(buf, sizeof buf, T("EURODEX   Vus : %d   Capturés : %d"), dex_count_seen(), dex_count_caught());
            canvas_frame(&g_bot, 4, 2, 248, 21, FRAME_DARK);
            ui_text_in(&g_bot, &font_small, 4, 2, 247, 20, buf, C_GOLD, C_INK, 0);
            for (int k = 0; k < 8 && scroll + k < NUM_SPECIES; k++) {
                int sp = scroll + k;
                int y = 24 + k * 21;
                canvas_frame(&g_bot, 4, y, 236, 20, sp == sel ? FRAME_SELECT : FRAME_MENU);
                snprintf(buf, sizeof buf, "%03d", species[sp].num);
                ui_text_in(&g_bot, &font_small, 8, y, 40, 19, buf, C_BTN_SH, 0, -1);
                if (dex_is_caught(sp))
                    ui_text_in(&g_bot, &font_small, 32, y, 20, 19, "★", C_GOLD_D, 0, -1);
                ui_text_in(&g_bot, &font_main, 48, y, 186, 19, dex_is_seen(sp) ? species[sp].name : "- - - - -",
                           C_TEXT, 0, -1);
            }
            ui_scrollbar(&g_bot, 243, 24, 167, NUM_SPECIES, 8, scroll);
            redraw = false;
        }
        frame_wait();
        {
            int f = ui_scrollbar_drag(243, 24, 167, NUM_SPECIES, 8);
            if (f >= 0 && f != scroll) {
                scroll = f;
                sel = CLAMP(sel, scroll, scroll + 7);
                redraw = true;
            }
        }
        int old = sel;
        if (g_krep & KEY_DOWN) sel = MIN(NUM_SPECIES - 1, sel + 1);
        if (g_krep & KEY_UP) sel = MAX(0, sel - 1);
        if (g_krep & KEY_RIGHT) sel = MIN(NUM_SPECIES - 1, sel + 8);
        if (g_krep & KEY_LEFT) sel = MAX(0, sel - 8);
        int pick = -1;
        for (int k = 0; k < 8; k++)
            if (touch_in(4, 24 + k * 21, 236, 20) && scroll + k < NUM_SPECIES) {
                if (sel == scroll + k)
                    pick = sel;
                sel = scroll + k;
            }
        if (g_kdown & KEY_A)
            pick = sel;
        if (old != sel) {
            sfx_play(SFX_CURSOR);
            redraw = true;
        }
        if (pick >= 0 && dex_is_seen(pick)) {
            sfx_play(SFX_SELECT);
            dex_entry(pick);
            redraw = true;
        }
        if (g_kdown & KEY_B) {
            sfx_play(SFX_CANCEL);
            break;
        }
    }
    ui_bottom_pop();
}

// ---------------------------------------------------------------- map / save / options
void map_menu(void)
{
    ui_bottom_push();
    canvas_clear(&g_bot, 0);
    bgi_load(true, 2, "ui/europe.bgi", 1);
    europe_map_markers();
    canvas_frame(&g_bot, 4, 2, 248, 23, FRAME_DARK);
    ui_text_in(&g_bot, &font_main, 4, 2, 247, 22, g_map.name, C_GOLD, C_INK, 0);
    frame_wait();
    while (!(g_kdown & (KEY_A | KEY_B)) && !g_touch_down)
        frame_wait();
    sfx_play(SFX_CANCEL);
    canvas_clear(&g_bot, 0);
    ui_bottom_pop();
    bgi_load(true, 2, "ui/pattern.bgi", 1);
}

void menu_save(void)
{
    if (!save_available()) {
        dlg_say("", "Aucun support de sauvegarde détecté.\fSur DS (DS Pico, R4…), lancez le jeu depuis la carte SD. Sur émulateur, activez le DLDI / la carte SD, ou utilisez les sauvegardes d'état.");
        dlg_close();
        return;
    }
    char q[96];
    snprintf(q, sizeof q, T("Rédiger un rapport de progression (emplacement %d) ?"), g_save_slot + 1);
    static const char *const opts[3] = {"Sauvegarder", "Autre emplacement…", "Annuler"};
    dlg_say_nowait("", q);
    int c = dlg_choice(opts, 3, true);
    if (c == 1) {
        dlg_close();
        int s = slot_picker(2);
        if (s < 0)
            return;
        g_save_slot = s;
    } else if (c != 0) {
        dlg_close();
        return;
    }
    g_save.dir = g_actors[PLAYER].dir;
    g_save.x = g_actors[PLAYER].tx;
    g_save.y = g_actors[PLAYER].ty;
    bool ok = save_write();
    char buf[96];
    if (ok) {
        sfx_play(SFX_SAVE);
        snprintf(buf, sizeof buf, T("Rapport transmis en 24 langues. Partie sauvegardée (emplacement %d) !"), g_save_slot + 1);
    } else {
        sfx_play(SFX_ERROR);
        snprintf(buf, sizeof buf, T("Échec de la sauvegarde. Réessayez."));
    }
    dlg_say("", buf);
    dlg_close();
}

void menu_open(int id)
{
    switch (id) {
    case 0: party_menu(0, NULL); break;
    case 1: bag_menu(0); break;
    case 2: dex_menu(); break;
    case 3: map_menu(); break;
    case 4: menu_save(); break;
    case 5: {
        static const char *const opts[4] = {"Réglages", "Débat multijoueur", "Sources des faits", "Retour au titre"};
        int c = dlg_choice(opts, 4, true);
        if (c == 0)
            scene_options(true);
        else if (c == 1)
            multiplayer_open();
        else if (c == 2)
            viewer_open("text/sources.txt", "Sources des faits");
        else if (c == 3) {
            dlg_say("", "Retourner à l'écran titre ? Ce qui n'est pas sauvegardé sera perdu.");
            if (dlg_yesno())
                world_special(16, 0);
            dlg_close();
        }
        break;
    }
    }
    menu_draw_panel();
}
