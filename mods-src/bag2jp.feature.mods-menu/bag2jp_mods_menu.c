/* In-game MODS menu (package bag2jp.feature.mods-menu).
 *
 * Adds a 4th entry "MODS" to the game's OPTION MODE menu (module system/002.dbi, base 0x8008F890,
 * FUN_80093388) and opens an HD, game-styled screen where every BAG2JP mod choice can be changed
 * with the pad. Choices are saved to mods/state.toml (psx_mod_feature_set_option / _enable +
 * psx_mod_save_selection, main = emulation thread); live-capable ones apply at once, the others on
 * the next start (marked '*').
 *
 * Game side (all guarded by the expected instruction words of module 002):
 *  - cursor limit of menu 0: byte 0x8009C794 2 -> 3; cursor position slot 3 of menu 0
 *    (0x8009C83C + 3*8) -> (70,170) below VIBRATION (70,141);
 *  - label: the VIBRATION text call `jal 0x8001FBFC` at 0x80093764 is redirected to a mod-defined
 *    guest function (0x0F000100) that draws VIBRATION and then "MODS" at y 172 (colour 6 when the
 *    cursor is on it, else 5), with the game's own text routine;
 *  - Circle on MODS: instruction hooks on the two `andi v0,v0,0x20` (Circle pressed, P1/P2) at
 *    0x8009355C / 0x80093570 clear the bit when the cursor is 3, so the game does not start its
 *    sub-menu transition, and open our screen instead;
 *  - while the screen is open (and until every button is released after closing) a pad transform
 *    gives the game a neutral pad and drives the screen.
 * Text uses the game's font 1 glyph table (pointer 0x8005E2B8[1]: +2 height, +4 3-byte u/v/width
 * records from ' ') over the HD font atlases of the texture pack (resource menu_assets). */
#include "mod_plugins.h"
#include "cpu_state.h"
#include "gpu_gl_renderer.h"
#include "bag2jp_hud.h"
#include "../psxrecomp/runtime/third_party/stb_image.h"
#include <SDL3/SDL.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <math.h>

/* ------------------------------------------------------------------ game addresses (JP) */
#define MM_FN_TEXT       0x8001FBFCu
#define MM_CALL_SITE     0x80093764u        /* jal 0x8001FBFC (VIBRATION) */
#define MM_CALL_WORD     0x0C007EFFu
#define MM_GUEST_FN      0x0F000100u
#define MM_CALL_PATCHED  (0x0C000000u | ((MM_GUEST_FN >> 2) & 0x03FFFFFFu))
#define MM_GUARD_ADDR    0x80093744u        /* addiu v0,v0,-0x6a8 ("VIBRATION") */
#define MM_GUARD_WORD    0x2442F958u
#define MM_CIRCLE_P1     0x8009355Cu
#define MM_CIRCLE_P2     0x80093570u
#define MM_ANDI_20       0x30420020u
#define MM_LIMIT         0x8009C794u
#define MM_CURSOR_POS3   (0x8009C83Cu + 3u * 8u)
#define MM_CURSOR        0x80191EBDu
#define MM_FONT_TABLES   0x8005E2B8u
#define MM_VIB_Y         143
#define MM_MODS_Y        172

/* ------------------------------------------------------------------ menu model */
typedef struct {
    const char* label;
    const char* pkg; const char* feat; const char* opt;   /* opt NULL = feature switch */
    int nvals; const char* vals[3]; const char* names[3];
    int def; int live;
    int cur, boot;
} MmItem;

#define REG "bag2jp.localization.regional", "regional"
#define JPI 2, {"japanese", "international"}, {"JAPANESE", "INTERNATIONAL"}
static MmItem s_items[] = {
    {"TITLE SCREEN",    REG, "title_screen",    JPI, 1, 0},
    {"BOOT LOGOS",      REG, "boot_logos",      JPI, 1, 0},
    {"HIRO ICON",       REG, "hiro_icon",       JPI, 1, 0},
    {"STAGE SIGNS",     REG, "stage_signs",     JPI, 1, 0},
    {"SONGS",           REG, "songs", 3, {"japanese", "international", "cd"}, {"JAPANESE", "ENGLISH", "CD QUALITY"}, 1, 0},
    {"ANNOUNCER",       REG, "announcer",       JPI, 1, 0},
    {"COMMAND BUTTONS", REG, "command_buttons", JPI, 1, 0},
    {"VS SCREEN",       REG, "vs_screen",       JPI, 1, 0},
    {"HD INTRO",        "bag2jp.enhancement.hd-intro", "hd-intro", NULL, 2, {"false", "true"}, {"OFF", "ON"}, 1, 0},
    {"HD FONT",         "psx.enhancement.hd-textures", "hd-textures", NULL, 2, {"false", "true"}, {"OFF", "ON"}, 0, 0},
    {"AUTOPLAY",        "bag2jp.feature.autoplay", "autoplay", "active", 2, {"false", "true"}, {"OFF", "ON"}, 1, 1},
};
#define MM_N ((int)(sizeof s_items / sizeof s_items[0]))

static int s_enabled, s_have_assets;
static char s_dir[1024];
static int s_open, s_sel, s_swallow;       /* emulation thread */
static uint32_t s_prev_buttons = 0xFFFFu;
static atomic_int s_visible, s_dirty;

static FILE* s_logf;
static void mm_log(const char* fmt, ...) {
    if (!s_logf) {
        const char* b = SDL_GetBasePath(); char p[1024];
        snprintf(p, sizeof p, "%sbag2jp_mods_menu.log", b ? b : "");
        s_logf = fopen(p, "w"); if (!s_logf) return;
    }
    va_list ap; va_start(ap, fmt); vfprintf(s_logf, fmt, ap); va_end(ap);
    fputc('\n', s_logf); fflush(s_logf);
}

/* ------------------------------------------------------------------ state.toml (current selection) */
static void mm_load_selection(void) {
    for (int i = 0; i < MM_N; ++i) s_items[i].cur = s_items[i].def;
    const char* b = SDL_GetBasePath(); char p[1200];
    snprintf(p, sizeof p, "%smods/state.toml", b ? b : "");
    FILE* f = fopen(p, "rb"); if (!f) return;
    char line[512], pkg[160] = "", feat[160] = "";
    int in_values = 0;
    while (fgets(line, sizeof line, f)) {
        char* s = line; while (*s == ' ' || *s == '\t') ++s;
        char* e = s + strlen(s); while (e > s && (e[-1] == '\n' || e[-1] == '\r' || e[-1] == ' ')) *--e = 0;
        if (!strcmp(s, "[[feature]]")) { pkg[0] = feat[0] = 0; in_values = 0; continue; }
        if (!strcmp(s, "[feature.values]")) { in_values = 1; continue; }
        if (s[0] == '[') { in_values = 0; pkg[0] = feat[0] = 0; continue; }
        char key[128], val[256];
        if (sscanf(s, "%127[^ =] = \"%255[^\"]\"", key, val) != 2 &&
            sscanf(s, "%127[^ =] = %255s", key, val) != 2) continue;
        if (!in_values && !strcmp(key, "package_id")) { snprintf(pkg, sizeof pkg, "%s", val); continue; }
        if (!in_values && !strcmp(key, "id")) { snprintf(feat, sizeof feat, "%s", val); continue; }
        for (int i = 0; i < MM_N; ++i) {
            MmItem* it = &s_items[i];
            if (strcmp(it->pkg, pkg) || strcmp(it->feat, feat)) continue;
            const char* want = it->opt ? (in_values ? it->opt : NULL) : (!in_values ? "enabled" : NULL);
            if (!want || strcmp(key, want)) continue;
            for (int k = 0; k < it->nvals; ++k) if (!strcmp(val, it->vals[k])) it->cur = k;
        }
    }
    fclose(f);
}

static void mm_apply(MmItem* it) {
    const char* v = it->vals[it->cur];
    int ok, live = 0;
    if (it->opt) {
        ok = psx_mod_feature_set_option(it->pkg, it->feat, it->opt, v);
        if (it->live) live = psx_mod_set_option_live(it->pkg, it->feat, it->opt, v) == 1;
    } else {
        ok = psx_mod_feature_enable(it->pkg, it->feat, it->cur != 0);
    }
    const int saved = psx_mod_save_selection();
    mm_log("set %s/%s/%s = %s (selection %d, saved %d, live %d)", it->pkg, it->feat,
           it->opt ? it->opt : "<enabled>", v, ok, saved, live);
}

/* ------------------------------------------------------------------ HD text rendering (render thread) */
#define CV_W 1280
#define CV_H 960
#define CV_SX (CV_W / 512.0)
#define CV_SY (CV_H / 240.0)
typedef struct { int w, h; unsigned char* px; } MmImg;
static MmImg s_font[2][16];                 /* [a=000.tim, b=001.tim][row] HD atlases (x6) */
static uint8_t s_glyph[96][3], s_glyph_h;   /* font 1, copied from guest RAM when opening */
static int s_have_glyphs;
static uint32_t* s_canvas;

static int mm_load_png(const char* name, MmImg* im) {
    char p[1200]; snprintf(p, sizeof p, "%s/%s", s_dir, name);
    im->px = NULL;
    FILE* f = fopen(p, "rb"); if (!f) return 0;
    fseek(f, 0, SEEK_END); long n = ftell(f); fseek(f, 0, SEEK_SET);
    unsigned char* buf = (unsigned char*)malloc((size_t)n);
    if (!buf || fread(buf, 1, (size_t)n, f) != (size_t)n) { fclose(f); free(buf); return 0; }
    fclose(f);
    int c; im->px = stbi_load_from_memory(buf, (int)n, &im->w, &im->h, &c, 4); free(buf);
    return im->px != NULL;
}
static MmImg* mm_font(int set, int row) {
    MmImg* im = &s_font[set][row & 15];
    if (!im->px) { char n[32]; snprintf(n, sizeof n, "font_%c%02d.png", set ? 'b' : 'a', row & 15); mm_load_png(n, im); }
    return im->px ? im : NULL;
}

static void cv_fill(int x0, int y0, int x1, int y1, uint32_t c) {
    if (x0 < 0) x0 = 0; if (y0 < 0) y0 = 0; if (x1 > CV_W) x1 = CV_W; if (y1 > CV_H) y1 = CV_H;
    for (int y = y0; y < y1; ++y) for (int x = x0; x < x1; ++x) s_canvas[y * CV_W + x] = c;
}
static void cv_round_rect(double px0, double py0, double px1, double py1, double r, uint32_t c) {
    const int x0 = (int)(px0 * CV_SX), y0 = (int)(py0 * CV_SY), x1 = (int)(px1 * CV_SX), y1 = (int)(py1 * CV_SY);
    const double R = r * CV_SX;
    for (int y = y0; y < y1; ++y) for (int x = x0; x < x1; ++x) {
        double dx = 0, dy = 0;
        if (x < x0 + R) dx = x0 + R - x; else if (x > x1 - R) dx = x - (x1 - R);
        if (y < y0 + R) dy = y0 + R - y; else if (y > y1 - R) dy = y - (y1 - R);
        if (dx * dx + dy * dy <= R * R && x >= 0 && y >= 0 && x < CV_W && y < CV_H) s_canvas[y * CV_W + x] = c;
    }
}

static void cv_dot(double px, double py, double r_canvas, uint32_t c) {
    const double cx = px * CV_SX, cy = py * CV_SY;
    for (int y = (int)(cy - r_canvas - 1); y <= (int)(cy + r_canvas + 1); ++y)
        for (int x = (int)(cx - r_canvas - 1); x <= (int)(cx + r_canvas + 1); ++x) {
            if (x < 0 || y < 0 || x >= CV_W || y >= CV_H) continue;
            const double d = sqrt((x + 0.5 - cx) * (x + 0.5 - cx) + (y + 0.5 - cy) * (y + 0.5 - cy));
            double a = r_canvas + 0.5 - d; if (a <= 0) continue; if (a > 1) a = 1;
            uint32_t* o = &s_canvas[y * CV_W + x];
            const unsigned r = (unsigned)(((c >> 16) & 255) * a + ((*o >> 16) & 255) * (1 - a));
            const unsigned g = (unsigned)(((c >> 8) & 255) * a + ((*o >> 8) & 255) * (1 - a));
            const unsigned b = (unsigned)((c & 255) * a + (*o & 255) * (1 - a));
            *o = 0xFF000000u | (r << 16) | (g << 8) | b;
        }
}

/* draw one glyph region (atlas texels u,v,w,h at 1x) at psx position, scale k (1 = native size) */
static void cv_glyph(const MmImg* at, int u, int v, int w, int h, double px, double py, double k) {
    const double S = at->w / 256.0;               /* HD atlas scale */
    const int dw = (int)(w * CV_SX * k + 0.5), dh = (int)(h * CV_SY * k + 0.5);
    const int X = (int)(px * CV_SX), Y = (int)(py * CV_SY);
    for (int j = 0; j < dh; ++j) {
        const double sy = (v + (j + 0.5) / dh * h) * S - 0.5;
        const int y0 = (int)sy; const double fy = sy - y0;
        if (Y + j < 0 || Y + j >= CV_H || y0 < 0 || y0 + 1 >= at->h) continue;
        for (int i = 0; i < dw; ++i) {
            const double sx = (u + (i + 0.5) / dw * w) * S - 0.5;
            const int x0 = (int)sx; const double fx = sx - x0;
            if (X + i < 0 || X + i >= CV_W || x0 < 0 || x0 + 1 >= at->w) continue;
            const unsigned char* a = at->px + ((size_t)y0 * at->w + x0) * 4;
            const unsigned char* b = a + 4; const unsigned char* c = a + (size_t)at->w * 4; const unsigned char* d = c + 4;
            double col[4];
            for (int ch = 0; ch < 4; ++ch)
                col[ch] = (a[ch] * (1 - fx) + b[ch] * fx) * (1 - fy) + (c[ch] * (1 - fx) + d[ch] * fx) * fy;
            const double al = col[3] / 255.0; if (al < 0.02) continue;
            uint32_t* o = &s_canvas[(Y + j) * CV_W + X + i];
            const unsigned ob = *o & 255, og = (*o >> 8) & 255, orr = (*o >> 16) & 255;
            const unsigned r = (unsigned)(col[0] * al + orr * (1 - al)), g = (unsigned)(col[1] * al + og * (1 - al)),
                           bb = (unsigned)(col[2] * al + ob * (1 - al));
            *o = 0xFF000000u | (r << 16) | (g << 8) | bb;
        }
    }
}
static double cv_text_w(const char* s, double k) {
    double w = 0;
    for (; *s; ++s) {
        const int c = (unsigned char)*s - 0x20;
        if (c <= 0 || c >= 96 || s_glyph[c][0] == 0xFF) { w += 9 * k; continue; }
        w += s_glyph[c][2] * k;
    }
    return w;
}
static void cv_text(const char* s, double x, double y, int set, int row, double k) {
    const MmImg* at = mm_font(set, row); if (!at || !s_have_glyphs) return;
    for (; *s; ++s) {
        const int c = (unsigned char)*s - 0x20;
        if (c <= 0 || c >= 96 || s_glyph[c][0] == 0xFF) { x += 9 * k; continue; }
        cv_glyph(at, s_glyph[c][0], s_glyph[c][1], s_glyph[c][2], s_glyph_h, x, y, k);
        x += s_glyph[c][2] * k;
    }
}

static void mm_compose(void) {
    if (!s_canvas) s_canvas = (uint32_t*)malloc((size_t)CV_W * CV_H * 4);
    if (!s_canvas) return;
    /* background like OPTION MODE: light blue, white rounded panel */
    for (int y = 0; y < CV_H; ++y) {
        const unsigned t = (unsigned)(y * 40 / CV_H);
        cv_fill(0, y, CV_W, y + 1, 0xFF000000u | ((110 - t) << 16) | ((185 - t) << 8) | (225 - t / 2));
    }
    cv_round_rect(26, 44, 494, 212, 8, 0xFF9AA4B4u);     /* shadow */
    cv_round_rect(20, 38, 488, 206, 8, 0xFFF0F0F0u);
    cv_text("MODS", 28, 8, 0, 6, 1.6);
    const double k = 0.72, row_h = s_glyph_h * k + 2.4, top = 46;
    for (int i = 0; i < MM_N; ++i) {
        const MmItem* it = &s_items[i];
        const int sel = i == s_sel, row = sel ? 6 : 5;
        const double y = top + i * row_h;
        const double cy = y + s_glyph_h * k * 0.5;
        if (sel) cv_dot(33, cy, 8.5, 0xFFD85840u);           /* the game's cursor dot */
        cv_text(it->label, 42, y, 0, row, k);
        const char* v = it->names[it->cur];
        const double vw = cv_text_w(v, k);
        cv_text(v, 470 - vw, y, 0, row, k);
        if (!it->live && it->cur != it->boot) cv_dot(478, cy, 6.5, 0xFFE8A030u);   /* pending: next start */
    }
    cv_text("LEFT RIGHT CHANGE   X EXIT", 24, 218, 0, 5, 0.66);
    const double nw = cv_text_w("APPLIES ON NEXT START", 0.66);
    cv_dot(488 - nw - 8, 218 + s_glyph_h * 0.33, 6.5, 0xFFE8A030u);
    cv_text("APPLIES ON NEXT START", 488 - nw, 218, 0, 5, 0.66);
}

static void mm_draw(int width, int height, void* ctx) {
    (void)ctx;
    if (!atomic_load(&s_visible)) return;
    const int upload = atomic_exchange(&s_dirty, 0);
    if (upload) mm_compose();
    if (s_canvas) gl_renderer_draw_host_movie(s_canvas, CV_W, CV_H, upload, width, height);
}

/* ------------------------------------------------------------------ emulation thread */
static void mm_read_glyphs(void) {
    const uint32_t t = psx_mod_read_word(MM_FONT_TABLES + 4u);
    if ((t & 0xFF000000u) != 0x80000000u) { s_have_glyphs = 0; return; }
    s_glyph_h = psx_mod_read_byte(t + 2u);
    for (int c = 0; c < 96; ++c)
        for (int k = 0; k < 3; ++k) s_glyph[c][k] = psx_mod_read_byte(t + 4u + (uint32_t)c * 3u + (uint32_t)k);
    s_have_glyphs = s_glyph_h > 0 && s_glyph_h < 40;
    mm_log("font 1 table %08X height %u ('A' u%u v%u w%u)", t, s_glyph_h, s_glyph['A' - 32][0],
           s_glyph['A' - 32][1], s_glyph['A' - 32][2]);
}

static void mm_open(void) {
    static int boot_known;
    if (s_open) return;
    mm_load_selection();
    if (!boot_known) { for (int i = 0; i < MM_N; ++i) s_items[i].boot = s_items[i].cur; boot_known = 1; }
    mm_read_glyphs();
    s_open = 1; s_sel = 0; s_swallow = 1;
    atomic_store(&s_dirty, 1); atomic_store(&s_visible, 1);
    mm_log("open");
}
static void mm_close(void) {
    s_open = 0; atomic_store(&s_visible, 0);
    mm_log("close");
}

/* pad transform: active-low buttons, SIO order (bit 4 Up, 5 Right, 6 Down, 7 Left, 13 Circle, 14 Cross) */
static int mm_pad(const PSXModPadFrame* in, PSXModPadOutput* out) {
    if (!s_open && !s_swallow) { s_prev_buttons = in->buttons; return 0; }
    const uint32_t down = ~in->buttons & 0xFFFFu, prev = ~s_prev_buttons & 0xFFFFu;
    const uint32_t press = down & ~prev;
    s_prev_buttons = in->buttons;
    if (s_open && press) {
        MmItem* it = &s_items[s_sel];
        if (press & 0x0010u) s_sel = (s_sel + MM_N - 1) % MM_N;
        else if (press & 0x0040u) s_sel = (s_sel + 1) % MM_N;
        else if (press & (0x0020u | 0x0080u | 0x2000u)) {
            const int step = (press & 0x0080u) ? it->nvals - 1 : 1;
            it->cur = (it->cur + step) % it->nvals;
            mm_apply(it);
        } else if (press & 0x4000u) mm_close();
        atomic_store(&s_dirty, 1);
    }
    if (!s_open && !down) s_swallow = 0;    /* released after closing: hand the pad back */
    out->buttons = 0xFFFFu;                 /* neutral pad for the game */
    out->type = PSX_MOD_PAD_DIGITAL;
    out->lx = out->ly = out->rx = out->ry = 0x80;
    return 1;
}

static void mm_circle_hook(struct CPUState* cpu, uint32_t address) {
    (void)address;
    if (!s_enabled || psx_mod_read_byte(MM_CURSOR) != 3) return;
    if (cpu->gpr[2] & 0x20u) mm_open();
    cpu->gpr[2] &= ~0x20u;                  /* the game must not start its sub-menu transition */
}

/* jal target replacing the VIBRATION text call: draw it, then "MODS" below */
static void mm_text_fn(struct CPUState* cpu, uint32_t address) {
    (void)address;
    const uint32_t ra = cpu->gpr[31], sp = cpu->gpr[29];
    const uint32_t a0 = cpu->gpr[4], a1 = cpu->gpr[5], a2 = cpu->gpr[6], a3 = cpu->gpr[7];
    const uint32_t v0 = psx_mod_call_guest(cpu, MM_FN_TEXT, ra, a0, a1, a2, a3);
    static int logged;
    if (logged < 3) {
        logged++;
        mm_log("text fn: ra %08X sp %08X a3 %u y %u col %u str %08X -> v0 %u", ra, sp, a3,
               psx_mod_read_word(sp + 0x10u), psx_mod_read_word(sp + 0x14u), psx_mod_read_word(sp + 0x20u), v0);
    }
    if (s_enabled) {
        /* the label string lives for the duration of the call in unused stack below the callee */
        const uint32_t str = (sp - 0x400u) & ~3u;
        const uint32_t keep0 = psx_mod_read_word(str), keep1 = psx_mod_read_word(str + 4u);
        psx_mod_write_word(str, 0x53444F4Du);          /* "MODS" */
        psx_mod_write_word(str + 4u, 0);
        uint32_t save[5];
        for (int i = 0; i < 5; ++i) save[i] = psx_mod_read_word(sp + 0x10u + 4u * (uint32_t)i);
        psx_mod_write_word(sp + 0x10u, MM_MODS_Y);
        psx_mod_write_word(sp + 0x14u, psx_mod_read_byte(MM_CURSOR) == 3 ? 6u : 5u);
        psx_mod_write_word(sp + 0x20u, str);
        const uint32_t v1 = psx_mod_call_guest(cpu, MM_FN_TEXT, ra, a0, a1, a2, a3);
        if (logged < 4) { logged++; mm_log("MODS call -> %u", v1); }
        for (int i = 0; i < 5; ++i) psx_mod_write_word(sp + 0x10u + 4u * (uint32_t)i, save[i]);
        psx_mod_write_word(str, keep0); psx_mod_write_word(str + 4u, keep1);
    }
    cpu->gpr[2] = v0;
}

static void mm_vblank(void) {
    if (!s_enabled) return;
    if (psx_mod_read_word(MM_GUARD_ADDR) != MM_GUARD_WORD) { if (s_open) mm_close(); return; }
    const uint32_t call = psx_mod_read_word(MM_CALL_SITE);
    if (call == MM_CALL_WORD) {
        psx_mod_write_code_word(MM_CALL_SITE, MM_CALL_PATCHED);
        psx_mod_write_byte(MM_LIMIT, 3);
        psx_mod_write_half(MM_CURSOR_POS3, 70);
        psx_mod_write_half(MM_CURSOR_POS3 + 4u, MM_MODS_Y - 2);
        mm_log("option menu patched");
    }
}

static void mm_activate(void) {
    s_enabled = 0; s_open = 0; atomic_store(&s_visible, 0);
    s_have_assets = psx_mod_current_resource_path("menu_assets", s_dir, sizeof s_dir) > 0;
    static const PSXModPadTransform tr = { sizeof(PSXModPadTransform), PSX_MOD_PAD_TYPE_BIT(PSX_MOD_PAD_DIGITAL) |
                                           PSX_MOD_PAD_TYPE_BIT(PSX_MOD_PAD_DUALSHOCK), PSX_MOD_PAD_DIGITAL, mm_pad };
    const int pad_ok = psx_mod_set_pad_transform(0, &tr);
    bag2jp_hud_add(mm_draw, NULL);
    s_enabled = 1;
    mm_log("activate: assets '%s' (%d), pad transform %d", s_dir, s_have_assets, pad_ok);
}

PSX_MOD_CONSTRUCTOR(bag2jp_register_mods_menu) {
    (void)psx_mod_register_activation_plugin("bag2jp.mods_menu", mm_activate);
    (void)psx_mod_register_vblank_plugin("bag2jp.mods_menu", mm_vblank);
    (void)psx_mod_register_guest_function_plugin("bag2jp.mods_menu", MM_GUEST_FN, mm_text_fn);
    (void)psx_mod_register_instruction_plugin("bag2jp.mods_menu", MM_CIRCLE_P1, MM_ANDI_20, mm_circle_hook);
    (void)psx_mod_register_instruction_plugin("bag2jp.mods_menu", MM_CIRCLE_P2, MM_ANDI_20, mm_circle_hook);
}
