#include "common.h"
#include "gfx.h"
#include "canvas.h"
#include "input.h"
#include "fs.h"
#include "audio.h"
#include "game.h"
#include "portrait.h"
#include "save.h"
#include "browser_save.h"
#include "multiplayer.h"
#include "script.h"
#include "gen/font_data.h"
#include <stdarg.h>

u32 g_frame;
static u32 rng_state = 0x12345678;

u32 rng_next(void)
{
    u32 x = rng_state;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    rng_state = x;
    return x;
}

int rng_range(int n)
{
    if (n <= 1)
        return 0;
    return (int)((rng_next() >> 8) % (u32)n);
}

void rng_seed(u32 s)
{
    rng_state = s ? s : 0x9E3779B9;
}

static FrameHook hooks[8];
volatile u32 g_vbl_count;

void frame_hook_add(FrameHook fn)
{
    for (int i = 0; i < 8; i++)
        if (hooks[i] == fn)
            return;
    for (int i = 0; i < 8; i++)
        if (!hooks[i]) {
            hooks[i] = fn;
            return;
        }
}

void frame_hook_remove(FrameHook fn)
{
    for (int i = 0; i < 8; i++)
        if (hooks[i] == fn)
            hooks[i] = NULL;
}

void frame_wait(void)
{
    for (int i = 0; i < 8; i++)
        if (hooks[i])
            hooks[i]();
    cothread_yield_irq(IRQ_VBLANK);
    // The music/SFX sequencer runs here, on the main thread, once per elapsed VBlank. It used to run in the
    // VBlank interrupt, but soundPlay*() waits for the ARM7's answer on the FIFO: on hardware, an interrupt
    // arriving while the ARM7 is busy with the SD card (slide/portrait loading) re-entered it and deadlocked
    // the game with the last note held.
    {
        static u32 last;
        u32 now = g_vbl_count, n = now - last;
        last = now;
        if (n > 4)
            n = 1; // after a long load: resume, don't fast-forward
        while (n--)
            audio_tick();
    }
    canvas_flush(&g_top);
    canvas_flush(&g_bot);
    oamUpdate(&oamMain);
    oamUpdate(&oamSub);
    bgUpdate();
    input_update();
    g_frame++;
    rng_next();
}

void fatal(const char *fmt, ...)
{
    char buf[256];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);
    gfx_brightness(false, 0);
    gfx_brightness(true, 0);
    canvas_clear(&g_bot, C_RED_D);
    canvas_text(&g_bot, &font_small, 4, 4, "ERREUR FATALE", C_WHITE, 0);
    canvas_text(&g_bot, &font_small, 4, 20, buf, C_WHITE, 0);
    while (1) {
        swiWaitForVBlank();
        canvas_flush(&g_bot);
    }
}

static void vblank_irq(void)
{
    g_vbl_count++;
}

int main(int argc, char **argv)
{
    g_rom_path = (argc > 0 && argv && argv[0]) ? argv[0] : NULL;
    defaultExceptionHandler();
    gfx_brightness(false, -16);
    gfx_brightness(true, -16);
    gfx_init();
    soundEnable();
    audio_init();
    irqSet(IRQ_VBLANK, vblank_irq);
    irqEnable(IRQ_VBLANK);
    if (!fs_init())
        fatal("NitroFS introuvable.\nLancez la ROM depuis une carte\nou un émulateur récent.");
    script_init();
    save_new_game();
    frame_hook_add(portrait_update);
    browser_save_init();
    multiplayer_init();
    game_main();
    return 0;
}
