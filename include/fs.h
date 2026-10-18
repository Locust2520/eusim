#pragma once
#include "common.h"

bool fs_init(void);
// Load a whole NitroFS file into a new malloc'd buffer (caller frees). size may be NULL. Fatal if missing.
void *fs_load(const char *path, u32 *size);
// Same but returns NULL when missing
void *fs_try_load(const char *path, u32 *size);
// Load into an existing buffer, returns bytes read (0 if missing)
u32 fs_load_into(const char *path, void *dst, u32 max);
bool fs_exists(const char *path);
