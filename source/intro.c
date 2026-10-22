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
    const char *S = "Professor Schuman";
    dlg_say(S, "Hello, hello! Welcome to the wonderful… and slightly bureaucratic… world of the European Union!");
    portrait_expr(SIDE_LEFT, "neutral");
    dlg_say(S, "My name is Robert Schuman. Perhaps you've heard of me: a story about coal, steel and the 9th of May… I'll tell you about it.");
    dlg_say(S, "Since then, this world has been inhabited by strange creatures: EUROMONS!\fDirectives, regulations, amendments, cookie banners… They live in piles of files and in the corridor carpets.");
    portrait_expr(SIDE_LEFT, "happy");
    dlg_say(S, "Some people collect them, others make them debate. Me, I study them. That's what we call… comitology!");
    portrait_expr(SIDE_LEFT, "neutral");
    dlg_say(S, "But let's talk about you. This morning, two interns are expected at the European Parliament…");
    // show both player characters so the choice is obvious
    portrait_hide(SIDE_LEFT);
    while (portrait_busy())
        frame_wait();
    portrait_show(SIDE_LEFT, "alex", "happy");
    portrait_show(SIDE_RIGHT, "max", "happy");
    portrait_focus(-1);
    while (portrait_busy())
        frame_wait();
    dlg_say_nowait(S, "On the left, Alex, the new intern — a girl. On the right, Max, the new intern — a boy. Who are you?");
    static const char *const who[2] = {"Alex, a girl", "Max, a boy"};
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
    dlg_say(S, "Perfect! And what shall I officially call you? It has to be written in all 24 languages, so choose carefully.");
    dlg_close();
    keyboard_input("Your first name (10 letters max.):", g_save.player_name, sizeof g_save.player_name, 10);
    portrait_expr(SIDE_LEFT, "happy");
    dlg_say(S, "{P}! Marvellous. I'll have it translated into Maltese right away.");

    portrait_show(SIDE_RIGHT, "oliver", "neutral");
    portrait_focus(SIDE_LEFT);
    dlg_say(S, "This is Oliver, your fellow intern, straight from London. He's… very confident.");
    portrait_focus(SIDE_RIGHT);
    dlg_say("Oliver", "Hello! Don't worry, {P}, I'll be the best intern in the whole Union. Easy.");
    portrait_focus(SIDE_LEFT);
    portrait_expr(SIDE_LEFT, "neutral");
    dlg_say(S, "Your mission, for both of you, is simple: get ONE directive adopted.\fThe directive ending the clock change. Parliament voted for it in March 2019…");
    portrait_expr(SIDE_LEFT, "worried");
    dlg_say(S, "… and since then, it's been sleeping in the Council. Like many things.");
    portrait_expr(SIDE_LEFT, "happy");
    dlg_say(S, "To succeed, you'll need the 8 badges of Europe's great cities, to convince the European Council, and the President of the Commission herself!\fCome on, {P}. Your internship starts now. It's unpaid, but very educational!");
    dlg_close();
    portrait_hide_all();
    music_fade_out(30);
    gfx_fade_out(30, false);
    canvas_clear(&g_top, 0);
    canvas_clear(&g_bot, 0);
    gfx_clear_scene(true);
}
