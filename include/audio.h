#pragma once
#include "common.h"

// Music: songs are compiled by tools/mml.py into nitrofs/music/<name>.sng
void audio_init(void);
void audio_tick(void);                 // called from frame_wait, once per elapsed VBlank
void music_play(const char *name);     // no-op if already playing the same song
void music_stop(void);
void music_fade_out(int frames);
bool music_is_playing(void);
void music_set_volume(int v);          // 0..127
const char *music_current(void);
// Temporarily duck/mute the music (e.g. jingle playing)
void music_pause(bool p);
// Jukebox: every soundtrack piece, in listening order, and which ones the player has heard
typedef struct { const char *file, *title; } MusicInfo;
extern const MusicInfo g_music_list[];
extern const int g_music_count;
void music_mark_heard(const char *name);
bool music_heard(int index);
u32 music_position(u32 *total, u32 *rate);   // streamed track: samples decoded so far

// Sound effects (built-in table in sfx.c)
typedef enum {
    SFX_BLIP, SFX_SELECT, SFX_CANCEL, SFX_CURSOR, SFX_BUMP, SFX_DOOR, SFX_STAMP,
    SFX_HIT, SFX_HIT_SUPER, SFX_HIT_WEAK, SFX_FAINT, SFX_HEAL, SFX_LEVELUP,
    SFX_CAPTURE_SHAKE, SFX_CAPTURE_OK, SFX_THROW, SFX_SMS, SFX_GAVEL, SFX_VOTE,
    SFX_PAPER, SFX_COIN, SFX_ERROR, SFX_STAR, SFX_EXP, SFX_SAVE, SFX_TRAIN,
    SFX_JUMP, SFX_ALARM, SFX_WHOOSH, SFX_STATUP, SFX_STATDOWN, SFX_COUNT
} SfxId;
void sfx_play(SfxId id);
// Talking blip with pitch variant (per character voice)
void sfx_voice(int pitch);
// Creature cry: procedurally generated from species id
void sfx_cry(int species);
// Microphone loudness 0..255 (for the blow mini-game), updated by mic_update()
void mic_start(void);
void mic_stop(void);
int mic_level(void);
