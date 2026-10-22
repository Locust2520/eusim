#pragma once
// Test builds (make QUICK=1 SCEN=n): skip title/intro, start from a scenario.
#include "save.h"
#include "mon.h"
#include "audio.h"
#include "gen/flags.h"
#include "gen/maps.h"
#ifndef SCEN
#define SCEN 0
#endif
static inline void quick_party(int sp, int lv)
{
    Mon m_;
    mon_create(&m_, sp, lv);
    party_add(&m_);
}
#if SCEN == 30
// Screenshot coordinates are supplied through QEXTRA only for scenario 30.
#define QUICKSTART_SCREENSHOT() do { \
    flag_set(FLAG_INTRO_DONE, 1); flag_set(FLAG_GOT_STARTER, 1); \
    flag_set(FLAG_GOT_DEX, 1); quick_party(SP_CECAGON, 40); quick_party(SP_DRAGHIZORD, 38); g_save.badges = 0x0F; \
    g_save.map = QMAP; g_save.x = QX; g_save.y = QY; g_save.dir = QDIR; \
} while (0)
#else
#define QUICKSTART_SCREENSHOT() do { } while (0)
#endif
#define QUICKSTART_SETUP() do { \
    if (SCEN == 0) { quick_party(0, 15); bag_add(IT_TAMPON, 10); bag_add(IT_CAFE, 5); } \
    if (SCEN >= 10) { quick_party(SP_CECAGON, 75); quick_party(SP_DRAGHIZORD, 75); quick_party(SP_NEUTRALIS, 75); g_save.badges = 0xFF; \
        for (int b_ = 0; b_ < 8; b_++) flag_set(FLAG_BADGE_1 + b_, 1); flag_set(FLAG_GOT_STARTER, 1); } \
    if (SCEN == 10) { g_save.badges = 0x0F; flag_set(FLAG_BADGE_5, 0); flag_set(FLAG_BADGE_6, 0); flag_set(FLAG_BADGE_7, 0); flag_set(FLAG_BADGE_8, 0); \
        g_save.map = MAP_GYM_LONDRES; g_save.x = 8; g_save.y = 14; } \
    if (SCEN == 11) { g_save.map = MAP_EUROPA_HALL; g_save.x = 8; g_save.y = 28; } \
    if (SCEN == 12) { flag_set(FLAG_POWERS_START, 1); g_save.map = MAP_ANVERS; g_save.x = 13; g_save.y = 10; } \
    if (SCEN == 13) { flag_set(FLAG_POWERS_START, 1); g_save.map = MAP_SOMMET; g_save.x = 10; g_save.y = 10; } \
    if (SCEN == 14) { g_save.badges = 0x01; flag_set(FLAG_BADGE_2, 0); g_save.map = MAP_GYM_BCE; g_save.x = 7; g_save.y = 3; } \
    if (SCEN == 3) { g_save.map = MAP_PARLEMENT_HALL; g_save.x = 8; g_save.y = 10; } \
    if (SCEN == 17) { flag_set(FLAG_INTRO_DONE, 1); quick_party(0, 15); g_save.map = MAP_BRUXELLES; g_save.x = 30; g_save.y = 33; g_save.dir = 1; } \
    if (SCEN == 18) { flag_set(FLAG_INTRO_DONE, 1); flag_set(FLAG_BADGE_1, 1); g_save.badges = 1; quick_party(0, 15); g_save.map = MAP_STUDIO; g_save.x = 8; g_save.y = 3; g_save.dir = 1; music_mark_heard("title"); music_mark_heard("bruxelles"); music_mark_heard("battle_wild"); music_mark_heard("route"); music_mark_heard("cantine"); music_mark_heard("labo"); music_mark_heard("victory"); music_mark_heard("battle_trainer"); music_mark_heard("luxembourg"); } \
    if (SCEN == 19) { flag_set(FLAG_INTRO_DONE, 1); quick_party(0, 15); g_save.map = MAP_CJUE_HALL; g_save.x = 3; g_save.y = 6; g_save.dir = 2; } \
    if (SCEN == 22) { flag_set(FLAG_INTRO_DONE, 1); quick_party(0, 15); g_save.map = MAP_CJUE_HALL; g_save.x = 12; g_save.y = 3; g_save.dir = 1; } \
    if (SCEN == 23) { flag_set(FLAG_INTRO_DONE, 1); quick_party(0, 15); g_save.map = MAP_STUDIO; g_save.x = 1; g_save.y = 3; g_save.dir = 1; } \
    QUICKSTART_SCREENSHOT(); \
    if (SCEN == 16) { flag_set(FLAG_INTRO_DONE, 1); g_save.map = MAP_CANTINE_BXL; g_save.x = 5; g_save.y = 4; g_save.dir = 1; } \
    if (SCEN == 31) { flag_set(FLAG_INTRO_DONE, 1); g_save.badges = 0x03; flag_set(FLAG_BADGE_1, 1); flag_set(FLAG_BADGE_2, 1); \
                      g_save.map = MAP_GYM_BCE; g_save.x = 11; g_save.y = 2; g_save.dir = 1; } \
    if (SCEN == 32) { flag_set(FLAG_INTRO_DONE, 1); g_save.badges = 0x03; flag_set(FLAG_BADGE_2, 1); flag_set(FLAG_BCE_VAULT_OPEN, 1); \
                      flag_set(FLAG_ATELIER_SEEN, 1); flag_set(FLAG_NOTE_STUDIO_PASSED, 1); g_save.map = MAP_ATELIER_BCE; g_save.x = 9; g_save.y = 7; g_save.dir = 3; } \
    if (SCEN == 33) { flag_set(FLAG_INTRO_DONE, 1); g_save.badges = 0x03; flag_set(FLAG_BADGE_2, 1); \
                      g_save.map = MAP_FRANCFORT; g_save.x = 46; g_save.y = 12; g_save.dir = 0; } \
    if (SCEN == 2) { quick_party(SP_CECAGON, 40); quick_party(SP_EUROLO, 12); flag_set(FLAG_GOT_STARTER, 1); flag_set(FLAG_GOT_DEX, 1); \
                     g_save.map = MAP_LUXEMBOURG; g_save.x = 25; g_save.y = 10; } \
} while (0)
