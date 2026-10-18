#pragma once
#include "common.h"
bool local_link_open(bool host, void (*draw_wait)(void));
bool local_link_exchange(int kind, const void *out, int size, void *in, int *received);
bool local_link_ok(void);
void local_link_close(void);
const char *local_link_error(void);
int local_link_seat(void);
u32 local_link_seed(void);
