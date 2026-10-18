"""Run production link battles as two independent processes with different frame timing."""
from pathlib import Path
import re
import unittest
from test_progression import ROOT, function, run_c


def without_includes(path):
    return re.sub(r'^#(?:include|pragma).*$', '', (ROOT / path).read_text(), flags=re.M)


class MultiplayerTests(unittest.TestCase):
    def test_two_seats_agree_and_restore_progress(self):
        battle = (ROOT / 'source/battle.c').read_text()
        state = battle[battle.index('typedef struct {'):battle.index('static SpriteSheet')]
        functions = [
            'static const char *pname', 'static int type1', 'static int type2',
            'static int stage_mult', 'static int eff_stat', 'static int type_eff',
            'static void send_out', 'static int calc_damage', 'static void apply_damage',
            'static bool try_status', 'static void stat_change', 'static bool accuracy_check',
            'static void use_move(int a, int slot, int move_override)\n{',
            'static bool can_act', 'static void end_of_turn', 'static int foe_next_alive',
        ]
        stubs = r'''
#include <assert.h>
#include <stddef.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <signal.h>
typedef uint8_t u8; typedef int8_t s8; typedef uint16_t u16; typedef int16_t s16;
typedef uint32_t u32; typedef int32_t s32;
#define MIN(a,b) ((a)<(b)?(a):(b))
#define MAX(a,b) ((a)>(b)?(a):(b))
#define CLAMP(v,l,h) MIN(MAX(v,l),h)
static u32 g_frame, rng_state = 1;
u32 rng_next(void) { u32 x=rng_state; x^=x<<13; x^=x>>17; x^=x<<5; return rng_state=x; }
int rng_range(int n) { return n>1 ? rng_next()%n : 0; }
'''
        headers = ''.join(without_includes(p) for p in
                          ('include/save.h', 'include/gen/data_ids.h', 'include/data.h',
                           'include/battle.h', 'include/multiplayer.h'))
        services = ['sfx_play', 'sfx_cry', 'fx_status', 'fx_stat', 'fx_move', 'load_mon_gfx',
                    'fx_throw_tampon', 'draw_infobox', 'bwait', 'dlg_close', 'intro_transition',
                    'setup_scene', 'teardown_scene', 'music_play', 'gfx_brightness',
                    'gfx_fade_out', 'withdraw_ally', 'ui_backdrop']
        source = stubs + headers + '\nSaveData g_save;\n' + without_includes('source/gen/data.c')
        source += '\n' + without_includes('source/mon.c') + '\n' + state
        source += '''
static int foe_flash, ally_flash, foe_shake, ally_shake, foe_x, foe_y, ally_x, ally_y;
static bool foe_visible, ally_visible;
#define FOE_HOME_X 156
#define FOE_HOME_Y 18
#define ALLY_HOME_X 28
#define ALLY_HOME_Y 70
static int test_seat, test_fd, turn, exchanges;
static u32 test_seed;
int link_seat(void) { return test_seat; }
u32 link_seed(void) { return test_seed; }
bool link_ok(void) { return true; }
#define tr(s) (s)
#define msg(...) do { g_frame += 1 + test_seat; for(int z=0;z<1+test_seat;z++) rng_next(); } while(0)
'''
        source += '\n'.join(f'#define {name}(...) ((void)0)' for name in services) + '\n'
        source += '#define animate_hp(s,from,to) (side[s].mon->hp = (to))\n'
        source += '\n'.join(function('source/battle.c', signature) for signature in functions)
        source += r'''
static int faint_check(int s) { side[s].mon->status=0; return 1; }
static int choose_switch(bool forced) {
    for (int i=0;i<g_save.party_count;i++) if (g_save.party[i].hp && i!=player_idx) return i;
    return -1;
}
static int main_menu(void) {
    turn++;
    if (turn>25) return 2;
    if (turn==3 && choose_switch(false)>=0) return 3;
    return 0;
}
static int move_menu(void) {
    for (int k=0;k<4;k++) {
        int i=(k+turn+test_seat)%4;
        if (side[0].mon->moves[i]!=0xffff && side[0].mon->pp[i]) return i;
    }
    return 4;
}
static void io_all(void *b, int n, bool writing) {
    while(n) { int k=writing ? write(test_fd,b,n) : read(test_fd,b,n); assert(k>0); b=(u8*)b+k; n-=k; }
}
bool link_exchange(int kind, const void *out, int size, void *in, int *received) {
    if (test_seed >= 1039 && exchanges == 8) return false;
    u8 a[256]={0}, b[256];
    a[0]=kind; a[1]=size; memcpy(a+2,out,size);
    io_all(a,sizeof a,true); io_all(b,sizeof b,false);
    assert(a[0]==b[0]);
    if(kind==LINK_CHECK) { assert(a[1]==b[1]); assert(!memcmp(a+2,b+2,size)); }
    memcpy(in,b+2,b[1]); *received=b[1]; exchanges++; return true;
}
'''
        source += battle[battle.index('static void team_encode'):]
        source += r'''
static void play(int seat, int fd, unsigned scenario) {
    test_seat=seat; test_fd=fd; test_seed=scenario+999;
    memset(&g_save,0,sizeof g_save); rng_state=1+seat;
    g_save.money=12345; g_save.badges=3; g_save.vars[0]=55;
    g_save.party_count=3;
    for(int i=0;i<3;i++) {
        mon_create(&g_save.party[i], (scenario*5+i+seat*3)%NUM_SPECIES, 35+i*10);
        for(int k=0;k<4;k++) {
            int move=(scenario*8+i*4+k+seat*4)%NUM_MOVES;
            g_save.party[i].moves[k]=move; g_save.party[i].pp[k]=moves[move].pp;
        }
        g_save.party[i].hp=1; g_save.party[i].status=STATUS_SCANDALE;
    }
    SaveData original=g_save;
    battle_multiplayer();
    assert(exchanges>=3); assert(!memcmp(&g_save,&original,sizeof original));
    close(fd); _exit(0);
}
int main(void) {
    alarm(20);
    for(unsigned scenario=0;scenario<80;scenario++) {
        int fd[2]; assert(socketpair(AF_UNIX,SOCK_STREAM,0,fd)==0);
        pid_t a=fork(); assert(a>=0); if(!a) { close(fd[1]); play(0,fd[0],scenario); }
        pid_t b=fork(); assert(b>=0); if(!b) { close(fd[0]); play(1,fd[1],scenario); }
        close(fd[0]); close(fd[1]);
        int x,y; waitpid(a,&x,0); waitpid(b,&y,0);
        assert(WIFEXITED(x)&&WEXITSTATUS(x)==0); assert(WIFEXITED(y)&&WEXITSTATUS(y)==0);
    }
}
'''
        run_c(source)
