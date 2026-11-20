/* Gas-O Authentic BAG1 Attack Visual Effect & Rival Reaction:
 * - Direct implementation of authentic 3D Tank Mesh from BAG1 PLAYER2/P_GAS_A2.DFS Member 2
 * - Authentic 41-vertex geometry, 8-quad glass chamber, 24-quad metal body, 8-triangle metal cap
 * - Factory BAG1 PS1 colors: Metal RGB(89,89,102), Chemical Glass RGB(125,255,106)
 * - Emits volumetric native cryo-smoke puffs using authentic BAG1 UV table (0x801DCE4C) & TIMs
 * - Falls from above with accelerated gravity trajectory onto rival
 * - Drops on each Gas-O hit and lasts while the rival is trapped (BAG1 timing)
 * - Diagnostic candidate: leaves the rival's native reaction untouched; CAUGHT is pending
 * - Uses shared matrix math and OT helpers from bag2jp_strike_shot.h
 */
#ifndef BAG2JP_GASO_TANK_H
#define BAG2JP_GASO_TANK_H

#include <stdatomic.h>
#include <stdint.h>
#include <string.h>
#include "bag2jp_gaso_bubble.h"
#include "bag2jp_gaso_smoke_tim.h"

#define GASO_CHAR_ID        9u
#define GASO_ATTACK_ANIM    74u
#define GASO_ATTACK_START   20u
#define GASO_ATTACK_END     65u
/* Last accessed dancer field is the 32-bit animation frame at +0x1554. */
#define GASO_DANCER_MAX_BASE (0x80800000u - 0x1558u)

/* Lifetime follows BAG1 (reference gaso-vs-heat-autoplay, 2026-11-12, wall-clock
 * stamps, about +-2 frames): the tank drops at the hit, stays while the rival
 * is trapped, is cut without a fade ~0.15 s after the release, and Gas-O's next
 * attack removes it ~0.61 s (1.43 beats) into the attack until that hit drops
 * a new one. Measured: frame 38 at +0x1554 came 62 vblanks after the attack
 * entry (take gaso-secondary-suppress-heat-bag1d, 2026-11-13 UTC, 0.428 s/beat)
 * and the hit about 4 beats in, near GASO_ATTACK_END. Inferred from that one
 * tempo: ~16 frames per beat, so 1.43 beats x 16 = 22.9 -> 23. Assumes BAG1's
 * cut follows the beat, not wall time. */
#define GASO_TANK_FALL_DUR    6u    /* frames of descent; BAG1 lands in ~0.1 s */
#define GASO_TANK_RELEASE_DUR 9u    /* frames kept after the rival leaves the hit slot */
#define GASO_TANK_CLEAR_FRAME 23u   /* Gas-O attack frame (16/beat) that clears it */
#define GASO_TANK_MAX_DUR     1800u /* bound if the rival never leaves the hit slot */
/* BAG1 tank sounds (JP DBI 801d6480, 801d666c and 801d7218), in Gas-O's voice
 * bank as rebased by build_gaso_assets.py (0x1800 -> 0x6900). Lock: state -1
 * becomes 0 on the first rhythm pulse after the drop and plays 0x1806 on the
 * next update. Bubbles: once the landed counter exceeds 32, 0x180a plays when
 * disarmed; it re-arms after more than 32 frames or on a 1-in-32 random draw.
 * BAG2's beat counter stands in for BAG1's pulse flag 0x8006ec30&2. */
#define GASO_TANK_CUE_LOCK     0x6906u
#define GASO_TANK_CUE_BUBBLE   0x690Au
#define GASO_TANK_CUE_LOCK_BIT   1u
#define GASO_TANK_CUE_BUBBLE_BIT 2u
#define GASO_TANK_BUBBLE_DELAY 0x20u
#define GASO_TANK_BEAT_ADDR    0x8005E2D0u
/* Rival animation while trapped: native hit slot 89, or slot1 when the
 * CAUGHT clip is published there (bag2jp_gaso_caught.c). */
#define GASO_TRAP_SLOT        89u
#define GASO_TRAP_BORROWED    1u

uint32_t bag2jp_gaso_caught_hits(uint32_t side);
uint32_t bag2jp_gaso_caught_epoch(void);
uint32_t bag2jp_gaso_caught_epoch_hits(uint32_t side);
int bag2jp_gaso_caught_owns_slot1(uint32_t side, uint32_t actor);

#define GASO_NATIVE_TANK_NUM_VERTS 41

/* Authentic 3D vertices from BAG1 PLAYER2/P_GAS_A2.DFS Member 2 */
static const int16_t s_gaso_native_verts[41][3] = {
    {  1080,    0,     0 }, /*  0 */
    {  1080,  371,     0 }, /*  1 */
    {  1080, 3758,     0 }, /*  2 */
    {  1080, 4149,     0 }, /*  3 */
    {   764,    0,  -764 }, /*  4 */
    {   764,  371,  -764 }, /*  5 */
    {   764, 3758,  -764 }, /*  6 */
    {   764, 4149,  -764 }, /*  7 */
    {     0,    0, -1080 }, /*  8 */
    {     0,  371, -1080 }, /*  9 */
    {     0, 3758, -1080 }, /* 10 */
    {     0, 4149, -1080 }, /* 11 */
    {  -764,    0,  -764 }, /* 12 */
    {  -764,  371,  -764 }, /* 13 */
    {  -764, 3758,  -764 }, /* 14 */
    {  -764, 4149,  -764 }, /* 15 */
    { -1080,    0,     0 }, /* 16 */
    { -1080,  371,     0 }, /* 17 */
    { -1080, 3758,     0 }, /* 18 */
    { -1080, 4149,     0 }, /* 19 */
    {  -764,    0,   764 }, /* 20 */
    {  -764,  371,   764 }, /* 21 */
    {  -764, 3758,   764 }, /* 22 */
    {  -764, 4149,   764 }, /* 23 */
    {     0,  371,  1080 }, /* 24 */
    {     0, 3758,  1080 }, /* 25 */
    {     0, 4149,  1080 }, /* 26 */
    {   764,    0,   764 }, /* 27 */
    {   764,  371,   764 }, /* 28 */
    {   764, 3758,   764 }, /* 29 */
    {   764, 4149,   764 }, /* 30 */
    {   549, 4354,   549 }, /* 31 */
    {   777, 4354,     0 }, /* 32 */
    {   549, 4354,  -549 }, /* 33 */
    {     0, 4354,  -777 }, /* 34 */
    {  -549, 4354,  -549 }, /* 35 */
    {  -777, 4354,     0 }, /* 36 */
    {  -549, 4354,   549 }, /* 37 */
    {     0,    0,  1080 }, /* 38 */
    {     0, 4354,   777 }, /* 39 */
    {     0, 4480,     0 }  /* 40: Cap Apex */
};

/* Authentic Triangles for Top Metal Bevel/Cap (8 triangles) */
static const uint8_t s_gaso_cap_tris[8][3] = {
    { 40, 34, 33 },
    { 40, 39, 37 },
    { 35, 34, 40 },
    { 40, 37, 36 },
    { 40, 36, 35 },
    { 31, 39, 40 },
    { 40, 33, 32 },
    { 32, 31, 40 }
};

/* Authentic Quads for Metal Base & Reinforcement Rings (24 quads) */
static const uint8_t s_gaso_body_quads[24][4] = {
    {  5,  4,  0,  1 },
    {  7,  6,  2,  3 },
    {  9,  8,  4,  5 },
    { 11, 10,  6,  7 },
    { 13, 12,  8,  9 },
    { 15, 14, 10, 11 },
    { 17, 16, 12, 13 },
    { 19, 18, 14, 15 },
    { 21, 20, 16, 17 },
    { 23, 22, 18, 19 },
    { 37, 39, 26, 23 },
    { 24, 38, 20, 21 },
    { 26, 25, 22, 23 },
    { 31, 32,  3, 30 },
    { 31, 30, 26, 39 },
    { 28, 27, 38, 24 },
    { 30, 29, 25, 26 },
    { 33,  7,  3, 32 },
    {  1,  0, 27, 28 },
    {  3,  2, 29, 30 },
    { 37, 23, 19, 36 },
    { 35, 36, 19, 15 },
    { 35, 15, 11, 34 },
    { 33, 34, 11,  7 }
};

/* Authentic Quads for Translucent Cryo-Glass Cylinder (8 quads) */
static const uint8_t s_gaso_glass_quads[8][4] = {
    {  6,  5,  1,  2 },
    { 10,  9,  5,  6 },
    { 14, 13,  9, 10 },
    { 18, 17, 13, 14 },
    { 22, 21, 17, 18 },
    { 25, 24, 21, 22 },
    { 29, 28, 24, 25 },
    {  2,  1, 28, 29 }
};

typedef struct {
    uint8_t active;
    uint8_t side;
    uint8_t clear_on_attack; /* observed non-attack -> attack after this hit */
    uint32_t start_frame;
    uint32_t opp_dancer;
    int32_t target_x;
    int32_t target_y;
    int32_t target_z;
    uint16_t elapsed;
    uint16_t released;   /* frames since the rival left the hit slot */
    uint8_t lock_state;  /* 1 waits for a beat, 2 plays the lock cue, 0 done */
    uint8_t bubble_armed;
    uint16_t landed;     /* frames since the tank landed */
    uint16_t bubble_acc;
    uint16_t last_beat;
} GasoTankState;

static GasoTankState s_gaso_tank[2];
/* Last bag2jp_gaso_caught_hits() value per recipient side; adopted without a
 * spawn after a reset so an old hit never drops a tank. */
static uint32_t s_gaso_hits_seen[2];
static uint8_t s_gaso_hits_synced;
static uint8_t s_gaso_attacking[2];
static uint32_t s_gaso_epoch_seen;
static uint32_t s_gaso_combat_frame;
static uint8_t s_gaso_smoke_uploaded;
/* Cue requests from the VBlank tick; a function-entry hook plays them. */
static _Atomic uint32_t s_gaso_tank_cues;
/* PsyQ rand() recurrence with its own seed, not the game's random stream. */
static uint32_t s_gaso_tank_seed = 1u;

/* Unit circle lookup for 16-segment dispersion */
static const int16_t s_circle_cos[16] = {
    4096, 3784, 2896, 1567, 0, -1567, -2896, -3784,
    -4096, -3784, -2896, -1567, 0, 1567, 2896, 3784
};
static const int16_t s_circle_sin[16] = {
    0, 1567, 2896, 3784, 4096, 3784, 2896, 1567,
    0, -1567, -2896, -3784, -4096, -3784, -2896, -1567
};

static void bag2jp_gaso_tank_reset(void) {
    memset(s_gaso_tank, 0, sizeof(s_gaso_tank));
    memset(s_gaso_attacking, 0, sizeof(s_gaso_attacking));
    atomic_store(&s_gaso_tank_cues, 0u);
    for (uint32_t side = 0; side < 2; ++side)
        s_gaso_hits_seen[side] = bag2jp_gaso_caught_hits(side);
    s_gaso_hits_synced = 1;
    s_gaso_epoch_seen = bag2jp_gaso_caught_epoch();
    s_gaso_combat_frame = 0;
    s_gaso_smoke_uploaded = 0;
}

/* Native BAG1 Gas-O smoke particle attributes from DBI table at 0x801DCE4C */
static const struct {
    uint8_t w;
    uint8_t h;
    int16_t u;
    int16_t v;
} s_gaso_smoke_tbl[16] = {
    { 120, 176,   8, 992 }, /*  0 */
    { 152, 189,   0,   2 }, /*  1 */
    {  15,  11,  16,   2 }, /*  2 */
    {  15,  11,  31,   2 }, /*  3 */
    {  16,  12,  47,   1 }, /*  4 */
    {  17,  14,  65,   0 }, /*  5 */
    {  21,  16,  90,   2 }, /*  6 */
    {  27,  19, 119,   1 }, /*  7 */
    {  32,  24, 152,   2 }, /*  8 */
    {  40,  28, 192,   2 }, /*  9 */
    {  40,  29,   0,  18 }, /* 10 */
    {  40,  29,  40,  18 }, /* 11 */
    {  40,  29,  80,  27 }, /* 12 */
    {  40,  28, 120,  34 }, /* 13 */
    {  40,  29, 160,  35 }, /* 14 */
    {  40,  29, 200,  34 }  /* 15 */
};

/* Emit POLY_F3 flat-shaded triangle (4 words = 16 bytes) */
static inline void gaso_emit_poly_f3(uint32_t* heap_ptr, uint32_t ot_addr,
                                     int16_t x0, int16_t y0,
                                     int16_t x1, int16_t y1,
                                     int16_t x2, int16_t y2,
                                     uint32_t color) {
    uint32_t heap = *heap_ptr;
    uint32_t ot_head = psx_mod_read_word(ot_addr);

    /* 4 words = 16 bytes = POLY_F3 */
    psx_mod_write_word(heap + 0x00u, (4u << 24) | (ot_head & 0x00FFFFFFu));
    psx_mod_write_word(heap + 0x04u, 0x20000000u | (color & 0x00FFFFFFu));
    psx_mod_write_word(heap + 0x08u, ((uint32_t)(uint16_t)y0 << 16) | (uint32_t)(uint16_t)x0);
    psx_mod_write_word(heap + 0x0Cu, ((uint32_t)(uint16_t)y1 << 16) | (uint32_t)(uint16_t)x1);
    psx_mod_write_word(heap + 0x10u, ((uint32_t)(uint16_t)y2 << 16) | (uint32_t)(uint16_t)x2);

    psx_mod_write_word(ot_addr, (ot_head & 0xFF000000u) | (heap & 0x00FFFFFFu));
    *heap_ptr = heap + 20u;
}

/* Emit textured semi-transparent POLY_FT4 (10 words = 40 bytes) for native smoke clouds */
static inline void gaso_emit_poly_ft4(uint32_t* heap_ptr, uint32_t ot_addr,
                                      int16_t x0, int16_t y0,
                                      int16_t x1, int16_t y1,
                                      int16_t x2, int16_t y2,
                                      int16_t x3, int16_t y3,
                                      uint8_t u0, uint8_t v0,
                                      uint8_t u1, uint8_t v1,
                                      uint8_t u2, uint8_t v2,
                                      uint8_t u3, uint8_t v3,
                                      uint16_t clut, uint16_t tpage,
                                      uint32_t color) {
    uint32_t heap = *heap_ptr;
    uint32_t ot_head = psx_mod_read_word(ot_addr);

    psx_mod_write_word(heap + 0x00u, (9u << 24) | (ot_head & 0x00FFFFFFu));
    psx_mod_write_word(heap + 0x04u, 0x2E000000u | (color & 0x00FFFFFFu)); 
    psx_mod_write_word(heap + 0x08u, ((uint32_t)(uint16_t)y0 << 16) | (uint32_t)(uint16_t)x0);
    psx_mod_write_word(heap + 0x0Cu, ((uint32_t)clut << 16) | ((uint32_t)v0 << 8) | (uint32_t)u0);
    psx_mod_write_word(heap + 0x10u, ((uint32_t)(uint16_t)y1 << 16) | (uint32_t)(uint16_t)x1);
    psx_mod_write_word(heap + 0x14u, ((uint32_t)tpage << 16) | ((uint32_t)v1 << 8) | (uint32_t)u1);
    psx_mod_write_word(heap + 0x18u, ((uint32_t)(uint16_t)y2 << 16) | (uint32_t)(uint16_t)x2);
    psx_mod_write_word(heap + 0x1Cu, ((uint32_t)clut << 16) | ((uint32_t)v2 << 8) | (uint32_t)u2);
    psx_mod_write_word(heap + 0x20u, ((uint32_t)(uint16_t)y3 << 16) | (uint32_t)(uint16_t)x3);
    psx_mod_write_word(heap + 0x24u, ((uint32_t)v3 << 8) | (uint32_t)u3);

    psx_mod_write_word(ot_addr, (ot_head & 0xFF000000u) | (heap & 0x00FFFFFFu));
    *heap_ptr = heap + 40u;
}

/* Gouraud POLY_G3 (7 words): opaque 0x30 or semi-transparent 0x32. */
static inline void gaso_emit_poly_g3(uint32_t* heap_ptr, uint32_t ot_addr, int semi,
                                     const StrikeScreenPt* p0, uint32_t c0,
                                     const StrikeScreenPt* p1, uint32_t c1,
                                     const StrikeScreenPt* p2, uint32_t c2) {
    uint32_t heap = *heap_ptr;
    uint32_t ot_head = psx_mod_read_word(ot_addr);

    psx_mod_write_word(heap + 0x00u, (6u << 24) | (ot_head & 0x00FFFFFFu));
    psx_mod_write_word(heap + 0x04u, (semi ? 0x32000000u : 0x30000000u) | (c0 & 0x00FFFFFFu));
    psx_mod_write_word(heap + 0x08u, ((uint32_t)(uint16_t)p0->y << 16) | (uint16_t)p0->x);
    psx_mod_write_word(heap + 0x0Cu, c1 & 0x00FFFFFFu);
    psx_mod_write_word(heap + 0x10u, ((uint32_t)(uint16_t)p1->y << 16) | (uint16_t)p1->x);
    psx_mod_write_word(heap + 0x14u, c2 & 0x00FFFFFFu);
    psx_mod_write_word(heap + 0x18u, ((uint32_t)(uint16_t)p2->y << 16) | (uint16_t)p2->x);

    psx_mod_write_word(ot_addr, (ot_head & 0xFF000000u) | (heap & 0x00FFFFFFu));
    *heap_ptr = heap + 28u;
}

/* Gouraud POLY_G4 for one mesh quad in cycle order a,b,c,d (PSX order a,d,b,c):
 * opaque 0x38 or semi-transparent 0x3A; strike_emit_poly_g4 is always 0x3A. */
static inline void gaso_emit_quad_g4(uint32_t* heap_ptr, uint32_t ot_addr, int semi,
                                     const StrikeScreenPt* pts, const uint8_t* q,
                                     const uint32_t* col) {
    static const uint8_t order[4] = { 0, 3, 1, 2 };
    uint32_t heap = *heap_ptr;
    uint32_t ot_head = psx_mod_read_word(ot_addr);

    psx_mod_write_word(heap + 0x00u, (8u << 24) | (ot_head & 0x00FFFFFFu));
    for (uint32_t k = 0; k < 4u; ++k) {
        const StrikeScreenPt* p = &pts[q[order[k]]];
        uint32_t code = k == 0u ? (semi ? 0x3A000000u : 0x38000000u) : 0u;
        psx_mod_write_word(heap + 0x04u + k * 8u, code | (col[q[order[k]]] & 0x00FFFFFFu));
        psx_mod_write_word(heap + 0x08u + k * 8u, ((uint32_t)(uint16_t)p->y << 16) | (uint16_t)p->x);
    }

    psx_mod_write_word(ot_addr, (ot_head & 0xFF000000u) | (heap & 0x00FFFFFFu));
    *heap_ptr = heap + 36u;
}

/* Twice the signed screen area of a mesh face in its stored cycle order. All
 * 40 faces wind the same way around the outward normal, so one sign marks the
 * camera-facing side; BAG1 culls the rest with NCLIP in every primitive emitter. */
static inline int64_t gaso_face_area(const StrikeScreenPt* pts, const uint8_t* idx, int n) {
    int64_t a = 0;
    for (int k = 0; k < n; ++k) {
        const StrikeScreenPt* p = &pts[idx[k]];
        const StrikeScreenPt* q = &pts[idx[(k + 1) % n]];
        a += (int64_t)p->x * q->y - (int64_t)q->x * p->y;
    }
    return a;
}

static inline int gaso_faces_camera(const StrikeScreenPt* pts, const int* valid,
                                    const uint8_t* idx, int n, int64_t front) {
    for (int k = 0; k < n; ++k)
        if (!valid[idx[k]]) return 0;
    int64_t a = gaso_face_area(pts, idx, n);
    return a != 0 && (a > 0) == (front > 0);
}

/* Round blob as an 8-triangle semi-transparent Gouraud fan; returns packets. */
static inline int gaso_emit_fan(uint32_t* heap_ptr, uint32_t ot_addr, int16_t cx, int16_t cy,
                                int32_t rx, int32_t ry, uint32_t centre, uint32_t rim) {
    StrikeScreenPt c = { cx, cy, 0 };
    for (uint32_t k = 0; k < 8u; ++k) {
        uint32_t a = k * 2u, b = (k * 2u + 2u) % 16u;
        StrikeScreenPt p0 = { (int16_t)(cx + ((rx * s_circle_cos[a]) >> 12)),
                              (int16_t)(cy + ((ry * s_circle_sin[a]) >> 12)), 0 };
        StrikeScreenPt p1 = { (int16_t)(cx + ((rx * s_circle_cos[b]) >> 12)),
                              (int16_t)(cy + ((ry * s_circle_sin[b]) >> 12)), 0 };
        gaso_emit_poly_g3(heap_ptr, ot_addr, 1, &c, centre, &p0, rim, &p1, rim);
    }
    return 8;
}

/* Bubble outline: 16 semi-transparent G4 segments from a black (clear, under
 * additive blending) inner edge at 80% of the radius to the rim colour. */
static inline int gaso_emit_ring(uint32_t* heap_ptr, uint32_t ot_addr, int16_t cx, int16_t cy,
                                 int32_t rx, int32_t ry, uint32_t rim) {
    for (uint32_t k = 0; k < 16u; ++k) {
        uint32_t a = k, b = (k + 1u) % 16u;
        int32_t oxa = (rx * s_circle_cos[a]) >> 12, oya = (ry * s_circle_sin[a]) >> 12;
        int32_t oxb = (rx * s_circle_cos[b]) >> 12, oyb = (ry * s_circle_sin[b]) >> 12;
        strike_emit_poly_g4(heap_ptr, ot_addr,
                            (int16_t)(cx + oxa * 80 / 100), (int16_t)(cy + oya * 80 / 100), 0u,
                            (int16_t)(cx + oxa), (int16_t)(cy + oya), rim,
                            (int16_t)(cx + oxb * 80 / 100), (int16_t)(cy + oyb * 80 / 100), 0u,
                            (int16_t)(cx + oxb), (int16_t)(cy + oyb), rim);
    }
    return 16;
}

/* Scale each channel by k16/16, saturating. */
static inline uint32_t gaso_shade(uint32_t rgb, int32_t k16) {
    uint32_t out = 0;
    for (uint32_t s = 0; s < 24u; s += 8u) {
        int32_t c = ((int32_t)((rgb >> s) & 0xFFu) * k16) >> 4;
        out |= (uint32_t)(c > 255 ? 255 : c) << s;
    }
    return out;
}

/* Draw modes with dither: ABR0 average restores the native default; the
 * liquid and highlights add. BAG1's cylinder averages (E1000600), but in BAG2's
 * darker scene that halved the rival's contrast; the owner asked for BAG1's
 * see-through look (2026-11-13), so the liquid adds a faint tint instead. */
#define GASO_MODE_AVERAGE  0x0600u
#define GASO_MODE_ADDITIVE 0x0620u
#define GASO_GLASS_RGB     0x051206u /* 0xBBGGRR; x1.125..x2.25 keeps the averaged layer's mean tint */
#define GASO_METAL_RGB     0x665959u
#define GASO_BUBBLE_PERIOD 64u       /* frames each bubble lives */
/* Native mesh -> BAG2 units, in percent. Matched to BAG1 on screen relative to
 * the rival (gaso-vs-heat-autoplay 31.0 s vs gaso-liquid6-heat-bag1 3.9 s):
 * tank height 1.42x and width 0.71x Heat's height, a margin above the head.
 * Near-uniform, like BAG1 (on-screen width/height 0.50; mesh 0.48). Not the
 * native 12*dim+230 / per-character Y table formula, whose BAG2 units are
 * unresolved. */
#define GASO_TANK_XZ_PCT   24        /* radius 1080 -> 259 units */
#define GASO_TANK_Y_PCT    26        /* height 4480 -> 1164 units */
#define GASO_BUBBLE_RADIUS 68        /* world units, ~26% of the tank diameter */
#define GASO_BUBBLE_RIM    0x3C3430u /* additive faint grey-blue rim; clear centre */
#define GASO_GLINT_RGB     0xC0C0B0u /* additive specular dot */

static uint32_t gaso_tank_rand(void) {
    s_gaso_tank_seed = s_gaso_tank_seed * 1103515245u + 12345u;
    return (s_gaso_tank_seed >> 16) & 0x7FFFu;
}

/* Cues requested since the last call; the caller plays them from guest code. */
static uint32_t bag2jp_gaso_tank_take_cues(void) {
    return atomic_exchange(&s_gaso_tank_cues, 0u);
}

/* One BAG1 tank-controller update of the lock and bubble cues. */
static void gaso_tank_sound(GasoTankState *tank) {
    const uint16_t beat = psx_mod_read_half(GASO_TANK_BEAT_ADDR);
    if (tank->lock_state == 2u) {
        atomic_fetch_or(&s_gaso_tank_cues, GASO_TANK_CUE_LOCK_BIT);
        tank->lock_state = 0;
    } else if (tank->lock_state == 1u && beat != tank->last_beat) {
        tank->lock_state = 2;
    }
    tank->last_beat = beat;
    if (tank->elapsed < GASO_TANK_FALL_DUR) return;
    if (++tank->landed <= GASO_TANK_BUBBLE_DELAY) return;
    ++tank->bubble_acc;
    if (!tank->bubble_armed) {
        atomic_fetch_or(&s_gaso_tank_cues, GASO_TANK_CUE_BUBBLE_BIT);
        tank->bubble_armed = 1;
    }
    if (tank->bubble_acc > GASO_TANK_BUBBLE_DELAY || (gaso_tank_rand() & 0x1Fu) == 0u) {
        tank->bubble_armed = 0;
        tank->bubble_acc = 0;
    }
}

/* State advances even when rendering resources are unavailable. */
static void gaso_tank_maintain(uint32_t side) {
    GasoTankState *tank = &s_gaso_tank[side];
    if (!tank->active) return;
    if (tank->elapsed >= GASO_TANK_MAX_DUR) {
        tank->active = 0;
        return;
    }
    ++tank->elapsed;
    uint32_t rival = psx_mod_read_word(B2_DANCER_BASE + (side ^ 1u) * 8u);
    if (rival != tank->opp_dancer || rival < 0x80010000u || rival > GASO_DANCER_MAX_BASE) {
        tank->active = 0;
        return;
    }
    uint32_t anim = psx_mod_read_word(rival + 0x154Cu);
    if (anim == GASO_TRAP_SLOT ||
        (anim == GASO_TRAP_BORROWED && bag2jp_gaso_caught_owns_slot1(side ^ 1u, rival))) {
        tank->released = 0;
    } else if (++tank->released > GASO_TANK_RELEASE_DUR) {
        tank->active = 0;
        return;
    }
    gaso_tank_sound(tank);
}

static int bag2jp_gaso_tank_tick(uint32_t frame) {
    if (s_gaso_epoch_seen != bag2jp_gaso_caught_epoch()) {
        bag2jp_gaso_tank_reset();
        for (uint32_t side = 0; side < 2; ++side)
            s_gaso_hits_seen[side] = bag2jp_gaso_caught_epoch_hits(side);
    }
    /* 1. Verify combat scene root (root 19) */
    if (psx_mod_read_word(B2_ROOT_ADDR) != 19u) {
        bag2jp_gaso_tank_reset();
        return 0;
    }
    ++s_gaso_combat_frame;

    /* 2. Drop a tank on each Gas-O hit; Gas-O's next attack removes it. The
     * hit count only grows for a direct hit by a BAG1 Gas-O (capture hook). */
    for (uint32_t side = 0; side < 2; ++side) {
        uint32_t hits = bag2jp_gaso_caught_hits(side ^ 1u);
        uint32_t new_hit = s_gaso_hits_synced && hits != s_gaso_hits_seen[side ^ 1u];
        s_gaso_hits_seen[side ^ 1u] = hits;

        uint32_t chr = psx_mod_read_word(side == 0 ? B2_CHAR_P1_ADDR : B2_CHAR_P2_ADDR);
        if (chr != GASO_CHAR_ID || !bag2jp_bag1_get_version((int)GASO_CHAR_ID, (int)side)) {
            s_gaso_tank[side].active = 0;
            s_gaso_attacking[side] = 0;
            continue;
        }

        uint32_t dancer = psx_mod_read_word(B2_DANCER_BASE + side * 8u);
        uint32_t opp_dancer = psx_mod_read_word(B2_DANCER_BASE + (side ^ 1u) * 8u);
        if (dancer < 0x80010000u || dancer > GASO_DANCER_MAX_BASE ||
            opp_dancer < 0x80010000u || opp_dancer > GASO_DANCER_MAX_BASE) {
            s_gaso_tank[side].active = 0;
            s_gaso_attacking[side] = 0;
            continue;
        }

        GasoTankState* tank = &s_gaso_tank[side];
        uint32_t anim = psx_mod_read_word(dancer + 0x154Cu);
        uint32_t anim_frame = psx_mod_read_word(dancer + 0x1554u);
        uint32_t attacking = anim == GASO_ATTACK_ANIM || anim == 88u;
        uint32_t attack_entry = attacking && !s_gaso_attacking[side];
        s_gaso_attacking[side] = (uint8_t)attacking;
        if (new_hit) {
            tank->active = 1;
            tank->side = (uint8_t)side;
            tank->start_frame = frame;
            tank->opp_dancer = opp_dancer;
            tank->elapsed = 0;
            tank->released = 0;
            tank->clear_on_attack = 0;
            tank->lock_state = 1;
            tank->bubble_armed = 0;
            tank->landed = 0;
            tank->bubble_acc = 0;
            tank->last_beat = psx_mod_read_half(GASO_TANK_BEAT_ADDR);

            /* strike_read_root() is the rival's pelvis (~488); the tank must
             * rest on the dance floor, which is Y = 0 in dancer space. */
            StrikeVec3 target_floor = strike_read_root(opp_dancer);
            tank->target_x = target_floor.x;
            tank->target_y = 0;
            tank->target_z = target_floor.z;

            b1v_log("gaso_tank: spawn native mesh tank on side %u rival at (%d, %d, %d)",
                    side ^ 1u, target_floor.x, 0, target_floor.z);
            continue;
        }

        /* A paused/looping frame counter is not a new attack. Require an
         * observed slot transition after the hit, not a comparison of clocks. */
        if (!attacking) tank->clear_on_attack = 0;
        else if (attack_entry && tank->active) tank->clear_on_attack = 1;
        if (tank->active && tank->clear_on_attack &&
            anim_frame >= GASO_TANK_CLEAR_FRAME) {
            tank->active = 0;
            b1v_log("gaso_tank: next attack clears tank on side %u", side ^ 1u);
        }
    }
    s_gaso_hits_synced = 1;
    for (uint32_t side = 0; side < 2; ++side) gaso_tank_maintain(side);

    uint32_t heap = psx_mod_read_word(B2_HEAP_ADDR);
    uint32_t ot_addr = psx_mod_read_word(B2_OT_ADDR);
    if (heap < 0x80010000u || heap >= 0x807E0000u) return 0;
    if (ot_addr < 0x80010000u || ot_addr >= 0x807E0000u) return 0;
    int16_t cam_rot[9];
    int32_t cam_pos[3];
    strike_read_matrix(B2_CAM_ROT_ADDR, cam_rot, cam_pos);
    int32_t geom_h = (int32_t)psx_mod_read_word(B2_GEOM_H_ADDR);
    if (geom_h <= 0 || geom_h > 4096) return 0;
    uint32_t ot_slot = ot_addr + 8u;
    int emitted = 0;

    /* 3. Emit native chemical gas puffs from Gas-O's backpack nozzles during the
     * entrance (BAG1 vents a continuous dense cloud while the rival descends)
     * and during victory pose (anim 67). Upload the BAG1 smoke TIM to VRAM once
     * per match before emitting. */
    if (!s_gaso_smoke_uploaded) {
        const uint32_t scratch = 0x8000F000u;
        for (uint32_t i = 0; i < sizeof(s_gaso_smoke_clut); ++i) {
            psx_mod_write_byte(scratch + i, s_gaso_smoke_clut[i]);
        }
        psx_mod_psyq_load_image(GASO_SMOKE_CLUT_X, GASO_SMOKE_CLUT_Y,
                                GASO_SMOKE_CLUT_W, GASO_SMOKE_CLUT_H, scratch);
        for (uint32_t i = 0; i < sizeof(s_gaso_smoke_pix); ++i) {
            psx_mod_write_byte(scratch + i, s_gaso_smoke_pix[i]);
        }
        psx_mod_psyq_load_image(GASO_SMOKE_PIX_X, GASO_SMOKE_PIX_Y,
                                GASO_SMOKE_PIX_W, GASO_SMOKE_PIX_H, scratch);
        s_gaso_smoke_uploaded = 1;
    }

    int tpage_emitted = 0;
    for (uint32_t side = 0; side < 2; ++side) {
        uint32_t chr = psx_mod_read_word(side == 0 ? B2_CHAR_P1_ADDR : B2_CHAR_P2_ADDR);
        if (chr != GASO_CHAR_ID || !bag2jp_bag1_get_version((int)GASO_CHAR_ID, (int)side)) continue;

        uint32_t dancer = psx_mod_read_word(B2_DANCER_BASE + side * 8u);
        if (dancer < 0x80010000u || dancer >= 0x80800000u) continue;

        uint32_t anim = psx_mod_read_word(dancer + 0x154Cu);
        int is_entrance = (s_gaso_combat_frame >= 50u && s_gaso_combat_frame <= 300u);
        int is_victory = (anim == 67u);
        if (!is_entrance && !is_victory) continue;

        if (!tpage_emitted) {
            strike_emit_tpage(&heap, ot_slot, 0x001Cu); /* authentic Gas-O TPAGE 0x001C */
            tpage_emitted = 1;
        }

        StrikeVec3 root = strike_read_root(dancer);
        for (int puff = 0; puff < 3; ++puff) {
            uint32_t t = frame + (uint32_t)puff * 7u;
            /* Backpack height: pelvis minus ~40 units, drifting further up
             * (smaller Y) as the puff ages; +-26 units of lateral spread. */
            StrikeVec3 w = {
                root.x + ((int32_t)s_circle_cos[t % 16u] * 26) / 4096,
                root.y - 40 - (int32_t)((t * 3u) % 90u),
                root.z + ((int32_t)s_circle_sin[t % 16u] * 26) / 4096
            };
            StrikeScreenPt pt;
            if (!strike_project(&w, cam_rot, cam_pos, geom_h, &pt)) continue;

            int idx = 2 + (int)((t / 3u) % 6u);
            uint8_t sw = s_gaso_smoke_tbl[idx].w;
            uint8_t sh = s_gaso_smoke_tbl[idx].h;
            uint8_t su = (uint8_t)s_gaso_smoke_tbl[idx].u;
            uint8_t sv = (uint8_t)s_gaso_smoke_tbl[idx].v;
            int16_t hw = (int16_t)(sw / 2);
            int16_t hh = (int16_t)(sh / 2);

            gaso_emit_poly_ft4(&heap, ot_slot,
                               pt.x - hw, pt.y - hh,
                               pt.x + hw, pt.y - hh,
                               pt.x - hw, pt.y + hh,
                               pt.x + hw, pt.y + hh,
                               su, sv,
                               (uint8_t)(su + sw - 1), sv,
                               su, (uint8_t)(sv + sh - 1),
                               (uint8_t)(su + sw - 1), (uint8_t)(sv + sh - 1),
                               0x7C00u, 0x001Cu, 0x00E0FFE0u);
            emitted++;
        }
    }

    /* 4. Draw active cryogenic tanks using authentic BAG1 3D Mesh. */
    for (uint32_t side = 0; side < 2; ++side) {
        GasoTankState* tank = &s_gaso_tank[side];
        if (!tank->active) continue;

        /* Follow the current rival's transform; this visual does not own the
         * reaction animation. The floor-zero anchor is still an experimental
         * approximation, not the native floor-field contract. */
        uint32_t opp_dancer = psx_mod_read_word(B2_DANCER_BASE + (side ^ 1u) * 8u);
        StrikeVec3 root = strike_read_root(opp_dancer);
        tank->target_x = root.x;
        tank->target_z = root.z;

        /* +0x810 is in dancer space, not camera/world space. Match the native
         * renderer (0x8002C404), including the rival's model transform. */
        int16_t model_rot[9], tank_rot[9];
        int32_t model_pos[3], tank_pos[3];
        strike_read_matrix(opp_dancer + B2_DANCER_MTX_OFF, model_rot, model_pos);
        strike_comp_matrix(cam_rot, cam_pos, model_rot, model_pos, tank_rot, tank_pos);

        /* Diagnostic run: retain the native reaction. The CAUGHT adapter is not
         * runtime-integrated yet; never force slot78 or freeze frame0 here. */

        /* Calculate vertical descent offset (fall trajectory from above) */
        int32_t y_drop = 0;
        if (tank->elapsed < GASO_TANK_FALL_DUR) {
            uint32_t rem = GASO_TANK_FALL_DUR - tank->elapsed;
            y_drop = (int32_t)((1200u * rem * rem) / (GASO_TANK_FALL_DUR * GASO_TANK_FALL_DUR));
        }

        /* Transform and project all 41 authentic vertices of the BAG1 native mesh:
         * scaled by GASO_TANK_XZ_PCT / GASO_TANK_Y_PCT. */
        StrikeScreenPt pts[GASO_NATIVE_TANK_NUM_VERTS];
        int valid[GASO_NATIVE_TANK_NUM_VERTS];

        for (int i = 0; i < GASO_NATIVE_TANK_NUM_VERTS; ++i) {
            int32_t vx = tank->target_x + ((int32_t)s_gaso_native_verts[i][0] * GASO_TANK_XZ_PCT) / 100;
            /* Dancer-space +Y is up; the camera supplies the screen-space flip.
             * Negating height here would put both chamber and descent below the floor. */
            int32_t vy = tank->target_y + ((int32_t)s_gaso_native_verts[i][1] * GASO_TANK_Y_PCT) / 100 + y_drop;
            int32_t vz = tank->target_z + ((int32_t)s_gaso_native_verts[i][2] * GASO_TANK_XZ_PCT) / 100;

            StrikeVec3 p = { vx, vy, vz };
            valid[i] = strike_project(&p, tank_rot, tank_pos, geom_h, &pts[i]);
        }

        /* Cull like BAG1's NCLIP. Every stored face winds inward, so a face looks
         * at the camera iff its screen area has the sign of det(tank_rot); this
         * holds for any camera position and under a mirrored rival transform. */
        int64_t front =
            (int64_t)tank_rot[0] * ((int64_t)tank_rot[4] * tank_rot[8] - (int64_t)tank_rot[5] * tank_rot[7])
          - (int64_t)tank_rot[1] * ((int64_t)tank_rot[3] * tank_rot[8] - (int64_t)tank_rot[5] * tank_rot[6])
          + (int64_t)tank_rot[2] * ((int64_t)tank_rot[3] * tank_rot[7] - (int64_t)tank_rot[4] * tank_rot[6]);
        if (front == 0) continue;
        int32_t x_min = 0x7FFF, x_max = -0x8000;
        for (int q = 0; q < 8; ++q) {
            const uint8_t* f = s_gaso_glass_quads[q];
            for (int k = 0; k < 4; ++k) {
                if (!valid[f[k]]) continue;
                if (pts[f[k]].x < x_min) x_min = pts[f[k]].x;
                if (pts[f[k]].x > x_max) x_max = pts[f[k]].x;
            }
        }
        if (x_max <= x_min) continue;

        /* Approximation of BAG1's GTE vertex lighting (0x8002bbe8 normals and
         * depth cue, not reproduced): about twice as bright on the screen-left
         * side as on the right, as in the reference frames. The additive tint
         * keeps the previous averaged layer's median per third of the tank
         * (gaso-bubble-aspect-heat-bag1 at 3.83 s) at full background contrast,
         * whose spread is near BAG1's in gaso-vs-heat-autoplay at 31.0 s. */
        uint32_t glass_col[GASO_NATIVE_TANK_NUM_VERTS];
        uint32_t metal_col[GASO_NATIVE_TANK_NUM_VERTS];
        for (int i = 0; i < GASO_NATIVE_TANK_NUM_VERTS; ++i) {
            if (!valid[i]) { glass_col[i] = metal_col[i] = 0; continue; }
            int32_t x = pts[i].x < x_min ? x_min : (pts[i].x > x_max ? x_max : pts[i].x);
            int32_t lat = ((x_max - x) * 16) / (x_max - x_min); /* 16 = left edge */
            int32_t ny = s_gaso_native_verts[i][1];
            glass_col[i] = gaso_shade(GASO_GLASS_RGB, 18 + (lat * 18) / 16);
            metal_col[i] = gaso_shade(GASO_METAL_RGB, ny >= 4354 ? 28 + lat / 2 : 8 + lat / 2);
        }

        /* --- Bubbles: BAG1 shows one or two round, bluish, translucent bubbles
         * with a specular dot, rising slowly in the upper liquid. --- */
        StrikeScreenPt bub[2];
        int32_t bub_rx[2], bub_ry[2];
        int bubbles = 0;
        if (tank->elapsed >= GASO_TANK_FALL_DUR) {
            static const int16_t lane[5] = { -300, 260, 120, -160, 360 }; /* native X */
            uint32_t since = (uint32_t)tank->elapsed - GASO_TANK_FALL_DUR;
            for (uint32_t b = 0; b < 2u; ++b) {
                uint32_t lag = b * (GASO_BUBBLE_PERIOD / 2u);
                if (since < lag) continue;
                uint32_t age = (since - lag) % GASO_BUBBLE_PERIOD;
                int32_t lx = lane[(((since - lag) / GASO_BUBBLE_PERIOD) * 2u + b) % 5u];
                lx += ((int32_t)s_circle_sin[(age / 4u) % 16u] * 40) >> 12;
                /* Rise from 83% to 90% of the liquid column (native Y 371..3758),
                 * up against the top ring as in BAG1; the opaque ring, drawn
                 * later, hides any overlap (radius 68 is native Y 262). */
                int32_t ny = 371 + (3387 * (83 + (int32_t)((age * 8u) / GASO_BUBBLE_PERIOD))) / 100;
                int32_t r = (GASO_BUBBLE_RADIUS * (int32_t)(age < 6u ? age + 2u : 8u)) / 8;
                StrikeVec3 c = { tank->target_x + (lx * GASO_TANK_XZ_PCT) / 100,
                                 tank->target_y + (ny * GASO_TANK_Y_PCT) / 100, tank->target_z };
                if (!strike_project(&c, tank_rot, tank_pos, geom_h, &bub[bubbles])) continue;
                /* Billboard radius uses depth and effective pixel aspect.
                 * Presented roundness still requires in-game verification. */
                if (!gaso_bubble_screen_radii(r, geom_h, bub[bubbles].z,
                                             &bub_rx[bubbles], &bub_ry[bubbles])) continue;
                bubbles++;
            }
        }

        /* Packets are prepended to the OT slot, so the GPU draws them in reverse
         * emission order and each draw-mode packet follows the group it governs.
         * Draw order: additive mode, liquid tint, bubbles (clear centre,
         * bluish outline, then glints; additive so they never darken the rival),
         * opaque metal (covers bubbles seen from above), average mode again so
         * later packets never inherit the additive mode. */
        strike_emit_tpage(&heap, ot_slot, GASO_MODE_AVERAGE);

        /* --- Metal base, rings and bevel (24 G4) and top cap (8 G3): opaque
         * like BAG1 (codes 0x38/0x30). --- */
        for (int q = 0; q < 24; ++q) {
            if (!gaso_faces_camera(pts, valid, s_gaso_body_quads[q], 4, front)) continue;
            gaso_emit_quad_g4(&heap, ot_slot, 0, pts, s_gaso_body_quads[q], metal_col);
            emitted++;
        }
        for (int t = 0; t < 8; ++t) {
            const uint8_t* f = s_gaso_cap_tris[t];
            if (!gaso_faces_camera(pts, valid, f, 3, front)) continue;
            gaso_emit_poly_g3(&heap, ot_slot, 0, &pts[f[0]], metal_col[f[0]],
                              &pts[f[1]], metal_col[f[1]], &pts[f[2]], metal_col[f[2]]);
            emitted++;
        }

        for (int b = 0; b < bubbles; ++b) {
            int32_t hx = bub_rx[b] / 4, hy = bub_ry[b] / 4;
            emitted += gaso_emit_fan(&heap, ot_slot, (int16_t)(bub[b].x + hx), (int16_t)(bub[b].y - hy),
                                     hx < 1 ? 1 : hx, hy < 1 ? 1 : hy, GASO_GLINT_RGB, 0u);
        }
        for (int b = 0; b < bubbles; ++b)
            emitted += gaso_emit_ring(&heap, ot_slot, bub[b].x, bub[b].y,
                                      bub_rx[b], bub_ry[b], GASO_BUBBLE_RIM);

        /* --- Liquid-filled glass (8 G4): one camera-facing translucent layer
         * (code 0x3A) that tints what is behind it without halving it. --- */
        for (int q = 0; q < 8; ++q) {
            if (!gaso_faces_camera(pts, valid, s_gaso_glass_quads[q], 4, front)) continue;
            gaso_emit_quad_g4(&heap, ot_slot, 1, pts, s_gaso_glass_quads[q], glass_col);
            emitted++;
        }
        strike_emit_tpage(&heap, ot_slot, GASO_MODE_ADDITIVE);
    }

    psx_mod_write_word(B2_HEAP_ADDR, heap);
    return emitted;
}

#endif /* BAG2JP_GASO_TANK_H */
