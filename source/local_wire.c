// Hardware-independent stop-and-wait link for the two nearby consoles.
#include "local_wire.h"

static void lw_put(u8 *b, u32 v) { for (int i = 0; i < 4; i++) b[i] = v >> (i * 8); }
static u32 lw_get(const u8 *b) { return (u32)b[0] | (u32)b[1]<<8 | (u32)b[2]<<16 | (u32)b[3]<<24; }
void local_wire_init(LocalWire *w, u32 cookie, u32 build)
{
    memset(w, 0, sizeof *w); w->cookie = cookie; w->build = build;
}
bool local_wire_offer(LocalWire *w, int kind, const void *data, int size)
{
    if (w->offered || w->failed || kind < 1 || kind > 4 || size < 0 || size > LOCAL_WIRE_BODY) return false;
    w->kind = kind; w->size = size; w->got = w->acked = false; w->received = 0;
    w->remote_ready = w->ready_seen && w->ready_sequence == w->sequence;
    if (w->remote_ready && w->ready_kind != kind) { w->failed = true; return false; }
    memcpy(w->out, data, size); w->offered = true; w->last_sent = (u32)-6; return true;
}
void local_wire_receive(LocalWire *w, const u8 *b, int size)
{
    if (size != LOCAL_WIRE_BYTES || memcmp(b, "EUN2", 4) || lw_get(b+4) != w->cookie || lw_get(b+8) != w->build) return;
    u32 seq = lw_get(b+12); int type = b[16], kind = b[17], n = b[18] | b[19]<<8;
    if (kind < 1 || kind > 4 || n > LOCAL_WIRE_BODY || type < 1 || type > 3) return;
    if (type == 3) { // ACK, including a late ACK after the next phase was offered.
        if (n == 0 && w->offered && seq == w->sequence && kind == w->kind) w->acked = true;
        return;
    }
    if (type == 1) { // READY for this or the immediately following exchange.
        if (n || (seq != w->sequence && seq != w->sequence + 1)) return;
        w->ready_seen = true; w->ready_sequence = seq; w->ready_kind = kind;
        if (w->offered && seq == w->sequence) {
            if (kind != w->kind) { w->failed = true; return; }
            w->remote_ready = true;
        }
        return;
    }
    // ACK duplicate data even while the player is choosing the next action.
    if (seq + 1 == w->sequence) { w->ack_pending = true; w->ack_sequence = seq; w->ack_kind = kind; return; }
    if (!w->offered || seq != w->sequence) return;
    if (kind != w->kind) { w->failed = true; return; }
    w->remote_ready = true; // DATA also proves READY if that earlier frame was lost.
    if (!w->got) { memcpy(w->in, b+20, n); w->received = n; w->got = true; }
    w->ack_pending = true; w->ack_sequence = seq; w->ack_kind = kind;
}
bool local_wire_poll(LocalWire *w, u32 frame, u8 *b)
{
    if (w->failed) return false;
    if (!w->ack_pending && (!w->offered || frame - w->last_sent < 6)) return false;
    memset(b, 0, LOCAL_WIRE_BYTES); memcpy(b, "EUN2", 4); lw_put(b+4,w->cookie); lw_put(b+8,w->build);
    if (w->ack_pending) {
        lw_put(b+12,w->ack_sequence); b[16] = 3;
        // ACK kind is copied from the accepted data, not a later offered step.
        b[17] = w->ack_kind; w->ack_pending = false;
    } else {
        lw_put(b+12,w->sequence); b[16] = w->remote_ready ? 2 : 1; b[17] = w->kind;
        if (w->remote_ready) { b[18] = w->size; b[19] = w->size >> 8; memcpy(b+20,w->out,w->size); }
        w->last_sent = frame;
    }
    return true;
}
bool local_wire_take(LocalWire *w, void *data, int *size)
{
    if (!w->offered || !w->got || !w->acked || w->failed) return false;
    memcpy(data,w->in,w->received); *size = w->received;
    w->offered = false; w->sequence++; return true;
}
