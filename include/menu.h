#pragma once
#include "common.h"
#include "canvas.h"
#include "save.h"
void menu_draw_panel(void);      // overworld bottom screen
int menu_panel_input(void);      // -1 or menu id to open
void menu_open(int id);
void menu_save(void);
void shop_open(int shop);
void archives_open(void);
void jukebox_open(void);
void badge_case_open(void);
int party_menu(int mode, const char *prompt);
int bag_menu(int mode);
void dex_menu(void);
void mon_summary(Mon *m);
void draw_hp_bar(Canvas *c, int x, int y, int w, int hp, int max);
void draw_type_ribbon(Canvas *c, int x, int y, int w, int h, int type1, int type2);
void draw_type_badge(Canvas *c, int x, int y, int type);
void europe_map_markers(void);
void evolve_mon(Mon *m, int into);
