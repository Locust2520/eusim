// Native two-console wireless. No AP, IP address, Internet or relay is involved.
#include "local_link.h"
#include "local_wire.h"
#include "input.h"
#include "ui.h"
#include "gfx.h"
#include "lang.h"
#include "save.h"
#include "gen/font_data.h"
#include "gen/link_build.h"
#include <dswifi9.h>

#define LOCAL_GAME 0x45555332u
#define RX_COUNT 8
static volatile u8 rx[RX_COUNT][LOCAL_WIRE_BYTES];
static volatile unsigned rx_read, rx_write;
static volatile bool enabled;
static bool host_side, connected, lobby_wait;
static volatile int peer_aid;
static LocalWire wire;
static const char *error;
static void (*draw_waiting)(void);

static void put(u8 *b, u32 v) { for (int i=0;i<4;i++) b[i]=v>>(i*8); }
static u32 get(const u8 *b) { return (u32)b[0]|(u32)b[1]<<8|(u32)b[2]<<16|(u32)b[3]<<24; }
// Called from an IRQ: copy only, no sockets, TLS, allocation or UI.
static void receive(int address, int size)
{
    unsigned next = (rx_write + 1) % RX_COUNT;
    if (!enabled || size != LOCAL_WIRE_BYTES || next == rx_read) return;
    u8 copy[LOCAL_WIRE_BYTES]; Wifi_RxRawReadPacket(address, size, copy);
    for (int i=0;i<size;i++) rx[rx_write][i]=copy[i];
    rx_write = next;
}
static void from_host(Wifi_MPPacketType type, int address, int size)
{
    if (type == WIFI_MPTYPE_DATA) receive(address,size);
}
static void from_client(Wifi_MPPacketType type, int aid, int address, int size)
{
    if (type == WIFI_MPTYPE_DATA && aid == peer_aid) receive(address,size);
}
static void pump(void)
{
    if (!enabled || !connected) return;
    u8 b[LOCAL_WIRE_BYTES];
    while (rx_read != rx_write) {
        for (int i=0;i<LOCAL_WIRE_BYTES;i++) b[i]=rx[rx_read][i];
        rx_read = (rx_read + 1) % RX_COUNT;
        local_wire_receive(&wire,b,sizeof b);
    }
    if (local_wire_poll(&wire,g_frame,b)) {
        if (host_side) Wifi_MultiplayerHostToClientDataTxFrame(peer_aid,b,sizeof b);
        else Wifi_MultiplayerClientToHostDataTxFrame(b,sizeof b);
    }
}
static bool fail(const char *message) { error=message; return false; }
static bool step(u32 start, int seconds)
{
    frame_wait();
    if ((g_kdown & KEY_B) || (lobby_wait && touch_in(50,146,156,34))) return fail("Debate cancelled.");
    if (g_frame-start>(u32)seconds*60) return fail("The console is not responding.");
    return true;
}
bool local_link_ok(void)
{
    if (!enabled || !connected || wire.failed) return false;
    if (host_side) return !!(Wifi_MultiplayerGetClientMask() & (1 << peer_aid));
    return Wifi_AssocStatus()==ASSOCSTATUS_ASSOCIATED;
}
const char *local_link_error(void) { return error ? error : "The other player left the debate."; }
int local_link_seat(void) { return host_side ? 0 : 1; }
u32 local_link_seed(void) { return wire.cookie; }
void local_link_close(void)
{
    enabled=connected=false; frame_hook_remove(pump);
    Wifi_MultiplayerFromHostSetPacketHandler(NULL);
    Wifi_MultiplayerFromClientSetPacketHandler(NULL);
    Wifi_IdleMode(); peer_aid=0; rx_read=rx_write=0;
}
bool local_link_open(bool host, void (*draw_wait)(void))
{
    lobby_wait=true; host_side=host; enabled=true; connected=false; error=NULL; draw_waiting=draw_wait;
    peer_aid=0; rx_read=rx_write=0;
    Wifi_MultiplayerFromHostSetPacketHandler(from_host);
    Wifi_MultiplayerFromClientSetPacketHandler(from_client);
    int result = host ? Wifi_MultiplayerHostMode(1,0,0) : Wifi_MultiplayerClientMode(0);
    if (result<0) return fail("Could not create the connection.");
    u32 start=g_frame;
    while (!Wifi_LibraryModeReady()) { draw_waiting(); if (!step(start,10)) return false; }
    if (host) {
        u8 metadata[DSWIFI_BEACON_NAME_SIZE]={0}; u32 cookie=rng_next(); if (!cookie) cookie=1;
        put(metadata,LINK_BUILD); put(metadata+4,cookie);
        local_wire_init(&wire,cookie,LINK_BUILD);
        Wifi_MultiplayerHostName(metadata,8);
        static const int channels[]={1,6,11}; Wifi_SetChannel(channels[rng_range(3)]);
        Wifi_MultiplayerAllowNewClients(true);
        char name[33]; snprintf(name,sizeof name,"EU Simulator %.12s",g_save.player_name);
        if (Wifi_BeaconStart(name,LOCAL_GAME)<0) return fail("Could not create the connection.");
        start=g_frame;
        while (!peer_aid) {
            draw_waiting(); if (!step(start,300)) return false;
            u16 mask=Wifi_MultiplayerGetClientMask();
            for (int i=1;i<=15;i++) if (mask & (1<<i)) { peer_aid=i; break; }
        }
        Wifi_MultiplayerAllowNewClients(false);
    } else {
        Wifi_ScanMode(); int selection=0; start=g_frame;
        while (!connected) {
            Wifi_AccessPoint hosts[16]; int count=0;
            for (int i=0;i<Wifi_GetNumAP() && count<16;i++) {
                Wifi_AccessPoint ap; Wifi_GetAPData(i,&ap);
                if ((ap.flags & WFLAG_APDATA_NINTENDO_TAG) && ap.nintendo.game_id==LOCAL_GAME &&
                    ap.nintendo.allows_connections && ap.nintendo.players_current<2) hosts[count++]=ap;
            }
            if (selection>=count) selection=MAX(0,count-1);
            draw_waiting();
            if (count) {
                ui_backdrop(&g_bot); ui_header(&g_bot,4,4,248,"Nearby games");
                int first=MAX(0,selection-4);
                for (int i=first;i<count && i<first+5;i++)
                    ui_button(&g_bot,8,34+(i-first)*21,240,20,hosts[i].ssid,i==selection?BTN_SELECTED:BTN_NORMAL,&font_small);
                ui_button(&g_bot,50,146,156,34,"Cancel (B)",BTN_DARK,&font_main);
            }
            if (!step(start,300)) return false;
            if (count && (g_krep & KEY_UP)) selection=(selection+count-1)%count;
            if (count && (g_krep & KEY_DOWN)) selection=(selection+1)%count;
            int pick = count && (g_kdown & KEY_A) ? selection : -1;
            int first=MAX(0,selection-4);
            for (int i=first;i<count && i<first+5;i++) if (touch_in(8,34+(i-first)*21,240,20)) pick=i;
            if (pick<0) continue;
            const u8 *meta=(const u8 *)hosts[pick].nintendo.name;
            if (hosts[pick].nintendo.name_len!=8 || get(meta)!=LINK_BUILD)
                return fail("The game versions differ.");
            local_wire_init(&wire,get(meta+4),LINK_BUILD);
            if (Wifi_ConnectOpenAP(&hosts[pick])!=WIFI_RETURN_OK) return fail("Could not create the connection.");
            u32 connecting=g_frame;
            while (Wifi_AssocStatus()!=ASSOCSTATUS_ASSOCIATED) {
                if (Wifi_AssocStatus()==ASSOCSTATUS_CANNOTCONNECT) return fail("The other player left the debate.");
                draw_waiting(); if (!step(connecting,30)) return false;
            }
            connected=true;
        }
    }
    connected=true; lobby_wait=false; frame_hook_add(pump); return true;
}
bool local_link_exchange(int kind, const void *out, int size, void *in, int *received)
{
    if (!local_wire_offer(&wire,kind,out,size)) return fail("The debates are out of sync.");
    u32 start=g_frame;
    while (!local_wire_take(&wire,in,received)) {
        if (!local_link_ok()) return fail(wire.failed ? "The debates are out of sync." : "The other player left the debate.");
        if (!step(start,300)) return false;
    }
    return true;
}
