/* Screenshot-only entry point; no code or mailbox is included in release ROMs.
 * The host restores a snapshot at the mailbox, then selects a language and scene.
 * All pixels are drawn by the game's own renderer and translation tables.
 */
#ifdef WEBSITE_CAPTURE
#include "common.h"
#include "lang.h"
#include "save.h"
#include "world.h"
#include "actor.h"
#include "map.h"
#include "gfx.h"
#include "mon.h"
#include "cine.h"
#include "dialog.h"
#include "portrait.h"
#include "battle.h"
#include "minigame.h"
#include "gen/maps.h"
#include "gen/flags.h"

volatile u32 g_site_capture[8] __attribute__((aligned(32))) = {0x50414353, 0, 0, 0, 0, 0, 0, 0};

void site_capture_main(void)
{
    while (!g_site_capture[3]) {
        DC_InvalidateRange((void *)g_site_capture, sizeof g_site_capture);
        frame_wait();
    }
    int language = g_site_capture[1], scene = g_site_capture[2];
    if (language < 0 || language >= LANG_COUNT) language = 5;
    lang_set(language);
    save_new_game();
    world_new_game();
    flag_set(FLAG_INTRO_DONE, 1);
    flag_set(FLAG_GOT_STARTER, 1);
    flag_set(FLAG_GOT_DEX, 1);
    Mon m;
    mon_create(&m, SP_CECAGON, 75); party_add(&m);
    mon_create(&m, SP_DRAGHIZORD, 75); party_add(&m);
    g_save.badges = 0x0F;
    g_save.opt_text_speed = 2;
    gfx_brightness(false, 0); gfx_brightness(true, 0);
#include "../build/site_capture_scenes.h"
    while (1) frame_wait();
}
#endif
