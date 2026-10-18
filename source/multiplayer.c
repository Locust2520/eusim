// Shared relay transport. Hardware uses DSWifi TCP; the webpage services a RAM mailbox.
#include "multiplayer.h"
#include "local_link.h"
#include "battle.h"
#include "scenes.h"
#include "dialog.h"
#include "input.h"
#include "ui.h"
#include "gfx.h"
#include "save.h"
#include "world.h"
#include "actor.h"
#include "gen/font_data.h"
#include "gen/link_build.h"
#include "lang.h"
#include <dswifi9.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <arpa/inet.h>
#include <errno.h>
#include <stddef.h>

// Layout is part of the browser ABI. Signature is written only at runtime.
// Browser writes rx then rx_ready; ROM writes tx then tx_ready. Each side owns its flag.
typedef struct {
    u32 magic[4];
    u32 heartbeat, active, generation, disconnected;
    u32 tx_ready, rx_ready;
    u8 tx[LINK_PACKET], rx[LINK_PACKET];
    u32 browser;
} Mailbox;
static volatile Mailbox mailbox __attribute__((aligned(32)));
_Static_assert(offsetof(Mailbox, tx) == 40, "Mailbox ABI");
static bool active, healthy, web_mode, wifi_initialized, local_mode, wifi_local_only, wifi_dsi;
static int sock = -1, seat;
static u32 seed, sequence, generation;
static char error_text[320];
static bool waiting;
static u32 wait_frame;
static int lobby_mode;
static char room_name[48] = "", room_pin[7] = "000000";
static const char *const server_errors[] = {
    "Réponse du serveur invalide.", "Réponse du serveur invalide.",
    "Demande de salon invalide.", "Ce nom de salon est déjà utilisé.",
    "Salon introuvable.", "Code PIN incorrect.", "Ce salon est complet.",
    "Les versions du jeu sont différentes.", "Le serveur est complet.",
    "L'autre joueur a quitté le débat.", "Le salon a expiré.",
    "Les débats ne sont plus synchronisés.", "Échange de débat invalide.",
    "Réponse du serveur invalide.", "Le serveur a été arrêté."
};

// A live host acknowledges this mailbox even while multiplayer is idle.
static void heartbeat(void) { mailbox.heartbeat++; }
void multiplayer_init(void)
{
    memset((void *)&mailbox, 0, sizeof mailbox);
    mailbox.magic[0] = 0x49535545; mailbox.magic[1] = 0x494c2d4d;
    mailbox.magic[2] = 0x562d4b4e; mailbox.magic[3] = 0x21323030;
    frame_hook_add(heartbeat);
}

static void star(int cx, int cy, int radius)
{
    int x[10], y[10];
    for (int k = 0; k < 10; k++) {
        int a = k * 32768 / 10, r = k & 1 ? radius * 2 / 5 : radius;
        x[k] = cx + (sinLerp(a) * r >> 12); y[k] = cy - (cosLerp(a) * r >> 12);
    }
    for (int row = cy - radius; row <= cy + radius; row++) {
        int hits[10], n = 0;
        for (int k = 0, j = 9; k < 10; j = k++)
            if ((y[k] > row) != (y[j] > row))
                hits[n++] = x[k] + (row - y[k]) * (x[j] - x[k]) / (y[j] - y[k]);
        for (int k = 0; k < n; k++) for (int j = k + 1; j < n; j++)
            if (hits[k] > hits[j]) { int a = hits[k]; hits[k] = hits[j]; hits[j] = a; }
        for (int k = 0; k + 1 < n; k += 2) canvas_hline(&g_top, hits[k], row, hits[k+1] - hits[k] + 1, C_GOLD);
    }
}

static void draw_waiting(void)
{
    int t = (g_frame - wait_frame) % 120;
    canvas_clear(&g_top, C_BLUE);
    for (int k = 0; k < 12; k++) {
        int a = k * 32768 / 12;
        int radius = 6;
        // Twelve successive zooms within one second, then one second at rest.
        if (t < 60 && t / 5 == k) radius += (2 - abs(t % 5 - 2)) * 2;
        star(128 + (sinLerp(a) * 64 >> 12), 96 - (cosLerp(a) * 64 >> 12), radius);
    }
    ui_backdrop(&g_bot);
    ui_text_in(&g_bot, &font_main, 4, 20, 248, 35, "En attente de joueurs…", C_GOLD, C_INK, 0);
    if (lobby_mode == 3) {
        ui_text_in(&g_bot, &font_small, 8, 68, 240, 38, "Sans routeur ni serveur.", C_WHITE, C_INK, 0);
    } else if (lobby_mode == 2) {
        ui_text_in(&g_bot, &font_small, 8, 68, 240, 38, "Recherche toutes les 10 secondes.", C_WHITE, C_INK, 0);
    } else {
        ui_text_in(&g_bot, &font_main, 8, 65, 240, 28, room_name, C_WHITE, C_INK, 0);
        char label[80]; snprintf(label, sizeof label, T("Code PIN : %s"), room_pin);
        ui_text_in(&g_bot, &font_main, 8, 97, 240, 28, label, C_GOLD, C_INK, 0);
    }
    ui_button(&g_bot, 50, 146, 156, 34, "Annuler (B)", BTN_DARK, &font_main);
}

bool link_active(void) { return active; }
bool link_ok(void) { return active && healthy && (!web_mode || !mailbox.disconnected) && (!local_mode || local_link_ok()); }
int link_seat(void) { return seat; }
u32 link_seed(void) { return seed; }

void link_close(void)
{
    active = false;
    mailbox.active = 0;
    waiting = false;
    if (sock >= 0) { closesocket(sock); sock = -1; }
    if (wifi_initialized && local_mode) {
        local_link_close();
        if (wifi_local_only) {
            Wifi_DisableWifi(); frame_wait(); frame_wait();
            if (Wifi_Deinit()) wifi_initialized = wifi_local_only = false;
        }
    } else if (wifi_initialized) Wifi_DisconnectAP();
    local_mode = false;
}

static bool failed(const char *s)
{
    snprintf(error_text, sizeof error_text, "%s", T(s));
    healthy = false;
    return false;
}

// Called only from synchronous wait loops, never from IRQs or frame hooks.
static bool wait_step(u32 start, int seconds)
{
    if (waiting) draw_waiting();
    frame_wait();
    if ((g_kdown & KEY_B) || (waiting && touch_in(50, 146, 156, 34))) return failed("Débat annulé.");
    if (g_frame - start > (u32)seconds * 60) return failed("Le serveur ne répond plus.");
    if (web_mode && mailbox.disconnected) return failed("Connexion au serveur interrompue.");
    return true;
}

static bool transfer(u8 *packet, bool sending)
{
    u32 start = g_frame;
    if (web_mode) {
        if (sending) {
            while (mailbox.tx_ready) if (!wait_step(start, 300)) return false;
            for (int i = 0; i < LINK_PACKET; i++) mailbox.tx[i] = packet[i];
            mailbox.tx_ready = 1;
        } else {
            while (!mailbox.rx_ready) if (!wait_step(start, 300)) return false;
            for (int i = 0; i < LINK_PACKET; i++) packet[i] = mailbox.rx[i];
            mailbox.rx_ready = 0;
        }
        return true;
    }
    int at = 0;
    while (at < LINK_PACKET) {
        int n = sending ? send(sock, packet + at, LINK_PACKET - at, 0) : recv(sock, packet + at, LINK_PACKET - at, 0);
        if (n > 0) at += n;
        else if (n == 0) return failed("L'autre joueur a quitté le débat.");
        else if (errno != EWOULDBLOCK && errno != EAGAIN && errno != EINPROGRESS)
            return failed("Connexion au serveur interrompue.");
        if (at < LINK_PACKET && !wait_step(start, 300)) return false;
    }
    return true;
}

static void put32(u8 *b, u32 v)
{
    for (int i = 0; i < 4; i++) b[i] = v >> (8 * i);
}
static u32 get32(const u8 *b)
{
    return (u32)b[0] | (u32)b[1] << 8 | (u32)b[2] << 16 | (u32)b[3] << 24;
}
static void init_packet(u8 *b, int type, int length)
{
    memset(b, 0, LINK_PACKET); memcpy(b, "EUL1", 4);
    b[4] = 2; b[5] = type; b[6] = length; b[7] = length >> 8;
}
static bool read_packet(u8 *b)
{
    if (!transfer(b, false)) return false;
    int n = b[6] | b[7] << 8;
    if (memcmp(b, "EUL1", 4) || b[4] != 2 || n > 248) return failed("Réponse du serveur invalide.");
    if (b[5] == 5) {
        int code = n == 1 ? b[8] : 0;
        return failed(server_errors[code < ARRAY_LEN(server_errors) ? code : 0]);
    }
    return true;
}

bool link_exchange(int kind, const void *out, int size, void *in, int *received)
{
    u8 packet[LINK_PACKET];
    if (!link_ok() || size < 0 || size > LINK_BODY) return false;
    if (local_mode) {
        dlg_say_nowait("", "En attente de l'autre joueur… B : annuler");
        bool ok = local_link_exchange(kind,out,size,in,received);
        if (!ok) return failed(local_link_error());
        dlg_close(); return true;
    }
    init_packet(packet, 4, size + 5);
    put32(packet + 8, sequence); packet[12] = kind;
    memcpy(packet + 13, out, size);
    dlg_say_nowait("", "En attente de l'autre joueur… B : annuler");
    if (!transfer(packet, true) || !read_packet(packet)) return false;
    int n = (packet[6] | packet[7] << 8) - 5;
    if (packet[5] != 4 || n < 0 || n > LINK_BODY || get32(packet + 8) != sequence || packet[12] != kind)
        return failed("Les débats ne sont plus synchronisés.");
    memcpy(in, packet + 13, n); *received = n; sequence++;
    dlg_close();
    return true;
}

// Numeric editor also works without a stylus; keyboard_input() only has letters.
static bool edit_number(const char *title, char *value, int width, bool dots)
{
    int cursor = 0;
    while (1) {
        ui_backdrop(&g_bot);
        ui_header(&g_bot, 4, 4, 248, title);
        int x = (256 - width * 16) / 2;
        for (int i = 0; i < width; i++) {
            char digit[2] = {value[i], 0};
            canvas_frame(&g_bot, x + i * 16, 45, 16, 30, i == cursor ? FRAME_SELECT : FRAME_MENU);
            ui_text_in(&g_bot, &font_main, x + i * 16, 46, 16, 28, digit, C_TEXT, C_SHADOW, 0);
        }
        ui_text_in(&g_bot, &font_small, 4, 102, 248, 20, "←→ : position    ↑↓ : chiffre", C_TEXT, 0, 0);
        ui_button(&g_bot, 4, 140, 116, 36, "Valider (A)", BTN_NORMAL, &font_main);
        ui_button(&g_bot, 136, 140, 116, 36, "Annuler (B)", BTN_DARK, &font_main);
        frame_wait();
        for (int i = 0; i < width; i++)
            if (value[i] != '.' && touch_in(x + i * 16, 45, 16, 30)) cursor = i;
        if (g_krep & KEY_LEFT) { do { cursor = (cursor + width - 1) % width; } while (dots && value[cursor] == '.'); }
        if (g_krep & KEY_RIGHT) { do { cursor = (cursor + 1) % width; } while (dots && value[cursor] == '.'); }
        if (g_krep & KEY_UP) value[cursor] = '0' + (value[cursor] - '0' + 1) % 10;
        if (g_krep & KEY_DOWN) value[cursor] = '0' + (value[cursor] - '0' + 9) % 10;
        if ((g_kdown & KEY_A) || touch_in(4, 140, 116, 36)) return true;
        if ((g_kdown & KEY_B) || touch_in(136, 140, 116, 36)) return false;
    }
}

static bool prepare_wifi(bool nearby)
{
    if (wifi_initialized && nearby && wifi_dsi)
        return failed("Redémarrez le jeu pour changer de mode Wi-Fi.");
    if (wifi_initialized && !nearby && wifi_local_only)
        return failed("Redémarrez le jeu pour changer de mode Wi-Fi.");
    if (!wifi_initialized) {
        unsigned flags = INIT_ONLY | (nearby ? WIFI_LOCAL_ONLY : WIFI_ATTEMPT_DSI_MODE);
        if (!Wifi_InitDefault(flags)) return failed("Impossible d'initialiser le Wi-Fi.");
        wifi_initialized = true; wifi_local_only = nearby; wifi_dsi = !nearby && isDSiMode();
    }
    if (!nearby) {
        Wifi_InternetMode(); u32 start=g_frame;
        while (!Wifi_LibraryModeReady()) if (!wait_step(start,10)) return false;
    }
    return true;
}

static bool native_connect(void)
{
    dlg_say_nowait("", isDSiMode() ? "Connexion Wi-Fi DSi… B : annuler" : "Connexion Wi-Fi DS… B : annuler");
    if (!prepare_wifi(false)) return false;
    Wifi_AutoConnect();
    u32 start = g_frame;
    while (Wifi_AssocStatus() != ASSOCSTATUS_ASSOCIATED) {
        if (Wifi_AssocStatus() == ASSOCSTATUS_CANNOTCONNECT || g_frame - start > 30 * 60) return failed(isDSiMode()
                ? "Wi-Fi DSi : vérifiez le réseau WPA2 et les réglages de la console."
                : "Mode DS : réseau ouvert/WEP. Pour WPA2, lancez le jeu en mode DSi.");
        if (!wait_step(start, 31)) return false;
    }
    sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) return failed("Impossible de créer la connexion.");
    unsigned long nonblocking = 1;
    if (ioctl(sock, FIONBIO, &nonblocking) < 0) return failed("Impossible de configurer la connexion.");
    struct sockaddr_in target = {0};
    target.sin_family = AF_INET; target.sin_port = htons(24816); target.sin_addr.s_addr = inet_addr("51.68.231.244");
    int r = connect(sock, (struct sockaddr *)&target, sizeof target);
    if (r < 0 && errno != EINPROGRESS && errno != EWOULDBLOCK) return failed("Serveur inaccessible.");
    start = g_frame;
    while (r < 0) {
        fd_set writable; FD_ZERO(&writable); FD_SET(sock, &writable);
        struct timeval tv = {0, 0};
        r = select(sock + 1, NULL, &writable, NULL, &tv);
        if (r < 0) return failed("Serveur inaccessible.");
        if (r > 0) {
            int err = 0; socklen_t len = sizeof err;
            if (getsockopt(sock, SOL_SOCKET, SO_ERROR, &err, &len) < 0 || err) return failed("Serveur inaccessible.");
            break;
        }
        r = -1;
        if (!wait_step(start, 15)) return false;
    }
    return true;
}

static bool join_room(void)
{
    u8 packet[LINK_PACKET];
    int length = lobby_mode == 2 ? 0 : strlen(room_name), sum = 0;
    for (int i = 0; i < g_save.party_count; i++) sum += g_save.party[i].level;
    int level = sum * 100 / g_save.party_count;
    init_packet(packet, 1, 14 + length); put32(packet + 8, LINK_BUILD);
    packet[12] = lobby_mode; packet[13] = level; packet[14] = level >> 8; packet[15] = length;
    memcpy(packet + 16, lobby_mode == 2 ? "000000" : room_pin, 6);
    memcpy(packet + 22, room_name, length);
    waiting = true; wait_frame = g_frame; dlg_close(); actors_hide_all(); draw_waiting();
    if (!transfer(packet, true)) return false;
    while (1) {
        if (!read_packet(packet)) return false;
        if (packet[5] == 2) continue;
        if (packet[5] != 3 || packet[6] != 5 || packet[7] || packet[8] > 1)
            return failed("Réponse du serveur invalide.");
        seat = packet[8]; seed = get32(packet + 9); sequence = 0; waiting = false; return true;
    }
}

void multiplayer_open(void)
{
    if (!g_save.party_count) { dlg_say("", "Il vous faut une équipe pour débattre."); return; }
    // Detect the browser without asking players to choose their platform.
    u32 start = g_frame;
    while (!mailbox.browser && g_frame - start < 60) frame_wait();
    web_mode = mailbox.browser == 1; local_mode = false; error_text[0] = 0;
    if (!web_mode) {
        static const char *const modes[]={"En ligne", "Sans Internet", "Retour"};
        int mode=dlg_choice(modes,3,true);
        if (mode<0 || mode==2) return;
        if (mode==1) {
            static const char *const nearby[]={"Créer une partie locale", "Rejoindre une partie locale", "Retour"};
            int choice=dlg_choice(nearby,3,true);
            if (choice<0 || choice==2) return;
            lobby_mode=3; active=healthy=true; local_mode=true;
            waiting=true; wait_frame=g_frame; dlg_close(); actors_hide_all(); draw_waiting();
            if (prepare_wifi(true) && local_link_open(choice==0,draw_waiting)) {
                waiting=false; seat=local_link_seat(); seed=local_link_seed();
                battle_multiplayer();
            } else if (!error_text[0]) failed(local_link_error());
            goto finished;
        }
    }
    static const char *const choices[] = {"Créer un salon", "Rejoindre un salon", "Jouer avec tout le monde", "Retour"};
    int c = dlg_choice(choices, 4, true);
    if (c < 0 || c == 3) return;
    lobby_mode = c;
    if (c != 2) {
        if (!keyboard_input(T("Nom du salon"), room_name, sizeof room_name, 20)) return;
        bool nonempty = false;
        for (const char *p = room_name; *p; p++) if (*p != ' ') nonempty = true;
        if (!nonempty) { dlg_say("", "Saisissez un nom de salon."); return; }
        if (!edit_number("Code PIN (6 chiffres)", room_pin, 6, false)) return;
    }
    active = healthy = true;
    mailbox.disconnected = mailbox.tx_ready = mailbox.rx_ready = 0;
    mailbox.generation = ++generation; mailbox.active = web_mode ? 1 : 0;
    bool connected = web_mode || native_connect();
    if (connected && join_room()) {
        dlg_close();
        battle_multiplayer();
    }
finished:
    link_close();
    if (error_text[0]) dlg_say("", error_text);
    dlg_close();
    world_refresh(); gfx_brightness(false, 0); gfx_brightness(true, 0);
}
