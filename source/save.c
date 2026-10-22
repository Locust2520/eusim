// Saves: three slots. Primary backend = files on the SD card of the flashcard (DLDI / DSi SD), written next to
// the ROM (e.g. "fat:/games/eusim.nds" -> "fat:/games/eusim_slot1.sav"); atomic write via a temp file.
// Fallback = cartridge EEPROM/flash (8 KB per slot) when the emulator/cart provides one.
// The optional SaveExtra block follows SaveData in each slot (appended to the file, at EXTRA_OFS in a cartridge slot).
#include "save.h"
#include "browser_save.h"
#include "lang.h"
#include <fat.h>
#include <sys/stat.h>

SaveData g_save;
SaveExtra g_save_extra;
int g_save_slot;
const char *g_rom_path;

#define SAVE_MAGIC 0x55534555u  // "UESU"
#define SAVE_VERSION 2
#define EEPROM_SLOT_SIZE 8192
#define EXTRA_OFS 4608   // SaveExtra offset inside a cartridge slot (SaveData rounded up)
_Static_assert(sizeof(SaveData) <= EXTRA_OFS && EXTRA_OFS + sizeof(SaveExtra) <= EEPROM_SLOT_SIZE, "cartridge slot layout");
_Static_assert(sizeof(SaveExtra) == SAVE_EXTRA_SIZE, "SaveExtra size");

typedef enum { BK_UNKNOWN, BK_FILE, BK_EEPROM, BK_NONE, BK_BROWSER } Backend;
static Backend backend = BK_UNKNOWN;
static char base_path[128];       // directory + stem, e.g. "fat:/games/eusim"
static int eeprom_type;

static u16 checksum_bytes(const void *data, u32 size)
{
    const u8 *p = data;
    u32 sum = 0;
    for (u32 i = 8; i < size; i++)
        sum = (sum * 31 + p[i]) & 0xFFFF;
    return (u16)sum;
}

static u16 checksum(const SaveData *s) { return checksum_bytes(s, sizeof *s); }

bool save_extra_present(const SaveExtra *e)
{
    return e->magic == SAVE_EXTRA_MAGIC && e->version == SAVE_EXTRA_VERSION &&
           e->checksum == checksum_bytes(e, sizeof *e);
}

static bool can_write(const char *path)
{
    char tmp[160];
    snprintf(tmp, sizeof tmp, "%s.probe", path);
    FILE *f = fopen(tmp, "wb");
    if (!f)
        return false;
    bool ok = fwrite("ok", 1, 2, f) == 2;
    fclose(f);
    remove(tmp);
    return ok;
}

static void detect(void)
{
    if (browser_save_connected()) { backend = BK_BROWSER; return; }
    if (backend != BK_UNKNOWN) return;
    // Give the webpage time to discover the live mailbox and hydrate its slots.
    // Other emulators/hardware simply continue with the normal physical backends.
    for (int i = 0; i < 75 && !browser_save_connected(); i++) frame_wait();
    if (browser_save_connected()) { backend = BK_BROWSER; return; }
    static bool fat_ok;
    fat_ok = fatInitDefault();
    if (fat_ok) {
        // 1) next to the ROM
        if (g_rom_path && g_rom_path[0] && strchr(g_rom_path, '/')) {
            strncpy(base_path, g_rom_path, sizeof base_path - 1);
            char *dot = strrchr(base_path, '.');
            char *slash = strrchr(base_path, '/');
            if (dot && dot > slash)
                *dot = 0;
            if (can_write(base_path)) {
                backend = BK_FILE;
                return;
            }
        }
        // 2) well-known roots
        static const char *const roots[] = {"sd:/eusim", "fat:/eusim", "/eusim"};
        for (unsigned i = 0; i < ARRAY_LEN(roots); i++) {
            if (can_write(roots[i])) {
                strcpy(base_path, roots[i]);
                backend = BK_FILE;
                return;
            }
        }
    }
    sysSetCardOwner(BUS_OWNER_ARM9);
    eeprom_type = cardEepromGetType();
    if (eeprom_type > 0 && cardEepromGetSize() >= EEPROM_SLOT_SIZE * SAVE_SLOTS) {
        backend = BK_EEPROM;
        return;
    }
    backend = BK_NONE;
}

const char *save_backend(void)
{
    detect();
    switch (backend) {
    case BK_BROWSER: return "browser";
    case BK_FILE: return "SD card";
    case BK_EEPROM: return "cartridge";
    default: return "none";
    }
}

bool save_available(void)
{
    detect();
    return backend == BK_BROWSER || backend == BK_FILE || backend == BK_EEPROM;
}

static void slot_path(int slot, char *out, int n)
{
    snprintf(out, n, "%s_slot%d.sav", base_path, slot + 1);
}

static bool read_raw(int slot, SaveData *s)
{
    if (slot < 0 || slot >= SAVE_SLOTS) return false;
    detect();
    if (backend == BK_BROWSER) return browser_save_read(slot, s);
    if (backend == BK_FILE) {
        char p[160];
        slot_path(slot, p, sizeof p);
        FILE *f = fopen(p, "rb");
        if (!f)
            return false;
        size_t n = fread(s, 1, sizeof(*s), f);
        fclose(f);
        return n == sizeof(*s);
    }
    if (backend == BK_EEPROM) {
        sysSetCardOwner(BUS_OWNER_ARM9);
        cardReadEeprom(slot * EEPROM_SLOT_SIZE, (u8 *)s, sizeof(*s), eeprom_type);
        return true;
    }
    return false;
}

static void read_extra(int slot, SaveExtra *e)
{
    bool ok = false;
    if (backend == BK_BROWSER)
        ok = browser_save_read_extra(slot, e);
    else if (backend == BK_FILE) {
        char p[160];
        slot_path(slot, p, sizeof p);
        FILE *f = fopen(p, "rb");
        if (f) {
            ok = fseek(f, sizeof(SaveData), SEEK_SET) == 0 && fread(e, 1, sizeof *e, f) == sizeof *e;
            fclose(f);
        }
    } else if (backend == BK_EEPROM) {
        sysSetCardOwner(BUS_OWNER_ARM9);
        cardReadEeprom(slot * EEPROM_SLOT_SIZE + EXTRA_OFS, (u8 *)e, sizeof *e, eeprom_type);
        ok = true;
    }
    if (!ok || !save_extra_present(e))
        memset(e, 0, sizeof *e);
}

static bool valid(const SaveData *s)
{
    return s->magic == SAVE_MAGIC && s->version == SAVE_VERSION && s->checksum == checksum(s);
}

bool save_slot_info(int slot, SlotInfo *out)
{
    static SaveData tmp;
    memset(out, 0, sizeof(*out));
    if (!read_raw(slot, &tmp) || !valid(&tmp))
        return false;
    out->used = true;
    memcpy(out->name, tmp.player_name, sizeof out->name);
    out->name[sizeof out->name - 1] = 0;
    out->badges = tmp.badges;
    out->gender = tmp.player_gender;
    out->play_frames = tmp.play_frames;
    out->map = tmp.map;
    int n = 0;
    for (int i = 0; i < 128; i++)
        n += (tmp.dex_caught[i >> 3] >> (i & 7)) & 1;
    out->dex = n;
    return true;
}

bool save_exists(void)
{
    SlotInfo si;
    for (int s = 0; s < SAVE_SLOTS; s++)
        if (save_slot_info(s, &si))
            return true;
    return false;
}

bool save_load(int slot)
{
    static SaveData tmp;
    if (!read_raw(slot, &tmp) || !valid(&tmp))
        return false;
    g_save = tmp;
    g_save_slot = slot;
    read_extra(slot, &g_save_extra);
    return true;
}

bool save_write(void)
{
    if (g_save_slot < 0 || g_save_slot >= SAVE_SLOTS) return false;
    detect();
    g_save.magic = SAVE_MAGIC;
    g_save.version = SAVE_VERSION;
    g_save.checksum = checksum(&g_save);
    bool extra = g_save_extra.magic == SAVE_EXTRA_MAGIC;
    if (extra) {
        g_save_extra.version = SAVE_EXTRA_VERSION;
        g_save_extra.checksum = checksum_bytes(&g_save_extra, sizeof g_save_extra);
    }
    if (backend == BK_BROWSER) return browser_save_write(g_save_slot, &g_save, extra ? &g_save_extra : NULL);
    if (backend == BK_FILE) {
        char p[160], tmpn[170];
        slot_path(g_save_slot, p, sizeof p);
        snprintf(tmpn, sizeof tmpn, "%s.tmp", p);
        FILE *f = fopen(tmpn, "wb");
        if (!f)
            return false;
        bool ok = fwrite(&g_save, 1, sizeof(g_save), f) == sizeof(g_save) &&
                  (!extra || fwrite(&g_save_extra, 1, sizeof(g_save_extra), f) == sizeof(g_save_extra));
        fflush(f);
        fclose(f);
        if (!ok)
            return false;
        remove(p);
        if (rename(tmpn, p) != 0) {
            // some FAT drivers dislike rename: write directly
            f = fopen(p, "wb");
            if (!f)
                return false;
            ok = fwrite(&g_save, 1, sizeof(g_save), f) == sizeof(g_save) &&
                 (!extra || fwrite(&g_save_extra, 1, sizeof(g_save_extra), f) == sizeof(g_save_extra));
            fclose(f);
            remove(tmpn);
            if (!ok)
                return false;
        }
        // verify
        static SaveData verify;
        static SaveExtra verify_extra;
        if (!read_raw(g_save_slot, &verify) || memcmp(&verify, &g_save, sizeof(g_save)) != 0)
            return false;
        if (!extra)
            return true;
        read_extra(g_save_slot, &verify_extra);
        return memcmp(&verify_extra, &g_save_extra, sizeof(g_save_extra)) == 0;
    }
    if (backend == BK_EEPROM) {
        sysSetCardOwner(BUS_OWNER_ARM9);
        cardWriteEeprom(g_save_slot * EEPROM_SLOT_SIZE, (u8 *)&g_save, sizeof(g_save), eeprom_type);
        static const u32 no_extra = 0;   // erases a note left by an earlier game in this slot
        cardWriteEeprom(g_save_slot * EEPROM_SLOT_SIZE + EXTRA_OFS, extra ? (u8 *)&g_save_extra : (u8 *)&no_extra,
                        extra ? sizeof(g_save_extra) : sizeof no_extra, eeprom_type);
        static SaveData verify;
        cardReadEeprom(g_save_slot * EEPROM_SLOT_SIZE, (u8 *)&verify, sizeof(verify), eeprom_type);
        if (memcmp(&verify, &g_save, sizeof(g_save)) != 0)
            return false;
        static SaveExtra verify_extra;
        if (!extra)
            return true;
        read_extra(g_save_slot, &verify_extra);
        return memcmp(&verify_extra, &g_save_extra, sizeof(g_save_extra)) == 0;
    }
    return false;
}

void save_new_game(void)
{
    int slot = g_save_slot;
    memset(&g_save, 0, sizeof(g_save));
    memset(&g_save_extra, 0, sizeof(g_save_extra));
    g_save_slot = slot;
    strcpy(g_save.player_name, "Alex");
    g_save.money = 500;
    g_save.opt_text_speed = 1;
    g_save.opt_music = 4;
    g_save.opt_battle_anim = 1;
}

// ---------------------------------------------------------------- language preference (shared by all slots)
#define LANG_EEPROM_OFS (EEPROM_SLOT_SIZE * SAVE_SLOTS)

int save_lang_load(void)
{
    detect();
    char code[4] = {0};
    if (backend == BK_BROWSER) {
        int language = browser_save_language();
        code[0] = language; code[1] = language >> 8;
        return code[0] && code[1] ? lang_index(code) : -1;
    }
    if (backend == BK_FILE) {
        char p[160];
        snprintf(p, sizeof p, "%s_lang.txt", base_path);
        FILE *f = fopen(p, "rb");
        if (!f)
            return -1;
        size_t n = fread(code, 1, 2, f);
        fclose(f);
        if (n != 2)
            return -1;
    } else if (backend == BK_EEPROM && cardEepromGetSize() >= LANG_EEPROM_OFS + 4) {
        u8 b[4];
        sysSetCardOwner(BUS_OWNER_ARM9);
        cardReadEeprom(LANG_EEPROM_OFS, b, 4, eeprom_type);
        if (b[0] != 'L' || b[1] != 'G')
            return -1;
        code[0] = b[2];
        code[1] = b[3];
    } else
        return -1;
    return lang_index(code);
}

void save_lang_store(int index)
{
    detect();
    const char *code = g_langs[index].code;
    if (backend == BK_BROWSER) { browser_save_set_language(code); return; }
    if (backend == BK_FILE) {
        char p[160];
        snprintf(p, sizeof p, "%s_lang.txt", base_path);
        FILE *f = fopen(p, "wb");
        if (f) {
            fwrite(code, 1, 2, f);
            fclose(f);
        }
    } else if (backend == BK_EEPROM && cardEepromGetSize() >= LANG_EEPROM_OFS + 4) {
        u8 b[4] = {'L', 'G', (u8)code[0], (u8)code[1]};
        sysSetCardOwner(BUS_OWNER_ARM9);
        cardWriteEeprom(LANG_EEPROM_OFS, b, 4, eeprom_type);
    }
}
