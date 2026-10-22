"""Exercise evolution visibility and cancellation after battle fade-out."""
import unittest

from test_progression import function, run_c


class EvolutionTests(unittest.TestCase):
    def test_evolution_restores_both_screens_before_dialogue_and_animation(self):
        run_c(r'''
#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
typedef unsigned short u16;
typedef struct { int species, hp, level, moves[4], pp[4]; } Mon;
typedef struct { u16 pal[256]; int ncolors; } SpriteSheet;
#define T(s) (s)
#define RGB8(r,g,b) 0
#define RGB15(r,g,b) 0
#define SpriteSize_64x64 0
#define SpriteColorFormat_256Color 0
#define PAL_BATTLE_FOE 0
#define PAL_BATTLE_ALLY 1
#define PAL_BATTLE_FX 2
#define OAM_BATTLE 50
#define KEY_B 1
#define SFX_CANCEL 0
#define SFX_LEVELUP 1
static int g_top, oamMain, g_kdown, dialogues, frames, cancel;
static int brightness[2];
static int choice, choices;
static u16 BG_PALETTE[256], pixels[2048];
static const u16 learn[] = {30, 4, 0xFFFF};
static const struct { const char *name; const u16 *learn; } species[] = {
    {"Before", learn}, {"After", learn}
};
static const struct { const char *name; int pp; } moves[] = {
    {"One", 10}, {"Two", 15}, {"Three", 20}, {"Spread", 25}, {"Enquete OLAF", 30}
};
static const char *mon_name(Mon *m) { return species[m->species].name; }
#define gfx_clear_scene(...) ((void)0)
#define canvas_clear(...) ((void)0)
#define creature_sheet_load(...) ((void)0)
#define spr_upload(...) ((void)0)
#define spr_ext_pal(...) ((void)0)
#define oamClearSprite(...) ((void)0)
#define music_play(...) ((void)0)
#define oamSet(...) ((void)0)
#define sfx_play(...) ((void)0)
#define sfx_cry(...) ((void)0)
#define dex_caught(...) ((void)0)
#define dlg_close(...) ((void)0)
#define oamUpdate(...) ((void)0)
#define spr_free(...) ((void)0)
#define sheet_free(...) ((void)0)
static u16 *spr_alloc(bool sub, int size, int format) { return pixels; }
static int mon_max_hp(Mon *m) { return 20 + m->species; }
''' + function('source/mon.c', 'int mon_learn(Mon *m, int move)') + r'''
static int dlg_choice(const char **opts, int count, bool cancellable) {
    assert(count == 5 && cancellable);
    assert(strcmp(opts[4], "Don't learn it") == 0);
    for (int i = 0; i < 4; i++)
        assert(strcmp(opts[i], moves[i].name) == 0);
    choices++;
    return choice;
}
static void gfx_fade_in(int duration, bool white) {
    brightness[0] = brightness[1] = 0;
}
static void dlg_say(const char *who, const char *text) {
    assert(brightness[0] == 0 && brightness[1] == 0);
    dialogues++;
}
static void frame_wait(void) {
    assert(brightness[0] == 0 && brightness[1] == 0);
    frames++;
    g_kdown = cancel ? KEY_B : 0;
}
''' + function('source/menu2.c', 'void evolve_mon(Mon *m, int into)') + r'''
int main(void) {
    for (cancel = 0; cancel <= 1; cancel++) {
        Mon m = {0, 20, 10};
        brightness[0] = brightness[1] = -16;
        dialogues = frames = 0;
        evolve_mon(&m, 1);
        assert(dialogues == 2 && frames > 0);
        assert(m.species == (cancel ? 0 : 1));
        assert(m.hp == (cancel ? 20 : 21));
    }
    cancel = 0;
    // A full moveset after learning Spread: offer every replacement slot,
    // explicit refusal, and cancellation. Preserve all other moves and PP.
    for (choice = -1; choice <= 4; choice++) {
        Mon m = {0, 20, 30, {0, 1, 2, 3}, {4, 5, 6, 7}};
        choices = 0;
        evolve_mon(&m, 1);
        assert(m.species == 1 && choices == 1);
        for (int i = 0; i < 4; i++) {
            assert(m.moves[i] == (i == choice ? 4 : i));
            assert(m.pp[i] == (i == choice ? 30 : i + 4));
        }
    }
    // Free slots learn directly; known moves retain their remaining PP.
    Mon free_slot = {0, 20, 30, {0, 1, 2, 0xFFFF}, {4, 5, 6, 0}};
    choices = 0;
    evolve_mon(&free_slot, 1);
    assert(free_slot.moves[3] == 4 && free_slot.pp[3] == 30 && choices == 0);
    free_slot.species = 0;
    free_slot.pp[3] = 7;
    evolve_mon(&free_slot, 1);
    assert(free_slot.pp[3] == 7 && choices == 0);
    // Cancelling evolution must not offer or teach the new form's move.
    cancel = 1;
    Mon cancelled = {0, 20, 30, {0, 1, 2, 3}, {4, 5, 6, 7}};
    evolve_mon(&cancelled, 1);
    assert(cancelled.species == 0 && cancelled.moves[3] == 3 && choices == 0);
}
''')
