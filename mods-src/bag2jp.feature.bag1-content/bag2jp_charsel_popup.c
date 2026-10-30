/* Character-select popup: game version (BAG1/BAG2, for characters imported from Bust A Groove 1)
 * and costume (A/B) per player (package bag2jp.feature.bag1-content, feature "select-popup").
 *
 * Character select = module system/007.dbi (base 0x8008F890). Per-player state 0x800971D4 + side*0x20:
 *   +0x19 side (pad index), +0x1A cursor index (= char id, Heat 0), +0x1C costume (0 A, 1 B),
 *   +0x1E state (1 choosing, 2 difficulty popup, 3 done), +0x1F difficulty.
 * In state 1 FUN_80091DB0 confirms on Circle (costume A; costume B when Select or Start is held) or
 * Triangle (costume B) if the index is selectable (mask 0x80096FA8). So BAG2 always had a hidden
 * costume choice; the popup makes it visible and adds the version.
 * Flow (pad transform, per port): Circle/Triangle on a selectable character opens the popup and is
 * kept from the game; while open the game gets a neutral pad; Circle confirms (version -> bag1
 * versions plugin, then the confirm is replayed to the game: Circle for costume A, Triangle for B),
 * Cross closes it. After closing, buttons stay hidden from the game until released.
 * The game's mirror rule (same character + costume -> the later pick switches costume) is skipped
 * when the two players picked different game versions (instruction hook at 0x80091B6C).
 * Online (bag2jp_netsync.c): each PC runs the popup for its own side on its own pad before the buttons
 * are sent; the version pick is sent as a message (the costume travels as the replayed button).
 * Drawn on the host HUD as an alpha overlay over the 4:3 picture, with the game's font 1 glyph table
 * over the HD font atlases (resource popup_assets: font_a05/a06.png). */
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

#define CS_PLAYER     0x800971D4u
#define CS_GUARD1     0x80091DB0u   /* FUN_80091DB0: addiu sp,sp,-0x38 */
#define CS_GUARD1_W   0x27BDFFC8u
#define CS_GUARD2     0x80093138u   /* FUN_80093138: addiu sp,sp,-0x50 */
#define CS_GUARD2_W   0x27BDFFB0u
#define CS_SELECTABLE 0x80096FA8u
#define CS_MODE       0x8005D2C4u
#define CS_HUMAN      0x8005E6C8u
#define CS_FONTS      0x8005E2B8u

/* SIO-order pad bits (active low in the frames) */
#define B_UP 0x0010u
#define B_RIGHT 0x0020u
#define B_DOWN 0x0040u
#define B_LEFT 0x0080u
#define B_TRI 0x1000u
#define B_CIRCLE 0x2000u
#define B_CROSS 0x4000u

int bag2jp_bag1_has_version(int chr);
int bag2jp_bag1_get_version(int chr, int side);
void bag2jp_bag1_set_version(int chr, int side, int v);
int bag2jp_mods_menu_pad_filter(const PSXModPadFrame* in, PSXModPadOutput* out);
int bag2jp_netsync_linked(void);
void bag2jp_netsync_send_pick(int side, int chr, int version);

enum { P_IDLE, P_OPEN, P_REPLAY, P_SWALLOW };
typedef struct {
    int phase, chr, side, row, version, costume, has_version, replay_t;
    uint32_t replay_btn, prev;
} CsPopup;
static CsPopup s_pop[2];
static int s_enabled;
static char s_dir[1024];
static atomic_int s_dirty, s_visible;

static FILE* s_logf;
static void cs_log(const char* fmt, ...) {
    if (!s_logf) {
        const char* b = SDL_GetBasePath(); char p[1024];
        snprintf(p, sizeof p, "%sbag2jp_charsel_popup.log", b ? b : "");
        s_logf = fopen(p, "w"); if (!s_logf) return;
    }
    va_list ap; va_start(ap, fmt); vfprintf(s_logf, fmt, ap); va_end(ap);
    fputc('\n', s_logf); fflush(s_logf);
}

/* ------------------------------------------------------------------ drawing (render thread) */
#define CV_W 1280
#define CV_H 960
#define CV_SX (CV_W / 512.0)
#define CV_SY (CV_H / 240.0)
typedef struct { int w, h; unsigned char* px; } CsImg;
static CsImg s_font[2];                     /* rows 5 (normal) and 6 (selected) of font atlas a */
static uint8_t s_glyph[96][3], s_glyph_h;
static int s_have_glyphs;
static uint32_t* s_canvas;
static CsPopup s_draw[2];                   /* snapshot for the render thread */

static int cs_load_png(const char* name, CsImg* im) {
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
static CsImg* cs_font(int selected) {
    CsImg* im = &s_font[selected ? 1 : 0];
    if (!im->px) cs_load_png(selected ? "font_a06.png" : "font_a05.png", im);
    return im->px ? im : NULL;
}
static void cv_blend(uint32_t* o, unsigned r, unsigned g, unsigned b, double a) {
    const double oa = ((*o >> 24) & 255) / 255.0, na = a + oa * (1 - a);
    if (na <= 0) return;
    const unsigned orr = (*o >> 16) & 255, og = (*o >> 8) & 255, ob = *o & 255;
    const unsigned rr = (unsigned)((r * a + orr * oa * (1 - a)) / na), gg = (unsigned)((g * a + og * oa * (1 - a)) / na),
                   bb = (unsigned)((b * a + ob * oa * (1 - a)) / na);
    *o = ((unsigned)(na * 255 + 0.5) << 24) | (rr << 16) | (gg << 8) | bb;
}
static void cv_round_rect(double px0, double py0, double px1, double py1, double r, uint32_t c) {
    const double x0 = px0 * CV_SX, y0 = py0 * CV_SY, x1 = px1 * CV_SX, y1 = py1 * CV_SY, R = r * CV_SX;
    const double ca = ((c >> 24) & 255) / 255.0;
    for (int y = (int)y0; y < (int)y1; ++y) for (int x = (int)x0; x < (int)x1; ++x) {
        if (x < 0 || y < 0 || x >= CV_W || y >= CV_H) continue;
        double dx = 0, dy = 0;
        if (x + 0.5 < x0 + R) dx = x0 + R - x - 0.5; else if (x + 0.5 > x1 - R) dx = x + 0.5 - (x1 - R);
        if (y + 0.5 < y0 + R) dy = y0 + R - y - 0.5; else if (y + 0.5 > y1 - R) dy = y + 0.5 - (y1 - R);
        double a = R + 0.5 - sqrt(dx * dx + dy * dy); if (a <= 0) continue; if (a > 1) a = 1;
        cv_blend(&s_canvas[y * CV_W + x], (c >> 16) & 255, (c >> 8) & 255, c & 255, a * ca);
    }
}
static void cv_dot(double px, double py, double r_canvas, uint32_t c) {
    const double cx = px * CV_SX, cy = py * CV_SY;
    for (int y = (int)(cy - r_canvas - 1); y <= (int)(cy + r_canvas + 1); ++y)
        for (int x = (int)(cx - r_canvas - 1); x <= (int)(cx + r_canvas + 1); ++x) {
            if (x < 0 || y < 0 || x >= CV_W || y >= CV_H) continue;
            const double d = sqrt((x + 0.5 - cx) * (x + 0.5 - cx) + (y + 0.5 - cy) * (y + 0.5 - cy));
            double a = r_canvas + 0.5 - d; if (a <= 0) continue; if (a > 1) a = 1;
            cv_blend(&s_canvas[y * CV_W + x], (c >> 16) & 255, (c >> 8) & 255, c & 255, a);
        }
}
static void cv_glyph(const CsImg* at, int u, int v, int w, int h, double px, double py, double k) {
    const double S = at->w / 256.0;
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
            cv_blend(&s_canvas[(Y + j) * CV_W + X + i], (unsigned)col[0], (unsigned)col[1], (unsigned)col[2], al);
        }
    }
}
static double cv_text_w(const char* s, double k) {
    double w = 0;
    for (; *s; ++s) {
        const int c = (unsigned char)*s - 0x20;
        w += (c <= 0 || c >= 96 || s_glyph[c][0] == 0xFF) ? 9 * k : s_glyph[c][2] * k;
    }
    return w;
}
static void cv_text(const char* s, double x, double y, int selected, double k) {
    const CsImg* at = cs_font(selected); if (!at || !s_have_glyphs) return;
    for (; *s; ++s) {
        const int c = (unsigned char)*s - 0x20;
        if (c <= 0 || c >= 96 || s_glyph[c][0] == 0xFF) { x += 9 * k; continue; }
        cv_glyph(at, s_glyph[c][0], s_glyph[c][1], s_glyph[c][2], s_glyph_h, x, y, k);
        x += s_glyph[c][2] * k;
    }
}

static void cv_tri(double px, double py, double size, int right, uint32_t c) {   /* small arrow */
    const double cx = px * CV_SX, cy = py * CV_SY, s = size * CV_SY;
    for (int y = (int)(cy - s - 1); y <= (int)(cy + s + 1); ++y)
        for (int x = (int)(cx - s - 1); x <= (int)(cx + s + 1); ++x) {
            if (x < 0 || y < 0 || x >= CV_W || y >= CV_H) continue;
            const double dx = right ? x + 0.5 - (cx - s * 0.5) : (cx + s * 0.5) - (x + 0.5);
            const double half = s - dx * 0.9;             /* tip at dx = s/0.9 */
            const double a = half + 0.5 - fabs(y + 0.5 - cy);
            if (dx < -0.5 || a <= 0) continue;
            cv_blend(&s_canvas[y * CV_W + x], (c >> 16) & 255, (c >> 8) & 255, c & 255, a > 1 ? 1 : a);
        }
}
static void cs_compose_one(const CsPopup* p) {
    const double w = 150, x0 = p->side ? 512 - 6 - w : 6, x1 = x0 + w, k = 0.6;
    const int rows = p->has_version ? 2 : 1;
    const double row_h = s_glyph_h * k + 8, top = 92, y0 = top - 26, y1 = top + rows * row_h + 20;
    cv_round_rect(x0 + 3, y0 + 3, x1 + 3, y1 + 3, 6, 0x90303848u);       /* shadow */
    cv_round_rect(x0, y0, x1, y1, 6, 0xFFF2F2F2u);
    cv_text(p->side ? "PLAYER 2" : "PLAYER 1", x0 + 9, y0 + 6, 1, 0.85);
    for (int r = 0; r < rows; ++r) {
        const int is_version = p->has_version && r == 0;
        const int sel = r == p->row;
        const double y = top + r * row_h, cy = y + s_glyph_h * k * 0.5;
        if (sel) cv_dot(x0 + 8, cy, 7.0, 0xFFD85840u);
        cv_text(is_version ? "GAME" : "COSTUME", x0 + 14, y, sel, k);
        const char* v = is_version ? (p->version ? "BAG 1" : "BAG 2") : (p->costume ? "B" : "A");
        const double vw = cv_text_w(v, k), vc = x1 - 24;          /* value centred between arrows */
        cv_text(v, vc - vw / 2, y, sel, k);
        if (sel) { cv_tri(vc - vw / 2 - 7, cy, 2.6, 0, 0xFFD85840u); cv_tri(vc + vw / 2 + 7, cy, 2.6, 1, 0xFFD85840u); }
    }
    cv_text("O OK  X BACK", x0 + 9, y1 - 14, 0, 0.58);
}
static void cs_compose(void) {
    if (!s_canvas) s_canvas = (uint32_t*)malloc((size_t)CV_W * CV_H * 4);
    if (!s_canvas) return;
    memset(s_canvas, 0, (size_t)CV_W * CV_H * 4);
    for (int i = 0; i < 2; ++i) if (s_draw[i].phase == P_OPEN) cs_compose_one(&s_draw[i]);
}
static void cs_draw(int width, int height, void* ctx) {
    (void)ctx;
    if (!atomic_load(&s_visible)) return;
    const int upload = atomic_exchange(&s_dirty, 0);
    if (upload) cs_compose();
    if (s_canvas) gl_renderer_draw_host_overlay(s_canvas, CV_W, CV_H, upload, width, height);
}

/* ------------------------------------------------------------------ game side (emulation thread) */
static int cs_screen_active(void) {
    return psx_mod_read_word(CS_GUARD1) == CS_GUARD1_W && psx_mod_read_word(CS_GUARD2) == CS_GUARD2_W;
}
static void cs_read_glyphs(void) {
    const uint32_t t = psx_mod_read_word(CS_FONTS + 4u);
    if ((t & 0xFF000000u) != 0x80000000u) { s_have_glyphs = 0; return; }
    s_glyph_h = psx_mod_read_byte(t + 2u);
    for (int c = 0; c < 96; ++c)
        for (int k = 0; k < 3; ++k) s_glyph[c][k] = psx_mod_read_byte(t + 4u + (uint32_t)c * 3u + (uint32_t)k);
    s_have_glyphs = s_glyph_h > 0 && s_glyph_h < 40;
}
static void cs_publish(void) {
    memcpy(s_draw, s_pop, sizeof s_draw);
    atomic_store(&s_visible, s_pop[0].phase == P_OPEN || s_pop[1].phase == P_OPEN);
    atomic_store(&s_dirty, 1);
}
static void cs_neutral(PSXModPadOutput* out, uint32_t buttons) {
    out->buttons = buttons; out->type = PSX_MOD_PAD_DIGITAL;
    out->lx = out->ly = out->rx = out->ry = 0x80;
}

/* side = the player block this pad drives (0/1); state is kept per side */
static int cs_run(int side, const PSXModPadFrame* in, PSXModPadOutput* out) {
    CsPopup* p = &s_pop[side];
    const uint32_t down = ~in->buttons & 0xFFFFu, press = down & ~p->prev;
    p->prev = down;
    if (p->phase == P_IDLE) {
        if (!(press & (B_CIRCLE | B_TRI)) || !cs_screen_active()) return 0;
        const uint32_t b = CS_PLAYER + 0x20u * (uint32_t)side;
        if ((int8_t)psx_mod_read_byte(b + 0x19u) != side || psx_mod_read_byte(b + 0x1Eu) != 1) return 0;
        const int idx = (int8_t)psx_mod_read_byte(b + 0x1Au);
        if (idx < 0 || idx > 31 || !(psx_mod_read_word(CS_SELECTABLE) & (1u << idx))) return 0;
        if (!s_have_glyphs) cs_read_glyphs();
        p->side = (int8_t)psx_mod_read_byte(b + 0x19u);
        p->chr = idx;
        p->has_version = bag2jp_bag1_has_version(idx);
        p->version = bag2jp_bag1_get_version(idx, p->side);
        /* Triangle (or Select/Start + Circle) is the game's own costume B shortcut: start there */
        p->costume = (press & B_TRI) || (down & 0x0009u) ? 1 : 0;
        p->row = 0; p->phase = P_OPEN;
        cs_log("open: side %d char %d (bag1 version %d, current %d)", p->side, idx, p->has_version, p->version);
        cs_publish();
        cs_neutral(out, 0xFFFFu); return 1;
    }
    if (p->phase == P_OPEN) {
        const int rows = p->has_version ? 2 : 1;
        if (!cs_screen_active()) { p->phase = P_SWALLOW; cs_publish(); }
        else if (press & (B_UP | B_DOWN)) p->row = (p->row + 1) % rows;
        else if (press & (B_LEFT | B_RIGHT)) {
            if (p->has_version && p->row == 0) p->version ^= 1; else p->costume ^= 1;
        } else if (press & B_CIRCLE) {
            if (p->has_version) {
                bag2jp_bag1_set_version(p->chr, p->side, p->version);
                bag2jp_netsync_send_pick(p->side, p->chr, p->version);   /* online: the other PC too */
            }
            p->replay_btn = p->costume ? B_TRI : B_CIRCLE;
            p->replay_t = 0; p->phase = P_REPLAY;
            cs_log("confirm: side %d char %d version %s costume %c", p->side, p->chr,
                   p->has_version ? (p->version ? "BAG1" : "BAG2") : "-", p->costume ? 'B' : 'A');
        } else if (press & B_CROSS) { p->phase = P_SWALLOW; cs_log("cancel: side %d", p->side); }
        if (press) cs_publish();
        cs_neutral(out, 0xFFFFu); return 1;
    }
    if (p->phase == P_REPLAY) {
        /* a few neutral polls, then the confirm button held for a few polls (the game samples
         * pressed = held & ~previous once per game frame) */
        const int t = p->replay_t++;
        cs_neutral(out, t >= 4 && t < 10 ? (0xFFFFu & ~p->replay_btn) : 0xFFFFu);
        if (p->replay_t >= 10) p->phase = P_SWALLOW;
        return 1;
    }
    /* P_SWALLOW: hand the pad back once everything is released */
    if (!down) { p->phase = P_IDLE; return 0; }
    cs_neutral(out, 0xFFFFu); return 1;
}

/* offline: port -> side (2P: same; 1P: port 1 drives the human's side) */
static int cs_filter(int port, const PSXModPadFrame* in, PSXModPadOutput* out) {
    if (!s_enabled || port < 0 || port > 1 || bag2jp_netsync_linked()) return 0;
    const int mode = (int16_t)psx_mod_read_half(CS_MODE);
    int side = port;
    if (mode != 2) { if (port != 0) return 0; side = (int8_t)psx_mod_read_byte(CS_HUMAN) & 1; }
    return cs_run(side, in, out);
}
int bag2jp_charsel_pad_filter(const PSXModPadFrame* in, PSXModPadOutput* out) {
    return cs_filter((int)in->player, in, out);
}
/* online (bag2jp_netsync.c): this PC's own pad drives its own side only, before the buttons are
 * sent; the other player's buttons arrive already resolved by their PC's popup */
int bag2jp_charsel_filter_side(int side, const PSXModPadFrame* in, PSXModPadOutput* out) {
    if (!s_enabled || side < 0 || side > 1) return 0;
    return cs_run(side, in, out);
}
static int cs_port0(const PSXModPadFrame* in, PSXModPadOutput* out) {
    if (bag2jp_mods_menu_pad_filter(in, out)) return 1;      /* MODS screen first */
    return cs_filter(0, in, out);
}
static int cs_port1(const PSXModPadFrame* in, PSXModPadOutput* out) { return cs_filter(1, in, out); }

static const PSXModPadTransform s_tr0 = { sizeof(PSXModPadTransform), PSX_MOD_PAD_TYPE_BIT(PSX_MOD_PAD_DIGITAL) |
                                          PSX_MOD_PAD_TYPE_BIT(PSX_MOD_PAD_DUALSHOCK), PSX_MOD_PAD_DIGITAL, cs_port0 };
static const PSXModPadTransform s_tr1 = { sizeof(PSXModPadTransform), PSX_MOD_PAD_TYPE_BIT(PSX_MOD_PAD_DIGITAL) |
                                          PSX_MOD_PAD_TYPE_BIT(PSX_MOD_PAD_DUALSHOCK), PSX_MOD_PAD_DIGITAL, cs_port1 };
/* netsync puts these back when an online link ends */
void bag2jp_charsel_reattach(void) {
    if (!s_enabled) return;
    (void)psx_mod_set_pad_transform(0, &s_tr0);
    (void)psx_mod_set_pad_transform(1, &s_tr1);
}
int bag2jp_charsel_enabled(void) { return s_enabled; }

/* Mirror rule (FUN_80091AE8): when both players pick the same character and costume, the later one
 * gets the other costume (`sb v0,0x1c(a2)` at 0x80091B6C, v0 = costume ^ 1). Not needed when they
 * picked different game versions of that character: keep the costume. */
#define CS_MIRROR_SB   0x80091B6Cu
#define CS_MIRROR_W    0xA0C2001Cu
static void cs_mirror_hook(struct CPUState* cpu, uint32_t address) {
    (void)address;
    if (!s_enabled) return;
    const uint32_t b = cpu->gpr[6];
    const int side = (int8_t)psx_mod_read_byte(b + 0x19u) & 1, idx = (int8_t)psx_mod_read_byte(b + 0x1Au);
    if (!bag2jp_bag1_has_version(idx) || bag2jp_bag1_get_version(idx, side) == bag2jp_bag1_get_version(idx, side ^ 1)) return;
    cpu->gpr[2] = cpu->gpr[7];                     /* store the costume it already has */
    cs_log("mirror: player %d keeps costume %c (other game version)", side + 1, cpu->gpr[7] ? 'B' : 'A');
}

static void cs_vblank(void) {
    /* close any popup left open when the screen goes away */
    if (!s_enabled || (s_pop[0].phase != P_OPEN && s_pop[1].phase != P_OPEN) || cs_screen_active()) return;
    for (int i = 0; i < 2; ++i) if (s_pop[i].phase == P_OPEN) s_pop[i].phase = P_SWALLOW;
    cs_publish();
}
static void cs_activate(void) {
    memset(s_pop, 0, sizeof s_pop);
    if (psx_mod_current_resource_path("popup_assets", s_dir, sizeof s_dir) <= 0) s_dir[0] = 0;
    s_enabled = 1;
    const int a = psx_mod_set_pad_transform(0, &s_tr0), b = psx_mod_set_pad_transform(1, &s_tr1);
    bag2jp_hud_add(cs_draw, NULL);
    cs_publish();
    cs_log("activate: assets '%s', pad transforms %d %d", s_dir, a, b);
}
static void cs_reset(void) { s_enabled = 0; atomic_store(&s_visible, 0); }

PSX_MOD_CONSTRUCTOR(bag2jp_register_charsel_popup) {
    (void)psx_mod_register_activation_plugin("bag2jp.charsel_popup", cs_activate);
    (void)psx_mod_register_session_reset_plugin("bag2jp.charsel_popup", cs_reset);
    (void)psx_mod_register_vblank_plugin("bag2jp.charsel_popup", cs_vblank);
    (void)psx_mod_register_instruction_plugin("bag2jp.charsel_popup", CS_MIRROR_SB, CS_MIRROR_W, cs_mirror_hook);
}
