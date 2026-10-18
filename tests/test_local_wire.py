"""Exercise the native wireless reliability engine with loss, duplication and menu delays."""
from test_progression import ROOT, run_c
from test_multiplayer import without_includes
import unittest

class LocalWireTests(unittest.TestCase):
    def test_loss_duplicates_delayed_actions_and_wrong_sessions(self):
        source = r'''
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <assert.h>
typedef uint8_t u8; typedef uint32_t u32;
'''
        source += without_includes('include/local_wire.h') + without_includes('source/local_wire.c')
        source += r'''
typedef struct { bool live; int to; u32 due; u8 b[LOCAL_WIRE_BYTES]; } Flight;
static Flight flight[128]; static u32 random_state=3;
static u32 random_value(void) { random_state=random_state*1664525+1013904223; return random_state; }
int main(void) {
    LocalWire w[2]; local_wire_init(&w[0],123,456); local_wire_init(&w[1],123,456);
    int round[2]={0}, count[2]={0}, sent_data[2]={0}; u32 next[2]={0};
    for (u32 frame=0;frame<300000 && (round[0]<100 || round[1]<100);frame++) {
        for (int i=0;i<2;i++) {
            if (round[i]<100 && !w[i].offered && frame>=next[i]) {
                u8 payload[239]; memset(payload,round[i]+i, sizeof payload);
                assert(local_wire_offer(&w[i],1+round[i]%4,payload,1+(round[i]*17)%239));
            }
            u8 b[LOCAL_WIRE_BYTES];
            if (local_wire_poll(&w[i],frame,b)) {
                // No choice is revealed before the peer offered this sequence.
                if (b[16]==2) { assert(w[1-i].offered || w[1-i].sequence>w[i].sequence); sent_data[i]++; }
                if (random_value()%4) {
                    for (int copies=1+random_value()%2;copies;copies--) {
                        int at=0;while(at<128 && flight[at].live)at++;assert(at<128);
                        flight[at].live=true;flight[at].to=1-i;flight[at].due=frame+1+random_value()%11;
                        memcpy(flight[at].b,b,sizeof b);
                    }
                }
                // A packet from another nearby room must never change this session.
                LocalWire original=w[1-i]; b[4]^=1;local_wire_receive(&w[1-i],b,sizeof b);
                assert(!memcmp(&original,&w[1-i],sizeof original));
            }
            u8 data[239]; int size;
            if (local_wire_take(&w[i],data,&size)) {
                assert(size==1+(round[i]*17)%239);
                for(int k=0;k<size;k++)assert(data[k]==round[i]+1-i);
                round[i]++;count[i]++;next[i]=frame+(i?77:3); // peer pumps ACKs while choosing
            }
            assert(!w[i].failed);
        }
        for(int k=0;k<128;k++)if(flight[k].live && flight[k].due<=frame){
            local_wire_receive(&w[flight[k].to],flight[k].b,sizeof flight[k].b);flight[k].live=false;
        }
    }
    assert(count[0]==100 && count[1]==100);assert(sent_data[0]>100 && sent_data[1]>100);
    // Reject oversized or mismatched phases, preserving caller memory.
    LocalWire a,b;local_wire_init(&a,9,8);local_wire_init(&b,9,8);u8 packet[264],data[240]={0};
    assert(!local_wire_offer(&a,1,data,240));assert(local_wire_offer(&a,1,data,1));
    assert(local_wire_offer(&b,2,data,1));assert(local_wire_poll(&b,10,packet));
    local_wire_receive(&a,packet,sizeof packet);assert(a.failed);
}
'''
        run_c(source)

    def test_wifi_initialization_selects_dsi_online_and_legacy_local(self):
        from test_progression import function
        source = r'''
#include <stdbool.h>
#include <stdint.h>
#include <assert.h>
#include <string.h>
typedef uint32_t u32;
#define INIT_ONLY 0
#define WIFI_LOCAL_ONLY 4
#define WIFI_ATTEMPT_DSI_MODE 8
static bool wifi_initialized,wifi_local_only,wifi_dsi,dsi,init_ok=true;
static unsigned flags_seen,init_calls,internet_calls;
static u32 g_frame;
static const char *error;
bool isDSiMode(void){return dsi;}
bool Wifi_InitDefault(unsigned f){flags_seen=f;init_calls++;return init_ok;}
void Wifi_InternetMode(void){internet_calls++;}
bool Wifi_LibraryModeReady(void){return true;}
bool wait_step(u32 a,int b){g_frame++;return true;}
bool failed(const char *s){error=s;return false;}
'''
        source += function('source/multiplayer.c', 'static bool prepare_wifi(bool nearby)')
        source += r'''
int main(void){
 dsi=true;assert(prepare_wifi(false));assert(flags_seen==8);assert(wifi_dsi);assert(internet_calls==1);
 assert(!prepare_wifi(true));assert(strstr(error,"Redémarrez"));assert(init_calls==1);
 wifi_initialized=false;assert(prepare_wifi(true));assert(flags_seen==4);assert(!wifi_dsi);assert(wifi_local_only);
 assert(!prepare_wifi(false));assert(init_calls==2);
 wifi_initialized=false;dsi=false;assert(prepare_wifi(false));assert(flags_seen==8);assert(!wifi_dsi);
 assert(prepare_wifi(true));assert(init_calls==3); // Original DS can switch to local with the same driver.
 wifi_initialized=false;init_ok=false;assert(!prepare_wifi(false));assert(!wifi_initialized);
}
'''
        run_c(source)
