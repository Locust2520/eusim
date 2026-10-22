// DSi camera: live greyscale preview with an oval guide on the bottom screen, the engraved result on the top.
// Uses libnds' camera driver (the default ARM7 core installs the camera FIFO handler in DSi mode).
#include "photo.h"
#include "note_render.h"
#include "canvas.h"
#include "gfx.h"
#include "ui.h"
#include "input.h"
#include "audio.h"
#include "save.h"
#include "gen/font_data.h"

#define CAM_NDMA 1
#define OVAL_X 80
#define OVAL_Y 34
#define OVAL_W 96
#define OVAL_H 120

static u16 *frame_buf;

bool photo_available(void)
{
    return isDSiMode();
}

static bool frame_done(void)
{
    return !ndmaBusy(CAM_NDMA) && !cameraTransferActive();
}

// Waits for the transfer started on the previous frame (bounded: a stalled camera must not freeze the game).
static bool grab(void)
{
    for (int i = 0; i < 20 && !frame_done(); i++)
        frame_wait();
    if (!frame_done()) {
        cameraStopTransfer();
        return false;
    }
    cameraStopTransfer();
    DC_InvalidateRange(frame_buf, 256 * 192 * 2);
    return true;
}

static int lum(u16 p)
{
    return ((p & 31) * 77 + ((p >> 5) & 31) * 150 + ((p >> 10) & 31) * 29) >> 8;   // 0..31
}

static bool in_oval(int x, int y)
{
    int dx = (x - OVAL_X) * 2 - OVAL_W, dy = (y - OVAL_Y) * 2 - OVAL_H;
    return dx * dx * 100 / (OVAL_W * OVAL_W) + dy * dy * 100 / (OVAL_H * OVAL_H) <= 100;
}

static void draw_preview(bool mirror)
{
    for (int y = 0; y < 192; y++) {
        u8 *row = g_bot.px + y * 256;
        const u16 *src = frame_buf + y * 256;
        for (int x = 0; x < 256; x++) {
            int v = lum(src[mirror ? 255 - x : x]);
            row[x] = NOTE_GREY + 15 - v / 2;
        }
    }
    for (int k = 0; k < 96; k++) {   // dashed oval guide
        if (k & 1)
            continue;
        int a = k * 65536 / 96;
        int x = OVAL_X + OVAL_W / 2 + (cosLerp(a) * (OVAL_W / 2) >> 12);
        int y = OVAL_Y + OVAL_H / 2 + (sinLerp(a) * (OVAL_H / 2) >> 12);
        canvas_rect(&g_bot, x - 1, y - 1, 3, 3, C_GOLD);
    }
    canvas_dirty(&g_bot, 0, 192);
}

// Crops the oval, scales it to NOTE_W x NOTE_H and stretches the contrast (2 % / 98 % of the face's tones).
static void to_face(u8 *px4, bool mirror)
{
    static u8 g[NOTE_W * NOTE_H];
    int hist[32] = {0}, n = 0;
    for (int y = 0; y < NOTE_H; y++)
        for (int x = 0; x < NOTE_W; x++) {
            int sx0 = OVAL_X + x * OVAL_W / NOTE_W, sx1 = OVAL_X + (x + 1) * OVAL_W / NOTE_W;
            int sy0 = OVAL_Y + y * OVAL_H / NOTE_H, sy1 = OVAL_Y + (y + 1) * OVAL_H / NOTE_H;
            int sum = 0, cnt = 0;
            for (int sy = sy0; sy < MAX(sy1, sy0 + 1); sy++)
                for (int sx = sx0; sx < MAX(sx1, sx0 + 1); sx++) {
                    sum += lum(frame_buf[sy * 256 + (mirror ? 255 - sx : sx)]);
                    cnt++;
                }
            int v = sum / cnt;
            g[y * NOTE_W + x] = v;
            if (in_oval(sx0, sy0)) {
                hist[v]++;
                n++;
            }
        }
    int lo = 0, hi = 31, acc = 0;
    while (lo < 31 && (acc += hist[lo]) < n / 50)
        lo++;
    acc = 0;
    while (hi > 0 && (acc += hist[hi]) < n / 50)
        hi--;
    if (hi <= lo)
        hi = lo + 1;
    memset(px4, 0, NOTE_W * NOTE_H / 2);
    for (int i = 0; i < NOTE_W * NOTE_H; i++) {
        int d = 15 - CLAMP((g[i] - lo) * 15 / (hi - lo), 0, 15);
        px4[i / 2] |= (i & 1) ? d << 4 : d;
    }
}

static void top_text(const char *a, const char *b)
{
    canvas_clear(&g_top, C_NAVY1);
    ui_text_in(&g_top, &font_main, 8, 4, 240, 20, a, C_WHITE, C_BLUE_D, 0);
    ui_text_in(&g_top, &font_small, 8, 24, 240, 14, b, C_PANEL, 0, 0);
}

int photo_capture(u8 *px4)
{
    if (!isDSiMode())
        return -1;
    frame_buf = malloc(256 * 192 * 2);
    if (!frame_buf)
        return -1;
    top_text("Starting the camera…", "");
    frame_wait();
    if (!cameraInit()) {
        free(frame_buf);
        return -1;
    }
    u16 pal[NOTE_PAL_N];
    note_palette(pal, 0);
    gfx_bg_pal(false, NOTE_PAL, pal, NOTE_PAL_N);
    gfx_bg_pal(true, NOTE_PAL, pal, NOTE_PAL_N);
    CameraDevice cam = CAMERA_INNER;
    int result = -1;
    bool ok = cameraSelect(cam) && cameraStartTransfer(frame_buf, MCUREG_APT_SEQ_CMD_PREVIEW, CAM_NDMA);
    top_text("Fit your face in the oval", "A or tap: take the photo · L/R: other camera · B: back");
    int failures = 0;
    while (ok) {
        if (!grab()) {
            if (++failures > 3)
                break;   // the camera stopped answering: drawing instead
        } else {
            failures = 0;
            draw_preview(cam == CAMERA_INNER);
        }
        if (g_kdown & KEY_B) {
            sfx_play(SFX_CANCEL);
            result = 0;
            break;
        }
        if (g_kdown & (KEY_L | KEY_R | KEY_X)) {
            cam = cam == CAMERA_INNER ? CAMERA_OUTER : CAMERA_INNER;
            sfx_play(SFX_CURSOR);
            if (!cameraSelect(cam))
                break;
        } else if ((g_kdown & KEY_A) || g_touch_down) {
            sfx_play(SFX_STAMP);
            to_face(px4, cam == CAMERA_INNER);
            canvas_clear(&g_top, C_NAVY1);
            note_engrave_face(&g_top, 64, 24, px4, 2);
            ui_text_in(&g_top, &font_main, 8, 2, 240, 20, "Engraving test", C_WHITE, C_BLUE_D, 0);
            ui_button(&g_bot, 16, 150, 104, 32, "Retake", BTN_NORMAL, &font_main);
            ui_button(&g_bot, 136, 150, 104, 32, "Keep", BTN_GREEN, &font_main);
            int choice = -1;
            while (choice < 0) {
                frame_wait();
                if ((g_kdown & KEY_A) || touch_released_in(136, 150, 104, 32))
                    choice = 1;
                if ((g_kdown & KEY_B) || touch_released_in(16, 150, 104, 32))
                    choice = 0;
            }
            sfx_play(choice ? SFX_SELECT : SFX_CANCEL);
            if (choice) {
                result = 1;
                break;
            }
            top_text("Fit your face in the oval", "A or tap: take the photo · L/R: other camera · B: back");
        }
        cameraStartTransfer(frame_buf, MCUREG_APT_SEQ_CMD_PREVIEW, CAM_NDMA);
        frame_wait();
    }
    for (int i = 0; i < 20 && !frame_done(); i++)
        frame_wait();
    cameraStopTransfer();
    cameraDeinit();
    free(frame_buf);
    frame_buf = NULL;
    canvas_clear(&g_bot, 0);
    canvas_clear(&g_top, 0);
    return result;
}
