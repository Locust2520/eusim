"""Production mini-game and event VM regressions for stamp rules/rewards."""
import json
import re
import unittest

from test_progression import ROOT, function, run_c


class StampGameTests(unittest.TestCase):
    def test_only_fifteen_valid_sheets_win_and_fake_stamp_loses(self):
        run_c(r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>
typedef uint8_t u8;
enum { C_GOLD_D, C_TEXT, C_WHITE, C_GREEN, C_RED, C_INK, C_LGREY };
enum { SFX_STAMP, SFX_ERROR };
static int g_bot, font_small, g_touch_x, g_touch_y;
static int mode, ticks, good_stamps, bad_stamps, fake_seen;
static unsigned seed;
static struct { int x, y; bool valid, stamped; } papers[6];
static int count;
static int rng_range(int n) {
    seed = seed * 1664525u + 1013904223u;
    return (seed >> 8) % n;
}
static void canvas_clear(int *canvas, int color) { count = 0; }
#define canvas_rect(...) ((void)0)
#define canvas_hline(...) ((void)0)
#define canvas_box(...) ((void)0)
static void ui_text_in(int *canvas, int *font, int x, int y, int w, int h,
                       const char *label, int color, int shadow, int align) {
    assert(count < 6);
    papers[count].x = x - 2; papers[count].y = y - 2;
    papers[count].valid = !strcmp(label, "ARRÊT");
    papers[count].stamped = false;
    if (!papers[count].valid) { assert(!strcmp(label, "FAUX")); fake_seen++; }
    count++;
}
static void canvas_text(int *canvas, int *font, int x, int y,
                        const char *text, int color, int shadow) {
    assert(count > 0 && !strcmp(text, "OK"));
    papers[count - 1].stamped = true;
}
static bool touch_ready(void) {
    if (mode == 0) return false;
    for (int i = count - 1; i >= 0; i--) {
        bool wanted = mode == 2 ? !papers[i].valid :
                      mode == 3 && good_stamps ? papers[i].stamped :
                      papers[i].valid && !papers[i].stamped;
        int x = papers[i].x + 20, y = papers[i].y + 24;
        if (!wanted || x < 0 || x >= 256) continue;
        bool covered = false;
        for (int j = i + 1; j < count; j++)
            if (x >= papers[j].x && x < papers[j].x + 40 &&
                y >= papers[j].y && y < papers[j].y + 48) covered = true;
        if (!covered) { g_touch_x = x; g_touch_y = y; return true; }
    }
    return false;
}
#define g_touch_down touch_ready()
#define MIN(a,b) ((a)<(b)?(a):(b))
static int intro(const char *title, const char *rule) {
    assert(strstr(rule, "15") && strstr(rule, "FAUX")); return 1;
}
static void top_panel(const char *title, const char *rule, int secs, int score, int goal) {
    assert(goal == 15 && score <= 15 && strstr(rule, "FAUX"));
}
static void sfx_play(int sound) {
    if (sound == SFX_STAMP) good_stamps++; else bad_stamps++;
}
static void frame_wait(void) { assert(++ticks <= 1800); }
static int outro(bool won, const char *win, const char *lose) {
    if (won) assert(good_stamps == 15 && !bad_stamps);
    if (bad_stamps) assert(strstr(lose, "mauvais"));
    return won;
}
''' + function('source/minigame.c', 'static int mg_tampon(void)') + r'''
static void reset(int play_mode, unsigned initial_seed) {
    mode = play_mode; seed = initial_seed;
    ticks = good_stamps = bad_stamps = fake_seen = count = 0;
}
int main(void) {
    for (unsigned s = 1; s <= 20; s++) {
        reset(1, s); assert(mg_tampon() == 1);
        assert(fake_seen > 0 && good_stamps == 15 && bad_stamps == 0);
        reset(2, s); assert(mg_tampon() == 0);
        assert(bad_stamps == 1 && good_stamps == 0 && ticks < 1800);
    }
    reset(0, 1); assert(mg_tampon() == 0 && ticks == 1800 && good_stamps == 0);
    reset(3, 1); assert(mg_tampon() == 0 && good_stamps == 1 && !bad_stamps);
}
''')

    def test_reward_progression_failure_refusal_and_saved_first_win(self):
        source = (ROOT / 'source/script.c').read_text()
        source = re.sub(r'^#include .*$', '', source, flags=re.M)
        real = {'script_init', 'script_string', 'script_running', 'rd8', 'rd16', 'rd32',
                'give_item_msg', 'script_run', 'flag_set', 'flag_get', 'fs_load', 'bag_add',
                'dlg_say', 'dlg_say_nowait', 'dlg_yesno', 'world_minigame', 'rng_range',
                'if', 'while', 'switch', 'for', 'sizeof', 'memcmp', 'snprintf', 'strncpy'}
        services = set(re.findall(r'\b([a-zA-Z_]\w*)\s*\(', source)) - real - {'tr', 'T', 'void'}
        stubs = '\n'.join(f'#define {name}(...) (0)' for name in sorted(services))
        flags = json.loads((ROOT / 'build/flag_ids.json').read_text())
        scripts = json.loads((ROOT / 'build/script_ids.json').read_text())
        items = json.loads((ROOT / 'build/item_ids.json').read_text())
        constants = '\n'.join(f'#define {name} {value}' for name, value in {
            'FIRST': flags['STAMP_DONE'], 'SECOND': flags['STAMP_SECOND_DONE'],
            'GREFFIER': scripts['cjue_greffier'], 'REWARD_ITEM': items['tampon_qualifie'],
        }.items())
        bank_path = json.dumps(str(ROOT / 'nitrofs/scripts.bin'))
        run_c(r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef uint8_t u8; typedef uint16_t u16; typedef uint32_t u32;
typedef int16_t s16; typedef int32_t s32;
enum { VAR_RESULT, FLAG_BADGE_1 = 0 };
struct { int vars[64], money, player_gender, badges, chapter, party_count; bool flags[2048]; } g_save;
struct { bool visible; } g_actors[10];
struct { const char *name; } items[96];
char g_strvar[10][24], last_message[512];
static int accept = 1, minigame_win, reward_count, rounds, coin, coin_calls;
''' + constants + r'''
static void *fs_load(const char *path, u32 *size) {
    FILE *f = fopen(''' + bank_path + r''', "rb"); assert(f);
    fseek(f, 0, SEEK_END); long n = ftell(f); rewind(f);
    void *data = malloc(n); assert(data && fread(data, 1, n, f) == n);
    fclose(f); *size = n; return data;
}
static bool flag_get(int f) { return g_save.flags[f]; }
static void flag_set(int f, bool v) { g_save.flags[f] = v; }
static void bag_add(int item, int n) { assert(item == REWARD_ITEM); reward_count += n; }
static void dlg_say(const char *who, const char *message) {
    snprintf(last_message, sizeof last_message, "%s", message);
}
static void dlg_say_nowait(const char *who, const char *message) { dlg_say(who, message); }
static bool dlg_yesno(void) { return accept; }
static int world_minigame(int id) { assert(id == 1); rounds++; return minigame_win; }
static int rng_range(int n) { assert(n == 2); coin_calls++; return coin; }
#define tr(s) (s)
#define T(s) (s)
''' + stubs + '\n' + source + r'''
int main(void) {
    for (int i = 0; i < 96; i++) items[i].name = "Tampon";
    script_init();
    minigame_win = 0; script_run(GREFFIER);
    assert(reward_count == 0 && !flag_get(FIRST) && !flag_get(SECOND));
    minigame_win = 1; script_run(GREFFIER);
    assert(reward_count == 3 && flag_get(FIRST) && !flag_get(SECOND) && coin_calls == 0);
    minigame_win = 0; script_run(GREFFIER);
    assert(reward_count == 3 && !flag_get(SECOND));
    // Progress survives resetting the temporary variables (as with a saved game).
    memset(g_save.vars, 0, sizeof(g_save.vars));
    minigame_win = 1; script_run(GREFFIER);
    assert(reward_count == 4 && flag_get(SECOND) && coin_calls == 0);
    for (int i = 0; i < 100; i++) {
        coin = i % 2; int before = reward_count;
        script_run(GREFFIER);
        assert(reward_count == before + coin);
        if (!coin) assert(strstr(last_message, "cette fois"));
    }
    assert(reward_count == 54 && coin_calls == 100);
    int played = rounds;
    accept = 0; script_run(GREFFIER);
    assert(rounds == played && reward_count == 54 && coin_calls == 100);
    // Old save with the original prize: next win is the guaranteed second prize.
    accept = 1; flag_set(SECOND, false);
    script_run(GREFFIER);
    assert(reward_count == 55 && flag_get(SECOND) && coin_calls == 100);
    free(bank);
}
''')


if __name__ == '__main__':
    unittest.main()
