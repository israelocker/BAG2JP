/* Native BAG1 Strike actor lighting; invoked at the actor-render entry. */
#ifndef BAG2JP_STRIKE_LIGHTING_H
#define BAG2JP_STRIKE_LIGHTING_H

/* Source: native ST_STRI light state, verified in face_audit/live-lighting-with-head.json.
 * Main-exe FUN_80022FF4 assigns stage lighting to both dancers on every update.
 * Apply only to BAG1 Strike at FUN_8002C404 before drawing, after that assignment.
 * Never change shared light globals.
 * A subsequent native update restores stage lighting when these guards stop matching. */
#define STRIKE_LIGHT_RENDER_ENTRY 0x8002C404u
#define STRIKE_LIGHT_RENDER_WORD 0x27BDFF68u

static inline int bag2jp_strike_lighting_apply(void) {
    static const int16_t direction[9] = {-1099, 3920, -455, 1099, -3920, 455, -109, -4085, 280};
    static const int16_t color[9] = {-2816, 5632, 7680, -2048, 8448, 1536, -768, 5632, -3072};
    if (psx_mod_read_word(0x8005D3D4u) != 19u || psx_mod_read_word(0x8005D2C4u) != 2u ||
        psx_mod_read_word(0x8005D3D8u) != 1u || psx_mod_read_word(0x8005D3DCu) != 3u ||
        psx_mod_read_word(0x8005D3E0u) != 3u) return 0;
    int changed = 0;
    for (uint32_t side = 0; side < 2; ++side) {
        if (psx_mod_read_word(0x8005E6A0u + side * 4u) != 1u ||
            !bag2jp_bag1_get_version(1, side)) continue;
        /* Preserve timed direction/color/ambient transitions (attack flashes/fades). */
        if (psx_mod_read_word(0x8005F2CCu + side * 4u) ||
            psx_mod_read_word(0x8005F2DCu + side * 4u) ||
            psx_mod_read_word(0x8005F2FCu + side * 4u)) continue;
        for (uint32_t model = 0; model < 2; ++model) {
            uint32_t d = psx_mod_read_word(0x8005F808u + side * 8u + model * 4u);
            if (d < 0x80010000u || d > 0x807FE600u || (d & 3u)) continue;
            for (uint32_t i = 0; i < 9; ++i) {
                psx_mod_write_half(d + 0x155Cu + i * 2u, (uint16_t)direction[i]);
                psx_mod_write_half(d + 0x157Cu + i * 2u, (uint16_t)color[i]);
            }
            psx_mod_write_word(d + 0x159Cu, 0x00A8A8A8u);
            ++changed;
        }
    }
    return changed;
}

#endif
