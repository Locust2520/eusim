#pragma once
#include "common.h"

#define PARTY_MAX 6
#define BOX_MAX 120
#define NUM_ITEMS 96
#define NUM_FLAGS 2048
#define NUM_VARS 64

typedef struct {
    u16 species;
    u8 level;
    u8 status;       // STATUS_* (data.h)
    u16 hp;
    u16 pad;
    u32 exp;
    u16 moves[4];
    u8 pp[4];
    u32 ivs;         // 6 x 5 bits
    u8 sleep_turns;
    u8 shiny;
    u8 friendship;
    u8 pad2;
} Mon;

typedef struct {
    u32 magic;
    u16 version;
    u16 checksum;
    char player_name[12];
    u8 player_gender;   // 0 = Alex (fille), 1 = Max (garçon)
    u8 chapter;
    u8 badges;          // bitmask of 8 badges
    u8 opt_text_speed;  // 0 slow 1 normal 2 fast
    u8 opt_music;       // 0..4
    u8 opt_battle_anim; // 1 on
    u8 opt_text_mute;   // 0 = typing sound on (default)
    u8 opt_pad[1];
    u32 money;
    u32 play_frames;
    u16 map;
    s16 x, y;
    u8 dir;
    u8 party_count;
    u16 heal_map;
    s16 heal_x, heal_y;
    u16 box_count;
    u16 repel;
    u8 flags[NUM_FLAGS / 8];
    u16 vars[NUM_VARS];
    u8 bag[NUM_ITEMS];
    u8 dex_seen[16];
    u8 dex_caught[16];
    Mon party[PARTY_MAX];
    Mon box[BOX_MAX];
} SaveData;

extern SaveData g_save;

#define SAVE_SLOTS 3
typedef struct {
    bool used;
    char name[12];
    u8 badges, gender;
    u32 play_frames;
    u16 map;
    u8 dex;
} SlotInfo;

extern int g_save_slot;             // current slot (0..2)
extern const char *g_rom_path;      // argv[0] from the loader (for saves next to the ROM)
void save_new_game(void);
bool save_exists(void);             // any slot used
bool save_slot_info(int slot, SlotInfo *out);
bool save_load(int slot);
bool save_write(void);              // writes g_save into g_save_slot
const char *save_backend(void);
bool save_available(void);
int save_lang_load(void);           // stored language index, -1 if none
void save_lang_store(int index);

static inline bool flag_get(int f) { return (g_save.flags[f >> 3] >> (f & 7)) & 1; }
static inline void flag_set(int f, bool v)
{
    if (v)
        g_save.flags[f >> 3] |= 1 << (f & 7);
    else
        g_save.flags[f >> 3] &= ~(1 << (f & 7));
}
