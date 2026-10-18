#include "sprite.h"
#include "fs.h"

void spr_ext_pal(bool sub, int slot, const u16 *pal, int count)
{
    if (sub) {
        vramSetBankI(VRAM_I_LCD);
        u16 *dst = VRAM_I_EXT_SPR_PALETTE[slot];
        for (int i = 0; i < count; i++)
            dst[i] = pal[i];
        vramSetBankI(VRAM_I_SUB_SPRITE_EXT_PALETTE);
    } else {
        vramSetBankF(VRAM_F_LCD);
        u16 *dst = VRAM_F_EXT_SPR_PALETTE[slot];
        for (int i = 0; i < count; i++)
            dst[i] = pal[i];
        vramSetBankF(VRAM_F_SPRITE_EXT_PALETTE);
    }
}

void spr_pal16(bool sub, int bank, const u16 *pal)
{
    u16 *dst = (sub ? SPRITE_PALETTE_SUB : SPRITE_PALETTE) + bank * 16;
    for (int i = 0; i < 16; i++)
        dst[i] = pal[i];
}

u16 *spr_alloc(bool sub, SpriteSize size, SpriteColorFormat fmt)
{
    u16 *p = oamAllocateGfx(sub ? &oamSub : &oamMain, size, fmt);
    if (!p)
        fatal("Sprite VRAM full (%s)", sub ? "sub" : "main");
    return p;
}

void spr_free(bool sub, u16 *gfx)
{
    if (gfx)
        oamFreeGfx(sub ? &oamSub : &oamMain, gfx);
}

void spr_upload(u16 *dst, const void *src, u32 bytes)
{
    // DMA cannot see dirty ARM9 cache lines or buffers on the DTCM stack.
    // BIOS CPU copy sees both and uses halfword stores, as sprite VRAM requires.
    swiCopy(src, dst, (bytes / sizeof(u16)) | COPY_MODE_HWORD);
}

void spr_set(bool sub, int id, int x, int y, SpriteSize size, SpriteColorFormat fmt, u16 *gfx,
             int palette, int priority, bool hflip)
{
    OamState *o = sub ? &oamSub : &oamMain;
    bool hide = x <= -64 || x >= 256 || y <= -64 || y >= 192;
    oamSet(o, id, x & 511, y & 255, priority, palette, size, fmt, gfx, -1, false, hide, hflip, false, false);
}

void spr_hide(bool sub, int id)
{
    oamClearSprite(sub ? &oamSub : &oamMain, id);
}

void spr_hide_range(bool sub, int from, int to)
{
    for (int i = from; i <= to; i++)
        spr_hide(sub, i);
}

void spr_move(bool sub, int id, int x, int y)
{
    OamState *o = sub ? &oamSub : &oamMain;
    bool hide = x <= -64 || x >= 256 || y <= -64 || y >= 192;
    oamSetXY(o, id, x & 511, y & 255);
    oamSetHidden(o, id, hide);
}

// .spr format: "SPR" ver(1) bpp fw fh pad | u16 nframes | u16 ncolors | pal[ncolors] | frames
bool sheet_load(SpriteSheet *s, const char *path)
{
    memset(s, 0, sizeof(*s));
    u32 size;
    u8 *d = fs_try_load(path, &size);
    if (!d)
        return false;
    if (d[0] != 'S' || d[1] != 'P' || d[2] != 'R') {
        free(d);
        return false;
    }
    s->bpp = d[4];
    s->fw = d[5];
    s->fh = d[6];
    s->extra = d[7];
    s->nframes = d[8] | (d[9] << 8);
    s->ncolors = d[10] | (d[11] << 8);
    const u8 *p = d + 12;
    for (int i = 0; i < s->ncolors && i < 256; i++)
        s->pal[i] = p[i * 2] | (p[i * 2 + 1] << 8);
    p += s->ncolors * 2;
    s->frame_bytes = (u32)s->fw * s->fh * s->bpp / 8;
    u32 total = s->frame_bytes * s->nframes;
    s->data = malloc(total);
    if (!s->data)
        fatal("OOM sheet %s", path);
    memcpy(s->data, p, total);
    free(d);
    return true;
}

void sheet_free(SpriteSheet *s)
{
    if (s->data)
        free(s->data);
    s->data = NULL;
}

const u8 *sheet_frame(const SpriteSheet *s, int frame)
{
    if (frame < 0 || frame >= s->nframes)
        frame = 0;
    return s->data + s->frame_bytes * frame;
}

SpriteSize sprite_size_for(int w, int h)
{
    if (w == h) {
        if (w == 8) return SpriteSize_8x8;
        if (w == 16) return SpriteSize_16x16;
        if (w == 32) return SpriteSize_32x32;
        return SpriteSize_64x64;
    }
    if (w > h) {
        if (w == 16) return SpriteSize_16x8;
        if (w == 32 && h == 8) return SpriteSize_32x8;
        if (w == 32) return SpriteSize_32x16;
        return SpriteSize_64x32;
    }
    if (h == 16) return SpriteSize_8x16;
    if (h == 32 && w == 8) return SpriteSize_8x32;
    if (h == 32) return SpriteSize_16x32;
    return SpriteSize_32x64;
}
