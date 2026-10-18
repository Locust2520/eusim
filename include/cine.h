#pragma once
#include "common.h"

// Cinematic slides on the top screen (384x256 pictures with slow pan/zoom, transitions, title cards).
enum { MOT_STILL, MOT_ZOOM_IN, MOT_ZOOM_OUT, MOT_PAN_RIGHT, MOT_PAN_LEFT, MOT_TILT_UP, MOT_TILT_DOWN };
enum { TR_FADE, TR_CUT, TR_FLASH, TR_IRIS, TR_WIPE };

void cine_begin(const char *title);              // leave the map view (fade), letterbox, bottom-screen panel
void cine_slide(const char *name, int motion, int transition);
void cine_card(const char *title, const char *subtitle); // chapter-style title card on black
void cine_end(void);                             // back to the map
bool cine_active(void);
bool cine_skipping(void);                        // START pressed: dialogue is skipped until cine_end
void cine_letterbox(void);                       // redraw the bars (after the dialogue box is cleared)
