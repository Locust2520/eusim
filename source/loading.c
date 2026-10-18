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
    "Le saviez-vous ? Le Parlement déménage à Strasbourg douze fois par an, malles comprises.",
    "Il y a 24 langues officielles dans l'UE. Votre stagiaire en parle une et demie.",
    "Astuce : les bouchons attachés à la bouteille ne se perdent plus (directive 2019/904).",
    "Chargement… comme la fin du changement d'heure : votée en 2019, toujours en attente.",
    "Le drapeau européen a 12 étoiles. Ce n'est pas le nombre de pays : c'est un symbole de perfection.",
    "La Déclaration Schuman date du 9 mai 1950. Le 9 mai, c'est la Fête de l'Europe !",
    "Les pièces en euros sont arrivées dans les poches le 1er janvier 2002.",
    "Depuis juin 2017, plus de frais d'itinérance en Europe. Appelez votre mère depuis Lisbonne !",
    "Le chargeur universel USB-C est obligatoire depuis fin 2024. Adieu le tiroir à câbles.",
    "Erasmus est né en 1987. Des millions d'étudiants ont depuis appris à cuisiner des pâtes.",
    "L'accord de Schengen a été signé en 1985 sur un bateau, sur la Moselle, au Luxembourg.",
    "Le Parlement européen compte 720 députés depuis 2024.",
    "Astuce : la cantine soigne toute votre équipe. Le café, lui, ne soigne rien.",
    "Astuce : courez en maintenant B. Les couloirs du Berlaymont sont longs.",
    "Le règlement sur la courbure des bananes (1994) existe… mais il parle surtout de qualité.",
    "Le RGPD (2018) vous a offert des bandeaux cookies. Beaucoup de bandeaux cookies.",
    "Le prix Nobel de la paix a été attribué à l'Union européenne en 2012.",
    "Le Traité de Rome (1957) a créé la Communauté économique européenne.",
    "Le Traité de Maastricht (1992) a créé l'Union européenne et prévu l'euro.",
    "Le Traité de Lisbonne (2007) contient l'article 50. Un seul pays l'a utilisé.",
    "Le Royaume-Uni a quitté l'UE le 31 janvier 2020. Oliver ne s'en est toujours pas remis.",
    "Astuce : les Tampons officiels capturent mieux les Euromons affaiblis.",
    "Astuce : un Euromon endormi par un Sommet nocturne est plus facile à capturer.",
    "Le Berlaymont a été désamianté de 1991 à 2004. La réunion de chantier a été longue.",
    "La Cour de justice de l'UE siège au Luxembourg, sur le plateau du Kirchberg.",
    "La BCE est à Francfort. Sa tour a coûté plus cher que prévu. Inflation, sans doute.",
    "Simone Veil fut la première présidente du Parlement européen élu, en 1979.",
    "La Commission a 27 commissaires : un par pays. Même pour la politique des pêches de l'Autriche.",
    "Astuce : appuyez sur X pour ouvrir le menu.",
    "Le Danube traverse dix pays. Vos chaussures, seulement deux.",
    "Le jour de l'Europe, un Euromon rare apparaît. Essayez le 9 mai !",
    "Les traductions de l'UE représentent des millions de pages par an.",
    "L'hymne européen est l'Ode à la joie de Beethoven, sans paroles officielles.",
    "Astuce : les attaques de type Juridique sont super efficaces contre le Lobby.",
    "Astuce : le Veto bloque une attaque, mais pas votre détermination.",
    "Le Brexit a duré si longtemps qu'on a inventé le mot « Brextension ».",
    "Il existe un bureau de liaison du Parlement dans chaque État membre.",
    "Astuce : parlez à tout le monde. Même au pigeon de la place Lux.",
    "Le Danemark a une exemption sur l'euro. Il garde sa couronne, et ses vikings.",
    "Chargement des 27 avis nationaux… 26 sur 27… On attend la Hongrie.",
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
    ui_text_in(&g_bot, &font_main, 12, 56, 232, 20, "Le saviez-vous ?", C_BLUE, C_SHADOW, 0);
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
    canvas_text_center(&g_top, &font_small, 128, 170, "Chargement…", C_WHITE, C_BLUE_D);

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
