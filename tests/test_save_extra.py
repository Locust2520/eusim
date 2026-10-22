"""The optional SaveExtra block (specimen banknote) on the SD-card file and cartridge backends."""
import json
import tempfile
import unittest
from test_progression import run_c
from test_browser_save import code


class SaveExtraTests(unittest.TestCase):
    def run_backend(self, file_backend):
        with tempfile.TemporaryDirectory() as directory:
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
#define FILE_BACKEND ''' + ('1' if file_backend else '0') + r'''
u32 g_frame;
void frame_hook_add(void (*fn)(void)) { (void)fn; }
void frame_wait(void) { g_frame++; }
static u8 eeprom[65536];
#define fatInitDefault() FILE_BACKEND
#define sysSetCardOwner(...) ((void)0)
#define cardEepromGetType() (FILE_BACKEND ? 0 : 3)
#define cardEepromGetSize() (FILE_BACKEND ? 0 : (int)sizeof eeprom)
#define cardReadEeprom(ofs, dst, n, type) memcpy((dst), eeprom + (ofs), (n))
#define cardWriteEeprom(ofs, src, n, type) memcpy(eeprom + (ofs), (src), (n))
static struct { const char *code; } g_langs[]={{"fr"},{"en"}};
static int lang_index(const char *s) { return !strcmp(s,"fr")?0:!strcmp(s,"en")?1:-1; }
bool browser_save_connected(void) { return false; }
bool browser_save_read(int slot, void *out) { return false; }
bool browser_save_read_extra(int slot, void *out) { return false; }
bool browser_save_write(int slot, const void *data, const void *extra) { return false; }
int browser_save_language(void) { return 0; }
void browser_save_set_language(const char *code) {}
''' + code('include/save.h') + code('source/save.c') + r'''
static long file_size(const char *p) { FILE *f = fopen(p, "rb"); if (!f) return -1; fseek(f, 0, SEEK_END); long n = ftell(f); fclose(f); return n; }
int main(void) {
    g_rom_path = ''' + json.dumps(directory + '/eusim.nds') + r''';
    char slot1[512]; snprintf(slot1, sizeof slot1, "%s", ''' + json.dumps(directory + '/eusim_slot1.sav') + r''');
    assert(save_available());
    // a save without a note keeps the original 4600-byte format
    g_save_slot = 0; save_new_game(); g_save.money = 77; assert(save_write());
    if (FILE_BACKEND) assert(file_size(slot1) == (long)sizeof(SaveData));
    assert(save_load(0) && g_save.money == 77 && g_save_extra.magic == 0);
    // with a note: appended after SaveData, read back intact
    g_save_extra.magic = SAVE_EXTRA_MAGIC; g_save_extra.note_denom = 5; g_save_extra.note_theme = 1;
    for (int i = 0; i < (int)sizeof g_save_extra.note_px; i++) g_save_extra.note_px[i] = (u8)(i * 7);
    assert(save_write());
    if (FILE_BACKEND) assert(file_size(slot1) == (long)(sizeof(SaveData) + sizeof(SaveExtra)));
    SaveExtra kept = g_save_extra;
    memset(&g_save_extra, 0, sizeof g_save_extra);
    assert(save_load(0) && save_extra_present(&g_save_extra) && !memcmp(&kept, &g_save_extra, sizeof kept));
    // an older game version reads only the SaveData part of the slot
    SaveData old; FILE *f;
    if (FILE_BACKEND) { f = fopen(slot1, "rb"); assert(fread(&old, 1, sizeof old, f) == sizeof old); fclose(f); }
    else memcpy(&old, eeprom, sizeof old);
    assert(old.money == 77 && old.magic == SAVE_MAGIC);
    // a new game saved over the slot removes the old note
    save_new_game(); g_save.money = 5; assert(save_write());
    assert(save_load(0) && g_save.money == 5 && g_save_extra.magic == 0);
    if (FILE_BACKEND) assert(file_size(slot1) == (long)sizeof(SaveData));
    // damaged note: ignored, the save itself still loads
    g_save_extra = kept; assert(save_write());
    if (FILE_BACKEND) { f = fopen(slot1, "r+b"); fseek(f, sizeof(SaveData) + 40, SEEK_SET); fputc(0x55, f); fclose(f); }
    else eeprom[4608 + 40] ^= 0x55;
    assert(save_load(0) && g_save.money == 5 && g_save_extra.magic == 0);
    return 0;
}
''')

    def test_sd_card_file(self):
        self.run_backend(True)

    def test_cartridge_slot(self):
        self.run_backend(False)


if __name__ == '__main__':
    unittest.main()
