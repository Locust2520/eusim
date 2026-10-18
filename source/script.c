// Event script virtual machine (bytecode compiled by tools/mkscripts.py). Runs synchronously:
// every command that needs time (dialogue, movement, battles) blocks while rendering the world.
#include "script.h"
#include "lang.h"
#include "world.h"
#include "fs.h"
#include "dialog.h"
#include "portrait.h"
#include "cine.h"
#include "audio.h"
#include "save.h"
#include "mon.h"
#include "actor.h"
#include "map.h"
#include "gfx.h"
#include "canvas.h"
#include "scenes.h"
#include "gen/flags.h"

enum {
    OP_END, OP_SAY, OP_ASK, OP_CLOSE, OP_SHOW, OP_EXPR, OP_HIDE, OP_FOCUS, OP_CHOICE, OP_GOTO,
    OP_IF_FLAG, OP_IF_VAR, OP_SETFLAG, OP_SETVAR, OP_ADDVAR, OP_GIVEMON, OP_GIVEITEM, OP_TAKEITEM, OP_MONEY, OP_HEAL,
    OP_BATTLE, OP_WILD, OP_MUSIC, OP_SFX, OP_WAIT, OP_FADE, OP_SCREENSHAKE, OP_WARP, OP_MOVE, OP_FACE,
    OP_EMOTE, OP_NPCVIS, OP_LOCK, OP_RELEASE, OP_MINIGAME, OP_BADGE, OP_CHAPTER, OP_LOADING, OP_IF_MONEY, OP_IF_ITEM,
    OP_CALL, OP_SPECIAL, OP_STRVAR, OP_FANFARE, OP_SHAKE, OP_IF_BADGE, OP_NOTICE, OP_RANDOM, OP_IF_GENDER, OP_SPAWN,
    OP_DESPAWN, OP_IF_PARTY, OP_YESNO, OP_CINE, OP_SLIDE, OP_CARD,
};

static u8 *bank;
static u32 *offs, *soffs;
static int nscripts, nstrings;
static int depth;
static bool battle_aborted;
int g_script_actor;

void script_init(void)
{
    u32 size;
    bank = fs_load("scripts.bin", &size);
    if (memcmp(bank, "SCR1", 4) != 0)
        fatal("Bad scripts.bin");
    nscripts = bank[4] | (bank[5] << 8);
    nstrings = bank[6] | (bank[7] << 8);
    offs = (u32 *)(bank + 8);
    soffs = offs + nscripts;
}

const char *script_string(int idx)
{
    if (idx < 0 || idx >= nstrings)
        return "";
    return tr((const char *)bank + soffs[idx]);
}

bool script_running(void) { return depth > 0; }

static int rd8(const u8 **p) { return *(*p)++; }
static int rd16(const u8 **p)
{
    int v = (*p)[0] | ((*p)[1] << 8);
    *p += 2;
    return v;
}
static s32 rd32(const u8 **p)
{
    s32 v = (*p)[0] | ((*p)[1] << 8) | ((*p)[2] << 16) | ((u32)(*p)[3] << 24);
    *p += 4;
    return v;
}

static void give_item_msg(int item, int n)
{
    bag_add(item, n);
    char buf[128];
    if (n > 1)
        snprintf(buf, sizeof buf, T("{P} obtient %d × %s !"), n, items[item].name);
    else
        snprintf(buf, sizeof buf, T("{P} obtient : %s !"), items[item].name);
    music_pause(true);
    sfx_play(SFX_LEVELUP);
    dlg_say("", buf);
    music_pause(false);
}

void script_run(int id)
{
    if (id < 0 || id >= nscripts)
        return;
    if (depth == 0)
        battle_aborted = false;
    depth++;
    const u8 *base = bank + offs[id];
    const u8 *p = base;
    bool running = true;
    while (running && !battle_aborted) {
        int op = rd8(&p);
        switch (op) {
        case OP_END:
            running = false;
            break;
        case OP_SAY:
        case OP_ASK: {
            const char *who = script_string(rd16(&p));
            const char *txt = script_string(rd16(&p));
            if (op == OP_SAY)
                dlg_say(who, txt);
            else
                dlg_say_nowait(who, txt);
            break;
        }
        case OP_CLOSE:
            dlg_close();
            break;
        case OP_SHOW: {
            int side = rd8(&p);
            const char *who = script_string(rd16(&p));
            const char *ex = script_string(rd16(&p));
            portrait_show(side, who, ex);
            portrait_focus(side);
            break;
        }
        case OP_EXPR: {
            int side = rd8(&p);
            portrait_expr(side, script_string(rd16(&p)));
            portrait_focus(side);
            break;
        }
        case OP_HIDE: {
            int side = rd8(&p);
            if (side == 2)
                portrait_hide_all();
            else
                portrait_hide(side);
            break;
        }
        case OP_FOCUS: {
            int side = rd8(&p);
            portrait_focus(side == 255 ? -1 : side);
            break;
        }
        case OP_SHAKE: {
            int side = rd8(&p);
            portrait_shake(side, rd8(&p));
            break;
        }
        case OP_CHOICE: {
            int n = rd8(&p);
            const char *opts[8];
            for (int i = 0; i < n; i++)
                opts[i] = script_string(rd16(&p));
            int var = rd8(&p);
            int r = dlg_choice(opts, n, false);
            g_save.vars[var] = r;
            break;
        }
        case OP_YESNO: {
            int var = rd8(&p);
            g_save.vars[var] = dlg_yesno() ? 1 : 0;
            break;
        }
        case OP_GOTO:
            p = base + rd16(&p);
            break;
        case OP_IF_FLAG: {
            int f = rd16(&p), v = rd8(&p), to = rd16(&p);
            if (flag_get(f) == (bool)v)
                p = base + to;
            break;
        }
        case OP_IF_VAR: {
            int var = rd8(&p), o = rd8(&p), val = rd16(&p), to = rd16(&p);
            int cur = g_save.vars[var];
            bool ok = (o == 0 && cur == val) || (o == 1 && cur != val) || (o == 2 && cur < val) || (o == 3 && cur >= val);
            if (ok)
                p = base + to;
            break;
        }
        case OP_IF_BADGE: {
            int b = rd8(&p), to = rd16(&p);
            if (g_save.badges & (1 << (b - 1)))
                p = base + to;
            break;
        }
        case OP_IF_MONEY: {
            s32 v = rd32(&p);
            int to = rd16(&p);
            if ((s32)g_save.money >= v)
                p = base + to;
            break;
        }
        case OP_IF_ITEM: {
            int it = rd16(&p), n = rd8(&p), to = rd16(&p);
            if (bag_count(it) >= n)
                p = base + to;
            break;
        }
        case OP_IF_GENDER: {
            int g = rd8(&p), to = rd16(&p);
            if (g_save.player_gender == g)
                p = base + to;
            break;
        }
        case OP_IF_PARTY: {
            int n = rd8(&p), to = rd16(&p);
            if (g_save.party_count >= n)
                p = base + to;
            break;
        }
        case OP_SETFLAG: {
            int f = rd16(&p);
            flag_set(f, rd8(&p));
            break;
        }
        case OP_SETVAR: {
            int var = rd8(&p);
            g_save.vars[var] = rd16(&p);
            break;
        }
        case OP_ADDVAR: {
            int var = rd8(&p);
            g_save.vars[var] += (s16)rd16(&p);
            break;
        }
        case OP_GIVEMON: {
            int sp = rd16(&p), lv = rd8(&p);
            if (sp & 0x8000)
                sp = g_save.vars[sp & 0xFF];
            world_give_mon(sp, lv);
            break;
        }
        case OP_GIVEITEM: {
            int it = rd16(&p), n = rd8(&p);
            give_item_msg(it, n);
            break;
        }
        case OP_TAKEITEM: {
            int it = rd16(&p), n = rd8(&p);
            bag_take(it, n);
            break;
        }
        case OP_MONEY: {
            s32 v = rd32(&p);
            s32 m = (s32)g_save.money + v;
            g_save.money = m < 0 ? 0 : (m > 9999999 ? 9999999 : m);
            if (v > 0)
                sfx_play(SFX_COIN);
            break;
        }
        case OP_HEAL:
            world_heal_party();
            break;
        case OP_BATTLE: {
            int tr = rd16(&p), nolose = rd8(&p);
            g_save.vars[VAR_RESULT] = world_battle_trainer(tr, nolose) ? 1 : 0;
            // A blackout ends the whole event, including callers of this script.
            // Explicit nolose battles (e.g. the first rival fight) may continue.
            if (!g_save.vars[VAR_RESULT] && !nolose)
                battle_aborted = true;
            break;
        }
        case OP_WILD: {
            int sp = rd16(&p), lv = rd8(&p);
            g_save.vars[VAR_RESULT] = world_battle_wild(sp, lv, true) ? 1 : 0;
            break;
        }
        case OP_MUSIC: {
            const char *s = script_string(rd16(&p));
            if (s[0])
                music_play(s);
            else
                music_stop();
            break;
        }
        case OP_FANFARE: {
            const char *s = script_string(rd16(&p));
            world_fanfare(s);
            break;
        }
        case OP_SFX:
            sfx_play(rd8(&p));
            break;
        case OP_WAIT:
            world_wait(rd16(&p));
            break;
        case OP_FADE: {
            int m = rd8(&p), fr = rd8(&p);
            if (m == 0 || m == 2)
                gfx_fade_out(fr, m == 2);
            else
                gfx_fade_in(fr, m == 3);
            break;
        }
        case OP_SCREENSHAKE:
            world_screenshake(rd8(&p));
            break;
        case OP_WARP: {
            int mp = rd16(&p), x = rd8(&p), y = rd8(&p), d = rd8(&p);
            world_warp(mp, x, y, d, true);
            break;
        }
        case OP_MOVE: {
            int who = rd16(&p);
            const char *path = script_string(rd16(&p));
            int nowait = rd8(&p);
            world_move_actor(world_actor_by_name(who), path, !nowait);
            break;
        }
        case OP_FACE: {
            int who = world_actor_by_name(rd16(&p));
            int d = rd8(&p);
            world_face_actor(who, d);
            break;
        }
        case OP_EMOTE: {
            int who = world_actor_by_name(rd16(&p));
            int e = rd8(&p), fr = rd8(&p);
            if (who >= 0) {
                actor_emote(who, e, fr);
                sfx_play(e == 1 ? SFX_ALARM : SFX_BLIP);
                world_wait(fr);
            }
            break;
        }
        case OP_NPCVIS: {
            int who = world_actor_by_name(rd16(&p));
            int v = rd8(&p);
            if (who > 0)
                g_actors[who].visible = v;
            break;
        }
        case OP_SPAWN: {
            int name = rd16(&p), spr = rd16(&p), x = rd8(&p), y = rd8(&p), d = rd8(&p);
            world_spawn(name, spr, x, y, d);
            break;
        }
        case OP_DESPAWN:
            world_despawn(rd16(&p));
            break;
        case OP_LOCK:
        case OP_RELEASE:
            break;
        case OP_MINIGAME:
            g_save.vars[VAR_RESULT] = world_minigame(rd8(&p));
            break;
        case OP_BADGE: {
            int b = rd8(&p);
            g_save.badges |= 1 << (b - 1);
            flag_set(FLAG_BADGE_1 + b - 1, true);
            world_badge_ceremony(b);
            break;
        }
        case OP_CHAPTER:
            g_save.chapter = rd8(&p);
            break;
        case OP_LOADING:
            world_loading(rd16(&p));
            break;
        case OP_CALL: {
            int sid = rd16(&p);
            script_run(sid);
            break;
        }
        case OP_SPECIAL: {
            int sp = rd8(&p), arg = rd16(&p);
            world_special(sp, arg);
            break;
        }
        case OP_STRVAR: {
            int i = rd8(&p);
            const char *s = script_string(rd16(&p));
            strncpy(g_strvar[i % 10], s, 23);
            g_strvar[i % 10][23] = 0;
            break;
        }
        case OP_NOTICE:
            dlg_notice(script_string(rd16(&p)));
            break;
        case OP_RANDOM: {
            int n = rd16(&p), var = rd8(&p);
            g_save.vars[var] = rng_range(n);
            break;
        }
        case OP_CINE: {
            int mode = rd8(&p);
            const char *t = script_string(rd16(&p));
            if (mode == 0)
                cine_begin(t);
            else
                cine_end();
            break;
        }
        case OP_SLIDE: {
            const char *n = script_string(rd16(&p));
            int mot = rd8(&p), tr = rd8(&p);
            cine_slide(n, mot, tr);
            break;
        }
        case OP_CARD: {
            const char *a = script_string(rd16(&p));
            const char *b = script_string(rd16(&p));
            cine_card(a, b);
            break;
        }
        default:
            fatal("Script %d: bad op %d", id, op);
        }
    }
    depth--;
    if (depth == 0) {
        dlg_close();
        portrait_hide_all();
    }
    (void)give_item_msg;
}
