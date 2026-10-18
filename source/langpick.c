// Language selection: shown on the very first boot (and from the Options). 24 official EU languages.
#include "scenes.h"
#include "canvas.h"
#include "gfx.h"
#include "ui.h"
#include "input.h"
#include "audio.h"
#include "lang.h"
#include "image.h"
#include "gen/font_data.h"

static const char *const choose[LANG_COUNT] = {
    "Изберете език", "Vyberte jazyk", "Vælg sprog", "Wähle deine Sprache", "Επίλεξε γλώσσα",
    "Choose your language", "Elige tu idioma", "Vali keel", "Valitse kieli", "Choisis ta langue",
    "Roghnaigh do theanga", "Odaberi jezik", "Válassz nyelvet", "Scegli la lingua", "Pasirink kalbą",
    "Izvēlies valodu", "Agħżel il-lingwa", "Kies je taal", "Wybierz język", "Escolhe o teu idioma",
    "Alege limba", "Vyber si jazyk", "Izberi jezik", "Välj språk",
};

#define COLS 3
#define ROWS 8
#define CX(i) (6 + ((i) / ROWS) * 82)
#define CY(i) (30 + ((i) % ROWS) * 20)
#define CW 80
#define CH 19

static void draw_cell(int i, bool sel)
{
    int x = CX(i), y = CY(i);
    canvas_frame(&g_bot, x, y, CW, CH + 1, sel ? FRAME_SELECT : FRAME_MENU);
    if (sel)
        canvas_text(&g_bot, &font_small, x + 4, y + 3, "▶", C_RED, 0);
    // endonyms are never translated: draw them directly
    const Font *f = font_width(&font_main, g_langs[i].name) > CW - 18 ? &font_small : &font_main;
    canvas_text_n(&g_bot, f, x + 13, f == &font_main ? y : y + 3, g_langs[i].name, 1 << 30, C_INK,
                  sel ? C_GLD_HI : C_SHADOW);
}

// English / French names under the endonym, so close pairs (Slovenčina = Slovak, Slovenščina = Slovenian)
// can be told apart.
static const char *const exonym[LANG_COUNT] = {
    "Bulgarian · Bulgare", "Czech · Tchèque", "Danish · Danois", "German · Allemand", "Greek · Grec",
    "English · Anglais", "Spanish · Espagnol", "Estonian · Estonien", "Finnish · Finnois", "French · Français",
    "Irish · Irlandais", "Croatian · Croate", "Hungarian · Hongrois", "Italian · Italien", "Lithuanian · Lituanien",
    "Latvian · Letton", "Maltese · Maltais", "Dutch · Néerlandais", "Polish · Polonais", "Portuguese · Portugais",
    "Romanian · Roumain", "Slovak · Slovaque", "Slovenian · Slovène", "Swedish · Suédois",
};

static void draw_top(int sel)
{
    canvas_clear(&g_top, 0);
    ui_backdrop(&g_top);
    ui_panel(&g_top, 20, 64, 216, 64, true);
    const char *s = choose[sel];
    int w = font_width(&font_main, s);
    canvas_text_n(&g_top, &font_main, 128 - w / 2, 74, s, 1 << 30, C_GOLD, C_INK);
    w = font_width(&font_small, g_langs[sel].name);
    canvas_text_n(&g_top, &font_small, 128 - w / 2, 96, g_langs[sel].name, 1 << 30, C_BTN_MID, C_INK);
    w = font_width(&font_small, exonym[sel]);
    canvas_text_n(&g_top, &font_small, 128 - w / 2, 110, exonym[sel], 1 << 30, C_BTN_LO, C_INK);
}

int lang_picker(int current)
{
    int sel = current >= 0 ? current : 9;
    gfx_brightness(false, 0);
    gfx_brightness(true, 0);
    ui_backdrop(&g_bot);
    ui_header(&g_bot, 24, 3, 208, "Langue · Language");
    for (int i = 0; i < LANG_COUNT; i++)
        draw_cell(i, i == sel);
    draw_top(sel);
    while (1) {
        frame_wait();
        int old = sel;
        if (g_krep & KEY_DOWN) sel = (sel + 1) % LANG_COUNT;
        if (g_krep & KEY_UP) sel = (sel + LANG_COUNT - 1) % LANG_COUNT;
        if (g_krep & KEY_RIGHT) sel = (sel + ROWS) % LANG_COUNT;
        if (g_krep & KEY_LEFT) sel = (sel + LANG_COUNT - ROWS) % LANG_COUNT;
        int pick = -1;
        for (int i = 0; i < LANG_COUNT; i++)
            if (touch_in(CX(i), CY(i), CW, CH))
                pick = sel = i;
        if (g_kdown & (KEY_A | KEY_START))
            pick = sel;
        if (sel != old) {
            sfx_play(SFX_CURSOR);
            draw_cell(old, false);
            draw_cell(sel, true);
            draw_top(sel);
        }
        if (pick >= 0) {
            sfx_play(SFX_SELECT);
            for (int k = 0; k < 10; k++)
                frame_wait();
            break;
        }
    }
    canvas_clear(&g_top, 0);
    canvas_clear(&g_bot, 0);
    return sel;
}
