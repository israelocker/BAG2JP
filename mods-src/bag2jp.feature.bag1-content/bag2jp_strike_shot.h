/* Strike BAG1 shot visual effect: muzzle flash, bullet tracer beam, and impact sparks.
 * Emits PSX GPU primitives directly into the match Ordering Table without modifying texture
 * memory or atlas coordinates. Preserves chest and emblema safety. */
#ifndef BAG2JP_STRIKE_SHOT_H
#define BAG2JP_STRIKE_SHOT_H

#include <stdint.h>
#include <string.h>

void b1v_log(const char* fmt, ...);

#define B2_ROOT_ADDR        0x8005D3D4u
#define B2_MODE_ADDR        0x8005D2C4u
#define B2_PHASE1_ADDR      0x8005D3D8u
#define B2_PHASE2_ADDR      0x8005D3DCu
#define B2_PHASE3_ADDR      0x8005D3E0u
#define B2_CHAR_P1_ADDR     0x8005E6A0u
#define B2_CHAR_P2_ADDR     0x8005E6A4u
#define B2_DANCER_BASE      0x8005F808u
#define B2_CAM_ROT_ADDR     0x8005D0F0u /* view MATRIX: m[3][3] int16, t[3] int32 at +0x14 */
#define B2_CAM_TRANS_ADDR   (B2_CAM_ROT_ADDR + 0x14u)
#define B2_GEOM_H_ADDR      0x8006D98Cu /* SetGeomScreen argument loaded at 0x8002DA78 */
#define B2_DANCER_ROOT_OFF  0x810u      /* projected root point, int16 values in words */
#define B2_DANCER_MTX_OFF   0x14C4u     /* dancer model MATRIX composed with the camera */
#define B2_HEAP_ADDR        0x80051A88u
#define B2_OT_ADDR          0x8006D990u

#define STRIKE_CHAR_ID      1u
#define STRIKE_ATTACK_ANIM  74u
#define STRIKE_SHOT_START   24u
#define STRIKE_SHOT_END     48u

int bag2jp_bag1_get_version(int chr, int side);

typedef struct {
    int32_t x, y, z;
} StrikeVec3;

typedef struct {
    int16_t x, y;
    int32_t z;
} StrikeScreenPt;

/* CompMatrix (0x80043A84): rot = m0 * m1, trans = (m0 * int16(m1.t) >> 12) + m0.t.
 * The dancer renderer 0x8002C404 composes camera 0x8005D0F0 with dancer +0x14C4 this way. */
static inline void strike_comp_matrix(const int16_t* r0, const int32_t* t0, const int16_t* r1, const int32_t* t1,
                                      int16_t* rot, int32_t* trans) {
    for (int i = 0; i < 3; ++i) {
        for (int j = 0; j < 3; ++j) {
            int32_t sum = 0;
            for (int k = 0; k < 3; ++k) sum += (int32_t)r0[i * 3 + k] * r1[k * 3 + j];
            rot[i * 3 + j] = (int16_t)(sum >> 12);
        }
        int64_t tsum = 0;
        for (int k = 0; k < 3; ++k) tsum += (int64_t)r0[i * 3 + k] * (int16_t)t1[k];
        trans[i] = (int32_t)(tsum >> 12) + t0[i];
    }
}

/* GTE RTPS equivalent with SetGeomOffset(256, 120) from 0x8002DCF8 (512x240 screen).
 * Includes 0.85x x-scaling factor matching dancer model scale relative to root. */
static inline int strike_project(const StrikeVec3* pt, const int16_t* rot, const int32_t* trans, int32_t h, StrikeScreenPt* out) {
    int64_t px = pt->x, py = pt->y, pz = pt->z;

    int64_t vx = ((rot[0] * px + rot[1] * py + rot[2] * pz) >> 12) + trans[0];
    int64_t vy = ((rot[3] * px + rot[4] * py + rot[5] * pz) >> 12) + trans[1];
    int64_t vz = ((rot[6] * px + rot[7] * py + rot[8] * pz) >> 12) + trans[2];

    if (vz <= 32 || vz >= 0x200000) return 0;

    int32_t raw_sx = (int32_t)((vx * h) / vz);
    out->x = (int16_t)(256 + (raw_sx * 85) / 100);
    out->y = (int16_t)((vy * h) / vz + 120);
    out->z = (int32_t)vz;
    return 1;
}

/* Dancer model matrix (+0x14C4: int16 m[3][3], int32 t[3] at +0x14D8). */
static inline void strike_read_matrix(uint32_t addr, int16_t* rot, int32_t* trans) {
    for (int i = 0; i < 9; ++i) rot[i] = (int16_t)psx_mod_read_half(addr + (uint32_t)i * 2u);
    for (int i = 0; i < 3; ++i) trans[i] = (int32_t)psx_mod_read_word(addr + 0x14u + (uint32_t)i * 4u);
}

/* Root point the renderer culls with RotTransPers: int16 x,y,z stored as words at +0x810. */
static inline StrikeVec3 strike_read_root(uint32_t dancer) {
    StrikeVec3 v = {
        (int16_t)psx_mod_read_word(dancer + B2_DANCER_ROOT_OFF),
        (int16_t)psx_mod_read_word(dancer + B2_DANCER_ROOT_OFF + 4u),
        (int16_t)psx_mod_read_word(dancer + B2_DANCER_ROOT_OFF + 8u)
    };
    return v;
}

static inline void strike_emit_poly_g4(uint32_t* heap_ptr, uint32_t ot_addr,
                                       int16_t x0, int16_t y0, uint32_t c0,
                                       int16_t x1, int16_t y1, uint32_t c1,
                                       int16_t x2, int16_t y2, uint32_t c2,
                                       int16_t x3, int16_t y3, uint32_t c3) {
    uint32_t heap = *heap_ptr;
    uint32_t ot_head = psx_mod_read_word(ot_addr);

    /* 9 words = 36 bytes = POLY_G4 */
    psx_mod_write_word(heap + 0x00u, (8u << 24) | (ot_head & 0x00FFFFFFu));
    psx_mod_write_word(heap + 0x04u, 0x3A000000u | (c0 & 0x00FFFFFFu)); /* semi-transparent G4 */
    psx_mod_write_word(heap + 0x08u, ((uint32_t)(uint16_t)y0 << 16) | (uint16_t)x0);
    psx_mod_write_word(heap + 0x0Cu, c1 & 0x00FFFFFFu);
    psx_mod_write_word(heap + 0x10u, ((uint32_t)(uint16_t)y1 << 16) | (uint16_t)x1);
    psx_mod_write_word(heap + 0x14u, c2 & 0x00FFFFFFu);
    psx_mod_write_word(heap + 0x18u, ((uint32_t)(uint16_t)y2 << 16) | (uint16_t)x2);
    psx_mod_write_word(heap + 0x1Cu, c3 & 0x00FFFFFFu);
    psx_mod_write_word(heap + 0x20u, ((uint32_t)(uint16_t)y3 << 16) | (uint16_t)x3);

    /* Link into OT */
    psx_mod_write_word(ot_addr, (ot_head & 0xFF000000u) | (heap & 0x00FFFFFFu));
    *heap_ptr = heap + 36u;
}

static inline void strike_emit_tpage(uint32_t* heap_ptr, uint32_t ot_addr, uint16_t tpage_val) {
    uint32_t heap = *heap_ptr;
    uint32_t ot_head = psx_mod_read_word(ot_addr);

    /* 2 words = 8 bytes = DR_TPAGE */
    psx_mod_write_word(heap + 0x00u, (1u << 24) | (ot_head & 0x00FFFFFFu));
    psx_mod_write_word(heap + 0x04u, 0xE1000000u | (uint32_t)tpage_val);

    psx_mod_write_word(ot_addr, (ot_head & 0xFF000000u) | (heap & 0x00FFFFFFu));
    *heap_ptr = heap + 8u;
}

static inline void strike_emit_spark(uint32_t* heap_ptr, uint32_t ot_addr, int16_t cx, int16_t cy, int16_t size, uint32_t color) {
    int16_t hs = size / 2;
    if (hs < 1) hs = 1;
    strike_emit_poly_g4(heap_ptr, ot_addr,
                        cx - hs, cy - hs, color,
                        cx + hs, cy - hs, color,
                        cx - hs, cy + hs, color,
                        cx + hs, cy + hs, color);
}

static inline int32_t strike_isqrt(int32_t v) {
    int32_t r = 0;
    while ((r + 1) * (r + 1) <= v) ++r;
    return r > 0 ? r : 1;
}

static int bag2jp_strike_shot_tick(uint32_t frame) {
    /* 1. Verify combat state */
    if (psx_mod_read_word(B2_ROOT_ADDR) != 19u) return 0;
    if (psx_mod_read_word(B2_MODE_ADDR) != 2u) return 0;
    if (psx_mod_read_word(B2_PHASE1_ADDR) != 1u) return 0;
    if (psx_mod_read_word(B2_PHASE2_ADDR) != 3u) return 0;
    if (psx_mod_read_word(B2_PHASE3_ADDR) != 3u) return 0;

    int emitted = 0;

    for (uint32_t side = 0; side < 2; ++side) {
        uint32_t char_id = psx_mod_read_word(side == 0 ? B2_CHAR_P1_ADDR : B2_CHAR_P2_ADDR);
        if (char_id != STRIKE_CHAR_ID) continue;
        if (!bag2jp_bag1_get_version((int)STRIKE_CHAR_ID, (int)side)) continue;

        uint32_t dancer = psx_mod_read_word(B2_DANCER_BASE + side * 8u);
        if (dancer < 0x80010000u || dancer >= 0x80800000u) continue;

        uint32_t anim = psx_mod_read_word(dancer + 0x154Cu);
        if (anim != STRIKE_ATTACK_ANIM) continue;

        uint32_t anim_frame = psx_mod_read_word(dancer + 0x1554u);
        if (anim_frame < STRIKE_SHOT_START || anim_frame > STRIKE_SHOT_END) continue;

        /* Target is the opponent */
        uint32_t opp_side = side ^ 1u;
        uint32_t opp_dancer = psx_mod_read_word(B2_DANCER_BASE + opp_side * 8u);
        if (opp_dancer < 0x80010000u || opp_dancer >= 0x80800000u) continue;

        /* Native dancer transform: camera 0x8005D0F0 composed with each dancer's +0x14C4 matrix. */
        int16_t cam_rot[9];
        int32_t cam_pos[3];
        strike_read_matrix(B2_CAM_ROT_ADDR, cam_rot, cam_pos);
        int32_t geom_h = (int32_t)psx_mod_read_word(B2_GEOM_H_ADDR);
        if (geom_h <= 0 || geom_h > 4096) continue;

        int16_t d_rot[9], o_rot[9], shoot_rot[9], targ_rot[9];
        int32_t d_t[3], o_t[3], shoot_t[3], targ_t[3];
        strike_read_matrix(dancer + B2_DANCER_MTX_OFF, d_rot, d_t);
        strike_read_matrix(opp_dancer + B2_DANCER_MTX_OFF, o_rot, o_t);
        strike_comp_matrix(cam_rot, cam_pos, d_rot, d_t, shoot_rot, shoot_t);
        strike_comp_matrix(cam_rot, cam_pos, o_rot, o_t, targ_rot, targ_t);

        StrikeVec3 shooter_pos = strike_read_root(dancer);
        StrikeVec3 target_pos = strike_read_root(opp_dancer);

        /* Gun and chest offsets from the root, in dancer space (+y is up on screen). */
        int gun_dir = (target_pos.x >= shooter_pos.x) ? 1 : -1;
        int hand_x_off = (anim_frame <= 27u) ? (gun_dir * 80) : (-gun_dir * 70);
        StrikeVec3 muzzle_left = { shooter_pos.x + hand_x_off, shooter_pos.y + 210, shooter_pos.z + 40 };
        StrikeVec3 muzzle_right = { shooter_pos.x + hand_x_off + gun_dir * 10, shooter_pos.y + 200, shooter_pos.z - 20 };
        StrikeVec3 chest_target = { target_pos.x, target_pos.y + 230, target_pos.z };
        StrikeVec3 shooter_root = shooter_pos;
        StrikeVec3 target_root = target_pos;

        StrikeScreenPt s_muzzle_l, s_muzzle_r, s_target, s_sroot, s_troot;
        int ok_l = strike_project(&muzzle_left, shoot_rot, shoot_t, geom_h, &s_muzzle_l);
        int ok_r = strike_project(&muzzle_right, shoot_rot, shoot_t, geom_h, &s_muzzle_r);
        int ok_t = strike_project(&chest_target, targ_rot, targ_t, geom_h, &s_target);
        int ok_sr = strike_project(&shooter_root, shoot_rot, shoot_t, geom_h, &s_sroot);
        int ok_tr = strike_project(&target_root, targ_rot, targ_t, geom_h, &s_troot);

        b1v_log("strike_shot f%u anim_frame %u h%d: root(%d,%d,%d)->(%d,%d ok%d) troot(%d,%d,%d)->(%d,%d ok%d)"
                " d_t(%d,%d,%d) o_t(%d,%d,%d) -> ml(%d,%d,z%d ok%d) mr(%d,%d,z%d ok%d) targ(%d,%d,z%d ok%d)",
                frame, anim_frame, geom_h,
                shooter_pos.x, shooter_pos.y, shooter_pos.z, s_sroot.x, s_sroot.y, ok_sr,
                target_pos.x, target_pos.y, target_pos.z, s_troot.x, s_troot.y, ok_tr,
                d_t[0], d_t[1], d_t[2], o_t[0], o_t[1], o_t[2],
                s_muzzle_l.x, s_muzzle_l.y, s_muzzle_l.z, ok_l,
                s_muzzle_r.x, s_muzzle_r.y, s_muzzle_r.z, ok_r,
                s_target.x, s_target.y, s_target.z, ok_t);

        if (!ok_l || !ok_r || !ok_t) continue;

        /* Heap and OT */
        uint32_t heap = psx_mod_read_word(B2_HEAP_ADDR);
        uint32_t ot_addr = psx_mod_read_word(B2_OT_ADDR);
        if (heap < 0x80010000u || heap >= 0x807E0000u) continue;
        if (ot_addr < 0x80010000u || ot_addr >= 0x807E0000u) continue;

        /* Target OT entry: slot 2 or 3 (front layers) */
        uint32_t ot_slot = ot_addr + 8u;

        /* Additive blending mode (mode 1: B + F) */
        strike_emit_tpage(&heap, ot_slot, 0x0020u);

        /* 1. Gun bursts: muzzle flashes and short bullet tracer streaks */
        if (anim_frame >= STRIKE_SHOT_START && anim_frame <= 39u) {
            StrikeScreenPt* muzzles[2] = { &s_muzzle_l, &s_muzzle_r };
            for (int m = 0; m < 2; ++m) {
                if (m == 1 && ((anim_frame & 1u) == 0)) continue; /* alternate or dual fire */
                StrikeScreenPt* muz = muzzles[m];

                /* Muzzle flash */
                strike_emit_spark(&heap, ot_slot, muz->x, muz->y, 8, 0x00FFFFFFu);
                emitted++;

                /* Short bullet tracer streak in firing direction */
                int16_t streak_dx, streak_dy;
                if (anim_frame <= 27u) {
                    /* Down-forward burst towards floor */
                    streak_dx = (int16_t)(gun_dir * 32);
                    streak_dy = 16;
                } else {
                    /* Lateral burst: Strike turns horizontally away/left */
                    streak_dx = (int16_t)(-gun_dir * 36);
                    streak_dy = (int16_t)(((anim_frame & 2u) != 0) ? 6 : -6);
                }

                int32_t len2 = (int32_t)streak_dx * streak_dx + (int32_t)streak_dy * streak_dy;
                int32_t len = strike_isqrt(len2);
                int16_t nx = (int16_t)(-streak_dy * 2 / len);
                int16_t ny = (int16_t)(streak_dx * 2 / len);
                if (nx == 0 && ny == 0) { nx = 0; ny = 2; }

                uint32_t streak_c0 = 0x00FFFFFFu; /* White at gun muzzle */
                uint32_t streak_c1 = 0x0030E0FFu; /* Bright golden yellow */
                uint32_t streak_c2 = 0x001080FFu; /* Fading orange tip */

                strike_emit_poly_g4(&heap, ot_slot,
                                    muz->x + nx, muz->y + ny, streak_c0,
                                    muz->x - nx, muz->y - ny, streak_c0,
                                    muz->x + streak_dx + nx / 2, muz->y + streak_dy + ny / 2, streak_c1,
                                    muz->x + streak_dx - nx / 2, muz->y + streak_dy - ny / 2, streak_c2);
                emitted++;
            }
        }

        /* 2. Opponent impact cloud: orange pixelated particles covering chest to feet */
        if (anim_frame >= 26u && anim_frame <= 46u) {
            int16_t y_top = s_target.y;
            int16_t y_bot = s_troot.y;
            if (y_bot <= y_top) y_bot = (int16_t)(y_top + 30);
            int16_t span = (int16_t)(y_bot - y_top);

            for (int i = 0; i < 8; ++i) {
                uint32_t seed = frame * 19u + anim_frame * 31u + (uint32_t)i * 47u;
                int16_t py = (int16_t)(y_top + (int16_t)((seed % 32u) * (uint32_t)span / 32u));
                int16_t px = (int16_t)(s_target.x + (int16_t)((seed >> 5) % 25u) - 12);
                int16_t psize = (int16_t)(4 + ((seed >> 10) & 3u) * 2);
                uint32_t pcol;
                switch ((seed >> 12) & 3u) {
                    case 0:  pcol = 0x002080FFu; break; /* Bright orange */
                    case 1:  pcol = 0x0030C0FFu; break; /* Amber / yellow */
                    case 2:  pcol = 0x001050E0u; break; /* Deep orange */
                    default: pcol = 0x0050FFFFu; break; /* Hot white-yellow spark */
                }
                strike_emit_spark(&heap, ot_slot, px, py, psize, pcol);
                emitted++;
            }
        }

        /* Update heap pointer in RAM */
        psx_mod_write_word(B2_HEAP_ADDR, heap);
    }

    return emitted;
}

#endif
