#pragma once
#include "common.h"

// Translations. French is the source language: every string is looked up by the hash of its French text in
// nitrofs/lang/<code>.bin (built by tools/mklang.py from assets/i18n/<code>*.txt).
// Missing translations use English. Selecting French uses the source text.
#define LANG_COUNT 24
#define LANG_DEFAULT 5 // English
typedef struct {
    const char *code;   // ISO 639-1
    const char *name;   // endonym
} LangInfo;
extern const LangInfo g_langs[LANG_COUNT];
extern int g_lang;      // index in g_langs

const char *tr(const char *french);
#define T(s) tr(s)
#define N_(s) (s)       // marks a string for extraction only (static tables); translate at use with T()
void lang_set(int index); // loads the table and re-translates the game data (species, moves, items…)
int lang_index(const char *code);
void *lang_load_text(const char *path, u32 *size); // localized text file, English fallback
