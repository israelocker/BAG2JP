/* Online step sync (package bag2jp.feature.netsync, feature "online", option transport).
 *
 * Same model as rhythm-game online play (StepMania/SMOnline) and the BAG1 port's bag.netsync:
 * each PC plays the match itself against its own music clock; only the result of each bar
 * travels. Lag only delays when the rival's bar is applied, never the local player's timing.
 *
 * The match is an ordinary 2-player battle on both PCs. P1 = the PC with the higher random id.
 * Menus (character, difficulty, stage): the other player's button changes arrive and drive their
 * side. Dance: their side gets a neutral pad and each bar is scored from the result they send.
 *
 * Connections (transport):
 *   lan       UDP broadcast on port 47300 with the room code's hash; direct UDP afterwards.
 *   internet  meet through a public MQTT broker (list in bag2jp_online_servers.txt, tried in
 *             order) on topic bag2jp/v1/<room hash>; each side learns its public address with
 *             STUN and both punch UDP holes; until (or unless) a direct path works, packets go
 *             through the broker (relay).
 *   direct    host: line 2 of bag2jp_online.txt empty -> listen on UDP 47100 (port forwarded on
 *             the router); the status line shows the public address to give the other player.
 *             join: line 2 = "ip:port" of the host.
 *   loopback  one PC test: the rival copies the local player's bars.
 * Room code: line 1 of bag2jp_online.txt (MODS > ROOM CODE), default BAG2. Re-read while idle.
 *
 * Match module system/005.dbi (base 0x8008F890), FUN_80099e90, once per bar:
 *   0x8009ABC4 bnez $v0 -> skip, taken while the bar's input window is open. When it opens the
 *     local bar is closed with the game's FUN_800120F8(player, command) and sent with this PC's
 *     score snapshot; the skip is forced (max NS_WAIT_MAX frames) until the other result arrives.
 *   0x8009B084 sw $s1,0x20($v0): per-player join point ($s4 player, judge block 0x8005CF08 +
 *     p*0x24, player block 0x8005E728 + p*0x32). Judge +08 finish time, +0C timing, +0E COOL,
 *     +12 pressed button, +14 result (0 none, bar command id when right, 0x6E attack, 0xAA
 *     dodge); player +02 the bar's command id. Both players are written before scoring.
 *   0x8009A0C0 bnez $v0 -> no beat advance: while a bar is still waiting, the beat that starts the
 *     next bar is held back too (otherwise the waiting bar would be dropped unresolved on one PC
 *     only). Judging uses absolute beat times, so a short hold only delays the next command.
 *   Each STEP carries the sender's COOL and right-bar counts (0x8005E798 / 0x8005E7A8, P1/P2,
 *   updated at once in the resolve loop) at the bar's close; a difference is reported (out of
 *   sync) instead of silently playing two matches. Scores (0x8005E6F8/FC) count up over time,
 *   so they are only logged.
 * Start barrier: when the match module loads, each PC waits (max 5 s) for the other's READY.
 * Log: bag2jp_netsync.log next to the game. */
#include <winsock2.h>
#include <ws2tcpip.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#include <ctype.h>
#include <stdatomic.h>
#include <SDL3/SDL.h>
#include "mod_plugins.h"
#include "cpu_state.h"
#include "host_osd.h"
#include "host_overlay.h"
#include "bag2jp_lobby_ui.h"
#include "bag2jp_lobby_client.h"

int bag2jp_mods_menu_pad_filter(const PSXModPadFrame* in, PSXModPadOutput* out);
void bag2jp_mods_menu_reattach(void);
void bag2jp_charsel_reattach(void);
int bag2jp_charsel_enabled(void);
int bag2jp_charsel_filter_side(int side, const PSXModPadFrame* in, PSXModPadOutput* out);
uint32_t bag2jp_bag1_content_id(void);
void bag2jp_bag1_online(int linked);
void bag2jp_bag1_force_stock(int on);
void bag2jp_bag1_set_version(int chr, int side, int v);

#define NS_SITE       0x8009B084u   /* sw $s1, 0x20($v0) */
#define NS_WORD       0xAC510020u
#define NS_GATE       0x8009ABC4u   /* bnez $v0, skip */
#define NS_GATE_WORD  0x144005C8u
#define NS_ADVANCE    0x8009A0C0u   /* bnez $v0, no-advance: beat time not reached yet */
#define NS_ADVANCE_WORD 0x1440002Cu
#define NS_BEAT       0x8005E2D0u   /* h: beat counter (a bar starts every 4 beats) */
#define NS_BAR_DONE   0x8005E711u   /* b: 1 once the current bar has been resolved */
#define NS_FN_CLOSE   0x800120F8u   /* close a human player's bar: (player, command) */
#define NS_MODE       0x8005D2C4u   /* h: 0 demo, 1 one player vs CPU, 2 two players, 3 practice */
#define NS_HUMAN      0x8005E6C8u   /* b: the human player in mode 1 */
#define NS_BAR        0x8005E684u   /* h: beat index of the current bar */
#define NS_SCORE      0x8005E6F8u   /* w[2]: P1, P2 (animated: shown, not compared) */
#define NS_COOLS      0x8005E798u   /* w[2]: COOL bars P1, P2 (set at once in the resolve loop) */
#define NS_GOODS      0x8005E7A8u   /* w[2]: right bars P1, P2 */
#define NS_JUDGE      0x8005CF08u
#define NS_PLAYER     0x8005E728u
#define NS_DISC_PORT  47300
#define NS_DIRECT_PORT 47100
#define NS_WAIT_MAX   180           /* frames a bar may wait for the other player's result */
#define PAD_START     0x0008u

/* Protocol packet header size ("B2NS" + version + type + padding + code_hash + nonce) */
#define NS_PKT_HDR    20
/* Maximum MQTT message buffer size */
#define NS_MQ_BUF     8192
/* Maximum event button buffer size (ring buffer for pad events) */
#define NS_EV_BUF     256
/* Maximum number of broker entries */
#define NS_BROKER_MAX 8
/* Maximum number of STUN entries */
#define NS_STUN_MAX   4
/* Maximum line length when reading settings files */
#define NS_LINE_MAX   160

enum { NS_OFF, NS_LOOPBACK, NS_LAN, NS_INTERNET, NS_DIRECT };
enum { M_HELLO = 1, M_PAD = 3, M_STEP = 4, M_PING = 5, M_READY = 6, M_PUNCH = 7, M_PONG = 8, M_FOCUS = 9,
       M_PICK = 10, M_CONTENT = 11 };
enum { CH_NONE, CH_UDP, CH_RELAY };

typedef struct {
    int16_t bar, state, timing, result, command;
    uint16_t pressed; uint8_t cool, valid; uint16_t match, pad;
    int32_t score[2];                       /* sender's scores when it closed this bar (log only) */
    int32_t check[4];                       /* COOL and right-bar counts P1/P2 at the close */
} NsStep;

static int s_transport;
static uint32_t s_vblanks;
static FILE* s_logf;

/* session */
static SOCKET s_data = INVALID_SOCKET, s_disc = INVALID_SOCKET;
static char s_code[64] = "BAG2", s_direct_target[128];
static uint32_t s_code_hash;
static uint64_t s_nonce, s_peer_nonce;
static struct sockaddr_in s_peer, s_cand[2];      /* s_cand: peer's public and local address */
static int s_linked, s_local = -1, s_lobby_role = -1, s_ch = CH_NONE, s_punch_until;
static uint32_t s_last_rx, s_last_hello, s_code_check;
static struct sockaddr_in s_public;               /* our address seen by STUN */
static int s_have_public;
static int s_rtt_ms = -1;

/* broker (internet) */
#define BROKER_MAX 8
static char s_brokers[BROKER_MAX][128]; static int s_nbrokers;
static char s_stuns[4][128]; static int s_nstuns;
static struct sockaddr_in s_stun_addr[4]; static atomic_int s_stun_ready;
static SOCKET s_mqtt = INVALID_SOCKET;
static atomic_int s_mqtt_ready;                   /* worker -> main: 1 connected socket in s_mqtt_new */
static SOCKET s_mqtt_new = INVALID_SOCKET;
static atomic_int s_worker_busy;
static int s_mqtt_state, s_broker_idx;            /* 0 none, 1 connect sent, 2 subscribed */
static uint8_t s_mq_buf[NS_MQ_BUF]; static int s_mq_len;
static uint32_t s_mq_ping, s_mq_retry;
static char s_topic[64];
static struct sockaddr_in s_local_addr;

/* steps */
static NsStep s_mine, s_theirs[64];       /* indexed by (bar/4) & 63 */
static int s_wait_bar = -1, s_wait_frames, s_desync_reported;
static uint32_t s_step_resend;
static int32_t s_my_scores[64][2], s_my_check[64][4]; static int16_t s_my_score_bar[64];

/* pads */
#define EV_N 256
static uint16_t s_out_btn[EV_N]; static uint32_t s_out_seq;
static uint16_t s_in_btn[EV_N];  static uint32_t s_in_seq, s_in_applied;
static uint16_t s_local_btn = 0xFFFF, s_remote_btn = 0xFFFF, s_last_local = 0xFFFF;
static int s_remote_hold;
static int s_routing;
static uint16_t s_match;
static int s_was_dance;
static int s_peer_ready = -1;

/* pause: while a dance runs, either PC losing window focus pauses both (host pause: guest and
 * audio frozen). The vblank plugin does not run during a host pause, so a timer thread keeps
 * the link alive and ends it; s_mu serializes it with the guest-side code. */
static SDL_Mutex* s_mu;
static SDL_TimerID s_timer;
static int s_lfocus = 1, s_rfocus = 1;    /* this PC's window / the other PC's, as last reported */
static volatile int s_pause_held;         /* we hold a host pause */
static int s_match_live;                  /* a dance is running (after the start barrier) */
static uint32_t s_dance_frames;           /* guest frames since the dance started */
static uint32_t s_pause_at, s_peer_pause_at; static int s_peer_pause_known;
static uint64_t s_resume_at;              /* SDL ticks when the resume countdown ends, 0 none */
static int s_resume_local;                /* this PC's own focus change allowed the resume */
static int s_focus_always = -1;           /* test switch BAG2JP_NETSYNC_FOCUS=always */
static char s_pause_msg[120];

static void ns_log(const char* fmt, ...) {
    if (!s_logf) {
        const char* b = SDL_GetBasePath(); char p[1024];
        snprintf(p, sizeof p, "%sbag2jp_netsync.log", b ? b : "");
        s_logf = fopen(p, "w"); if (!s_logf) return;
    }
    va_list ap; va_start(ap, fmt); vfprintf(s_logf, fmt, ap); va_end(ap);
    fputc('\n', s_logf); fflush(s_logf);
}

static const char* ns_addr(const struct sockaddr_in* a) {
    static char b[4][32]; static int k; k = (k + 1) & 3;
    snprintf(b[k], sizeof b[k], "%s:%u", inet_ntoa(a->sin_addr), ntohs(a->sin_port));
    return b[k];
}

/* ------------------------------------------------------------------ settings files */
static uint32_t ns_hash(const char* s) {
    uint32_t h = 2166136261u;
    for (; *s; ++s) {
        int c = toupper((unsigned char)*s);
        if (c == ' ' || c == '-' || c == '_') continue;
        h = (h ^ (uint32_t)c) * 16777619u;
    }
    return h;
}

static int ns_read_code(void) {                 /* 1 when the room code changed */
    const char* b = SDL_GetBasePath(); char p[1024], code[64] = "", target[128] = "";
    snprintf(p, sizeof p, "%sbag2jp_online.txt", b ? b : "");
    FILE* f = fopen(p, "r");
    if (f) {
        if (fgets(code, sizeof code, f)) code[strcspn(code, "\r\n")] = 0;
        if (fgets(target, sizeof target, f)) target[strcspn(target, "\r\n ")] = 0;
        fclose(f);
    }
    if (!code[0]) strcpy(code, "BAG2");
    snprintf(s_direct_target, sizeof s_direct_target, "%s", target);
    const uint32_t h = ns_hash(s_transport == NS_DIRECT ? "DIRECT" : code);
    const int changed = h != s_code_hash;
    snprintf(s_code, sizeof s_code, "%s", code);
    s_code_hash = h;
    return changed;
}

static void ns_net_open(void);
static void ns_disconnect_locked(const char* why);

void bag2jp_netsync_apply_lobby_match(const char* room_code) {
    if (!room_code || !room_code[0]) return;
    if (!s_mu) s_mu = SDL_CreateMutex();
    const char* env_tr = getenv("BAG2JP_LOBBY_TRANSPORT");
    s_transport = (env_tr && strcmp(env_tr, "lan") == 0) ? NS_LAN : NS_INTERNET;
    s_lobby_role = bag2jp_lobby_state()->is_host ? 0 : 1;
    snprintf(s_code, sizeof s_code, "%s", room_code);
    s_code_hash = ns_hash(s_code);
    if (s_data == INVALID_SOCKET) {
        ns_net_open();
    }
    ns_log("lobby match applied: transport=%d room='%s' hash=%08x", s_transport, s_code, s_code_hash);
}

static void ns_read_servers(void) {
    const char* b = SDL_GetBasePath(); char p[1024], line[160];
    snprintf(p, sizeof p, "%sbag2jp_online_servers.txt", b ? b : "");
    FILE* f = fopen(p, "r");
    if (!f) {                                         /* first run: write the defaults */
        f = fopen(p, "w");
        if (f) {
            fputs("# Online play meeting points. One per line, tried in order.\n"
                  "# mqtt host:port = where two games with the same room code find each other.\n"
                  "# stun host:port = tells each game its public address for a direct connection.\n"
                  "mqtt broker.hivemq.com:1883\nmqtt broker.emqx.io:1883\nmqtt test.mosquitto.org:1883\n"
                  "stun stun.l.google.com:19302\nstun stun.cloudflare.com:3478\n", f);
            fclose(f);
        }
        f = fopen(p, "r"); if (!f) return;
    }
    s_nbrokers = s_nstuns = 0;
    while (fgets(line, sizeof line, f)) {
        char kind[16], host[128];
        if (line[0] == '#' || sscanf(line, "%15s %127s", kind, host) != 2) continue;
        if (!strcmp(kind, "mqtt") && s_nbrokers < BROKER_MAX) snprintf(s_brokers[s_nbrokers++], 128, "%s", host);
        if (!strcmp(kind, "stun") && s_nstuns < 4) snprintf(s_stuns[s_nstuns++], 128, "%s", host);
    }
    fclose(f);
}

static int ns_resolve(const char* hostport, struct sockaddr_in* out) {
    char host[128]; snprintf(host, sizeof host, "%s", hostport);
    char* c = strrchr(host, ':'); if (!c) return 0;
    *c = 0; const char* port = c + 1;
    struct addrinfo hints, *res = NULL; memset(&hints, 0, sizeof hints); hints.ai_family = AF_INET;
    if (getaddrinfo(host, port, &hints, &res) != 0 || !res) return 0;
    memcpy(out, res->ai_addr, sizeof *out); freeaddrinfo(res);
    return 1;
}

/* ------------------------------------------------------------------ worker: DNS + TCP connect */
static int ns_worker(void* arg) {
    (void)arg;
    if (!atomic_load(&s_stun_ready)) {
        int n = 0;
        for (int i = 0; i < s_nstuns; ++i) if (ns_resolve(s_stuns[i], &s_stun_addr[n])) n++;
        /* this PC's LAN address (no packet is sent by a UDP connect) */
        SOCKET t = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
        struct sockaddr_in g; memset(&g, 0, sizeof g); g.sin_family = AF_INET; g.sin_port = htons(53);
        g.sin_addr.s_addr = inet_addr("8.8.8.8");
        if (connect(t, (struct sockaddr*)&g, sizeof g) == 0) { int l = sizeof s_local_addr; getsockname(t, (struct sockaddr*)&s_local_addr, &l); }
        closesocket(t);
        atomic_store(&s_stun_ready, n > 0 ? n : -1);
    }
    for (int tries = 0; tries < s_nbrokers && s_transport == NS_INTERNET; ++tries) {
        const int i = (s_broker_idx + tries) % s_nbrokers;
        struct sockaddr_in a;
        if (!ns_resolve(s_brokers[i], &a)) { ns_log("broker %s: name not found", s_brokers[i]); continue; }
        SOCKET so = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
        u_long nb = 1; ioctlsocket(so, FIONBIO, &nb);
        connect(so, (struct sockaddr*)&a, sizeof a);
        fd_set w; FD_ZERO(&w); FD_SET(so, &w); struct timeval tv = { 4, 0 };
        int err = 0, el = sizeof err;
        if (select(0, NULL, &w, NULL, &tv) == 1 && getsockopt(so, SOL_SOCKET, SO_ERROR, (char*)&err, &el) == 0 && err == 0) {
            BOOL nd = TRUE; setsockopt(so, IPPROTO_TCP, TCP_NODELAY, (const char*)&nd, sizeof nd);
            s_mqtt_new = so; s_broker_idx = i;
            ns_log("broker %s connected", s_brokers[i]);
            atomic_store(&s_mqtt_ready, 1);
            break;
        }
        ns_log("broker %s: no connection", s_brokers[i]);
        closesocket(so);
    }
    atomic_store(&s_worker_busy, 0);
    return 0;
}

static void ns_start_worker(void) {
    if (atomic_exchange(&s_worker_busy, 1)) return;
    SDL_Thread* t = SDL_CreateThread(ns_worker, "bag2jp-netsync", NULL);
    if (t) SDL_DetachThread(t); else atomic_store(&s_worker_busy, 0);
}

/* ------------------------------------------------------------------ MQTT 3.1.1 (QoS 0) */
static int mq_varlen(uint8_t* b, int n) { int k = 0; do { uint8_t d = n % 128; n /= 128; if (n) d |= 128; b[k++] = d; } while (n); return k; }
static void mq_send(const uint8_t* b, int n) {
    if (s_mqtt == INVALID_SOCKET) return;
    if (send(s_mqtt, (const char*)b, n, 0) != n) ns_log("broker send failed");
}
static void mq_publish(const void* payload, int n) {
    uint8_t b[600]; const int tl = (int)strlen(s_topic);
    int body = 2 + tl + n; if (body > 500) return;
    int k = 0; b[k++] = 0x30; k += mq_varlen(b + k, body);
    b[k++] = (uint8_t)(tl >> 8); b[k++] = (uint8_t)tl; memcpy(b + k, s_topic, (size_t)tl); k += tl;
    memcpy(b + k, payload, (size_t)n); k += n;
    mq_send(b, k);
}
static void mq_connected(void) {
    char id[32]; snprintf(id, sizeof id, "bag2jp-%08x", (unsigned)(s_nonce & 0xFFFFFFFFu));
    uint8_t b[96]; int k = 0; const int il = (int)strlen(id);
    b[k++] = 0x10; k += mq_varlen(b + k, 10 + 2 + il);
    const uint8_t vh[10] = { 0, 4, 'M', 'Q', 'T', 'T', 4, 0x02, 0, 60 };
    memcpy(b + k, vh, 10); k += 10;
    b[k++] = 0; b[k++] = (uint8_t)il; memcpy(b + k, id, (size_t)il); k += il;
    mq_send(b, k);
    snprintf(s_topic, sizeof s_topic, "bag2jp/v1/%08x", s_code_hash);
    const int tl = (int)strlen(s_topic);
    k = 0; b[k++] = 0x82; k += mq_varlen(b + k, 2 + 2 + tl + 1);
    b[k++] = 0; b[k++] = 1; b[k++] = 0; b[k++] = (uint8_t)tl; memcpy(b + k, s_topic, (size_t)tl); k += tl; b[k++] = 0;
    mq_send(b, k);
    s_mqtt_state = 1; s_mq_len = 0; s_mq_ping = s_vblanks;
}
static void mq_drop(const char* why) {
    if (s_mqtt != INVALID_SOCKET) closesocket(s_mqtt);
    s_mqtt = INVALID_SOCKET; s_mqtt_state = 0; s_mq_len = 0;
    ns_log("broker connection closed: %s", why);
    s_broker_idx = (s_broker_idx + 1) % (s_nbrokers ? s_nbrokers : 1);
    s_mq_retry = s_vblanks;
}

/* ------------------------------------------------------------------ packets */
static int ns_hdr(uint8_t* b, int type) {
    memcpy(b, "B2NS", 4); b[4] = 2; b[5] = (uint8_t)type; b[6] = b[7] = 0;
    memcpy(b + 8, &s_code_hash, 4); memcpy(b + 12, &s_nonce, 8);
    return 20;
}
static void ns_send_to(const struct sockaddr_in* to, const void* b, int n) {
    if (s_data != INVALID_SOCKET) sendto(s_data, (const char*)b, n, 0, (const struct sockaddr*)to, sizeof *to);
}
static void ns_relay(uint64_t to, const void* b, int n) {
    if (s_mqtt_state != 2) return;
    uint8_t f[520]; if (n > 500) return;
    memcpy(f, &to, 8); memcpy(f + 8, b, (size_t)n); mq_publish(f, n + 8);
}
static void ns_send(const void* b, int n) {
    if (!s_linked) return;
    if (s_ch == CH_UDP) ns_send_to(&s_peer, b, n);
    else if (s_ch == CH_RELAY) ns_relay(s_peer_nonce, b, n);
}

static void ns_send_hello(const struct sockaddr_in* to, uint64_t relay_to) {
    uint8_t b[64]; int n = ns_hdr(b, M_HELLO);
    struct sockaddr_in pub = s_public, loc = s_local_addr;
    if (!s_have_public) memset(&pub, 0, sizeof pub);
    uint16_t lp = 0; { struct sockaddr_in a; int l = sizeof a; if (getsockname(s_data, (struct sockaddr*)&a, &l) == 0) lp = a.sin_port; }
    loc.sin_port = lp;
    memcpy(b + n, &pub.sin_addr, 4); memcpy(b + n + 4, &pub.sin_port, 2);
    memcpy(b + n + 6, &loc.sin_addr, 4); memcpy(b + n + 10, &loc.sin_port, 2); n += 12;
    if (to) ns_send_to(to, b, n); else ns_relay(relay_to, b, n);
}

static void ns_send_step(const NsStep* s) {
    uint8_t b[128]; int n = ns_hdr(b, M_STEP);
    memcpy(b + n, s, sizeof *s); n += (int)sizeof *s;
    ns_send(b, n);
}

static void ns_send_pads(void) {
    uint8_t b[20 + 4 + 16 * 2]; int n = ns_hdr(b, M_PAD);
    uint32_t first = s_out_seq > 16 ? s_out_seq - 16 : 0;
    memcpy(b + n, &first, 4); n += 4;
    for (uint32_t q = first; q < s_out_seq; ++q) { memcpy(b + n, &s_out_btn[q % EV_N], 2); n += 2; }
    ns_send(b, n);
}

static void ns_send_focus(void) {
    uint8_t b[40]; int n = ns_hdr(b, M_FOCUS);
    b[n] = (uint8_t)s_lfocus; b[n + 1] = (uint8_t)s_pause_held; memcpy(b + n + 2, &s_match, 2);
    memcpy(b + n + 4, &s_pause_at, 4); n += 8;
    ns_send(b, n);
}

/* Character select popup (bag2jp_charsel_popup.c): the version a player picks for a character with
 * a BAG1 version is sent to the other PC (M_PICK: u8 side, chr, version, seq), repeated with every
 * ping (idempotent, the latest seq wins). M_CONTENT (u32 id of the BAG1 content index) is repeated
 * too: if the two PCs have different BAG1 content both use BAG2 versions only. */
static uint8_t s_pick[2][4], s_pick_have[2], s_pick_seq[2], s_pick_rseq[2], s_pick_rhave[2];
static int s_content_state;                         /* 0 unknown, 1 same, 2 different */
static void ns_send_picks(void) {
    for (int s = 0; s < 2; ++s) {
        if (!s_pick_have[s]) continue;
        uint8_t b[32]; int n = ns_hdr(b, M_PICK);
        memcpy(b + n, s_pick[s], 4); n += 4;
        ns_send(b, n);
    }
}
static void ns_send_content(void) {
    uint8_t b[32]; int n = ns_hdr(b, M_CONTENT);
    const uint32_t id = bag2jp_bag1_content_id();
    memcpy(b + n, &id, 4); n += 4;
    ns_send(b, n);
}
void bag2jp_netsync_send_pick(int side, int chr, int version) {
    if (!s_linked || side < 0 || side > 1) return;
    if (s_mu) SDL_LockMutex(s_mu);
    s_pick[side][0] = (uint8_t)side; s_pick[side][1] = (uint8_t)chr; s_pick[side][2] = (uint8_t)(version ? 1 : 0);
    s_pick[side][3] = ++s_pick_seq[side];
    s_pick_have[side] = 1;
    ns_log("v%u pick sent: P%d char %d %s", s_vblanks, side + 1, chr, version ? "BAG1" : "BAG2");
    ns_send_picks();
    if (s_mu) SDL_UnlockMutex(s_mu);
}

static void ns_status_reset(void);
static void ns_unlink(const char* why) {
    if (!s_linked) return;
    ns_log("v%u link lost: %s", s_vblanks, why);
    host_osd_push("ONLINE  the other player left", 4000);
    s_linked = 0; s_peer_nonce = 0; s_ch = CH_NONE; s_rtt_ms = -1;
    bag2jp_bag1_online(0);
    ns_status_reset();
}

static void ns_link(uint64_t nonce, int ch, const struct sockaddr_in* udp) {
    s_peer_nonce = nonce; s_linked = 1; s_ch = ch;
    if (udp) s_peer = *udp;
    s_local = (s_lobby_role >= 0) ? s_lobby_role
            : (s_transport == NS_DIRECT ? (s_direct_target[0] ? 1 : 0)   /* direct: the host is P1 */
                                        : (s_nonce > nonce ? 0 : 1));
    s_in_seq = s_in_applied = 0; s_out_seq = 0; s_match = 0; s_was_dance = 0; s_peer_ready = -1;
    s_last_rx = s_vblanks; s_desync_reported = 0; s_rfocus = 1; s_match_live = 0;
    memset(s_theirs, 0, sizeof s_theirs);
    memset(s_pick_have, 0, sizeof s_pick_have); memset(s_pick_rhave, 0, sizeof s_pick_rhave);
    s_content_state = 0; bag2jp_bag1_online(1); bag2jp_bag1_force_stock(0);
    ns_log("v%u linked (%s%s), this PC is P%d", s_vblanks, ch == CH_UDP ? "direct " : "through the broker",
           ch == CH_UDP ? ns_addr(udp) : "", s_local + 1);
}

static void ns_on_packet(const uint8_t* b, int n, const struct sockaddr_in* from, int via_relay) {
    if (n < NS_PKT_HDR || memcmp(b, "B2NS", 4) || b[4] != 2) return;
    uint32_t h; memcpy(&h, b + 8, 4); if (h != s_code_hash) return;
    uint64_t sender; memcpy(&sender, b + 12, 8);
    if (sender == s_nonce) return;                              /* our own broadcast/publish */
    const uint8_t* p = b + 20; n -= 20;
    if (s_linked && sender != s_peer_nonce) return;             /* room taken: one pair only */
    if (b[5] == M_HELLO) {
        if (!s_linked) {
            if (via_relay) ns_link(sender, CH_RELAY, NULL);
            else ns_link(sender, CH_UDP, from);
            if (via_relay) ns_send_hello(NULL, sender); else ns_send_hello(from, 0);
        }
        if (via_relay && n >= 12 && s_ch == CH_RELAY) {         /* candidates for a direct path */
            memset(s_cand, 0, sizeof s_cand);
            s_cand[0].sin_family = s_cand[1].sin_family = AF_INET;
            memcpy(&s_cand[0].sin_addr, p, 4); memcpy(&s_cand[0].sin_port, p + 4, 2);
            memcpy(&s_cand[1].sin_addr, p + 6, 4); memcpy(&s_cand[1].sin_port, p + 10, 2);
            s_punch_until = (int)s_vblanks + 600;
            ns_log("v%u peer candidates %s / %s", s_vblanks, ns_addr(&s_cand[0]), ns_addr(&s_cand[1]));
        }
    }
    if (!s_linked) return;
    s_last_rx = s_vblanks;
    if (!via_relay && s_ch == CH_RELAY && b[5] != M_HELLO) {     /* a UDP packet got through */
        s_ch = CH_UDP; s_peer = *from;
        ns_log("v%u direct connection to %s", s_vblanks, ns_addr(from));
        ns_status_reset();
    }
    switch (b[5]) {
    case M_PUNCH: break;
    case M_PAD: {
        if (n < 4) return;
        uint32_t first; memcpy(&first, p, 4);
        const int k = (n - 4) / 2;
        if (first > s_in_seq) {
            ns_log("v%u pad gap: jumping s_in_seq %u -> %u", s_vblanks, s_in_seq, first);
            s_in_seq = first;
            s_in_applied = first;
        }
        for (int i = 0; i < k; ++i) {
            const uint32_t q = first + (uint32_t)i;
            if (q < s_in_seq) continue;
            if (q > s_in_seq) break;
            memcpy(&s_in_btn[q % EV_N], p + 4 + 2 * i, 2); s_in_seq = q + 1;
        }
        break; }
    case M_STEP: {
        if (n < (int)sizeof(NsStep)) return;
        NsStep s; memcpy(&s, p, sizeof s);
        if (s.match != s_match) return;
        NsStep* slot = &s_theirs[(s.bar / 4) & 63];
        if (!slot->valid || slot->bar != s.bar) {
            *slot = s; slot->valid = 1;
            ns_log("v%u got step bar %d state %d timing %d result 0x%x", s_vblanks, s.bar, s.state,
                   s.timing, (uint16_t)s.result);
        }
        break; }
    case M_PING: {
        uint8_t r[32]; int m = ns_hdr(r, M_PONG); if (n >= 4) { memcpy(r + m, p, 4); m += 4; }
        ns_send(r, m);
        break; }
    case M_PONG: {
        if (n < 4) return;
        uint32_t t; memcpy(&t, p, 4);
        const int rtt = (int)((uint32_t)SDL_GetTicks() - t);
        s_rtt_ms = s_rtt_ms < 0 ? rtt : (s_rtt_ms * 3 + rtt) / 4;
        break; }
    case M_READY: {
        if (n < 2) return;
        uint16_t m; memcpy(&m, p, 2); s_peer_ready = m;
        break; }
    case M_PICK: {          /* u8 side, u8 char, u8 version, u8 seq */
        if (n < 4 || p[0] > 1) return;
        const int s = p[0];
        if (s_pick_rhave[s] && s_pick_rseq[s] == p[3]) break;
        s_pick_rhave[s] = 1; s_pick_rseq[s] = p[3];
        bag2jp_bag1_set_version(p[1], s, p[2]);
        ns_log("v%u pick received: P%d char %d %s", s_vblanks, s + 1, p[1], p[2] ? "BAG1" : "BAG2");
        break; }
    case M_CONTENT: {
        if (n < 4) return;
        uint32_t id; memcpy(&id, p, 4);
        const int st = id == bag2jp_bag1_content_id() ? 1 : 2;
        if (st != s_content_state) {
            s_content_state = st;
            bag2jp_bag1_force_stock(st == 2);
            ns_log("v%u BAG1 content %s (theirs %08x)", s_vblanks, st == 1 ? "same" : "DIFFERENT", id);
            if (st == 2) host_osd_push("ONLINE  Bust A Groove 1 content differs from the other PC: BAG2 versions only", 6000);
        }
        break; }
    case M_FOCUS: {         /* u8 focused, u8 paused, u16 match, u32 dance frame of the pause */
        if (n < 8) return;
        uint16_t m; memcpy(&m, p + 2, 2);
        const int f = p[0] != 0;
        if (f != s_rfocus) {
            s_rfocus = f;
            if (f && s_lfocus) s_resume_local = 0;
            ns_log("v%u other PC window %s", s_vblanks, f ? "back in focus" : "lost focus");
        }
        if (p[1] && m == s_match && !s_peer_pause_known) {
            memcpy(&s_peer_pause_at, p + 4, 4); s_peer_pause_known = 1;
        }
        break; }
    }
}

static void ns_on_stun(const uint8_t* b, int n) {
    if (n < 20 || b[0] != 0x01 || b[1] != 0x01) return;
    for (int i = 20; i + 4 <= n; ) {
        const int type = (b[i] << 8) | b[i + 1], len = (b[i + 2] << 8) | b[i + 3];
        if (type == 0x0020 && len >= 8 && b[i + 5] == 0x01) {
            uint16_t port = (uint16_t)(((b[i + 6] << 8) | b[i + 7]) ^ 0x2112);
            uint32_t ip = (((uint32_t)b[i + 8] << 24) | ((uint32_t)b[i + 9] << 16) | ((uint32_t)b[i + 10] << 8) | b[i + 11]) ^ 0x2112A442u;
            memset(&s_public, 0, sizeof s_public); s_public.sin_family = AF_INET;
            s_public.sin_port = htons(port); s_public.sin_addr.s_addr = htonl(ip);
            if (!s_have_public) ns_log("public address %s", ns_addr(&s_public));
            s_have_public = 1; ns_status_reset();
            return;
        }
        i += 4 + ((len + 3) & ~3);
    }
}

static void ns_stun_query(void) {
    const int n = atomic_load(&s_stun_ready);
    for (int i = 0; i < n; ++i) {
        uint8_t q[20] = { 0x00, 0x01, 0, 0, 0x21, 0x12, 0xA4, 0x42 };
        for (int k = 8; k < 20; ++k) q[k] = (uint8_t)(rand() & 0xFF);
        ns_send_to(&s_stun_addr[i], q, 20);
    }
}

static void ns_mqtt_poll(void) {
    if (s_transport != NS_INTERNET) return;
    if (atomic_exchange(&s_mqtt_ready, 0)) { s_mqtt = s_mqtt_new; mq_connected(); }
    if (s_mqtt == INVALID_SOCKET) {
        if (!atomic_load(&s_worker_busy) && (s_mq_retry == 0 || s_vblanks - s_mq_retry > 300)) { s_mq_retry = s_vblanks; ns_start_worker(); }
        return;
    }
    for (;;) {
        const int r = recv(s_mqtt, (char*)s_mq_buf + s_mq_len, (int)sizeof s_mq_buf - s_mq_len, 0);
        if (r == 0) { mq_drop("closed by the broker"); return; }
        if (r < 0) { if (WSAGetLastError() != WSAEWOULDBLOCK) { mq_drop("network error"); return; } break; }
        s_mq_len += r;
        if (s_mq_len == (int)sizeof s_mq_buf) { mq_drop("oversized message"); return; }
    }
    for (;;) {                                         /* parse whole packets */
        if (s_mq_len < 2) break;
        int len = 0, mul = 1, k = 1;
        for (; k < 5 && k < s_mq_len; ++k) { len += (s_mq_buf[k] & 127) * mul; mul *= 128; if (!(s_mq_buf[k] & 128)) break; }
        if (k >= s_mq_len || (s_mq_buf[k] & 128)) break;
        const int hl = k + 1, total = hl + len;
        if (s_mq_len < total) break;
        const uint8_t type = s_mq_buf[0] & 0xF0;
        const uint8_t* body = s_mq_buf + hl;
        if (type == 0x20) { if (len >= 2 && body[1] != 0) { mq_drop("connection refused"); return; } }
        else if (type == 0x90) { s_mqtt_state = 2; ns_log("broker: joined room topic %s", s_topic); ns_status_reset(); s_last_hello = 0; }
        else if (type == 0x30 && len >= 2) {
            const int tl = (body[0] << 8) | body[1];
            const int qos = (s_mq_buf[0] >> 1) & 3;
            const int off = 2 + tl + (qos ? 2 : 0);
            if (off + 8 <= len) {
                uint64_t to; memcpy(&to, body + off, 8);
                if (to == 0 || to == s_nonce) ns_on_packet(body + off + 8, len - off - 8, NULL, 1);
            }
        }
        memmove(s_mq_buf, s_mq_buf + total, (size_t)(s_mq_len - total)); s_mq_len -= total;
    }
    if (s_vblanks - s_mq_ping > 1200) { const uint8_t pr[2] = { 0xC0, 0 }; mq_send(pr, 2); s_mq_ping = s_vblanks; }
}

static void ns_net_open(void) {
    WSADATA w; if (WSAStartup(MAKEWORD(2, 2), &w) != 0) { ns_log("WSAStartup failed"); return; }
    if (s_lobby_role < 0) ns_read_code();
    s_nonce = ((uint64_t)SDL_GetPerformanceCounter() << 16) ^ (uint64_t)SDL_GetTicksNS() ^ (uint64_t)(uintptr_t)&w;
    srand((unsigned)s_nonce);
    u_long nb = 1; BOOL yes = TRUE;
    s_data = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    struct sockaddr_in a; memset(&a, 0, sizeof a); a.sin_family = AF_INET; a.sin_addr.s_addr = htonl(INADDR_ANY);
    if (s_transport == NS_DIRECT && !s_direct_target[0]) a.sin_port = htons(NS_DIRECT_PORT);
    if (bind(s_data, (struct sockaddr*)&a, sizeof a) != 0) ns_log("bind failed %d", WSAGetLastError());
    ioctlsocket(s_data, FIONBIO, &nb);
    setsockopt(s_data, SOL_SOCKET, SO_BROADCAST, (const char*)&yes, sizeof yes);
    if (s_transport == NS_LAN) {
        s_disc = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
        setsockopt(s_disc, SOL_SOCKET, SO_REUSEADDR, (const char*)&yes, sizeof yes);
        a.sin_port = htons(NS_DISC_PORT);
        if (bind(s_disc, (struct sockaddr*)&a, sizeof a) != 0) ns_log("discovery bind failed %d", WSAGetLastError());
        ioctlsocket(s_disc, FIONBIO, &nb);
    }
    if (s_transport == NS_INTERNET || s_transport == NS_DIRECT) { ns_read_servers(); ns_start_worker(); }
    ns_log("net: transport %d room '%s' hash %08x nonce %016llx target '%s'", s_transport, s_code, s_code_hash,
           (unsigned long long)s_nonce, s_direct_target);
}

static void ns_net_poll(void) {
    if (s_data == INVALID_SOCKET) return;
    uint8_t b[600]; struct sockaddr_in from; int fl;
    SOCKET socks[2] = { s_data, s_disc };
    for (int s = 0; s < 2; ++s) {
        if (socks[s] == INVALID_SOCKET) continue;
        for (;;) {
            fl = sizeof from;
            const int n = recvfrom(socks[s], (char*)b, sizeof b, 0, (struct sockaddr*)&from, &fl);
            if (n <= 0) break;
            if (n >= 20 && b[0] == 0x01 && b[1] == 0x01 && b[4] == 0x21 && b[5] == 0x12) { ns_on_stun(b, n); continue; }
            ns_on_packet(b, n, &from, 0);
        }
    }
    ns_mqtt_poll();
    /* STUN: once the servers are known, and again every 20 s (keeps the router mapping open) */
    static uint32_t s_stun_t; static int s_stun_sent;
    if (atomic_load(&s_stun_ready) > 0 && (!s_stun_sent || s_vblanks - s_stun_t > 1200 || (!s_have_public && s_vblanks - s_stun_t > 120))) {
        s_stun_sent = 1; s_stun_t = s_vblanks; ns_stun_query();
    }
    if (!s_linked) {
        if (s_vblanks - s_code_check > 120) {          /* room code edited in MODS: use it */
            s_code_check = s_vblanks;
            if (ns_read_code() && s_mqtt_state) { ns_log("room code now '%s'", s_code); mq_drop("room changed"); }
        }
        if (s_vblanks - s_last_hello >= 30) {
            s_last_hello = s_vblanks;
            struct sockaddr_in to; memset(&to, 0, sizeof to); to.sin_family = AF_INET;
            if (s_transport == NS_LAN) {
                to.sin_port = htons(NS_DISC_PORT); to.sin_addr.s_addr = htonl(INADDR_BROADCAST);
                ns_send_hello(&to, 0);
            } else if (s_transport == NS_INTERNET && s_mqtt_state == 2) {
                if (s_vblanks - s_last_hello >= 0) ns_send_hello(NULL, 0);
            } else if (s_transport == NS_DIRECT && s_direct_target[0]) {
                if (ns_resolve(s_direct_target, &to)) ns_send_hello(&to, 0);
            }
        }
    } else {
        if (s_vblanks - s_last_rx > 300) ns_unlink("nothing received for 5 s");
        static int relay_only = -1;     /* test switch: BAG2JP_NETSYNC_RELAY_ONLY=1 never punches */
        if (relay_only < 0) relay_only = SDL_getenv("BAG2JP_NETSYNC_RELAY_ONLY") != NULL;
        if (!relay_only && s_ch == CH_RELAY && (int)s_vblanks < s_punch_until && s_vblanks % 6 == 0) {
            uint8_t p[24]; const int n = ns_hdr(p, M_PUNCH);
            for (int i = 0; i < 2; ++i) if (s_cand[i].sin_addr.s_addr) ns_send_to(&s_cand[i], p, n);
        }
        if (s_vblanks % 20 == 0) {
            uint8_t p[32]; int n = ns_hdr(p, M_PING); const uint32_t t = (uint32_t)SDL_GetTicks();
            memcpy(p + n, &t, 4); n += 4; ns_send(p, n);
            ns_send_pads();
            ns_send_focus();
            ns_send_picks();
            ns_send_content();
        }
    }
}

/* ------------------------------------------------------------------ status line */
static int s_status_shown = -1, s_status_rtt = -2;
static void ns_status_reset(void) { s_status_shown = -1; }
static void ns_status(void) {
    if (s_pause_held) { s_status_shown = -1; return; }      /* the pause owns the status line */
    int want = !s_linked ? 0 : (s_routing ? 2 : 1);
    if (s_routing && psx_mod_read_word(NS_SITE) == NS_WORD) want = 3;     /* dancing: keep it quiet */
    const int rtt_bucket = s_rtt_ms < 0 ? -1 : s_rtt_ms / 20;
    if (want == s_status_shown && (want == 0 || want == 3 || rtt_bucket == s_status_rtt)) return;
    s_status_shown = want; s_status_rtt = rtt_bucket;
    char m[200], lat[48] = "";
    if (s_rtt_ms >= 0) snprintf(lat, sizeof lat, "  (%d ms%s)", s_rtt_ms, s_rtt_ms > 250 ? ", slow" : "");
    switch (want) {
    case 0:
        if (s_transport == NS_DIRECT && !s_direct_target[0])
            snprintf(m, sizeof m, "ONLINE  host  -  give the other player %s:%d",
                     s_have_public ? inet_ntoa(s_public.sin_addr) : "(finding your address)", NS_DIRECT_PORT);
        else if (s_transport == NS_DIRECT)
            snprintf(m, sizeof m, "ONLINE  DIRECT IP  -  connecting to %s...", s_direct_target);
        else if (s_transport == NS_INTERNET && s_mqtt_state != 2)
            snprintf(m, sizeof m, "ONLINE  room %s  -  connecting...", s_code);
        else
            snprintf(m, sizeof m, "ONLINE  room %s  -  looking for the other player...", s_code);
        break;
    case 1: snprintf(m, sizeof m, "ONLINE  you are P%d  -  choose 2PLAYER GAME%s", s_local + 1, lat); break;
    case 2: snprintf(m, sizeof m, "ONLINE  you are P%d%s", s_local + 1, lat); break;
    default: m[0] = 0; break;
    }
    host_osd_set_status(m);
}

/* ------------------------------------------------------------------ pads */
static int ns_in_dance(void) { return psx_mod_read_word(NS_SITE) == NS_WORD; }

static int ns_pad_transform(const PSXModPadFrame* f, PSXModPadOutput* out) {
    const int port = (int)f->player;
    if (port == 1) {
        out->buttons = !s_routing ? 0xFFFFu : (s_local == 1 ? s_local_btn : s_remote_btn);
        return 1;
    }
    if (bag2jp_mods_menu_pad_filter(f, out)) { s_local_btn = 0xFFFF; return 1; }   /* MODS screen */
    if (!s_routing) return 0;
    uint32_t mine = f->buttons;
    {   /* character select popup for this PC's own side: resolved here, before the buttons are sent */
        PSXModPadOutput po; memset(&po, 0, sizeof po); po.struct_size = sizeof po;
        if (s_local >= 0 && bag2jp_charsel_filter_side(s_local, f, &po)) mine = po.buttons;
    }
    s_local_btn = (uint16_t)(mine | (ns_in_dance() ? PAD_START : 0));
    out->buttons = s_local == 0 ? s_local_btn : s_remote_btn;
    return 1;
}

/* Port 2 is a controller source while linked: it plugs a pad in (so 2PLAYER GAME opens without a
 * second controller). Port 1 is resolved first each frame, so s_local_btn is current. */
static int ns_port2_source(PSXModControllerState* st) {
    st->buttons = !s_routing ? 0xFFFFu : (s_local == 1 ? s_local_btn : s_remote_btn);
    st->lx = st->ly = st->rx = st->ry = 0x80; st->analog = 0;
    return 1;
}

static void ns_pads_frame(void) {
    const int mode = (int16_t)psx_mod_read_half(NS_MODE);
    static int s_attached;
    if (s_linked != s_attached) {
        static PSXModPadTransform t;
        t.struct_size = sizeof t; t.allowed_types = PSX_MOD_PAD_TYPE_BIT(PSX_MOD_PAD_DIGITAL);
        t.initial_type = PSX_MOD_PAD_DIGITAL; t.transform = ns_pad_transform;
        s_attached = s_linked;
        int a = 0, b;
        if (s_linked) a = psx_mod_set_pad_transform(0, &t); else bag2jp_mods_menu_reattach();
        b = psx_mod_set_controller_source(1, s_linked ? ns_port2_source : NULL) +
            2 * psx_mod_set_pad_transform(1, s_linked ? &t : NULL);
        if (!s_linked && bag2jp_charsel_enabled()) bag2jp_charsel_reattach();   /* select-screen popup */
        ns_log("v%u pad transforms %s %d %d", s_vblanks, s_linked ? "on" : "off", a, b);
    }
    const int want = s_linked && mode == 2;
    if (want != s_routing) {
        const int was_routing = s_routing;
        s_routing = want;
        ns_log("v%u pad routing %s (P%d local)", s_vblanks, want ? "on" : "off", s_local + 1);
        s_remote_btn = s_local_btn = 0xFFFF; s_remote_hold = 0;
        if (was_routing && !want && s_lobby_role >= 0) {
            ns_disconnect_locked("backed out to menu");
            bag2jp_lobby_ui_return_from_match();
            return;
        }
    }
    if (!s_routing) return;
    if (s_local_btn != s_last_local) {
        s_last_local = s_local_btn;
        s_out_btn[s_out_seq % EV_N] = s_local_btn; s_out_seq++;
        ns_send_pads();
    }
    if (ns_in_dance()) { s_remote_btn = 0xFFFF; s_in_applied = s_in_seq; return; }
    if (s_remote_hold > 0) { s_remote_hold--; return; }
    if (s_in_applied < s_in_seq) {
        s_remote_btn = s_in_btn[s_in_applied % EV_N]; s_in_applied++; s_remote_hold = 1;
    }
}

/* ------------------------------------------------------------------ match */
static uint32_t ns_timer(void* u, SDL_TimerID id, uint32_t interval);
static void ns_activate(void) {
    bag2jp_lobby_ui_init("127.0.0.1", 47400, "Player", bag2jp_bag1_content_id());
    char v[32] = {0};
    s_transport = NS_OFF;
    if (psx_mod_current_option_value("transport", v, sizeof v) > 0) {
        if (!strcmp(v, "loopback")) s_transport = NS_LOOPBACK;
        else if (!strcmp(v, "lan")) s_transport = NS_LAN;
        else if (!strcmp(v, "internet")) s_transport = NS_INTERNET;
        else if (!strcmp(v, "direct")) s_transport = NS_DIRECT;
    }
    ns_log("activate: transport %s (%d)", v, s_transport);
    if (s_transport >= NS_LAN && s_data == INVALID_SOCKET) ns_net_open();
    if (s_transport >= NS_LAN && !s_mu) s_mu = SDL_CreateMutex();
    if (s_transport >= NS_LAN && !s_timer) s_timer = SDL_AddTimer(16, ns_timer, NULL);
}

static void ns_match_start(void) {
    s_match++; memset(s_theirs, 0, sizeof s_theirs); s_mine.valid = 0; s_mine.bar = -1; s_wait_bar = -1;
    memset(s_my_score_bar, 0xFF, sizeof s_my_score_bar); s_desync_reported = 0;
    /* Start barrier: the match module just loaded; both PCs run from here in step, so hold this one
     * until the other has loaded too (max 5 s). The game is still loading, so the wait is unseen. */
    const uint64_t t0 = SDL_GetTicks();
    uint8_t b[32]; int n = ns_hdr(b, M_READY); memcpy(b + n, &s_match, 2); n += 2;
    uint64_t sent = 0;
    while (s_linked && s_peer_ready != s_match && SDL_GetTicks() - t0 < 5000) {
        if (SDL_GetTicks() - sent >= 20) { ns_send(b, n); sent = SDL_GetTicks(); }
        ns_net_poll(); SDL_Delay(1);
    }
    for (int i = 0; i < 3; ++i) ns_send(b, n);
    s_match_live = 1; s_dance_frames = 0; s_peer_pause_known = 0; s_pause_at = 0;
    ns_log("v%u match %u starts (waited %llu ms for the other PC%s, %d ms ping, %s)", s_vblanks, s_match,
           (unsigned long long)(SDL_GetTicks() - t0), s_peer_ready == s_match ? "" : ", gave up", s_rtt_ms,
           s_ch == CH_UDP ? "direct" : "relay");
}

static void ns_check_scores(int bar) {
    const NsStep* t = &s_theirs[(bar / 4) & 63];
    const int slot = (bar / 4) & 63;
    if (!t->valid || t->bar != bar || s_my_score_bar[slot] != bar) return;
    if (!memcmp(t->check, s_my_check[slot], sizeof t->check)) return;
    ns_log("v%u bar %d OUT OF SYNC: here cool %d/%d right %d/%d, other PC cool %d/%d right %d/%d", s_vblanks, bar,
           s_my_check[slot][0], s_my_check[slot][1], s_my_check[slot][2], s_my_check[slot][3],
           t->check[0], t->check[1], t->check[2], t->check[3]);
    if (!s_desync_reported) { s_desync_reported = 1; host_osd_push("ONLINE  scores differ from the other PC (out of sync)", 6000); }
}

/* ------------------------------------------------------------------ pause */
static void ns_pause_status(const char* m) {
    if (!strcmp(m, s_pause_msg)) return;
    snprintf(s_pause_msg, sizeof s_pause_msg, "%s", m);
    host_osd_set_status(m);
}

static void ns_pause_end(const char* why) {
    if (!s_pause_held) return;
    psx_host_pause_pop(); s_pause_held = 0; s_resume_at = 0; s_pause_msg[0] = 0;
    host_osd_set_status(""); ns_status_reset();
    ns_log("v%u pause ends (%s)", s_vblanks, why);
}

/* Called every frame, and from the timer while paused (both under s_mu). */
static void ns_pause_tick(void) {
    if (s_focus_always < 0) {
        const char* e = SDL_getenv("BAG2JP_NETSYNC_FOCUS");
        s_focus_always = !(e && !strcmp(e, "strict"));
    }
    const int lf = s_focus_always ? 1 : SDL_GetKeyboardFocus() != NULL;
    if (lf != s_lfocus) {
        s_lfocus = lf;
        if (lf && s_rfocus) s_resume_local = 1;
        ns_log("v%u this window %s", s_vblanks, lf ? "back in focus" : "lost focus");
        if (s_linked) ns_send_focus();
    }
    const int active = s_linked && s_routing && s_match_live;
    if (!active) { ns_pause_end(s_linked ? "dance over" : "link lost"); return; }
    if (!s_lfocus || !s_rfocus) {
        s_resume_at = 0;
        if (!s_pause_held && psx_host_pause_push("online")) {
            s_pause_held = 1; s_pause_at = s_dance_frames; s_peer_pause_known = 0;
            ns_send_focus();
            ns_log("v%u pause at dance frame %u (%s)", s_vblanks, s_pause_at,
                   !s_lfocus ? "this window lost focus" : "the other window lost focus");
        }
        if (s_pause_held)
            ns_pause_status(!s_lfocus ? "ONLINE  PAUSED  -  come back to the game window to continue"
                                      : "ONLINE  PAUSED  -  the other player left the game window");
        return;
    }
    if (!s_pause_held) return;
    const uint64_t now = SDL_GetTicks();
    if (!s_resume_at) {
        /* Both PCs count 3 s from the moment they see both windows in focus. The PC whose own window
         * came back sees it first, so it waits half a ping longer. What drift is left (the other PC
         * paused half a ping later) is absorbed by the bar hold like any network delay. */
        const int half_ping = (s_resume_local && s_rtt_ms > 0) ? s_rtt_ms / 2 : 0;
        s_resume_at = now + 3000 + (uint64_t)half_ping;
        ns_log("v%u both windows in focus: resume in %llu ms (dance frame %u, other PC paused at %d)", s_vblanks,
               (unsigned long long)(s_resume_at - now), s_pause_at, s_peer_pause_known ? (int)s_peer_pause_at : -1);
    }
    if (now >= s_resume_at) { ns_pause_end("both windows in focus"); return; }
    char m[80]; snprintf(m, sizeof m, "ONLINE  resuming in %d...", (int)((s_resume_at - now + 999) / 1000));
    ns_pause_status(m);
}

static uint32_t ns_timer(void* u, SDL_TimerID id, uint32_t interval) {
    (void)u; (void)id;
    if (!s_pause_held) return interval;
    SDL_LockMutex(s_mu);
    if (s_pause_held) { s_vblanks++; ns_net_poll(); ns_pause_tick(); }
    SDL_UnlockMutex(s_mu);
    return interval;
}

/* Test switch BAG2JP_AUDIO_PROBE=1: once a second, log the audio output buffer (how far the sound
 * heard lags the game) to bag2jp_audio_probe.log. Used to tune game.toml [audio] buffer_ms. */
extern int psx_audio_out_stats(double* fill_ms, double* target_ms, uint64_t* underruns,
                               uint64_t* overflow_drops, double* correction, int* legacy, int* host_rate);
static void ns_audio_probe(void) {
    static int on = -1; static FILE* f;
    if (on < 0) {
        on = SDL_getenv("BAG2JP_AUDIO_PROBE") != NULL;
        if (on) { const char* b = SDL_GetBasePath(); char p[1024];
                  snprintf(p, sizeof p, "%sbag2jp_audio_probe.log", b ? b : ""); f = fopen(p, "w"); }
    }
    if (!on || !f) return;
    static uint64_t last; const uint64_t now = SDL_GetTicks();
    if (last && now - last > 40) {
        double fl = 0, tg = 0, cr = 0; uint64_t un = 0, ov = 0; int lg = 0, rt = 0;
        psx_audio_out_stats(&fl, &tg, &un, &ov, &cr, &lg, &rt);
        fprintf(f, "v%u stall %llu ms (fill now %.1f ms, underruns %llu, dance %d)\n", s_vblanks,
                (unsigned long long)(now - last), fl, (unsigned long long)un, ns_in_dance());
    }
    last = now;
    if (s_vblanks % 60) return;
    double fill = 0, target = 0, corr = 0; uint64_t under = 0, over = 0; int legacy = 0, rate = 0;
    psx_audio_out_stats(&fill, &target, &under, &over, &corr, &legacy, &rate);
    fprintf(f, "v%u t%llu fill %.1f ms target %.1f underruns %llu overflow %llu corr %.4f legacy %d rate %d dance %d\n",
            s_vblanks, (unsigned long long)SDL_GetTicks(), fill, target, (unsigned long long)under,
            (unsigned long long)over, corr, legacy, rate, ns_in_dance());
    fflush(f);
}

static void ns_vblank(void) {
    bag2jp_lobby_ui_tick();
    s_vblanks++;
    ns_audio_probe();
    if (s_transport < NS_LAN) return;
    SDL_LockMutex(s_mu);
    ns_net_poll();
    ns_pads_frame();
    ns_status();
    if (s_mine.valid && s_vblanks - s_step_resend < 60 && (s_vblanks - s_step_resend) % 6 == 5) ns_send_step(&s_mine);
    const int dance = ns_in_dance();
    if (dance && !s_was_dance && s_routing) ns_match_start();
    if (!dance && s_was_dance) {
        if (s_lobby_role >= 0) ns_disconnect_locked("match finished");
        bag2jp_lobby_ui_return_from_match();
    }
    if (!dance) s_match_live = 0;
    s_was_dance = dance;
    if (s_match_live && !s_pause_held) s_dance_frames++;
    ns_pause_tick();
    SDL_UnlockMutex(s_mu);
}

static void ns_disconnect_locked(const char* why) {
    s_transport = NS_OFF;
    s_linked = 0;
    s_routing = 0;
    s_lobby_role = -1;
    s_local = -1;
    s_match_live = 0;
    s_was_dance = 0;
    bag2jp_mods_menu_reattach();
    (void)psx_mod_set_controller_source(1, NULL);
    (void)psx_mod_set_pad_transform(1, NULL);
    if (bag2jp_charsel_enabled()) bag2jp_charsel_reattach();
    if (s_data != INVALID_SOCKET) { closesocket(s_data); s_data = INVALID_SOCKET; }
    if (s_disc != INVALID_SOCKET) { closesocket(s_disc); s_disc = INVALID_SOCKET; }
    mq_drop(why);
    host_osd_set_status("");
    s_status_shown = -1;
    ns_log("v%u lobby netsync disconnected (%s)", s_vblanks, why ? why : "");
}

void bag2jp_netsync_disconnect_lobby(void) {
    if (!s_mu) return;
    SDL_LockMutex(s_mu);
    if (s_transport >= NS_LAN || s_linked) {
        ns_disconnect_locked("left online match");
    }
    SDL_UnlockMutex(s_mu);
}

static int ns_local_player(int mode) {
    if (s_transport >= NS_LAN) return (s_linked && mode == 2) ? s_local : -1;
    if (mode == 1) return (int8_t)psx_mod_read_byte(NS_HUMAN);
    if (mode == 2) return 0;
    return -1;
}

static void ns_read(int p, NsStep* s, int bar) {
    const uint32_t j = NS_JUDGE + (uint32_t)p * 0x24, pl = NS_PLAYER + (uint32_t)p * 0x32;
    s->bar = (int16_t)bar;
    s->state   = (int16_t)psx_mod_read_half(j + 0x08);
    s->timing  = (int16_t)psx_mod_read_half(j + 0x0C);
    s->cool    = psx_mod_read_byte(j + 0x0E);
    s->pressed = psx_mod_read_half(j + 0x12);
    s->result  = (int16_t)psx_mod_read_half(j + 0x14);
    s->command = (int16_t)psx_mod_read_half(pl + 0x02);
    s->valid = 1; s->match = s_match;
}

/* A right bar carries the sender's command id; here the bar may have another id (random
 * commands), so "right" is mapped to this PC's command for that player. */
static void ns_write(int p, const NsStep* s) {
    const uint32_t j = NS_JUDGE + (uint32_t)p * 0x24, pl = NS_PLAYER + (uint32_t)p * 0x32;
    int16_t result = s->result;
    if (result != 0 && result != 0x6E && result != 0xAA && result == s->command)
        result = (int16_t)psx_mod_read_half(pl + 0x02);
    psx_mod_write_half(j + 0x08, (uint16_t)s->state);
    psx_mod_write_half(j + 0x0C, (uint16_t)s->timing);
    psx_mod_write_byte(j + 0x0E, s->cool);
    psx_mod_write_half(j + 0x12, s->pressed);
    psx_mod_write_half(j + 0x14, (uint16_t)result);
}

static void ns_gate_body(struct CPUState* cpu, uint32_t address) {
    if (s_transport < NS_LAN || cpu->gpr[2] != 0) return;      /* window still open */
    const int mode = (int16_t)psx_mod_read_half(NS_MODE);
    const int local = ns_local_player(mode);
    if (local < 0) return;
    const int bar = (int16_t)psx_mod_read_half(NS_BAR);
    if (s_wait_bar != bar) {                                    /* first frame of this bar's close */
        s_wait_bar = bar; s_wait_frames = 0;
        const int slot = (bar / 4) & 63;
        s_my_scores[slot][0] = (int32_t)psx_mod_read_word(NS_SCORE);
        s_my_scores[slot][1] = (int32_t)psx_mod_read_word(NS_SCORE + 4u);
        for (int i = 0; i < 2; ++i) {
            s_my_check[slot][i] = (int32_t)psx_mod_read_word(NS_COOLS + 4u * (uint32_t)i);
            s_my_check[slot][2 + i] = (int32_t)psx_mod_read_word(NS_GOODS + 4u * (uint32_t)i);
        }
        s_my_score_bar[slot] = (int16_t)bar;
        const char* ap2_env = getenv("BAG2JP_NETSYNC_AUTOPLAY");
        const unsigned ap2_mask = (ap2_env && ap2_env[0]) ? (unsigned)atoi(ap2_env) : 0u;
        const int ap2_local = (ap2_mask & (1u << (unsigned)local)) != 0;
        const uint32_t cmd = psx_mod_read_half(NS_PLAYER + (uint32_t)local * 0x32 + 0x02);
        (void)psx_mod_call_guest(cpu, NS_FN_CLOSE, address, (uint32_t)local, cmd, 0, 0);
        ns_read(local, &s_mine, bar);
        if (ap2_local && s_mine.command > 0) {
            const char* atk_env = getenv("BAG2JP_NETSYNC_ATTACKS");
            const int force_atk = (atk_env && atk_env[0] == '1') && (bar == 72 || bar == 136);
            s_mine.state = 0;
            s_mine.timing = 0;
            s_mine.cool = 1;
            s_mine.result = force_atk ? (int16_t)0x6E : s_mine.command;
        }
        s_mine.score[0] = s_my_scores[slot][0]; s_mine.score[1] = s_my_scores[slot][1];
        memcpy(s_mine.check, s_my_check[slot], sizeof s_mine.check);
        s_step_resend = s_vblanks;
        ns_send_step(&s_mine);
        ns_log("v%u bar %d mine state %d timing %d result 0x%x score %d/%d check %d/%d/%d/%d", s_vblanks, bar,
               s_mine.state, s_mine.timing, (uint16_t)s_mine.result, s_mine.score[0], s_mine.score[1],
               s_mine.check[0], s_mine.check[1], s_mine.check[2], s_mine.check[3]);
    }
    const NsStep* t = &s_theirs[(bar / 4) & 63];
    if (t->valid && t->bar == bar) { ns_check_scores(bar); return; }
    if (++s_wait_frames <= NS_WAIT_MAX) { cpu->gpr[2] = 1; return; }   /* hold the bar */
    if (s_wait_frames == NS_WAIT_MAX + 1) ns_log("v%u bar %d: no step from the other PC, scored as a miss", s_vblanks, bar);
}

/* Hold the beat that would start the next bar while this bar still waits for the other PC. */
static void ns_advance_body(struct CPUState* cpu, uint32_t address) {
    (void)address;
    if (s_transport < NS_LAN || cpu->gpr[2] != 0 || !s_routing) return;
    if ((psx_mod_read_half(NS_BEAT) & 3) != 0 || psx_mod_read_byte(NS_BAR_DONE)) return;
    const int bar = (int16_t)psx_mod_read_half(NS_BAR);
    if (s_wait_bar != bar) return;                              /* this bar never reached its close */
    /* Hold even when the result has just arrived: the advance runs before the bar's resolve in
     * the same frame, so letting it through now would drop the bar. Next frame it resolves. */
    if (s_wait_frames > NS_WAIT_MAX) return;
    cpu->gpr[2] = 1;
    static int logged_bar = -1;
    if (logged_bar != bar) { logged_bar = bar; ns_log("v%u bar %d: holding the next bar for the other PC", s_vblanks, bar); }
}

static void ns_hook_body(struct CPUState* cpu, uint32_t address) {
    (void)address;
    const int p = (int)cpu->gpr[20];
    const int mode = (int16_t)psx_mod_read_half(NS_MODE);
    const int bar = (int16_t)psx_mod_read_half(NS_BAR);
    if (s_transport == NS_OFF || (p != 0 && p != 1)) return;
    const int local = ns_local_player(mode);
    if (local < 0) return;
    if (s_transport == NS_LOOPBACK) {
        if (p == local) { ns_read(p, &s_mine, bar); return; }
        if (s_mine.bar != bar) return;
        ns_write(p, &s_mine);
        return;
    }
    if (p == local) { if (s_mine.bar == bar) ns_write(p, &s_mine); }
    else {
        const NsStep* t = &s_theirs[(bar / 4) & 63];
        if (t->valid && t->bar == bar) ns_write(p, t);
        else {                    /* no step in time: a miss, or nothing when this bar has no steps */
            NsStep miss; memset(&miss, 0, sizeof miss); miss.state = -1;
            if (s_mine.bar == bar && s_mine.result == -1) miss.result = -1;
            ns_write(p, &miss);
        }
    }
    if (p == 1) {
        NsStep a, b; ns_read(0, &a, bar); ns_read(1, &b, bar);
        ns_log("v%u bar %d resolve: P1 result 0x%x timing %d / P2 result 0x%x timing %d", s_vblanks, bar,
               (uint16_t)a.result, a.timing, (uint16_t)b.result, b.timing);
    }
}

static void ns_gate(struct CPUState* cpu, uint32_t address) {
    SDL_LockMutex(s_mu); ns_gate_body(cpu, address); SDL_UnlockMutex(s_mu);
}
static void ns_advance(struct CPUState* cpu, uint32_t address) {
    SDL_LockMutex(s_mu); ns_advance_body(cpu, address); SDL_UnlockMutex(s_mu);
}
static void ns_hook(struct CPUState* cpu, uint32_t address) {
    SDL_LockMutex(s_mu); ns_hook_body(cpu, address); SDL_UnlockMutex(s_mu);
}

PSX_MOD_CONSTRUCTOR(bag2jp_register_netsync) {
    bag2jp_lobby_ui_init("127.0.0.1", 47400, "Player", 0);
    (void)psx_mod_register_vblank_plugin("bag2jp.lobby", bag2jp_lobby_ui_tick);
    (void)psx_mod_register_activation_plugin("bag2jp.netsync", ns_activate);
    (void)psx_mod_register_vblank_plugin("bag2jp.netsync", ns_vblank);
    (void)psx_mod_register_instruction_plugin("bag2jp.netsync", NS_SITE, NS_WORD, ns_hook);
    (void)psx_mod_register_instruction_plugin("bag2jp.netsync", NS_GATE, NS_GATE_WORD, ns_gate);
    (void)psx_mod_register_instruction_plugin("bag2jp.netsync", NS_ADVANCE, NS_ADVANCE_WORD, ns_advance);
}

/* The character-select popup stays off while two PCs are linked (choices are not synced). */
int bag2jp_netsync_linked(void) { return s_linked; }
