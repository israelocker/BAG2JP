/* Heat BAG1 attack effect: port of the native BAG1 Heat DBI flame (FUN_801daa10 spawn,
 * FUN_801dad98 flame, FUN_801db64c/6b0 ground ring, FUN_801dbc34/dbd28 particles).
 * The BAG2 Heat DBI renderer is nopped in the BAG1 payload (patch_heat_dbi.py patch 4);
 * its hit/guard logic and cues still run. Uses the BAG1 Heat textures already resident in
 * the side's DBI texture page (descriptor *(0x80053544 + side*0x4c)).
 * Requires bag2jp_strike_shot.h (shared addresses, matrix and projection helpers). */
#ifndef BAG2JP_HEAT_FLAME_H
#define BAG2JP_HEAT_FLAME_H

#include <stdint.h>
#include <string.h>

#define B2_PAUSE_ADDR        0x8005D3E4u
#define B2_DT_ADDR           0x8006D994u
#define B2_TEXDESC_BASE      0x80053544u
#define B2_TEXDESC_STRIDE    0x4Cu
#define B2_MOTION_BASE       0x8005F820u /* dancer motion player (FUN_8002b5bc(0x8005f820, dancer)) */
#define B2_MOTION_STRIDE     0x98u
#define B2_MOTION_LEFT_OFF   0x20u       /* remaining motion ticks, decremented by dt */

#define HEAT_CHAR_ID         0u
#define HEAT_ATTACK_ANIM     74u
#define HEAT_ATTACK_FRAMES   51   /* BAG1 anim 63 length; type-16 event fires at frame 1 */
#define HEAT_TARGET_RADIUS   16   /* BAG1 (0x800558FC[char] = ~0x80) / 8, opponent +0x43BC */

#define HEAT_FLAME_COUNT     3
#define HEAT_RING_COUNT      3
#define HEAT_PARTICLE_COUNT  0x48
#define HEAT_BURST_PARTICLES 24

/* BAG1 effect space -> BAG2 dancer-local space, Q12. Measured 2026-11-05 (heat-flame-diag log):
 * BAG2 local +1000 y projects to 131 px at otz ~725 and the dancer is ~880 local units tall, while
 * native BAG1 particles (peak ~1150 units) reach ~0.6 body, so a BAG1 body is ~1900 units.
 * Offsets scale by 880/1900 around the spawn floor points. Sprite sizes are fitted to the native
 * clip (heat-native-attack-final.mp4: body flame ~1.1 x body tall, ~1.3 x body wide), not derived. */
#define HEAT_POS_SCALE_Q12   1897 /* 0.463 */
#define HEAT_SIZE_W_Q12      2048 /* widths: native body flame ~1.3-1.5 x body width */
#define HEAT_SIZE_H_Q12      2540 /* particle heights: native floor flames ~0.5 x body height */
#define HEAT_FLAME_H_Q12     1800 /* slot flame heights: native body flame ~1.1-1.3 x body height */

typedef struct {
    int32_t x, y, z;
} HeatVec3;

typedef struct {
    int active, state, life, timer;
    int32_t bright, w, h, w_t, h_t, div;
    int frame, low_uv, flip;
    HeatVec3 pos, target;
    int32_t radius;
} HeatFlame;

typedef struct {
    int active;
    int32_t radius, alpha, t, y_off, speed, vh, outer;
    int32_t cx, cy, cz;
} HeatRing;

typedef struct {
    int active, state, frame, hflip;
    int32_t color, vh, size;
    HeatVec3 pos, vel; /* 20.12 fixed point */
} HeatParticle;

typedef struct {
    HeatFlame flames[HEAT_FLAME_COUNT];
    HeatRing rings[HEAT_RING_COUNT];
    HeatParticle particles[HEAT_PARTICLE_COUNT];
    uint32_t seed;
    HeatVec3 anchor[2]; /* spawn floor points of attacker and target */
} HeatFxState;

/* Frame UVs, table 0x801DCA18 in the BAG1 Heat DBI (14 frames, 0x20 x 0x72 cells).
 * BAG2 uploads its "HEAT" name label over u 0x37..0x7A, v 0xA5..0xB0 of this page (VRAM dump
 * of run 20261105T141829785610Z), so frames 9-11 reuse the matching upper-row cells. */
static const uint8_t heat_flame_uv[14][2] = {
    {0x00, 0x00}, {0x20, 0x00}, {0x40, 0x00}, {0x60, 0x00}, {0x80, 0x00}, {0xA0, 0x00}, {0xC0, 0x00},
    {0xE0, 0x00}, {0x00, 0x78}, {0x20, 0x00}, {0x40, 0x00}, {0x60, 0x00}, {0x80, 0x78}, {0xA0, 0x78}
};

/* rsin/rcos at (i+1)*0x200 for the 8 ring points. */
static const int16_t heat_ring_sin[8] = {2896, 4096, 2896, 0, -2896, -4096, -2896, 0};
static const int16_t heat_ring_cos[8] = {2896, 0, -2896, -4096, -2896, 0, 2896, 4096};

static inline int32_t heat_rand(HeatFxState* fx) {
    fx->seed = fx->seed * 1103515245u + 12345u;
    return (int32_t)((fx->seed >> 16) & 0x7FFFu);
}

/* BAG1 helper: rand() % (2n) - n, or 0 when rand() returned 0. */
static inline int32_t heat_rand_signed(HeatFxState* fx, int32_t n) {
    int32_t r = heat_rand(fx);
    return r ? r % (n * 2) - n : 0;
}

static inline void heat_fx_spawn(HeatFxState* fx, const HeatVec3* start, const HeatVec3* target,
                                 int32_t radius, int life) {
    for (int i = 0; i < HEAT_FLAME_COUNT; ++i) {
        HeatFlame* f = &fx->flames[i];
        if (f->active) continue;
        memset(f, 0, sizeof(*f));
        f->active = 1;
        f->life = life;
        f->timer = life / 4;
        f->bright = 0x80000;
        f->w = 1;
        f->h = 1;
        f->w_t = 500;
        f->h_t = 600;
        f->div = 0xF;
        f->pos = *start;
        f->target = *target;
        f->radius = radius;
        return;
    }
}

static inline void heat_ring_spawn(HeatFxState* fx, int32_t radius, const HeatVec3* at) {
    for (int i = 0; i < HEAT_RING_COUNT; ++i) {
        HeatRing* r = &fx->rings[i];
        if (r->active) continue;
        r->active = 1;
        r->radius = radius;
        r->alpha = 0x80;
        r->t = 0;
        r->y_off = 0;
        r->speed = radius * 2;
        r->vh = 0x1F;
        r->outer = radius * 4 + 100;
        r->cx = at->x;
        r->cy = at->y;
        r->cz = at->z;
        return;
    }
}

static inline void heat_particles_spawn(HeatFxState* fx, const HeatVec3* at) {
    int spawned = 0;
    for (int i = 0; i < HEAT_PARTICLE_COUNT && spawned < HEAT_BURST_PARTICLES; ++i) {
        HeatParticle* p = &fx->particles[i];
        if (p->active) continue;
        p->active = 1;
        p->state = 0;
        p->frame = 0;
        p->color = 0x80;
        p->vh = 0x72;
        p->size = 0x78;
        p->hflip = heat_rand(fx) & 1;
        p->pos.x = (at->x + heat_rand_signed(fx, 0x200)) << 12;
        p->pos.y = at->y + 100; /* BAG1 stores this unshifted */
        p->pos.z = (at->z + heat_rand_signed(fx, 0x200)) << 12;
        p->vel.x = heat_rand_signed(fx, 0x1000) * 0x18;
        p->vel.y = (heat_rand(fx) % 0x1000) * 0x30;
        p->vel.z = heat_rand_signed(fx, 0x1000) * 0x18;
        for (int k = 0; k < 2; ++k) {
            p->pos.x += p->vel.x;
            p->pos.y += p->vel.y;
            p->pos.z += p->vel.z;
        }
        ++spawned;
    }
}

static inline void heat_flame_update(HeatFxState* fx, HeatFlame* f, int dt) {
    for (int i = 0; i < dt; ++i) {
        if (++f->frame > 0xD) f->frame = 0;
        f->w += (f->w_t - f->w) / f->div;
        f->h += (f->h_t - f->h) / f->div;
    }
    int life4 = f->life / 4 > 0 ? f->life / 4 : 1;
    int life6 = f->life / 6 > 0 ? f->life / 6 : 1;
    int life16 = f->life / 16 > 0 ? f->life / 16 : 1;
    switch (f->state) {
    case 0:
        f->bright += 0x80000 / life4;
        if (f->bright > 0x80000) f->bright = 0x80000;
        f->timer -= dt;
        if (f->timer < 1) {
            f->bright = 0x80000;
            f->timer = f->life / 4 + f->life / 8;
            f->state = 1;
        }
        break;
    case 1:
        f->timer -= dt;
        if (f->timer <= 0) {
            f->timer = f->life / 16;
            f->state = 2;
        }
        break;
    case 2:
        f->bright -= 0x80000 / life16;
        if (f->bright < 0x1000) f->bright = 0;
        f->timer -= dt;
        if (f->timer < 1) {
            f->bright = 0x80000;
            f->timer = f->life / 8;
            f->flip = 1;
            f->w = 1500;
            f->h = 100;
            f->w_t = 300;
            f->h_t = 700;
            f->div = 3;
            f->pos.y += 1000;
            f->state = 3;
        }
        break;
    case 3:
        f->bright += 0x10000;
        if (f->bright > 0xFF000) f->bright = 0xFF000;
        f->timer -= dt;
        f->pos.y += dt * 300;
        if (f->timer < 1) {
            f->w = f->w_t = 300;
            f->h = f->h_t = 900;
            f->flip = 0;
            f->pos = f->target;
            f->pos.y = f->target.y + (f->life / 8) * 400;
            f->state = 4;
        }
        break;
    case 4:
        f->pos.y -= dt * 200;
        if (f->pos.y <= f->target.y) {
            heat_ring_spawn(fx, f->radius, &f->target);
            heat_particles_spawn(fx, &f->target);
            f->w = 1000;
            f->w_t = 400;
            f->h_t = 100;
            f->div = 0xF;
            f->low_uv = 1;
            f->pos.y = f->target.y;
            f->state = 5;
        }
        break;
    case 5:
        f->bright -= 0x100000 / life6;
        if ((f->bright >> 12) <= 0) f->state = 6;
        break;
    default:
        f->active = 0;
        break;
    }
}

static inline void heat_ring_update(HeatRing* r, int dt) {
    int32_t dec = (r->radius >> 3) * dt;
    r->t += dt;
    r->speed -= dec;
    if (r->speed < 0) r->speed = 0;
    r->y_off += (r->speed + dec / 2) * dt;
    r->outer += 100 + r->radius * dt;
    if (r->t > 5) {
        r->alpha -= 16 * dt;
        if (r->alpha < 0) r->alpha = 0;
        r->vh += 4 * dt;
        if (r->vh > 0x3F) r->vh = 0x3F;
    }
    if (r->alpha < 1) r->active = 0;
}

static inline void heat_particle_update(HeatParticle* p, int dt) {
    for (int i = 0; i < dt && p->active; ++i) {
        if (++p->frame > 0xD) p->frame = 0;
        switch (p->state) {
        case 0:
            p->vel.y -= 0x1000;
            p->pos.x += p->vel.x;
            p->pos.y += p->vel.y;
            p->pos.z += p->vel.z;
            if (p->pos.y < 0) {
                p->pos.y = 0;
                p->vel.y = 0;
                p->state = 1;
            }
            break;
        case 1:
            p->vh -= 4;
            if (p->vh < 0x40) {
                p->vh = 0x3F;
                p->state = 2;
            }
            break;
        case 2:
            p->color -= 0x10;
            if (p->color < 0) {
                p->color = 0;
                p->state = 3;
            }
            break;
        default:
            p->active = 0;
            break;
        }
    }
}

static inline void heat_fx_update(HeatFxState* fx, int dt) {
    if (dt <= 0) return;
    for (int i = 0; i < HEAT_FLAME_COUNT; ++i)
        if (fx->flames[i].active) heat_flame_update(fx, &fx->flames[i], dt);
    for (int i = 0; i < HEAT_RING_COUNT; ++i)
        if (fx->rings[i].active) heat_ring_update(&fx->rings[i], dt);
    for (int i = 0; i < HEAT_PARTICLE_COUNT; ++i)
        if (fx->particles[i].active) heat_particle_update(&fx->particles[i], dt);
}

static inline int heat_fx_any_active(const HeatFxState* fx) {
    for (int i = 0; i < HEAT_FLAME_COUNT; ++i) if (fx->flames[i].active) return 1;
    for (int i = 0; i < HEAT_RING_COUNT; ++i) if (fx->rings[i].active) return 1;
    for (int i = 0; i < HEAT_PARTICLE_COUNT; ++i) if (fx->particles[i].active) return 1;
    return 0;
}

/* ---- Runtime rendering ---- */

/* Frames as in the BAG2 Heat DBI renderer FUN_801ce628: camera composed with the attacker's
 * (+0x14C4) matrix for attacker-side effects, with the opponent's for target-side effects. */
#define HEAT_FRAME_ATTACKER 0
#define HEAT_FRAME_TARGET   1

typedef struct {
    int16_t rot[2][9];
    int32_t trans[2][3];
    int32_t h;
    uint32_t heap, ot;
    uint16_t tpage, clut;
    uint8_t u_base, v_base;
    HeatVec3 anchor[2];
} HeatDrawCtx;

typedef struct {
    int16_t x[4], y[4];
    uint8_t u[4], v[4];
    uint8_t gray;
    uint16_t clut;
    int32_t ot_index;
} HeatQuad;

static inline int heat_project(const HeatDrawCtx* c, int frame, const HeatVec3* w, StrikeScreenPt* s) {
    const HeatVec3* a = &c->anchor[frame];
    StrikeVec3 p = {a->x + (int32_t)(((int64_t)(w->x - a->x) * HEAT_POS_SCALE_Q12) >> 12),
                    a->y + (int32_t)(((int64_t)(w->y - a->y) * HEAT_POS_SCALE_Q12) >> 12),
                    a->z + (int32_t)(((int64_t)(w->z - a->z) * HEAT_POS_SCALE_Q12) >> 12)};
    return strike_project(&p, c->rot[frame], c->trans[frame], c->h, s);
}

static inline int heat_emit_ft4(HeatDrawCtx* c, const HeatQuad* q) {
    if (q->ot_index < 0 || q->ot_index >= 0x1000) return 0;
    if (c->heap + 40u >= 0x807E0000u) return 0;
    uint32_t ot_entry = c->ot + (uint32_t)q->ot_index * 4u;
    uint32_t head = psx_mod_read_word(ot_entry);
    uint32_t a = c->heap;
    uint32_t g = q->gray;
    psx_mod_write_word(a + 0x00u, (9u << 24) | (head & 0x00FFFFFFu));
    psx_mod_write_word(a + 0x04u, 0x2E000000u | (g << 16) | (g << 8) | g);
    for (int i = 0; i < 4; ++i) {
        uint32_t extra = i == 0 ? (uint32_t)q->clut << 16 : i == 1 ? (uint32_t)c->tpage << 16 : 0u;
        psx_mod_write_word(a + 0x08u + (uint32_t)i * 8u,
                           ((uint32_t)(uint16_t)q->y[i] << 16) | (uint16_t)q->x[i]);
        psx_mod_write_word(a + 0x0Cu + (uint32_t)i * 8u,
                           extra | ((uint32_t)q->v[i] << 8) | q->u[i]);
    }
    psx_mod_write_word(ot_entry, (head & 0xFF000000u) | (a & 0x00FFFFFFu));
    c->heap = a + 40u;
    return 1;
}

static inline int heat_draw_flame(HeatDrawCtx* c, const HeatFlame* f) {
    StrikeScreenPt s;
    /* State 4 moves the flame onto the target; earlier states stay on the attacker. */
    if (!heat_project(c, f->state >= 4 ? HEAT_FRAME_TARGET : HEAT_FRAME_ATTACKER, &f->pos, &s)) return 0;
    int32_t otz = s.z >> 2;
    if ((uint32_t)(otz - 0x60) >= 0x1000u) return 0;
    HeatQuad q;
    int32_t g = f->bright >> 12;
    q.gray = (uint8_t)(g > 0xFF ? 0xFF : g < 0 ? 0 : g);
    q.clut = c->clut;
    uint8_t u = heat_flame_uv[f->frame][0], v = heat_flame_uv[f->frame][1];
    uint8_t vh = f->low_uv ? 0x3F : 0x72;
    int16_t hw = (int16_t)(((((f->w << 10) / 5) / otz) * HEAT_SIZE_W_Q12) >> 12);
    int16_t hh = (int16_t)((((f->h * 0x1CC) / otz) * HEAT_FLAME_H_Q12) >> 12);
    int16_t top = f->flip ? s.y : (int16_t)(s.y - hh);
    int16_t bot = f->flip ? (int16_t)(s.y + hh) : s.y;
    for (int i = 0; i < 4; ++i) {
        q.x[i] = (int16_t)((i & 1) ? s.x + hw : s.x - hw);
        q.y[i] = i < 2 ? top : bot;
        q.u[i] = (uint8_t)((i & 1) ? u + 0x1F : u);
        q.v[i] = (uint8_t)((i < 2) != (f->flip != 0) ? v : v + vh);
    }
    q.ot_index = otz - 0x60;
    return heat_emit_ft4(c, &q);
}

static inline int heat_draw_ring(HeatDrawCtx* c, const HeatRing* r) {
    StrikeScreenPt inner[8], outer[8];
    int ok_in[8], ok_out[8];
    int32_t r_in = r->radius * 4 + 200;
    for (int i = 0; i < 8; ++i) {
        HeatVec3 pi = {r->cx + ((heat_ring_sin[i] * r_in) >> 12), r->cy,
                       r->cz + ((heat_ring_cos[i] * r_in) >> 12)};
        HeatVec3 po = {r->cx + ((heat_ring_sin[i] * r->outer) >> 12), r->cy + r->y_off,
                       r->cz + ((heat_ring_cos[i] * r->outer) >> 12)};
        ok_in[i] = heat_project(c, HEAT_FRAME_TARGET, &pi, &inner[i]);
        ok_out[i] = heat_project(c, HEAT_FRAME_TARGET, &po, &outer[i]);
    }
    int emitted = 0;
    for (int qi = 0; qi < 8; ++qi) {
        int qn = (qi + 1) & 7;
        if (!ok_in[qi] || !ok_in[qn] || !ok_out[qi] || !ok_out[qn]) continue;
        const StrikeScreenPt* pts[4] = {&outer[qi], &outer[qn], &inner[qi], &inner[qn]};
        int32_t otz = (pts[0]->z + pts[1]->z + pts[2]->z + pts[3]->z) >> 4;
        if ((uint32_t)(otz - 0x60) >= 0x1000u) continue;
        HeatQuad q;
        q.gray = (uint8_t)r->alpha;
        q.clut = (uint16_t)(c->clut + 0x40u);
        for (int i = 0; i < 4; ++i) {
            q.x[i] = pts[i]->x;
            q.y[i] = pts[i]->y;
            q.u[i] = (uint8_t)(c->u_base + ((i & 1) ? -0x29 : -0x40));
            q.v[i] = (uint8_t)(c->v_base + 0x78 + (i < 2 ? 0 : r->vh));
        }
        q.ot_index = otz - 0x60 - 500; /* BAG1: OT + (otz-0x60)*4 - 2000 */
        if (q.ot_index < 0) q.ot_index = 0;
        emitted += heat_emit_ft4(c, &q);
    }
    return emitted;
}

static inline int heat_draw_particle(HeatDrawCtx* c, const HeatParticle* p) {
    HeatVec3 w = {p->pos.x >> 12, p->pos.y >> 12, p->pos.z >> 12};
    StrikeScreenPt s;
    if (!heat_project(c, HEAT_FRAME_TARGET, &w, &s)) return 0;
    int32_t otz = s.z >> 2;
    if ((uint32_t)(otz - 0x60) >= 0x1000u) return 0;
    int16_t hw = (int16_t)((((((((p->size << 10) / 5) / otz) * 3) >> 2)) * HEAT_SIZE_W_Q12) >> 12);
    if (p->hflip) hw = (int16_t)-hw;
    int16_t hh = (int16_t)((((p->vh * p->size * 4) / otz) * HEAT_SIZE_H_Q12) >> 12);
    HeatQuad q;
    q.gray = (uint8_t)p->color;
    q.clut = c->clut;
    uint8_t u = heat_flame_uv[p->frame][0], v = heat_flame_uv[p->frame][1];
    for (int i = 0; i < 4; ++i) {
        q.x[i] = (int16_t)((i & 1) ? s.x + hw : s.x - hw);
        q.y[i] = i < 2 ? (int16_t)(s.y - hh) : s.y;
        q.u[i] = (uint8_t)((i & 1) ? u + 0x1F : u);
        q.v[i] = (uint8_t)(i < 2 ? v : v + p->vh);
    }
    q.ot_index = otz - 0x60;
    return heat_emit_ft4(c, &q);
}

static inline int heat_fx_draw(HeatDrawCtx* c, const HeatFxState* fx) {
    int n = 0;
    for (int i = 0; i < HEAT_FLAME_COUNT; ++i) if (fx->flames[i].active) n += heat_draw_flame(c, &fx->flames[i]);
    for (int i = 0; i < HEAT_RING_COUNT; ++i) if (fx->rings[i].active) n += heat_draw_ring(c, &fx->rings[i]);
    for (int i = 0; i < HEAT_PARTICLE_COUNT; ++i)
        if (fx->particles[i].active) n += heat_draw_particle(c, &fx->particles[i]);
    return n;
}

/* ---- Runtime state ---- */

static HeatFxState s_heat_fx[2];
static int s_heat_attack_seen[2];
static uint32_t s_heat_last_ot;

static void bag2jp_heat_flame_reset(void) {
    memset(s_heat_fx, 0, sizeof(s_heat_fx));
    memset(s_heat_attack_seen, 0, sizeof(s_heat_attack_seen));
    s_heat_last_ot = 0;
}

static inline int heat_valid_ptr(uint32_t p) {
    return p >= 0x80010000u && p < 0x807E0000u;
}

/* Floor point under the dancer in its own frame, as the BAG2 Heat DBI uses it:
 * x = +0x810, y = 0, z = +0x818. */
static inline HeatVec3 heat_dancer_floor(uint32_t dancer) {
    HeatVec3 v = {(int16_t)psx_mod_read_word(dancer + B2_DANCER_ROOT_OFF), 0,
                  (int16_t)psx_mod_read_word(dancer + B2_DANCER_ROOT_OFF + 8u)};
    return v;
}

static inline void heat_compose_frame(HeatDrawCtx* c, int frame, const int16_t* cam_rot, const int32_t* cam_t,
                                      uint32_t dancer) {
    int16_t d_rot[9];
    int32_t d_t[3];
    strike_read_matrix(dancer + B2_DANCER_MTX_OFF, d_rot, d_t);
    strike_comp_matrix(cam_rot, cam_t, d_rot, d_t, c->rot[frame], c->trans[frame]);
}

static int bag2jp_heat_flame_tick(uint32_t frame) {
    if (psx_mod_read_word(B2_ROOT_ADDR) != 19u || psx_mod_read_word(B2_MODE_ADDR) != 2u ||
        psx_mod_read_word(B2_PHASE1_ADDR) != 1u || psx_mod_read_word(B2_PHASE2_ADDR) != 3u ||
        psx_mod_read_word(B2_PHASE3_ADDR) != 3u) {
        if (s_heat_last_ot) bag2jp_heat_flame_reset();
        return 0;
    }

    uint32_t dancers[2];
    for (uint32_t side = 0; side < 2; ++side) dancers[side] = psx_mod_read_word(B2_DANCER_BASE + side * 8u);

    /* Spawn on the imported attack (BAG1 anim 63 type-16 event at frame 1, life = remaining frames). */
    for (uint32_t side = 0; side < 2; ++side) {
        uint32_t chr = psx_mod_read_word(side == 0 ? B2_CHAR_P1_ADDR : B2_CHAR_P2_ADDR);
        uint32_t dancer = dancers[side], opp = dancers[side ^ 1u];
        if (chr != HEAT_CHAR_ID || !bag2jp_bag1_get_version((int)HEAT_CHAR_ID, (int)side) ||
            !heat_valid_ptr(dancer) || !heat_valid_ptr(opp)) {
            s_heat_attack_seen[side] = 0;
            continue;
        }
        uint32_t anim = psx_mod_read_word(dancer + 0x154Cu);
        uint32_t anim_frame = psx_mod_read_word(dancer + 0x1554u);
        if (anim != HEAT_ATTACK_ANIM) {
            s_heat_attack_seen[side] = 0;
            continue;
        }
        if (s_heat_attack_seen[side] || anim_frame < 1u || anim_frame >= (uint32_t)HEAT_ATTACK_FRAMES) continue;
        s_heat_attack_seen[side] = 1;
        HeatVec3 start = heat_dancer_floor(dancer);
        HeatVec3 target = heat_dancer_floor(opp);
        if (!s_heat_fx[side].seed) s_heat_fx[side].seed = 0x1D872B41u ^ frame;
        s_heat_fx[side].anchor[HEAT_FRAME_ATTACKER] = start;
        s_heat_fx[side].anchor[HEAT_FRAME_TARGET] = target;
        /* BAG1 passes the motion's remaining ticks (FUN_800318d0 param_1[7]); BAG2 keeps the same
         * counter at motion+0x20 (FUN_8002d06c param_1[8]). Fall back to two ticks per frame. */
        int32_t life = (int32_t)psx_mod_read_word(B2_MOTION_BASE + side * B2_MOTION_STRIDE + B2_MOTION_LEFT_OFF);
        if (life < 1 || life > 600) life = (HEAT_ATTACK_FRAMES - (int)anim_frame) * 2;
        heat_fx_spawn(&s_heat_fx[side], &start, &target, HEAT_TARGET_RADIUS, life);
        b1v_log("heat_flame f%u side %u spawn start(%d,%d,%d) target(%d,%d,%d) life %d", frame, side,
                start.x, start.y, start.z, target.x, target.y, target.z, life);
        {
            /* Diagnostic: BAG2 effect scale (stage descriptor +4, dancer +0x14F4) and local-unit projection. */
            uint32_t stage = psx_mod_read_word(0x80089200u);
            int16_t cam_rot[9];
            int32_t cam_t[3];
            HeatDrawCtx dc;
            strike_read_matrix(B2_CAM_ROT_ADDR, cam_rot, cam_t);
            dc.h = (int32_t)psx_mod_read_word(B2_GEOM_H_ADDR);
            heat_compose_frame(&dc, HEAT_FRAME_ATTACKER, cam_rot, cam_t, dancer);
            HeatVec3 up = {start.x, start.y + 1000, start.z}, side_pt = {start.x + 1000, start.y, start.z};
            StrikeScreenPt s0 = {0, 0, 0}, s1 = {0, 0, 0}, s2 = {0, 0, 0};
            int ok0 = heat_project(&dc, HEAT_FRAME_ATTACKER, &start, &s0);
            int ok1 = heat_project(&dc, HEAT_FRAME_ATTACKER, &up, &s1);
            int ok2 = heat_project(&dc, HEAT_FRAME_ATTACKER, &side_pt, &s2);
            b1v_log("heat_flame diag stage %08x mode %u scale %d d14f4 %d h %d rot(%d,%d,%d|%d,%d,%d|%d,%d,%d)"
                    " t(%d,%d,%d) root(%d,%d,z%d,%d) up1000(%d,%d,z%d,%d) x1000(%d,%d,z%d,%d)",
                    stage, heat_valid_ptr(stage) ? psx_mod_read_byte(stage) : 0u,
                    heat_valid_ptr(stage) ? (int)(int16_t)psx_mod_read_half(stage + 4u) : 0,
                    (int)psx_mod_read_word(dancer + 0x14F4u), dc.h,
                    dc.rot[0][0], dc.rot[0][1], dc.rot[0][2], dc.rot[0][3], dc.rot[0][4], dc.rot[0][5],
                    dc.rot[0][6], dc.rot[0][7], dc.rot[0][8], dc.trans[0][0], dc.trans[0][1], dc.trans[0][2],
                    s0.x, s0.y, s0.z, ok0, s1.x, s1.y, s1.z, ok1, s2.x, s2.y, s2.z, ok2);
        }
    }

    if (!heat_fx_any_active(&s_heat_fx[0]) && !heat_fx_any_active(&s_heat_fx[1])) return 0;

    /* Draw and step once per game frame (one OT buffer). */
    uint32_t ot = psx_mod_read_word(B2_OT_ADDR);
    uint32_t heap = psx_mod_read_word(B2_HEAP_ADDR);
    if (!heat_valid_ptr(ot) || !heat_valid_ptr(heap) || ot == s_heat_last_ot) return 0;
    s_heat_last_ot = ot;

    HeatDrawCtx c;
    int16_t cam_rot[9];
    int32_t cam_t[3];
    strike_read_matrix(B2_CAM_ROT_ADDR, cam_rot, cam_t);
    c.h = (int32_t)psx_mod_read_word(B2_GEOM_H_ADDR);
    c.heap = heap;
    c.ot = ot;
    int paused = psx_mod_read_word(B2_PAUSE_ADDR) != 0u;
    int dt = (int)psx_mod_read_word(B2_DT_ADDR);
    int emitted = 0;
    for (uint32_t side = 0; side < 2; ++side) {
        HeatFxState* fx = &s_heat_fx[side];
        if (!heat_fx_any_active(fx)) continue;
        uint32_t desc = psx_mod_read_word(B2_TEXDESC_BASE + side * B2_TEXDESC_STRIDE);
        uint32_t dancer = dancers[side], opp = dancers[side ^ 1u];
        if (heat_valid_ptr(desc) && heat_valid_ptr(dancer) && heat_valid_ptr(opp) && c.h > 0 && c.h <= 4096) {
            heat_compose_frame(&c, HEAT_FRAME_ATTACKER, cam_rot, cam_t, dancer);
            heat_compose_frame(&c, HEAT_FRAME_TARGET, cam_rot, cam_t, opp);
            c.tpage = (uint16_t)((psx_mod_read_half(desc + 0x46u) & 0xFF9Fu) | 0x20u);
            c.clut = psx_mod_read_half(desc + 0x44u);
            c.u_base = psx_mod_read_byte(desc + 0x3Eu);
            c.v_base = psx_mod_read_byte(desc + 0x3Fu);
            c.anchor[0] = fx->anchor[0];
            c.anchor[1] = fx->anchor[1];
            emitted += heat_fx_draw(&c, fx);
        }
        if (!paused && dt > 0 && dt < 8) heat_fx_update(fx, dt);
        {
            /* Diagnostic: flame state timing against the attacker's animation frame. */
            static int s_heat_logged_state[2] = {-1, -1};
            int st = fx->flames[0].active ? fx->flames[0].state : -1;
            if (st != s_heat_logged_state[side]) {
                s_heat_logged_state[side] = st;
                b1v_log("heat_flame f%u side %u state %d dt %d anim %u frame %u tpage %04x clut %04x uv %02x,%02x",
                        frame, side, st, dt,
                        heat_valid_ptr(dancer) ? psx_mod_read_word(dancer + 0x154Cu) : 0u,
                        heat_valid_ptr(dancer) ? psx_mod_read_word(dancer + 0x1554u) : 0u,
                        c.tpage, c.clut, c.u_base, c.v_base);
            }
        }
    }
    psx_mod_write_word(B2_HEAP_ADDR, c.heap);
    return emitted;
}

#endif
