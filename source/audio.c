// Audio: the soundtrack is streamed from nitrofs/music/<name>.ads (8-bit PCM, see tools/mkstream.py) on hardware
// channel 0; the old chiptune sequencer (.sng) stays as a fallback for songs without a stream.
// SFX use channel 13 (PSG) and 15 (noise) and 4 (wave).
#include "audio.h"
#include "fs.h"
#include "save.h"
#include <stdio.h>
#include <string.h>
#include <malloc.h>

// ---------------------------------------------------------------- waveforms
#define WAVE_LEN 32
static s8 waves[6][WAVE_LEN] __attribute__((aligned(4)));

static void make_waves(void)
{
    for (int i = 0; i < WAVE_LEN; i++) {
        // 0 triangle
        int t = i < 16 ? (i * 16 - 128) : (127 - (i - 16) * 16);
        waves[0][i] = CLAMP(t, -127, 127);
        // 1 sine (table)
        static const s8 sine[32] = {0, 25, 49, 71, 90, 106, 117, 125, 127, 125, 117, 106, 90, 71, 49, 25,
                                    0, -25, -49, -71, -90, -106, -117, -125, -127, -125, -117, -106, -90, -71, -49, -25};
        waves[1][i] = sine[i];
        // 2 saw
        waves[2][i] = (s8)(i * 8 - 128);
        // 3 organ: fundamental + octave + fifth-ish
        int o = sine[i] / 2 + sine[(i * 2) & 31] / 3 + sine[(i * 3) & 31] / 6;
        waves[3][i] = CLAMP(o, -127, 127);
        // 4 soft square (rounded)
        static const s8 soft[32] = {40, 90, 110, 118, 120, 120, 120, 120, 120, 120, 120, 120, 118, 110, 90, 40,
                                    -40, -90, -110, -118, -120, -120, -120, -120, -120, -120, -120, -120, -118, -110, -90, -40};
        waves[4][i] = soft[i];
        // 5 "piano" bright: saw+sine
        int p = (i * 8 - 128) / 2 + sine[i] / 2;
        waves[5][i] = CLAMP(p, -127, 127);
    }
    DC_FlushRange(waves, sizeof(waves));
}

// ---------------------------------------------------------------- pitch
// Frequencies (Hz * 16) of MIDI notes 108..119 (octave 8); lower octaves are shifts.
static const u32 top_oct[12] = {66976, 70959, 75178, 79649, 84385, 89402,
                                94719, 100351, 106318, 112640, 119338, 126434};

static u32 note_hz16(int note) // returns Hz*16
{
    if (note < 0)
        note = 0;
    if (note > 119)
        note = 119;
    int oct = note / 12, k = note % 12;
    return top_oct[k] >> (9 - oct);
}

// ---------------------------------------------------------------- song data
typedef struct {
    u8 env_len, env_loop, release, duty_or_wave;
    u8 vib_delay, vib_depth, vib_speed;
    s8 sweep;       // pitch slide in 1/16 semitone per frame
    u8 arp_len;
    s8 arp[8];
    u8 env[32];
} Instrument;

typedef struct {
    u8 kind;     // 0 square, 1 noise, 2 wave
    u8 hw;       // hardware channel
    const u8 *pc, *loop_pc, *start;
    u8 rep_count[4];
    const u8 *rep_pc[4];
    int rep_sp;
    s32 ticks_left;  // fixed 16.16 ticks until next event
    s32 gate_left;   // fixed ticks until release
    int note, transpose, vol, pan, instr, gate_pct;
    int env_pos, frame_in_note, cur_vol, released, rel_level;
    s32 slide;       // accumulated sweep (1/16 semitone)
    int sound_id;
    bool active, playing;
    u32 last_freq;
    int last_out_vol;
} Track;

#define MAX_TRACKS 8
static Track tracks[MAX_TRACKS];
static int ntracks;
static Instrument instrs[32];
static int ninstr;
static u8 *song_data;
static char song_name[24];
static u32 tempo_step;   // 16.16 ticks per frame
static int master_vol = 110, fade_frames, fade_total, music_paused;
static volatile bool song_lock;

// ---------------------------------------------------------------- streamed music (nitrofs/music/<name>.ads)
// The real soundtrack: 8-bit PCM (or IMA-ADPCM) read from NitroFS a few hundred bytes per frame into a ring
// buffer that one hardware channel loops over. Runs on the main thread (audio_tick from frame_wait).
#define RING 32768                       // bytes = samples (8-bit), ~1.5 s at 22 kHz
#define STREAM_CH 0
extern volatile u32 g_vbl_count;
static s8 *ring;
static FILE *sf;
static u32 s_rate, s_total, s_pos, s_wr, s_start, s_spf; // s_spf: samples per frame, 16.16
static bool s_loop, s_pcm8, s_on;
static int s_id = -1, s_vol = -1;
static u8 s_buf[1024] __attribute__((aligned(32)));
static int s_blen, s_bpos, s_pred, s_idx, s_byte, s_half;
static const u16 ima_step[89] = {7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31, 34, 37, 41, 45, 50, 55,
    60, 66, 73, 80, 88, 97, 107, 118, 130, 143, 157, 173, 190, 209, 230, 253, 279, 307, 337, 371, 408, 449, 494, 544,
    598, 658, 724, 796, 876, 963, 1060, 1166, 1282, 1411, 1552, 1707, 1878, 2066, 2272, 2499, 2749, 3024, 3327, 3660,
    4026, 4428, 4871, 5358, 5894, 6484, 7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899, 15289, 16818, 18500,
    20350, 22385, 24623, 27086, 29794, 32767};
static const s8 ima_idx[8] = {-1, -1, -1, -1, 2, 4, 6, 8};

static int s_getbyte(void)
{
    if (s_bpos >= s_blen) {
        DC_FlushRange(s_buf, sizeof s_buf);
        s_blen = fread(s_buf, 1, sizeof s_buf, sf);
        DC_InvalidateRange(s_buf, sizeof s_buf);
        s_bpos = 0;
        if (s_blen <= 0)
            return 0;
    }
    return s_buf[s_bpos++];
}

static void s_rewind(void)
{
    fseek(sf, 16, SEEK_SET);
    s_blen = s_bpos = 0;
    s_pos = 0;
    s_pred = s_idx = 0;
    s_half = 0;
}

static s8 s_sample(void)
{
    if (s_pos >= s_total) {
        if (!s_loop)
            return 0;
        s_rewind();
    }
    s_pos++;
    if (s_pcm8)
        return (s8)s_getbyte();
    int code;
    if (!s_half) {
        s_byte = s_getbyte();
        code = s_byte & 15;
    } else
        code = s_byte >> 4;
    s_half ^= 1;
    int step = ima_step[s_idx], dq = step >> 3;
    if (code & 4) dq += step;
    if (code & 2) dq += step >> 1;
    if (code & 1) dq += step >> 2;
    s_pred = CLAMP(code & 8 ? s_pred - dq : s_pred + dq, -32768, 32767);
    s_idx = CLAMP(s_idx + ima_idx[code & 7], 0, 88);
    return (s8)(s_pred >> 8);
}

static void s_fill(u32 upto)
{
    u32 a = s_wr % RING, n = upto - s_wr;
    for (u32 i = 0; i < n; i++)
        ring[(s_wr + i) % RING] = s_sample();
    // the ARM7 reads main RAM directly: push the new bytes out of the data cache
    if (a + n <= RING)
        DC_FlushRange(ring + a, n);
    else {
        DC_FlushRange(ring + a, RING - a);
        DC_FlushRange(ring, n - (RING - a));
    }
    s_wr = upto;
}

static void stream_stop(void)
{
    if (s_id >= 0)
        soundKill(s_id);
    s_id = -1;
    if (sf)
        fclose(sf);
    sf = NULL;
    s_on = false;
}

static bool stream_start(const char *name)
{
    char path[64];
    snprintf(path, sizeof path, "nitro:/music/%s.ads", name);
    FILE *f = fopen(path, "rb");
    if (!f)
        return false;
    u32 hdr[4];
    if (fread(hdr, 1, 16, f) != 16 || memcmp(hdr, "ADS1", 4) != 0) {
        fclose(f);
        return false;
    }
    if (!ring) {
        ring = memalign(32, RING);
        if (!ring) {
            fclose(f);
            return false;
        }
    }
    sf = f;
    s_rate = hdr[1];
    s_total = hdr[2];
    s_loop = hdr[3] & 1;
    s_pcm8 = (hdr[3] & 2) != 0;
    s_rewind();
    // hardware rate as programmed by the ARM7 (integer timer divider of the 16.756991 MHz sound clock)
    u32 div = 0x1000000 / s_rate;
    s_spf = (u32)((u64)16756991 * 65536 / div * 1000 / 59826);  // per 59.8261 Hz frame
    s_wr = 0;
    s_fill(RING - 1024);
    s_vol = 0;
    s_id = soundPlaySampleChannel(STREAM_CH, ring, SoundFormat_8Bit, RING, s_rate, 0, 64, true, 0);
    s_start = g_vbl_count;
    s_on = true;
    return true;
}

static void stream_tick(int vol)
{
    if (!s_on)
        return;
    u32 played = (u32)((u64)(g_vbl_count - s_start) * s_spf >> 16);
    if (s_wr < played + 256)              // fell behind (long load): skip ahead instead of replaying old audio
        s_wr = played + 256;
    u32 target = played + RING - 1024;
    if (s_wr < target)
        s_fill(target);
    if (vol != s_vol && s_id >= 0) {
        soundSetVolume(s_id, vol);
        s_vol = vol;
    }
}


static int read_len(Track *t)
{
    int v = *t->pc++;
    if (v == 0) {
        v = t->pc[0] | (t->pc[1] << 8);
        t->pc += 2;
    }
    return v;
}

static void track_silence(Track *t)
{
    if (t->sound_id >= 0) {
        soundKill(t->sound_id);
        t->sound_id = -1;
    }
    t->playing = false;
}

static void set_tempo(int bpm)
{
    // 48 ticks per quarter note; frames at ~59.83 Hz
    tempo_step = (u32)(((u64)bpm * 48 * 65536) / 3590);
}

static u32 track_freq(Track *t, const Instrument *in)
{
    int n16 = (t->note + t->transpose) * 16 + t->slide;
    if (in->arp_len)
        n16 += in->arp[t->frame_in_note % in->arp_len] * 16;
    if (in->vib_depth && t->frame_in_note >= in->vib_delay) {
        int ph = ((t->frame_in_note - in->vib_delay) * in->vib_speed) & 63;
        int tri = ph < 32 ? ph - 16 : 48 - ph; // -16..16
        n16 += (tri * in->vib_depth) / 16;
    }
    if (n16 < 0)
        n16 = 0;
    int base = n16 >> 4, frac = n16 & 15;
    u32 f0 = note_hz16(base), f1 = note_hz16(base + 1);
    u32 f = f0 + ((f1 - f0) * frac >> 4); // Hz*16
    return f;
}

static void track_note_on(Track *t)
{
    const Instrument *in = &instrs[t->instr < ninstr ? t->instr : 0];
    t->env_pos = 0;
    t->frame_in_note = 0;
    t->released = 0;
    t->slide = 0;
    t->playing = true;
    if (t->sound_id >= 0)
        soundKill(t->sound_id);
    u32 f16 = track_freq(t, in);
    int vol = 0;
    if (t->kind == 0) {
        t->sound_id = soundPlayPSGChannel(t->hw, (DutyCycle)(in->duty_or_wave & 7), f16 >> 4, vol, t->pan);
    } else if (t->kind == 1) {
        // noise: note number maps to noise frequency
        u32 nf = note_hz16(t->note + t->transpose) >> 2;
        if (nf > 65000)
            nf = 65000;
        t->sound_id = soundPlayNoiseChannel(t->hw, nf, vol, t->pan);
    } else {
        u32 rate = (f16 * WAVE_LEN) >> 4;
        if (rate > 65535)
            rate = 65535;
        t->sound_id = soundPlaySampleChannel(t->hw, waves[in->duty_or_wave % 6], SoundFormat_8Bit,
                                             WAVE_LEN, rate, vol, t->pan, true, 0);
    }
    t->last_freq = 0;
    t->last_out_vol = -1;
}

static void track_update_voice(Track *t)
{
    if (!t->playing || t->sound_id < 0)
        return;
    const Instrument *in = &instrs[t->instr < ninstr ? t->instr : 0];
    int ev;
    if (!t->released) {
        if (t->env_pos < in->env_len) {
            ev = in->env[t->env_pos];
            t->env_pos++;
            if (t->env_pos >= in->env_len && in->env_loop != 0xFF)
                t->env_pos = in->env_loop;
        } else {
            ev = in->env_len ? in->env[in->env_len - 1] : 127;
        }
        t->rel_level = ev;
    } else {
        t->rel_level -= in->release ? in->release : 127;
        if (t->rel_level <= 0) {
            t->rel_level = 0;
            track_silence(t);
            return;
        }
        ev = t->rel_level;
    }
    t->slide += in->sweep;
    int fv = (fade_total > 0) ? (master_vol * fade_frames / fade_total) : master_vol;
    if (music_paused)
        fv = 0;
    int out = (ev * t->vol / 127) * fv / 127;
    if (out != t->last_out_vol) {
        soundSetVolume(t->sound_id, out);
        t->last_out_vol = out;
    }
    if (t->kind != 1) {
        u32 f16 = track_freq(t, in);
        u32 f = (t->kind == 0) ? (f16 >> 4) : ((f16 * WAVE_LEN) >> 4);
        if (f > 65535)
            f = 65535;
        if (f != t->last_freq && t->frame_in_note > 0) {
            soundSetFreq(t->sound_id, f);
        }
        t->last_freq = f;
    }
    t->frame_in_note++;
}

static void track_step(Track *t)
{
    t->ticks_left -= tempo_step;
    if (t->playing && !t->released) {
        t->gate_left -= tempo_step;
        if (t->gate_left <= 0)
            t->released = 1;
    }
    while (t->active && t->ticks_left <= 0) {
        u8 op = *t->pc++;
        if (op < 0x80) {
            t->note = op;
            int len = read_len(t);
            t->ticks_left += len << 16;
            t->gate_left = ((len * t->gate_pct) / 100) << 16;
            if (t->gate_left <= 0)
                t->gate_left = 1 << 16;
            track_note_on(t);
            continue;
        }
        switch (op) {
        case 0x80: { // rest
            int len = read_len(t);
            t->ticks_left += len << 16;
            if (t->playing)
                t->released = 1;
            break;
        }
        case 0x81: t->instr = *t->pc++; break;
        case 0x82: t->vol = *t->pc++; break;
        case 0x83: t->pan = *t->pc++; break;
        case 0x84: t->loop_pc = t->pc; break;
        case 0x85:
            if (t->rep_sp < 4) {
                t->rep_count[t->rep_sp] = *t->pc++;
                t->rep_pc[t->rep_sp] = t->pc;
                t->rep_sp++;
            } else
                t->pc++;
            break;
        case 0x86:
            if (t->rep_sp > 0) {
                int i = t->rep_sp - 1;
                if (--t->rep_count[i] > 0)
                    t->pc = t->rep_pc[i];
                else
                    t->rep_sp--;
            }
            break;
        case 0x87: t->transpose = (s8)*t->pc++; break;
        case 0x88: { // tie
            int len = read_len(t);
            t->ticks_left += len << 16;
            t->gate_left += ((len * t->gate_pct) / 100) << 16;
            break;
        }
        case 0x89: {
            int bpm = t->pc[0] | (t->pc[1] << 8);
            t->pc += 2;
            set_tempo(bpm);
            break;
        }
        case 0x8A: t->gate_pct = *t->pc++; break;
        case 0xFF:
        default:
            if (t->loop_pc) {
                t->pc = t->loop_pc;
                t->rep_sp = 0;
            } else {
                t->active = false;
                if (t->playing)
                    t->released = 1;
                t->ticks_left = 0x7FFFFFFF;
            }
            break;
        }
    }
}

static void music_tick(void)
{
    if (s_on) {
        int v = master_vol * 100 / 127;
        if (fade_total > 0) {
            if (--fade_frames <= 0) {
                fade_total = 0;
                stream_stop();
                song_name[0] = 0;
                return;
            }
            v = v * fade_frames / fade_total;
        }
        stream_tick(music_paused ? 0 : v);
        return;
    }
    if (!song_data || song_lock)
        return;
    if (fade_total > 0) {
        if (--fade_frames <= 0) {
            fade_total = 0;
            for (int i = 0; i < ntracks; i++) {
                track_silence(&tracks[i]);
                tracks[i].active = false;
            }
            free(song_data);
            song_data = NULL;
            song_name[0] = 0;
            ntracks = 0;
            return;
        }
    }
    bool any = false;
    for (int i = 0; i < ntracks; i++) {
        Track *t = &tracks[i];
        if (t->active)
            track_step(t);
        track_update_voice(t);
        any |= t->active || t->playing;
    }
    (void)any;
}


void music_stop(void)
{
    stream_stop();
    song_lock = true;
    for (int i = 0; i < ntracks; i++)
        track_silence(&tracks[i]);
    ntracks = 0;
    if (song_data)
        free(song_data);
    song_data = NULL;
    song_name[0] = 0;
    fade_total = 0;
    song_lock = false;
}

void music_play(const char *name)
{
    if ((song_data || s_on) && strcmp(name, song_name) == 0 && fade_total == 0)
        return;
    music_stop();
    music_mark_heard(name);
    if (stream_start(name)) {
        strncpy(song_name, name, sizeof(song_name) - 1);
        song_name[sizeof(song_name) - 1] = 0;
        fade_total = 0;
        return;
    }
    char path[48];
    snprintf(path, sizeof(path), "music/%s.sng", name);
    u32 size;
    u8 *d = fs_try_load(path, &size);
    if (!d)
        return;
    if (d[0] != 'S' || d[1] != 'N' || d[2] != 'G') {
        free(d);
        return;
    }
    song_lock = true;
    int nt = d[4];
    int bpm = d[5] | (d[6] << 8);
    ninstr = d[7];
    const u8 *p = d + 8;
    for (int i = 0; i < ninstr && i < 32; i++) {
        Instrument *in = &instrs[i];
        memset(in, 0, sizeof(*in));
        in->env_len = p[0];
        in->env_loop = p[1];
        in->release = p[2];
        in->duty_or_wave = p[3];
        in->vib_delay = p[4];
        in->vib_depth = p[5];
        in->vib_speed = p[6];
        in->sweep = (s8)p[7];
        in->arp_len = p[8];
        for (int k = 0; k < 8; k++)
            in->arp[k] = (s8)p[9 + k];
        p += 17;
        for (int k = 0; k < in->env_len && k < 32; k++)
            in->env[k] = p[k];
        p += in->env_len;
    }
    ntracks = MIN(nt, MAX_TRACKS);
    for (int i = 0; i < ntracks; i++) {
        Track *t = &tracks[i];
        memset(t, 0, sizeof(*t));
        t->kind = p[0];
        t->hw = p[1];
        u16 off = p[2] | (p[3] << 8);
        p += 4;
        t->start = d + off;
        t->pc = t->start;
        t->vol = 100;
        t->pan = 64;
        t->gate_pct = 90;
        t->sound_id = -1;
        t->active = true;
        t->ticks_left = 0;
    }
    set_tempo(bpm);
    song_data = d;
    strncpy(song_name, name, sizeof(song_name) - 1);
    fade_total = 0;
    song_lock = false;
}

void music_fade_out(int frames)
{
    if (!song_data && !s_on)
        return;
    fade_total = frames;
    fade_frames = frames;
}

bool music_is_playing(void) { return song_data != NULL || s_on; }
void music_set_volume(int v) { master_vol = CLAMP(v, 0, 127); }
const char *music_current(void) { return song_name; }
void music_pause(bool p) { music_paused = p; }

// ---------------------------------------------------------------- SFX
typedef struct {
    u8 kind;          // 0 square, 1 noise, 2 wave(triangle)
    u8 duty;
    u16 f0, f1;       // start/end frequency (Hz; noise: noise freq)
    u8 v0, v1;        // start/end volume
    u8 frames;
} SfxSeg;

typedef struct {
    const SfxSeg *seg;
    int nseg;
} Sfx;

#define S(k, d, f0, f1, v0, v1, n) {k, d, f0, f1, v0, v1, n}
static const SfxSeg s_blip[] = {S(0, 2, 880, 880, 50, 0, 3)};
static const SfxSeg s_select[] = {S(0, 2, 1047, 1047, 80, 60, 3), S(0, 2, 1568, 1568, 80, 0, 6)};
static const SfxSeg s_cancel[] = {S(0, 2, 784, 784, 80, 60, 3), S(0, 2, 523, 523, 80, 0, 6)};
static const SfxSeg s_cursor[] = {S(0, 1, 1320, 1320, 60, 0, 3)};
static const SfxSeg s_bump[] = {S(0, 4, 110, 80, 90, 0, 6)};
static const SfxSeg s_door[] = {S(1, 0, 3000, 1200, 90, 0, 10), S(0, 2, 220, 180, 60, 0, 6)};
static const SfxSeg s_stamp[] = {S(1, 0, 6000, 800, 127, 0, 8), S(0, 4, 90, 60, 100, 0, 6)};
static const SfxSeg s_hit[] = {S(1, 0, 8000, 1500, 127, 0, 10)};
static const SfxSeg s_hit_super[] = {S(1, 0, 12000, 2000, 127, 60, 6), S(1, 0, 4000, 800, 127, 0, 12)};
static const SfxSeg s_hit_weak[] = {S(1, 0, 3000, 1500, 70, 0, 8)};
static const SfxSeg s_faint[] = {S(0, 2, 880, 110, 100, 0, 40)};
static const SfxSeg s_heal[] = {S(0, 2, 523, 523, 80, 70, 6), S(0, 2, 659, 659, 80, 70, 6), S(0, 2, 784, 784, 80, 70, 6), S(0, 2, 1047, 1047, 90, 0, 16)};
static const SfxSeg s_levelup[] = {S(0, 2, 784, 784, 90, 80, 6), S(0, 2, 988, 988, 90, 80, 6), S(0, 2, 1175, 1175, 90, 80, 6), S(0, 2, 1568, 1568, 100, 0, 18)};
static const SfxSeg s_shake[] = {S(0, 4, 300, 200, 80, 0, 8)};
static const SfxSeg s_capture[] = {S(0, 2, 1047, 1047, 100, 100, 5), S(0, 2, 1319, 1319, 100, 100, 5), S(0, 2, 1568, 1568, 100, 100, 5), S(0, 2, 2093, 2093, 110, 0, 20)};
static const SfxSeg s_throw[] = {S(0, 2, 400, 1600, 70, 30, 12)};
static const SfxSeg s_sms[] = {S(0, 2, 1760, 1760, 90, 90, 4), S(0, 2, 0, 0, 0, 0, 3), S(0, 2, 1760, 1760, 90, 90, 4), S(0, 2, 2349, 2349, 90, 0, 8)};
static const SfxSeg s_gavel[] = {S(1, 0, 5000, 600, 127, 0, 6), S(0, 4, 0, 0, 0, 0, 6), S(1, 0, 5000, 600, 127, 0, 6)};
static const SfxSeg s_vote[] = {S(0, 2, 1568, 1568, 90, 0, 10)};
static const SfxSeg s_paper[] = {S(1, 0, 20000, 9000, 50, 0, 8), S(1, 0, 16000, 9000, 40, 0, 6)};
static const SfxSeg s_coin[] = {S(0, 2, 1976, 1976, 90, 90, 4), S(0, 2, 2637, 2637, 90, 0, 16)};
static const SfxSeg s_error[] = {S(0, 4, 200, 200, 100, 100, 8), S(0, 4, 0, 0, 0, 0, 3), S(0, 4, 160, 160, 100, 0, 12)};
static const SfxSeg s_star[] = {S(0, 2, 2093, 3136, 70, 0, 10)};
static const SfxSeg s_exp[] = {S(0, 1, 600, 2400, 50, 30, 30)};
static const SfxSeg s_save[] = {S(0, 2, 784, 784, 80, 80, 8), S(0, 2, 1047, 1047, 80, 0, 16)};
static const SfxSeg s_train[] = {S(1, 0, 2000, 2000, 60, 60, 6), S(1, 0, 2000, 2000, 20, 20, 6), S(1, 0, 2000, 2000, 60, 60, 6), S(1, 0, 2000, 2000, 0, 0, 6)};
static const SfxSeg s_jump[] = {S(0, 2, 300, 900, 80, 0, 10)};
static const SfxSeg s_alarm[] = {S(0, 2, 988, 988, 100, 100, 10), S(0, 2, 740, 740, 100, 100, 10), S(0, 2, 988, 988, 100, 100, 10), S(0, 2, 740, 740, 100, 0, 10)};
static const SfxSeg s_whoosh[] = {S(1, 0, 2000, 12000, 20, 90, 8), S(1, 0, 12000, 3000, 90, 0, 10)};
static const SfxSeg s_statup[] = {S(0, 2, 400, 1600, 80, 40, 16), S(0, 2, 800, 2400, 80, 0, 12)};
static const SfxSeg s_statdown[] = {S(0, 2, 1600, 400, 80, 40, 16), S(0, 2, 1000, 200, 80, 0, 12)};
#undef S
#define E(a) {a, ARRAY_LEN(a)}
static const Sfx sfx_table[SFX_COUNT] = {
    E(s_blip), E(s_select), E(s_cancel), E(s_cursor), E(s_bump), E(s_door), E(s_stamp),
    E(s_hit), E(s_hit_super), E(s_hit_weak), E(s_faint), E(s_heal), E(s_levelup),
    E(s_shake), E(s_capture), E(s_throw), E(s_sms), E(s_gavel), E(s_vote),
    E(s_paper), E(s_coin), E(s_error), E(s_star), E(s_exp), E(s_save), E(s_train),
    E(s_jump), E(s_alarm), E(s_whoosh), E(s_statup), E(s_statdown),
};
#undef E

typedef struct {
    SfxSeg segs[8];
    int nseg, seg, frame, sound_id, hwkind;
    bool active;
} SfxVoice;

static SfxVoice sv[2]; // 0 = tone/wave (ch 13 / ch 4), 1 = noise (ch 15)
static volatile int pending_sfx = -1, pending_voice = -1, pending_cry = -1;

static void sfx_start_voice(SfxVoice *v, const SfxSeg *segs, int n)
{
    if (v->sound_id >= 0)
        soundKill(v->sound_id);
    v->sound_id = -1;
    memcpy(v->segs, segs, sizeof(SfxSeg) * MIN(n, 8));
    v->nseg = MIN(n, 8);
    v->seg = 0;
    v->frame = 0;
    v->active = true;
    v->hwkind = -1;
}

static void sfx_voice_tick(SfxVoice *v, int chan_tone, int chan_noise)
{
    if (!v->active)
        return;
    if (v->seg >= v->nseg) {
        if (v->sound_id >= 0)
            soundKill(v->sound_id);
        v->sound_id = -1;
        v->active = false;
        return;
    }
    const SfxSeg *s = &v->segs[v->seg];
    int n = s->frames ? s->frames : 1;
    int f = s->f0 + ((int)s->f1 - (int)s->f0) * v->frame / n;
    int vol = s->v0 + ((int)s->v1 - (int)s->v0) * v->frame / n;
    vol = vol * 110 / 127;
    if (v->frame == 0 || v->hwkind != s->kind) {
        if (v->sound_id >= 0)
            soundKill(v->sound_id);
        v->sound_id = -1;
        if (f > 0) {
            if (s->kind == 1)
                v->sound_id = soundPlayNoiseChannel(chan_noise, f, vol, 64);
            else
                v->sound_id = soundPlayPSGChannel(chan_tone, (DutyCycle)s->duty, f, vol, 64);
        }
        v->hwkind = s->kind;
    } else if (v->sound_id >= 0) {
        soundSetFreq(v->sound_id, f > 0 ? f : 1);
        soundSetVolume(v->sound_id, vol);
    }
    if (++v->frame >= n) {
        v->frame = 0;
        v->seg++;
    }
}

void sfx_play(SfxId id)
{
    if (id >= 0 && id < SFX_COUNT)
        pending_sfx = id;
}

void sfx_voice(int pitch)
{
    pending_voice = pitch;
}

void sfx_cry(int species)
{
    pending_cry = species;
}

static void process_pending(void)
{
    int id = pending_sfx;
    if (id >= 0) {
        pending_sfx = -1;
        const Sfx *s = &sfx_table[id];
        bool noise = false;
        for (int i = 0; i < s->nseg; i++)
            if (s->seg[i].kind == 1)
                noise = true;
        sfx_start_voice(noise ? &sv[1] : &sv[0], s->seg, s->nseg);
    }
    int p = pending_voice;
    if (p >= 0) {
        pending_voice = -1;
        if (!sv[0].active) {
            SfxSeg seg = {0, 2, (u16)(300 + p * 40), (u16)(300 + p * 40), 36, 0, 3};
            sfx_start_voice(&sv[0], &seg, 1);
        }
    }
    int c = pending_cry;
    if (c >= 0) {
        pending_cry = -1;
        // deterministic cry from species id
        u32 h = (u32)c * 2654435761u;
        SfxSeg segs[4];
        int base = 300 + (h % 700);
        for (int i = 0; i < 4; i++) {
            h = h * 1103515245u + 12345u;
            int f0 = base + (int)(h % 400) - 200;
            int f1 = f0 + (int)((h >> 9) % 600) - 300;
            segs[i].kind = 0;
            segs[i].duty = (h >> 4) % 4;
            segs[i].f0 = CLAMP(f0, 80, 4000);
            segs[i].f1 = CLAMP(f1, 80, 4000);
            segs[i].v0 = 100;
            segs[i].v1 = i == 3 ? 0 : 70;
            segs[i].frames = 4 + (h >> 13) % 8;
        }
        sfx_start_voice(&sv[0], segs, 4);
    }
}

// ---------------------------------------------------------------- mic
static int mic_lvl;
static u8 *mic_buf;
static void mic_cb(void *data, int len)
{
    u8 *d = data;
    int mx = 0;
    for (int i = 0; i < len; i++) {
        int v = (int)d[i] - 128;
        if (v < 0)
            v = -v;
        if (v > mx)
            mx = v;
    }
    mic_lvl = mx * 2;
}
void mic_start(void)
{
    if (!mic_buf)
        mic_buf = malloc(1600);
    mic_lvl = 0;
    soundMicRecord(mic_buf, 1600, MicFormat_8Bit, 8000, mic_cb);
}
void mic_stop(void)
{
    soundMicOff();
}
int mic_level(void)
{
    return mic_lvl;
}

// ---------------------------------------------------------------- tick
void audio_init(void)
{
    make_waves();
    sv[0].sound_id = sv[1].sound_id = -1;
    for (int i = 0; i < MAX_TRACKS; i++)
        tracks[i].sound_id = -1;
}

void audio_tick(void)
{
    music_tick();
    process_pending();
    sfx_voice_tick(&sv[0], 13, 15);
    sfx_voice_tick(&sv[1], 13, 15);
}

// ---------------------------------------------------------------- jukebox catalogue
// Order = jukebox order. The "heard" bits live in the save (vars 60..63), so the jukebox only lists
// what the player has already met in the game.
const MusicInfo g_music_list[] = {
    {"title", "Title screen"}, {"intro", "Meet Professor Schuman"}, {"labo", "The laboratory"},
    {"home", "Your studio"}, {"bruxelles", "Brussels"}, {"cantine", "The canteen"}, {"shop", "The shop"},
    {"gare", "The station"}, {"route", "On the road"}, {"battle_wild", "Battle: wild Euromon"},
    {"encounter", "Eye contact"}, {"battle_trainer", "Battle: trainer"}, {"rival", "Battle: Oliver"},
    {"victory", "Victory"}, {"victory_wild", "Victory (wild)"}, {"victory_trainer", "Victory (trainer)"},
    {"evolution", "Evolution"}, {"luxembourg", "Luxembourg"}, {"gym", "The arena"},
    {"battle_gym", "Battle: arena"}, {"gym_leader", "Battle: arena leader"}, {"schengen", "Schengen"},
    {"francfort", "Frankfurt"}, {"strasbourg", "Strasbourg"}, {"minigame", "Minigame"},
    {"athenes", "Athens"}, {"londres", "London"}, {"sad", "Goodbye, Oliver"}, {"budapest", "Budapest"},
    {"lobby", "The Team Lobby"}, {"boss", "Battle: boss"}, {"ghost", "The ghost wing"}, {"paris", "Paris"},
    {"council_hall", "The European Council"}, {"council", "Battle: Council"},
    {"champion_hall", "The 13th floor"}, {"champion", "Battle: the President"},
    {"powers_map", "The Great Powers"}, {"trump", "Antwerp"}, {"putin", "Warsaw"}, {"xi", "Piraeus"},
    {"powers", "Battle: Great Powers"}, {"sommet_hall", "The G-Everything Summit"}, {"final", "Final battle"},
    {"ending", "Epilogue"}, {"legend", "Legendary places"}, {"battle_legend", "Battle: legendary"},
    {"battle_final", "Final battle (variant)"},
};
const int g_music_count = sizeof g_music_list / sizeof g_music_list[0];

#define HEARD_VAR 60
static int music_index(const char *name)
{
    for (int i = 0; i < g_music_count; i++)
        if (strcmp(g_music_list[i].file, name) == 0)
            return i;
    return -1;
}

void music_mark_heard(const char *name)
{
    int i = music_index(name);
    if (i >= 0)
        g_save.vars[HEARD_VAR + i / 16] |= 1 << (i % 16);
}

bool music_heard(int i)
{
    return i >= 0 && i < g_music_count && (g_save.vars[HEARD_VAR + i / 16] >> (i % 16)) & 1;
}

u32 music_position(u32 *total, u32 *rate)
{
    if (total)
        *total = s_on ? s_total : 0;
    if (rate)
        *rate = s_on ? s_rate : 1;
    if (!s_on)
        return 0;
    // what is actually heard (the decoder runs ~1.5 s ahead in the ring buffer)
    u32 played = (u32)((u64)(g_vbl_count - s_start) * s_spf >> 16);
    if (s_loop && s_total)
        return played % s_total;
    return MIN(played, s_total);
}
