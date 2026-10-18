#pragma once
#include "common.h"

#define LINK_PACKET 256
#define LINK_BODY 239
enum { LINK_TEAM = 1, LINK_ACTION, LINK_CHECK, LINK_REPLACE };

void multiplayer_init(void);
void multiplayer_open(void);
bool link_exchange(int kind, const void *out, int size, void *in, int *received);
int link_seat(void);
u32 link_seed(void);
bool link_ok(void);
bool link_active(void);
void link_close(void);
