// New game intro: Professor Robert Schuman, choice of character, name entry, rival.
#include "scenes.h"
#include "canvas.h"
#include "gfx.h"
#include "image.h"
#include "input.h"
#include "audio.h"
#include "dialog.h"
#include "portrait.h"
#include "save.h"
#include "ui.h"
#include "gen/font_data.h"

static void bottom_flag(void)
{
    ui_backdrop(&g_bot);
}

void scene_intro(void)
{
    gfx_clear_scene(false);
    gfx_clear_scene(true);
    canvas_clear(&g_top, 0);
    BG_PALETTE[0] = RGB8(16, 24, 72);
    bottom_flag();
    music_play("intro");
    gfx_fade_in(30, false);

    portrait_show(SIDE_LEFT, "schuman", "happy");
    portrait_focus(-1);
    while (portrait_busy())
        frame_wait();
    const char *S = "Professeur Schuman";
    dlg_say(S, "Bonjour, bonjour ! Bienvenue dans le monde merveilleux… et légèrement administratif… de l'Union européenne !");
    portrait_expr(SIDE_LEFT, "neutral");
    dlg_say(S, "Je m'appelle Robert Schuman. Tu as peut-être entendu parler de moi : une histoire de charbon, d'acier et de 9 mai… Je te la raconterai.");
    dlg_say(S, "Depuis, ce monde est peuplé de créatures étranges : les EUROMONS !\fDirectives, règlements, amendements, bandeaux cookies… Ils vivent dans les piles de dossiers et la moquette des couloirs.");
    portrait_expr(SIDE_LEFT, "happy");
    dlg_say(S, "Certains les collectionnent, d'autres les font débattre. Moi, je les étudie. C'est ce qu'on appelle… la comitologie !");
    portrait_expr(SIDE_LEFT, "neutral");
    dlg_say(S, "Mais parlons de toi. Ce matin, deux stagiaires sont attendus au Parlement européen…");
    // show both player characters so the choice is obvious
    portrait_hide(SIDE_LEFT);
    while (portrait_busy())
        frame_wait();
    portrait_show(SIDE_LEFT, "alex", "happy");
    portrait_show(SIDE_RIGHT, "max", "happy");
    portrait_focus(-1);
    while (portrait_busy())
        frame_wait();
    dlg_say_nowait(S, "À gauche, Alex, la nouvelle stagiaire. À droite, Max, le nouveau stagiaire. Qui es-tu ?");
    static const char *const who[2] = {"Alex, une fille", "Max, un garçon"};
    int g = dlg_choice(who, 2, false);
    g_save.player_gender = g;
    strcpy(g_save.player_name, g == 0 ? "Alex" : "Max");
    portrait_hide(g == 0 ? SIDE_RIGHT : SIDE_LEFT);
    portrait_focus(g == 0 ? SIDE_LEFT : SIDE_RIGHT);
    for (int i = 0; i < 40; i++)
        frame_wait();
    portrait_hide_all();
    portrait_show(SIDE_LEFT, "schuman", "happy");
    while (portrait_busy())
        frame_wait();
    dlg_say(S, "Parfait ! Et comment dois-je t'appeler, officiellement ? Il faut que ce soit écrit dans les 24 langues, alors choisis bien.");
    dlg_close();
    keyboard_input("Ton prénom (10 lettres max.) :", g_save.player_name, sizeof g_save.player_name, 10);
    portrait_expr(SIDE_LEFT, "happy");
    dlg_say(S, "{P} ! Magnifique. Je vais faire traduire ça en maltais tout de suite.");

    portrait_show(SIDE_RIGHT, "oliver", "neutral");
    portrait_focus(SIDE_LEFT);
    dlg_say(S, "Voici Oliver, ton collègue stagiaire, venu tout droit de Londres. Il est… très confiant.");
    portrait_focus(SIDE_RIGHT);
    dlg_say("Oliver", "Hello ! Don't worry, {P}, je serai le meilleur stagiaire de toute l'Union. Easy.");
    portrait_focus(SIDE_LEFT);
    portrait_expr(SIDE_LEFT, "neutral");
    dlg_say(S, "Votre mission, à tous les deux, est simple : faire adopter UNE directive.\fLa directive sur la fin du changement d'heure. Le Parlement l'a votée en mars 2019…");
    portrait_expr(SIDE_LEFT, "worried");
    dlg_say(S, "… et depuis, elle dort au Conseil. Comme beaucoup de choses.");
    portrait_expr(SIDE_LEFT, "happy");
    dlg_say(S, "Pour y arriver, il vous faudra les 8 badges des grandes villes d'Europe, convaincre le Conseil européen, et la présidente de la Commission elle-même !\fAllez, {P}. Ton stage commence maintenant. Il n'est pas rémunéré, mais il est formateur !");
    dlg_close();
    portrait_hide_all();
    music_fade_out(30);
    gfx_fade_out(30, false);
    canvas_clear(&g_top, 0);
    canvas_clear(&g_bot, 0);
    gfx_clear_scene(true);
}
