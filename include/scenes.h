#pragma once
#include "common.h"

int scene_title(void);              // 0 new, 1 continue, 2 options, 3 credits
void loading_screen(int min_frames);
bool keyboard_input(const char *prompt, char *out, size_t capacity, int maxlen);
void scene_options(bool in_game);
void scene_credits(void);
void scene_intro(void);             // new game intro (Prof. Schuman), sets name etc.
void viewer_open(const char *path, const char *title);
void ending_run(void);
int slot_picker(int mode);   // 0 continue, 1 new game, 2 save; returns slot or -1
int lang_picker(int current);           // returns the chosen language index
