/* Experimental dance & end-pose centering at the native leash seam, never from VBlank.
 * Caller supplies a main dancer already verified as the selected BAG1 version.
 * At 0x8002D818, s3 is ctl and s0 is actor, after reanchor/blend handling and
 * before FUN_8002CD48 and FUN_8002C404. Gently centers toward each dancer's own
 * initial home position during settled normal dance (phase 1/3, anim <= 72, no
 * active/pending attacks) and finishes centering on settled anim67/anim68 in phase 1/4;
 * native victory/defeat, duet/solo fever, attack clips and INT_MAX stay untouched.
 * Move base, not root: C404 consumes base once to produce the rendered pose. */
#ifndef BAG2JP_BAG1_CENTER_H
#define BAG2JP_BAG1_CENTER_H

#define B1CENTER_SITE             0x8002D818u
#define B1CENTER_WORD             0x8E660038u  /* lw a2,0x38(s3) */
#define B1CENTER_ROOT             0x8005D3D4u
#define B1CENTER_PHASE1           0x8005D3D8u
#define B1CENTER_PHASE2           0x8005D3DCu
#define B1CENTER_PAUSED           0x8005D3E4u
#define B1CENTER_MODE             0x8005D2C4u
#define B1CENTER_ACTORS           0x8005F808u
#define B1CENTER_ACTOR_SIZE       0x155Cu
#define B1CENTER_ROOT_X           0x810u
#define B1CENTER_BASE_X           0x14B8u
#define B1CENTER_ANIM             0x154Cu
#define B1CENTER_IDLE_ALT         67u
#define B1CENTER_IDLE             68u
#define B1CENTER_DANCE_PHASE      3u
#define B1CENTER_MAX_DANCE_ANIM   72u
#define B1CENTER_MAX_STEP         8
#define B1CENTER_DIVISOR          32
#define B1CENTER_DANCE_DEADZONE   16
#define B1CENTER_DANCE_DIVISOR    48
#define B1CENTER_DANCE_MAX_STEP   3
#define B1CENTER_P1_ATTACK_ACTIVE 0x8005E748u
#define B1CENTER_P1_ATTACK_PEND   0x8005E754u
#define B1CENTER_P2_ATTACK_ACTIVE 0x8005E778u  /* P2 halfword in upper 16 bits (+2) */
#define B1CENTER_P2_ATTACK_PEND   0x8005E784u  /* P2 pending byte in bits 16..23 (+2) */

static uint32_t b1center_actor[2], b1center_tick[2];

static void b1center_forget(void) {
    memset(b1center_actor, 0, sizeof b1center_actor);
    memset(b1center_tick, 0, sizeof b1center_tick);
}

/* A savestate restores guest RAM, not the process-local leash cache. Derive the
 * expected tightened radius from native raw/zoom/home instead of that cache. */
static int b1center_radius_ready(uint32_t ctl, int32_t home, uint32_t radius) {
    const uint32_t stage = psx_mod_read_word(B1LEASH_STAGE_PTR);
    if (stage < B1LEASH_RAM_LOW || stage > B1LEASH_RAM_END - 8u || (stage & 3u)) return 0;
    const uint32_t zoom = psx_mod_read_word(stage + B1LEASH_STAGE_ZOOM) & 0xFFFFu;
    const uint32_t raw = psx_mod_read_word(ctl + B1LEASH_RAW_RADIUS);
    if (!zoom || zoom > 0x7FFFu || raw > 0xFFFFu) return 0;
    return radius && radius != B1LEASH_UNLIMITED &&
        radius == b1leash_target(b1home_reference(ctl, home), (raw * zoom) >> 8);
}

static int b1center_attack_busy(void) {
    return (psx_mod_read_word(B1CENTER_P1_ATTACK_ACTIVE) & 0xFFFFu) != 0u ||
           (psx_mod_read_word(B1CENTER_P1_ATTACK_PEND) & 0xFFu) != 0u ||
           ((psx_mod_read_word(B1CENTER_P2_ATTACK_ACTIVE) >> 16) & 0xFFFFu) != 0u ||
           ((psx_mod_read_word(B1CENTER_P2_ATTACK_PEND) >> 16) & 0xFFu) != 0u;
}

static int b1center_eligible(int slot, uint32_t dancer) {
    if ((slot != 0 && slot != 2) || (dancer & 3u) || dancer < 0x80010000u ||
        dancer > 0x80800000u - B1CENTER_ACTOR_SIZE) return 0;
    const uint32_t mode = psx_mod_read_word(B1CENTER_MODE);
    if ((mode != 1u && mode != 2u) || psx_mod_read_word(B1CENTER_PAUSED) ||
        psx_mod_read_word(B1CENTER_ROOT) != 19u ||
        psx_mod_read_word(B1CENTER_PHASE1) != 1u) return 0;
    const uint32_t phase2 = psx_mod_read_word(B1CENTER_PHASE2);
    if (phase2 != 4u && phase2 != B1CENTER_DANCE_PHASE) return 0;
    const uint32_t ctl = B1LEASH_CTL + (uint32_t)slot * B1LEASH_CTL_STRIDE;
    const uint32_t radius = psx_mod_read_word(ctl + B1LEASH_RADIUS);
    const int32_t home = (int32_t)psx_mod_read_word(ctl + B1LEASH_HOME_X);
    if (psx_mod_read_word(B1CENTER_ACTORS + (uint32_t)slot * 4u) != dancer ||
        psx_mod_read_word(ctl) != dancer || !b1center_radius_ready(ctl, home, radius) ||
        !(slot ? home > 0 : home < 0) || home < -65536 || home > 65536 ||
        psx_mod_read_word(ctl + B1LEASH_HOME_X + 8u) != 0u ||
        !(psx_mod_read_word(ctl + 0xCu) & 0xFFu) ||
        !(psx_mod_read_word(dancer) >> 24) ||
        (psx_mod_read_word(ctl + 4u) & 0xFFFFu) != 0x1000u) return 0;
    const uint32_t anim = psx_mod_read_word(dancer + B1CENTER_ANIM);
    if (phase2 == 4u) return anim == B1CENTER_IDLE_ALT || anim == B1CENTER_IDLE;
    return anim <= B1CENTER_MAX_DANCE_ANIM && !b1center_attack_busy();
}

static void b1center_axis_step(uint32_t root, uint32_t base, int32_t home,
                               int64_t deadzone, int64_t divisor, int64_t max_step) {
    const int64_t error = (int64_t)(int32_t)psx_mod_read_word(root) - home;
    const int64_t magnitude = error < 0 ? -error : error;
    if (magnitude <= deadzone) return;
    int64_t step = (magnitude - deadzone + divisor - 1) / divisor;
    if (step > max_step) step = max_step;
    const int64_t position = (int32_t)psx_mod_read_word(base);
    const int64_t next = position + (error < 0 ? step : -step);
    if (step && next >= INT32_MIN && next <= INT32_MAX)
        psx_mod_write_word(base, (uint32_t)(int32_t)next);
}

static void b1center_apply(int slot, uint32_t dancer, uint32_t tick) {
    if (!b1center_eligible(slot, dancer)) return;
    const unsigned side = (unsigned)slot / 2u;
    if (b1center_actor[side] == dancer && b1center_tick[side] == tick) return;
    b1center_actor[side] = dancer;
    b1center_tick[side] = tick;
    const uint32_t ctl = B1LEASH_CTL + (uint32_t)slot * B1LEASH_CTL_STRIDE;
    const int32_t home = (int32_t)psx_mod_read_word(ctl + B1LEASH_HOME_X);
    const int dance = psx_mod_read_word(B1CENTER_PHASE2) == B1CENTER_DANCE_PHASE;
    const int64_t deadzone = dance ? B1CENTER_DANCE_DEADZONE : 0;
    const int64_t divisor = dance ? B1CENTER_DANCE_DIVISOR : B1CENTER_DIVISOR;
    const int64_t max_step = dance ? B1CENTER_DANCE_MAX_STEP : B1CENTER_MAX_STEP;
    b1center_axis_step(dancer + B1CENTER_ROOT_X, dancer + B1CENTER_BASE_X,
                       home, deadzone, divisor, max_step);
    b1center_axis_step(dancer + B1CENTER_ROOT_X + 8u, dancer + B1CENTER_BASE_X + 8u,
                       0, deadzone, divisor, max_step);
}

#endif
