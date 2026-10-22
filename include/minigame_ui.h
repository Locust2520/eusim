#pragma once
// Shared screens of the touch mini-games (minigame.c) and the city mini-games (minigame2.c).
#include "common.h"
#include "canvas.h"

bool mg_intro(const char *title, const char *text);                 // title card, rules, 3-2-1
int mg_outro(bool ok, const char *win, const char *lose);           // result line, returns 1/0
// Top screen: title, rule, time left and score (goal < 0: score is a percentage of time on target)
void mg_top_panel(const char *title, const char *rule, int secs_left, int score, int goal);

// City mini-games (minigame2.c)
int mg_billets(void);      // ECB studio, Frankfurt: feel, look, tilt
int mg_bembel(void);       // apple-wine tavern, Sachsenhausen
int mg_evzones(void);      // changing of the guard, Syntagma (Athens)
int mg_periptero(void);    // kiosk, Monastiraki (Athens)
int mg_conteneurs(void);   // container ship, Piraeus
int mg_tapis(void);        // flower carpet, Grand-Place (Brussels)
int mg_cigognes(void);     // storks, Petite France (Strasbourg)
int mg_douane(void);       // post-Brexit customs (London)
int mg_echecs(void);       // chess in the Széchenyi baths (Budapest)
int mg_schuman(void);      // the Schuman Declaration, Salon de l'Horloge (Paris)
int mg_casemates(void);    // the Bock casemates (Luxembourg)
