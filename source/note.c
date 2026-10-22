// The ECB studio (Frankfurt): the player's portrait becomes a specimen of the next euro banknotes.
// Portrait from the DSi camera, a stylus drawing or the official photo; theme and value of one of the
// finalist designs of the ECB's 2026 contest; printed with a SPECIMEN overprint (see note_render.c).
#include "note.h"
#include "note_render.h"
#include "photo.h"
#include "canvas.h"
#include "gfx.h"
#include "ui.h"
#include "input.h"
#include "audio.h"
#include "dialog.h"
#include "fs.h"
#include "lang.h"
#include "mon.h"
#include "gen/data_ids.h"
#include "gen/flags.h"
#include "gen/font_data.h"

// Motifs of the ten finalist designs (shortlist published by the ECB on 23 July 2026)
static const char *const people[NOTE_DENOMS] = {"Maria Callas", "Ludwig van Beethoven", "Marie Curie",
                                                "Miguel de Cervantes", "Leonardo da Vinci", "Bertha von Suttner"};
static const char *const spaces[NOTE_DENOMS] = {"street performers", "a song festival", "a school", "a library",
                                                "street art", "a tree-lined square"};
static const char *const birds[NOTE_DENOMS] = {
    "a wallcreeper by a mountain spring", "a kingfisher at a waterfall", "bee-eaters in a river valley",
    "a white stork by a meandering river", "an avocet at a river mouth", "a northern gannet over the sea"};
static const char *const institutions[NOTE_DENOMS] = {
    "the European Parliament", "the European Commission", "the European Central Bank",
    "the Court of Justice of the EU", "the European Council and the Council of the EU", "the European Court of Auditors"};

static u8 *art_blob;
static NoteArt art;

static bool art_open(void)
{
    u32 n = 0;
    art_blob = fs_try_load("ui/note_art.bin", &n);
    return art_blob && note_art_parse(&art, art_blob, n);
}

static void art_close(void)
{
    free(art_blob);
    art_blob = NULL;
}

// ---------------------------------------------------------------- borrowing the screens
typedef struct {
    u16 pal[2][NOTE_PAL_N];
    u8 *px[2];
    u32 dispcnt[2];
} Screens;

static void screens_take(Screens *s)
{
    memcpy(s->pal[0], (const void *)&BG_PALETTE[NOTE_PAL], sizeof s->pal[0]);
    memcpy(s->pal[1], (const void *)&BG_PALETTE_SUB[NOTE_PAL], sizeof s->pal[1]);
    s->px[0] = malloc(256 * 192);
    s->px[1] = malloc(256 * 192);
    if (s->px[0])
        memcpy(s->px[0], g_top.px, 256 * 192);
    if (s->px[1])
        memcpy(s->px[1], g_bot.px, 256 * 192);
    s->dispcnt[0] = REG_DISPCNT;
    s->dispcnt[1] = REG_DISPCNT_SUB;
    REG_DISPCNT &= ~DISPLAY_SPR_ACTIVE;       // characters and portraits would show through the note
    REG_DISPCNT_SUB &= ~DISPLAY_SPR_ACTIVE;
}

static void screens_give_back(Screens *s)
{
    frame_wait();
    gfx_bg_pal(false, NOTE_PAL, s->pal[0], NOTE_PAL_N);
    gfx_bg_pal(true, NOTE_PAL, s->pal[1], NOTE_PAL_N);
    if (s->px[0])
        memcpy(g_top.px, s->px[0], 256 * 192);
    if (s->px[1])
        memcpy(g_bot.px, s->px[1], 256 * 192);
    canvas_dirty(&g_top, 0, 192);
    canvas_dirty(&g_bot, 0, 192);
    free(s->px[0]);
    free(s->px[1]);
    REG_DISPCNT = s->dispcnt[0];
    REG_DISPCNT_SUB = s->dispcnt[1];
}

static void load_palette(int denom)
{
    u16 pal[NOTE_PAL_N];
    note_palette(pal, denom);
    gfx_bg_pal(false, NOTE_PAL, pal, NOTE_PAL_N);
    gfx_bg_pal(true, NOTE_PAL, pal, NOTE_PAL_N);
}

// ---------------------------------------------------------------- the player's note
static void official_face(u8 *px4)
{
    if (fs_load_into(g_save.player_gender ? "ui/note_face_max.bin" : "ui/note_face_alex.bin", px4,
                     NOTE_W * NOTE_H / 2) != NOTE_W * NOTE_H / 2)
        memset(px4, 0, NOTE_W * NOTE_H / 2);
}

void note_current(SaveExtra *out)
{
    if (g_save_extra.magic == SAVE_EXTRA_MAGIC) {
        *out = g_save_extra;
        return;
    }
    memset(out, 0, sizeof *out);
    out->note_denom = 2;
    out->note_theme = NOTE_CULTURE;
    out->note_source = 3;
    u32 h = 2166136261u;
    for (const char *s = g_save.player_name; *s; s++)
        h = (h ^ (u8)*s) * 16777619u;
    out->note_serial = h % 1000000000u;
    official_face(out->note_px);
}

static void centred_note(Canvas *c, const SaveExtra *n, int y, bool back)
{
    int w, h;
    note_card_size(n->note_denom, &w, &h);
    note_draw(c, (256 - w) / 2, y + (126 - h) / 2, n, art_blob ? &art : NULL, back);
}

static void caption(Canvas *c, int y, const char *s)
{
    ui_text_in(c, &font_small, 4, y, 248, 14, s, C_PANEL, 0, 0);
}

static void motif_lines(const SaveExtra *n, char *a, char *b, int size)
{
    int dn = n->note_denom;
    if (n->note_theme == NOTE_CULTURE) {
        snprintf(a, size, T("Front: your portrait, in place of %s"), tr(people[dn]));
        snprintf(b, size, T("Back: %s"), tr(spaces[dn]));
    } else {
        snprintf(a, size, T("Front: %s"), tr(birds[dn]));
        snprintf(b, size, T("Back: %s"), tr(institutions[dn]));
    }
}

static void view_screens(const SaveExtra *n, bool back_on_top)
{
    load_palette(n->note_denom);
    canvas_clear(&g_top, C_NAVY1);
    canvas_clear(&g_bot, C_NAVY1);
    centred_note(&g_top, n, 22, back_on_top);
    centred_note(&g_bot, n, 22, !back_on_top);
    char title[96], a[160], b[160];
    snprintf(title, sizeof title, T("Specimen note – €%d"), note_values[n->note_denom]);
    ui_text_in(&g_top, &font_main, 4, 2, 248, 20, title, C_GOLD, C_BLUE_D, 0);
    caption(&g_top, 152, "Not legal tender: this is a design specimen.");
    motif_lines(n, a, b, sizeof a);
    caption(&g_top, 166, a);
    caption(&g_top, 178, b);
    caption(&g_bot, 4, back_on_top ? "Front side" : "Back side");
    caption(&g_bot, 172, "L/R or tap: turn over · B: close");
}

void note_view(void)
{
    Screens sv;
    screens_take(&sv);
    bool own_art = !art_blob && art_open();
    SaveExtra n;
    note_current(&n);
    bool flipped = false;
    view_screens(&n, flipped);
    frame_wait();
    while (1) {
        frame_wait();
        if (g_kdown & (KEY_B | KEY_A | KEY_START))
            break;
        if ((g_kdown & (KEY_L | KEY_R)) || g_touch_down) {
            flipped = !flipped;
            sfx_play(SFX_PAPER);
            view_screens(&n, flipped);
        }
    }
    sfx_play(SFX_CANCEL);
    if (own_art)
        art_close();
    screens_give_back(&sv);
}

// ---------------------------------------------------------------- drawing the portrait with the stylus
#define DX 8
#define DY 16

static bool in_oval_cell(int x, int y)
{
    int ex = x * 2 - NOTE_W + 1, ey = y * 2 - NOTE_H + 1;
    return ex * ex * 100 / (NOTE_W * NOTE_W) + ey * ey * 100 / (NOTE_H * NOTE_H) <= 100;
}

static void draw_cells(const u8 *cells)
{
    for (int y = 0; y < NOTE_H; y++)
        for (int x = 0; x < NOTE_W; x++) {
            u8 col = in_oval_cell(x, y) ? NOTE_GREY + cells[y * NOTE_W + x] : C_NAVY2;
            u8 *p = g_bot.px + (DY + y * 2) * 256 + DX + x * 2;
            p[0] = p[1] = p[256] = p[257] = col;
        }
    canvas_dirty(&g_bot, DY, DY + NOTE_H * 2);
}

static void pack(const u8 *cells, u8 *px4)
{
    memset(px4, 0, NOTE_W * NOTE_H / 2);
    for (int i = 0; i < NOTE_W * NOTE_H; i++)
        px4[i / 2] |= (i & 1) ? cells[i] << 4 : cells[i];
}

static void draw_preview(const u8 *cells)
{
    static u8 px4[NOTE_W * NOTE_H / 2];
    pack(cells, px4);
    canvas_rect(&g_top, 64, 28, 128, 160, C_NAVY1);
    note_engrave_face(&g_top, 64, 28, px4, 2);
}

static void tool_buttons(int tone, int size)
{
    static const char *const tones[4] = {"Light", "Medium", "Dark", "Eraser"};
    canvas_rect(&g_bot, 140, 0, 116, 192, C_NAVY1);
    for (int i = 0; i < 4; i++)
        ui_button(&g_bot, 144, 4 + i * 26, 108, 24, tones[i], i == tone ? BTN_SELECTED : BTN_NORMAL, &font_small);
    for (int i = 0; i < 3; i++) {   // brush sizes: a dot of the brush's size reads the same in every language
        ui_button(&g_bot, 144 + i * 37, 110, 34, 24, "", i == size ? BTN_SELECTED : BTN_NORMAL, &font_small);
        int r = 2 + i * 2, cx = 144 + i * 37 + 17, cy = 110 + 12;
        for (int dy = -r; dy <= r; dy++) {
            int half = 0;
            while ((half + 1) * (half + 1) + dy * dy <= r * r)
                half++;
            canvas_hline(&g_bot, cx - half, cy + dy, half * 2 + 1, C_INK);
        }
    }
    ui_button(&g_bot, 144, 138, 52, 24, "Undo", BTN_NORMAL, &font_small);
    ui_button(&g_bot, 200, 138, 52, 24, "Clear", BTN_NORMAL, &font_small);
    ui_button(&g_bot, 144, 165, 108, 24, "Done", BTN_GREEN, &font_small);
}

static void paint(u8 *cells, int cx, int cy, int r, int v)
{
    for (int y = cy - r; y <= cy + r; y++)
        for (int x = cx - r; x <= cx + r; x++)
            if (x >= 0 && y >= 0 && x < NOTE_W && y < NOTE_H && (x - cx) * (x - cx) + (y - cy) * (y - cy) <= r * r + r)
                cells[y * NOTE_W + x] = v;
}

// Returns true when the player is done (px4 filled), false when backing out.
static bool draw_face(u8 *px4)
{
    static u8 cells[NOTE_W * NOTE_H], undo[NOTE_W * NOTE_H];
    static const u8 tone_values[4] = {4, 8, 13, 0};
    for (int i = 0; i < NOTE_W * NOTE_H; i++)
        cells[i] = (i & 1) ? px4[i / 2] >> 4 : px4[i / 2] & 15;
    memcpy(undo, cells, sizeof undo);
    int tone = 2, size = 1, last_x = -1, last_y = -1, since = 0;
    load_palette(0);
    canvas_clear(&g_top, C_NAVY1);
    ui_text_in(&g_top, &font_main, 4, 2, 248, 20, "Draw your portrait", C_GOLD, C_BLUE_D, 0);
    caption(&g_top, 16, "The studio engraves it like a banknote portrait.");
    canvas_clear(&g_bot, C_NAVY1);
    tool_buttons(tone, size);
    draw_cells(cells);
    draw_preview(cells);
    bool result = false;
    while (1) {
        frame_wait();
        bool in_area = g_touch_x >= DX && g_touch_x < DX + NOTE_W * 2 && g_touch_y >= DY && g_touch_y < DY + NOTE_H * 2;
        if (g_touch_held && in_area) {
            int cx = (g_touch_x - DX) / 2, cy = (g_touch_y - DY) / 2;
            if (g_touch_down || last_x < 0) {
                memcpy(undo, cells, sizeof undo);
                last_x = cx;
                last_y = cy;
            }
            int steps = MAX(abs(cx - last_x), abs(cy - last_y));
            for (int k = 0; k <= steps; k++)   // continuous stroke between two frames
                paint(cells, last_x + (cx - last_x) * k / MAX(1, steps), last_y + (cy - last_y) * k / MAX(1, steps),
                      size + 1, tone_values[tone]);
            last_x = cx;
            last_y = cy;
            draw_cells(cells);
            if (++since >= 12) {
                draw_preview(cells);
                since = 0;
            }
            continue;
        }
        if (last_x >= 0) {
            last_x = last_y = -1;
            draw_preview(cells);
            since = 0;
        }
        int old_tone = tone, old_size = size;
        for (int i = 0; i < 4; i++)
            if (touch_released_in(144, 4 + i * 26, 108, 24))
                tone = i;
        for (int i = 0; i < 3; i++)
            if (touch_released_in(144 + i * 37, 110, 34, 24))
                size = i;
        if (g_kdown & KEY_UP) tone = (tone + 3) % 4;
        if (g_kdown & KEY_DOWN) tone = (tone + 1) % 4;
        if (g_kdown & KEY_LEFT) size = MAX(0, size - 1);
        if (g_kdown & KEY_RIGHT) size = MIN(2, size + 1);
        if (tone != old_tone || size != old_size) {
            sfx_play(SFX_CURSOR);
            tool_buttons(tone, size);
        }
        if (touch_released_in(144, 138, 52, 24) || (g_kdown & KEY_Y)) {
            memcpy(cells, undo, sizeof cells);
            sfx_play(SFX_CANCEL);
            draw_cells(cells);
            draw_preview(cells);
        }
        if (touch_released_in(200, 138, 52, 24)) {
            memcpy(undo, cells, sizeof undo);
            memset(cells, 0, sizeof cells);
            sfx_play(SFX_PAPER);
            draw_cells(cells);
            draw_preview(cells);
        }
        if (touch_released_in(144, 165, 108, 24) || (g_kdown & (KEY_A | KEY_START))) {
            sfx_play(SFX_SELECT);
            result = true;
            break;
        }
        if (g_kdown & KEY_B) {
            sfx_play(SFX_CANCEL);
            break;
        }
    }
    if (result) {
        // a light blur: stylus pixels become soft tones for the engraving
        static u8 soft[NOTE_W * NOTE_H];
        for (int y = 0; y < NOTE_H; y++)
            for (int x = 0; x < NOTE_W; x++) {
                int sum = cells[y * NOTE_W + x] * 4, n = 4;
                for (int dy = -1; dy <= 1; dy++)
                    for (int dx = -1; dx <= 1; dx++)
                        if ((dx || dy) && x + dx >= 0 && y + dy >= 0 && x + dx < NOTE_W && y + dy < NOTE_H) {
                            sum += cells[(y + dy) * NOTE_W + x + dx];
                            n++;
                        }
                soft[y * NOTE_W + x] = (sum + n / 2) / n;
            }
        pack(soft, px4);
    }
    return result;
}

// ---------------------------------------------------------------- choosing the design
static void design_screen(const SaveExtra *n, bool back)
{
    load_palette(n->note_denom);
    canvas_clear(&g_top, C_NAVY1);
    ui_text_in(&g_top, &font_main, 4, 2, 248, 20, "Your specimen note", C_GOLD, C_BLUE_D, 0);
    centred_note(&g_top, n, 26, back);
    caption(&g_top, 160, back ? "Back side" : "Front side");
    canvas_clear(&g_bot, C_NAVY1);
    ui_button(&g_bot, 4, 4, 122, 26, "European culture", n->note_theme == NOTE_CULTURE ? BTN_SELECTED : BTN_NORMAL, &font_small);
    ui_button(&g_bot, 130, 4, 122, 26, "Rivers and birds", n->note_theme == NOTE_BIRDS ? BTN_SELECTED : BTN_NORMAL, &font_small);
    ui_panel(&g_bot, 4, 34, 248, 58, false);
    char a[160], b[160];
    motif_lines(n, a, b, sizeof a);
    ui_text_wrapped(&g_bot, &font_small, 10, 38, 236, a, C_TEXT, 0);
    ui_text_wrapped(&g_bot, &font_small, 10, 64, 236, b, C_TEXT, 0);
    for (int i = 0; i < NOTE_DENOMS; i++) {
        char v[16];
        snprintf(v, sizeof v, T("€%d"), note_values[i]);
        ui_button(&g_bot, 4 + i * 41, 98, 39, 26, v, i == n->note_denom ? BTN_SELECTED : BTN_NORMAL, &font_small);
    }
    ui_button(&g_bot, 4, 130, 122, 26, "Turn over", BTN_NORMAL, &font_small);
    ui_button(&g_bot, 130, 130, 122, 26, "New portrait", BTN_NORMAL, &font_small);
    ui_button(&g_bot, 4, 162, 248, 26, "Print the specimen", BTN_GREEN, &font_main);
}

// 1 = print, 0 = back to the portrait
static int design(SaveExtra *n)
{
    bool back = false, dirty = true;
    while (1) {
        if (dirty) {
            design_screen(n, back);
            dirty = false;
        }
        frame_wait();
        int theme = n->note_theme, dn = n->note_denom;
        if (touch_released_in(4, 4, 122, 26)) theme = NOTE_CULTURE;
        if (touch_released_in(130, 4, 122, 26)) theme = NOTE_BIRDS;
        if (g_kdown & (KEY_UP | KEY_DOWN)) theme = !theme;
        for (int i = 0; i < NOTE_DENOMS; i++)
            if (touch_released_in(4 + i * 41, 98, 39, 26))
                dn = i;
        if (g_krep & KEY_LEFT) dn = (dn + NOTE_DENOMS - 1) % NOTE_DENOMS;
        if (g_krep & KEY_RIGHT) dn = (dn + 1) % NOTE_DENOMS;
        if (theme != n->note_theme || dn != n->note_denom) {
            n->note_theme = theme;
            n->note_denom = dn;
            sfx_play(SFX_CURSOR);
            dirty = true;
        }
        if (touch_released_in(4, 130, 122, 26) || (g_kdown & (KEY_L | KEY_R))) {
            back = !back;
            sfx_play(SFX_PAPER);
            dirty = true;
        }
        if (touch_released_in(130, 130, 122, 26) || (g_kdown & KEY_B)) {
            sfx_play(SFX_CANCEL);
            return 0;
        }
        if (touch_released_in(4, 162, 248, 26) || (g_kdown & (KEY_A | KEY_START))) {
            sfx_play(SFX_SELECT);
            return 1;
        }
    }
}

// The press: the note appears line by line on the top screen, then the SPECIMEN stamp falls.
static void print_animation(const SaveExtra *n)
{
    Canvas off = {malloc(256 * 192), NULL, 0, 0};
    if (!off.px)
        return;
    memset(off.px, C_NAVY1, 256 * 192);
    centred_note(&off, n, 34, false);
    load_palette(n->note_denom);
    canvas_clear(&g_top, C_NAVY1);
    ui_text_in(&g_top, &font_main, 4, 2, 248, 20, "Printing…", C_GOLD, C_BLUE_D, 0);
    for (int y = 34; y < 34 + 126; y += 3) {
        memcpy(g_top.px + y * 256, off.px + y * 256, 256 * 3);
        canvas_dirty(&g_top, y, y + 3);
        if ((y / 3) % 6 == 0)
            sfx_play(SFX_PAPER);
        frame_wait();
    }
    sfx_play(SFX_STAMP);
    for (int i = 0; i < 30; i++)
        frame_wait();
    free(off.px);
}

bool note_studio(void)
{
    Screens sv;
    screens_take(&sv);
    bool printed = false;
    if (!art_open()) {
        art_close();
        screens_give_back(&sv);
        return false;
    }
    SaveExtra n;
    note_current(&n);
    static u8 face[NOTE_W * NOTE_H / 2];
    while (1) {
        canvas_clear(&g_top, C_NAVY1);
        ui_text_in(&g_top, &font_main, 4, 60, 248, 24, "Your portrait for the specimen", C_GOLD, C_BLUE_D, 0);
        caption(&g_top, 88, photo_available() ? "The DSi camera, the stylus or your official photo."
                                              : "The stylus or your official photo.");
        static const char *const with_camera[4] = {"Take a photo", "Draw my portrait", "Use my official photo", "Cancel"};
        static const char *const without[3] = {"Draw my portrait", "Use my official photo", "Cancel"};
        int c = photo_available() ? dlg_choice(with_camera, 4, true) : dlg_choice(without, 3, true);
        if (c >= 0 && !photo_available())
            c++;
        if (c < 0 || c == 3)
            break;
        bool got = false;
        if (c == 0) {
            int r = photo_capture(face);
            if (r < 0) {
                dlg_notice("The camera cannot be used here. You can draw your portrait instead.");
                c = 1;
            }
            got = r > 0;
            if (got)
                n.note_source = 1;
        }
        if (c == 1) {
            memset(face, 0, sizeof face);
            got = draw_face(face);
            if (got)
                n.note_source = 2;
        }
        if (c == 2) {
            official_face(face);
            n.note_source = 3;
            got = true;
        }
        if (!got)
            continue;
        memcpy(n.note_px, face, sizeof n.note_px);
        if (design(&n)) {
            n.magic = SAVE_EXTRA_MAGIC;
            n.version = SAVE_EXTRA_VERSION;
            n.note_serial = rng_next() % 1000000000u;
            n.note_pad = flag_get(FLAG_ALBUM_DONE) ? 1 : 0;   // gold edition once the jury's album is complete
            g_save_extra = n;
            print_animation(&n);
            if (!bag_count(IT_BILLET_SPECIMEN))
                bag_add(IT_BILLET_SPECIMEN, 1);
            flag_set(FLAG_NOTE_PRINTED, true);
            printed = true;
            break;
        }
    }
    art_close();
    screens_give_back(&sv);
    if (printed)
        note_view();
    return printed;
}

// ---------------------------------------------------------------- epilogue
void note_ending(void)
{
    bool own_art = !art_blob && art_open();
    SaveExtra n;
    note_current(&n);
    load_palette(n.note_denom);
    canvas_clear(&g_top, 0);
    canvas_clear(&g_bot, 0);
    centred_note(&g_top, &n, 30, false);
    bool printed = g_save_extra.magic == SAVE_EXTRA_MAGIC;
    ui_text_wrapped(&g_bot, &font_main, 16, 50, 224,
                    printed ? "Your specimen note joined the collection of the Money Museum in Frankfurt."
                            : "In Frankfurt, the ECB studio is still keeping a blank specimen with your name on it.",
                    C_GOLD, 0);
    for (int i = 0; i < 300 && !(g_kdown & (KEY_A | KEY_START)); i++)
        frame_wait();
    if (own_art)
        art_close();
    canvas_clear(&g_top, 0);
    canvas_clear(&g_bot, 0);
}
