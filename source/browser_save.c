// Browser-owned persistent slots. Hardware without a host keeps its SD/cart backend.
#include "browser_save.h"
#include <stddef.h>

typedef struct {
    u32 magic[4];
    u32 heartbeat, ready, size, version;
    u32 request, operation, slot, result, language, reserved;
    SaveData data[4];             // three committed slots plus a pending write
} BrowserSave;
static volatile BrowserSave browser __attribute__((aligned(32)));
_Static_assert(sizeof(SaveData) == 4600, "Update the browser save format when changing SaveData");
_Static_assert(offsetof(BrowserSave, data) == 56, "Browser save ABI");

static void tick(void) { browser.heartbeat++; }
void browser_save_init(void)
{
    memset((void *)&browser, 0, sizeof browser);
    browser.magic[0] = 0x49535545; browser.magic[1] = 0x41532d4d;
    browser.magic[2] = 0x562d4556; browser.magic[3] = 0x21313030;
    browser.size = sizeof(SaveData); browser.version = 2;
    frame_hook_add(tick);
}
bool browser_save_connected(void) { return browser.ready != 0; }
bool browser_save_read(int slot, SaveData *out)
{
    if (!browser.ready || slot < 0 || slot >= SAVE_SLOTS) return false;
    memcpy(out, (const void *)&browser.data[slot], sizeof *out);
    return true;
}
static bool request(int operation, int slot)
{
    browser.operation = operation; browser.slot = slot; browser.result = 0;
    browser.request++;
    u32 start = g_frame;
    while (!browser.result && g_frame - start < 600) frame_wait();
    return browser.result == 1;
}
bool browser_save_write(int slot, const SaveData *data)
{
    if (!browser.ready || slot < 0 || slot >= SAVE_SLOTS) return false;
    memcpy((void *)&browser.data[3], data, sizeof *data);
    return request(1, slot);
}
int browser_save_language(void) { return browser.language; }
void browser_save_set_language(const char *code)
{
    browser.language = (u8)code[0] | ((u8)code[1] << 8);
    request(2, 0);
}
