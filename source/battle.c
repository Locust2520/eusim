// Battle engine: Gen-4-like turn-based battles, top screen scene, bottom screen touch menu.
#include "battle.h"
#include "multiplayer.h"
#include <stddef.h>
#include "lang.h"
#include <stdarg.h>
#include "battle_fx.h"
#include "mon.h"
#include "gfx.h"
#include "canvas.h"
#include "image.h"
#include "input.h"
#include "audio.h"
#include "dialog.h"
#include "ui.h"
#include "portrait.h"
#include "sprite.h"
#include "creature_gfx.h"
#include "menu.h"
#include "save.h"
#include "world.h"
#include "gen/font_data.h"

// ---------------------------------------------------------------- state
typedef struct {
    Mon *mon;            // points into party (player) or foe array
    s8 stage[8];         // atk def spa spd spe acc eva (index STAT_*)
    u8 confuse, flinch, protect, protect_chain, charge_move_slot, trap, recharge;
    s16 charge_move;
    u8 last_move_ok;
    s16 last_move;
    u8 steal_turn_used, first_turn;
    s16 delayed_move;    // Poutine long table: queued player move
    u8 delayed_turns;
    s8 type_override;    // Xi: changing type (-1 none)
} Side;

// Combat randomness is independent of animation timing and frame_wait() in link battles.
static bool is_link;
static u32 link_rng;
static int battle_random(int n)
{
    if (!is_link) return rng_range(n);
    if (n <= 1) return 0;
    u32 x = link_rng;
    x ^= x << 13; x ^= x >> 17; x ^= x << 5;
    link_rng = x;
    return (int)((x >> 8) % (u32)n);
}

static Side side[2];          // 0 = player, 1 = foe
static Mon foe_party[6];
static int foe_count, foe_idx, player_idx;
static bool is_trainer, is_wild;
static int trainer_id;
static int gimmick;           // GIM_*
static bool participants[6];
static int run_attempts;
static int result;
static int money_bonus;
static bool exp_share;

enum { GIM_NONE, GIM_VETO, GIM_TAUX, GIM_LONGTABLE, GIM_RIVAL_SYS, GIM_TRUMP, GIM_SMS, GIM_COFFEE };

static SpriteSheet sh_foe, sh_ally;
static u16 *gfx_foe, *gfx_ally;
static int foe_x, foe_y, ally_x, ally_y;
static bool foe_visible, ally_visible;
static int foe_flash, ally_flash, foe_shake, ally_shake;

#define FOE_HOME_X 156
#define FOE_HOME_Y 18
#define ALLY_HOME_X 28
#define ALLY_HOME_Y 70

// ---------------------------------------------------------------- helpers
static const char *pname(int s)
{
    return species[side[s].mon->species].name;
}

static void msg(const char *fmt, ...) __attribute__((format(printf, 1, 2)));
static void msg(const char *fmt, ...)
{
    char buf[200];
    va_list ap;
    va_start(ap, fmt);
    // translate the format (the Trump shout marker stays outside the translated text)
    bool shout = !strncmp(fmt, "(trump)", 7);
    char f2[160];
    snprintf(f2, sizeof f2, "%s%s", shout ? "(trump)" : "", tr(shout ? fmt + 7 : fmt));
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wformat-nonliteral"
    vsnprintf(buf, sizeof buf, f2, ap);
#pragma GCC diagnostic pop
    va_end(ap);
    if (gimmick == GIM_TRUMP && strstr(buf, "(trump)")) {
        char *p = strstr(buf, "(trump)");
        memmove(p, p + 7, strlen(p + 7) + 1);
        for (char *q = buf; *q; q++)
            if (*q >= 'a' && *q <= 'z')
                *q -= 32;
    }
    dlg_say("", buf);
}

static int type1(int s)
{
    if (side[s].type_override >= 0)
        return side[s].type_override;
    return species[side[s].mon->species].type1;
}

static int type2(int s)
{
    if (side[s].type_override >= 0)
        return side[s].type_override;
    return species[side[s].mon->species].type2;
}

static int stage_mult(int stat, int st, int base)
{
    // returns base * multiplier
    if (stat == STAT_ACC || stat == STAT_EVA) {
        static const int num[13] = {3, 3, 3, 3, 3, 3, 3, 4, 5, 6, 7, 8, 9};
        static const int den[13] = {9, 8, 7, 6, 5, 4, 3, 3, 3, 3, 3, 3, 3};
        return base * num[st + 6] / den[st + 6];
    }
    if (st >= 0)
        return base * (2 + st) / 2;
    return base * 2 / (2 - st);
}

static int eff_stat(int s, int stat)
{
    Mon *m = side[s].mon;
    int v = mon_stat(m, stat);
    v = stage_mult(stat, side[s].stage[stat], v);
    if (stat == STAT_SPE && m->status == STATUS_GEL)
        v /= 4;
    if (stat == STAT_ATK && m->status == STATUS_SCANDALE)
        v /= 2;
    return MAX(1, v);
}

static int type_eff(int mtype, int s) // returns x4 (0,1,2,4,8,16)
{
    int a = type_chart[mtype][type1(s)];
    int b = type1(s) == type2(s) ? 2 : type_chart[mtype][type2(s)];
    return a * b; // 4 = neutral
}

// ---------------------------------------------------------------- drawing
static const char *const st_short[6] = {"", "LOB", "SCA", "GEL", "SOM", "BLO"};
static const u8 st_col[6] = {0, C_TYPE0 + 13, C_RED, C_BLUE_L, C_MGREY, C_TYPE0 + 7};

static void status_tag(int x, int y, int status)
{
    canvas_rect(&g_top, x, y, 24, 11, C_INK);
    canvas_rect(&g_top, x + 1, y + 1, 22, 9, st_col[status]);
    ui_text_in(&g_top, &font_small, x, y, 24, 11, st_short[status], C_WHITE, C_INK, 0);
}

static void draw_infobox(int s)
{
    Mon *m = side[s].mon;
    char buf[32];
    int mx = mon_max_hp(m);
    if (s == 1) {
        canvas_rect(&g_top, 0, 2, 140, 40, 0);
        if (!foe_visible)
            return;
        canvas_frame(&g_top, 4, 4, 132, 36, FRAME_MENU);
        draw_type_ribbon(&g_top, 6, 6, 3, 31, type1(s), type2(s));
        canvas_text(&g_top, &font_main, 13, 4, pname(1), C_TEXT, C_SHADOW);
        snprintf(buf, sizeof buf, T("N.%d"), m->level);
        canvas_text_right(&g_top, &font_small, 128, 7, buf, C_BTN_SH, 0);
        if (is_wild && dex_is_caught(m->species))
            canvas_text(&g_top, &font_small, 96, 7, "★", C_GOLD_D, 0);
        draw_hp_bar(&g_top, 34, 27, 94, m->hp, mx);
        if (m->status)
            status_tag(10, 24, m->status);
    } else {
        canvas_rect(&g_top, 116, 84, 140, 50, 0);
        if (!ally_visible)
            return;
        canvas_frame(&g_top, 120, 86, 132, 47, FRAME_MENU);
        draw_type_ribbon(&g_top, 246, 88, 3, 42, type1(s), type2(s));
        canvas_text(&g_top, &font_main, 126, 86, pname(0), C_TEXT, C_SHADOW);
        snprintf(buf, sizeof buf, T("N.%d"), m->level);
        canvas_text_right(&g_top, &font_small, 242, 89, buf, C_BTN_SH, 0);
        draw_hp_bar(&g_top, 148, 104, 94, m->hp, mx);
        snprintf(buf, sizeof buf, "%d/%d", m->hp, mx);
        canvas_text_right(&g_top, &font_small, 242, 108, buf, C_TEXT, 0);
        // exp bar
        u32 lo = exp_for_level(species[m->species].growth, m->level);
        u32 hi = exp_for_level(species[m->species].growth, m->level + 1);
        int pct = (m->level >= 100 || hi <= lo) ? 0 : (int)((m->exp - lo) * 100 / (hi - lo));
        canvas_text(&g_top, &font_small, 126, 114, "EXP", C_BLUE, 0);
        canvas_rect(&g_top, 148, 120, 94, 4, C_INK);
        canvas_rect(&g_top, 149, 121, 92, 2, C_LGREY);
        canvas_rect(&g_top, 149, 121, 92 * CLAMP(pct, 0, 100) / 100, 2, C_BLUE_L);
        if (m->status)
            status_tag(123, 102, m->status);
    }
}

static void place_sprites(void)
{
    int fs = foe_shake ? ((foe_shake & 2) ? 3 : -3) : 0;
    int as = ally_shake ? ((ally_shake & 2) ? 3 : -3) : 0;
    bool fh = !foe_visible || (foe_flash && (foe_flash & 4));
    bool ah = !ally_visible || (ally_flash && (ally_flash & 4));
    oamSet(&oamMain, OAM_BATTLE, foe_x + fs, foe_y, 1, PAL_BATTLE_FOE, SpriteSize_64x64, SpriteColorFormat_256Color,
           gfx_foe, -1, false, fh, false, false, false);
    oamSet(&oamMain, OAM_BATTLE + 1, ally_x + as, ally_y, 1, PAL_BATTLE_ALLY, SpriteSize_64x64,
           SpriteColorFormat_256Color, gfx_ally, -1, false, ah, false, false, false);
    if (foe_shake) foe_shake--;
    if (ally_shake) ally_shake--;
    if (foe_flash) foe_flash--;
    if (ally_flash) ally_flash--;
}

static void bframe(void)
{
    place_sprites();
    fx_update();
    frame_wait();
}

static void bwait(int n)
{
    for (int i = 0; i < n; i++)
        bframe();
}

static void load_mon_gfx(int s)
{
    SpriteSheet *sh = s ? &sh_foe : &sh_ally;
    sheet_free(sh);
    int sp = side[s].mon->species;
    if (!creature_sheet_load(sh, sp, s == 0)) {
        dmaFillHalfWords(0, s ? gfx_foe : gfx_ally, 4096);
        return;
    }
    u16 pal[256];
    memcpy(pal, sh->pal, sizeof(u16) * sh->ncolors);
    if (side[s].mon->shiny) // shiny: rotate hue (swap channels)
        for (int i = 1; i < sh->ncolors; i++) {
            u16 c = pal[i];
            pal[i] = ((c >> 5) & 31) | (((c >> 10) & 31) << 5) | ((c & 31) << 10);
        }
    spr_ext_pal(false, s ? PAL_BATTLE_FOE : PAL_BATTLE_ALLY, pal, sh->ncolors);
    spr_upload(s ? gfx_foe : gfx_ally, sheet_frame(sh, 0), 4096);
}

// HP bar animation from old to new
static void animate_hp(int s, int from, int to)
{
    Mon *m = side[s].mon;
    int steps = MAX(8, MIN(40, abs(from - to)));
    for (int i = 1; i <= steps; i++) {
        m->hp = from + (to - from) * i / steps;
        draw_infobox(s);
        bframe();
    }
    m->hp = to;
    draw_infobox(s);
}

// ---------------------------------------------------------------- bottom screen menus
#define BM_Y 120
#define BM_W 74
#define BM_H 58
static const int bm_x[3] = {8, 91, 174};

static void draw_main_menu(int sel)
{
    ui_backdrop(&g_bot);
    // big DÉBATTRE button
    ui_button(&g_bot, 24, 12, 206, 94, NULL, sel == 0 ? BTN_SELECTED : BTN_RED, NULL);
    ui_icon(&g_bot, 24 + (206 - 36) / 2, 26, ICON_FIGHT, 3);
    ui_text_in(&g_bot, &font_main, 24, 66, 206, 26, "DÉBATTRE", sel == 0 ? C_INK : C_WHITE, sel == 0 ? C_GLD_HI : C_RED_D, 0);
    static const char *const lab[3] = {"SAC", "FUIR", "ÉQUIPE"};
    static const int ic[3] = {ICON_BAG, ICON_RUN, ICON_TEAM};
    for (int i = 0; i < 3; i++) {
        bool on = sel == i + 1;
        ui_button(&g_bot, bm_x[i], BM_Y, BM_W, BM_H, NULL, on ? BTN_SELECTED : BTN_NORMAL, NULL);
        ui_icon(&g_bot, bm_x[i] + (BM_W - 24) / 2, BM_Y + 7, ic[i], 2);
        ui_text_in(&g_bot, &font_main, bm_x[i], BM_Y + 32, BM_W, 20, lab[i], C_INK, on ? C_GLD_HI : C_BTN_HI, 0);
    }
}

static int main_menu(void)
{
    int sel = 0;
    draw_main_menu(sel);
    while (1) {
        bframe();
        if (is_link && !link_ok()) return -1;
        int old = sel;
        if (g_krep & KEY_UP) sel = 0;
        if (g_krep & KEY_DOWN && sel == 0) sel = 1;
        if (g_krep & KEY_LEFT && sel > 1) sel--;
        if (g_krep & KEY_RIGHT && sel >= 1 && sel < 3) sel++;
        if (old != sel) {
            sfx_play(SFX_CURSOR);
            draw_main_menu(sel);
        }
        if (g_kdown & KEY_A) {
            sfx_play(SFX_SELECT);
            return sel;
        }
        if (touch_in(24, 12, 206, 94)) {
            sfx_play(SFX_SELECT);
            return 0;
        }
        for (int i = 0; i < 3; i++)
            if (touch_in(bm_x[i], BM_Y, BM_W, BM_H)) {
                sfx_play(SFX_SELECT);
                return i + 1;
            }
        if (g_kdown & KEY_B && sel != 2) {
            sel = 2; // jump cursor to FUIR like DP
            draw_main_menu(sel);
        }
    }
}

static void draw_move_menu(int sel)
{
    ui_backdrop(&g_bot);
    Mon *m = side[0].mon;
    for (int k = 0; k < 4; k++) {
        int x = 4 + (k % 2) * 126, y = 8 + (k / 2) * 72;
        if (m->moves[k] == 0xFFFF) {
            canvas_frame(&g_bot, x, y, 122, 66, FRAME_MENU);
            ui_text_in(&g_bot, &font_main, x, y, 122, 66, "—", C_MGREY, 0, 0);
            continue;
        }
        const MoveData *mv = &moves[m->moves[k]];
        canvas_frame(&g_bot, x, y, 122, 66, k == sel ? FRAME_SELECT : FRAME_MENU);
        canvas_rect(&g_bot, x + 4, y + 4, 113, 5, C_TYPE0 + mv->type);
        canvas_hline(&g_bot, x + 4, y + 9, 113, C_INK);
        ui_text_in(&g_bot, &font_main, x, y + 10, 121, 22, mv->name, C_TEXT, C_SHADOW, 0);
        char buf[24];
        snprintf(buf, sizeof buf, T("PP %d/%d"), m->pp[k], mv->pp);
        canvas_text(&g_bot, &font_small, x + 9, y + 32, buf, m->pp[k] ? C_TEXT : C_RED, 0);
        canvas_text_right(&g_bot, &font_small, x + 113, y + 32, type_names[mv->type], C_TYPE0 + mv->type, C_INK);
        if (!is_wild || true) {
            // effectiveness hint
            if (mv->cat != CAT_STATUS && dex_is_seen(side[1].mon->species)) {
                int e = type_eff(mv->type, 1);
                const char *h = e == 0 ? "Aucun effet" : e > 4 ? "Super efficace" : e < 4 ? "Peu efficace" : "";
                ui_text_in(&g_bot, &font_small, x, y + 46, 121, 16, h, e > 4 ? C_TYPE0 + 5 : C_BTN_SH, 0, 0);
            }
        }
    }
    ui_button(&g_bot, 86, 156, 84, 30, "Retour", BTN_DARK, &font_main);
}

static int move_menu(void)
{
    Mon *m = side[0].mon;
    // Struggle-like if no PP at all
    bool any = false;
    for (int k = 0; k < 4; k++)
        if (m->moves[k] != 0xFFFF && m->pp[k] > 0)
            any = true;
    if (!any)
        return 4;
    int sel = 0;
    draw_move_menu(sel);
#ifdef WEBSITE_CAPTURE
    extern volatile u32 g_site_capture[8];
    g_site_capture[5] = 2;
    DC_FlushRange((void *)g_site_capture, 32);
#endif
    while (1) {
        bframe();
        if (is_link && !link_ok()) return -1;
        int old = sel;
        if (g_krep & KEY_RIGHT) sel ^= 1;
        if (g_krep & KEY_LEFT) sel ^= 1;
        if (g_krep & (KEY_UP | KEY_DOWN)) sel ^= 2;
        if (old != sel) {
            sfx_play(SFX_CURSOR);
            draw_move_menu(sel);
        }
        int pick = -1;
        if (g_kdown & KEY_A)
            pick = sel;
        for (int k = 0; k < 4; k++)
            if (touch_in(4 + (k % 2) * 126, 8 + (k / 2) * 72, 122, 66))
                pick = k;
        if (pick >= 0) {
            if (m->moves[pick] == 0xFFFF)
                continue;
            if (m->pp[pick] == 0) {
                sfx_play(SFX_ERROR);
                msg("Plus de PP pour cette attaque !");
                dlg_close();
                draw_move_menu(sel);
                continue;
            }
            sfx_play(SFX_SELECT);
            return pick;
        }
        if ((g_kdown & KEY_B) || touch_in(88, 156, 80, 32)) {
            sfx_play(SFX_CANCEL);
            return -1;
        }
    }
}

// ---------------------------------------------------------------- send out / withdraw
static void slide_in_ally(void)
{
    ally_visible = true;
    for (int i = 0; i <= 16; i++) {
        ally_x = -64 + (ALLY_HOME_X + 64) * i / 16;
        bframe();
    }
    sfx_cry(side[0].mon->species);
    draw_infobox(0);
}

static void send_out(int s, int idx, bool announce)
{
    if (is_link) { memset(&side[s], 0, sizeof side[s]); side[s].type_override = -1; }
    if (s == 0) {
        player_idx = idx;
        side[0].mon = &g_save.party[idx];
        participants[idx] = true;
    } else {
        foe_idx = idx;
        side[1].mon = &foe_party[idx];
        dex_seen(side[1].mon->species);
    }
    memset(side[s].stage, 0, sizeof side[s].stage);
    side[s].confuse = side[s].flinch = side[s].protect = side[s].protect_chain = side[s].trap = 0;
    side[s].charge_move = -1;
    side[s].last_move = -1;
    side[s].first_turn = 1;
    side[s].steal_turn_used = 0;
    side[s].delayed_move = -1;
    load_mon_gfx(s);
    if (s == 0) {
        if (announce)
            msg("À toi, %s !", pname(0));
        fx_throw_tampon(ALLY_HOME_X + 32, ALLY_HOME_Y + 40);
        ally_x = ALLY_HOME_X;
        ally_visible = true;
        ally_flash = 12;
        sfx_cry(side[0].mon->species);
        bwait(12);
        draw_infobox(0);
    } else {
        if (announce) {
            if (is_link) msg("L'autre joueur envoie %s !", pname(1));
            else {
                const TrainerData *t = &trainers[trainer_id];
                msg("%s envoie %s !", t->name, pname(1));
            }
        }
        foe_x = FOE_HOME_X;
        foe_visible = true;
        foe_flash = 12;
        sfx_cry(side[1].mon->species);
        bwait(12);
        draw_infobox(1);
    }
}

// ---------------------------------------------------------------- damage
static int calc_damage(int a, int d, int move, bool *crit, int *eff)
{
    const MoveData *mv = &moves[move];
    Mon *ma = side[a].mon;
    int lvl = ma->level;
    int power = mv->power;
    if (mv->effect == EF_FIXED_LEVEL) {
        *eff = type_eff(mv->type, d) ? 4 : 0;
        *crit = false;
        return *eff ? lvl : 0;
    }
    bool phys = mv->cat == CAT_PHYS;
    int atk = eff_stat(a, phys ? STAT_ATK : STAT_SPA);
    int def = eff_stat(d, phys ? STAT_DEF : STAT_SPD);
    int crit_rate = mv->effect == EF_HIGH_CRIT ? 8 : 16;
    *crit = battle_random(crit_rate) == 0;
    if (*crit) {
        // crits ignore negative attack stages / positive defence stages
        if (side[a].stage[phys ? STAT_ATK : STAT_SPA] < 0)
            atk = mon_stat(ma, phys ? STAT_ATK : STAT_SPA);
        if (side[d].stage[phys ? STAT_DEF : STAT_SPD] > 0)
            def = mon_stat(side[d].mon, phys ? STAT_DEF : STAT_SPD);
    }
    int dmg = ((2 * lvl / 5 + 2) * power * atk / def) / 50 + 2;
    if (*crit)
        dmg = dmg * 3 / 2;
    if (mv->type == type1(a) || mv->type == type2(a))
        dmg = dmg * 3 / 2;
    *eff = type_eff(mv->type, d);
    dmg = dmg * *eff / 4;
    if (gimmick == GIM_TAUX) {
        // Lagarde's key interest rate: +/- 25% depending on the turn's rate
        static int rate;
        rate = (g_frame / 60) % 5;
        dmg = dmg * (90 + rate * 5) / 100;
    }
    dmg = dmg * (85 + battle_random(16)) / 100;
    if (*eff && dmg < 1)
        dmg = 1;
    return dmg;
}

static void apply_damage(int d, int dmg)
{
    Mon *m = side[d].mon;
    int from = m->hp;
    int to = MAX(0, from - dmg);
    animate_hp(d, from, to);
}

static bool try_status(int target, int st, bool announce_fail)
{
    Mon *m = side[target].mon;
    if (m->hp == 0)
        return false;
    if (m->status) {
        if (announce_fail)
            msg("Mais %s a déjà un problème…", pname(target));
        return false;
    }
    // type immunities
    if (st == STATUS_LOBBY && (type1(target) == TYPE_LOBBY || type2(target) == TYPE_LOBBY)) {
        if (announce_fail)
            msg("%s est déjà du côté des lobbies !", pname(target));
        return false;
    }
    if (st == STATUS_GEL && (type1(target) == TYPE_MONETAIRE || type2(target) == TYPE_MONETAIRE)) {
        if (announce_fail)
            msg("On ne gèle pas les fonds d'un banquier central !");
        return false;
    }
    m->status = st;
    if (st == STATUS_SOMMEIL)
        m->sleep_turns = 1 + battle_random(3);
    static const char *const txt[6] = {"", "%s est sous l'influence d'un lobby !", "%s est pris dans un scandale !",
                                       "Les fonds de %s sont gelés !", "%s s'endort en plein sommet nocturne !",
                                       "%s est bloqué en commission !"};
    fx_status(target, st);
    msg(txt[st], pname(target));
    draw_infobox(target);
    return true;
}

static void stat_change(int target, int stat, int n, bool self)
{
    static const char *const sn[8] = {"", "Argumentation", "Résilience", "Expertise", "Diplomatie",
                                      "Réactivité", "Précision", "Esquive"};
    Side *s = &side[target];
    int old = s->stage[stat];
    int nv = CLAMP(old + n, -6, 6);
    const char *st = tr(sn[stat]);
    if (nv == old) {
        if (n > 0)
            msg("%s : %s ne peut plus monter !", pname(target), st);
        else
            msg("%s : %s ne peut plus baisser !", pname(target), st);
        return;
    }
    s->stage[stat] = nv;
    sfx_play(n > 0 ? SFX_STATUP : SFX_STATDOWN);
    fx_stat(target, n > 0);
    int a = abs(nv - old);
    if (n > 0)
        msg(a >= 2 ? "%s : %s augmente beaucoup !" : "%s : %s augmente !", pname(target), st);
    else
        msg(a >= 2 ? "%s : %s baisse beaucoup !" : "%s : %s baisse !", pname(target), st);
    (void)self;
}

// ---------------------------------------------------------------- one move
static bool faint_check(int s);

static bool accuracy_check(int a, int d, int move)
{
    const MoveData *mv = &moves[move];
    if (mv->acc == 0 || mv->effect == EF_ALWAYS_HIT)
        return true;
    int acc = mv->acc;
    int st = CLAMP(side[a].stage[STAT_ACC] - side[d].stage[STAT_EVA], -6, 6);
    acc = stage_mult(STAT_ACC, st, acc);
    return battle_random(100) < acc;
}

static void use_move(int a, int slot, int move_override)
{
    int d = 1 - a;
    Mon *ma = side[a].mon, *md = side[d].mon;
    int move = move_override >= 0 ? move_override : ma->moves[slot];
    if (move < 0 || move >= NUM_MOVES)
        move = 0;
    const MoveData *mv = &moves[move];
    if (slot >= 0 && slot < 4 && move_override < 0 && ma->pp[slot] > 0)
        ma->pp[slot]--;
    side[a].last_move = move;
    if (a == 0 || !is_trainer || gimmick != GIM_TRUMP)
        msg("%s utilise %s !", pname(a), mv->name);
    else
        msg("(trump)%s utilise %s !", pname(a), mv->name);

    // charge moves: first turn charges
    if (mv->effect == EF_CHARGE && side[a].charge_move < 0) {
        side[a].charge_move = move;
        msg("%s prépare un dossier de 400 pages…", pname(a));
        return;
    }
    side[a].charge_move = -1;

    if (mv->effect == EF_STEAL_TURN && !side[a].first_turn) {
        msg("Mais personne ne tombe deux fois dans le piège du canapé !");
        return;
    }
    if (mv->effect == EF_COPY) {
        if (side[d].last_move >= 0 && moves[side[d].last_move].effect != EF_COPY) {
            msg("%s plagie l'adversaire !", pname(a));
            use_move(a, -1, side[d].last_move);
        } else
            msg("Mais il n'y a rien à plagier…");
        return;
    }
    if (mv->effect == EF_LEAVE) {
        if (is_wild && a == 0) {
            msg("%s invoque l'Article 50 et quitte le débat !", pname(a));
            result = BATTLE_FLED;
            return;
        }
        if (is_wild && a == 1) {
            msg("%s invoque l'Article 50 et s'en va !", pname(a));
            result = BATTLE_FLED;
            return;
        }
        msg("%s invoque l'Article 50… mais les négociations vont durer des années !", pname(a));
        stat_change(a, STAT_SPE, 2, true);
        return;
    }

    // target protected?
    if (mv->cat != CAT_STATUS || mv->effect == EF_STAT_DOWN || mv->effect == EF_GEL || mv->effect == EF_SOMMEIL ||
        mv->effect == EF_LOBBY || mv->effect == EF_SCANDALE || mv->effect == EF_CONFUSE || mv->effect == EF_BLOQUE) {
        if (side[d].protect) {
            msg("%s se protège avec un veto !", pname(d));
            return;
        }
    }
    // Orbán's veto gimmick
    if (gimmick == GIM_VETO && a == 0 && battle_random(100) < 25) {
        sfx_play(SFX_GAVEL);
        msg("« VETO ! » L'adversaire bloque la décision à l'unanimité requise.");
        return;
    }
    if (!accuracy_check(a, d, move)) {
        msg("Mais l'attaque de %s rate la cible !", pname(a));
        side[a].last_move_ok = 0;
        return;
    }
    side[a].last_move_ok = 1;

    if (mv->cat == CAT_STATUS) {
        fx_move(a, mv->type, mv->cat);
        switch (mv->effect) {
        case EF_STAT_UP: stat_change(a, mv->param / 10, mv->param % 10, true); break;
        case EF_STAT_DOWN: stat_change(d, mv->param / 10, -(mv->param % 10), false); break;
        case EF_LOBBY: try_status(d, STATUS_LOBBY, true); break;
        case EF_SCANDALE: try_status(d, STATUS_SCANDALE, true); break;
        case EF_GEL: try_status(d, STATUS_GEL, true); break;
        case EF_SOMMEIL: try_status(d, STATUS_SOMMEIL, true); break;
        case EF_BLOQUE: try_status(d, STATUS_BLOQUE, true); break;
        case EF_CONFUSE:
            if (side[d].confuse)
                msg("%s est déjà désinformé !", pname(d));
            else {
                side[d].confuse = 2 + battle_random(4);
                msg("%s est désinformé !", pname(d));
            }
            break;
        case EF_HEAL_HALF: {
            int mx = mon_max_hp(ma);
            if (ma->hp >= mx) {
                msg("Mais les PV de %s sont déjà au max !", pname(a));
                break;
            }
            sfx_play(SFX_HEAL);
            animate_hp(a, ma->hp, MIN(mx, ma->hp + mx / 2));
            msg("%s récupère des PV !", pname(a));
            break;
        }
        case EF_REST: {
            int mx = mon_max_hp(ma);
            ma->status = STATUS_SOMMEIL;
            ma->sleep_turns = 2;
            sfx_play(SFX_HEAL);
            animate_hp(a, ma->hp, mx);
            msg("%s fait une sieste réparatrice !", pname(a));
            break;
        }
        case EF_PROTECT:
            if (side[a].protect_chain && battle_random(2)) {
                msg("Mais le veto ne passe pas cette fois !");
                side[a].protect_chain = 0;
            } else {
                side[a].protect = 1;
                side[a].protect_chain++;
                msg("%s brandit son droit de veto !", pname(a));
            }
            break;
        case EF_HAZE:
            memset(side[0].stage, 0, sizeof side[0].stage);
            memset(side[1].stage, 0, sizeof side[1].stage);
            msg("Clause de sauvegarde ! Toutes les modifications sont annulées.");
            break;
        case EF_ERASE:
            memset(side[d].stage, 0, sizeof side[d].stage);
            sfx_play(SFX_SMS);
            msg("Les messages de %s ont été effacés… Plus aucune trace !", pname(d));
            break;
        case EF_PAY_DAY:
            money_bonus += ma->level * 5;
            sfx_play(SFX_COIN);
            msg("Des fonds structurels pleuvent sur le terrain !");
            break;
        case EF_STEAL_TURN:
            side[d].flinch = 1;
            msg("%s se retrouve assis sur le canapé !", pname(d));
            break;
        default:
            msg("Mais rien ne se passe…");
        }
        return;
    }

    // damaging
    int hits = 1;
    if (mv->effect == EF_MULTI_HIT) {
        static const u8 dist[8] = {2, 2, 2, 3, 3, 3, 4, 5};
        hits = dist[battle_random(8)];
    }
    int total = 0, eff = 4;
    bool crit = false;
    int i;
    for (i = 0; i < hits && md->hp > 0; i++) {
        int dmg = calc_damage(a, d, move, &crit, &eff);
        if (eff == 0) {
            msg("Ça n'affecte pas %s…", pname(d));
            return;
        }
        fx_move(a, mv->type, mv->cat);
        if (d == 1) {
            foe_shake = 12;
            foe_flash = 16;
        } else {
            ally_shake = 12;
            ally_flash = 16;
        }
        sfx_play(eff > 4 ? SFX_HIT_SUPER : eff < 4 ? SFX_HIT_WEAK : SFX_HIT);
        dmg = MIN(dmg, md->hp);
        apply_damage(d, dmg);
        total += dmg;
        if (crit)
            msg("Coup critique !");
    }
    if (hits > 1)
        msg("Touché %d fois !", i);
    if (eff > 4)
        msg("C'est super efficace !");
    else if (eff < 4)
        msg("Ce n'est pas très efficace…");

    // secondary effects
    int ch = mv->chance ? mv->chance : 100;
    if (md->hp > 0 && battle_random(100) < ch) {
        switch (mv->effect) {
        case EF_LOBBY: try_status(d, STATUS_LOBBY, false); break;
        case EF_SCANDALE: try_status(d, STATUS_SCANDALE, false); break;
        case EF_GEL: try_status(d, STATUS_GEL, false); break;
        case EF_SOMMEIL: try_status(d, STATUS_SOMMEIL, false); break;
        case EF_BLOQUE: try_status(d, STATUS_BLOQUE, false); break;
        case EF_CONFUSE:
            if (!side[d].confuse) {
                side[d].confuse = 2 + battle_random(4);
                msg("%s est désinformé !", pname(d));
            }
            break;
        case EF_FLINCH: side[d].flinch = 1; break;
        case EF_STAT_DOWN: stat_change(d, mv->param / 10, -(mv->param % 10), false); break;
        case EF_STAT_UP: stat_change(a, mv->param / 10, mv->param % 10, true); break;
        case EF_TRAP:
            if (!side[d].trap) {
                side[d].trap = 2 + battle_random(4);
                msg("%s est pris dans une procédure sans fin !", pname(d));
            }
            break;
        }
    }
    if (mv->effect == EF_DRAIN && total > 0) {
        int mx = mon_max_hp(ma);
        animate_hp(a, ma->hp, MIN(mx, ma->hp + MAX(1, total / 2)));
        msg("%s ponctionne des fonds !", pname(a));
    }
    if (mv->effect == EF_RECOIL && total > 0 && ma->hp > 0) {
        apply_damage(a, MAX(1, total / 4));
        msg("%s subit le contrecoup !", pname(a));
    }
    if (mv->effect == EF_SELF_DESTRUCT) {
        apply_damage(a, ma->hp);
    }
    if (mv->effect == EF_PAY_DAY) {
        money_bonus += ma->level * 5;
        msg("Des pièces s'éparpillent partout !");
    }
}

// ---------------------------------------------------------------- turn flow
static bool can_act(int s)
{
    Mon *m = side[s].mon;
    if (m->hp == 0)
        return false;
    if (side[s].flinch) {
        side[s].flinch = 0;
        msg("%s est trop déstabilisé pour agir !", pname(s));
        return false;
    }
    if (m->status == STATUS_SOMMEIL) {
        if (m->sleep_turns > 0) {
            m->sleep_turns--;
            msg("%s dort profondément… (on est à 4 h du matin)", pname(s));
            return false;
        }
        m->status = 0;
        msg("%s se réveille ! Le sommet est terminé.", pname(s));
        draw_infobox(s);
    }
    if (m->status == STATUS_BLOQUE) {
        if (battle_random(5) == 0) {
            m->status = 0;
            msg("%s sort enfin de commission !", pname(s));
            draw_infobox(s);
        } else {
            msg("%s est bloqué en commission !", pname(s));
            return false;
        }
    }
    if (m->status == STATUS_GEL && battle_random(4) == 0) {
        msg("Les fonds de %s sont gelés ! Impossible d'agir.", pname(s));
        return false;
    }
    if (side[s].confuse) {
        side[s].confuse--;
        if (side[s].confuse == 0) {
            msg("%s a vérifié ses sources !", pname(s));
        } else {
            msg("%s est désinformé…", pname(s));
            if (battle_random(2) == 0) {
                int dmg = ((2 * m->level / 5 + 2) * 40 * eff_stat(s, STAT_ATK) / eff_stat(s, STAT_DEF)) / 50 + 2;
                msg("Il relaie une fausse information et se discrédite lui-même !");
                if (s == 0) ally_shake = 10; else foe_shake = 10;
                sfx_play(SFX_HIT);
                apply_damage(s, MIN(dmg, m->hp));
                return false;
            }
        }
    }
    if (gimmick == GIM_COFFEE && s == 1 && battle_random(100) < 15) {
        msg("Orbán est sorti prendre un café ! Son Euromon attend, désemparé.");
        return false;
    }
    return true;
}

static void end_of_turn(int s)
{
    Mon *m = side[s].mon;
    side[s].protect = 0;
    side[s].first_turn = 0;
    if (m->hp == 0)
        return;
    int mx = mon_max_hp(m);
    if (m->status == STATUS_LOBBY) {
        msg("%s subit l'influence des lobbies !", pname(s));
        if (s == 0) ally_flash = 10; else foe_flash = 10;
        apply_damage(s, MAX(1, mx / 8));
    } else if (m->status == STATUS_SCANDALE) {
        msg("Le scandale éclabousse %s !", pname(s));
        apply_damage(s, MAX(1, mx / 16));
    }
    if (side[s].trap && m->hp > 0) {
        side[s].trap--;
        msg("%s est englué dans la procédure !", pname(s));
        apply_damage(s, MAX(1, mx / 8));
    }
}

static int foe_choose_move(void)
{
    Mon *m = side[1].mon;
    const TrainerData *t = is_trainer ? &trainers[trainer_id] : NULL;
    int ai = t ? t->ai : 0;
    int best = -1, best_score = -9999;
    for (int k = 0; k < 4; k++) {
        if (m->moves[k] == 0xFFFF || m->pp[k] == 0)
            continue;
        const MoveData *mv = &moves[m->moves[k]];
        int score = battle_random(20);
        if (ai >= 1) {
            if (mv->cat != CAT_STATUS) {
                int e = type_eff(mv->type, 0);
                score += mv->power * e / 4;
                if (mv->type == type1(1) || mv->type == type2(1))
                    score += mv->power / 2;
                if (e == 0)
                    score -= 500;
            } else {
                score += 30;
                if (mv->effect == EF_HEAL_HALF && m->hp < mon_max_hp(m) / 2)
                    score += 120;
                if ((mv->effect >= EF_LOBBY && mv->effect <= EF_BLOQUE) && side[0].mon->status)
                    score -= 200;
                if (mv->effect == EF_STAT_UP && side[1].stage[mv->param / 10] >= 2)
                    score -= 150;
            }
        } else
            score += mv->power / 3;
        if (score > best_score) {
            best_score = score;
            best = k;
        }
    }
    return best < 0 ? 4 : best;
}

static bool faint_check(int s)
{
    if (side[s].mon->hp > 0)
        return false;
    sfx_cry(side[s].mon->species);
    bwait(20);
    sfx_play(SFX_FAINT);
    // slide down
    for (int i = 0; i < 16; i++) {
        if (s == 1) foe_y += 5; else ally_y += 5;
        bframe();
    }
    if (s == 1) {
        foe_visible = false;
        foe_y = FOE_HOME_Y;
    } else {
        ally_visible = false;
        ally_y = ALLY_HOME_Y;
    }
    draw_infobox(s);
    msg("%s est K.O. !", pname(s));
    side[s].mon->status = 0;
    return true;
}

// experience, level up, learning
static void learn_new_moves(Mon *m, int from_level)
{
    const u16 *l = species[m->species].learn;
    for (int i = 0; l[i] != 0xFFFF; i += 2) {
        if (l[i] <= from_level || l[i] > m->level)
            continue;
        int mv = l[i + 1];
        int r = mon_learn(m, mv);
        if (r >= 0) {
            sfx_play(SFX_LEVELUP);
            msg("%s apprend %s !", mon_name(m), moves[mv].name);
        } else if (r == -2) {
            msg("%s veut apprendre %s, mais connaît déjà quatre attaques.", mon_name(m), moves[mv].name);
            const char *opts[5];
            for (int k = 0; k < 4; k++)
                opts[k] = moves[m->moves[k]].name;
            opts[4] = "Ne pas apprendre";
            msg("Quelle attaque oublier ?");
            int c = dlg_choice(opts, 5, true);
            if (c >= 0 && c < 4) {
                msg("1, 2, 3… Hop ! %s oublie %s…", mon_name(m), moves[m->moves[c]].name);
                m->moves[c] = mv;
                m->pp[c] = moves[mv].pp;
                sfx_play(SFX_LEVELUP);
                msg("… et apprend %s !", moves[mv].name);
            } else
                msg("%s n'apprend pas %s.", mon_name(m), moves[mv].name);
        }
    }
}

static void gain_exp(void)
{
    Mon *f = side[1].mon;
    int base = species[f->species].exp_yield;
    int total = base * f->level / 7;
    if (is_trainer)
        total = total * 3 / 2;
    int n = 0;
    for (int i = 0; i < g_save.party_count; i++)
        if (participants[i] && g_save.party[i].hp > 0)
            n++;
    if (n == 0)
        return;
    for (int i = 0; i < g_save.party_count; i++) {
        Mon *m = &g_save.party[i];
        if (!participants[i] || m->hp == 0 || m->level >= 100)
            continue;
        int gain = MAX(1, total / n);
        msg("%s gagne %d points d'expérience !", mon_name(m), gain);
        int start_level = m->level;
        u32 target = m->exp + gain;
        // animate exp bar for active mon
        while (m->exp < target) {
            u32 next = exp_for_level(species[m->species].growth, m->level + 1);
            u32 step = MAX(1, (target - m->exp) / 12);
            m->exp = MIN(target, m->exp + step);
            if (m == side[0].mon) {
                draw_infobox(0);
                sfx_play(SFX_EXP);
                bframe();
            }
            if (m->exp >= next && m->level < 100) {
                int oldmax = mon_max_hp(m);
                m->level++;
                m->hp += mon_max_hp(m) - oldmax;
                if (m == side[0].mon)
                    draw_infobox(0);
                sfx_play(SFX_LEVELUP);
                msg("%s monte au niveau %d !", mon_name(m), m->level);
            }
        }
        if (m->level > start_level)
            learn_new_moves(m, start_level);
    }
}

// capture
static bool try_capture(int item)
{
    const ItemData *it = &items[item];
    Mon *m = side[1].mon;
    msg("{P} lance un %s !", it->name);
    fx_throw_ball_to_foe(foe_x + 32, foe_y + 32);
    foe_visible = false;
    bwait(10);
    int mx = mon_max_hp(m);
    int rate = species[m->species].catch_rate;
    int ball = it->param;      // x10
    int a;
    if (ball >= 255)
        a = 255;
    else {
        a = ((3 * mx - 2 * m->hp) * rate * ball / 10) / (3 * mx);
        if (m->status == STATUS_SOMMEIL || m->status == STATUS_BLOQUE)
            a *= 2;
        else if (m->status)
            a = a * 3 / 2;
    }
    if (m->species == SP_CONSTITUTIO)
        a = 0;
    int shakes = 0;
    if (a >= 255)
        shakes = 4;
    else if (a > 0) {
        // Four independent shakes must give an overall chance of a / 255.
        // Find floor(65536 * fourth_root(a / 255)) without rounding both
        // square roots to whole numbers (which understated capture odds).
        // UINT64_MAX / 255 is exact; mid < 65536 keeps mid^4 in u64.
        u64 target = 0x0101010101010101ULL * a;
        int lo = 0, hi = 65536;
        while (lo + 1 < hi) {
            int mid = (lo + hi) / 2;
            u64 square = (u64)mid * mid;
            if (square * square <= target)
                lo = mid;
            else
                hi = mid;
        }
        int b = lo;
        for (shakes = 0; shakes < 4; shakes++)
            if ((int)(rng_next() & 0xFFFF) >= b)
                break;
    }
    for (int i = 0; i < MIN(shakes, 3); i++) {
        fx_ball_shake();
        sfx_play(SFX_CAPTURE_SHAKE);
        bwait(30);
    }
    if (shakes >= 4) {
        sfx_play(SFX_CAPTURE_OK);
        fx_ball_stars();
        msg("Et voilà ! %s est enregistré au Journal officiel !", pname(1));
        bool new_entry = !dex_is_caught(m->species);
        Mon copy = *m;
        int r2 = party_add(&copy);
        if (new_entry)
            msg("Les données de %s sont ajoutées à l'Eurodex.", pname(1));
        if (r2 == 1)
            msg("%s est envoyé aux Archives.", pname(1));
        fx_clear();
        return true;
    }
    fx_clear();
    foe_visible = true;
    foe_flash = 10;
    static const char *const fail[4] = {"Oh non ! %s s'est libéré !", "Raah ! Ça y était presque !",
                                        "Mince ! Il manquait juste un tampon !", "Argh ! Un vice de procédure !"};
    if (m->species == SP_CONSTITUTIO)
        msg("%s a été rejeté par référendum ! Impossible de le capturer.", pname(1));
    else
        msg(fail[MIN(shakes, 3)], pname(1));
    return false;
}

static bool use_battle_item(int item)
{
    const ItemData *it = &items[item];
    if (it->kind == IK_BALL) {
        if (is_trainer) {
            msg("On ne capture pas l'Euromon d'un autre dresseur ! Ce serait un scandale.");
            return false;
        }
        bag_take(item, 1);
        if (try_capture(item)) {
            result = BATTLE_CAUGHT;
        }
        return true;
    }
    if (it->kind == IK_BATTLE) {
        bag_take(item, 1);
        msg("{P} utilise %s !", it->name);
        stat_change(0, CLAMP(it->param / 10, 1, 7), MAX(1, it->param % 10), true);
        return true;
    }
    if (it->kind == IK_HEAL || it->kind == IK_STATUS || it->kind == IK_REVIVE || it->kind == IK_PP) {
        int i = party_menu(1, "Sur quel Euromon ?");
        if (i < 0)
            return false;
        Mon *m = &g_save.party[i];
        int mx = mon_max_hp(m);
        if (it->kind == IK_HEAL && m->hp > 0 && m->hp < mx) {
            bag_take(item, 1);
            int h = it->param >= 999 ? mx : it->param;
            sfx_play(SFX_HEAL);
            if (m == side[0].mon)
                animate_hp(0, m->hp, MIN(mx, m->hp + h));
            else
                m->hp = MIN(mx, m->hp + h);
            msg("%s récupère des PV.", mon_name(m));
            return true;
        }
        if (it->kind == IK_STATUS && m->status && m->hp > 0) {
            bag_take(item, 1);
            m->status = 0;
            if (m == side[0].mon)
                draw_infobox(0);
            msg("%s va mieux.", mon_name(m));
            return true;
        }
        if (it->kind == IK_REVIVE && m->hp == 0) {
            bag_take(item, 1);
            m->hp = it->param >= 999 ? mx : mx / 2;
            msg("%s reprend du service !", mon_name(m));
            return true;
        }
        msg("Ça n'aura aucun effet.");
        return false;
    }
    msg("Ce n'est pas le moment !");
    return false;
}

static int choose_switch(bool forced)
{
    extern int g_party_menu_default;
    while (1) {
        for (int k = 0; k < g_save.party_count; k++)
            if (g_save.party[k].hp > 0 && k != player_idx) {
                g_party_menu_default = k;
                break;
            }
        int i = party_menu(1, forced ? "Qui envoyer au débat ?" : "Qui envoyer ?");
        if (i < 0) {
            if (is_link) return -1;
            if (forced)
                continue;
            return -1;
        }
        if (g_save.party[i].hp == 0) {
            msg("%s n'est plus en état de débattre !", mon_name(&g_save.party[i]));
            dlg_close();
            continue;
        }
        if (i == player_idx && side[0].mon->hp > 0) {
            if (!forced)
                return -1;
            msg("%s est déjà sur le terrain !", mon_name(&g_save.party[i]));
            dlg_close();
            continue;
        }
        return i;
    }
}

static void withdraw_ally(void)
{
    msg("Reviens, %s !", pname(0));
    for (int i = 0; i < 12; i++) {
        ally_x -= 8;
        bframe();
    }
    ally_visible = false;
    draw_infobox(0);
}

static int foe_next_alive(void)
{
    for (int i = 0; i < foe_count; i++)
        if (foe_party[i].hp > 0)
            return i;
    return -1;
}

// Xi's gimmick: type rotates partner / competitor / systemic rival
static void gimmick_turn_start(void)
{
    if (gimmick == GIM_RIVAL_SYS) {
        static const int rot[3] = {TYPE_DIPLO, TYPE_INDUSTRIE, TYPE_SOUVERAIN};
        static const char *const lab[3] = {"partenaire", "concurrent", "rival systémique"};
        static int k;
        k = (k + 1) % 3;
        side[1].type_override = rot[k];
        draw_infobox(1);
        msg("L'Euromon adverse se présente désormais comme… %s ! (type %s)", tr(lab[k]), type_names[rot[k]]);
    }
}

// ---------------------------------------------------------------- scene setup
static void setup_scene(void)
{
    gfx_clear_scene(false);
    gfx_clear_scene(true);
    canvas_clear(&g_top, 0);
    ui_backdrop(&g_bot);
    // background by map type
    const char *bg = "ui/bt_grass.bgi";
    extern int g_battle_bg_hint;
    switch (g_battle_bg_hint) {
    case 1: bg = "ui/bt_indoor.bgi"; break;
    case 2: bg = "ui/bt_hemicycle.bgi"; break;
    case 3: bg = "ui/bt_city.bgi"; break;
    case 4: bg = "ui/bt_night.bgi"; break;
    }
    if (bgi_load(false, 2, bg, 1) < 0)
        bgi_load(false, 2, "ui/bt_grass.bgi", 1);
    bgi_load(true, 2, "ui/pattern.bgi", 1);
    for (int i = OAM_WORLD; i < 128; i++)
        oamClearSprite(&oamMain, i);
    gfx_foe = spr_alloc(false, SpriteSize_64x64, SpriteColorFormat_256Color);
    gfx_ally = spr_alloc(false, SpriteSize_64x64, SpriteColorFormat_256Color);
    fx_init();
}

static void teardown_scene(void)
{
    oamClearSprite(&oamMain, OAM_BATTLE);
    oamClearSprite(&oamMain, OAM_BATTLE + 1);
    fx_shutdown();
    spr_free(false, gfx_foe);
    spr_free(false, gfx_ally);
    sheet_free(&sh_foe);
    sheet_free(&sh_ally);
    portrait_hide_all();
    canvas_clear(&g_top, 0);
    canvas_clear(&g_bot, 0);
}

int g_battle_bg_hint;

// transition: 12 stars spiral in, flash
static void intro_transition(void)
{
    fx_star_transition();
}

// ---------------------------------------------------------------- main loop
static int run_battle(void)
{
    result = -1;
    money_bonus = 0;
    run_attempts = 0;
    memset(participants, 0, sizeof participants);
    memset(side, 0, sizeof side);
    side[0].type_override = side[1].type_override = -1;
    int first = party_first_alive();
    if (first < 0)
        return BATTLE_LOST;

    intro_transition();
    setup_scene();
    gfx_brightness(false, 0);
    gfx_brightness(true, 0);
    // foe slides in from the left, ally (trainer) from the right
    side[1].mon = &foe_party[0];
    foe_idx = 0;
    dex_seen(foe_party[0].species);
    load_mon_gfx(1);
    foe_visible = true;
    ally_visible = false;
    foe_y = FOE_HOME_Y;
    ally_y = ALLY_HOME_Y;
    if (is_trainer) {
        foe_visible = false;
        const TrainerData *t = &trainers[trainer_id];
        if (t->portrait)
            portrait_show(SIDE_RIGHT, t->portrait, "neutral");
        portrait_set_y(20);
        bwait(20);
        msg("%s %s veut débattre !", t->cls, t->name);
        portrait_hide(SIDE_RIGHT);
        bwait(16);
        portrait_set_y(38);
        send_out(1, 0, true);
    } else {
        for (int i = 0; i <= 20; i++) {
            foe_x = -64 + (FOE_HOME_X + 64) * i / 20;
            bframe();
        }
        sfx_cry(foe_party[0].species);
        draw_infobox(1);
        if (foe_party[0].shiny) {
            fx_ball_stars();
            msg("Oh ! Un %s chromatique !", pname(1));
        }
        msg("Un %s sauvage apparaît !", pname(1));
    }
    send_out(0, first, true);
    dlg_close();

    while (result < 0) {
        gimmick_turn_start();
        // ---- player choice
        int p_action = -1, p_slot = -1, p_item = -1, p_switch = -1;
        while (p_action < 0) {
            dlg_say_nowait("", "Que doit faire {P} ?");
            if (side[0].charge_move >= 0) {
                p_action = 0;
                p_slot = -2;
                break;
            }
            int c = main_menu();
            if (c == 0) {
                int s = move_menu();
                if (s >= 0) {
                    p_action = 0;
                    p_slot = s;
                }
            } else if (c == 1) {
                int it = bag_menu(1);
                if (it >= 0) {
                    p_action = 1;
                    p_item = it;
                }
            } else if (c == 3) {
                int i = choose_switch(false);
                if (i >= 0) {
                    p_action = 2;
                    p_switch = i;
                }
            } else if (c == 2) {
                if (is_trainer) {
                    msg("On ne quitte pas un débat officiel ! Ce serait un aveu de faiblesse.");
                    continue;
                }
                run_attempts++;
                int ps = eff_stat(0, STAT_SPE), fs = MAX(1, eff_stat(1, STAT_SPE) / 4 % 256);
                int odds = ps * 32 / fs + 30 * run_attempts;
                if (odds > 255 || battle_random(256) < odds) {
                    sfx_play(SFX_WHOOSH);
                    msg("Vous prenez la fuite par la sortie de secours !");
                    result = BATTLE_FLED;
                    break;
                }
                msg("Impossible de fuir : la séance n'est pas levée !");
                p_action = 3; // lose turn
            }
        }
        ui_backdrop(&g_bot);
        if (result >= 0)
            break;

        // ---- foe choice
        int f_slot = side[1].charge_move >= 0 ? -2 : foe_choose_move();

        // ---- non-move actions first
        if (p_action == 1) {
            bool used = use_battle_item(p_item);
            if (!used) {
                dlg_close();
                continue;
            }
            if (result >= 0)
                break;
        } else if (p_action == 2) {
            withdraw_ally();
            send_out(0, p_switch, true);
        }

        // ---- order
        int order[2] = {0, 1};
        if (p_action == 0) {
            int pm = p_slot == -2 ? side[0].charge_move : (p_slot == 4 ? 0 : side[0].mon->moves[p_slot]);
            int fm = f_slot == -2 ? side[1].charge_move : (f_slot == 4 ? 0 : side[1].mon->moves[f_slot]);
            int pp = moves[pm].priority, fp = moves[fm].priority;
            int ps = eff_stat(0, STAT_SPE), fsp = eff_stat(1, STAT_SPE);
            bool foe_first = fp > pp || (fp == pp && (fsp > ps || (fsp == ps && battle_random(2))));
            if (foe_first) {
                order[0] = 1;
                order[1] = 0;
            }
        } else {
            order[0] = 1;
            order[1] = -1;
        }
        for (int k = 0; k < 2 && result < 0; k++) {
            int s = order[k];
            if (s < 0)
                break;
            if (side[s].mon->hp == 0 || side[1 - s].mon->hp == 0)
                continue;
            if (!can_act(s))
                continue;
            if (s == 0) {
                if (gimmick == GIM_LONGTABLE) {
                    // Putin's long table: your move takes a turn to reach the other end
                    int queued = side[0].delayed_move;
                    int now = p_slot == -2 ? side[0].charge_move : (p_slot == 4 ? -1 : side[0].mon->moves[p_slot]);
                    if (p_slot >= 0 && p_slot < 4 && side[0].mon->pp[p_slot])
                        side[0].mon->pp[p_slot]--;
                    side[0].delayed_move = now;
                    msg("%s lance son argument… La table est si longue qu'il mettra un tour à arriver !", pname(0));
                    if (queued >= 0) {
                        msg("L'argument du tour précédent atteint enfin l'autre bout de la table !");
                        use_move(0, -1, queued);
                    }
                } else if (p_slot == 4)
                    use_move(0, -1, 0);
                else
                    use_move(0, p_slot == -2 ? -1 : p_slot, p_slot == -2 ? side[0].charge_move : -1);
            } else {
                if (f_slot == 4)
                    use_move(1, -1, 0);
                else
                    use_move(1, f_slot == -2 ? -1 : f_slot, f_slot == -2 ? side[1].charge_move : -1);
            }
            if (result >= 0)
                break;
            if (faint_check(1 - s) || faint_check(s)) {
                // handled below
            }
        }
        if (result >= 0)
            break;
        // ---- end of turn
        for (int s = 0; s < 2; s++)
            if (side[s].mon->hp > 0)
                end_of_turn(s);
        faint_check(0);
        faint_check(1);

        // ---- faint resolution
        if (side[1].mon->hp == 0) {
            gain_exp();
            int nx = foe_next_alive();
            if (nx < 0) {
                result = BATTLE_WON;
                break;
            }
            if (is_trainer) {
                const TrainerData *t = &trainers[trainer_id];
                msg("%s va envoyer %s.", t->name, species[foe_party[nx].species].name);
                int healthy = 0;
                for (int k = 0; k < g_save.party_count; k++)
                    healthy += g_save.party[k].hp > 0;
                if (healthy > 1) {
                    static const char *const sw[2] = {"Continuer", "Changer d'Euromon"};
                    dlg_say_nowait("", "Changer d'Euromon ?");
                    if (dlg_choice(sw, 2, true) == 1) {
                        int i = choose_switch(false);
                        if (i >= 0) {
                            withdraw_ally();
                            send_out(0, i, true);
                        }
                    }
                }
                send_out(1, nx, true);
            }
        }
        if (side[0].mon->hp == 0) {
            if (party_all_fainted()) {
                result = BATTLE_LOST;
                break;
            }
            int i = choose_switch(true);
            send_out(0, i, true);
        }
        dlg_close();
    }

    // ---- outcome
    if (result == BATTLE_WON) {
        if (is_trainer) {
            const TrainerData *t = &trainers[trainer_id];
            music_play("victory_trainer");
            if (t->portrait)
                portrait_show(SIDE_RIGHT, t->portrait, "worried");
            char who[40];
            snprintf(who, sizeof who, "%s", t->name);
            dlg_say(who, t->defeat);
            int money = t->money * foe_party[foe_count - 1].level;
            g_save.money += money + money_bonus;
            msg("{P} remporte %d € pour ce débat !", money + money_bonus);
            portrait_hide(SIDE_RIGHT);
        } else {
            music_play("victory_wild");
            if (money_bonus) {
                g_save.money += money_bonus;
                msg("{P} ramasse %d € de fonds structurels.", money_bonus);
            }
        }
    } else if (result == BATTLE_LOST) {
        if (is_trainer) {
            const TrainerData *t = &trainers[trainer_id];
            if (t->win && t->win[0]) {
                char who[40];
                snprintf(who, sizeof who, "%s", t->name);
                dlg_say(who, t->win);
            }
        }
    } else if (result == BATTLE_CAUGHT) {
        music_play("victory_wild");
    }
    dlg_close();
    gfx_fade_out(20, false);
    teardown_scene();
    // evolutions after battle
    for (int i = 0; i < g_save.party_count; i++) {
        Mon *m = &g_save.party[i];
        const SpeciesData *s = &species[m->species];
        if (participants[i] && m->hp > 0 && s->evo_into != 0xFFFF && s->evo_level && m->level >= s->evo_level)
            evolve_mon(m, s->evo_into);
    }
    return result;
}

bool battle_trainer(int tr)
{
    is_link = false;
    const TrainerData *t = &trainers[tr];
    is_trainer = true;
    is_wild = false;
    trainer_id = tr;
    foe_count = MIN(6, t->npoke);
    for (int i = 0; i < foe_count; i++)
        mon_create(&foe_party[i], t->party[i * 2], t->party[i * 2 + 1]);
    gimmick = GIM_NONE;
    if (t->portrait) {
        if (!strcmp(t->portrait, "orban")) gimmick = GIM_VETO;
        else if (!strcmp(t->portrait, "lagarde")) gimmick = GIM_TAUX;
        else if (!strcmp(t->portrait, "putin")) gimmick = GIM_LONGTABLE;
        else if (!strcmp(t->portrait, "xi")) gimmick = GIM_RIVAL_SYS;
        else if (!strcmp(t->portrait, "trump")) gimmick = GIM_TRUMP;
        else if (!strcmp(t->portrait, "vdl")) gimmick = GIM_SMS;
    }
    music_play(t->music && t->music[0] ? t->music : "battle_trainer");
    int r = run_battle();
    return r == BATTLE_WON;
}

int battle_wild(int sp, int level)
{
    is_link = false;
    is_trainer = false;
    is_wild = true;
    gimmick = GIM_NONE;
    foe_count = 1;
    mon_create(&foe_party[0], sp, level);
    music_play(sp >= SP_ROMULUS ? "battle_legend" : "battle_wild");
    return run_battle();
}

// ---------------------------------------------------------------- friendly link debates
// 32 bytes per member, explicitly serialized; no native structs/pointers on the wire.
static void team_encode(u8 *b)
{
    memset(b, 0, 193); b[0] = g_save.party_count;
    for (int i = 0; i < b[0]; i++) {
        Mon *m = &g_save.party[i]; u8 *p = b + 1 + i * 32;
        p[0] = m->species; p[1] = m->species >> 8; p[2] = m->level; p[3] = !!m->shiny;
        for (int k = 0; k < 4; k++) p[4 + k] = m->ivs >> (8 * k);
        for (int k = 0; k < 4; k++) { p[8 + 2*k] = m->moves[k]; p[9 + 2*k] = m->moves[k] >> 8; }
    }
}
static bool team_decode(const u8 *b, int n, Mon *team, int *count)
{
    if (n < 1 || b[0] < 1 || b[0] > 6 || n != 1 + b[0] * 32) return false;
    *count = b[0];
    for (int i = 0; i < *count; i++) {
        const u8 *p = b + 1 + i * 32; Mon *m = &team[i];
        int sp = p[0] | p[1] << 8;
        if (sp >= NUM_SPECIES || !p[2] || p[2] > 100 || p[3] > 1) return false;
        memset(m, 0, sizeof *m); m->species = sp; m->level = p[2]; m->shiny = p[3];
        for (int k = 0; k < 4; k++) m->ivs |= (u32)p[4+k] << (8*k);
        m->ivs &= 0x3fffffff; m->friendship = 70;
        m->exp = exp_for_level(species[sp].growth, m->level);
        for (int k = 0; k < 4; k++) {
            int mv = p[8+2*k] | p[9+2*k] << 8;
            if (mv != 0xffff && mv >= NUM_MOVES) return false;
            m->moves[k] = mv;
        }
        mon_heal(m);
    }
    return true;
}
static u32 link_hash_bytes(u32 h, const void *v, int n)
{
    const u8 *b = v;
    while (n--) h = (h ^ *b++) * 16777619u;
    return h;
}
static bool link_check_state(void)
{
    u32 hash = 2166136261u;
    // Hash in server seat order, independent of which player owns this screen.
    for (int seat = 0; seat < 2; seat++) {
        int s = seat ^ link_seat();
        int count = s ? foe_count : g_save.party_count;
        Mon *team = s ? foe_party : g_save.party;
        u8 idx = s ? foe_idx : player_idx;
        hash = link_hash_bytes(hash, &idx, 1);
        hash = link_hash_bytes(hash, team, count * sizeof(Mon));
        hash = link_hash_bytes(hash, side[s].stage, sizeof(Side) - offsetof(Side, stage));
    }
    hash = link_hash_bytes(hash, &link_rng, sizeof link_rng);
    u8 out[4], in[LINK_BODY]; int n;
    for (int k = 0; k < 4; k++) out[k] = hash >> (8*k);
    return link_exchange(LINK_CHECK, out, sizeof out, in, &n) && n == 4 && !memcmp(in, out, 4);
}
static bool link_move_valid(int s, int slot)
{
    Mon *m = side[s].mon;
    if (side[s].charge_move >= 0) return slot == 5;
    bool any = false;
    for (int i = 0; i < 4; i++) if (m->moves[i] != 0xffff && m->pp[i]) any = true;
    if (!any) return slot == 4;
    return slot < 4 && m->moves[slot] != 0xffff && m->pp[slot];
}
static bool link_switch_valid(int s, int idx)
{
    int count = s ? foe_count : g_save.party_count;
    Mon *team = s ? foe_party : g_save.party;
    return idx < count && team[idx].hp && idx != (s ? foe_idx : player_idx);
}
static void link_do_move(int s, int slot)
{
    if (slot == 4) use_move(s, -1, 0);
    else if (slot == 5) use_move(s, -1, side[s].charge_move);
    else use_move(s, slot, -1);
}
static int link_move_id(int s, int slot)
{
    return slot == 4 ? 0 : slot == 5 ? side[s].charge_move : side[s].mon->moves[slot];
}
static bool link_replacements(void)
{
    u8 pick = 255, in[LINK_BODY]; int n;
    if (!side[0].mon->hp) {
        int i = choose_switch(true);
        if (i < 0) return false;
        pick = i;
    }
    if (!link_exchange(LINK_REPLACE, &pick, 1, in, &n) || n != 1) return false;
    if (side[1].mon->hp ? in[0] != 255 : !link_switch_valid(1, in[0])) return false;
    u8 picks[2] = {pick, in[0]};
    for (int seat = 0; seat < 2; seat++) {
        int s = seat ^ link_seat();
        if (picks[s] != 255) send_out(s, picks[s], true);
    }
    return true;
}

int battle_multiplayer(void)
{
    static SaveData backup;
    backup = g_save;
    u8 own[193], other[LINK_BODY]; int n, count;
    team_encode(own);
    if (!link_exchange(LINK_TEAM, own, 1 + own[0] * 32, other, &n) ||
        !team_decode(other, n, foe_party, &foe_count) ||
        !team_decode(own, 1 + own[0] * 32, g_save.party, &count)) {
        g_save = backup;
        msg("Équipe ou connexion invalide."); return BATTLE_FLED;
    }
    is_link = true; is_trainer = is_wild = false; gimmick = GIM_NONE;
    link_rng = link_seed() ? link_seed() : 0x9e3779b9;
    result = -1; money_bonus = 0;
    memset(participants, 0, sizeof participants); memset(side, 0, sizeof side);
    side[0].type_override = side[1].type_override = -1;
    foe_visible = ally_visible = false;
    foe_flash = ally_flash = foe_shake = ally_shake = 0;
    foe_x = FOE_HOME_X; foe_y = FOE_HOME_Y; ally_x = ALLY_HOME_X; ally_y = ALLY_HOME_Y;
    intro_transition(); setup_scene();
    music_play("battle_trainer"); gfx_brightness(false, 0); gfx_brightness(true, 0);
    for (int seat = 0; seat < 2; seat++) send_out(seat ^ link_seat(), 0, true);
    dlg_close();
    while (result < 0 && link_ok()) {
        if (!link_check_state()) break;
        bool lost = party_all_fainted(), won = foe_next_alive() < 0;
        if (lost || won) { result = lost && won ? BATTLE_FLED : lost ? BATTLE_LOST : BATTLE_WON; break; }
        if (!link_replacements()) break;
        u8 action[2] = {255, 0}, in[LINK_BODY];
        while (action[0] == 255 && link_ok()) {
            if (side[0].charge_move >= 0) { action[0] = 0; action[1] = 5; break; }
            int c = main_menu();
            if (c == 0) { int slot = move_menu(); if (slot >= 0) { action[0] = 0; action[1] = slot; } }
            else if (c == 3) { int idx = choose_switch(false); if (idx >= 0) { action[0] = 1; action[1] = idx; } }
            else if (c == 1) msg("Les objets ne sont pas autorisés dans un débat amical.");
            else if (c == 2 || c < 0) { action[0] = 2; action[1] = 0; }
        }
        if (!link_exchange(LINK_ACTION, action, 2, in, &n) || n != 2) break;
        u8 actions[2][2] = {{action[0], action[1]}, {in[0], in[1]}};
        if (in[0] > 2 || (in[0] == 0 && !link_move_valid(1, in[1])) ||
            (in[0] == 1 && !link_switch_valid(1, in[1]))) break;
        if (action[0] == 2 || in[0] == 2) {
            result = action[0] == 2 && in[0] == 2 ? BATTLE_FLED : action[0] == 2 ? BATTLE_LOST : BATTLE_WON;
            break;
        }
        // Switches happen before attacks. Resolve every phase in canonical seat order.
        for (int seat = 0; seat < 2; seat++) {
            int s = seat ^ link_seat();
            if (actions[s][0] == 1) {
                if (s == 0) withdraw_ally();
                send_out(s, actions[s][1], true);
            }
        }
        int order[2] = {link_seat(), 1 ^ link_seat()};
        if (actions[0][0] == 0 && actions[1][0] == 0) {
            int a = order[0], b = order[1];
            int ap = moves[link_move_id(a, actions[a][1])].priority;
            int bp = moves[link_move_id(b, actions[b][1])].priority;
            int as = eff_stat(a, STAT_SPE), bs = eff_stat(b, STAT_SPE);
            if (bp > ap || (bp == ap && (bs > as || (bs == as && battle_random(2))))) {
                order[0] = b; order[1] = a;
            }
        }
        for (int k = 0; k < 2; k++) {
            int s = order[k];
            if (actions[s][0] == 0 && side[s].mon->hp && side[1-s].mon->hp && can_act(s))
                link_do_move(s, actions[s][1]);
        }
        for (int seat = 0; seat < 2; seat++) {
            int s = seat ^ link_seat();
            if (side[s].mon->hp) end_of_turn(s);
            if (!side[s].mon->hp) faint_check(s);
        }
        dlg_close();
    }
    if (result == BATTLE_WON) msg("Vous remportez ce débat amical !");
    else if (result == BATTLE_LOST) msg("L'autre joueur remporte ce débat amical !");
    else msg("Débat terminé ou connexion interrompue.");
    dlg_close(); gfx_fade_out(20, false); teardown_scene();
    g_save = backup; is_link = false;
    return result;
}
