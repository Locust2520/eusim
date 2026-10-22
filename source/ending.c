// Ending: scrolling staff roll over a starry sky with the Euromons of the player's team.
#include "scenes.h"
#include "note.h"
#include "lang.h"
#include "canvas.h"
#include "gfx.h"
#include "fs.h"
#include "input.h"
#include "audio.h"
#include "save.h"
#include "creature_gfx.h"
#include "data.h"
#include "gen/font_data.h"

void ending_run(void)
{
    u32 size;
    char *txt = lang_load_text("text/credits.txt", &size);
    if (!txt)
        return;
    txt = realloc(txt, size + 1);
    txt[size] = 0;
    music_play("ending");
    gfx_fade_out(30, true);
    gfx_clear_scene(false);
    gfx_clear_scene(true);
    canvas_clear(&g_top, 0);
    canvas_clear(&g_bot, 0);
    BG_PALETTE[0] = RGB8(8, 12, 40);
    BG_PALETTE_SUB[0] = RGB8(8, 12, 40);
    for (int i = 50; i < 128; i++)
        oamClearSprite(&oamMain, i);
    gfx_fade_in(30, true);
    // lines
    const char *lines[400];
    int n = 0;
    char *s = txt;
    while (*s && n < 400) {
        lines[n++] = s;
        char *e = strchr(s, '\n');
        if (!e)
            break;
        *e = 0;
        s = e + 1;
    }
    int total_h = n * 14 + 192;
    for (int off = -192; off < total_h; off++) {
        canvas_clear(&g_bot, 0);
        for (int i = 0; i < n; i++) {
            int y = i * 14 - off;
            if (y < -14 || y > 192)
                continue;
            const char *l = lines[i];
            if (l[0] == '#')
                canvas_text_center(&g_bot, &font_main, 128, y, l + 2, C_GOLD, 0);
            else {
                // shrink overly long lines by cutting at a word boundary
                char tmp[80];
                strncpy(tmp, l, sizeof tmp - 1);
                tmp[sizeof tmp - 1] = 0;
                while (font_width(&font_small, tmp) > 248) {
                    char *sp = strrchr(tmp, ' ');
                    if (!sp)
                        break;
                    strcpy(sp, "…");
                    if (font_width(&font_small, tmp) <= 248)
                        break;
                    *sp = 0;
                }
                canvas_text_center(&g_bot, &font_small, 128, y + 2, tmp, C_WHITE, 0);
            }
        }
        // top: team parade + stars
        if (off % 4 == 0) {
            canvas_clear(&g_top, 0);
            for (int k = 0; k < 30; k++)
                canvas_pixel(&g_top, (k * 97 + off / 3) % 256, (k * 53) % 192, C_LGREY);
            canvas_text_center(&g_top, &font_main, 128, 20, "EU SIMULATOR", C_GOLD, C_BLUE_D);
            canvas_text_center(&g_top, &font_small, 128, 40, "Thanks for playing!", C_WHITE, 0);
            int i = (off / 120) % MAX(1, g_save.party_count);
            if (g_save.party_count) {
                creature_big_draw(&g_top, g_save.party[i].species, 96, 70);
                canvas_text_center(&g_top, &font_main, 128, 140, species[g_save.party[i].species].name, C_WHITE, C_BLUE_D);
            }
        }
        frame_wait();
        if (g_kheld & KEY_START)
            off += 3;
    }
    free(txt);
    note_ending();   // the specimen banknote from the ECB studio
    canvas_text_center(&g_bot, &font_main, 128, 90, "THE END… or almost.", C_GOLD, 0);
    for (int i = 0; i < 180 && !(g_kdown & (KEY_A | KEY_START)); i++)
        frame_wait();
    gfx_fade_out(30, false);
    canvas_clear(&g_top, 0);
    canvas_clear(&g_bot, 0);
}
