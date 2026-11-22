/* Score-only diagnostic seam. Never enable on personal cards. */
#ifndef BAG2JP_SCORE_FIXTURE_H
#define BAG2JP_SCORE_FIXTURE_H

/* JP identity, local-versus root/mode, active dance, Heat A/B mirror, and the
 * exact native score-gap gate. No code or winner/fever flags are written. */
static const uint32_t BAG2_SCORE_FIXTURE_GUARDS[][3] = {
    {0x8004E2D8u, 0x54535542u, 0xFFFFFFFFu}, /* BUST */
    {0x8004E2DCu, 0x4D5F415Fu, 0xFFFFFFFFu}, /* _A_M */
    {0x8005D3D4u, 19u, 0xFFFFFFFFu},         /* battle root */
    {0x8005D2C4u, 2u, 0xFFFFu},             /* local versus mode */
    {0x8005D3D8u, 1u, 0xFFFFFFFFu},          /* dance phase */
    {0x8005D3DCu, 3u, 0xFFFFFFFFu},
    {0x8005E6A0u, 0u, 0xFFFFFFFFu},          /* Heat P1 */
    {0x8005E6A4u, 0u, 0xFFFFFFFFu},          /* Heat P2 */
    {0x8005E668u, 0x100u, 0xFFFFu},          /* A/P1, B/P2 */
    {0x80098C44u, 0x284203E8u, 0xFFFFFFFFu}  /* native abs(score gap)<1000 */
};
#define BAG2_FIXTURE_SCORE_P1_ADDR 0x8005E6F8u
#define BAG2_FIXTURE_SCORE_P2_ADDR 0x8005E6FCu
#define BAG2_FIXTURE_SCORE_P1 500000u
#define BAG2_FIXTURE_SCORE_P2 500100u
#define BAG2_FIXTURE_RNG_CALL_ADDR 0x8009CDB8u
#define BAG2_FIXTURE_RNG_CALL_WORD 0x0C0127C9u
#define BAG2_FIXTURE_RNG_SEED_ADDR 0x00008548u
#define BAG2_FIXTURE_RNG_SEED 1u /* OpenBIOS rand=16838, modulo3=2. */

/* Checked at the duet's rand call, never while dancing or at other rand sites.
 * The complete BIOS rand body binds the seed address and arithmetic contract. */
static const uint32_t BAG2_DUET_RNG_GUARDS[][3] = {
    {0x8004E2D8u, 0x54535542u, 0xFFFFFFFFu},
    {0x8004E2DCu, 0x4D5F415Fu, 0xFFFFFFFFu},
    {0x8005D3D4u, 19u, 0xFFFFFFFFu},
    {0x8005D2C4u, 2u, 0xFFFFu},
    {0x8005D3D8u, 1u, 0xFFFFFFFFu},
    {0x8005D3DCu, 7u, 0xFFFFFFFFu},
    {0x8005D3E0u, 1u, 0xFFFFFFFFu},
    {0x8005E6A0u, 0u, 0xFFFFFFFFu},
    {0x8005E6A4u, 0u, 0xFFFFFFFFu},
    {0x8005E668u, 0x100u, 0xFFFFu},
    {0x8005E6C0u, 2u, 0xFFu},
    {BAG2_FIXTURE_RNG_CALL_ADDR, BAG2_FIXTURE_RNG_CALL_WORD, 0xFFFFFFFFu},
    {0x8009CE20u, 0x244200B4u, 0xFFFFFFFFu},
    {0x8009CE24u, 0x02221021u, 0xFFFFFFFFu},
    {0x80049F24u, 0x240A00A0u, 0xFFFFFFFFu},
    {0x80049F28u, 0x01400008u, 0xFFFFFFFFu},
    {0x80049F2Cu, 0x2409002Fu, 0xFFFFFFFFu},
    {0xBFC060E4u, 0x3C030001u, 0xFFFFFFFFu},
    {0xBFC060E8u, 0x8C648548u, 0xFFFFFFFFu},
    {0xBFC060ECu, 0x3C0241C6u, 0xFFFFFFFFu},
    {0xBFC060F0u, 0x24424E6Du, 0xFFFFFFFFu},
    {0xBFC060F4u, 0x00820018u, 0xFFFFFFFFu},
    {0xBFC060F8u, 0x00001012u, 0xFFFFFFFFu},
    {0xBFC060FCu, 0x24423039u, 0xFFFFFFFFu},
    {0xBFC06100u, 0xAC628548u, 0xFFFFFFFFu},
    {0xBFC06104u, 0x00021402u, 0xFFFFFFFFu},
    {0xBFC06108u, 0x03E00008u, 0xFFFFFFFFu},
    {0xBFC0610Cu, 0x30427FFFu, 0xFFFFFFFFu}
};

static int bag2_duet_rng_fixture_tick(int enabled) {
    if (!enabled) return 0;
    for (unsigned int i = 0; i < sizeof(BAG2_DUET_RNG_GUARDS) /
                                      sizeof(BAG2_DUET_RNG_GUARDS[0]); ++i) {
        const uint32_t* guard = BAG2_DUET_RNG_GUARDS[i];
        if ((psx_mod_read_word(guard[0]) & guard[2]) != guard[1]) return 0;
    }
    psx_mod_write_word(BAG2_FIXTURE_RNG_SEED_ADDR, BAG2_FIXTURE_RNG_SEED);
    return 1;
}

static int bag2_score_fixture_matches(void) {
    /* JP005 FUN_80099e90 dispatches dance via 800987bc without reading this
     * residual field. Recorded paths retain 3 or 23; accept only those paths,
     * never an arbitrary phase. The dance/root/actor/code guards still apply. */
    const uint32_t residual = psx_mod_read_word(0x8005D3E0u);
    if (residual != 3u && residual != 23u) return 0;
    for (unsigned int i = 0; i < sizeof(BAG2_SCORE_FIXTURE_GUARDS) /
                                      sizeof(BAG2_SCORE_FIXTURE_GUARDS[0]); ++i) {
        const uint32_t* guard = BAG2_SCORE_FIXTURE_GUARDS[i];
        if ((psx_mod_read_word(guard[0]) & guard[2]) != guard[1]) return 0;
    }
    return 1;
}

static int bag2_score_fixture_tick(int enabled) {
    if (!enabled || !bag2_score_fixture_matches()) return 0;
    psx_mod_write_word(BAG2_FIXTURE_SCORE_P1_ADDR, BAG2_FIXTURE_SCORE_P1);
    psx_mod_write_word(BAG2_FIXTURE_SCORE_P2_ADDR, BAG2_FIXTURE_SCORE_P2);
    return 1;
}

#endif
