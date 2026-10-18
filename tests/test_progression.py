"""Host-side regressions: python3 -m unittest discover -s tests -v.

Run the production VM and world functions with hardware/UI calls stubbed out.
"""
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from mkscripts import Compiler, OPS
from map_ids import ordered_map_sources


def function(path, signature):
    source = (ROOT / path).read_text()
    start = source.index(signature)
    opening = source.index('{', start)
    depth = 1
    end = opening + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


def run_c(source):
    with tempfile.TemporaryDirectory() as directory:
        src = Path(directory) / 'test.c'
        binary = Path(directory) / 'test'
        src.write_text(source)
        subprocess.run(['cc', '-std=c11', '-O2', '-w', str(src), '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True)


class ProgressionTests(unittest.TestCase):
    def test_scripts_use_released_map_ids(self):
        compiler = Compiler()
        released = (ROOT / 'assets/maps/order.txt').read_text().splitlines()
        built = json.loads((ROOT / 'build/map_ids.json').read_text())
        self.assertEqual(compiler.maps, built)
        self.assertEqual(list(compiler.maps), released)
        code = compiler.compile_script('visit', 'test', [(1, 'warp schengen 11 1 down')])
        self.assertEqual(code[0], OPS['WARP'])
        self.assertEqual(int.from_bytes(code[1:3], 'little'), built['schengen'])
        self.assertNotEqual(built['schengen'], built['strasbourg'])

    def test_new_maps_append_without_changing_existing_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            maps = Path(directory) / 'assets/maps'
            maps.mkdir(parents=True)
            (maps / 'order.txt').write_text('z_old\nb_old\n')
            for name in ('z_old', 'b_old', 'a_new', 'c_new'):
                (maps / f'{name}.map').touch()
            self.assertEqual([Path(p).stem for p in ordered_map_sources(directory)],
                             ['z_old', 'b_old', 'a_new', 'c_new'])

    def test_battle_loss_aborts_vm_and_callers_but_nolose_continues(self):
        source = (ROOT / 'source/script.c').read_text()
        source = re.sub(r'^#include .*$', '', source, flags=re.M)
        # Keep all VM code; only unrelated UI/hardware services are no-ops.
        real = {'script_init', 'script_string', 'script_running', 'rd8', 'rd16', 'rd32',
                'give_item_msg', 'script_run', 'world_battle_trainer', 'flag_set',
                'if', 'while', 'switch', 'for', 'sizeof', 'memcmp', 'snprintf', 'strncpy'}
        services = set(re.findall(r'\b([a-zA-Z_]\w*)\s*\(', source)) - real
        services -= {'tr', 'T', 'void'}
        stubs = '\n'.join(f'#define {name}(...) (0)' for name in sorted(services))
        run_c('''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef int16_t s16;
typedef int32_t s32;
enum { VAR_RESULT, FLAG_BADGE_1 = 0 };
struct { int vars[64], money, player_gender, badges, chapter, party_count; } g_save;
struct { bool visible; } g_actors[10];
struct { const char *name; } items[10];
char g_strvar[10][24];
static int won, flags;
static int world_battle_trainer(int trainer, int nolose) { return won; }
static void flag_set(int flag, int value) { if (value) flags |= 1 << flag; }
#define tr(s) (s)
#define T(s) (s)
''' + stubs + '\n' + source + '''
static void setup(u8 *bytes, u32 *offsets, int count) {
    bank = bytes; offs = offsets; nscripts = count;
    memset(&g_save, 0, sizeof(g_save)); flags = 0;
}
int main(void) {
    u32 offsets[] = {0, 9};
    u8 direct[] = {OP_BATTLE, 0, 0, 0, OP_BADGE, 1, OP_CHAPTER, 2, OP_END};
    setup(direct, offsets, 1); won = 0;
    script_run(0);
    assert(g_save.badges == 0 && flags == 0 && g_save.chapter == 0 && depth == 0);
    // Same event remains retryable; a fresh invocation clears cancellation.
    won = 1; script_run(0);
    assert(g_save.badges == 1 && flags == 1 && g_save.chapter == 2);
    setup(direct, offsets, 1); won = 0; direct[3] = 1;
    script_run(0);
    assert(g_save.chapter == 2 && g_save.vars[VAR_RESULT] == 0);
    u8 nested[] = {OP_CALL, 1, 0, OP_BADGE, 2, OP_CHAPTER, 3, OP_END, OP_END,
                   OP_BATTLE, 0, 0, 0, OP_BADGE, 1, OP_END};
    setup(nested, offsets, 2); won = 0;
    script_run(0);
    assert(g_save.badges == 0 && flags == 0 && g_save.chapter == 0 && depth == 0);
    won = 1; script_run(0);
    assert(g_save.badges == 3 && g_save.chapter == 3);
}
''')

    def test_exit_guard_runs_before_warp(self):
        run_c('''
#include <assert.h>
#include <stdbool.h>
#define PLAYER 0
struct { int tx, ty; } g_actors[1];
struct { int x, y; } g_save;
static int badge, warps, guards, encounters;
static bool check_triggers(void) { if (!badge) { guards++; return true; } return false; }
static bool check_warp(void) { warps++; return true; }
static bool check_trainers(void) { return false; }
static bool check_encounter(void) { encounters++; return false; }
''' + function('source/world.c', 'static void after_step(void)') + '''
int main(void) {
    badge = 0; after_step(); assert(guards == 1 && warps == 0);
    badge = 1; after_step(); assert(guards == 1 && warps == 1 && encounters == 0);
}
''')

    def test_trainer_outcomes_restore_screens_before_blackout_dialogue(self):
        run_c('''
#include <assert.h>
#include <stdbool.h>
#define FLAG_TRAINER_BASE 100
static int won, blackouts, marked;
static int brightness[2];
static bool refreshed;
static void set_battle_bg(void) {}
static bool battle_trainer(int tr) {
    brightness[0] = brightness[1] = -16;
    refreshed = false;
    return won;
}
static void world_refresh(void) { refreshed = true; }
static void world_blackout(void) {
    assert(refreshed && brightness[0] == 0 && brightness[1] == 0);
    blackouts++;
}
static void flag_set(int flag, bool value) { marked += value; }
static void gfx_brightness(bool bottom, int value) {
    assert(refreshed);
    brightness[bottom] = value;
}
''' + function('source/world.c', 'bool world_battle_trainer(int tr, bool nolose)') + '''
int main(void) {
    won = 0;
    assert(!world_battle_trainer(1, false) && blackouts == 1 && marked == 0);
    assert(!world_battle_trainer(1, true) && blackouts == 1 && marked == 0);
    assert(brightness[0] == 0 && brightness[1] == 0);
    won = 1;
    assert(world_battle_trainer(1, false) && blackouts == 1 && marked == 1);
    assert(brightness[0] == 0 && brightness[1] == 0);
}
''')

    def test_luxembourg_capture_with_real_species_and_items(self):
        species = sorted(json.loads((ROOT / 'data/species.json').read_text()), key=lambda s: s['num'])
        ids = {s['id']: i for i, s in enumerate(species)}
        items = json.loads((ROOT / 'data/items.json').read_text())
        encounters = json.loads((ROOT / 'data/encounters.json').read_text())
        rates = ','.join(str(s['catch']) for s in species)
        params = ','.join('{"tampon",%d}' % item['param'] for item in items[:4])
        visitors = ','.join(str(ids[slot[0]]) for slot in encounters['lux_parc']['slots'])
        capture = function('source/battle.c', 'static bool try_capture(int item)')
        run_c('''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
typedef uint32_t u32;
typedef uint64_t u64;
enum { STATUS_NONE, STATUS_LOBBY, STATUS_SCANDALE, STATUS_GEL, STATUS_SOMMEIL, STATUS_BLOQUE };
enum { SFX_CAPTURE_SHAKE, SFX_CAPTURE_OK };
typedef struct { int species, hp, status; } Mon;
typedef struct { const char *name; int param; } ItemData;
struct { Mon *mon; } side[2];
static const int rates[] = {''' + rates + '''};
static const ItemData items[] = {''' + params + '''};
static const int visitors[] = {''' + visitors + '''};
static int foe_x, foe_y, foe_flash, stored;
static bool foe_visible;
static int mon_max_hp(Mon *mon) { return 40; }
static int party_add(Mon *mon) { stored++; return 0; }
static u32 rng_state = 12345678;
''' + function('source/main.c', 'u32 rng_next(void)') + '''
#define MIN(a,b) ((a)<(b)?(a):(b))
#define msg(...) ((void)0)
#define pname(...) "Euromon"
#define fx_throw_ball_to_foe(...) ((void)0)
#define bwait(...) ((void)0)
#define fx_ball_shake(...) ((void)0)
#define sfx_play(...) ((void)0)
#define fx_ball_stars(...) ((void)0)
#define fx_clear(...) ((void)0)
#define dex_is_caught(...) false
''' + f'#define SP_CONSTITUTIO {ids["constitutio"]}\n' +
                # Access production catch rates through the same field as the engine.
                'static struct { int catch_rate; } species[' + str(len(species)) + '];\n' + capture + '''
int main(void) {
    for (int i = 0; i < sizeof(rates)/sizeof(*rates); i++) species[i].catch_rate = rates[i];
    Mon foe; side[1].mon = &foe;
    for (int i = 0; i < sizeof(visitors)/sizeof(*visitors); i++) {
        foe.species = visitors[i]; foe.status = STATUS_NONE;
        int full[3], low[3];
        for (int item = 0; item < 3; item++) {
            full[item] = low[item] = 0;
            foe.hp = 40;
            for (int n = 0; n < 10000; n++) full[item] += try_capture(item);
            foe.hp = 1;
            for (int n = 0; n < 10000; n++) low[item] += try_capture(item);
            assert(full[item] > 1000 && low[item] > full[item]);
            // Capture odds should match the HP/ball formula within sampling error.
            int expected_full = (species[foe.species].catch_rate * items[item].param / 30);
            int expected_low = ((120 - 2) * species[foe.species].catch_rate * items[item].param / 10) / 120;
            if (expected_low > 255) expected_low = 255;
            assert(full[item] * 255 > (expected_full - 8) * 10000);
            assert(full[item] * 255 < (expected_full + 8) * 10000);
            assert(low[item] * 255 > (expected_low - 8) * 10000);
            assert(low[item] * 255 < (expected_low + 8) * 10000);
        }
        assert(full[2] > full[1] && full[1] > full[0]);
        assert(low[2] >= low[1] && low[1] > low[0]);
        assert(try_capture(3)); // unanimous stamp always works
    }
    // Only the deliberately uncatchable referendum species is excluded.
    foe.species = SP_CONSTITUTIO;
    assert(!try_capture(3));
    assert(stored > 0);
}
''')


if __name__ == '__main__':
    unittest.main()
