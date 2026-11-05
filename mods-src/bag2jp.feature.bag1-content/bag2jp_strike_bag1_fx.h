/* BAG1 Strike visual simulation: FUN_801da81c / FUN_801dab28.
 * No gameplay, sound or VRAM writes. Runtime rendering is integrated separately. */
#ifndef BAG2JP_STRIKE_BAG1_FX_H
#define BAG2JP_STRIKE_BAG1_FX_H

#include <stdint.h>

#define STRIKE_B1_SHOTS 20
#define STRIKE_B1_PARTICLES 40
#define STRIKE_B1_LIFE 20
#define STRIKE_B1_FIXED 4096
#define STRIKE_B1_PARTICLE_SIZE 320
#define STRIKE_B1_EVENT_COUNT 5

typedef struct { int32_t x, y, z; } StrikeB1Vec;
typedef struct {
    int state, count, life, impact;
    StrikeB1Vec a, b, target;
} StrikeB1Shot;
typedef struct {
    int active, frame, size;
    StrikeB1Vec pos, vel;
} StrikeB1Particle;
typedef struct {
    StrikeB1Shot shots[STRIKE_B1_SHOTS];
    StrikeB1Particle particles[STRIKE_B1_PARTICLES];
    unsigned next_shot;
    uint32_t seed;
} StrikeB1Fx;

/* Local RNG deliberately avoids changing the game's random stream. */
static inline uint32_t strike_b1_random(StrikeB1Fx* fx) {
    fx->seed = fx->seed * 1664525u + 1013904223u;
    return fx->seed >> 1;
}

static inline int32_t strike_b1_signed_random(StrikeB1Fx* fx, uint32_t radius) {
    uint32_t value = strike_b1_random(fx);
    return value ? (int32_t)(value % (radius * 2u)) - (int32_t)radius : 0;
}

static inline unsigned strike_b1_crossings(unsigned previous, unsigned current) {
    static const unsigned events[STRIKE_B1_EVENT_COUNT] = {26, 31, 36, 41, 46};
    unsigned mask = 0;
    for (unsigned i = 0; i < STRIKE_B1_EVENT_COUNT; ++i)
        if (previous < events[i] && current >= events[i]) mask |= 1u << i;
    return mask;
}

static inline void strike_b1_spawn(StrikeB1Fx* fx, const StrikeB1Vec* a, const StrikeB1Vec* b,
                                    const StrikeB1Vec* target, int impact) {
    StrikeB1Shot* shot = &fx->shots[fx->next_shot];
    fx->next_shot = (fx->next_shot + 1u) % STRIKE_B1_SHOTS;
    *shot = (StrikeB1Shot){1, 0, STRIKE_B1_LIFE, impact, *a, *b, *target};
}

static inline void strike_b1_spawn_particle(StrikeB1Fx* fx, const StrikeB1Vec* target, int spark) {
    StrikeB1Particle* p = 0;
    for (int i = 0; i < STRIKE_B1_PARTICLES; ++i)
        if (!fx->particles[i].active) { p = &fx->particles[i]; break; }
    if (!p) return;
    p->active = 1;
    p->frame = 0;
    p->size = STRIKE_B1_PARTICLE_SIZE;
    uint32_t radius = spark ? 0x100u : 0x200u;
    p->pos.x = (target->x + strike_b1_signed_random(fx, radius)) * STRIKE_B1_FIXED;
    /* BAG1 dust starts at raw y=100, not 100<<12; do not normalize this quirk. */
    p->pos.y = spark ? (target->y + strike_b1_signed_random(fx, radius)) * STRIKE_B1_FIXED : 100;
    p->pos.z = (target->z + strike_b1_signed_random(fx, radius)) * STRIKE_B1_FIXED;
    p->vel.x = strike_b1_signed_random(fx, 0x1000u) * (spark ? 128 : 32);
    p->vel.y = spark ? strike_b1_signed_random(fx, 0x1000u) * 32 :
                      (int32_t)(strike_b1_random(fx) % 0x1000u) * 128;
    p->vel.z = strike_b1_signed_random(fx, 0x1000u) * (spark ? 128 : 32);
}

static inline void strike_b1_update_shots(StrikeB1Fx* fx, int dt) {
    if (dt <= 0) return;
    for (int i = 0; i < STRIKE_B1_SHOTS; ++i) {
        StrikeB1Shot* shot = &fx->shots[i];
        if (!shot->state) continue;
        /* Count is per draw, not per tick; life is in motion ticks. */
        if (shot->state == 1 && ++shot->count > 2) shot->state = 2;
        shot->life -= dt;
        if (shot->life > 0) continue;
        if (shot->impact)
            for (int p = 0; p < 3; ++p) strike_b1_spawn_particle(fx, &shot->target, p == 2);
        shot->state = 0;
    }
}

static inline void strike_b1_update_particles(StrikeB1Fx* fx, int dt) {
    if (dt <= 0) return;
    for (int i = 0; i < STRIKE_B1_PARTICLES; ++i) {
        StrikeB1Particle* p = &fx->particles[i];
        if (!p->active) continue;
        if (++p->frame >= 4) { p->active = 0; continue; }
        p->pos.x += p->vel.x * dt;
        p->pos.y += p->vel.y * dt;
        p->pos.z += p->vel.z * dt;
    }
}

static inline int strike_b1_any_active(const StrikeB1Fx* fx) {
    for (int i = 0; i < STRIKE_B1_SHOTS; ++i) if (fx->shots[i].state) return 1;
    for (int i = 0; i < STRIKE_B1_PARTICLES; ++i) if (fx->particles[i].active) return 1;
    return 0;
}

#endif
