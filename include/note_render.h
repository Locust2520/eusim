#pragma once
// Specimen banknotes of the ECB studio: drawing only (see note.c for the screens).
// The design follows the brief of the ECB's 2025-2026 contest for the next euro banknotes: same sizes and dominant
// colours as today, European flag and map, and the two finalist themes ("European culture", "Rivers and birds").
#include "common.h"
#include "canvas.h"
#include "save.h"

enum { NOTE_CULTURE, NOTE_BIRDS };
#define NOTE_DENOMS 6
extern const int note_values[NOTE_DENOMS];   // 5, 10, 20, 50, 100, 200

// Palette: NOTE_PAL_N colours written at NOTE_PAL in the BG palette of the screen showing the note.
#define NOTE_PAL 1
#define NOTE_PAL_N 48
#define NOTE_GREY (NOTE_PAL + 32)   // 16 neutral greys (photo preview, drawing)
void note_palette(u16 *out, int denom);

// Pictures from nitrofs/ui/note_art.bin (tools/mknote.py): 4-bit darkness maps.
enum { ART_BIRD = 0, ART_INSTITUTION = 6, ART_CULTURE = 12, ART_MAP = 18, ART_COUNT = 19 };
typedef struct {
    int count, w, h;
    const u8 *px;      // count images, w * h / 2 bytes each, low nibble = left pixel
} NoteArt;
bool note_art_parse(NoteArt *art, const u8 *blob, u32 size);

// Size on screen of a note (real proportions: 120 x 62 mm for 5 euros … 153 x 77 mm for 200 euros)
void note_card_size(int denom, int *w, int *h);
// Draw the front or the back of the note with its top-left corner at (x, y).
void note_draw(Canvas *c, int x, int y, const SaveExtra *note, const NoteArt *art, bool back);
// Engrave a 4-bit portrait into the canvas (also used for live previews while drawing).
void note_engrave_face(Canvas *c, int x, int y, const u8 *px4, int scale);
