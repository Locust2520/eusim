#pragma once
#include "common.h"

void script_init(void);
void script_run(int id);            // blocking
bool script_running(void);
const char *script_string(int idx);
extern int g_script_actor;          // actor that triggered the script (talked-to NPC), 0 = player
