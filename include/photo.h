#pragma once
// DSi camera (DSi, and 3DS in DSi mode): photo of the player's face for the specimen banknote.
#include "common.h"

// True when the game runs in DSi mode, where the cameras can exist.
bool photo_available(void);
// Camera screen. On success fills px4 (NOTE_W x NOTE_H, 4-bit darkness) and returns 1; returns 0 if the
// player backs out, -1 if the camera could not be started (the caller then offers drawing instead).
int photo_capture(u8 *px4);
