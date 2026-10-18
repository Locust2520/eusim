// Touch-screen mini-games: plenary vote, rubber stamp, cookie banners, night summit (microphone), trunks,
// and the five computer terminals: inbox, fact-check, translation desk, ECB rate, USB-C.
#include "minigame.h"
#include "lang.h"
#include "canvas.h"
#include "gfx.h"
#include "ui.h"
#include "input.h"
#include "audio.h"
#include "dialog.h"
#include "gen/font_data.h"

enum { MG_VOTE, MG_TAMPON, MG_COOKIES, MG_SOMMET, MG_TRILOGUE, MG_LANGUES, MG_BOUCHON, MG_SIGNATURE, MG_MALLES,
       MG_COURRIELS, MG_DESINFOX, MG_TAUX, MG_USBC };

static void top_panel(const char *title, const char *rule, int secs_left, int score, int goal)
{
    canvas_clear(&g_top, 0);
    ui_backdrop(&g_top);
    canvas_frame(&g_top, 8, 8, 240, 46, FRAME_GOLD);
    ui_text_in(&g_top, &font_main, 8, 10, 239, 22, title, C_BLUE, C_SHADOW, 0);
    ui_text_in(&g_top, &font_small, 8, 31, 239, 18, rule, C_TEXT, 0, 0);
    char buf[48];
    canvas_frame(&g_top, 40, 70, 176, 58, FRAME_DIALOG);
    snprintf(buf, sizeof buf, T("Temps : %d s"), secs_left);
    ui_text_in(&g_top, &font_main, 40, 74, 175, 24, buf, secs_left <= 5 ? C_RED : C_TEXT, C_SHADOW, 0);
    if (goal < 0)   // percentage games: score = % of the time on target
        snprintf(buf, sizeof buf, T("Zone verte : %d %%"), score);
    else
        snprintf(buf, sizeof buf, T("Score : %d / %d"), score, goal);
    ui_text_in(&g_top, &font_main, 40, 98, 175, 24, buf, C_BLUE, C_SHADOW, 0);
}

static bool intro(const char *title, const char *text)
{
    canvas_clear(&g_top, 0);
    ui_backdrop(&g_bot);
    BG_PALETTE[0] = RGB8(0, 36, 110);
    ui_backdrop(&g_top);
    canvas_frame(&g_top, 8, 8, 240, 46, FRAME_GOLD);
    ui_text_in(&g_top, &font_main, 8, 10, 239, 22, title, C_BLUE, C_SHADOW, 0);
    ui_text_in(&g_top, &font_small, 8, 31, 239, 18, "Mini-jeu", C_TEXT, 0, 0);
    music_play("minigame");
    dlg_say("", text);
    dlg_close();
    for (int i = 3; i > 0; i--) {
        char b[4];
        snprintf(b, sizeof b, "%d", i);
        ui_button(&g_bot, 100, 70, 56, 50, b, BTN_SELECTED, &font_main);
        sfx_play(SFX_CURSOR);
        for (int k = 0; k < 40; k++)
            frame_wait();
    }
    sfx_play(SFX_SELECT);
#ifdef WEBSITE_CAPTURE
    extern volatile u32 g_site_capture[8];
    g_site_capture[5] = 1;
    DC_FlushRange((void *)g_site_capture, 32);
#endif
    return true;
}

static int outro(bool ok, const char *win, const char *lose)
{
    sfx_play(ok ? SFX_LEVELUP : SFX_ERROR);
    dlg_say("", ok ? win : lose);
    dlg_close();
    canvas_clear(&g_top, 0);
    canvas_clear(&g_bot, 0);
    return ok ? 1 : 0;
}

// ---------------------------------------------------------------- vote: tap the seats that light up
static int mg_vote(void)
{
    intro("Vote en plénière", "Les députés arrivent dans l'hémicycle ! Touchez chaque siège qui s'allume en jaune avant qu'il ne s'éteigne. 25 votes en 30 secondes !");
    int sx[48], sy[48], life[48];
    int n = 0;
    for (int r = 0; r < 4; r++) {
        int cnt = 9 + r * 1;
        int rad = 40 + r * 22;
        for (int k = 0; k < cnt && n < 48; k++) {
            int a = 32768 + (k * 32768) / (cnt - 1);
            sx[n] = 128 + (cosLerp(a) * rad >> 12);
            sy[n] = 176 + (sinLerp(a) * rad >> 12);
            life[n] = 0;
            n++;
        }
    }
    int score = 0, goal = 25, frames = 30 * 60, misses = 0;
    while (frames > 0 && score < goal) {
        if (frames % 30 == 0) {
            int k = rng_range(n);
            if (!life[k])
                life[k] = 70 + rng_range(40);
        }
        ui_backdrop(&g_bot);
        canvas_rect(&g_bot, 108, 160, 40, 24, C_GOLD_D);
        canvas_text_center(&g_bot, &font_small, 128, 166, "Présidence", C_WHITE, 0);
        for (int k = 0; k < n; k++) {
            u8 c = life[k] ? (life[k] < 25 && (life[k] & 4) ? C_GOLD_D : C_YELLOW) : C_BLUE_L;
            canvas_rect(&g_bot, sx[k] - 5, sy[k] - 5, 11, 11, C_TEXT);
            canvas_rect(&g_bot, sx[k] - 4, sy[k] - 4, 9, 9, c);
            if (life[k] && --life[k] == 0)
                misses++;
        }
        if (g_touch_down) {
            bool hit = false;
            for (int k = 0; k < n; k++)
                if (life[k] && abs(g_touch_x - sx[k]) <= 8 && abs(g_touch_y - sy[k]) <= 8) {
                    life[k] = 0;
                    score++;
                    hit = true;
                    sfx_play(SFX_VOTE);
                }
            if (!hit)
                sfx_play(SFX_BUMP);
        }
        if (frames % 15 == 0)
            top_panel("Vote en plénière", "Touchez les sièges jaunes !", frames / 60, score, goal);
        frame_wait();
        frames--;
    }
    return outro(score >= goal, "Adopté à une large majorité ! Applaudissements sur tous les bancs.",
                 "Le quorum n'est pas atteint. La séance est suspendue…");
}

// ---------------------------------------------------------------- tampon: approve valid documents, let fakes pass
static int mg_tampon(void)
{
    intro("Le Tampon", "Tamponnez 15 arrêts valides en 30 secondes. Laissez passer les papiers marqués « FAUX » : en tamponner un fait perdre la manche !");
    int x[6], y[6], st[6];
    bool valid[6];
    for (int i = 0; i < 6; i++)
        x[i] = -100;
    int score = 0, goal = 15, frames = 30 * 60, spawn = 0;
    bool mistake = false;
    while (frames > 0 && score < goal && !mistake) {
        if (--spawn <= 0) {
            for (int i = 0; i < 6; i++)
                if (x[i] < -60 || x[i] > 260) {
                    x[i] = -50;
                    y[i] = 20 + rng_range(120);
                    st[i] = 0;
                    valid[i] = rng_range(3) != 0;
                    break;
                }
            spawn = 40 - MIN(25, score);
        }
        canvas_clear(&g_bot, C_GOLD_D);
        for (int i = 0; i < 6; i++) {
            if (x[i] < -60 || x[i] > 260)
                continue;
            x[i] += 1 + score / 5;
            canvas_rect(&g_bot, x[i], y[i], 40, 48, C_TEXT);
            canvas_rect(&g_bot, x[i] + 1, y[i] + 1, 38, 46, C_WHITE);
            u8 label_color = valid[i] ? C_GREEN : C_RED;
            canvas_rect(&g_bot, x[i] + 2, y[i] + 2, 36, 13, label_color);
            ui_text_in(&g_bot, &font_small, x[i] + 2, y[i] + 2, 36, 13,
                       valid[i] ? "ARRÊT" : "FAUX", C_WHITE, C_INK, 0);
            for (int l = 0; l < 4; l++)
                canvas_hline(&g_bot, x[i] + 5, y[i] + 20 + l * 7, 28, C_LGREY);
            if (st[i]) {
                canvas_box(&g_bot, x[i] + 8, y[i] + 14, 24, 18, C_RED);
                canvas_text(&g_bot, &font_small, x[i] + 11, y[i] + 16, "OK", C_RED, 0);
            }
        }
        if (g_touch_down) {
            // The last drawn sheet is on top; never stamp through it.
            for (int i = 5; i >= 0; i--)
                if (x[i] >= -40 && x[i] < 256 && g_touch_x >= x[i] && g_touch_x < x[i] + 40 &&
                    g_touch_y >= y[i] && g_touch_y < y[i] + 48) {
                    if (!st[i]) {
                        st[i] = 1;
                        if (valid[i]) {
                            score++;
                            sfx_play(SFX_STAMP);
                        } else {
                            mistake = true;
                            sfx_play(SFX_ERROR);
                        }
                    }
                    break;
                }
        }
        if (frames % 15 == 0)
            top_panel("Le Tampon", "ARRÊT : tamponner. FAUX : laisser passer.", frames / 60, score, goal);
        frame_wait();
        frames--;
    }
    return outro(score >= goal, "Quinze arrêts valides tamponnés ! L'administration est fière de vous.",
                 mistake ? "Un mauvais document a été tamponné ! Il faut vérifier avant de valider…"
                         : "Les quinze arrêts valides ne sont pas prêts. Le greffe ferme, il faudra réessayer…");
}

// ---------------------------------------------------------------- cookies: refuse banners before they pile up
static int mg_cookies(void)
{
    intro("Bandeaux cookies", "Des bandeaux cookies envahissent l'écran ! Touchez « Refuser » sur chacun. Si six bandeaux s'accumulent, c'est perdu. Tenez 25 secondes !");
    int bx[8], by[8];
    bool on[8] = {0};
    int frames = 25 * 60, spawn = 30, score = 0;
    bool lost = false;
    while (frames > 0 && !lost) {
        if (--spawn <= 0) {
            for (int i = 0; i < 8; i++)
                if (!on[i]) {
                    on[i] = true;
                    bx[i] = 4 + rng_range(140);
                    by[i] = 4 + rng_range(140);
                    break;
                }
            spawn = 45 - MIN(25, score * 2);
        }
        int count = 0;
        canvas_clear(&g_bot, C_PANEL);
        canvas_text_center(&g_bot, &font_small, 128, 90, "(un site internet quelconque)", C_LGREY, 0);
        for (int i = 0; i < 8; i++) {
            if (!on[i])
                continue;
            count++;
            canvas_frame(&g_bot, bx[i], by[i], 108, 44, FRAME_MENU);
            canvas_text(&g_bot, &font_small, bx[i] + 7, by[i] + 2, "Nous respectons", C_TEXT, 0);
            canvas_text(&g_bot, &font_small, bx[i] + 7, by[i] + 12, "votre vie privée", C_TEXT, 0);
            canvas_rect(&g_bot, bx[i] + 5, by[i] + 27, 48, 13, C_GREEN);
            ui_text_in(&g_bot, &font_small, bx[i] + 5, by[i] + 27, 48, 13, "Accepter", C_WHITE, C_INK, 0);
            canvas_rect(&g_bot, bx[i] + 55, by[i] + 27, 48, 13, C_RED);
            ui_text_in(&g_bot, &font_small, bx[i] + 55, by[i] + 27, 48, 13, "Refuser", C_WHITE, C_INK, 0);
        }
        if (count >= 6)
            lost = true;
        if (g_touch_down) {
            for (int i = 7; i >= 0; i--) {
                if (!on[i])
                    continue;
                if (g_touch_x >= bx[i] + 56 && g_touch_x < bx[i] + 102 && g_touch_y >= by[i] + 28 && g_touch_y < by[i] + 40) {
                    on[i] = false;
                    score++;
                    sfx_play(SFX_SELECT);
                    break;
                }
                if (g_touch_x >= bx[i] + 6 && g_touch_x < bx[i] + 52 && g_touch_y >= by[i] + 28 && g_touch_y < by[i] + 40) {
                    // accepting spawns two more banners
                    sfx_play(SFX_ERROR);
                    for (int k = 0, added = 0; k < 8 && added < 2; k++)
                        if (!on[k]) {
                            on[k] = true;
                            bx[k] = 4 + rng_range(140);
                            by[k] = 4 + rng_range(140);
                            added++;
                        }
                    break;
                }
            }
        }
        if (frames % 15 == 0)
            top_panel("Bandeaux cookies", "Refusez tout ! (ne cliquez pas sur Accepter)", frames / 60, score, 99);
        frame_wait();
        frames--;
    }
    return outro(!lost, "Tous les cookies refusés ! Le RGPD est fier de vous.",
                 "Submergé par les bandeaux… Vous avez accepté 437 partenaires publicitaires.");
}

// ---------------------------------------------------------------- sommet: wake up the 27 leaders (mic or tap)
static int mg_sommet(void)
{
    intro("Sommet nocturne", "Il est 3 h du matin, les 27 chefs d'État s'endorment ! Soufflez dans le micro (ou touchez la tête qui dort) pour les réveiller. 27 réveils avant l'aube !");
    mic_start();
    int asleep = -1, score = 0, goal = 27, frames = 45 * 60, sleep_timer = 20;
    int cx[27], cy[27];
    for (int i = 0; i < 27; i++) {
        int a = (i * 65536) / 27;
        cx[i] = 128 + (cosLerp(a) * 104 >> 12);
        cy[i] = 96 + (sinLerp(a) * 76 >> 12);
    }
    while (frames > 0 && score < goal) {
        if (asleep < 0 && --sleep_timer <= 0)
            asleep = rng_range(27);
        ui_backdrop(&g_bot);
        canvas_rect(&g_bot, 60, 60, 136, 72, C_GOLD_D);
        canvas_rect(&g_bot, 62, 62, 132, 68, RGB15(0, 0, 0) ? 0 : C_GOLD);
        int hour = 3 + (45 * 60 - frames) / (60 * 15);
        char buf[16];
        snprintf(buf, sizeof buf, "%d h %02d", hour, ((45 * 60 - frames) / 15) % 60);
        canvas_text_center(&g_bot, &font_main, 128, 88, buf, C_TEXT, 0);
        for (int i = 0; i < 27; i++) {
            bool z = i == asleep;
            canvas_rect(&g_bot, cx[i] - 6, cy[i] - 6, 12, 12, C_TEXT);
            canvas_rect(&g_bot, cx[i] - 5, cy[i] - 5, 10, 10, z ? C_LGREY : C_YELLOW);
            if (z)
                canvas_text(&g_bot, &font_small, cx[i] + 6, cy[i] - 14, (frames / 20) & 1 ? "Zz" : "z", C_WHITE, 0);
            else {
                canvas_pixel(&g_bot, cx[i] - 2, cy[i] - 1, C_TEXT);
                canvas_pixel(&g_bot, cx[i] + 2, cy[i] - 1, C_TEXT);
            }
        }
        bool woke = false;
        if (asleep >= 0) {
            if (mic_level() > 120)
                woke = true;
            if (g_touch_down && abs(g_touch_x - cx[asleep]) <= 10 && abs(g_touch_y - cy[asleep]) <= 10)
                woke = true;
            if (g_kdown & KEY_A)
                woke = true;
        }
        if (woke) {
            sfx_play(SFX_ALARM);
            score++;
            asleep = -1;
            sleep_timer = 15 + rng_range(25);
        }
        if (frames % 15 == 0)
            top_panel("Sommet nocturne", "Soufflez / touchez la tête endormie !", frames / 60, score, goal);
        frame_wait();
        frames--;
    }
    mic_stop();
    return outro(score >= goal, "Tous réveillés ! Accord trouvé à 4 h 37. Comme d'habitude.",
                 "Le soleil se lève sur une table de dirigeants endormis. Le sommet est reporté.");
}

// ---------------------------------------------------------------- malles: tap trunks in numeric order
static int mg_malles(void)
{
    intro("Les malles de Strasbourg", "Chargez les malles des députés dans le train, dans l'ordre : 1, 2, 3… jusqu'à 10. Vous avez 30 secondes !");
    int mx[10], my[10];
    bool done[10] = {0};
    for (int i = 0; i < 10; i++) {
        bool ok;
        do {
            ok = true;
            mx[i] = 8 + rng_range(200);
            my[i] = 8 + rng_range(140);
            for (int j = 0; j < i; j++)
                if (abs(mx[i] - mx[j]) < 46 && abs(my[i] - my[j]) < 36)
                    ok = false;
        } while (!ok);
    }
    int next = 0, frames = 30 * 60;
    while (frames > 0 && next < 10) {
        canvas_clear(&g_bot, C_MGREY);
        canvas_rect(&g_bot, 0, 170, 256, 22, C_DGREY);
        canvas_text_center(&g_bot, &font_small, 128, 174, "Quai — TGV Strasbourg ⇄ Bruxelles", C_WHITE, 0);
        for (int i = 0; i < 10; i++) {
            if (done[i])
                continue;
            canvas_rect(&g_bot, mx[i], my[i], 40, 30, C_TEXT);
            canvas_rect(&g_bot, mx[i] + 1, my[i] + 1, 38, 28, C_BLUE);
            canvas_hline(&g_bot, mx[i] + 1, my[i] + 10, 38, C_DGREY);
            char b[4];
            snprintf(b, sizeof b, "%d", i + 1);
            canvas_text_center(&g_bot, &font_main, mx[i] + 20, my[i] + 10, b, C_GOLD, C_TEXT);
        }
        if (g_touch_down) {
            for (int i = 0; i < 10; i++)
                if (!done[i] && g_touch_x >= mx[i] && g_touch_x < mx[i] + 40 && g_touch_y >= my[i] && g_touch_y < my[i] + 30) {
                    if (i == next) {
                        done[i] = true;
                        next++;
                        sfx_play(SFX_SELECT);
                    } else {
                        sfx_play(SFX_ERROR);
                        frames -= 60;
                    }
                }
        }
        if (frames % 15 == 0)
            top_panel("Les malles", "Touchez les malles dans l'ordre !", MAX(0, frames / 60), next, 10);
        frame_wait();
        frames--;
    }
    return outro(next >= 10, "Toutes les malles sont dans le train ! La session peut commencer.",
                 "Le train est parti sans les malles. Les députés siégeront en pyjama.");
}

// ================================================================ computer terminals (5 mini-games)
// small helpers shared by the terminal games
static void top_extra(const char *text, u8 col)
{
    ui_text_in(&g_top, &font_main, 8, 136, 240, 22, text, col, C_SHADOW, 0);
}

// word-wrap WITHOUT translation (foreign sample text); returns the y after the last line
static int text_wrap_raw(Canvas *c, const Font *f, int x, int y, int w, const char *s, u8 col, u8 shadow)
{
    while (*s) {
        int n = 0, best = 0;
        while (s[n]) {
            int e = n;
            while (s[e] && s[e] != ' ')
                e++;
            if (font_width_n(f, s, e) > w && best > 0)
                break;
            best = e;
            if (!s[e])
                break;
            n = e + 1;
        }
        if (best == 0)
            best = strlen(s);
        canvas_text_n(c, f, x, y, s, best, col, shadow);
        y += f->line_h;
        s += best;
        while (*s == ' ')
            s++;
    }
    return y;
}

static void shuffle(int *a, int n)
{
    for (int i = n - 1; i > 0; i--) {
        int j = rng_range(i + 1), t = a[i];
        a[i] = a[j];
        a[j] = t;
    }
}

// ---------------------------------------------------------------- courriels: read real mail, bin the spam
static const struct { const char *from, *subj; bool spam; } mails[] = {
    {"Prince Mbeki III", "Héritage de 4 M€ à partager", true},
    {"Lobby du diesel", "Invitation : dîner au homard", true},
    {"Service RH", "Réunion de coordination sur les réunions", true},
    {"SuperPromo", "Votre téléphone gratuit vous attend", true},
    {"Qatar Events", "Une petite valise pour vous ?", true},
    {"Banque Sécurité", "Confirmez votre mot de passe ici", true},
    {"Newsletter", "47 nouveautés passionnantes du RGPD", true},
    {"Roberta Metsola", "Ordre du jour de la plénière", false},
    {"Maman", "Tu manges bien à Bruxelles ?", false},
    {"Cantine", "Menu du jour : waterzooi", false},
    {"Greffe de la Cour", "Arrêt à notifier avant midi", false},
    {"Commission", "Vote du budget demain", false},
    {"Jean Monnet", "Ton Eurodex a été mis à jour", false},
    {"Oliver", "Débat ce soir ? Je vais gagner.", false},
};

static int mg_courriels(void)
{
    intro("Boîte de réception", "437 courriels non lus ! Touchez un vrai courriel pour le lire, et la croix rouge pour jeter un spam. Traitez-en 20 avant que la boîte ne déborde !");
    int q[8], n = 0;
    int score = 0, goal = 20, errors = 0, frames = 40 * 60, spawn = 10, flash = 0;
    bool lost = false, overflow = false;
    while (frames > 0 && score < goal && !lost) {
        if (--spawn <= 0) {
            if (n >= 7) {
                overflow = lost = true;
                break;
            }
            memmove(q + 1, q, n * sizeof q[0]);
            int k;
            do
                k = rng_range(ARRAY_LEN(mails));
            while (n > 0 && k == q[1]);
            q[0] = k;
            n++;
            spawn = 75 - MIN(40, score * 2);
            sfx_play(SFX_SMS);
        }
        canvas_clear(&g_bot, C_PANEL);
        canvas_rect(&g_bot, 0, 0, 256, 16, C_BLUE);
        ui_text_in(&g_bot, &font_small, 0, 0, 200, 16, "Boîte de réception", C_WHITE, 0, -1);
        char buf[16];
        snprintf(buf, sizeof buf, "%d / 7", n);
        canvas_text_right(&g_bot, &font_small, 250, 3, buf, n >= 6 ? C_YELLOW : C_WHITE, 0);
        for (int i = 0; i < n; i++) {
            int y = 18 + i * 24;
            canvas_rect(&g_bot, 2, y, 252, 22, C_DGREY);
            canvas_rect(&g_bot, 3, y + 1, 214, 20, C_WHITE);
            ui_text_in(&g_bot, &font_small, 3, y, 214, 11, mails[q[i]].from, C_BLUE, 0, -1);
            ui_text_in(&g_bot, &font_small, 3, y + 10, 214, 11, mails[q[i]].subj, C_TEXT, 0, -1);
            canvas_rect(&g_bot, 219, y + 1, 34, 20, C_RED);
            for (int d = 0; d < 10; d++) {   // white cross
                canvas_rect(&g_bot, 231 + d, y + 6 + d, 2, 1, C_WHITE);
                canvas_rect(&g_bot, 240 - d, y + 6 + d, 2, 1, C_WHITE);
            }
        }
        if (flash > 0) {
            flash--;
            canvas_box(&g_bot, 0, 0, 256, 192, C_RED);
            canvas_box(&g_bot, 1, 1, 254, 190, C_RED);
        }
        if (g_touch_down && g_touch_y >= 18) {
            int i = (g_touch_y - 18) / 24;
            if (i < n) {
                bool trash = g_touch_x >= 218;
                if (trash == mails[q[i]].spam) {
                    score++;
                    sfx_play(trash ? SFX_PAPER : SFX_SELECT);
                } else {
                    errors++;
                    flash = 20;
                    sfx_play(SFX_ERROR);
                    if (errors >= 3)
                        lost = true;
                }
                memmove(q + i, q + i + 1, (n - i - 1) * sizeof q[0]);
                n--;
            }
        }
        if (frames % 15 == 0 || flash == 19) {
            top_panel("Boîte de réception", "Lire : touchez · Spam : croix rouge", frames / 60, score, goal);
            snprintf(buf, sizeof buf, T("Erreurs : %d / 3"), errors);
            top_extra(buf, errors ? C_RED : C_TEXT);
        }
        frame_wait();
        frames--;
    }
    return outro(!lost && score >= goal, "Boîte vide ! Pour la première fois depuis 2019. Savourez, ça ne durera pas.",
                 overflow ? "La boîte déborde ! Le serveur de la Commission vient de planter. Encore."
                          : "Vous avez jeté le courriel de la présidente et répondu au prince. Ça arrive aux meilleurs.");
}

// ---------------------------------------------------------------- désinfox: true or false about the EU
static const struct { const char *q, *why; bool vrai; } intox[] = {
    {"Depuis 2024, les nouveaux téléphones vendus dans l'UE doivent avoir un port USB-C.",
     "Vrai : la directive sur le chargeur universel s'applique depuis fin 2024.", true},
    {"L'UE interdit de vendre des bananes trop courbées.",
     "Faux : un règlement de 1994 classait les bananes par qualité. Les courbées restent en vente.", false},
    {"Le drapeau européen a 12 étoiles parce qu'il y avait 12 pays membres.",
     "Faux : 12 est un symbole de perfection. Le drapeau date de 1955, bien avant les 12 pays.", false},
    {"Le Parlement européen siège une semaine par mois à Strasbourg.",
     "Vrai : 12 sessions par an à Strasbourg, avec les malles qui vont avec.", true},
    {"Les commissaires européens sont élus directement par les citoyens.",
     "Faux : ils sont proposés par les gouvernements puis approuvés par le Parlement.", false},
    {"L'Union européenne compte 24 langues officielles.",
     "Vrai : de l'irlandais au maltais, tous les textes sont traduits dans les 24.", true},
    {"Tous les pays de l'UE utilisent l'euro.",
     "Faux : en 2026, 21 pays sur 27 l'utilisent. La Bulgarie est la dernière arrivée.", false},
    {"Les frais d'itinérance mobile ont été supprimés dans l'UE en 2017.",
     "Vrai : depuis juin 2017, on appelle partout « comme à la maison ».", true},
    {"L'hymne européen est l'Ode à la joie de Beethoven.",
     "Vrai : sans paroles officielles, pour ne fâcher aucune langue.", true},
    {"Le Luxembourg est le plus petit pays de l'UE.",
     "Faux : c'est Malte, environ 316 km².", false},
    {"L'Union européenne a reçu le prix Nobel de la paix.",
     "Vrai : en 2012, pour 60 ans de paix et de réconciliation.", true},
    {"Le RGPD protège les données personnelles depuis 2018.",
     "Vrai : il s'applique depuis le 25 mai 2018. D'où les bandeaux cookies…", true},
    {"Les concombres tordus sont interdits à la vente dans l'UE.",
     "Faux : la norme sur leur courbure a été supprimée en 2009.", false},
    {"Les bouchons doivent rester attachés aux bouteilles en plastique.",
     "Vrai : obligatoire depuis juillet 2024, pour qu'ils ne finissent plus dans la nature.", true},
    {"La Suisse est membre de l'Union européenne.",
     "Faux : elle est dans l'espace Schengen, mais pas dans l'UE.", false},
    {"La Banque centrale européenne a son siège à Bruxelles.",
     "Faux : elle est à Francfort, en Allemagne.", false},
};

static int mg_desinfox(void)
{
    intro("Désinfox", "Les rumeurs sur l'Europe circulent plus vite que les directives ! Pour chaque affirmation, touchez VRAI ou FAUX. Il faut 7 bonnes réponses sur 10.");
    int order[ARRAY_LEN(intox)];
    for (unsigned i = 0; i < ARRAY_LEN(intox); i++)
        order[i] = i;
    shuffle(order, ARRAY_LEN(intox));
    int score = 0;
    char buf[48];
    for (int qi = 0; qi < 10; qi++) {
        int k = order[qi], t = 12 * 60, ans = -1;
        ui_backdrop(&g_bot);
        canvas_frame(&g_bot, 6, 6, 244, 110, FRAME_DIALOG);
        ui_text_wrapped(&g_bot, &font_main, 16, 14, 224, intox[k].q, C_TEXT, C_SHADOW);
        ui_button(&g_bot, 10, 128, 112, 54, "VRAI", BTN_GREEN, &font_main);
        ui_button(&g_bot, 134, 128, 112, 54, "FAUX", BTN_RED, &font_main);
        while (t > 0 && ans < 0) {
            canvas_bar(&g_bot, 16, 108, 224, 5, t, 12 * 60, t < 180 ? C_RED : C_GOLD);
            if (touch_in(10, 128, 112, 54) || (g_kdown & KEY_LEFT))
                ans = 1;
            if (touch_in(134, 128, 112, 54) || (g_kdown & KEY_RIGHT))
                ans = 0;
            if (t % 15 == 0 || t == 12 * 60) {
                top_panel("Désinfox", "Vrai ou faux ?", t / 60, score, 7);
                snprintf(buf, sizeof buf, T("Question %d / 10"), qi + 1);
                top_extra(buf, C_TEXT);
            }
            frame_wait();
            t--;
        }
        bool ok = ans >= 0 && ans == (int)intox[k].vrai;
        if (ok)
            score++;
        sfx_play(ok ? SFX_SELECT : SFX_ERROR);
        ui_backdrop(&g_bot);
        canvas_frame(&g_bot, 6, 6, 244, 180, FRAME_DIALOG);
        ui_text_in(&g_bot, &font_main, 6, 10, 244, 22, ok ? "Bonne réponse !" : ans < 0 ? "Trop tard !" : "Raté !",
                   ok ? C_GREEN : C_RED, C_SHADOW, 0);
        ui_text_wrapped(&g_bot, &font_main, 16, 40, 224, intox[k].why, C_TEXT, C_SHADOW);
        ui_text_in(&g_bot, &font_small, 6, 166, 244, 14, "Touchez pour continuer", C_MGREY, 0, 0);
        top_panel("Désinfox", "Vrai ou faux ?", MAX(0, t / 60), score, 7);
        for (int w = 0; w < 420; w++) {
            frame_wait();
            if (w > 20 && input_confirm())
                break;
        }
    }
    return outro(score >= 7, "Bravo ! Toutes ces intox sont démontées. Les fact-checkeurs veulent vous recruter.",
                 "Trop d'intox ont circulé… Le compte « VraieEurope2027 » gagne 10 000 abonnés.");
}

// ---------------------------------------------------------------- langues: route each message to the right booth
extern const char *const g_mg_lang_msgs[24][2];
static const char *const lang_names[24] = {
    N_("Bulgare"), N_("Tchèque"), N_("Danois"), N_("Allemand"), N_("Grec"), N_("Anglais"), N_("Espagnol"),
    N_("Estonien"), N_("Finnois"), N_("Français"), N_("Irlandais"), N_("Croate"), N_("Hongrois"), N_("Italien"),
    N_("Lituanien"), N_("Letton"), N_("Maltais"), N_("Néerlandais"), N_("Polonais"), N_("Portugais"),
    N_("Roumain"), N_("Slovaque"), N_("Slovène"), N_("Suédois")};
// look-alike groups, so the wrong booths are tempting: slavic, germanic, romance, finno-ugric, baltic, misc
static const u8 lang_family[24] = {0, 0, 1, 1, 6, 5, 2, 3, 3, 2, 5, 0, 3, 2, 4, 4, 5, 1, 0, 2, 2, 0, 0, 1};

static int mg_langues(void)
{
    intro("Service de traduction", "Des messages arrivent de toute l'Europe ! Lisez chacun et envoyez-le à la bonne cabine de traduction. 12 messages en 45 secondes. Une erreur coûte 3 secondes !");
    int score = 0, goal = 12, frames = 45 * 60;
    while (frames > 0 && score < goal) {
        int correct = rng_range(24), opts[6], n = 1;
        const char *msg = g_mg_lang_msgs[correct][rng_range(2)];
        opts[0] = correct;
        for (int tries = 0; tries < 200 && n < 6; tries++) {
            int c = rng_range(24);
            bool dup = false;
            for (int i = 0; i < n; i++)
                dup |= opts[i] == c;
            // the first two decoys come from the same family when possible
            if (dup || (n < 3 && tries < 100 && lang_family[c] != lang_family[correct]))
                continue;
            opts[n++] = c;
        }
        shuffle(opts, 6);
        int chosen = -1, fb = 0;
        bool redraw = true;
        while (frames > 0) {
            if (redraw) {
                redraw = false;
                ui_backdrop(&g_bot);
                ui_text_in(&g_bot, &font_small, 0, 2, 256, 16, "Cabines de traduction", C_GOLD, C_INK, 0);
                for (int i = 0; i < 6; i++) {
                    BtnStyle st = BTN_NORMAL;
                    if (chosen >= 0 && opts[i] == correct)
                        st = BTN_GREEN;
                    else if (i == chosen)
                        st = BTN_RED;
                    ui_button(&g_bot, 8 + (i & 1) * 124, 22 + (i >> 1) * 56, 116, 48, lang_names[opts[i]], st, &font_main);
                }
            }
            if (frames % 15 == 0 || fb == 0) {
                top_panel("Service de traduction", "Envoyez le message à la bonne cabine", frames / 60, score, goal);
                canvas_frame(&g_top, 8, 132, 240, 58, FRAME_DIALOG);
                const Font *f = font_width(&font_main, msg) > 440 ? &font_small : &font_main;
                text_wrap_raw(&g_top, f, 18, 140, 220, msg, C_TEXT, C_SHADOW);
                if (fb == 0)
                    fb = -1;
            }
            if (chosen >= 0) {
                if (++fb > 30)
                    break;
            } else if (g_touch_down) {
                for (int i = 0; i < 6; i++)
                    if (touch_in(8 + (i & 1) * 124, 22 + (i >> 1) * 56, 116, 48)) {
                        chosen = i;
                        fb = 1;
                        redraw = true;
                        if (opts[i] == correct) {
                            score++;
                            sfx_play(SFX_SELECT);
                        } else {
                            frames -= 180;
                            sfx_play(SFX_ERROR);
                        }
                    }
            }
            frame_wait();
            frames--;
        }
    }
    return outro(score >= goal, "Tous les messages sont arrivés à bon port ! La DG Traduction vous propose un poste. En 24 langues.",
                 "Un message slovaque est parti chez les Slovènes… L'incident diplomatique est en cours de traduction.");
}

// ---------------------------------------------------------------- taux: keep inflation near 2 %
static void fmt_pct(char *out, int n, int bp)
{
    snprintf(out, n, "%s%d,%02d %%", bp < 0 ? "-" : "", abs(bp) / 100, abs(bp) % 100);
}

static const struct { const char *text; int delta; } chocs[] = {
    {"Crise énergétique ! Les prix s'envolent.", 300},
    {"Confinement : plus personne n'achète rien.", -250},
    {"Plan de relance géant voté cette nuit !", 220},
    {"Krach boursier à Francfort !", -200},
    {"Pénurie de puces électroniques !", 160},
    {"Les ménages épargnent tout leur argent.", -150},
};

static int mg_taux(void)
{
    intro("Taux directeur", "Vous présidez la BCE ! L'inflation grimpe ? Montez le taux. Elle chute ? Baissez-le. Gardez-la dans la zone verte (autour de 2 %) au moins la moitié du temps. 40 secondes !");
    enum { HN = 232 };
    s16 hist[HN];
    int hn = 0;
    int infl = 200, rate = 200, press = 200, frames = 40 * 60, total = frames, inband = 0, news = 0, ev = 0;
    int order[ARRAY_LEN(chocs)];
    for (unsigned i = 0; i < ARRAY_LEN(chocs); i++)
        order[i] = i;
    shuffle(order, ARRAY_LEN(chocs));
    char buf[48], v[16];
    while (frames > 0) {
        int t = total - frames;
        if (t > 0 && t % (8 * 60) == 0 && ev < 4) {
            press += chocs[order[ev]].delta;
            news = ev + 1;
            ev++;
            sfx_play(SFX_ALARM);
        }
        if ((frames & 3) == 0) {
            press = CLAMP(press + rng_range(9) - 4, -200, 900);
            infl = CLAMP(infl + (press - rate) / 64 + rng_range(5) - 2, -300, 1500);
        }
        if (infl >= 150 && infl <= 250)
            inband++;
        if ((frames & 7) == 0) {
            if (hn < HN)
                hist[hn++] = infl;
            else {
                memmove(hist, hist + 1, (HN - 1) * sizeof hist[0]);
                hist[HN - 1] = infl;
            }
        }
        if (touch_in(8, 146, 116, 42) || (g_kdown & (KEY_DOWN | KEY_LEFT))) {
            rate = MAX(-50, rate - 25);
            sfx_play(SFX_STATDOWN);
        }
        if (touch_in(132, 146, 116, 42) || (g_kdown & (KEY_UP | KEY_RIGHT))) {
            rate = MIN(1000, rate + 25);
            sfx_play(SFX_STATUP);
        }
        // graph: -2 % .. +8 %
#define TY(bp) (124 - (CLAMP(bp, -200, 800) + 200) * 112 / 1000)
        canvas_clear(&g_bot, C_PANEL);
        canvas_rect(&g_bot, 8, 8, 240, 120, C_TEXT);
        canvas_rect(&g_bot, 12, TY(250), 232, TY(150) - TY(250) + 1, C_TYPE0 + 5);
        canvas_hline(&g_bot, 12, TY(0), 232, C_DGREY);
        canvas_hline(&g_bot, 12, TY(200), 232, C_GREEN);
        for (int i = 1; i < hn; i++) {
            int y0 = TY(hist[i - 1]), y1 = TY(hist[i]);
            canvas_vline(&g_bot, 12 + i, MIN(y0, y1), abs(y1 - y0) + 1, C_YELLOW);
        }
        canvas_text(&g_bot, &font_small, 14, 10, "8 %", C_MGREY, 0);
        canvas_text(&g_bot, &font_small, 14, TY(0) - 11, "0 %", C_MGREY, 0);
        fmt_pct(v, sizeof v, infl);
        snprintf(buf, sizeof buf, T("Inflation : %s"), v);
        ui_text_in(&g_bot, &font_small, 8, 129, 120, 16, buf, infl >= 150 && infl <= 250 ? C_GREEN : C_RED, 0, -1);
        fmt_pct(v, sizeof v, rate);
        snprintf(buf, sizeof buf, T("Taux : %s"), v);
        ui_text_in(&g_bot, &font_small, 128, 129, 120, 16, buf, C_BLUE, 0, 1);
        ui_button(&g_bot, 8, 146, 116, 42, "Baisser", BTN_NORMAL, &font_main);
        ui_button(&g_bot, 132, 146, 116, 42, "Monter", BTN_NORMAL, &font_main);
#undef TY
        if (frames % 15 == 0) {
            int pct = inband * 100 / MAX(1, t + 1);
            top_panel("Taux directeur", "Objectif : la moitié du temps dans le vert", frames / 60, pct, -50);
            if (news && t - (ev * 8 * 60) < 4 * 60)
                top_extra(chocs[order[news - 1]].text, C_RED);
        }
        frame_wait();
        frames--;
    }
    int pct = inband * 100 / total;
    return outro(pct >= 50, "Inflation maîtrisée ! Les marchés applaudissent, les épargnants dorment tranquilles.",
                 "L'inflation vous a échappé… Le prix du café à la cantine vient de doubler.");
}

// ---------------------------------------------------------------- usb-c: bring old devices into line
static const char *const ports[5] = {"USB-C", N_("Micro-USB"), N_("Lightning"), N_("Mini-USB"), N_("Dock 30")};

static void draw_port(int cx, int y, int type)
{
    switch (type) {
    case 0: // USB-C: small rounded oval
        canvas_rect(&g_bot, cx - 6, y, 12, 5, C_LGREY);
        canvas_pixel(&g_bot, cx - 6, y, C_DGREY); canvas_pixel(&g_bot, cx + 5, y, C_DGREY);
        canvas_pixel(&g_bot, cx - 6, y + 4, C_DGREY); canvas_pixel(&g_bot, cx + 5, y + 4, C_DGREY);
        canvas_hline(&g_bot, cx - 3, y + 2, 6, C_TEXT);
        break;
    case 1: // micro: trapezoid
        canvas_hline(&g_bot, cx - 6, y, 12, C_LGREY);
        canvas_hline(&g_bot, cx - 5, y + 1, 10, C_LGREY);
        canvas_hline(&g_bot, cx - 4, y + 2, 8, C_LGREY);
        break;
    case 2: // lightning: thin gold blade
        canvas_rect(&g_bot, cx - 4, y, 8, 3, C_GOLD);
        break;
    case 3: // mini: chunky trapezoid
        canvas_rect(&g_bot, cx - 5, y, 10, 3, C_LGREY);
        canvas_hline(&g_bot, cx - 3, y + 3, 6, C_LGREY);
        break;
    default: // 30-pin: wide slot
        canvas_rect(&g_bot, cx - 12, y, 24, 3, C_LGREY);
        break;
    }
}

static int mg_usbc(void)
{
    intro("Chargeur universel", "Depuis 2024, l'USB-C est obligatoire ! Touchez les appareils qui ont encore un vieux port pour les mettre en conformité. Surtout pas ceux en USB-C ! 20 appareils en 30 secondes.");
    int type[9], life[9], ok[9];
    for (int i = 0; i < 9; i++)
        life[i] = ok[i] = 0;
    int score = 0, goal = 20, errors = 0, frames = 30 * 60, spawn = 20;
    bool lost = false;
    char buf[32];
    while (frames > 0 && score < goal && !lost) {
        if (--spawn <= 0) {
            int s = rng_range(9);
            for (int k = 0; k < 9 && (life[s] || ok[s]); k++)
                s = (s + 1) % 9;
            if (!life[s] && !ok[s]) {
                type[s] = rng_range(10) < 4 ? 0 : 1 + rng_range(4);
                life[s] = 110 - MIN(50, score * 3);
            }
            spawn = 30 - MIN(14, score);
        }
        ui_backdrop(&g_bot);
        for (int i = 0; i < 9; i++) {
            int cx = 48 + (i % 3) * 80, y = 4 + (i / 3) * 63;
            canvas_rect(&g_bot, cx - 26, y + 50, 52, 8, C_NAVY1);
            if (ok[i]) {
                ok[i]--;
                canvas_rect(&g_bot, cx - 26, y, 52, 56, C_INK);
                canvas_rect(&g_bot, cx - 25, y + 1, 50, 54, C_GREEN);
                ui_text_in(&g_bot, &font_main, cx - 26, y + 16, 52, 22, "USB-C", C_WHITE, C_INK, 0);
                continue;
            }
            if (!life[i])
                continue;
            life[i]--;
            canvas_rect(&g_bot, cx - 26, y, 52, 56, C_INK);
            canvas_rect(&g_bot, cx - 25, y + 1, 50, 54, C_DGREY);
            canvas_rect(&g_bot, cx - 22, y + 5, 44, 38, life[i] < 25 && (life[i] & 4) ? C_RED_D : C_BLUE_L);
            ui_text_in(&g_bot, &font_small, cx - 22, y + 16, 44, 16, ports[type[i]], C_INK, 0, 0);
            draw_port(cx, y + 47, type[i]);
        }
        if (g_touch_down) {
            for (int i = 0; i < 9; i++) {
                int cx = 48 + (i % 3) * 80, y = 4 + (i / 3) * 63;
                if (!life[i] || !touch_in(cx - 28, y - 2, 56, 60))
                    continue;
                if (type[i] == 0) {
                    errors++;
                    sfx_play(SFX_ERROR);
                    if (errors >= 3)
                        lost = true;
                } else {
                    score++;
                    ok[i] = 20;
                    sfx_play(SFX_STAMP);
                }
                life[i] = 0;
            }
        }
        if (frames % 15 == 0) {
            top_panel("Chargeur universel", "Touchez les vieux ports, pas l'USB-C !", frames / 60, score, goal);
            snprintf(buf, sizeof buf, T("Erreurs : %d / 3"), errors);
            top_extra(buf, errors ? C_RED : C_TEXT);
        }
        frame_wait();
        frames--;
    }
    return outro(!lost && score >= goal, "Tous conformes ! Un seul chargeur pour tout le monde. Les tiroirs de câbles d'Europe respirent.",
                 lost ? "Vous avez « mis en conformité » un appareil déjà en USB-C. Il a maintenant trois adaptateurs."
                      : "Trop de vieux câbles ont échappé à la directive… Le tiroir à câbles déborde.");
}

int minigame_run(int id)
{
    music_pause(false);
    char prev[24];
    strncpy(prev, music_current(), sizeof prev - 1);
    prev[sizeof prev - 1] = 0;
    gfx_brightness(false, 0);
    gfx_brightness(true, 0);
    int r;
    switch (id) {
    case MG_VOTE: r = mg_vote(); break;
    case MG_TAMPON: case MG_SIGNATURE: r = mg_tampon(); break;
    case MG_COOKIES: r = mg_cookies(); break;
    case MG_SOMMET: r = mg_sommet(); break;
    case MG_LANGUES: r = mg_langues(); break;
    case MG_COURRIELS: r = mg_courriels(); break;
    case MG_DESINFOX: r = mg_desinfox(); break;
    case MG_TAUX: r = mg_taux(); break;
    case MG_USBC: r = mg_usbc(); break;
    case MG_MALLES: default: r = mg_malles(); break;
    }
    if (prev[0])
        music_play(prev);
    return r;
}
