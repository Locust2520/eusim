#pragma once
#include "common.h"

#define NUM_TYPES 16
enum { STAT_HP, STAT_ATK, STAT_DEF, STAT_SPA, STAT_SPD, STAT_SPE, STAT_ACC, STAT_EVA };
enum { CAT_PHYS, CAT_SPEC, CAT_STATUS };
enum { STATUS_NONE, STATUS_LOBBY, STATUS_SCANDALE, STATUS_GEL, STATUS_SOMMEIL, STATUS_BLOQUE };
enum { GROW_FAST, GROW_MEDIUM, GROW_SLOW, GROW_PARABOLIC };
enum {
    EF_NONE, EF_LOBBY, EF_SCANDALE, EF_GEL, EF_SOMMEIL, EF_BLOQUE, EF_CONFUSE, EF_FLINCH,
    EF_STAT_UP, EF_STAT_DOWN, EF_HEAL_HALF, EF_DRAIN, EF_RECOIL, EF_MULTI_HIT, EF_HIGH_CRIT,
    EF_FIXED_LEVEL, EF_PROTECT, EF_PAY_DAY, EF_REST, EF_CHARGE, EF_HAZE, EF_LEAVE, EF_COPY,
    EF_ERASE, EF_ALWAYS_HIT, EF_STEAL_TURN, EF_SELF_DESTRUCT, EF_TRAP,
};
enum { IK_BALL, IK_HEAL, IK_STATUS, IK_REVIVE, IK_PP, IK_BATTLE, IK_EVO, IK_KEY, IK_REPEL, IK_MISC };

typedef struct {
    const char *name;
    u8 type, cat, power, acc, pp, effect, chance, param;
    s8 priority;
    const char *desc;
} MoveData;

typedef struct {
    const char *name;
    u8 num;
    u8 type1, type2;      // type2 == type1 if single type
    u8 base[6];
    u8 growth, catch_rate;
    u16 exp_yield;
    u16 evo_into;         // 0xFFFF none
    u8 evo_level;         // 0 if item evolution
    u16 evo_item;         // 0xFFFF none
    const u16 *learn;     // pairs (level, move), terminated by 0xFFFF
    const char *dex;
    const char *category;
} SpeciesData;

typedef struct {
    const char *name;
    u8 kind;
    u16 price;
    u16 param;
    const char *desc;
} ItemData;

typedef struct {
    const char *name;         // e.g. "Lobbyiste Hugo"
    const char *cls;          // class label
    const char *portrait;     // portrait id or NULL (uses overworld sprite)
    u16 sprite;
    u16 money;
    u8 ai, npoke;
    const u16 *party;         // (species, level) pairs
    const char *intro, *defeat, *win;
    const char *music;
} TrainerData;

typedef struct {
    u16 species;
    u8 min, max, weight;
} EncSlot;

typedef struct {
    u8 rate;      // % per step on encounter tiles
    u8 n;
    const EncSlot *slots;
} EncTable;

extern const char *type_names[NUM_TYPES];
extern const u8 type_chart[NUM_TYPES][NUM_TYPES]; // 0=immune 1=0.5 2=1 4=2
extern MoveData moves[];
extern SpeciesData species[];
extern ItemData items[];
extern TrainerData trainers[];
extern const EncTable enc_tables[];
extern const int NUM_MOVES, NUM_SPECIES, NUM_ITEMS_DEF, NUM_TRAINERS, NUM_ENC;

#include "gen/data_ids.h"
