/* Online step sync (package bag2jp.feature.netsync, feature "online").
 *
 * Same idea as the BAG1 port's bag.netsync: each PC plays the match itself and only the result
 * of each bar travels, so lag barely matters and every mod stays on.
 *
 * The match is an ordinary 2-player battle on both PCs. Whoever is P1 (the host) and P2 is
 * decided when the two games find each other. In the menus (character, difficulty, stage) the
 * other player's buttons arrive over the network and drive their side; in the dance their side
 * gets a neutral pad and each bar is scored from the result they send.
 *
 * Match module system/005.dbi (base 0x8008F890), FUN_80099e90, once per bar:
 *   0x8009ABC4 bnez $v0 -> skip: taken while the bar's input window is still open. Here, when it
 *     opens, the local player's bar is closed with the game's own FUN_800120f8(player, command)
 *     and sent; while the other player's result has not arrived the skip is forced (up to
 *     NS_WAIT_MAX frames), so both PCs resolve the bar with the same two results.
 *   0x8009B084 sw $s1,0x20($v0): join point of the per-player loop body ($s4 player, $s5 judge
 *     block 0x8005CF08+p*0x24, $s3 player block 0x8005E728+p*0x32). Judge +0x08 time of the
 *     finishing press, +0x0C timing offset, +0x12 pressed button, +0x0E COOL flag, +0x14 result
 *     (0 none, the bar's command id when right, 0x6E attack, 0xAA dodge); player +0x02 the
 *     bar's command id. Both players' values are written here before the bar is scored.
 * Transport "loopback" mirrors the local player onto the rival (one PC, for testing).
 * Log: bag2jp_netsync.log next to the game. Room code: bag2jp_online.txt next to the game. */
#include <winsock2.h>
#include <ws2tcpip.h>
#include <stdint.h>
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <ctype.h>
#include <SDL3/SDL.h>
#include "mod_plugins.h"
#include "cpu_state.h"
#include "host_osd.h"

#define NS_SITE       0x8009B084u   /* sw $s1, 0x20($v0) */
#define NS_WORD       0xAC510020u
#define NS_GATE       0x8009ABC4u   /* bnez $v0, skip */
#define NS_GATE_WORD  0x144005C8u
#define NS_FN_CLOSE   0x800120F8u   /* close a human player's bar: (player, command) */
#define NS_MODE       0x8005D2C4u   /* h: 0 demo, 1 one player vs CPU, 2 two players, 3 practice */
#define NS_HUMAN      0x8005E6C8u   /* b: the human player in mode 1 */
#define NS_BAR        0x8005E684u   /* h: beat index of the current bar */
#define NS_MODULE     0x8005F7CCu   /* b: loaded program module */
#define NS_JUDGE      0x8005CF08u
#define NS_PLAYER     0x8005E728u
#define NS_DISC_PORT  47300
#define NS_WAIT_MAX   30            /* frames a bar may wait for the other player's result */
#define PAD_START     0x0008u

enum { NS_OFF, NS_LOOPBACK, NS_LAN, NS_INTERNET };
enum { M_HELLO = 1, M_PAD = 3, M_STEP = 4, M_PING = 5, M_READY = 6 };

typedef struct {
    int16_t bar, state, timing, result, command;
    uint16_t pressed; uint8_t cool, valid; uint16_t match, pad;
} NsStep;

static int s_transport;
static uint32_t s_vblanks;
static FILE* s_logf;

/* session */
static SOCKET s_data = INVALID_SOCKET, s_disc = INVALID_SOCKET;
static uint32_t s_code_hash;
static uint64_t s_nonce, s_peer_nonce;
static struct sockaddr_in s_peer;
static int s_linked, s_local = -1;       /* s_local: 0 = this PC is P1 (host), 1 = P2 */
static uint32_t s_last_rx, s_last_hello;
static char s_code[64] = "BAG2";

/* steps */
static NsStep s_mine, s_theirs[64];       /* indexed by (bar/4) & 63 */
static int s_wait_bar = -1, s_wait_frames;
static uint32_t s_step_resend;

/* pads: local events out, remote events in */
#define EV_N 256
static uint16_t s_out_btn[EV_N]; static uint32_t s_out_seq;      /* next seq to assign */
static uint16_t s_in_btn[EV_N];  static uint32_t s_in_seq, s_in_applied;
static uint16_t s_local_btn = 0xFFFF, s_remote_btn = 0xFFFF, s_last_local = 0xFFFF;
static int s_remote_hold;
static int s_routing;                     /* pads routed through the network this frame */
static uint16_t s_match;                  /* matches started since the link (same count on both PCs) */
static int s_was_dance;
static int s_peer_ready = -1;            /* last match the other PC is ready to start */

static void ns_log(const char* fmt, ...) {
    if (!s_logf) {
        const char* b = SDL_GetBasePath(); char p[1024];
        snprintf(p, sizeof p, "%sbag2jp_netsync.log", b ? b : "");
        s_logf = fopen(p, "w"); if (!s_logf) return;
    }
    va_list ap; va_start(ap, fmt); vfprintf(s_logf, fmt, ap); va_end(ap);
    fputc('\n', s_logf); fflush(s_logf);
}

/* ------------------------------------------------------------------ network */
static void ns_send(const void* body, int n) {
    if (s_data == INVALID_SOCKET || !s_linked) return;
    sendto(s_data, (const char*)body, n, 0, (struct sockaddr*)&s_peer, sizeof s_peer);
}

static int ns_hdr(uint8_t* b, int type) {
    memcpy(b, "B2NS", 4); b[4] = 1; b[5] = (uint8_t)type; b[6] = b[7] = 0;
    memcpy(b + 8, &s_code_hash, 4);
    return 12;
}

static void ns_send_hello(const struct sockaddr_in* to) {
    uint8_t b[32]; int n = ns_hdr(b, M_HELLO);
    memcpy(b + n, &s_nonce, 8); n += 8;
    sendto(s_data, (const char*)b, n, 0, (const struct sockaddr*)to, sizeof *to);
}

static void ns_send_step(const NsStep* s) {
    uint8_t b[40]; int n = ns_hdr(b, M_STEP);
    memcpy(b + n, s, sizeof *s); n += (int)sizeof *s;
    ns_send(b, n);
}

static void ns_send_pads(void) {
    uint8_t b[12 + 4 + 16 * 4]; int n = ns_hdr(b, M_PAD);
    uint32_t first = s_out_seq > 16 ? s_out_seq - 16 : 0;
    memcpy(b + n, &first, 4); n += 4;
    for (uint32_t q = first; q < s_out_seq; ++q) { memcpy(b + n, &s_out_btn[q % EV_N], 2); n += 2; }
    ns_send(b, n);
}

static uint32_t ns_hash(const char* s) {
    uint32_t h = 2166136261u;
    for (; *s; ++s) {
        int c = toupper((unsigned char)*s);
        if (c == ' ' || c == '-' || c == '_') continue;
        h = (h ^ (uint32_t)c) * 16777619u;
    }
    return h;
}

static void ns_net_open(void) {
    WSADATA w; if (WSAStartup(MAKEWORD(2, 2), &w) != 0) { ns_log("WSAStartup failed"); return; }
    char* code = s_code;
    { const char* b = SDL_GetBasePath(); char p[1024];
      snprintf(p, sizeof p, "%sbag2jp_online.txt", b ? b : "");
      FILE* f = fopen(p, "r");
      if (f) { if (fgets(code, sizeof s_code, f)) code[strcspn(code, "\r\n")] = 0; fclose(f); }
      if (!code[0]) strcpy(code, "BAG2"); }
    s_code_hash = ns_hash(code);
    s_nonce = ((uint64_t)SDL_GetPerformanceCounter() << 16) ^ (uint64_t)SDL_GetTicksNS() ^ (uint64_t)(uintptr_t)&w;
    u_long nb = 1; BOOL yes = TRUE;
    s_data = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    struct sockaddr_in a; memset(&a, 0, sizeof a); a.sin_family = AF_INET; a.sin_addr.s_addr = htonl(INADDR_ANY);
    bind(s_data, (struct sockaddr*)&a, sizeof a);
    ioctlsocket(s_data, FIONBIO, &nb);
    setsockopt(s_data, SOL_SOCKET, SO_BROADCAST, (const char*)&yes, sizeof yes);
    s_disc = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    setsockopt(s_disc, SOL_SOCKET, SO_REUSEADDR, (const char*)&yes, sizeof yes);
    a.sin_port = htons(NS_DISC_PORT);
    if (bind(s_disc, (struct sockaddr*)&a, sizeof a) != 0) ns_log("discovery bind failed %d", WSAGetLastError());
    ioctlsocket(s_disc, FIONBIO, &nb);
    ns_log("net: room '%s' hash %08x nonce %016llx", code, s_code_hash, (unsigned long long)s_nonce);
}

static void ns_unlink(const char* why);
static void ns_on_packet(const uint8_t* b, int n, const struct sockaddr_in* from) {
    if (n < 12 || memcmp(b, "B2NS", 4) || b[4] != 1) return;
    uint32_t h; memcpy(&h, b + 8, 4); if (h != s_code_hash) return;
    const uint8_t* p = b + 12; n -= 12;
    switch (b[5]) {
    case M_HELLO: {
        if (n < 8) return;
        uint64_t nonce; memcpy(&nonce, p, 8);
        if (nonce == s_nonce) return;                          /* our own broadcast */
        if (!s_linked || nonce != s_peer_nonce) {
            s_peer = *from; s_peer_nonce = nonce; s_linked = 1;
            s_local = s_nonce > nonce ? 0 : 1;
            s_in_seq = s_in_applied = 0; s_out_seq = 0; s_match = 0; s_was_dance = 0; s_peer_ready = -1;
            memset(s_theirs, 0, sizeof s_theirs);
            ns_log("v%u linked with %s:%u, this PC is P%d", s_vblanks, inet_ntoa(from->sin_addr),
                   ntohs(from->sin_port), s_local + 1);
            ns_send_hello(from);
        }
        s_last_rx = s_vblanks;
        break; }
    case M_PAD: {
        if (n < 4) return;
        uint32_t first; memcpy(&first, p, 4);
        int k = (n - 4) / 2;
        for (int i = 0; i < k; ++i) {
            uint32_t q = first + (uint32_t)i;
            if (q < s_in_seq) continue;
            if (q > s_in_seq) break;                          /* gap: wait for a resend */
            memcpy(&s_in_btn[q % EV_N], p + 4 + 2 * i, 2); s_in_seq = q + 1;
        }
        s_last_rx = s_vblanks;
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
        s_last_rx = s_vblanks;
        break; }
    case M_PING: s_last_rx = s_vblanks; break;
    case M_READY: {
        if (n < 2) return;
        uint16_t m; memcpy(&m, p, 2); s_peer_ready = m; s_last_rx = s_vblanks;
        break; }
    }
}

static void ns_net_poll(void) {
    if (s_data == INVALID_SOCKET) return;
    uint8_t b[512]; struct sockaddr_in from; int fl;
    for (SOCKET so = s_disc; ; so = s_data) {
        for (;;) {
            fl = sizeof from;
            int n = recvfrom(so, (char*)b, sizeof b, 0, (struct sockaddr*)&from, &fl);
            if (n <= 0) break;
            ns_on_packet(b, n, &from);
        }
        if (so == s_data) break;
    }
    if (!s_linked && s_vblanks - s_last_hello >= 30) {           /* look for the other PC */
        s_last_hello = s_vblanks;
        struct sockaddr_in to; memset(&to, 0, sizeof to); to.sin_family = AF_INET;
        to.sin_port = htons(NS_DISC_PORT); to.sin_addr.s_addr = htonl(INADDR_BROADCAST);
        ns_send_hello(&to);
        to.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
        ns_send_hello(&to);
    }
    if (s_linked && s_vblanks - s_last_rx > 300) ns_unlink("nothing received for 5 s");
    if (s_linked && s_vblanks % 20 == 0) {
        uint8_t p[16]; int n = ns_hdr(p, M_PING); ns_send(p, n);
        ns_send_pads();
    }
}

/* ------------------------------------------------------------------ status */
static int s_status_shown = -1;
static void ns_status(void) {
    const int mode = (int16_t)psx_mod_read_half(NS_MODE);
    int want = !s_linked ? 0 : (s_routing ? 2 : 1);
    if (s_routing && psx_mod_read_word(NS_SITE) == NS_WORD) want = 3;     /* dancing: keep it quiet */
    (void)mode;
    if (want == s_status_shown) return;
    s_status_shown = want;
    char m[160];
    switch (want) {
    case 0: snprintf(m, sizeof m, "ONLINE  room %s  -  looking for the other player...", s_code); break;
    case 1: snprintf(m, sizeof m, "ONLINE  connected, you are P%d  -  choose 2PLAYER GAME", s_local + 1); break;
    case 2: snprintf(m, sizeof m, "ONLINE  you are P%d", s_local + 1); break;
    default: m[0] = 0; break;
    }
    host_osd_set_status(m);
}

static void ns_unlink(const char* why) {
    ns_log("v%u link lost: %s", s_vblanks, why);
    host_osd_push("ONLINE  the other player left", 4000);
    s_linked = 0; s_peer_nonce = 0;
}

/* ------------------------------------------------------------------ pads */
static int ns_in_dance(void) { return psx_mod_read_word(NS_SITE) == NS_WORD; }

static int ns_pad_transform(const PSXModPadFrame* f, PSXModPadOutput* out) {
    const int port = (int)f->player;
    if (port == 1) {                         /* exactly what the source decided, nothing else */
        out->buttons = !s_routing ? 0xFFFFu : (s_local == 1 ? s_local_btn : s_remote_btn);
        return 1;
    }
    if (!s_routing) return 0;
    if (port == 0) {                                          /* the host device is always P1's */
        s_local_btn = (uint16_t)(f->buttons | (ns_in_dance() ? PAD_START : 0));
        if (s_local == 0) { out->buttons = s_local_btn; return 1; }
        out->buttons = s_remote_btn; return 1;
    }
    return 0;
}

/* Port 2 is a controller source while linked: it plugs a pad in (so "2player game" opens
 * without a second controller) and carries the other player's buttons, or this PC's own when
 * this PC is P2. Port 1 is resolved first each frame, so s_local_btn is current. */
static int ns_port2_source(PSXModControllerState* st) {
    st->buttons = !s_routing ? 0xFFFFu : (s_local == 1 ? s_local_btn : s_remote_btn);
    st->lx = st->ly = st->rx = st->ry = 0x80; st->analog = 0;
    return 1;
}

static void ns_pads_frame(void) {
    const int mode = (int16_t)psx_mod_read_half(NS_MODE);
    static int s_attached;
    if (s_linked != s_attached) {
        /* While linked both ports go through the transform; it also keeps the empty port 2
         * from receiving the host pad (stock pad there repeats the keyboard). */
        static PSXModPadTransform t;
        t.struct_size = sizeof t; t.allowed_types = PSX_MOD_PAD_TYPE_BIT(PSX_MOD_PAD_DIGITAL);
        t.initial_type = PSX_MOD_PAD_DIGITAL; t.transform = ns_pad_transform;
        s_attached = s_linked;
        const int a = psx_mod_set_pad_transform(0, s_linked ? &t : NULL);
        const int b = psx_mod_set_controller_source(1, s_linked ? ns_port2_source : NULL) +
                      2 * psx_mod_set_pad_transform(1, s_linked ? &t : NULL);
        ns_log("v%u pad transforms %s %d %d", s_vblanks, s_linked ? "on" : "off", a, b);
    }
    const int want = s_linked && mode == 2;
    if (want != s_routing) {
        s_routing = want;
        ns_log("v%u pad routing %s (P%d local)", s_vblanks, want ? "on" : "off", s_local + 1);
        s_remote_btn = s_local_btn = 0xFFFF; s_remote_hold = 0;
    }
    if (!s_routing) return;
    /* local changes go out as ordered events */
    if (s_local_btn != s_last_local) {
        s_last_local = s_local_btn;
        s_out_btn[s_out_seq % EV_N] = s_local_btn; s_out_seq++;
        ns_send_pads();
    }
    /* remote events replay in order, each held at least two frames */
    if (ns_in_dance()) { s_remote_btn = 0xFFFF; s_in_applied = s_in_seq; return; }
    if (s_remote_hold > 0) { s_remote_hold--; return; }
    if (s_in_applied < s_in_seq) {
        s_remote_btn = s_in_btn[s_in_applied % EV_N]; s_in_applied++; s_remote_hold = 1;
    }
}

/* ------------------------------------------------------------------ steps */
static void ns_activate(void) {
    char v[32] = {0};
    s_transport = NS_OFF;
    if (psx_mod_current_option_value("transport", v, sizeof v) > 0) {
        if (!strcmp(v, "loopback")) s_transport = NS_LOOPBACK;
        else if (!strcmp(v, "lan")) s_transport = NS_LAN;
        else if (!strcmp(v, "internet")) s_transport = NS_INTERNET;
    }
    ns_log("activate: transport %s (%d)", v, s_transport);
    if (s_transport == NS_LAN && s_data == INVALID_SOCKET) ns_net_open();
}

static uint32_t s_last_dbg;
static void ns_vblank(void) {
    s_vblanks++;
    if (s_transport != NS_LAN) return;
    ns_net_poll();
    ns_pads_frame();
    ns_status();
    if (s_mine.valid && s_vblanks - s_step_resend >= 6 && s_vblanks - s_step_resend < 60) {
        if ((s_vblanks - s_step_resend) % 6 == 0) ns_send_step(&s_mine);
    }
    const int dance = ns_in_dance();
    if (dance && !s_was_dance && s_routing) {
        s_match++; memset(s_theirs, 0, sizeof s_theirs); s_mine.valid = 0; s_mine.bar = -1; s_wait_bar = -1;
        /* Start barrier: the match module just loaded; both PCs run from here in step, so hold
         * this one until the other has loaded too (at most 5 s). The game is still loading,
         * so the wait is not seen; afterwards the two songs run within the network delay. */
        const uint64_t t0 = SDL_GetTicks();
        uint8_t b[16]; int n = ns_hdr(b, M_READY); memcpy(b + n, &s_match, 2); n += 2;
        uint64_t sent = 0;
        while (s_linked && s_peer_ready != s_match && SDL_GetTicks() - t0 < 5000) {
            if (SDL_GetTicks() - sent >= 20) { ns_send(b, n); sent = SDL_GetTicks(); }
            ns_net_poll(); SDL_Delay(1);
        }
        for (int i = 0; i < 3; ++i) ns_send(b, n);
        ns_log("v%u match %u starts (waited %llu ms for the other PC%s)", s_vblanks, s_match,
               (unsigned long long)(SDL_GetTicks() - t0), s_peer_ready == s_match ? "" : ", gave up");
    }
    s_was_dance = dance;
    uint32_t dbg = psx_mod_read_byte(NS_MODULE) | (uint32_t)psx_mod_read_half(NS_MODE) << 8;
    if (dbg != s_last_dbg) { s_last_dbg = dbg; ns_log("v%u module %u mode %d", s_vblanks, dbg & 0xFF, (int16_t)(dbg >> 8)); }
}

static int ns_local_player(int mode) {
    if (s_transport == NS_LAN) return (s_linked && mode == 2) ? s_local : -1;
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

static void ns_gate(struct CPUState* cpu, uint32_t address) {
    if (s_transport != NS_LAN || cpu->gpr[2] != 0) return;      /* window still open */
    const int mode = (int16_t)psx_mod_read_half(NS_MODE);
    const int local = ns_local_player(mode);
    if (local < 0) return;
    const int bar = (int16_t)psx_mod_read_half(NS_BAR);
    if (s_wait_bar != bar) {                                    /* first frame of this bar's close */
        s_wait_bar = bar; s_wait_frames = 0;
        const uint32_t cmd = psx_mod_read_half(NS_PLAYER + (uint32_t)local * 0x32 + 0x02);
        (void)psx_mod_call_guest(cpu, NS_FN_CLOSE, address, (uint32_t)local, cmd, 0, 0);
        ns_read(local, &s_mine, bar);
        s_step_resend = s_vblanks;
        ns_send_step(&s_mine);
        ns_log("v%u bar %d mine state %d timing %d result 0x%x", s_vblanks, bar, s_mine.state,
               s_mine.timing, (uint16_t)s_mine.result);
    }
    const NsStep* t = &s_theirs[(bar / 4) & 63];
    if (t->valid && t->bar == bar) return;
    if (++s_wait_frames <= NS_WAIT_MAX) { cpu->gpr[2] = 1; return; }   /* hold the bar */
    if (s_wait_frames == NS_WAIT_MAX + 1) ns_log("v%u bar %d: no step from the other PC, scored as a miss", s_vblanks, bar);
}

static void ns_hook(struct CPUState* cpu, uint32_t address) {
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
        else { NsStep miss; memset(&miss, 0, sizeof miss); miss.state = -1; ns_write(p, &miss); }
    }
    if (p == 1) {                                   /* both written: what this PC scores */
        NsStep a, b; ns_read(0, &a, bar); ns_read(1, &b, bar);
        ns_log("v%u bar %d resolve: P1 result 0x%x timing %d / P2 result 0x%x timing %d", s_vblanks, bar,
               (uint16_t)a.result, a.timing, (uint16_t)b.result, b.timing);
    }
}

PSX_MOD_CONSTRUCTOR(bag2jp_register_netsync) {
    (void)psx_mod_register_activation_plugin("bag2jp.netsync", ns_activate);
    (void)psx_mod_register_vblank_plugin("bag2jp.netsync", ns_vblank);
    (void)psx_mod_register_instruction_plugin("bag2jp.netsync", NS_SITE, NS_WORD, ns_hook);
    (void)psx_mod_register_instruction_plugin("bag2jp.netsync", NS_GATE, NS_GATE_WORD, ns_gate);
}
