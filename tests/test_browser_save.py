"""Production save slots use the browser backend only when a host has connected."""
import re
import unittest
from test_progression import ROOT, run_c


def code(path):
    return re.sub(r'^#(?:include|pragma).*$', '', (ROOT / path).read_text(), flags=re.M)


class BrowserSaveTests(unittest.TestCase):
    def test_committed_slots_failure_timeout_language_and_native_fallback(self):
        run_c(r'''
#include <assert.h>
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef uint8_t u8; typedef int8_t s8; typedef uint16_t u16; typedef int16_t s16;
typedef uint32_t u32; typedef int32_t s32;
#define ARRAY_LEN(a) (sizeof(a)/sizeof((a)[0]))
u32 g_frame;
static void (*hook)(void);
void frame_hook_add(void (*fn)(void)) { hook=fn; }
void frame_wait(void);
#define fatInitDefault() false
#define sysSetCardOwner(...) ((void)0)
#define cardEepromGetType() 0
#define cardEepromGetSize() 0
#define cardReadEeprom(...) ((void)0)
#define cardWriteEeprom(...) ((void)0)
static struct { const char *code; } g_langs[]={{"fr"},{"en"}};
static int lang_index(const char *s) { return !strcmp(s,"fr")?0:!strcmp(s,"en")?1:-1; }
''' + code('include/save.h') + code('include/browser_save.h') + code('source/browser_save.c') + code('source/save.c') + r'''
static int outcome=1;
static unsigned seen;
void frame_wait(void) {
    g_frame++; if(hook) hook();
    if(browser.ready && browser.request!=seen && outcome) {
        seen=browser.request;
        if(outcome==1 && browser.operation==1) memcpy((void*)&browser.data[browser.slot],(void*)&browser.data[3],sizeof(SaveData));
        browser.result=outcome;
    }
}
int main(void) {
    browser_save_init();
    assert(sizeof(SaveData)==4600);
    assert(!save_available() && backend==BK_NONE && g_frame==75);
    assert(!strcmp(save_backend(),"aucune"));
    browser.ready=1;
    assert(save_available() && !strcmp(save_backend(),"navigateur"));
    SlotInfo info;
    for(int i=0;i<3;i++) assert(!save_slot_info(i,&info));
    SaveData originals[3];
    for(int i=0;i<3;i++) {
        g_save_slot=i; save_new_game(); g_save.money=1000+i; g_save.party_count=1;
        snprintf(g_save.player_name,sizeof g_save.player_name,"Player%d",i);
        assert(save_write()); originals[i]=g_save;
        assert(save_slot_info(i,&info) && info.used && !strcmp(info.name,g_save.player_name));
    }
    for(int i=0;i<3;i++) { assert(save_load(i)); assert(!memcmp(&g_save,&originals[i],sizeof g_save)); }
    outcome=2; g_save.money=9999; assert(!save_write()); assert(save_load(2)); assert(g_save.money==1002);
    outcome=0; g_save.money=8888; unsigned start=g_frame; assert(!save_write()); assert(g_frame-start==600);
    assert(save_load(2) && g_save.money==1002);
    outcome=1; save_lang_store(1); assert(save_lang_load()==1);
    assert(!save_load(-1) && !save_load(3));
    unsigned before=browser.request; g_save_slot=3; assert(!save_write() && browser.request==before);
    browser.data[0].money++; assert(!save_load(0)); // checksum detects corruption
}
''')
