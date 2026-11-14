/* BAG2 JP combat overlay 005, FUN_80093de0: adjust only the current sprite.
 * Never patch the shared Bi-O descriptors: mixed BAG1/BAG2 sides use them too.
 * Native BAG2 glyph indices use the game's shared HUD CLUT, not body CLUTs.
 * Experimental until recorded mixed-side and regional acceptance passes. */
#ifndef BAG2JP_BAG1_HUD_H
#define BAG2JP_BAG1_HUD_H

#include <stdint.h>
#include "bag2jp_bag1_load_latch.h"

#define B1HUD_WIDTH 69u
#define B1HUD_HEIGHT 7u

int bag2jp_bag1_get_version(int chr, int side);

static int b1hud_ram(uint32_t address, uint32_t bytes) {
    return address >= 0x80010000u && address <= 0x80800000u - bytes;
}

static void b1hud_sprite_hook(struct CPUState* cpu, uint32_t address) {
    if (!cpu || address != 0x80093F6Cu) return;
    /* Registers are callee-preserved at the instruction after SetSprt's caller.
     * Fingerprint both the site and preceding JAL/delay store, since other
     * overlays reuse this address. The framework still executes original LUI. */
    if (psx_mod_read_word(address) != 0x3C0400FFu
        || psx_mod_read_word(address - 8u) != 0x0C012649u
        || psx_mod_read_word(address - 4u) != 0xA6220012u) return;
    const uint32_t side = cpu->gpr[20] - 0x8005E6CCu;
    if (side > 1u || bag2jp_bag1_get_version(9, (int)side) != 1) return;
    const uint32_t dancer = psx_mod_read_word(0x8005F808u + side * 8u);
    if (!b1hud_ram(dancer, 8u) || psx_mod_read_byte(dancer + 4u) != 9u) return;
    const uint32_t costume = psx_mod_read_byte(dancer + 6u);
    /* The pack actually read, not the per-frame DF2_ table: see the load latch. */
    if (costume > 1u || !b1load_hud_loaded_alt(53u + side + costume * 72u)) return;
    const uint32_t descriptor = 0x8009E6D6u + costume * 0x6Cu;
    if (cpu->gpr[19] != descriptor
        || psx_mod_read_word(descriptor) != 0x072D7020u
        || psx_mod_read_half(descriptor + 4u) != 1u) return;
    const uint32_t sprite = cpu->gpr[17], texture = cpu->gpr[18];
    const uint32_t textures = psx_mod_read_word(0x80053544u + (side * 19u + 9u) * 4u);
    if (!b1hud_ram(sprite, 20u) || !b1hud_ram(textures, 96u)
        || texture != textures + 48u
        || sprite + 20u != psx_mod_read_word(0x80051A88u)) return;
    const uint32_t u = psx_mod_read_byte(texture + 14u);
    const uint32_t v = psx_mod_read_byte(texture + 15u);
    if (u + B1HUD_WIDTH > 256u || v + B1HUD_HEIGHT > 256u
        || psx_mod_read_half(sprite + 16u) != 45u
        || psx_mod_read_half(sprite + 18u) != 7u
        || psx_mod_read_byte(sprite + 12u) != ((u + 32u) & 255u)
        || psx_mod_read_byte(sprite + 13u) != ((v + 112u) & 255u)) return;
    /* Right-side native X already subtracts stock width. Keep its right edge. */
    const int32_t x = (int16_t)psx_mod_read_half(sprite + 8u);
    psx_mod_write_half(sprite + 8u, (uint16_t)(x + (45 - (int32_t)B1HUD_WIDTH) * (int32_t)side));
    psx_mod_write_byte(sprite + 12u, (uint8_t)u);
    psx_mod_write_byte(sprite + 13u, (uint8_t)v);
    psx_mod_write_half(sprite + 16u, B1HUD_WIDTH);
    psx_mod_write_half(sprite + 18u, B1HUD_HEIGHT);
}

#endif
