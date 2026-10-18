#include "mon.h"

u32 exp_for_level(int growth, int L)
{
    if (L <= 1)
        return 0;
    u32 c = (u32)L * L * L;
    switch (growth) {
    case GROW_FAST: return c * 4 / 5;
    case GROW_SLOW: return c * 5 / 4;
    case GROW_PARABOLIC: {
        s32 v = (s32)(c * 6 / 5) - 15 * L * L + 100 * L - 140;
        return v < 0 ? 0 : (u32)v;
    }
    default: return c;
    }
}

int mon_iv(const Mon *m, int stat)
{
    return (m->ivs >> (stat * 5)) & 31;
}

int mon_stat(const Mon *m, int stat)
{
    const SpeciesData *s = &species[m->species];
    int b = s->base[stat];
    int v = ((2 * b + mon_iv(m, stat)) * m->level) / 100;
    if (stat == STAT_HP)
        return v + m->level + 10;
    return v + 5;
}

int mon_max_hp(const Mon *m) { return mon_stat(m, STAT_HP); }

const char *mon_name(const Mon *m) { return species[m->species].name; }

int mon_learn(Mon *m, int move)
{
    for (int i = 0; i < 4; i++)
        if (m->moves[i] == move && m->pp[i] != 0xFF)
            if (m->moves[i] == move)
                return -1;
    for (int i = 0; i < 4; i++)
        if (m->moves[i] == 0xFFFF) {
            m->moves[i] = move;
            m->pp[i] = moves[move].pp;
            return i;
        }
    return -2;
}

void mon_create(Mon *m, int sp, int level)
{
    memset(m, 0, sizeof(*m));
    m->species = sp;
    m->level = CLAMP(level, 1, 100);
    m->ivs = rng_next() & 0x3FFFFFFF;
    m->exp = exp_for_level(species[sp].growth, m->level);
    for (int i = 0; i < 4; i++)
        m->moves[i] = 0xFFFF;
    // last 4 moves learnt at or below level
    const u16 *l = species[sp].learn;
    int cand[32], n = 0;
    for (int i = 0; l[i] != 0xFFFF && n < 32; i += 2)
        if (l[i] <= m->level)
            cand[n++] = l[i + 1];
    int start = n > 4 ? n - 4 : 0;
    int k = 0;
    for (int i = start; i < n; i++) {
        bool dup = false;
        for (int j = 0; j < k; j++)
            if (m->moves[j] == cand[i])
                dup = true;
        if (!dup) {
            m->moves[k] = cand[i];
            m->pp[k] = moves[cand[i]].pp;
            k++;
        }
    }
    m->shiny = (rng_next() % 512) == 0;
    m->friendship = 70;
    m->hp = mon_max_hp(m);
}

void mon_heal(Mon *m)
{
    m->hp = mon_max_hp(m);
    m->status = STATUS_NONE;
    m->sleep_turns = 0;
    for (int i = 0; i < 4; i++)
        if (m->moves[i] != 0xFFFF)
            m->pp[i] = moves[m->moves[i]].pp;
}

static void bit_set(u8 *b, int i) { b[i >> 3] |= 1 << (i & 7); }
static bool bit_get(const u8 *b, int i) { return (b[i >> 3] >> (i & 7)) & 1; }

void dex_seen(int sp) { if (sp >= 0 && sp < 128) bit_set(g_save.dex_seen, sp); }
void dex_caught(int sp) { if (sp >= 0 && sp < 128) { bit_set(g_save.dex_seen, sp); bit_set(g_save.dex_caught, sp); } }
bool dex_is_seen(int sp) { return bit_get(g_save.dex_seen, sp); }
bool dex_is_caught(int sp) { return bit_get(g_save.dex_caught, sp); }

int dex_count_caught(void)
{
    int n = 0;
    for (int i = 0; i < NUM_SPECIES; i++)
        n += dex_is_caught(i);
    return n;
}

int dex_count_seen(void)
{
    int n = 0;
    for (int i = 0; i < NUM_SPECIES; i++)
        n += dex_is_seen(i);
    return n;
}

int party_add(const Mon *m)
{
    dex_caught(m->species);
    if (g_save.party_count < PARTY_MAX) {
        g_save.party[g_save.party_count++] = *m;
        return 0;
    }
    if (g_save.box_count < BOX_MAX) {
        g_save.box[g_save.box_count++] = *m;
        return 1;
    }
    return -1;
}

void party_heal_all(void)
{
    for (int i = 0; i < g_save.party_count; i++)
        mon_heal(&g_save.party[i]);
}

int party_first_alive(void)
{
    for (int i = 0; i < g_save.party_count; i++)
        if (g_save.party[i].hp > 0)
            return i;
    return -1;
}

bool party_all_fainted(void)
{
    return party_first_alive() < 0;
}

int bag_count(int item)
{
    if (item < 0 || item >= NUM_ITEMS)
        return 0;
    return g_save.bag[item];
}

void bag_add(int item, int n)
{
    if (item < 0 || item >= NUM_ITEMS)
        return;
    int v = g_save.bag[item] + n;
    g_save.bag[item] = CLAMP(v, 0, 99);
}

bool bag_take(int item, int n)
{
    if (bag_count(item) < n)
        return false;
    g_save.bag[item] -= n;
    return true;
}
