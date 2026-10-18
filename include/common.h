// EU Simulator — common definitions
#pragma once

#include <nds.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define SCREEN_W 256
#define SCREEN_H 192

#define ARRAY_LEN(a) ((int)(sizeof(a) / sizeof((a)[0])))
#define MIN(a, b) ((a) < (b) ? (a) : (b))
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define CLAMP(v, lo, hi) ((v) < (lo) ? (lo) : (v) > (hi) ? (hi) : (v))

// Frame counter, incremented once per main-loop frame.
extern u32 g_frame;

// Wait for the next frame: flushes canvases, updates OAM, runs audio, reads input.
void frame_wait(void);

// Per-frame hooks run by frame_wait() before the VBlank wait
typedef void (*FrameHook)(void);
void frame_hook_add(FrameHook fn);
void frame_hook_remove(FrameHook fn);

// Simple deterministic RNG (xorshift)
u32 rng_next(void);
int rng_range(int n);  // 0..n-1
void rng_seed(u32 s);

// Fatal error screen
void fatal(const char *fmt, ...) __attribute__((noreturn));
