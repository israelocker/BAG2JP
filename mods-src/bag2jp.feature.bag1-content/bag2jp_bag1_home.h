/* Initial world-space anchors, not screen locking. Standard BAG1 main dancers
 * use +/-870 at 1x zoom; the leash still uses native +/-520 as its reference.
 * GO+2s camera: go-plus2-measure/solution.json (includes 16:9 GTE scaling).
 * Special stages, actors and unknown layouts retain their native init. */
#ifndef BAG2JP_BAG1_HOME_H
#define BAG2JP_BAG1_HOME_H

#define B1HOME_SITE         0x8002BA18u
#define B1HOME_WORD         0x0C00B617u
#define B1HOME_STAGE_TABLE  0x80051918u
#define B1HOME_ACTORS       0x8005F808u
#define B1HOME_MODE         0x8005D2C4u
#define B1HOME_NATIVE       520
#define B1HOME_WIDE         870
#define B1HOME_ACTOR_SIZE   0x155Cu

static int b1home_pair(uint32_t dancer, int slot, int32_t *native, int32_t *wide) {
    if ((slot != 0 && slot != 2) || (dancer & 3u) ||
        dancer < B1LEASH_RAM_LOW || dancer > B1LEASH_RAM_END - B1HOME_ACTOR_SIZE) return 0;
    const uint32_t stage = psx_mod_read_word(B1LEASH_STAGE_PTR);
    if ((stage & 3u) || stage < B1LEASH_RAM_LOW || stage > B1LEASH_RAM_END - 8u) return 0;
    const uint32_t id = psx_mod_read_word(stage) & 0xFFu;
    const uint32_t zoom = psx_mod_read_word(stage + B1LEASH_STAGE_ZOOM) & 0xFFFFu;
    if (id >= 11u || !zoom || zoom > 0x7FFFu ||
        ((psx_mod_read_word(B1HOME_STAGE_TABLE + (id & ~3u)) >> ((id & 3u) * 8u)) & 0xFFu) != 130u)
        return 0;
    const uint32_t actor = psx_mod_read_word(dancer + 4u);
    const uint32_t character = actor & 0xFFu;
    if (((actor >> 8) & 0xFFu) != (uint32_t)slot / 2u || character == 10u || character == 14u)
        return 0;
    const int32_t sign = slot ? 1 : -1;
    *native = sign * (int32_t)(B1HOME_NATIVE * zoom / 256u);
    *wide = sign * (int32_t)(B1HOME_WIDE * zoom / 256u);
    return *native && *wide >= -65536 && *wide <= 65536;
}

/* Derive from restored guest metadata, not a process-local widening latch. */
static int32_t b1home_reference(uint32_t ctl, int32_t home) {
    if (ctl < B1LEASH_CTL || (ctl - B1LEASH_CTL) % B1LEASH_CTL_STRIDE) return home;
    const uint32_t slot = (ctl - B1LEASH_CTL) / B1LEASH_CTL_STRIDE;
    if (slot != 0u && slot != 2u) return home;
    int32_t native, wide;
    return b1home_pair(psx_mod_read_word(ctl), (int)slot, &native, &wide) && home == wide
        ? native : home;
}

/* Called immediately before native init consumes its stack vector. Only X is
 * changed; native code initializes home/root/base and keeps its Y/Z/yaw logic. */
static int b1home_apply(int slot, uint32_t dancer, uint32_t vector) {
    const uint32_t mode = psx_mod_read_word(B1HOME_MODE);
    if ((mode != 1u && mode != 2u) || (vector & 3u) ||
        vector < B1LEASH_RAM_LOW || vector > B1LEASH_RAM_END - 12u) return 0;
    int32_t native, wide;
    if (!b1home_pair(dancer, slot, &native, &wide) ||
        psx_mod_read_word(B1HOME_ACTORS + (uint32_t)slot * 4u) != dancer ||
        (int32_t)psx_mod_read_word(vector) != native || psx_mod_read_word(vector + 8u)) return 0;
    psx_mod_write_word(vector, (uint32_t)wide);
    return 1;
}

#endif
