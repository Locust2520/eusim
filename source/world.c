// Overworld: map entering, player control, NPC behaviour, triggers, warps, encounters, trainers.
#include "world.h"
#include "lang.h"
#include "map.h"
#include "actor.h"
#include "script.h"
#include "gfx.h"
#include "ui.h"
#include "canvas.h"
#include "input.h"
#include "audio.h"
#include "dialog.h"
#include "portrait.h"
#include "save.h"
#include "mon.h"
#include "menu.h"
#include "battle.h"
#include "scenes.h"
#include "minigame.h"
#include "note.h"
#include "gen/font_data.h"
#include "gen/flags.h"
#include "gen/maps.h"
#include <time.h>

#define NPC_BASE 1
#define MAP_START MAP_STUDIO
#define START_X 4
#define START_Y 4
static int npc_actor[64];       // map npc index -> actor index
static u16 actor_name[MAX_ACTORS];
static int popup_timer;
static int shake_frames;
static bool quit_to_title;
static int turn_delay;
static int last_heal_map;

// ---------------------------------------------------------------- helpers
static void set_default_heal_point(void)
{
    g_save.heal_map = MAP_CANTINE_BXL;
    g_save.heal_x = 5;
    g_save.heal_y = 4;
}

static int player_sprite(void)
{
    // sprite ids: 0 player_f, 1 player_m (see tools/proc_chars.py CAST order)
    return g_save.player_gender == 0 ? 0 : 1;
}

static bool npc_should_exist(const NpcDef *d)
{
    if (d->hide != 0xFFFF && flag_get(d->hide))
        return false;
    if (d->show != 0xFFFF && !flag_get(d->show))
        return false;
    return true;
}

static void draw_popup(void)
{
    canvas_rect(&g_top, 0, 0, 256, 26, 0);
    if (popup_timer <= 0)
        return;
    int w = MIN(font_width(&font_main, tr(g_map.name)) + 24, 248);   // measured in the player's language
    int slide = popup_timer > 140 ? (popup_timer - 140) * 3 : (popup_timer < 20 ? (20 - popup_timer) * 3 : 0);
    canvas_frame(&g_top, 4, 2 - slide, w, 23, FRAME_DIALOG);
    ui_text_in(&g_top, &font_main, 4, 2 - slide, w - 1, 22, g_map.name, C_BLUE, C_SHADOW, 0);
}

static void update_camera(void)
{
    Actor *p = &g_actors[PLAYER];
    int cx = p->x + 8 - 128, cy = p->y + 8 - 96;
    if (shake_frames > 0) {
        cx += (shake_frames & 2) ? 3 : -3;
        shake_frames--;
    }
    map_set_camera(cx, cy);
}

static void render(void)
{
    update_camera();
    actors_render();
    map_animate();
    if (popup_timer > 0) {
        popup_timer--;
        if (popup_timer % 3 == 0 || popup_timer == 0)
            draw_popup();
    }
}

// NPC idle behaviour
static void npc_ai(void)
{
    for (int i = 1; i < MAX_ACTORS; i++) {
        Actor *a = &g_actors[i];
        if (!a->active || !a->visible || a->frozen || actor_moving(i))
            continue;
        if (--a->timer > 0)
            continue;
        a->timer = 60 + rng_range(120);
        switch (a->move) {
        case MOVE_LOOK:
            a->dir = rng_range(4);
            break;
        case MOVE_SPIN:
            a->dir = (a->dir + 1) & 3;
            a->timer = 40;
            break;
        case MOVE_WANDER: {
            int d = rng_range(4);
            int nx = a->tx + dir_dx[d], ny = a->ty + dir_dy[d];
            if (abs(nx - a->home_x) <= 2 && abs(ny - a->home_y) <= 2 &&
                !(nx == g_actors[PLAYER].tx && ny == g_actors[PLAYER].ty))
                actor_step(i, d, 1, true);
            else
                a->dir = d;
            break;
        }
        case MOVE_WALK_H:
        case MOVE_WALK_V: {
            int d = a->move == MOVE_WALK_H ? (a->tx < a->home_x + 2 ? DIR_RIGHT : DIR_LEFT)
                                          : (a->ty < a->home_y + 2 ? DIR_DOWN : DIR_UP);
            if (a->tx >= a->home_x + 2 && a->move == MOVE_WALK_H)
                d = DIR_LEFT;
            if (!actor_step(i, d, 1, true))
                a->dir = d;
            a->timer = 30;
            break;
        }
        default:
            break;
        }
    }
}

void world_wait(int frames)
{
    for (int i = 0; i < frames; i++) {
        actors_update();
        render();
        frame_wait();
    }
}

static void wait_actor(int a)
{
    while (a >= 0 && actor_moving(a)) {
        actors_update();
        render();
        frame_wait();
    }
}

// ---------------------------------------------------------------- bottom screen
void world_redraw_bottom(void)
{
    menu_draw_panel();
}

// ---------------------------------------------------------------- map entering
static void spawn_npcs(void)
{
    for (int i = 0; i < 64; i++)
        npc_actor[i] = -1;
    for (int i = 0; i < g_map.nnpcs && i < 64; i++) {
        const NpcDef *d = &g_map.npcs[i];
        if (!npc_should_exist(d))
            continue;
        int a = actor_spawn(d->sprite, d->x, d->y, d->dir == DIR_KEEP ? DIR_DOWN : d->dir);
        if (a < 0)
            break;
        Actor *ac = &g_actors[a];
        ac->npc_index = i;
        ac->move = d->move;
        ac->home_x = d->x;
        ac->home_y = d->y;
        ac->script = d->script;
        ac->trainer = d->trainer;
        ac->range = d->range;
        ac->timer = rng_range(90);
        actor_name[a] = d->name;
        npc_actor[i] = a;
    }
}

static void enter_map(int map, int x, int y, int dir)
{
    portrait_hide_all();
    dlg_close();
    actors_reset();
    memset(actor_name, 0, sizeof actor_name);
    gfx_clear_scene(false);
    canvas_clear(&g_top, 0);
    if (!map_load(map))
        fatal("Carte %d introuvable", map);
    g_save.map = map;
    g_save.x = x;
    g_save.y = y;
    if (dir != DIR_KEEP)
        g_save.dir = dir;
    actor_set_sprite(PLAYER, player_sprite());
    Actor *p = &g_actors[PLAYER];
    p->tx = x;
    p->ty = y;
    p->x = x * 16;
    p->y = y * 16;
    p->dir = g_save.dir;
    p->npc_index = -1;
    spawn_npcs();
    map_draw_all();
    update_camera();
    actors_render();
    if (g_map.music[0])
        music_play(g_map.music);
    popup_timer = (g_map.flags & MAPF_OUTDOOR) || last_heal_map != map ? 160 : 0;
    world_redraw_bottom();
}

void world_check_special_day(void)
{
    // 9 May, Europe Day: Schumark appears in Brussels (once)
    time_t now = time(NULL);
    struct tm *tmv = localtime(&now);
    if (tmv && tmv->tm_mon == 4 && tmv->tm_mday == 9 && g_map.id == MAP_BRUXELLES && flag_get(FLAG_GOT_STARTER) &&
        !flag_get(FLAG_FETE_EUROPE))
        script_run(SCRIPT_FETE_EUROPE);
}

void world_warp(int map, int x, int y, int dir, bool fade)
{
    if (fade)
        gfx_fade_out(12, false);
    enter_map(map, x, y, dir);
    if (fade) {
        for (int i = 16; i >= 0; i -= 2) {
            gfx_brightness(false, -i);
            gfx_brightness(true, -i);
            render();
            frame_wait();
        }
    }
    if (g_map.onload != 0xFFFF)
        script_run(g_map.onload);
#if defined(QUICKSTART) && defined(QSCRIPT_MAP)
    script_run(QSCRIPT_MAP);   // screenshot rig: an NPC script on its own map
#endif
    world_check_special_day();
}

void world_refresh(void)
{
    // re-upload everything after a full screen scene
    int map = g_save.map;
    int x = g_actors[PLAYER].tx, y = g_actors[PLAYER].ty, d = g_actors[PLAYER].dir;
    // keep NPC positions: remember them
    int nx[MAX_ACTORS], ny[MAX_ACTORS], nd[MAX_ACTORS];
    bool vis[MAX_ACTORS], act[MAX_ACTORS];
    for (int i = 0; i < MAX_ACTORS; i++) {
        nx[i] = g_actors[i].tx;
        ny[i] = g_actors[i].ty;
        nd[i] = g_actors[i].dir;
        vis[i] = g_actors[i].visible;
        act[i] = g_actors[i].active;
    }
    u16 names[MAX_ACTORS];
    memcpy(names, actor_name, sizeof names);
    int sprites[MAX_ACTORS];
    for (int i = 0; i < MAX_ACTORS; i++)
        sprites[i] = g_actors[i].sprite;
    Actor saved[MAX_ACTORS];
    memcpy(saved, g_actors, sizeof saved);
    // reload map gfx
    gfx_clear_scene(false);
    map_load(map);
    actors_reset();
    actor_set_sprite(PLAYER, player_sprite());
    for (int i = 1; i < MAX_ACTORS; i++) {
        if (!act[i])
            continue;
        int a = actor_spawn(sprites[i], nx[i], ny[i], nd[i]);
        if (a < 0)
            continue;
        Actor keep = g_actors[a];
        g_actors[a] = saved[i];
        g_actors[a].gfx = keep.gfx;
        g_actors[a].slot = keep.slot;
        g_actors[a].cur_frame = -1;
        g_actors[a].x = nx[i] * 16;
        g_actors[a].y = ny[i] * 16;
        g_actors[a].step_frames = 0;
        g_actors[a].visible = vis[i];
        actor_name[a] = names[i];
        if (saved[i].npc_index >= 0 && saved[i].npc_index < 64)
            npc_actor[saved[i].npc_index] = a;
    }
    Actor *p = &g_actors[PLAYER];
    p->tx = x;
    p->ty = y;
    p->x = x * 16;
    p->y = y * 16;
    p->dir = d;
    p->step_frames = 0;
    map_draw_all();
    update_camera();
    actors_render();
    canvas_clear(&g_top, 0);
    world_redraw_bottom();
    if (g_map.music[0])
        music_play(g_map.music);
}

// ---------------------------------------------------------------- script helpers
int world_actor_by_name(u16 hash)
{
    if (hash == 0)
        return PLAYER;
    for (int i = 1; i < MAX_ACTORS; i++)
        if (g_actors[i].active && actor_name[i] == hash)
            return i;
    return -1;
}

void world_move_actor(int a, const char *path, bool wait)
{
    if (a < 0)
        return;
    const char *s = path;
    while (*s) {
        while (*s == ' ')
            s++;
        if (!*s)
            break;
        char c = *s++;
        int n = 0;
        while (*s >= '0' && *s <= '9')
            n = n * 10 + (*s++ - '0');
        if (n == 0)
            n = 1;
        int d = c == 'U' ? DIR_UP : c == 'D' ? DIR_DOWN : c == 'L' ? DIR_LEFT : c == 'R' ? DIR_RIGHT : -1;
        if (c == 'W') {
            world_wait(n * 8);
            continue;
        }
        if (c == 'J') {
            actor_jump(a, g_actors[a].dir);
            wait_actor(a);
            continue;
        }
        if (d < 0)
            continue;
        for (int k = 0; k < n; k++) {
            wait_actor(a);
            // the player is never pushed into a wall or a hedge (e.g. "move player D" in front of a locked door)
            if (!actor_step(a, d, 2, a == PLAYER)) {
                g_actors[a].dir = d;
                break;
            }
            if (wait || k < n - 1)
                wait_actor(a);
        }
    }
    if (wait)
        wait_actor(a);
}

void world_face_actor(int a, int dir)
{
    if (a < 0)
        return;
    Actor *p = &g_actors[PLAYER];
    if (dir == 4) {
        Actor *t = &g_actors[a];
        int dx = p->tx - t->tx, dy = p->ty - t->ty;
        if (abs(dx) > abs(dy))
            t->dir = dx > 0 ? DIR_RIGHT : DIR_LEFT;
        else
            t->dir = dy > 0 ? DIR_DOWN : DIR_UP;
    } else if (dir == 5) {
        Actor *t = &g_actors[a];
        int dx = t->tx - p->tx, dy = t->ty - p->ty;
        if (abs(dx) > abs(dy))
            p->dir = dx > 0 ? DIR_RIGHT : DIR_LEFT;
        else
            p->dir = dy > 0 ? DIR_DOWN : DIR_UP;
    } else
        g_actors[a].dir = dir;
    render();
}

void world_spawn(u16 name, int sprite, int x, int y, int dir)
{
    int a = actor_spawn(sprite, x, y, dir);
    if (a >= 0) {
        actor_name[a] = name;
        g_actors[a].move = MOVE_STILL;
    }
}

void world_despawn(u16 name)
{
    int a = world_actor_by_name(name);
    if (a > 0) {
        actor_remove(a);
        actor_name[a] = 0;
    }
}

void world_give_mon(int sp, int lv)
{
    Mon m;
    mon_create(&m, sp, lv);
    int r = party_add(&m);
    char buf[128];
    snprintf(buf, sizeof buf, T("{P} received %s!"), species[sp].name);
    music_pause(true);
    sfx_play(SFX_CAPTURE_OK);
    dlg_say("", buf);
    music_pause(false);
    if (r == 1)
        dlg_say("", "Your team is full: it goes to the Archives.");
}

void world_heal_party(void)
{
    party_heal_all();
    music_pause(true);
    sfx_play(SFX_HEAL);
    world_wait(70);
    music_pause(false);
}

void world_fanfare(const char *song)
{
    char prev[24];
    strncpy(prev, music_current(), sizeof prev - 1);
    prev[sizeof prev - 1] = 0;
    music_play(song);
    for (int i = 0; i < 600 && music_is_playing(); i++) {
        render();
        frame_wait();
        if (i > 60 && (g_kdown & KEY_A))
            break;
    }
    if (prev[0])
        music_play(prev);
}

void world_screenshake(int frames)
{
    shake_frames = frames;
    world_wait(frames);
}

void world_loading(int frames)
{
    loading_screen(frames);
    world_refresh();
    gfx_brightness(false, 0);
    gfx_brightness(true, 0);
}

static void set_battle_bg(void)
{
    extern int g_battle_bg_hint;
    if (g_map.id == MAP_GYM_HEMICYCLE)
        g_battle_bg_hint = 2;
    else if (g_map.flags & MAPF_DARK)
        g_battle_bg_hint = 4;
    else if (!(g_map.flags & MAPF_OUTDOOR))
        g_battle_bg_hint = 1;
    else if (g_map.city != 255 && g_map.enc_table == 0xFFFF)
        g_battle_bg_hint = 3;
    else
        g_battle_bg_hint = 0;
}

bool world_battle_trainer(int tr, bool nolose)
{
    set_battle_bg();
    bool win = battle_trainer(tr);
    world_refresh();
    // Battle teardown leaves both screens black; show the loss dialogue too.
    gfx_brightness(false, 0);
    gfx_brightness(true, 0);
    if (!win && !nolose) {
        // blackout -> back to last cantine
        world_blackout();
        return false;
    }
    if (win)
        flag_set(FLAG_TRAINER_BASE + tr, true);
    return win;
}

bool world_battle_wild(int sp, int lv, bool scripted)
{
    set_battle_bg();
    int r = battle_wild(sp, lv);
    world_refresh();
    gfx_brightness(false, 0);
    gfx_brightness(true, 0);
    if (r == BATTLE_LOST) {
        world_blackout();
        return false;
    }
    (void)scripted;
    return r == BATTLE_WON || r == BATTLE_CAUGHT;
}

void world_blackout(void)
{
    dlg_say("", "{P} has no Euromon fit to debate…\f{P} runs back to the canteen, head down.");
    dlg_close();
    g_save.money /= 2;
    gfx_fade_out(30, false);
    party_heal_all();
    // Older saves used the studio until the first canteen visit.
    if (g_save.heal_map == MAP_STUDIO)
        set_default_heal_point();
    world_warp(g_save.heal_map, g_save.heal_x, g_save.heal_y, DIR_UP, false);
    gfx_fade_in(20, false);
    dlg_say("Canteen lady", "There you go, a good coffee and you're off again! Your Euromons are in great shape.");
    dlg_close();
}

int world_minigame(int id)
{
    int r = minigame_run(id);
    world_refresh();
    gfx_brightness(false, 0);
    gfx_brightness(true, 0);
    return r;
}

void world_badge_ceremony(int b)
{
    static const char *const names[8] = {"Tax Ruling Badge", "Euro Badge", "Hemicycle Badge", "OXI Badge",
                                         "Article 50 Badge", "Veto Badge", "Fine Badge", "Sorbonne Badge"};
    char buf[96];
    snprintf(buf, sizeof buf, T("{P} received the %s!"), tr(names[(b - 1) & 7]));
    music_pause(true);
    sfx_play(SFX_LEVELUP);
    dlg_say("", buf);
    music_pause(false);
    world_redraw_bottom();
}

void world_special(int id, int arg)
{
    switch (id) {
    case 0: shop_open(arg); world_refresh(); break;
    case 1: archives_open(); world_refresh(); break;
    case 2: {
        char buf[256];
        int n = dex_count_caught();
        snprintf(buf, sizeof buf, T("Your Eurodex has %d Euromons caught out of %d seen."), n, dex_count_seen());
        dlg_say("Jean Monnet", buf);
        dlg_say("Jean Monnet", n < 10 ? "It's a start! Small steps make great unions." :
                               n < 40 ? "Not bad! You're moving faster than the daylight saving directive." :
                               n < 80 ? "Impressive! Not even the Commission has that many files." :
                                        "Extraordinary! You're a real institution all by yourself.");
        break;
    }
    case 3: case 11: ending_run(); world_refresh(); break;
    case 22: train_menu(); break;
    case 23: jukebox_open(); world_refresh(); break;
    case 24: g_save.vars[VAR_RESULT] = note_studio(); world_refresh(); break;
    case 25: note_view(); break;
    case 27: {
        static const int cards[12] = {FLAG_CARD_CALLAS, FLAG_CARD_BEETHOVEN, FLAG_CARD_CURIE, FLAG_CARD_CERVANTES,
                                      FLAG_CARD_LEONARDO, FLAG_CARD_SUTTNER, FLAG_CARD_WALLCREEPER, FLAG_CARD_KINGFISHER,
                                      FLAG_CARD_BEE_EATER, FLAG_CARD_STORK, FLAG_CARD_AVOCET, FLAG_CARD_GANNET};
        int n = 0;
        for (int i = 0; i < 12; i++)
            n += flag_get(cards[i]);
        char buf[96];
        snprintf(buf, sizeof buf, T("Jury postcards: %d of 12."), n);
        dlg_say("", buf);
        if (n == 12) {
            flag_set(FLAG_ALBUM_DONE, true);
            dlg_say("", "That's all twelve motifs! Eleni, in the ECB studio in Frankfurt, will want to see them.");
        }
        break;
    }
    case 26: {
        int code = keypad_code(arg ? arg : 4);
        g_save.vars[VAR_RESULT] = code < 0 ? 0 : code;
        break;
    }
    case 5: menu_save(); break;
    case 6: world_heal_party(); break;
    case 7: popup_timer = 160; break;
    case 8: viewer_open("text/sources.txt", "Fact sources"); world_refresh(); break;
    case 9:
        g_save.heal_map = g_save.map;
        g_save.heal_x = g_actors[PLAYER].tx;
        g_save.heal_y = g_actors[PLAYER].ty;
        last_heal_map = g_save.map;
        break;
    case 10: badge_case_open(); world_refresh(); break;
    case 16: quit_to_title = true; break;
    default: break;
    }
}

// ---------------------------------------------------------------- interaction
static int facing_tile(int *fx, int *fy)
{
    Actor *p = &g_actors[PLAYER];
    *fx = p->tx + dir_dx[p->dir];
    *fy = p->ty + dir_dy[p->dir];
    return map_behavior(*fx, *fy);
}

static void talk_to(int a)
{
    Actor *n = &g_actors[a];
    int olddir = n->dir;
    world_face_actor(a, 4);
    n->frozen = true;
    g_script_actor = a;
    if (n->trainer != 0xFFFF && !flag_get(FLAG_TRAINER_BASE + n->trainer)) {
        trainer_encounter(a, false);
    } else if (n->script != 0xFFFF) {
        script_run(n->script);
    }
    n->frozen = false;
    if (n->move == MOVE_STILL)
        n->dir = olddir == n->dir ? n->dir : n->dir;
}

static bool interact(void)
{
    int fx, fy;
    int b = facing_tile(&fx, &fy);
    int a = actor_at(fx, fy, PLAYER);
    if (a > 0) {
        talk_to(a);
        return true;
    }
    if (b == B_COUNTER || b == B_HEAL || b == B_SHOP || b == B_SOLID) {
        // talk across counters and desks (the canteen lady stands behind the coffee machine)
        Actor *p = &g_actors[PLAYER];
        int a2 = actor_at(fx + dir_dx[p->dir], fy + dir_dy[p->dir], PLAYER);
        if (a2 > 0) {
            talk_to(a2);
            return true;
        }
    }
    const Sign *s = map_sign_at(fx, fy);
    if (s) {
        g_script_actor = 0;
        script_run(s->script);
        return true;
    }
    for (int i = 0; i < g_map.nitems; i++) {
        const ItemDef *it = &g_map.items[i];
        if (it->x == fx && it->y == fy && !flag_get(it->flag)) {
            flag_set(it->flag, true);
            bag_add(it->item, 1);
            char buf[96];
            snprintf(buf, sizeof buf, T("{P} found: %s!"), items[it->item].name);
            sfx_play(SFX_COIN);
            dlg_say("", buf);
            dlg_close();
            return true;
        }
    }
    if (b == B_PC) {
        archives_open();
        world_refresh();
        return true;
    }
    return false;
}

// trainer line-of-sight
void trainer_encounter(int a, bool spotted)
{
    Actor *n = &g_actors[a];
    const TrainerData *t = &trainers[n->trainer];
    if (spotted) {
        music_play(t->music && t->music[0] ? t->music : "encounter");
        actor_emote(a, EMOTE_EXCL, 40);
        sfx_play(SFX_ALARM);
        world_wait(40);
        // walk to the player
        Actor *p = &g_actors[PLAYER];
        while (abs(n->tx - p->tx) + abs(n->ty - p->ty) > 1) {
            actor_step(a, n->dir, 2, false);
            wait_actor(a);
        }
        world_face_actor(PLAYER, 5);
    }
    if (t->portrait)
        portrait_show(SIDE_RIGHT, t->portrait, "neutral");
    char who[48];
    snprintf(who, sizeof who, "%s", t->name);
    dlg_say(who, t->intro);
    dlg_close();
    portrait_hide_all();
    world_battle_trainer(n->trainer, false);
    if (flag_get(FLAG_TRAINER_BASE + n->trainer) && n->script != 0xFFFF)
        script_run(n->script);
}

static bool check_trainers(void)
{
    Actor *p = &g_actors[PLAYER];
    for (int i = 1; i < MAX_ACTORS; i++) {
        Actor *n = &g_actors[i];
        if (!n->active || !n->visible || n->trainer == 0xFFFF || flag_get(FLAG_TRAINER_BASE + n->trainer))
            continue;
        int dx = dir_dx[n->dir], dy = dir_dy[n->dir];
        for (int k = 1; k <= n->range; k++) {
            int x = n->tx + dx * k, y = n->ty + dy * k;
            if (x == p->tx && y == p->ty) {
                n->frozen = true;
                trainer_encounter(i, true);
                n->frozen = false;
                return true;
            }
            int b = map_behavior(x, y);
            if (b == B_SOLID || b == B_WATER || b == B_COUNTER || actor_at(x, y, i) >= 0)
                break;
        }
    }
    return false;
}

static bool check_triggers(void)
{
    Actor *p = &g_actors[PLAYER];
    for (int i = 0; i < g_map.ntrigs; i++) {
        const Trigger *t = &g_map.trigs[i];
        if (p->tx >= t->x && p->tx < t->x + t->w && p->ty >= t->y && p->ty < t->y + t->h) {
            if (t->cflag != 0xFFFF && flag_get(t->cflag) != (bool)t->cval)
                continue;
            g_script_actor = 0;
            script_run(t->script);
            return true;
        }
    }
    return false;
}

static bool check_warp(void)
{
    Actor *p = &g_actors[PLAYER];
    const Warp *w = map_warp_at(p->tx, p->ty);
    if (!w)
        return false;
    sfx_play(w->kind ? SFX_DOOR : SFX_WHOOSH);
    world_warp(w->map, w->dx, w->dy, w->dir, true);
    return true;
}

static bool check_encounter(void)
{
    Actor *p = &g_actors[PLAYER];
    int b = map_behavior(p->tx, p->ty);
    if (b != B_GRASS && b != B_CARPET)
        return false;
    if (g_map.enc_table == 0xFFFF || g_map.enc_table >= NUM_ENC)
        return false;
    if (g_save.repel > 0) {
        g_save.repel--;
        if (g_save.repel == 0)
            dlg_notice("The Non-Solicitation Clause has expired.");
        return false;
    }
    const EncTable *e = &enc_tables[g_map.enc_table];
    if (rng_range(100) >= e->rate)
        return false;
    {
        // the day the clocks change, Changheure shows up everywhere
        time_t now = time(NULL);
        struct tm *tmv = localtime(&now);
        if (tmv && (tmv->tm_mon == 2 || tmv->tm_mon == 9) && tmv->tm_wday == 0 && tmv->tm_mday > 24 &&
            rng_range(100) < 30) {
            world_battle_wild(SP_CHANGHEURE, 10 + g_save.badges * 0 + party_first_alive() * 0 + 5 * dex_count_caught() / 20, false);
            return true;
        }
    }
    int total = 0;
    for (int i = 0; i < e->n; i++)
        total += e->slots[i].weight;
    int r = rng_range(total);
    for (int i = 0; i < e->n; i++) {
        r -= e->slots[i].weight;
        if (r < 0) {
            const EncSlot *s = &e->slots[i];
            int lv = s->min + rng_range(s->max - s->min + 1);
            world_battle_wild(s->species, lv, false);
            return true;
        }
    }
    return false;
}

static void after_step(void)
{
    g_save.x = g_actors[PLAYER].tx;
    g_save.y = g_actors[PLAYER].ty;
    // Exit guards must run before a warp on the same tile.
    if (check_triggers())
        return;
    if (check_warp())
        return;
    if (check_trainers())
        return;
    check_encounter();
}

// ---------------------------------------------------------------- main loop
void world_new_game(void)
{
    g_save.map = MAP_START;
    g_save.x = START_X;
    g_save.y = START_Y;
    g_save.dir = DIR_UP;
    set_default_heal_point();
    g_save.money = 500;
}

void world_run(void)
{
    quit_to_title = false;
    last_heal_map = -1;
    gfx_brightness(false, -16);
    gfx_brightness(true, -16);
    enter_map(g_save.map, g_save.x, g_save.y, g_save.dir);
    for (int i = 16; i >= 0; i -= 2) {
        gfx_brightness(false, -i);
        gfx_brightness(true, -i);
        render();
        frame_wait();
    }
    if (g_map.onload != 0xFFFF)
        script_run(g_map.onload);
    world_check_special_day();
    bool was_moving = false;
    while (!quit_to_title) {
        g_save.play_frames++;
        Actor *p = &g_actors[PLAYER];
        if (!actor_moving(PLAYER)) {
            if (was_moving) {
                was_moving = false;
                after_step();
                if (quit_to_title)
                    break;
                continue;
            }
            int act = menu_panel_input();
            if (act >= 0) {
                menu_open(act);
                world_redraw_bottom();
                if (quit_to_title)
                    break;
            } else if (g_kdown & KEY_A) {
                interact();
            } else {
                int d = -1;
                if (g_kheld & KEY_UP) d = DIR_UP;
                else if (g_kheld & KEY_DOWN) d = DIR_DOWN;
                else if (g_kheld & KEY_LEFT) d = DIR_LEFT;
                else if (g_kheld & KEY_RIGHT) d = DIR_RIGHT;
                if (d >= 0) {
                    if (p->dir != d && (g_kdown & (KEY_UP | KEY_DOWN | KEY_LEFT | KEY_RIGHT))) {
                        p->dir = d;
                        turn_delay = 5;
                    } else if (turn_delay > 0) {
                        turn_delay--;
                    } else {
                        int nx = p->tx + dir_dx[d], ny = p->ty + dir_dy[d];
                        int b = map_behavior(nx, ny);
                        bool run = (g_kheld & KEY_B) != 0;
                        if (b == B_LEDGE_D && d == DIR_DOWN && actor_at(nx, ny + 1, PLAYER) < 0) {
                            actor_jump(PLAYER, d);
                            was_moving = true;
                        } else if (actor_step(PLAYER, d, run ? 4 : 2, true)) {
                            was_moving = true;
                        } else {
                            // bump: door/warp in front of a wall (e.g. stairs, exits at map edge)
                            const Warp *w = map_warp_at(nx, ny);
                            if (w && (b == B_DOOR || b == B_STAIRS)) {
                                sfx_play(SFX_DOOR);
                                world_warp(w->map, w->dx, w->dy, w->dir, true);
                            } else if ((g_frame & 15) == 0)
                                sfx_play(SFX_BUMP);
                        }
                    }
                }
            }
        } else
            was_moving = true;
        npc_ai();
        actors_update();
        render();
        frame_wait();
    }
    music_fade_out(30);
    gfx_fade_out(30, false);
    actors_reset();
    portrait_hide_all();
    canvas_clear(&g_top, 0);
    canvas_clear(&g_bot, 0);
}

#include "gen/europe.h"
const char *world_city_key(void)
{
    static int last = -1;
    if (g_map.city < NUM_EUROPE_CITIES)
        last = g_map.city;
    return last >= 0 ? europe_cities[last].key : NULL;
}

// ---------------------------------------------------------------- train (Interrail)
typedef struct { const char *label; int map, x, y; int flag; } TrainDest;

void train_menu(void)
{
    const TrainDest all[] = {
        {"Brussels", MAP_BRUXELLES, 38, 26, FLAG_TRAIN_BRUXELLES},
        {"Luxembourg", MAP_LUXEMBOURG, 32, 23, FLAG_TRAIN_LUXEMBOURG},
        {"Frankfurt", MAP_FRANCFORT, 32, 22, FLAG_TRAIN_FRANCFORT},
        {"Strasbourg", MAP_STRASBOURG, 8, 22, FLAG_TRAIN_STRASBOURG},
        {"Athens", MAP_ATHENES, 7, 20, FLAG_TRAIN_ATHENES},
        {"London", MAP_LONDRES, 7, 20, FLAG_TRAIN_LONDRES},
        {"Budapest", MAP_BUDAPEST, 7, 20, FLAG_TRAIN_BUDAPEST},
        {"Paris", MAP_PARIS, 7, 20, FLAG_TRAIN_PARIS},
        {"Antwerp", MAP_ANVERS, 7, 16, FLAG_TRAIN_ANVERS},
        {"Warsaw", MAP_VARSOVIE, 7, 21, FLAG_TRAIN_VARSOVIE},
        {"Rome", MAP_ROME, 6, 13, FLAG_TRAIN_ROME},
        {"Maastricht", MAP_MAASTRICHT, 6, 13, FLAG_TRAIN_MAASTRICHT},
        {"Lisbon", MAP_LISBONNE, 6, 13, FLAG_TRAIN_LISBONNE},
    };
    const TrainDest *list[16];
    int n = 0;
    for (unsigned i = 0; i < ARRAY_LEN(all); i++)
        if (flag_get(all[i].flag) && all[i].map != g_save.map)
            list[n++] = &all[i];
    if (n == 0) {
        dlg_say("Ticket clerk", "No destination available for now.");
        dlg_close();
        return;
    }
    int page = 0;
    while (1) {
        const char *opts[7];
        int k = 0, base = page * 5;
        for (int i = base; i < n && k < 5; i++)
            opts[k++] = list[i]->label;
        int has_more = base + 5 < n;
        if (has_more)
            opts[k++] = "Other destinations…";
        opts[k++] = "Cancel";
        int c = dlg_choice(opts, k, true);
        if (c < 0 || c == k - 1)
            return;
        if (has_more && c == k - 2) {
            page++;
            continue;
        }
        if (!has_more && page > 0 && c == k - 1)
            return;
        const TrainDest *d = list[base + c];
        sfx_play(SFX_TRAIN);
        dlg_say("Ticket clerk", "All aboard! The train is leaving… only a few minutes late.");
        dlg_close();
        loading_screen(70);
        world_warp(d->map, d->x, d->y, DIR_DOWN, false);
        gfx_brightness(false, 0);
        gfx_brightness(true, 0);
        return;
    }
}

#ifdef QUICKSTART
// Test helper: show every map for 2 seconds (centre camera on the map middle)
void world_map_tour(void)
{
    for (int m = 0; m < NUM_MAPS; m++) {
        enter_map(m, 1, 1, DIR_DOWN);
        g_actors[PLAYER].visible = false;
        int cx = g_map.w * 8 - 128, cy = g_map.h * 8 - 96;
        for (int f = 0; f < 120; f++) {
            map_set_camera(cx, cy);
            actors_render();
            frame_wait();
        }
    }
}
#endif
