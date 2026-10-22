#pragma once
// The ECB studio's specimen banknote: making it (camera / drawing / official portrait) and looking at it.
#include "common.h"
#include "save.h"

// Studio session: portrait, theme and value, printing. Returns true when a note was printed into g_save_extra.
bool note_studio(void);
// Full-screen viewer of the player's note (front on top, back below). Restores the screens it used.
void note_view(void);
// The player's note, or (when none was printed) a default one made from the official portrait.
void note_current(SaveExtra *out);
// Ending scene: the note on the top screen with a closing line on the bottom one.
void note_ending(void);
