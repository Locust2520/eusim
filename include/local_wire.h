#pragma once
#include "common.h"

#define LOCAL_WIRE_BYTES 264
#define LOCAL_WIRE_BODY 239
// One reliable exchange at a time. READY hides choices until both have chosen;
// DATA retries and duplicate ACKs continue from the per-frame pump during menus.
typedef struct {
    u32 cookie, build, sequence, ready_sequence, ack_sequence, last_sent;
    int kind, size, received, ready_kind, ack_kind;
    bool offered, remote_ready, got, acked, ack_pending, ready_seen, failed;
    u8 out[LOCAL_WIRE_BODY], in[LOCAL_WIRE_BODY];
} LocalWire;
void local_wire_init(LocalWire *w, u32 cookie, u32 build);
bool local_wire_offer(LocalWire *w, int kind, const void *data, int size);
void local_wire_receive(LocalWire *w, const u8 *packet, int size);
bool local_wire_poll(LocalWire *w, u32 frame, u8 *packet);
bool local_wire_take(LocalWire *w, void *data, int *size);
