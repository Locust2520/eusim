// Top-level game flow: title -> intro / continue -> overworld.
#include "game.h"
#include "scenes.h"
#include "lang.h"
#include "gfx.h"
#include "canvas.h"
#include "audio.h"
#include "dialog.h"
#include "save.h"
#include "input.h"
#include "world.h"
#include "mon.h"
#ifdef QUICKSTART
#include "quickstart.h"
#endif

void game_main(void)
{
#ifdef WEBSITE_CAPTURE
    extern void site_capture_main(void);
    site_capture_main();
#endif
#ifdef QUICKSTART
#ifdef QLANG
    lang_set(lang_index(QLANG));
#else
    lang_set(lang_index("fr"));
#endif
    save_new_game();
    world_new_game();
    QUICKSTART_SETUP();
    gfx_brightness(false, 0);
    gfx_brightness(true, 0);
#if SCEN == 7
    { extern void script_run(int); script_run(131); }   // cine_prologue
#endif
#if SCEN == 9
    world_map_tour();
#endif
#if SCEN == 8
    { extern int minigame_run(int); int ids[5] = {0, 1, 2, 3, 8}; for (int i = 0; i < 5; i++) minigame_run(ids[i]); }
#endif
#if SCEN == 30 && defined(QSCRIPT)
    { extern void script_run(int); script_run(QSCRIPT); }   // cinematic, then the map
#endif
#if SCEN == 21
    { extern int minigame_run(int); minigame_run(12); minigame_run(11); }
#endif
#if SCEN == 20
    { extern int minigame_run(int); int ids[5] = {9, 10, 5, 11, 12}; for (int i = 0; i < 5; i++) minigame_run(ids[i]); }
#endif
    world_run();
#endif
    {
        // first boot: ask for the language (remembered next to the saves)
        int li = save_lang_load();
        if (li < 0) {
            li = lang_picker(-1);
            save_lang_store(li);
        }
        lang_set(li);
    }
    while (1) {
        int c = scene_title();
        if (c == 2) {
            gfx_brightness(false, 0);
            gfx_brightness(true, 0);
            scene_options(false);
            continue;
        }
        if (c == 3) {
            gfx_brightness(false, 0);
            gfx_brightness(true, 0);
            scene_credits();
            continue;
        }
        gfx_brightness(false, 0);
        gfx_brightness(true, 0);
        if (c == 0) {
            int slot = save_available() ? slot_picker(1) : 0;
            if (slot < 0)
                continue;
            g_save_slot = slot;
            save_new_game();
            gfx_brightness(false, -16);
            gfx_brightness(true, -16);
            scene_intro();
            world_new_game();
        } else {
            int slot = slot_picker(0);
            if (slot < 0)
                continue;
            if (!save_load(slot)) {
                dlg_notice("Sauvegarde illisible !");
                continue;
            }
        }
        music_set_volume(g_save.opt_music * 110 / 4);
        loading_screen(60);
        world_run();
    }
}
