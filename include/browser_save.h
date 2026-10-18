#pragma once
#include "save.h"
void browser_save_init(void);
bool browser_save_connected(void);
bool browser_save_read(int slot, SaveData *out);
bool browser_save_write(int slot, const SaveData *data);
int browser_save_language(void);
void browser_save_set_language(const char *code);
