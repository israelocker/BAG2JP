/* International 2P VS loading screen (package bag2jp.localization.regional, option vs_screen).
 *
 * Port of the US (SLUS-01159) loading-screen art: SLUS FUN_80033324 draws, for game modes 0 and 2,
 * red/blue flames, both portraits (P2 mirrored except chars 9-11), the names (CLUT row = command
 * difficulty) and the VS logo from per-character BUST2.BIN entries the JP disc does not have. JP
 * shows "P1 VS P2 / NOW LOADING" text instead (FUN_800342dc). The announcer voices and the wait
 * for them are the same in both versions, so only the picture is ported: it is composed from HD
 * layers (resource vs_hd, built by tools/build_vs.py from the US TIMs) on a worker thread and drawn
 * full-window on the host HUD layer while the JP loading function runs.
 * JP RAM: mode 0x8005D2C4, P1/P2 char 0x80089250/51 (&0x1F, 0xFF = none), difficulty 0x8005E6CC[p],
 * loading-function timer 0x80089210 and frame counter 0x80089214 (change every call), state
 * 0x80089215 / announcer step 0x80089234 (0x0C and > 3 = loading finished, match starts). */
#include "mod_plugins.h"
#include "gpu_gl_renderer.h"
#include "bag2jp_hud.h"
#include "../psxrecomp/runtime/third_party/stb_image.h"
#include <SDL3/SDL.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>

#define VS_W 2048
#define VS_H 1536
#define VS_SX 4.0
#define VS_SY 6.4
#define A_MODE  0x8005D2C4u
#define A_P1    0x80089250u
#define A_DIFF  0x8005E6CCu
#define A_TIMER 0x80089210u
#define A_COUNT 0x80089214u
#define A_STATE 0x80089215u   /* loading state; 0x0C + voice step > 3 = finished */
#define A_VOICE 0x80089234u

static char s_dir[1024];
static int s_enabled;
static uint32_t s_last_timer, s_last_count;
static int s_hold;
static atomic_int s_visible;
static atomic_int s_want_key = -1;        /* p1 | p2<<5 | d1<<10 | d2<<12 */
static int s_ready_key = -1;               /* key of s_front */
static uint32_t* s_front;                  /* VS_W*VS_H BGRA, guarded by s_lock */
static int s_front_seq, s_drawn_seq;
static SDL_Mutex* s_lock;
static SDL_Condition* s_wake;
static SDL_Thread* s_thread;

static FILE* s_logf;
static void vs_log(const char* fmt, ...) {
    if (!s_logf) {
        const char* b = SDL_GetBasePath(); char p[1024];
        snprintf(p, sizeof p, "%sbag2jp_vs_screen.log", b ? b : "");
        s_logf = fopen(p, "w"); if (!s_logf) return;
    }
    va_list ap; va_start(ap, fmt); vfprintf(s_logf, fmt, ap); va_end(ap);
    fputc('\n', s_logf); fflush(s_logf);
}

/* ------------------------------------------------------------------ layers (worker thread) */
typedef struct { int w, h; unsigned char* px; } Layer;   /* RGBA */
static int load_layer(const char* name, Layer* L) {
    char p[1200]; snprintf(p, sizeof p, "%s/%s.png", s_dir, name);
    L->px = NULL; L->w = L->h = 0;
    FILE* f = fopen(p, "rb"); if (!f) { vs_log("missing %s", p); return 0; }
    fseek(f, 0, SEEK_END); long n = ftell(f); fseek(f, 0, SEEK_SET);
    unsigned char* buf = (unsigned char*)malloc((size_t)n);
    if (!buf || fread(buf, 1, (size_t)n, f) != (size_t)n) { fclose(f); free(buf); return 0; }
    fclose(f);
    int c = 0; L->px = stbi_load_from_memory(buf, (int)n, &L->w, &L->h, &c, 4); free(buf);
    return L->px != NULL;
}
static void free_layer(Layer* L) { if (L->px) stbi_image_free(L->px); L->px = NULL; }

/* psx coordinates (512x240 screen) -> canvas */
static void put(uint32_t* cv, const Layer* L, double x, double y, int additive) {
    if (!L->px) return;
    const int X = (int)(x * VS_SX + 0.5), Y = (int)(y * VS_SY + 0.5);
    for (int j = 0; j < L->h; ++j) {
        const int yy = Y + j; if (yy < 0 || yy >= VS_H) continue;
        const unsigned char* s = L->px + (size_t)j * L->w * 4;
        uint32_t* d = cv + (size_t)yy * VS_W;
        for (int i = 0; i < L->w; ++i, s += 4) {
            const int xx = X + i; if (xx < 0 || xx >= VS_W) continue;
            const unsigned a = s[3]; if (!a) continue;
            const uint32_t o = d[xx];
            unsigned ob = o & 255, og = (o >> 8) & 255, orr = (o >> 16) & 255, r, g, b;
            if (additive) {
                r = orr + s[0] * a / 255; g = og + s[1] * a / 255; b = ob + s[2] * a / 255;
                if (r > 255) r = 255; if (g > 255) g = 255; if (b > 255) b = 255;
            } else {
                r = (s[0] * a + orr * (255 - a)) / 255; g = (s[1] * a + og * (255 - a)) / 255;
                b = (s[2] * a + ob * (255 - a)) / 255;
            }
            d[xx] = 0xFF000000u | (r << 16) | (g << 8) | b;
        }
    }
}

static void put_name(uint32_t* cv, int c, int diff, double cx, double cy) {
    char n[32]; Layer L; snprintf(n, sizeof n, "c%02d_name%d", c, diff);
    if (!load_layer(n, &L)) return;
    put(cv, &L, cx - (L.w / VS_SX) / 2.0, cy - (L.h / VS_SY) / 2.0, 0);   /* centred like the US code */
    free_layer(&L);
}

static int compose(uint32_t* cv, int p1, int p2, int d1, int d2) {
    for (int i = 0; i < VS_W * VS_H; ++i) cv[i] = 0xFF000000u;
    char n[32]; Layer L; int ok = 1;
    /* back slot (drawn first): blue flames, red flames, P2 portrait, P1 portrait */
    if (load_layer("flames_blue", &L)) { put(cv, &L, 256, 0, 0); free_layer(&L); } else ok = 0;
    if (load_layer("flames_red", &L)) { put(cv, &L, 0, 0, 0); free_layer(&L); } else ok = 0;
    snprintf(n, sizeof n, "c%02d_p2", p2); if (load_layer(n, &L)) { put(cv, &L, 256, 0, 0); free_layer(&L); } else ok = 0;
    snprintf(n, sizeof n, "c%02d_p1", p1); if (load_layer(n, &L)) { put(cv, &L, 0, 0, 0); free_layer(&L); } else ok = 0;
    /* front slot: VS, P2 extra, P2 name, P1 extra, P1 name */
    if (load_layer("vs", &L)) { put(cv, &L, 256 - (L.w / VS_SX) / 2.0, 204 - (L.h / VS_SY) / 2.0, 0); free_layer(&L); }
    if (p2 == 11 || p2 == 13) {
        snprintf(n, sizeof n, "c%02d_p2x", p2);
        if (load_layer(n, &L)) { put(cv, &L, p2 == 11 ? 300 : 304, p2 == 11 ? 44 : 0, 1); free_layer(&L); }
    }
    put_name(cv, p2, d2, 400, 204);
    if (p1 == 11 || p1 == 13) {
        snprintf(n, sizeof n, "c%02d_p1x", p1);
        if (load_layer(n, &L)) { put(cv, &L, p1 == 11 ? 98 : 6, p1 == 11 ? 44 : 0, 1); free_layer(&L); }
    }
    put_name(cv, p1, d1, 112, 204);
    return ok;
}

static int worker(void* arg) {
    (void)arg;
    uint32_t* cv = (uint32_t*)malloc((size_t)VS_W * VS_H * 4);
    if (!cv) return 0;
    for (;;) {
        SDL_LockMutex(s_lock);
        while (atomic_load(&s_want_key) < 0 || atomic_load(&s_want_key) == s_ready_key)
            SDL_WaitCondition(s_wake, s_lock);
        const int key = atomic_load(&s_want_key);
        SDL_UnlockMutex(s_lock);
        const uint64_t t0 = SDL_GetTicksNS();
        const int ok = compose(cv, key & 31, (key >> 5) & 31, (key >> 10) & 3, (key >> 12) & 3);
        SDL_LockMutex(s_lock);
        memcpy(s_front, cv, (size_t)VS_W * VS_H * 4);
        s_ready_key = key; s_front_seq++;
        SDL_UnlockMutex(s_lock);
        vs_log("composed P1 %d vs P2 %d (difficulty %d/%d) ok=%d in %.0f ms", key & 31, (key >> 5) & 31,
               (key >> 10) & 3, (key >> 12) & 3, ok, (double)(SDL_GetTicksNS() - t0) / 1e6);
    }
}

/* ------------------------------------------------------------------ render thread */
static void vs_draw(int width, int height, void* ctx) {
    (void)ctx;
    if (!atomic_load(&s_visible) || !s_lock) return;
    SDL_LockMutex(s_lock);
    if (s_ready_key >= 0 && s_ready_key == atomic_load(&s_want_key)) {
        const int upload = s_front_seq != s_drawn_seq;
        gl_renderer_draw_host_movie(s_front, VS_W, VS_H, upload, width, height);
        s_drawn_seq = s_front_seq;
    }
    SDL_UnlockMutex(s_lock);
}

/* ------------------------------------------------------------------ emulation thread */
static void vs_vblank(void) {
    if (!s_enabled) return;
    const uint32_t t = psx_mod_read_word(A_TIMER), c = psx_mod_read_byte(A_COUNT);
    if (t != s_last_timer || c != s_last_count) s_hold = 45;   /* bridges blocking CD loads */
    else if (s_hold > 0) s_hold--;
    s_last_timer = t; s_last_count = c;
    const int mode = (int16_t)psx_mod_read_half(A_MODE);
    const int p1 = psx_mod_read_byte(A_P1), p2 = psx_mod_read_byte(A_P1 + 1);
    const int done = psx_mod_read_byte(A_STATE) == 0x0C && psx_mod_read_byte(A_VOICE) > 3;
    if (done) s_hold = 0;
    int vis = s_hold > 0 && (mode == 0 || mode == 2) && p1 != 0xFF && p2 != 0xFF &&
              (p1 & 31) < 18 && (p2 & 31) < 18;
    /* compose as soon as both characters are known (stage select), so the picture is ready
     * on the first loading frame */
    const int armed = (mode == 0 || mode == 2) && p1 != 0xFF && p2 != 0xFF && (p1 & 31) < 18 && (p2 & 31) < 18;
    if (armed) {
        int d1 = psx_mod_read_byte(A_DIFF) & 3, d2 = psx_mod_read_byte(A_DIFF + 1) & 3;
        if (d1 > 2) d1 = 2; if (d2 > 2) d2 = 2;
        const int key = (p1 & 31) | ((p2 & 31) << 5) | (d1 << 10) | (d2 << 12);
        if (atomic_load(&s_want_key) != key) {
            SDL_LockMutex(s_lock); atomic_store(&s_want_key, key); SDL_SignalCondition(s_wake); SDL_UnlockMutex(s_lock);
        }
    }
    if (vis != atomic_load(&s_visible)) {
        atomic_store(&s_visible, vis);
        vs_log("%s (mode %d, P1 %02X, P2 %02X)", vis ? "show" : "hide", mode, p1, p2);
    }
}

static void vs_activate(void) {
    char v[32] = {0};
    s_enabled = 0; atomic_store(&s_visible, 0);
    if (psx_mod_current_option_value("vs_screen", v, sizeof v) <= 0 || strcmp(v, "international") != 0) return;
    if (psx_mod_current_resource_path("vs_hd", s_dir, sizeof s_dir) <= 0) { vs_log("no vs_hd resource"); return; }
    if (!s_lock) { s_lock = SDL_CreateMutex(); s_wake = SDL_CreateCondition(); }
    if (!s_front) s_front = (uint32_t*)calloc((size_t)VS_W * VS_H, 4);
    if (!s_lock || !s_wake || !s_front) return;
    if (!s_thread) s_thread = SDL_CreateThread(worker, "bag2jp-vs-screen", NULL);
    if (!s_thread) return;
    bag2jp_hud_add(vs_draw, NULL);
    s_enabled = 1;
    vs_log("activate: layers '%s'", s_dir);
}

PSX_MOD_CONSTRUCTOR(bag2jp_register_vs_screen) {
    (void)psx_mod_register_activation_plugin("bag2jp.vs_screen", vs_activate);
    (void)psx_mod_register_vblank_plugin("bag2jp.vs_screen", vs_vblank);
}
