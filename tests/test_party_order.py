"""Party moves insert complete members and preserve everyone else's order."""
import unittest

from test_progression import function, run_c


class PartyOrderTests(unittest.TestCase):
    def test_insertion_in_both_directions_and_same_slot(self):
        run_c(r'''
#include <assert.h>
#include <string.h>
typedef struct { int species, hp, moves[4], pp[4]; } Mon;
static struct { Mon party[6]; } g_save;
''' + function('source/menu.c', 'static void party_move(int from, int to)') + r'''
int main(void) {
    Mon original[6];
    for (int i = 0; i < 6; i++) {
        original[i].species = i;
        original[i].hp = 10 + i;
        for (int j = 0; j < 4; j++) {
            original[i].moves[j] = i * 4 + j;
            original[i].pp[j] = 20 - i - j;
        }
    }
    for (int from = 0; from < 6; from++) {
        for (int to = 0; to < 6; to++) {
            memcpy(g_save.party, original, sizeof original);
            party_move(from, to);
            int next = 0;
            for (int slot = 0; slot < 6; slot++) {
                int expected;
                if (slot == to) expected = from;
                else {
                    if (next == from) next++;
                    expected = next++;
                }
                assert(memcmp(&g_save.party[slot], &original[expected], sizeof(Mon)) == 0);
            }
        }
    }
}
''')
