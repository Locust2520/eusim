// Loading screen: the 12 stars of the EU flag turning in a circle on EU blue, with trails,
// one star lighting up in turn like a progress bar, and a random "le saviez-vous ?" hint.
#include "scenes.h"
#include "gfx.h"
#include "ui.h"
#include "canvas.h"
#include "input.h"
#include "sprite.h"
#include "audio.h"
#include "gen/font_data.h"

static const char *const hints[] = {
    "Did you know? Parliament moves to Strasbourg twelve times a year, trunks included.",
    "The EU has 24 official languages. Your intern speaks one and a half.",
    "Tip: caps attached to the bottle no longer get lost (Directive 2019/904).",
    "Loading… like the end of the clock change: voted in 2019, still pending.",
    "The European flag has 12 stars. It's not the number of countries: it's a symbol of perfection.",
    "The Schuman Declaration dates from 9 May 1950. 9 May is Europe Day!",
    "Euro coins arrived in people's pockets on 1 January 2002.",
    "Since June 2017, no more roaming charges in Europe. Call your mum from Lisbon!",
    "The universal USB-C charger has been mandatory since late 2024. Farewell, drawer of cables.",
    "Erasmus was born in 1987. Since then, millions of students have learned to cook pasta.",
    "The Schengen Agreement was signed in 1985 on a boat on the Moselle, in Luxembourg.",
    "The European Parliament has had 720 MEPs since 2024.",
    "Tip: the canteen heals your whole team. Coffee, on the other hand, heals nothing.",
    "Tip: hold B to run. The Berlaymont's corridors are long.",
    "The regulation on banana curvature (1994) exists… but it's mostly about quality.",
    "The GDPR (2018) gave you cookie banners. Lots of cookie banners.",
    "The Nobel Peace Prize was awarded to the European Union in 2012.",
    "The Treaty of Rome (1957) created the European Economic Community.",
    "The Maastricht Treaty (1992) created the European Union and planned the euro.",
    "The Treaty of Lisbon (2007) contains Article 50. Only one country has used it.",
    "The United Kingdom left the EU on 31 January 2020. Oliver still hasn't got over it.",
    "Tip: Official Stamps capture weakened Euromons better.",
    "Tip: a Euromon put to sleep by a Night Summit is easier to capture.",
    "The Berlaymont was cleared of asbestos from 1991 to 2004. The site meeting was a long one.",
    "The EU Court of Justice sits in Luxembourg, on the Kirchberg plateau.",
    "The ECB is in Frankfurt. Its tower cost more than planned. Inflation, no doubt.",
    "Simone Veil was the first President of the elected European Parliament, in 1979.",
    "The Commission has 27 commissioners: one per country. Even for Austria's fisheries policy.",
    "Tip: press X to open the menu.",
    "The Danube flows through ten countries. Your shoes, only two.",
    "On Europe Day, a rare Euromon appears. Try 9 May!",
    "EU translations amount to millions of pages a year.",
    "The European anthem is Beethoven's Ode to Joy, with no official lyrics.",
    "Tip: Legal-type moves are super effective against Lobby.",
    "Tip: Veto blocks an attack, but not your determination.",
    "Brexit lasted so long that the word “Brextension” was invented.",
    "Parliament has a liaison office in every member state.",
    "Tip: talk to everyone. Even the pigeon on Place Lux.",
    "Denmark has an opt-out from the euro. It keeps its krone, and its Vikings.",
    "Loading 27 national opinions… 26 out of 27… Waiting for Hungary.",
};

static SpriteSheet stars, sofa;
static u16 *gfx_star[3], *gfx_sofa;

void loading_screen(int min_frames)
{
    gfx_brightness(false, -16);
    gfx_brightness(true, -16);
    gfx_clear_scene(false);
    gfx_clear_scene(true);
    canvas_clear(&g_top, 0);
    canvas_clear(&g_bot, 0);
    u16 bg_top = BG_PALETTE[0], bg_bot = BG_PALETTE_SUB[0];
    BG_PALETTE[0] = RGB8(0, 51, 153);
    BG_PALETTE_SUB[0] = RGB8(0, 36, 110);
    sheet_load(&stars, "ui/stars.spr");
    sheet_load(&sofa, "ui/sofa.spr");
    spr_ext_pal(false, PAL_FX_LOAD, stars.pal, stars.ncolors);
    spr_ext_pal(false, PAL_FX_LOAD + 1, sofa.pal, sofa.ncolors);
    for (int i = 0; i < 3; i++) {
        gfx_star[i] = spr_alloc(false, SpriteSize_16x16, SpriteColorFormat_256Color);
        spr_upload(gfx_star[i], sheet_frame(&stars, i), 256);
    }
    gfx_sofa = spr_alloc(false, SpriteSize_32x32, SpriteColorFormat_256Color);
    spr_upload(gfx_sofa, sheet_frame(&sofa, 0), 1024);

    const char *hint = hints[rng_range(ARRAY_LEN(hints))];
    ui_backdrop(&g_bot);
    canvas_frame(&g_bot, 12, 50, 232, 92, FRAME_DIALOG);
    ui_text_in(&g_bot, &font_main, 12, 56, 232, 20, "Did you know?", C_BLUE, C_SHADOW, 0);
    canvas_hline(&g_bot, 40, 77, 176, C_GOLD);
    // wrap hint manually into the panel
    {
        char line[80];
        const char *s = hint;
        int y = 80;
        while (*s && y < 132) {
            int n = 0, last_sp = -1;
            while (s[n] && font_width_n(&font_small, s, n + 1) < 212) {
                if (s[n] == ' ')
                    last_sp = n;
                n++;
            }
            if (s[n] && last_sp > 0)
                n = last_sp;
            memcpy(line, s, n);
            line[n] = 0;
            canvas_text_center(&g_bot, &font_small, 128, y, line, C_TEXT, C_SHADOW);
            s += n;
            while (*s == ' ')
                s++;
            y += 12;
        }
    }
    canvas_text_center(&g_top, &font_small, 128, 170, "Loading…", C_WHITE, C_BLUE_D);

    bool sofa_mode = (g_kheld & KEY_L) != 0;
    for (int t = 0; t < min_frames + 16; t++) {
        int fade = t < 8 ? -16 + t * 2 : (t >= min_frames + 8 ? -(t - min_frames - 8) * 2 : 0);
        gfx_brightness(false, fade);
        gfx_brightness(true, fade);
        int ang = t * 200;
        oamRotateScale(&oamMain, 1, -(t * 250) & 0xFFFF, intToFixed(1, 8), intToFixed(1, 8));
        int lit = (t / 5) % 12;
        for (int i = 0; i < 12; i++) {
            int a = ang + i * 65536 / 12;
            int x = 128 + (sinLerp(a) * 52 >> 12) - 8;
            int y = 84 - (cosLerp(a) * 52 >> 12) - 8;
            bool sit = sofa_mode && i == 0;
            if (sit) {
                x = 128 - 8;
                y = 84 - 8 - 6;
            }
            oamSet(&oamMain, i, x, y, 1, PAL_FX_LOAD, SpriteSize_16x16, SpriteColorFormat_256Color,
                   gfx_star[i == lit ? 2 : 0], 1, false, false, false, false, false);
            // trail (lagging, dim)
            int a2 = a - 2600;
            int x2 = 128 + (sinLerp(a2) * 52 >> 12) - 8;
            int y2 = 84 - (cosLerp(a2) * 52 >> 12) - 8;
            oamSet(&oamMain, 12 + i, x2, y2, 2, PAL_FX_LOAD, SpriteSize_16x16, SpriteColorFormat_256Color,
                   gfx_star[1], -1, false, sit, false, false, false);
        }
        oamSet(&oamMain, 24, 128 - 16, 84 - 16 + 2, 2, PAL_FX_LOAD + 1, SpriteSize_32x32, SpriteColorFormat_256Color,
               gfx_sofa, -1, false, !sofa_mode, false, false, false);
        frame_wait();
    }
    spr_hide_range(false, 0, 24);
    oamUpdate(&oamMain);
    for (int i = 0; i < 3; i++)
        spr_free(false, gfx_star[i]);
    spr_free(false, gfx_sofa);
    sheet_free(&stars);
    sheet_free(&sofa);
    canvas_clear(&g_top, 0);
    canvas_clear(&g_bot, 0);
    BG_PALETTE[0] = bg_top;
    BG_PALETTE_SUB[0] = bg_bot;
}
