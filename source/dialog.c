#include "dialog.h"
#include "lang.h"
#include "canvas.h"
#include "gfx.h"
#include "input.h"
#include "audio.h"
#include "save.h"
#include "ui.h"
#include "cine.h"
#include "gen/font_data.h"

char g_strvar[10][24];

#define BOX_X 4
#define BOX_Y 134
#define BOX_W 248
#define BOX_H 54
#define TEXT_X 14
#define TEXT_Y 141
#define TEXT_W 228
#define LINES 2

static bool box_open;
static int plate_w; // width of the speaker plate currently drawn (0 = none)
static u8 bot_backup[4][256 * 192];
static int bot_sp;

void ui_bottom_push(void)
{
    if (bot_sp < 4)
        memcpy(bot_backup[bot_sp++], g_bot.px, 256 * 192);
}

void ui_bottom_pop(void)
{
    if (bot_sp > 0) {
        memcpy(g_bot.px, bot_backup[--bot_sp], 256 * 192);
        canvas_dirty(&g_bot, 0, 192);
    }
}

void dlg_expand(const char *in, char *out, int max)
{
    int o = 0;
    while (*in && o < max - 1) {
        if (in[0] == '{') {
            const char *e = strchr(in, '}');
            if (e) {
                char key[8] = {0};
                int kl = MIN((int)(e - in - 1), 7);
                memcpy(key, in + 1, kl);
                char tmp[32] = {0};
                if (!strcmp(key, "P"))
                    snprintf(tmp, sizeof tmp, "%s", g_save.player_name);
                else if (!strcmp(key, "R"))
                    snprintf(tmp, sizeof tmp, "%s", "Oliver");
                else if (!strcmp(key, "M"))
                    snprintf(tmp, sizeof tmp, "%lu", (unsigned long)g_save.money);
                else if (key[0] == 'V' && key[1] >= '0' && key[1] <= '9')
                    snprintf(tmp, sizeof tmp, "%s", g_strvar[key[1] - '0']);
                for (char *t = tmp; *t && o < max - 1; t++)
                    out[o++] = *t;
                in = e + 1;
                continue;
            }
        }
        out[o++] = *in++;
    }
    out[o] = 0;
}

int dlg_voice_for(const char *speaker)
{
    u32 h = 5381;
    for (const char *s = speaker; s && *s; s++)
        h = h * 33 + (u8)*s;
    return (int)(h % 12);
}

// Word-wrap into lines (each line a [start,len) in buffer); \f forces new page (stored as line with len -1)
typedef struct {
    int start, len;
    bool page_break;
} Line;

static int wrap(const char *t, Line *lines, int maxl)
{
    int n = 0;
    int i = 0;
    int len = strlen(t);
    while (i < len && n < maxl) {
        int line_start = i;
        int last_space = -1;
        int w = 0;
        bool pb = false;
        int j = i;
        while (j < len) {
            if (t[j] == '\n')
                break;
            if (t[j] == '\f') {
                pb = true;
                break;
            }
            const char *p = t + j;
            u32 c = utf8_next(&p);
            const FontGlyph *g = font_glyph(&font_main, c);
            int cw = g ? g->adv : 0;
            if (w + cw > TEXT_W && last_space >= 0) {
                j = last_space;
                break;
            }
            if (c == ' ')
                last_space = j;
            w += cw;
            j = p - t;
        }
        lines[n].start = line_start;
        lines[n].len = j - line_start;
        lines[n].page_break = pb;
        n++;
        i = j;
        if (i < len && (t[i] == '\n' || t[i] == '\f' || t[i] == ' '))
            i++;
    }
    return n;
}

static void draw_box(const char *speaker)
{
    // only erase what the box owns, so battle infoboxes just above stay intact
    if (plate_w)
        canvas_rect(&g_top, BOX_X + 6, BOX_Y - 15, plate_w + 2, 17, 0);
    plate_w = 0;
    canvas_rect(&g_top, 0, BOX_Y, 256, BOX_H + 4, 0);
    cine_letterbox();
    canvas_frame(&g_top, BOX_X, BOX_Y, BOX_W, BOX_H, FRAME_DIALOG);
    if (speaker && speaker[0]) {
        int w = font_width(&font_small, speaker) + 16;
        plate_w = w;
        ui_panel(&g_top, BOX_X + 6, BOX_Y - 15, w, 17, true);
        ui_text_in(&g_top, &font_small, BOX_X + 6, BOX_Y - 15, w, 17, speaker, C_GOLD, C_INK, 0);
    }
    box_open = true;
}

static void clear_text(void)
{
    canvas_checker(&g_top, BOX_X + 3, BOX_Y + 3, BOX_W - 7, BOX_H - 8, C_WHITE, C_CHECK, 1);
    canvas_dialog_corners(&g_top, BOX_X, BOX_Y, BOX_W, BOX_H);
}

static int text_speed(void)
{
    // characters per frame: slow 1, normal 2, fast 4 (instant handled by key)
    static const int sp[3] = {1, 2, 4};
    return sp[CLAMP(g_save.opt_text_speed, 0, 2)];
}

static void say_impl(const char *speaker, const char *text, bool wait_end)
{
    static char buf[1024];
    static Line lines[48];
    static char who[48];
    if (cine_skipping())
        return;
    text = tr(text);
    if (speaker) {
        dlg_expand(tr(speaker), who, sizeof who);
        speaker = who;
    }
    dlg_expand(text, buf, sizeof(buf));
    int nl = wrap(buf, lines, 48);
    draw_box(speaker);
    int voice = dlg_voice_for(speaker);
    int li = 0;
    while (li < nl) {
        clear_text();
        int page_lines = 0;
        bool skip = false;
        while (page_lines < LINES && li < nl) {
            Line *L = &lines[li];
            int y = TEXT_Y + page_lines * 18;
            int shown = 0;
            int nchars = 0, last_blip = -3;
            while (shown < L->len) {
                // advance by N characters (UTF-8 aware)
                int step = skip ? 9999 : text_speed();
                for (int k = 0; k < step && shown < L->len; k++) {
                    const char *p = buf + L->start + shown;
                    utf8_next(&p);
                    shown = p - (buf + L->start);
                    nchars++;
                }
                canvas_checker(&g_top, TEXT_X - 1, y, TEXT_W + 2, 17, C_WHITE, C_CHECK, 1);
                canvas_text_n(&g_top, &font_main, TEXT_X, y, buf + L->start, shown, C_TEXT, C_SHADOW);
                if (!skip) {
                    // typing sound (option, on by default): a short blip every few letters
                    if (!g_save.opt_text_mute && nchars - last_blip >= 3 && buf[L->start + shown - 1] != ' ') {
                        sfx_voice(speaker && speaker[0] ? voice : 6);
                        last_blip = nchars;
                    }
                    frame_wait();
                    if (g_kdown & (KEY_A | KEY_B) || g_touch_down || cine_skipping())
                        skip = true;
                }
            }
            page_lines++;
            bool pb = L->page_break;
            li++;
            if (pb)
                break;
        }
        bool last = li >= nl;
        if (last && !wait_end)
            break;
#ifdef WEBSITE_CAPTURE
        extern volatile u32 g_site_capture[8];
        g_site_capture[4]++;
        DC_FlushRange((void *)g_site_capture, 32);
#endif
        // wait for key with blinking arrow
        int t = 0;
        frame_wait();
        while (1) {
            bool on = (t / 16) % 2 == 0;
            canvas_checker(&g_top, BOX_X + BOX_W - 18, BOX_Y + BOX_H - 14, 10, 8, C_WHITE, C_CHECK, 1);
            if (on)
                canvas_text(&g_top, &font_small, BOX_X + BOX_W - 17, BOX_Y + BOX_H - 17, "\xee\x80\x81", C_RED, 0);
            frame_wait();
            t++;
            if (input_confirm() || cine_skipping())
                break;
        }
        sfx_play(SFX_BLIP);
    }
}

void dlg_say(const char *speaker, const char *text)
{
    say_impl(speaker, text, true);
}

void dlg_say_nowait(const char *speaker, const char *text)
{
    say_impl(speaker, text, false);
}

void dlg_close(void)
{
    if (!box_open)
        return;
    if (plate_w)
        canvas_rect(&g_top, BOX_X + 6, BOX_Y - 15, plate_w + 2, 17, 0);
    plate_w = 0;
    canvas_rect(&g_top, 0, BOX_Y, 256, BOX_H + 4, 0);
    cine_letterbox();
    box_open = false;
}

bool dlg_is_open(void) { return box_open; }

// A plain list with a cursor (▶) on the left of the selected line, like the classic handheld RPGs.
#define ROW_H 20
static void choice_draw(char opts[][96], int n, int x, int y, int w, int sel, int bob)
{
    for (int i = 0; i < n; i++) {
        int ry = y + 7 + i * ROW_H;
        canvas_rect(&g_bot, x + 4, ry, w - 9, ROW_H, C_WHITE);
        if (i == sel)
            canvas_rect(&g_bot, x + 6, ry + 1, w - 13, ROW_H - 2, C_BTN_HI);
        if (i == sel)
            canvas_text(&g_bot, &font_small, x + 10 + bob, ry + 3, "▶", C_RED, 0);
        ui_text_in(&g_bot, &font_main, x + 22, ry, w - 30, ROW_H, opts[i], i == sel ? C_INK : C_TEXT,
                   C_SHADOW, -1);
    }
}

int dlg_choice(const char *const *options, int n, bool allow_cancel)
{
    ui_bottom_push();
    static char opts[8][96];
    n = MIN(n, 8);
    int w = 120;
    for (int i = 0; i < n; i++) {
        dlg_expand(tr(options[i]), opts[i], sizeof opts[i]);
        w = MAX(w, font_width(&font_main, opts[i]) + 44);
    }
    w = MIN(w, 240);
    int h = n * ROW_H + 14;
    int x = (256 - w) / 2, y = (192 - h) / 2;
    int sel = 0, result = -1, t = 0;
    ui_backdrop(&g_bot);
    canvas_frame(&g_bot, x - 2, y - 2, w + 4, h + 4, FRAME_DIALOG);
    choice_draw(opts, n, x, y, w, sel, 0);
    while (1) {
        frame_wait();
        t++;
        int old = sel;
        if (g_krep & KEY_UP)
            sel = (sel + n - 1) % n;
        if (g_krep & KEY_DOWN)
            sel = (sel + 1) % n;
        if (sel != old)
            sfx_play(SFX_CURSOR);
        if (g_kdown & KEY_A)
            result = sel;
        for (int i = 0; i < n; i++)
            if (touch_in(x, y + 7 + i * ROW_H, w, ROW_H))
                result = sel = i;
        if (allow_cancel && (g_kdown & KEY_B)) {
            sfx_play(SFX_CANCEL);
            result = -1;
            goto done;
        }
        if (sel != old || (t % 16) == 0 || result >= 0)
            choice_draw(opts, n, x, y, w, sel, result >= 0 ? 2 : (t / 16) & 1);
        if (result >= 0) {
            for (int k = 0; k < 6; k++)
                frame_wait();
            break;
        }
    }
    sfx_play(SFX_SELECT);
done:
    ui_bottom_pop();
    return result;
}

bool dlg_yesno(void)
{
    static const char *const yn[2] = {"Yes", "No"};
    return dlg_choice(yn, 2, true) == 0;
}

void dlg_notice(const char *text)
{
    ui_bottom_push();
    char tmp[256];
    dlg_expand(tr(text), tmp, sizeof tmp);
    ui_backdrop(&g_bot);
    ui_panel(&g_bot, 12, 52, 232, 88, false);
    ui_text_wrapped(&g_bot, &font_main, 22, 62, 212, tmp, C_TEXT, C_SHADOW);
    ui_text_in(&g_bot, &font_small, 12, 120, 232, 16, "Tap or press A", C_MGREY, 0, 0);
    frame_wait();
    while (!input_confirm())
        frame_wait();
    sfx_play(SFX_BLIP);
    ui_bottom_pop();
}
