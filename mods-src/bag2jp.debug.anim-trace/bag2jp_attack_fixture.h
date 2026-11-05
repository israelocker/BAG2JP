/* Test-only CPU input at the native per-measure setup boundary. No visual effects,
 * scores, winner flags or attack-in-flight state are written. P1 Strike and Heat. */
#ifndef BAG2JP_ATTACK_FIXTURE_H
#define BAG2JP_ATTACK_FIXTURE_H
#define BAG2_ATTACK_INPUT_SITE 0x8009B084u
#define BAG2_ATTACK_INPUT_WORD 0xAC510020u
static inline int bag2_char_attack_fixture_tick(int enabled, uint32_t side, uint32_t input, uint32_t char_id) {
    if (!enabled || side != 0 || input != 0x8005CF08u) return 0;
    const uint32_t guards[][2] = {
        {0x8004E2D8u,0x54535542u}, {0x8004E2DCu,0x4D5F415Fu},
        {0x8005D3D4u,19u}, {0x8005D2C4u,2u}, {0x8005D3D8u,1u},
        {0x8005D3DCu,3u}, {0x8005D3E0u,3u},
        {BAG2_ATTACK_INPUT_SITE,BAG2_ATTACK_INPUT_WORD},
        {0x8005E6A0u,char_id}, {0x8005E754u,0u}, {0x8005E748u,0u}
    };
    for (unsigned i = 0; i < sizeof guards / sizeof guards[0]; ++i) {
        uint32_t value = psx_mod_read_word(guards[i][0]);
        if (guards[i][0] == 0x8005E754u) value &= 0xFFu;
        if (guards[i][0] == 0x8005E748u) value &= 0xFFFFu;
        if (value != guards[i][1]) return 0;
    }
    psx_mod_write_half(input + 8u, 0u);    /* CPU ready to submit input */
    psx_mod_write_half(input + 12u, 0u);   /* exact judgement timing */
    psx_mod_write_half(input + 20u, 0x6Eu); /* native attack command */
    return 1;
}
static inline int bag2_attack_fixture_tick(int enabled, uint32_t side, uint32_t input) {
    return bag2_char_attack_fixture_tick(enabled, side, input, 1u);
}
static inline int bag2_heat_attack_fixture_tick(int enabled, uint32_t side, uint32_t input) {
    return bag2_char_attack_fixture_tick(enabled, side, input, 0u);
}
/* P2 CPU under attack chose dodge (0xAA) or counter (0x6E) at 0x8009AFB8; clearing the
 * command before 0x8009B0E8 consumes it leaves the native struck path. */
static inline int bag2_char_defense_fixture_tick(int enabled, uint32_t side, uint32_t input,
                                                 uint32_t under_attack, uint32_t attacker_char) {
    if (!enabled || side != 1 || input != 0x8005CF2Cu || !under_attack) return 0;
    const uint32_t guards[][2] = {
        {0x8004E2D8u,0x54535542u}, {0x8004E2DCu,0x4D5F415Fu},
        {0x8005D3D4u,19u}, {0x8005D2C4u,2u}, {0x8005D3D8u,1u},
        {0x8005D3DCu,3u}, {0x8005D3E0u,3u},
        {BAG2_ATTACK_INPUT_SITE,BAG2_ATTACK_INPUT_WORD}, {0x8005E6A0u,attacker_char}
    };
    for (unsigned i = 0; i < sizeof guards / sizeof guards[0]; ++i)
        if (psx_mod_read_word(guards[i][0]) != guards[i][1]) return 0;
    const uint16_t command = psx_mod_read_half(input + 20u);
    if (command != 0xAAu && command != 0x6Eu) return 0;
    psx_mod_write_half(input + 20u, 0u);
    return 1;
}
static inline int bag2_heat_defense_fixture_tick(int enabled, uint32_t side, uint32_t input,
                                                 uint32_t under_attack) {
    return bag2_char_defense_fixture_tick(enabled, side, input, under_attack, 0u);
}
#endif
