/* Gas-O Authentic BAG1 Attack Visual Effect & Rival Reaction:
 * - Direct implementation of authentic 3D Tank Mesh from BAG1 PLAYER2/P_GAS_A2.DFS Member 2
 * - Authentic 41-vertex geometry, 8-quad glass chamber, 24-quad metal body, 8-triangle metal cap
 * - Factory BAG1 PS1 colors: Metal RGB(89,89,102), Chemical Glass RGB(125,255,106)
 * - Emits volumetric native cryo-smoke puffs using authentic BAG1 UV table (0x801DCE4C) & TIMs
 * - Falls from above with accelerated gravity trajectory onto rival
 * - Smooth fade out upon tank break/dissolution
 * - Preserves rival standing/stunned state (no knockdown, slot 78) for all BAG2 characters
 * - Uses shared matrix math and OT helpers from bag2jp_strike_shot.h
 */
#ifndef BAG2JP_GASO_TANK_H
#define BAG2JP_GASO_TANK_H

#include <stdint.h>
#include <string.h>

#define GASO_CHAR_ID        9u
#define GASO_ATTACK_ANIM    74u
#define GASO_ATTACK_START   20u
#define GASO_ATTACK_END     65u

#define GASO_TANK_FALL_DUR  12u  /* Frames of vertical descent from above */
#define GASO_TANK_HOLD_DUR  65u  /* Frames of locked cryo-trap confinement */
#define GASO_TANK_FADE_DUR  15u  /* Frames of smooth evaporation fade out */
#define GASO_TANK_TOTAL_DUR (GASO_TANK_FALL_DUR + GASO_TANK_HOLD_DUR + GASO_TANK_FADE_DUR)

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
    uint32_t start_frame;
    uint32_t opp_dancer;
    int32_t target_x;
    int32_t target_y;
    int32_t target_z;
    uint16_t elapsed;
} GasoTankState;

static GasoTankState s_gaso_tank[2];
static uint8_t s_gaso_attack_seen[2];
static uint32_t s_gaso_combat_frame;

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
    s_gaso_attack_seen[0] = 0;
    s_gaso_attack_seen[1] = 0;
    s_gaso_combat_frame = 0;
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

static int bag2jp_gaso_tank_tick(uint32_t frame) {
    /* 1. Verify combat scene root (root 19) */
    if (psx_mod_read_word(B2_ROOT_ADDR) != 19u) {
        bag2jp_gaso_tank_reset();
        return 0;
    }
    ++s_gaso_combat_frame;

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

    /* 2. Process attack trigger per side */
    for (uint32_t side = 0; side < 2; ++side) {
        uint32_t chr = psx_mod_read_word(side == 0 ? B2_CHAR_P1_ADDR : B2_CHAR_P2_ADDR);
        if (chr != GASO_CHAR_ID || !bag2jp_bag1_get_version((int)GASO_CHAR_ID, (int)side)) {
            s_gaso_attack_seen[side] = 0;
            continue;
        }

        uint32_t dancer = psx_mod_read_word(B2_DANCER_BASE + side * 8u);
        uint32_t opp_dancer = psx_mod_read_word(B2_DANCER_BASE + (side ^ 1u) * 8u);
        if (dancer < 0x80010000u || dancer >= 0x80800000u ||
            opp_dancer < 0x80010000u || opp_dancer >= 0x80800000u) {
            s_gaso_attack_seen[side] = 0;
            continue;
        }

        uint32_t anim = psx_mod_read_word(dancer + 0x154Cu);
        uint32_t anim_frame = psx_mod_read_word(dancer + 0x1554u);

        /* Attack animation slot 74 (or 88) */
        if (s_gaso_combat_frame >= 600u && (anim == GASO_ATTACK_ANIM || anim == 88u)) {
            if (anim_frame >= 25u && anim_frame <= 66u) {
                if (!s_gaso_attack_seen[side]) {
                    s_gaso_attack_seen[side] = 1;
                    GasoTankState* tank = &s_gaso_tank[side];
                    tank->active = 1;
                    tank->side = (uint8_t)side;
                    tank->start_frame = frame;
                    tank->opp_dancer = opp_dancer;
                    tank->elapsed = 0;

                    /* strike_read_root() is the rival's pelvis (~488); the tank must
                     * rest on the dance floor, which is Y = 0 in dancer space. */
                    StrikeVec3 target_floor = strike_read_root(opp_dancer);
                    tank->target_x = target_floor.x;
                    tank->target_y = 0;
                    tank->target_z = target_floor.z;

                    b1v_log("gaso_tank: spawn native mesh tank on side %u rival at (%d, %d, %d)",
                            side ^ 1u, target_floor.x, 0, target_floor.z);
                }
            }
        } else {
            s_gaso_attack_seen[side] = 0;
        }
    }

    /* 3. Emit native chemical gas puffs from Gas-O's backpack nozzles during the
     * entrance (BAG1 vents a continuous dense cloud while the rival descends). */
    if (s_gaso_combat_frame >= 50u && s_gaso_combat_frame <= 300u) {
        strike_emit_tpage(&heap, ot_slot, 0x001Cu); /* authentic Gas-O TPAGE 0x001C */
        for (uint32_t side = 0; side < 2; ++side) {
            uint32_t chr = psx_mod_read_word(side == 0 ? B2_CHAR_P1_ADDR : B2_CHAR_P2_ADDR);
            if (chr != GASO_CHAR_ID || !bag2jp_bag1_get_version((int)GASO_CHAR_ID, (int)side)) continue;

            uint32_t dancer = psx_mod_read_word(B2_DANCER_BASE + side * 8u);
            if (dancer < 0x80010000u || dancer >= 0x80800000u) continue;

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

                int idx = 2 + (int)((t / 3u) % 8u);
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
    }

    /* 4. Draw & maintain active cryogenic tanks using authentic BAG1 3D Mesh */
    for (uint32_t side = 0; side < 2; ++side) {
        GasoTankState* tank = &s_gaso_tank[side];
        if (!tank->active) continue;

        if (tank->elapsed < GASO_TANK_TOTAL_DUR) {
            tank->elapsed++;
        } else {
            tank->active = 0;
            continue;
        }

        /* Refresh the rival dancer pointer every frame so the tank follows the rival
         * and the freeze applies to the correct character. The tank must stay
         * anchored on top of the rival (floor contact at Y = 0). */
        uint32_t opp_dancer = psx_mod_read_word(B2_DANCER_BASE + (side ^ 1u) * 8u);
        tank->opp_dancer = opp_dancer;
        if (opp_dancer >= 0x80010000u && opp_dancer < 0x80800000u) {
            StrikeVec3 root = strike_read_root(opp_dancer);
            tank->target_x = root.x;
            tank->target_z = root.z;
        }

        /* Keep rival frozen upright inside the cryogenic tank (slot 78, no knockdown).
         * Applies for the whole hold window so the rival never breaks out early. */
        if (opp_dancer >= 0x80010000u && opp_dancer < 0x80800000u) {
            if (tank->elapsed >= GASO_TANK_FALL_DUR && tank->elapsed < (GASO_TANK_FALL_DUR + GASO_TANK_HOLD_DUR)) {
                psx_mod_write_word(opp_dancer + 0x154Cu, 78u); /* standing stunned / caught */
                psx_mod_write_word(opp_dancer + 0x1554u, 0u);  /* freeze animation frame */
                psx_mod_write_half(0x8005CF08u + (uint32_t)(tank->side ^ 1u) * 0x24u + 20u, 0u);
            }
        }

        /* Calculate vertical descent offset (fall trajectory from above) */
        int32_t y_drop = 0;
        if (tank->elapsed < GASO_TANK_FALL_DUR) {
            uint32_t rem = GASO_TANK_FALL_DUR - tank->elapsed;
            y_drop = (int32_t)((1200u * rem * rem) / (GASO_TANK_FALL_DUR * GASO_TANK_FALL_DUR));
        }

        /* Calculate fade multiplier (0..255) for smooth dissolution */
        uint32_t alpha_scale = 255u;
        if (tank->elapsed > (GASO_TANK_FALL_DUR + GASO_TANK_HOLD_DUR)) {
            uint32_t fade_cur = tank->elapsed - (GASO_TANK_FALL_DUR + GASO_TANK_HOLD_DUR);
            if (fade_cur <= GASO_TANK_FADE_DUR) {
                alpha_scale = ((GASO_TANK_FADE_DUR - fade_cur) * 255u) / GASO_TANK_FADE_DUR;
            } else {
                alpha_scale = 0;
            }
        }

        if (alpha_scale == 0) continue;

        /* Transform and project all 41 authentic vertices of the BAG1 native mesh:
         * Scale factors to fit BAG2 world coordinates:
         * Native Y: 0..4480 -> scaled by 22/100 gives 0..985 units height
         * Native XZ: radius 1080 -> scaled by 35/100 gives radius 378 units
         */
        StrikeScreenPt pts[GASO_NATIVE_TANK_NUM_VERTS];
        int valid[GASO_NATIVE_TANK_NUM_VERTS];

        for (int i = 0; i < GASO_NATIVE_TANK_NUM_VERTS; ++i) {
            int32_t vx = tank->target_x + ((int32_t)s_gaso_native_verts[i][0] * 35) / 100;
            /* PSX GTE world space: -Y is up, so the native +Y height must be
             * subtracted, and y_drop is a positive offset above the floor. */
            int32_t vy = tank->target_y - ((int32_t)s_gaso_native_verts[i][1] * 22) / 100 - y_drop;
            int32_t vz = tank->target_z + ((int32_t)s_gaso_native_verts[i][2] * 35) / 100;

            StrikeVec3 p = { vx, vy, vz };
            valid[i] = strike_project(&p, cam_rot, cam_pos, geom_h, &pts[i]);
        }

        /* --- 1. Translucent cryo-glass chamber (8 quads), drawn first so the
         * opaque metal rings stay in front of it. A dim chemical-green tint
         * replaces the old additive lime wash that turned the tank into a
         * solid green box; far side first, near side after. --- */
        strike_emit_tpage(&heap, ot_slot, 0x0020u); /* semi-transparent blend */
        uint32_t glass_r = (0x14u * alpha_scale) >> 8;
        uint32_t glass_g = (0x42u * alpha_scale) >> 8;
        uint32_t glass_b = (0x1Cu * alpha_scale) >> 8;
        uint32_t glass_far = glass_r | (glass_g << 8) | (glass_b << 16);
        uint32_t glass_near = (glass_r * 2u) | ((glass_g * 2u) << 8) | ((glass_b * 2u) << 16);

        for (int pass = 0; pass < 2; ++pass) {
            for (int q = 0; q < 8; ++q) {
                uint8_t i0 = s_gaso_glass_quads[q][0];
                uint8_t i1 = s_gaso_glass_quads[q][3];
                uint8_t i2 = s_gaso_glass_quads[q][1];
                uint8_t i3 = s_gaso_glass_quads[q][2];
                if (!valid[i0] || !valid[i1] || !valid[i2] || !valid[i3]) continue;

                /* Screen-space winding separates the far side from the near side. */
                int32_t cross = (int32_t)(pts[i1].x - pts[i0].x) * (int32_t)(pts[i2].y - pts[i0].y)
                              - (int32_t)(pts[i1].y - pts[i0].y) * (int32_t)(pts[i2].x - pts[i0].x);
                int near_side = cross < 0;
                if ((pass == 0) == near_side) continue;

                uint32_t col = near_side ? glass_near : glass_far;
                strike_emit_poly_g4(&heap, ot_slot,
                                    pts[i0].x, pts[i0].y, col,
                                    pts[i1].x, pts[i1].y, col,
                                    pts[i2].x, pts[i2].y, col,
                                    pts[i3].x, pts[i3].y, col);
                emitted++;
            }
        }

        /* --- 2. Render Metal Base & Body Rings (24 quads) --- */
        strike_emit_tpage(&heap, ot_slot, 0x0000u); /* Opaque standard blend */
        /* Native Metal color: RGB(89, 89, 102) = (0x59, 0x59, 0x66) */
        uint32_t metal_r = (0x59u * alpha_scale) >> 8;
        uint32_t metal_g = (0x59u * alpha_scale) >> 8;
        uint32_t metal_b = (0x66u * alpha_scale) >> 8;
        uint32_t metal_col = metal_r | (metal_g << 8) | (metal_b << 16);

        for (int q = 0; q < 24; ++q) {
            uint8_t i0 = s_gaso_body_quads[q][0];
            uint8_t i1 = s_gaso_body_quads[q][3];
            uint8_t i2 = s_gaso_body_quads[q][1];
            uint8_t i3 = s_gaso_body_quads[q][2];

            if (valid[i0] && valid[i1] && valid[i2] && valid[i3]) {
                strike_emit_poly_g4(&heap, ot_slot,
                                    pts[i0].x, pts[i0].y, metal_col,
                                    pts[i1].x, pts[i1].y, metal_col,
                                    pts[i2].x, pts[i2].y, metal_col,
                                    pts[i3].x, pts[i3].y, metal_col);
                emitted++;
            }
        }

        /* --- 3. Render Metal Top Bevel/Cap (8 triangles) --- */
        for (int t = 0; t < 8; ++t) {
            uint8_t i0 = s_gaso_cap_tris[t][0];
            uint8_t i1 = s_gaso_cap_tris[t][1];
            uint8_t i2 = s_gaso_cap_tris[t][2];

            if (valid[i0] && valid[i1] && valid[i2]) {
                gaso_emit_poly_f3(&heap, ot_slot,
                                    pts[i0].x, pts[i0].y,
                                    pts[i1].x, pts[i1].y,
                                    pts[i2].x, pts[i2].y,
                                    metal_col);
                emitted++;
            }
        }

        /* --- 4. Render Volumetric Cryo-Smoke Puffs (Authentic UV Table 0x801DCE4C) --- */
        strike_emit_tpage(&heap, ot_slot, 0x001Cu); /* Authentic Gas-O TPAGE: 0x001C */
        uint16_t clut_gaso = 0x7C00u;
        uint32_t smoke_val = (0xD8u * alpha_scale) >> 8;
        uint32_t smoke_col = smoke_val | (smoke_val << 8) | (((0xE8u * alpha_scale) >> 8) << 16);

        for (int b = 2; b < 16; ++b) {
            int seg = (frame * 2u + (uint32_t)b * 5u) % 8u;
            uint8_t v_bot = s_gaso_glass_quads[seg][1];
            uint8_t v_top = s_gaso_glass_quads[seg][0];

            if (valid[v_bot] && valid[v_top]) {
                int32_t progress = (int32_t)((frame * 3u + (uint32_t)b * 23u) % 100u);
                int16_t cy = pts[v_bot].y - (int16_t)(((pts[v_bot].y - pts[v_top].y) * progress) / 100);
                int16_t cx = pts[v_bot].x + (int16_t)((s_circle_cos[(frame + b) % 16] * 20) >> 12);

                uint8_t sw = s_gaso_smoke_tbl[b].w;
                uint8_t sh = s_gaso_smoke_tbl[b].h;
                uint8_t su = (uint8_t)s_gaso_smoke_tbl[b].u;
                uint8_t sv = (uint8_t)s_gaso_smoke_tbl[b].v;

                int16_t hw = (int16_t)(sw / 2);
                int16_t hh = (int16_t)(sh / 2);

                gaso_emit_poly_ft4(&heap, ot_slot,
                                   cx - hw, cy - hh,
                                   cx + hw, cy - hh,
                                   cx - hw, cy + hh,
                                   cx + hw, cy + hh,
                                   su, sv,
                                   su + sw - 1, sv,
                                   su, sv + sh - 1,
                                   su + sw - 1, sv + sh - 1,
                                   clut_gaso, 0x001Cu, smoke_col);
                emitted++;
            }
        }

        /* --- 5. Air bubbles floating up inside chemical fluid --- */
        uint32_t air_bub_val = (0xD0u * alpha_scale) >> 8;
        uint32_t air_bub_col = air_bub_val | (air_bub_val << 8) | (air_bub_val << 16);
        for (int b = 0; b < 8; ++b) {
            int seg = (frame * 2u + b * 4u) % 8u;
            uint8_t v_bot = s_gaso_glass_quads[seg][1];
            uint8_t v_top = s_gaso_glass_quads[seg][0];

            if (valid[v_bot] && valid[v_top]) {
                int32_t bub_progress = (int32_t)((frame * 5u + b * 27u) % 100u);
                int16_t by = pts[v_bot].y - (int16_t)(((pts[v_bot].y - pts[v_top].y) * (40 + bub_progress / 2)) / 100);
                int16_t bx = pts[v_bot].x + (int16_t)((s_circle_cos[(frame * 2 + b * 3) % 16] * 14) >> 12);
                int16_t b_sz = 8 + (int16_t)((b * 2) % 6);
                strike_emit_spark(&heap, ot_slot, bx, by, b_sz, air_bub_col);
                emitted++;
            }
        }
    }

    psx_mod_write_word(B2_HEAP_ADDR, heap);
    return emitted;
}

#endif /* BAG2JP_GASO_TANK_H */
