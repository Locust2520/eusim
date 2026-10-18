#pragma once
#include "common.h"
#include "canvas.h"
#include "font.h"

// Retro-styled widgets drawn into a canvas: bevelled gradient buttons, panels, headers.
typedef enum { BTN_NORMAL, BTN_SELECTED, BTN_DARK, BTN_RED, BTN_DISABLED, BTN_GREEN, BTN_PRESSED } BtnStyle;

void ui_gradient(Canvas *c, int x, int y, int w, int h, u8 top, u8 mid, u8 bottom);
void ui_button(Canvas *c, int x, int y, int w, int h, const char *label, BtnStyle st, const Font *f);
void ui_target_corners(Canvas *c, int x, int y, int w, int h);
// Button with a small icon (12x12 bitmap from ICON_*, displayed at 2x) on the left
void ui_button_icon(Canvas *c, int x, int y, int w, int h, const char *label, BtnStyle st, int icon);
void ui_panel(Canvas *c, int x, int y, int w, int h, bool dark);
void ui_header(Canvas *c, int x, int y, int w, const char *text);
void ui_backdrop(Canvas *c);                       // full-screen navy gradient + star dots (no black areas)
// Text vertically centred in a box (uses the font's cap height)
void ui_text_in(Canvas *c, const Font *f, int x, int y, int w, int h, const char *s, u8 col, u8 shadow, int align);
int ui_font_cap_top(const Font *f);
int ui_font_cap_h(const Font *f);

enum { ICON_TEAM, ICON_BAG, ICON_DEX, ICON_MAP, ICON_SAVE, ICON_OPTIONS, ICON_FIGHT, ICON_RUN, ICON_STAR, ICON_COUNT };
void ui_icon(Canvas *c, int x, int y, int icon, int scale);
void ui_backdrop_rect(Canvas *c, int x, int y, int w, int h);
int ui_text_wrapped(Canvas *c, const Font *f, int x, int y, int w, const char *s, u8 col, u8 shadow);

#define SB_W 11
// Touch-only scrollbar for long lists: draw it, then each frame ask for the dragged first index (-1 = none)
void ui_scrollbar(Canvas *c, int x, int y, int h, int total, int vis, int first);
int ui_scrollbar_drag(int x, int y, int h, int total, int vis);
