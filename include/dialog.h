#pragma once
#include "common.h"

// Dialogue box on the top screen (Pokémon-style), typewriter text, voice blips.
// Text codes: {P} player name, {R} rival name, {M} money, {V0}..{V9} script string vars,
//             \n new line, \f new page.
void dlg_say(const char *speaker, const char *text);
// Same but does not wait for a key at the end (box stays; for "and then the choice")
void dlg_say_nowait(const char *speaker, const char *text);
void dlg_close(void);
bool dlg_is_open(void);
// Choice list on the bottom screen (touch + d-pad). Returns index, or -1 if cancelled (when allow_cancel).
int dlg_choice(const char *const *options, int n, bool allow_cancel);
bool dlg_yesno(void);
// Expand {P} etc. into out
void dlg_expand(const char *in, char *out, int max);
// A message on the bottom screen centred in a panel (for system messages)
void dlg_notice(const char *text);
// Voice pitch for a speaker (stable hash)
int dlg_voice_for(const char *speaker);

// Bottom-screen backup/restore (for overlays)
void ui_bottom_push(void);
void ui_bottom_pop(void);

extern char g_strvar[10][24];
