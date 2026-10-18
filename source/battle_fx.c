// Battle visual effects: procedural 16x16 particle sprites, one per type, plus the "tampon" ball.
#include "battle_fx.h"
#include "sprite.h"
#include "gfx.h"
#include "audio.h"

#define FX_OAM (OAM_BATTLE + 2)
#define FX_N 12
#define NSHAPES 20

static u16 *shape_gfx[NSHAPES];
static bool ready;
static int ball_x, ball_y, ball_t, ball_shake;
static bool ball_on;

// palette (ext slot PAL_BATTLE_FX)
static const u16 fx_pal[32] = {
    0, RGB8(168, 168, 152), RGB8(64, 104, 224), RGB8(176, 64, 48), RGB8(240, 192, 32), RGB8(232, 72, 88),
    RGB8(80, 184, 72), RGB8(136, 104, 72), RGB8(248, 136, 32), RGB8(112, 88, 176), RGB8(216, 176, 64),
    RGB8(152, 192, 64), RGB8(64, 192, 216), RGB8(96, 160, 160), RGB8(48, 48, 64), RGB8(232, 104, 168),
    RGB8(120, 96, 160), RGB8(255, 255, 255), RGB8(24, 24, 32), RGB8(255, 204, 0), RGB8(160, 88, 40),
    RGB8(200, 40, 40), RGB8(255, 240, 160), 0};

// 16x16 shapes: '.'=0, 'c' = type colour, 'w' white, 'k' black, 'g' gold, 'b' brown, 'r' red, 'y' light
static const char *const shapes[NSHAPES][16] = {
    // 0 TECHNO: sheet of paper
    {"................", "...kkkkkkkk.....", "...kwwwwwwkk....", "...kwccccwwkk...", "...kwwwwwwwwk...",
     "...kwccccccwk...", "...kwwwwwwwwk...", "...kwcccccwwk...", "...kwwwwwwwwk...", "...kwccccccwk...",
     "...kwwwwwwwwk...", "...kkkkkkkkkk...", "................", "................", "................", "................"},
    // 1 FEDERAL: star
    {".......kk.......", "......kggk......", "......kggk......", ".....kgggk......", "kkkkkkggggkkkkk.",
     ".kggggggggggggk.", "..kggggggggggk..", "...kggggggggk...", "....kgggggggk...", "...kgggkkgggk...",
     "..kgggk..kgggk..", "..kggk....kggk..", "..kkk......kkk..", "................", "................", "................"},
    // 2 SOUVERAIN: shield
    {"................", "..kkkkkkkkkkk...", "..kcccccccccck..", "..kcwwccccccck..", "..kcwcccccccck..",
     "..kcccccccccck..", "..kcccccccccck..", "...kccccccccck..", "...kcccccccck...", "....kccccccck...",
     ".....kcccccck...", "......kcccck....", ".......kkkk.....", "................", "................", "................"},
    // 3 generic orb (LIBERAL, SOCIAL...)
    {"................", ".....kkkkkk.....", "...kkccccccckk..", "..kcwwcccccccck.", "..kcwccccccccck.",
     ".kcccccccccccccc", ".kcccccccccccccc", ".kcccccccccccccc", ".kcccccccccccccc", "..kcccccccccck..",
     "..kcccccccccck..", "...kkcccccckk...", ".....kkkkkk.....", "................", "................", "................"},
    // 4 VERT: leaf
    {"................", "..........kkkk..", ".......kkkccck..", ".....kkccccwck..", "....kcccccwcck..",
     "...kccccwcccck..", "...kcccwcccck...", "..kcccwcccck....", "..kccwcccck.....", "..kcwcckkk......",
     ".kkwkkk.........", "kk..............", "................", "................", "................", "................"},
    // 5 INDUSTRIE: gear
    {"................", "......kkkk......", "...kk.kcck.kk...", "..kcckkcckkcck..", "..kccccccccccck.",
     "...kccckkkccck..", ".kkcck....kcckk.", ".kccck....kccck.", ".kkcck....kcckk.", "...kccckkkccck..",
     "..kccccccccccck.", "..kcckkcckkcck..", "...kk.kcck.kk...", "......kkkk......", "................", "................"},
    // 6 ENERGIE: bolt
    {"........kkkk....", ".......kgggk....", "......kgggk.....", ".....kgggk......", "....kggggkkkk...",
     "...kggggggggk...", "...kkkkgggggk...", "......kgggk.....", ".....kgggk......", "....kggk........",
     "...kgk..........", "...kk...........", "................", "................", "................", "................"},
    // 7 JURIDIQUE: gavel
    {"................", "...kkkkkk.......", "..kbbbbbbk......", "..kbbbbbbk......", "..kbbbbbbk......",
     "...kkkbkkk......", "......kbk.......", ".......kbk......", "........kbk.....", ".........kbk....",
     "..........kbk...", "...........kk...", "................", "................", "................", "................"},
    // 8 MONETAIRE: coin
    {"................", ".....kkkkkk.....", "...kkggggggkk...", "..kggyyyyyyggk..", "..kgygggggygk...",
     ".kgyggkkggyggk..", ".kgyggkgggyggk..", ".kgygkkkkgyggk..", ".kgyggkgggyggk..", "..kgyggkkgygk...",
     "..kggyyyyyyggk..", "...kkggggggkk...", ".....kkkkkk.....", "................", "................", "................"},
    // 9 AGRICOLE: wheat
    {".......k........", "......kgk.......", ".....kgkgk......", "......kgk.......", ".....kgkgk......",
     "......kgk.......", ".....kgkgk......", "......kgk.......", ".......k........", ".......k........",
     ".......k........", ".......k........", "................", "................", "................", "................"},
    // 10 NUMERIQUE: pixel block
    {"................", "..kkkk..kkkk....", "..kcck..kwwk....", "..kcck..kwwk....", "..kkkk..kkkk....",
     "................", "..kkkk..kkkk....", "..kwwk..kcck....", "..kwwk..kcck....", "..kkkk..kkkk....",
     "................", "................", "................", "................", "................", "................"},
    // 11 DIPLO: dove
    {"................", "........kkk.....", ".......kwwwk....", "..kk..kwwwkk....", ".kwwkkwwwwk.....",
     "..kwwwwwwwwkk...", "...kwwwwwwwwwk..", "....kkwwwwwkk...", "......kkkkk.....", "................",
     "................", "................", "................", "................", "................", "................"},
    // 12 LOBBY: briefcase
    {"................", "......kkkk......", ".....k....k.....", "..kkkkkkkkkkkk..", "..kccccccccccck.",
     "..kccccccccccck.", "..kkkkkggkkkkkk.", "..kccccccccccck.", "..kccccccccccck.", "..kccccccccccck.",
     "..kkkkkkkkkkkkk.", "................", "................", "................", "................", "................"},
    // 13 POPULISTE: megaphone
    {"................", "...........kk...", ".........kkck...", ".......kkccck...", "..kkkkkccccck...",
     "..kwwkcccccck...", "..kwwkcccccck...", "..kkkkkccccck...", "....kk.kkccck...", "....kk...kkck...",
     "...........kk...", "................", "................", "................", "................", "................"},
    // 14 FANTOME: ghost
    {"................", ".....kkkkkk.....", "....kwwwwwwk....", "...kwwwwwwwwk...", "...kwkkwwkkwk...",
     "...kwkkwwkkwk...", "...kwwwwwwwwk...", "...kwwwkkwwwk...", "...kwwwwwwwwk...", "...kwwwwwwwwk...",
     "...kwkwwkwwkk...", "...kk.kk.kk.....", "................", "................", "................", "................"},
    // 15 hit spark
    {"................", "......k.k.......", "..k...kgk...k...", "...k..kgk..k....", "....k.kgk.k.....",
     ".....kgggk......", "kkkkggwwwggkkkk.", ".....kgggk......", "....k.kgk.k.....", "...k..kgk..k....",
     "..k...kgk...k...", "......k.k.......", "................", "................", "................", "................"},
    // 16 tampon ball
    {"................", ".....kkkkkk.....", "....kbbbbbbk....", "....kbbbbbbk....", ".....kbbbbk.....",
     "......kbbk......", "...kkkkkkkkkk...", "..kccccccccccck.", "..kccccccccccck.", "..kkkkkkkkkkkkk.",
     "..krrrrrrrrrrrk.", "...kkkkkkkkkkk..", "................", "................", "................", "................"},
    // 17 arrow up
    {"................", ".......kk.......", "......kwwk......", ".....kwwwwk.....", "....kwwwwwwk....",
     "...kkkwwwwkkk...", ".....kwwwwk.....", ".....kwwwwk.....", ".....kwwwwk.....", ".....kkkkkk.....",
     "................", "................", "................", "................", "................", "................"},
    // 18 arrow down
    {"................", ".....kkkkkk.....", ".....kwwwwk.....", ".....kwwwwk.....", ".....kwwwwk.....",
     "...kkkwwwwkkk...", "....kwwwwwwk....", ".....kwwwwk.....", "......kwwk......", ".......kk.......",
     "................", "................", "................", "................", "................", "................"},
    // 19 small star
    {"................", "................", ".......k........", "......kgk.......", "..kkkkkgkkkkk...",
     "...kgggggggk....", "....kgggggk.....", "...kggkkkggk....", "...kk.....kk....", "................",
     "................", "................", "................", "................", "................", "................"},
};

static const u8 type_shape[16] = {0, 1, 2, 3, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14};

typedef struct {
    bool on;
    int x, y, vx, vy, life, shape, color;
} Particle;
static Particle parts[FX_N];

static void build_shape(int s, int color, u16 *dst)
{
    u8 buf[256];
    memset(buf, 0, sizeof buf);
    for (int y = 0; y < 16; y++)
        for (int x = 0; x < 16; x++) {
            char ch = shapes[s][y][x];
            u8 v = 0;
            switch (ch) {
            case 'c': v = 1 + color; break;
            case 'w': v = 17; break;
            case 'k': v = 18; break;
            case 'g': v = 19; break;
            case 'b': v = 20; break;
            case 'r': v = 21; break;
            case 'y': v = 22; break;
            }
            int t = (y / 8) * 2 + (x / 8);
            buf[t * 64 + (y % 8) * 8 + (x % 8)] = v;
        }
    spr_upload(dst, buf, sizeof buf);
}

static int part_color[FX_N];
static u16 *part_gfx[FX_N];

void fx_init(void)
{
    spr_ext_pal(false, PAL_BATTLE_FX, fx_pal, 32);
    for (int i = 0; i < FX_N; i++) {
        part_gfx[i] = spr_alloc(false, SpriteSize_16x16, SpriteColorFormat_256Color);
        part_color[i] = -1;
        parts[i].on = false;
    }
    shape_gfx[0] = NULL;
    ready = true;
    ball_on = false;
}

void fx_shutdown(void)
{
    if (!ready)
        return;
    for (int i = 0; i < FX_N; i++) {
        oamClearSprite(&oamMain, FX_OAM + i);
        spr_free(false, part_gfx[i]);
    }
    oamClearSprite(&oamMain, FX_OAM + FX_N);
    ready = false;
}

static void set_part(int i, int shape, int color, int x, int y, int vx, int vy, int life)
{
    Particle *p = &parts[i];
    p->on = true;
    p->x = x << 4;
    p->y = y << 4;
    p->vx = vx;
    p->vy = vy;
    p->life = life;
    if (p->shape != shape || part_color[i] != color) {
        build_shape(shape, color, part_gfx[i]);
        p->shape = shape;
        part_color[i] = color;
    }
}

void fx_update(void)
{
    if (!ready)
        return;
    for (int i = 0; i < FX_N; i++) {
        Particle *p = &parts[i];
        if (!p->on) {
            oamSetHidden(&oamMain, FX_OAM + i, true);
            continue;
        }
        p->x += p->vx;
        p->y += p->vy;
        if (--p->life <= 0)
            p->on = false;
        oamSet(&oamMain, FX_OAM + i, (p->x >> 4) - 8, (p->y >> 4) - 8, 0, PAL_BATTLE_FX, SpriteSize_16x16,
               SpriteColorFormat_256Color, part_gfx[i], -1, false, !p->on, false, false, false);
    }
}

static void run(int frames)
{
    for (int i = 0; i < frames; i++) {
        fx_update();
        frame_wait();
    }
}

// attacker 0 = player (bottom left), 1 = foe (top right)
void fx_move(int a, int type, int cat)
{
    if (!ready)
        return;
    int sx = a == 0 ? 60 : 188, sy = a == 0 ? 110 : 50;
    int tx = a == 0 ? 188 : 60, ty = a == 0 ? 50 : 110;
    int shape = type_shape[type & 15];
    if (cat == 2) {
        // status: particles swirl around the user
        for (int i = 0; i < 6; i++) {
            int ang = i * 65536 / 6;
            set_part(i, shape, type, sx + (cosLerp(ang) * 20 >> 12), sy + (sinLerp(ang) * 12 >> 12), 0, -10, 24);
        }
        sfx_play(SFX_STAR);
        run(24);
        return;
    }
    if (cat == 0) {
        // physical: quick dash streak then impact
        for (int i = 0; i < 4; i++)
            set_part(i, shape, type, sx, sy, (tx - sx) * 16 / (10 + i * 2), (ty - sy) * 16 / (10 + i * 2), 10 + i * 2);
        sfx_play(SFX_WHOOSH);
        run(12);
    } else {
        // special: volley of projectiles
        for (int i = 0; i < 6; i++)
            set_part(i, shape, type, sx, sy, (tx - sx) * 16 / 16, (ty - sy) * 16 / 16 + (i - 3) * 4, 16);
        sfx_play(SFX_STAR);
        run(16);
    }
    // impact burst
    for (int i = 0; i < 6; i++) {
        int ang = i * 65536 / 6;
        set_part(6 + i % 6, 15, type, tx, ty, cosLerp(ang) >> 9, sinLerp(ang) >> 9, 10);
    }
    run(6);
}

void fx_status(int target, int status)
{
    if (!ready)
        return;
    int x = target == 0 ? 60 : 188, y = target == 0 ? 110 : 50;
    static const int st_type[6] = {0, 13, 3, 12, 11, 2};
    for (int i = 0; i < 5; i++)
        set_part(i, 3, st_type[status % 6], x - 20 + i * 10, y + 10, 0, -12, 20);
    run(20);
}

void fx_stat(int target, bool up)
{
    if (!ready)
        return;
    int x = target == 0 ? 60 : 188, y = target == 0 ? 110 : 50;
    for (int i = 0; i < 4; i++)
        set_part(i, up ? 17 : 18, 0, x - 18 + i * 12, y + (up ? 16 : -16), 0, up ? -16 : 16, 18);
    run(18);
}

static void ball_draw(int frame_shake)
{
    oamSet(&oamMain, FX_OAM + FX_N - 1, ball_x - 8 + frame_shake, ball_y - 8, 0, PAL_BATTLE_FX, SpriteSize_16x16,
           SpriteColorFormat_256Color, part_gfx[FX_N - 1], -1, false, !ball_on, false, false, false);
}

static void throw_arc(int x0, int y0, int x1, int y1, int frames)
{
    set_part(FX_N - 1, 16, 1, x0, y0, 0, 0, 0);
    parts[FX_N - 1].on = false;
    ball_on = true;
    sfx_play(SFX_THROW);
    for (int i = 0; i <= frames; i++) {
        ball_x = x0 + (x1 - x0) * i / frames;
        int h = (i * (frames - i)) * 60 / (frames * frames / 4 + 1) / 4;
        ball_y = y0 + (y1 - y0) * i / frames - h;
        ball_draw(0);
        frame_wait();
    }
}

void fx_throw_tampon(int x, int y)
{
    if (!ready)
        return;
    throw_arc(20, 150, x, y, 16);
    sfx_play(SFX_STAMP);
    ball_on = false;
    ball_draw(0);
    for (int i = 0; i < 6; i++) {
        int ang = i * 65536 / 6;
        set_part(i, 19, 0, x, y, cosLerp(ang) >> 8, sinLerp(ang) >> 8, 12);
    }
    run(10);
}

void fx_throw_ball_to_foe(int x, int y)
{
    if (!ready)
        return;
    throw_arc(40, 150, x, y, 22);
    sfx_play(SFX_STAMP);
    ball_x = x;
    ball_y = y + 20;
    ball_draw(0);
    for (int i = 0; i < 8; i++)
        set_part(i, 15, 3, x, y, ((i % 3) - 1) * 12, ((i / 3) - 1) * 12, 10);
    run(12);
}

void fx_ball_shake(void)
{
    for (int i = 0; i < 16; i++) {
        int s = (i / 2) % 4;
        ball_draw(s == 1 ? 2 : s == 3 ? -2 : 0);
        fx_update();
        frame_wait();
    }
    ball_draw(0);
}

void fx_ball_stars(void)
{
    int x = ball_on ? ball_x : 188, y = ball_on ? ball_y : 50;
    for (int i = 0; i < 6; i++) {
        int ang = i * 65536 / 6;
        set_part(i, 19, 0, x, y, cosLerp(ang) >> 9, (sinLerp(ang) >> 9) - 8, 30);
    }
    run(30);
}

void fx_clear(void)
{
    ball_on = false;
    ball_draw(0);
    for (int i = 0; i < FX_N; i++)
        parts[i].on = false;
    fx_update();
}

// Overworld -> battle: 12 stars converge in a spiral, then a white flash
void fx_star_transition(void)
{
    SpriteSheet st;
    if (!sheet_load(&st, "ui/stars.spr"))
        return;
    spr_ext_pal(false, PAL_MISC, st.pal, st.ncolors);
    u16 *g = spr_alloc(false, SpriteSize_16x16, SpriteColorFormat_256Color);
    spr_upload(g, sheet_frame(&st, 2), 256);
    sfx_play(SFX_WHOOSH);
    for (int t = 0; t < 40; t++) {
        int r = 140 - t * 3;
        if (r < 0)
            r = 0;
        oamRotateScale(&oamMain, 2, (t * 1200) & 0xFFFF, intToFixed(1, 8), intToFixed(1, 8));
        for (int i = 0; i < 12; i++) {
            int ang = i * 65536 / 12 + t * 900;
            int x = 128 + (cosLerp(ang) * r >> 12) - 8;
            int y = 96 + (sinLerp(ang) * r >> 12) - 8;
            oamSet(&oamMain, FX_OAM + i, x, y, 0, PAL_MISC, SpriteSize_16x16, SpriteColorFormat_256Color, g, 2,
                   false, false, false, false, false);
        }
        if (t > 28) {
            gfx_brightness(false, (t - 28) * 16 / 11);
            gfx_brightness(true, (t - 28) * 16 / 11);
        }
        frame_wait();
    }
    for (int i = 0; i < 12; i++)
        oamClearSprite(&oamMain, FX_OAM + i);
    oamUpdate(&oamMain);
    spr_free(false, g);
    sheet_free(&st);
}
