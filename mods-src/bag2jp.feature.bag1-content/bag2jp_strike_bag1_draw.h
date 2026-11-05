/* Native Strike BAG1 FT4 rendering. Included after the shared projection/Heat GPU helpers.
 * Simulation is kept independent in bag2jp_strike_bag1_fx.h. */
#ifndef BAG2JP_STRIKE_BAG1_DRAW_H
#define BAG2JP_STRIKE_BAG1_DRAW_H

#include "bag2jp_strike_bag1_fx.h"

#define STRIKE_B1_BONES_OFF 0x28u
#define STRIKE_B1_BONE_STRIDE 0xB0u
#define STRIKE_B1_BONE_MATRIX 0x2Cu
#define STRIKE_B1_STAGE_PTR 0x80089200u
#define STRIKE_B1_STAGE_MATRIX 0x34u
#define STRIKE_B1_GUN_NEAR (-4000)
#define STRIKE_B1_GUN_FAR (-32000)
#define STRIKE_B1_BEAM_WIDTH 0x1200

static StrikeB1Fx s_strike_b1_fx[2];
static unsigned s_strike_b1_previous[2];
static uint32_t s_strike_b1_last_ot;

static inline void strike_b1_reset(void) {
    memset(s_strike_b1_fx, 0, sizeof(s_strike_b1_fx));
    memset(s_strike_b1_previous, 0, sizeof(s_strike_b1_previous));
    s_strike_b1_last_ot = 0;
}

/* Native bones 1B/1A are initialized as copies of hands 15/11 in both imported costumes.
 * B payload entries 145/146 force the A initializer (branch at DBI file +10480 is nop).
 * Do not apply stock BAG2 B's one-bone decrement to these imported skeletons.
 * +2C is the skeletal hierarchy's actor-space matrix. FUN_8002C404 temporarily replaces
 * the global camera with camera*dancer while calling the DBI; vblank must compose it too. */
static inline int strike_b1_gun(uint32_t dancer, unsigned gun, StrikeB1Vec* a, StrikeB1Vec* b) {
    uint32_t bones = psx_mod_read_word(dancer + STRIKE_B1_BONES_OFF);
    unsigned index = gun == 0 ? 0x1Bu : 0x1Au;
    uint32_t matrix = bones + index * STRIKE_B1_BONE_STRIDE + STRIKE_B1_BONE_MATRIX;
    if (!heat_valid_ptr(bones) || !heat_valid_ptr(matrix + 0x1Cu)) return 0;
    int16_t rot[9];
    int32_t trans[3];
    strike_read_matrix(matrix, rot, trans);
    int32_t* va[3] = {&a->x, &a->y, &a->z};
    int32_t* vb[3] = {&b->x, &b->y, &b->z};
    for (int i = 0; i < 3; ++i) {
        *va[i] = ((int32_t)rot[i * 3 + 1] * STRIKE_B1_GUN_NEAR >> 12) + (int16_t)trans[i];
        *vb[i] = ((int32_t)rot[i * 3 + 1] * STRIKE_B1_GUN_FAR >> 12) + (int16_t)trans[i];
    }
    return 1;
}

static inline int strike_b1_draw_beam(HeatDrawCtx* c, const StrikeB1Shot* shot) {
    if (shot->state != 1) return 0;
    StrikeVec3 a = {shot->a.x, shot->a.y, shot->a.z}, b = {shot->b.x, shot->b.y, shot->b.z};
    StrikeScreenPt sa, sb;
    if (!strike_project(&a, c->rot[0], c->trans[0], c->h, &sa) ||
        !strike_project(&b, c->rot[0], c->trans[0], c->h, &sb)) return 0;
    int32_t za = sa.z >> 2, zb = sb.z >> 2, otz = (za + zb) / 2;
    if (shot->count == 0)
        b1v_log("strike_b1 beam a(%d,%d,z%d) b(%d,%d,z%d) t(%d,%d,%d) h%d clut%04x page%04x",
                sa.x, sa.y, sa.z, sb.x, sb.y, sb.z, c->trans[0][0], c->trans[0][1], c->trans[0][2],
                c->h, c->clut, c->tpage);
    if (!za || !zb || (uint32_t)(otz - 0x60) >= 0x1000u) return 0;
    int32_t dx = sb.x - sa.x, dy = sb.y - sa.y;
    int32_t length = strike_isqrt(dx * dx + dy * dy);
    int32_t nx = dx * 4096 / length, ny = dy * 4096 / length;
    int32_t ka = STRIKE_B1_BEAM_WIDTH / za, kb = STRIKE_B1_BEAM_WIDTH / zb;
    /* Integer division rounds toward zero, matching the original signed shifts. */
    int16_t xa = (int16_t)(ny * ka / 2048), xb = (int16_t)(ny * kb / 2048);
    int16_t ya = (int16_t)(nx * ka / 4096), yb = (int16_t)(nx * kb / 4096);
    HeatQuad q = {{sa.x + xa, sa.x - xa, sb.x + xb, sb.x - xb},
                  {sa.y - ya, sa.y + ya, sb.y - yb, sb.y + ya},
                  {0, 0, 0xC0, 0xC0}, {0, 0x18, 0, 0x18}, 0x80,
                  (uint16_t)(c->clut + shot->count * 0x40), otz - 0x60};
    return heat_emit_ft4(c, &q);
}

static inline int strike_b1_draw_particle(HeatDrawCtx* c, const StrikeB1Particle* p) {
    static const uint16_t palette[4] = {3, 4, 5, 5};
    HeatVec3 pos = {p->pos.x / STRIKE_B1_FIXED, p->pos.y / STRIKE_B1_FIXED,
                   p->pos.z / STRIKE_B1_FIXED};
    StrikeScreenPt s;
    if (!heat_project(c, HEAT_FRAME_TARGET, &pos, &s)) return 0;
    int32_t otz = s.z >> 2;
    if ((uint32_t)(otz - 0x60) >= 0x1000u) return 0;
    int32_t size = p->size * HEAT_POS_SCALE_Q12 / 4096;
    int16_t hw = (int16_t)((16 * size * 32 / 5) / otz);
    int16_t hh = (int16_t)((16 * size * 4) / otz);
    uint8_t u = (uint8_t)(p->frame * 16 + 0x40);
    HeatQuad q = {{s.x - hw, s.x + hw, s.x - hw, s.x + hw},
                  {s.y - hh, s.y - hh, s.y + hh, s.y + hh},
                  {u, u + 15, u, u + 15}, {0, 0, 15, 15}, 0x80,
                  (uint16_t)(c->clut + palette[p->frame] * 0x40), otz - 0x60};
    return heat_emit_ft4(c, &q);
}

static inline void strike_b1_spawn_events(uint32_t side, uint32_t dancer, uint32_t opponent,
                                          uint32_t frame) {
    unsigned anim = psx_mod_read_word(dancer + 0x154Cu);
    unsigned current = psx_mod_read_word(dancer + 0x1554u);
    if (anim != STRIKE_ATTACK_ANIM || current > 59u) { s_strike_b1_previous[side] = 0; return; }
    unsigned previous = s_strike_b1_previous[side];
    if (current < previous) previous = 0;
    unsigned events = strike_b1_crossings(previous, current);
    s_strike_b1_previous[side] = current;
    StrikeB1Fx* fx = &s_strike_b1_fx[side];
    HeatVec3 floor = heat_dancer_floor(opponent);
    StrikeB1Vec target = {floor.x, 1000, floor.z};
    if (!fx->seed) fx->seed = 0xB1u ^ frame;
    for (unsigned e = 0; e < STRIKE_B1_EVENT_COUNT; ++e) {
        if (!(events & (1u << e))) continue;
        for (unsigned gun = 0; gun < 2; ++gun) {
            StrikeB1Vec a, b;
            if (!strike_b1_gun(dancer, gun, &a, &b)) continue;
            strike_b1_spawn(fx, &a, &b, &target, 1);
            b1v_log("strike_b1 f%u side%u anim_frame%u gun%u a(%d,%d,%d) b(%d,%d,%d)",
                    frame, side, current, gun, a.x, a.y, a.z, b.x, b.y, b.z);
        }
    }
}

static inline int strike_b1_draw_side(HeatDrawCtx* c, StrikeB1Fx* fx, int dt) {
    int n = 0;
    for (int i = 0; i < STRIKE_B1_SHOTS; ++i) n += strike_b1_draw_beam(c, &fx->shots[i]);
    strike_b1_update_shots(fx, dt);
    /* Native ordering: expired shots spawn particles before their first draw/update. */
    for (int i = 0; i < STRIKE_B1_PARTICLES; ++i)
        if (fx->particles[i].active) n += strike_b1_draw_particle(c, &fx->particles[i]);
    strike_b1_update_particles(fx, dt);
    return n;
}

static int bag2jp_strike_bag1_tick(uint32_t frame) {
    if (psx_mod_read_word(B2_ROOT_ADDR) != 19u || psx_mod_read_word(B2_MODE_ADDR) != 2u ||
        psx_mod_read_word(B2_PHASE1_ADDR) != 1u || psx_mod_read_word(B2_PHASE2_ADDR) != 3u ||
        psx_mod_read_word(B2_PHASE3_ADDR) != 3u) { strike_b1_reset(); return 0; }
    uint32_t ot = psx_mod_read_word(B2_OT_ADDR), heap = psx_mod_read_word(B2_HEAP_ADDR);
    if (!heat_valid_ptr(ot) || !heat_valid_ptr(heap) || ot == s_strike_b1_last_ot) return 0;
    s_strike_b1_last_ot = ot;
    HeatDrawCtx c = {0};
    c.ot = ot; c.heap = heap;
    c.h = (int32_t)psx_mod_read_word(B2_GEOM_H_ADDR);
    if (c.h <= 0 || c.h > 4096) return 0;
    int16_t cr[9], sr[9];
    int32_t ct[3], st[3];
    strike_read_matrix(B2_CAM_ROT_ADDR, cr, ct);
    uint32_t stage = psx_mod_read_word(STRIKE_B1_STAGE_PTR);
    /* Special mode B has a separate world transform; leave it unresolved rather than guess. */
    if (!heat_valid_ptr(stage) || psx_mod_read_byte(stage) == 0xBu) return 0;
    strike_read_matrix(stage + STRIKE_B1_STAGE_MATRIX, sr, st);
    int dt = (int)psx_mod_read_word(B2_DT_ADDR);
    if (psx_mod_read_word(B2_PAUSE_ADDR) || dt < 0 || dt >= 8) dt = 0;
    int emitted = 0;
    for (uint32_t side = 0; side < 2; ++side) {
        uint32_t chr = psx_mod_read_word(side ? B2_CHAR_P2_ADDR : B2_CHAR_P1_ADDR);
        uint32_t dancer = psx_mod_read_word(B2_DANCER_BASE + side * 8u);
        uint32_t opponent = psx_mod_read_word(B2_DANCER_BASE + (side ^ 1u) * 8u);
        /* Main-exe FUN_80031DAC: descriptor table [side * 19 + character]. */
        uint32_t desc = psx_mod_read_word(B2_TEXDESC_BASE + side * B2_TEXDESC_STRIDE + STRIKE_CHAR_ID * 4u);
        if (chr != STRIKE_CHAR_ID || !bag2jp_bag1_get_version(STRIKE_CHAR_ID, side) ||
            !heat_valid_ptr(dancer) || !heat_valid_ptr(opponent) || !heat_valid_ptr(desc)) {
            memset(&s_strike_b1_fx[side], 0, sizeof(s_strike_b1_fx[side]));
            s_strike_b1_previous[side] = 0;
            continue;
        }
        if (dt) strike_b1_spawn_events(side, dancer, opponent, frame);
        c.tpage = (uint16_t)((psx_mod_read_half(desc + 0x46u) & 0xFF9Fu) | 0x20u);
        c.clut = psx_mod_read_half(desc + 0x44u);
        HeatDrawCtx actor = {0};
        heat_compose_frame(&actor, HEAT_FRAME_ATTACKER, cr, ct, dancer);
        strike_comp_matrix(actor.rot[0], actor.trans[0], sr, st, c.rot[0], c.trans[0]);
        heat_compose_frame(&c, HEAT_FRAME_TARGET, cr, ct, opponent);
        HeatVec3 anchor = heat_dancer_floor(opponent);
        c.anchor[HEAT_FRAME_TARGET] = anchor;
        emitted += strike_b1_draw_side(&c, &s_strike_b1_fx[side], dt);
    }
    psx_mod_write_word(B2_HEAP_ADDR, c.heap);
    return emitted;
}

#endif
