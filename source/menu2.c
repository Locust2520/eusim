// Shop, Archives (PC storage), badge case, Europe map markers, evolution scene.
#include "menu.h"
#include "lang.h"
#include "canvas.h"
#include "gfx.h"
#include "ui.h"
#include "image.h"
#include "input.h"
#include "audio.h"
#include "dialog.h"
#include "save.h"
#include "mon.h"
#include "sprite.h"
#include "creature_gfx.h"
#include "portrait.h"
#include "gen/font_data.h"
#include "gen/flags.h"
#include "gen/europe.h"

// ---------------------------------------------------------------- shop
static int shop_items(int tier, int *out)
{
    static const int base[] = {IT_TAMPON, IT_CAFE, IT_AVIS_JURIDIQUE, IT_REVEIL, IT_NON_SOLLICITATION};
    static const int t1[] = {IT_SUPER_TAMPON, IT_SANDWICH, IT_MOTION_RELANCE, IT_X_ARGUMENT, IT_X_RESILIENCE};
    static const int t2[] = {IT_TAMPON_QUALIFIE, IT_GAUFRE, IT_X_EXPERTISE, IT_X_DIPLOMATIE, IT_X_REACTIVITE};
    static const int t3[] = {IT_KNIDDELEN, IT_MENU_COMPLET, IT_PAUSE_SYNDICALE};
    int n = 0;
    for (unsigned i = 0; i < ARRAY_LEN(base); i++) out[n++] = base[i];
    if (tier >= 1) for (unsigned i = 0; i < ARRAY_LEN(t1); i++) out[n++] = t1[i];
    if (tier >= 2) for (unsigned i = 0; i < ARRAY_LEN(t2); i++) out[n++] = t2[i];
    if (tier >= 3) for (unsigned i = 0; i < ARRAY_LEN(t3); i++) out[n++] = t3[i];
    return n;
}

static int badge_count(void)
{
    int n = 0;
    for (int i = 0; i < 8; i++)
        n += (g_save.badges >> i) & 1;
    return n;
}

static int qty_picker(int price, int max)
{
    int q = 1;
    ui_bottom_push();
    bool redraw = true;
    while (1) {
        if (redraw) {
            canvas_frame(&g_bot, 40, 60, 176, 72, FRAME_GOLD);
            canvas_rect(&g_bot, 46, 66, 164, 60, C_WHITE);
            char buf[48];
            snprintf(buf, sizeof buf, "◀  × %d  ▶", q);
            ui_text_in(&g_bot, &font_main, 40, 64, 176, 24, buf, C_TEXT, C_SHADOW, 0);
            snprintf(buf, sizeof buf, T("Total : %d €"), q * price);
            ui_text_in(&g_bot, &font_small, 40, 88, 176, 18, buf, C_BLUE, 0, 0);
            ui_text_in(&g_bot, &font_small, 40, 106, 176, 20, "A : valider   B : annuler", C_BTN_SH, 0, 0);
            redraw = false;
        }
        frame_wait();
        int o = q;
        if (g_krep & (KEY_RIGHT | KEY_UP)) q++;
        if (g_krep & (KEY_LEFT | KEY_DOWN)) q--;
        if (touch_in(40, 60, 60, 40)) q--;
        if (touch_in(156, 60, 60, 40)) q++;
        q = CLAMP(q, 1, MAX(1, max));
        if (q != o) {
            sfx_play(SFX_CURSOR);
            redraw = true;
        }
        if (g_kdown & KEY_A || touch_in(60, 100, 136, 30)) {
            ui_bottom_pop();
            return q;
        }
        if (g_kdown & KEY_B) {
            ui_bottom_pop();
            return 0;
        }
    }
}

void shop_open(int shop)
{
    (void)shop;
    static const char *const opts[3] = {"Acheter", "Vendre", "Au revoir"};
    dlg_say("Vendeur", "Bienvenue à la Boutique du Parlementarium ! Tout est garanti conforme aux normes CE.");
    while (1) {
        int c = dlg_choice(opts, 3, true);
        if (c < 0 || c == 2)
            break;
        if (c == 0) {
            int list[32];
            int n = shop_items(badge_count() / 2, list);
            ui_bottom_push();
            int sel = 0, scroll = 0;
            bool redraw = true;
            while (1) {
                if (sel < scroll) scroll = sel;
                if (sel >= scroll + 6) scroll = sel - 5;
                if (redraw) {
                    ui_backdrop(&g_bot);
                    char buf[48];
                    snprintf(buf, sizeof buf, T("Votre budget : %lu €"), (unsigned long)g_save.money);
                    canvas_frame(&g_bot, 4, 2, 248, 20, FRAME_DARK);
                    ui_text_in(&g_bot, &font_small, 4, 2, 247, 19, buf, C_GOLD, C_INK, 0);
                    for (int k = 0; k < 6 && scroll + k < n; k++) {
                        int it = list[scroll + k], y = 24 + k * 20;
                        canvas_frame(&g_bot, 4, y, 236, 19, scroll + k == sel ? FRAME_SELECT : FRAME_MENU);
                        ui_text_in(&g_bot, &font_small, 8, y, 180, 18, items[it].name, C_TEXT, 0, -1);
                        snprintf(buf, sizeof buf, "%d €", items[it].price);
                        ui_text_in(&g_bot, &font_small, 150, y, 86, 18, buf, C_BLUE, 0, 1);
                    }
                    if (n > 6)
                        ui_scrollbar(&g_bot, 243, 24, 119, n, 6, scroll);
                    canvas_frame(&g_bot, 4, 146, 248, 44, FRAME_DIALOG);
                    ui_text_wrapped(&g_bot, &font_small, 10, 149, 236, items[list[sel]].desc, C_TEXT, 0);
                    snprintf(buf, sizeof buf, T("En stock dans votre sac : %d"), bag_count(list[sel]));
                    canvas_text(&g_bot, &font_small, 12, 175, buf, C_BTN_SH, 0);
                    redraw = false;
                }
                frame_wait();
                {
                    int f = ui_scrollbar_drag(243, 24, 119, n, 6);
                    if (f >= 0 && f != scroll) {
                        scroll = f;
                        sel = CLAMP(sel, scroll, scroll + 5);
                        redraw = true;
                    }
                }
                int o = sel, pick = -1;
                if (g_krep & KEY_DOWN) sel = (sel + 1) % n;
                if (g_krep & KEY_UP) sel = (sel + n - 1) % n;
                for (int k = 0; k < 6 && scroll + k < n; k++)
                    if (touch_in(4, 24 + k * 20, 236, 19)) {
                        if (sel == scroll + k) pick = sel;
                        sel = scroll + k;
                    }
                if (g_kdown & KEY_A) pick = sel;
                if (o != sel) {
                    sfx_play(SFX_CURSOR);
                    redraw = true;
                }
                if (pick >= 0) {
                    int it = list[pick];
                    int price = items[it].price;
                    int maxq = MIN(99 - bag_count(it), price ? (int)(g_save.money / price) : 99);
                    if (maxq <= 0) {
                        sfx_play(SFX_ERROR);
                        dlg_say("Vendeur", "Il semble que votre budget soit… sous plafond de dépenses.");
                        dlg_close();
                    } else {
                        int q = qty_picker(price, maxq);
                        if (q > 0) {
                            g_save.money -= q * price;
                            bag_add(it, q);
                            sfx_play(SFX_COIN);
                            dlg_say("Vendeur", q >= 10 && it == IT_TAMPON ?
                                    "Merci ! Et voici un Super Tampon en cadeau, pour l'achat groupé !" :
                                    "Merci pour votre achat ! Facture en triple exemplaire.");
                            if (q >= 10 && it == IT_TAMPON)
                                bag_add(IT_SUPER_TAMPON, 1);
                            dlg_close();
                        }
                    }
                    redraw = true;
                }
                if (g_kdown & KEY_B)
                    break;
            }
            ui_bottom_pop();
        } else {
            int it = bag_menu(1);
            if (it < 0)
                continue;
            if (items[it].kind == IK_KEY || items[it].price == 0) {
                dlg_say("Vendeur", "Ça ? Ce n'est pas à vendre, c'est un objet d'importance stratégique !");
                continue;
            }
            int q = qty_picker(items[it].price / 2, bag_count(it));
            if (q > 0) {
                bag_take(it, q);
                g_save.money += q * (items[it].price / 2);
                sfx_play(SFX_COIN);
                dlg_say("Vendeur", "Marché conclu !");
            }
        }
    }
    dlg_say("Vendeur", "Au revoir ! N'oubliez pas : le chargeur USB-C est vendu séparément.");
    dlg_close();
}

// ---------------------------------------------------------------- archives (PC)
static void draw_box_list(int sel, int scroll, bool party_side)
{
    ui_backdrop(&g_bot);
    canvas_frame(&g_bot, 4, 2, 248, 20, FRAME_DARK);
    char buf[48];
    snprintf(buf, sizeof buf, party_side ? "ÉQUIPE → ARCHIVES (%d/%d)" : "ARCHIVES → ÉQUIPE (%d/%d)",
             party_side ? g_save.party_count : g_save.box_count, party_side ? PARTY_MAX : BOX_MAX);
    ui_text_in(&g_bot, &font_small, 4, 2, 247, 19, buf, C_GOLD, C_INK, 0);
    int n = party_side ? g_save.party_count : g_save.box_count;
    Mon *arr = party_side ? g_save.party : g_save.box;
    for (int k = 0; k < 6 && scroll + k < n; k++) {
        Mon *m = &arr[scroll + k];
        int y = 24 + k * 26;
        canvas_frame(&g_bot, 4, y, 236, 24, scroll + k == sel ? FRAME_SELECT : FRAME_MENU);
        creature_icon_draw(&g_bot, m->species, 8, y);
        ui_text_in(&g_bot, &font_main, 40, y, 150, 23, mon_name(m), C_TEXT, 0, -1);
        snprintf(buf, sizeof buf, T("N.%d"), m->level);
        ui_text_in(&g_bot, &font_small, 150, y, 86, 23, buf, C_BLUE, 0, 1);
    }
    if (n > 6)
        ui_scrollbar(&g_bot, 243, 24, 154, n, 6, scroll);
    if (n == 0)
        ui_text_in(&g_bot, &font_main, 0, 60, 256, 60, "(vide)", C_BTN_LO, C_INK, 0);
    ui_text_in(&g_bot, &font_small, 0, 178, 256, 14, "◀▶ côté   A : déplacer   B : quitter", C_BTN_LO, C_INK, 0);
}

void archives_open(void)
{
    dlg_say("", "{P} allume le terminal des Archives. « Bienvenue dans le système de gestion documentaire. »");
    dlg_close();
    ui_bottom_push();
    bool party_side = true;
    int sel = 0, scroll = 0;
    bool redraw = true;
    while (1) {
        int n = party_side ? g_save.party_count : g_save.box_count;
        if (sel >= n) sel = MAX(0, n - 1);
        if (sel < scroll) scroll = sel;
        if (sel >= scroll + 6) scroll = sel - 5;
        if (redraw) {
            draw_box_list(sel, scroll, party_side);
            redraw = false;
        }
        frame_wait();
        {
            int f = ui_scrollbar_drag(243, 24, 154, n, 6);
            if (f >= 0 && f != scroll) {
                scroll = f;
                sel = CLAMP(sel, scroll, scroll + 5);
                redraw = true;
            }
        }
        int o = sel;
        if (g_krep & KEY_DOWN && n) sel = (sel + 1) % n;
        if (g_krep & KEY_UP && n) sel = (sel + n - 1) % n;
        if (g_krep & (KEY_LEFT | KEY_RIGHT)) {
            party_side = !party_side;
            sel = scroll = 0;
            sfx_play(SFX_CURSOR);
            redraw = true;
        }
        int pick = -1;
        for (int k = 0; k < 6 && scroll + k < n; k++)
            if (touch_in(4, 24 + k * 26, 236, 24)) {
                if (sel == scroll + k) pick = sel;
                sel = scroll + k;
            }
        if (g_kdown & KEY_A && n) pick = sel;
        if (o != sel) {
            sfx_play(SFX_CURSOR);
            redraw = true;
        }
        if (pick >= 0) {
            if (party_side) {
                if (g_save.party_count <= 1) {
                    sfx_play(SFX_ERROR);
                    dlg_say("", "Il faut garder au moins un Euromon dans l'équipe !");
                    dlg_close();
                } else if (g_save.box_count >= BOX_MAX) {
                    sfx_play(SFX_ERROR);
                } else {
                    g_save.box[g_save.box_count++] = g_save.party[pick];
                    for (int i = pick; i < g_save.party_count - 1; i++)
                        g_save.party[i] = g_save.party[i + 1];
                    g_save.party_count--;
                    sfx_play(SFX_PAPER);
                }
            } else {
                if (g_save.party_count >= PARTY_MAX) {
                    sfx_play(SFX_ERROR);
                    dlg_say("", "L'équipe est complète (6 Euromons maximum).");
                    dlg_close();
                } else {
                    Mon m = g_save.box[pick];
                    mon_heal(&m);
                    g_save.party[g_save.party_count++] = m;
                    for (int i = pick; i < g_save.box_count - 1; i++)
                        g_save.box[i] = g_save.box[i + 1];
                    g_save.box_count--;
                    sfx_play(SFX_PAPER);
                }
            }
            redraw = true;
        }
        if (g_kdown & KEY_B)
            break;
    }
    sfx_play(SFX_CANCEL);
    ui_bottom_pop();
}

// ---------------------------------------------------------------- badge case
static const char *const badge_names[8] = {"Rescrit", "Euro", "Hémicycle", "OXI", "Article 50", "Veto", "Amende", "Sorbonne"};
static const char *const badge_from[8] = {"Jean-Claude Juncker, Luxembourg", "Christine Lagarde, Francfort",
                                          "Roberta Metsola, Strasbourg", "Yanis Varoufakis, Athènes",
                                          "Farage & Johnson, Londres", "Viktor Orbán, Budapest",
                                          "Margrethe Vestager, Bruxelles", "Emmanuel Macron, Paris"};

void badge_case_open(void)
{
    ui_bottom_push();
    ui_backdrop(&g_bot);
    canvas_frame(&g_bot, 4, 2, 248, 20, FRAME_DARK);
    ui_text_in(&g_bot, &font_small, 4, 2, 247, 19, "ÉTUI À BADGES DES TRAITÉS", C_GOLD, C_INK, 0);
    for (int b = 0; b < 8; b++) {
        int x = 6 + (b % 2) * 124, y = 26 + (b / 2) * 40;
        bool has = g_save.badges & (1 << b);
        canvas_frame(&g_bot, x, y, 120, 38, has ? FRAME_GOLD : FRAME_MENU);
        // badge medallion
        canvas_rect(&g_bot, x + 6, y + 8, 22, 22, has ? C_BLUE : C_LGREY);
        canvas_box(&g_bot, x + 6, y + 8, 22, 22, has ? C_GOLD : C_MGREY);
        ui_text_in(&g_bot, &font_main, x + 4, y, 26, 37, "★", has ? C_GOLD_D : C_MGREY, 0, 0);
        canvas_text(&g_bot, &font_small, x + 30, y + 3, has ? badge_names[b] : "???", C_TEXT, 0);
        canvas_text(&g_bot, &font_small, x + 30, y + 18, has ? "obtenu" : "à conquérir", has ? C_TYPE0 + 5 : C_MGREY, 0);
    }
    frame_wait();
    int sel = -1;
    while (!(g_kdown & KEY_B)) {
        frame_wait();
        for (int b = 0; b < 8; b++)
            if (touch_in(6 + (b % 2) * 124, 26 + (b / 2) * 40, 120, 38) && (g_save.badges & (1 << b)))
                sel = b;
        if (sel >= 0) {
            char buf[96];
            snprintf(buf, sizeof buf, T("Badge %s — remis par %s."), tr(badge_names[sel]), tr(badge_from[sel]));
            dlg_say("", buf);
            dlg_close();
            sel = -1;
        }
        if (g_kdown & KEY_A)
            break;
    }
    sfx_play(SFX_CANCEL);
    ui_bottom_pop();
}

// ---------------------------------------------------------------- Europe map markers
typedef struct { int x, y, w, h; } MapLabel;

static bool map_labels_overlap(MapLabel a, MapLabel b)
{
    return a.x < b.x + b.w + 2 && a.x + a.w + 2 > b.x &&
           a.y < b.y + b.h + 2 && a.y + a.h + 2 > b.y;
}

static void map_label_line(int x, int y, int tx, int ty, u8 color)
{
    int dx = abs(tx - x), dy = -abs(ty - y);
    int sx = x < tx ? 1 : -1, sy = y < ty ? 1 : -1;
    int err = dx + dy;
    while (1) {
        canvas_pixel(&g_bot, x, y, color);
        if (x == tx && y == ty)
            break;
        int e = 2 * err;
        if (e >= dy) { err += dy; x += sx; }
        if (e <= dx) { err += dx; y += sy; }
    }
}

void europe_map_markers(void)
{
    extern const char *world_city_key(void);
    const char *here = world_city_key();
    MapLabel labels[NUM_EUROPE_CITIES];
    int order[NUM_EUROPE_CITIES], count = 0;
    // Give the current city first choice of nearby space.
    for (int i = 0; i < NUM_EUROPE_CITIES; i++)
        if (here && !strcmp(here, europe_cities[i].key))
            order[count++] = i;
    for (int i = 0; i < NUM_EUROPE_CITIES; i++)
        if (!here || strcmp(here, europe_cities[i].key))
            order[count++] = i;
    for (int n = 0; n < count; n++) {
        int i = order[n];
        const EuropeCity *c = &europe_cities[i];
        int w = MIN(100, font_width(&font_small, tr(c->label)) + 10);
        int best = 0x7FFFFFFF;
        MapLabel chosen = {2, 28, w, 13};
        // Search free space below the banner; keep labels clear of every marker.
        // Long translations may need a narrower box; ui_text_in fits the text.
        for (; w >= 20 && best == 0x7FFFFFFF; w -= 4) {
            for (int y = 28; y + 13 <= 190; y += 2) {
                for (int x = 2; x + w <= 254; x += 2) {
                    MapLabel box = {x, y, w, 13};
                    int tx = CLAMP(c->x, x, x + w - 1);
                    int ty = CLAMP(c->y, y, y + 12);
                    int dx = tx - c->x, dy = ty - c->y;
                    int score = dx * dx + dy * dy;
                    if (score >= best)
                        continue;
                    bool blocked = false;
                    for (int k = 0; k < n && !blocked; k++)
                        blocked = map_labels_overlap(box, labels[order[k]]);
                    for (int k = 0; k < NUM_EUROPE_CITIES && !blocked; k++) {
                        MapLabel marker = {europe_cities[k].x - 3, europe_cities[k].y - 3, 7, 7};
                        blocked = map_labels_overlap(box, marker);
                    }
                    if (!blocked) { best = score; chosen = box; }
                }
            }
        }
        labels[i] = chosen;
    }
    // Leaders first, then opaque labels, then markers so all three stay distinct.
    for (int i = 0; i < NUM_EUROPE_CITIES; i++) {
        MapLabel b = labels[i];
        const EuropeCity *c = &europe_cities[i];
        map_label_line(c->x, c->y, CLAMP(c->x, b.x, b.x + b.w - 1),
                       CLAMP(c->y, b.y, b.y + b.h - 1), C_INK);
    }
    for (int i = 0; i < NUM_EUROPE_CITIES; i++) {
        MapLabel b = labels[i];
        bool cur = here && !strcmp(here, europe_cities[i].key);
        canvas_rect(&g_bot, b.x, b.y, b.w, b.h, C_INK);
        ui_text_in(&g_bot, &font_small, b.x, b.y, b.w, b.h, europe_cities[i].label,
                   cur ? C_GOLD : C_WHITE, 0, 0);
    }
    for (int i = 0; i < NUM_EUROPE_CITIES; i++) {
        const EuropeCity *c = &europe_cities[i];
        bool cur = here && !strcmp(here, c->key);
        canvas_rect(&g_bot, c->x - 2, c->y - 2, 5, 5, cur ? C_RED : C_BLUE_D);
        canvas_rect(&g_bot, c->x - 1, c->y - 1, 3, 3, cur ? C_GOLD : C_WHITE);
    }
}

// ---------------------------------------------------------------- evolution
void evolve_mon(Mon *m, int into)
{
    char old_name[24];
    strncpy(old_name, mon_name(m), sizeof old_name - 1);
    old_name[23] = 0;
    gfx_clear_scene(false);
    canvas_clear(&g_top, 0);
    u16 prev_bg = BG_PALETTE[0];
    BG_PALETTE[0] = RGB8(16, 20, 48);
    SpriteSheet a, b;
    creature_sheet_load(&a, m->species, false);
    creature_sheet_load(&b, into, false);
    u16 *ga = spr_alloc(false, SpriteSize_64x64, SpriteColorFormat_256Color);
    u16 *gb = spr_alloc(false, SpriteSize_64x64, SpriteColorFormat_256Color);
    spr_upload(ga, sheet_frame(&a, 0), 4096);
    spr_upload(gb, sheet_frame(&b, 0), 4096);
    spr_ext_pal(false, PAL_BATTLE_FOE, a.pal, a.ncolors);
    spr_ext_pal(false, PAL_BATTLE_ALLY, b.pal, b.ncolors);
    u16 white[256];
    for (int i = 0; i < 256; i++)
        white[i] = RGB15(31, 31, 31);
    for (int i = 50; i < 128; i++)
        oamClearSprite(&oamMain, i);
    music_play("evolution");
    oamSet(&oamMain, OAM_BATTLE, 96, 50, 0, PAL_BATTLE_FOE, SpriteSize_64x64, SpriteColorFormat_256Color, ga, -1,
           false, false, false, false, false);
    char buf[96];
    snprintf(buf, sizeof buf, T("Quoi ? %s évolue !"), old_name);
    // Post-battle evolution starts with both screens faded to black.
    gfx_fade_in(20, false);
    dlg_say("", buf);
    dlg_close();
    bool cancelled = false;
    int t = 0;
    for (int phase = 0; phase < 14 && !cancelled; phase++) {
        int period = 24 - phase * 3 / 2;
        for (int k = 0; k < period; k++) {
            bool show_new = (phase % 2) == 1;
            spr_ext_pal(false, PAL_BATTLE_FX, white, 32);
            oamSet(&oamMain, OAM_BATTLE, 96, 50, 0, PAL_BATTLE_FX, SpriteSize_64x64, SpriteColorFormat_256Color,
                   show_new ? gb : ga, -1, false, false, false, false, false);
            frame_wait();
            t++;
            if (g_kdown & KEY_B) {
                cancelled = true;
                break;
            }
        }
    }
    sfx_play(cancelled ? SFX_CANCEL : SFX_LEVELUP);
    oamSet(&oamMain, OAM_BATTLE, 96, 50, 0, cancelled ? PAL_BATTLE_FOE : PAL_BATTLE_ALLY, SpriteSize_64x64,
           SpriteColorFormat_256Color, cancelled ? ga : gb, -1, false, false, false, false, false);
    gfx_fade_in(1, true);
    if (cancelled) {
        snprintf(buf, sizeof buf, T("Vous avez reporté la réforme. %s n'a pas évolué."), old_name);
        dlg_say("", buf);
    } else {
        int oldmax = mon_max_hp(m);
        m->species = into;
        m->hp += mon_max_hp(m) - oldmax;
        if (m->hp < 1)
            m->hp = 1;
        dex_caught(into);
        sfx_cry(into);
        snprintf(buf, sizeof buf, T("Félicitations ! %s a évolué en %s !"), old_name, species[into].name);
        dlg_say("", buf);
        // learn moves of the new form at current level
        const u16 *l = species[into].learn;
        for (int i = 0; l[i] != 0xFFFF; i += 2)
            if (l[i] == m->level) {
                int mv = l[i + 1];
                int r = mon_learn(m, mv);
                if (r >= 0) {
                    snprintf(buf, sizeof buf, T("%s apprend %s !"), species[into].name, moves[l[i + 1]].name);
                    dlg_say("", buf);
                } else if (r == -2) {
                    snprintf(buf, sizeof buf, T("%s veut apprendre %s, mais connaît déjà quatre attaques."),
                             mon_name(m), moves[mv].name);
                    dlg_say("", buf);
                    const char *opts[5];
                    for (int k = 0; k < 4; k++)
                        opts[k] = moves[m->moves[k]].name;
                    opts[4] = "Ne pas apprendre";
                    dlg_say("", "Quelle attaque oublier ?");
                    int c = dlg_choice(opts, 5, true);
                    if (c >= 0 && c < 4) {
                        snprintf(buf, sizeof buf, T("1, 2, 3… Hop ! %s oublie %s…"),
                                 mon_name(m), moves[m->moves[c]].name);
                        dlg_say("", buf);
                        m->moves[c] = mv;
                        m->pp[c] = moves[mv].pp;
                        sfx_play(SFX_LEVELUP);
                        snprintf(buf, sizeof buf, T("… et apprend %s !"), moves[mv].name);
                        dlg_say("", buf);
                    } else {
                        snprintf(buf, sizeof buf, T("%s n'apprend pas %s."), mon_name(m), moves[mv].name);
                        dlg_say("", buf);
                    }
                }
            }
    }
    dlg_close();
    oamClearSprite(&oamMain, OAM_BATTLE);
    oamUpdate(&oamMain);
    spr_free(false, ga);
    spr_free(false, gb);
    sheet_free(&a);
    sheet_free(&b);
    BG_PALETTE[0] = prev_bg;
}

// ---------------------------------------------------------------- jukebox (studio bonus)
// Lists only the pieces of the soundtrack the player has already heard in the game.
static void jukebox_top(const char *title, int idx, int n_heard, int t)
{
    u32 total = 0, rate = 1;
    u32 pos = music_position(&total, &rate);
    canvas_rect(&g_top, 0, 0, 256, 192, 0);
    ui_backdrop(&g_top);
    ui_panel(&g_top, 12, 20, 232, 150, true);
    ui_text_in(&g_top, &font_main, 12, 26, 232, 22, "Juke-box", C_GOLD, C_INK, 0);
    char buf[48];
    snprintf(buf, sizeof buf, T("%d musiques sur %d"), n_heard, g_music_count);
    ui_text_in(&g_top, &font_small, 12, 48, 232, 14, buf, C_BTN_MID, C_INK, 0);
    // equaliser
    for (int b = 0; b < 16; b++) {
        int h = idx >= 0 ? 6 + (int)((u32)((b * 7 + 3) * (t / 4 + b * 13) * 2654435761u) >> 27) : 2;
        canvas_rect(&g_top, 40 + b * 11, 120 - h, 8, h, b < 5 ? C_GREEN : b < 11 ? C_GOLD : C_RED);
    }
    if (idx >= 0) {
        ui_text_in(&g_top, &font_main, 16, 64, 224, 22, title, C_WHITE, C_INK, 0);
        canvas_bar(&g_top, 40, 128, 176, 6, total ? (int)(pos * 1000ull / total) : 0, 1000, C_GOLD);
        snprintf(buf, sizeof buf, "%lu:%02lu / %lu:%02lu", (unsigned long)(pos / rate / 60),
                 (unsigned long)(pos / rate % 60), (unsigned long)(total / rate / 60), (unsigned long)(total / rate % 60));
        ui_text_in(&g_top, &font_small, 12, 138, 232, 14, buf, C_BTN_MID, C_INK, 0);
    } else {
        ui_text_in(&g_top, &font_small, 16, 70, 224, 16, "Choisis un morceau.", C_BTN_MID, C_INK, 0);
    }
}

void jukebox_open(void)
{
    char prev[24];
    snprintf(prev, sizeof prev, "%s", music_current());
    int list[64], n = 0;
    for (int i = 0; i < g_music_count && n < 64; i++)
        if (music_heard(i))
            list[n++] = i;
    ui_bottom_push();
    int sel = 0, scroll = 0, playing = -1, t = 0;
    bool redraw = true;
    const int VIS = 7;
    while (1) {
        if (sel < scroll) scroll = sel;
        if (sel >= scroll + VIS) scroll = sel - VIS + 1;
        if (redraw) {
            ui_backdrop(&g_bot);
            canvas_frame(&g_bot, 4, 2, 248, 20, FRAME_DARK);
            ui_text_in(&g_bot, &font_small, 4, 2, 247, 19, "JUKE-BOX", C_GOLD, C_INK, 0);
            for (int k = 0; k < VIS && scroll + k < n; k++) {
                int i = list[scroll + k], y = 24 + k * 22;
                canvas_frame(&g_bot, 4, y, 236, 21, scroll + k == sel ? FRAME_SELECT : FRAME_MENU);
                if (i == playing)
                    ui_text_in(&g_bot, &font_small, 8, y, 16, 20, "▶", C_RED, 0, -1);
                ui_text_in(&g_bot, &font_small, 22, y, 214, 20, g_music_list[i].title, C_TEXT, 0, -1);
            }
            if (n > VIS)
                ui_scrollbar(&g_bot, 243, 24, VIS * 22 - 1, n, VIS, scroll);
            ui_text_in(&g_bot, &font_small, 0, 178, 256, 14, "A : écouter    B : retour", C_BTN_LO, C_INK, 0);
            redraw = false;
        }
        if ((t & 7) == 0)
            jukebox_top(playing >= 0 ? g_music_list[playing].title : "", playing, n, t);
        frame_wait();
        t++;
        {
            int f = ui_scrollbar_drag(243, 24, VIS * 22 - 1, n, VIS);
            if (f >= 0 && f != scroll) {
                scroll = f;
                sel = CLAMP(sel, scroll, scroll + VIS - 1);
                redraw = true;
            }
        }
        int o = sel, pick = -1;
        if (g_krep & KEY_DOWN && n) sel = (sel + 1) % n;
        if (g_krep & KEY_UP && n) sel = (sel + n - 1) % n;
        for (int k = 0; k < VIS && scroll + k < n; k++)
            if (touch_in(4, 24 + k * 22, 236, 21)) {
                if (sel == scroll + k) pick = sel;
                sel = scroll + k;
            }
        if (g_kdown & KEY_A && n) pick = sel;
        if (o != sel) {
            sfx_play(SFX_CURSOR);
            redraw = true;
        }
        if (pick >= 0) {
            playing = list[pick];
            music_stop();
            music_play(g_music_list[playing].file);
            redraw = true;
        }
        if (g_kdown & KEY_B) {
            sfx_play(SFX_CANCEL);
            break;
        }
    }
    ui_bottom_pop();
    music_stop();
    if (prev[0])
        music_play(prev);
}
