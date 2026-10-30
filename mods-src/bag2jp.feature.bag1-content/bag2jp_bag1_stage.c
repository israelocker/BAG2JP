/* BAG1 stage support (package bag2jp.feature.bag1-content, feature "bag1-stage").
 *
 * The BAG1 Heat stage program is ported to a BAG2 stage DBI by tools/bag1import/port_bag1_stage.py.
 * It reads a few BAG1 game variables that BAG2 does not have; the port points them at a shim block
 * inside the DBI image (0x801E0100: 'B1ST', beat flags u32, score level u8, previous level u8) and
 * this plugin fills it once per frame while that DBI is resident and stage id 0 is loaded:
 *   beat flags (BAG1 0x80068704): bit 0 = a beat happened this frame (BAG2 beat counter 0x8005E2D0
 *   changed), bit 4 = it is the first beat of a bar (= bar start 0x8005E684), bit 6 = song over
 *   (beats left 0x8005E658 reached 0);
 *   score level (BAG1 0x80068714): 1 from 15000 points, 2 from 45000 (best of 0x8005E6F8/FC);
 *   previous level (BAG1 0x800979D0, set by BAG1 after each stage update): last frame's level. */
#include <stdint.h>
#include "mod_plugins.h"

#define B1S_SHIM   0x801E0100u
#define B1S_MAGIC  0x54533142u   /* 'B1ST' */

static void b1s_vblank(void) {
    static uint16_t last_beat = 0xFFFF;
    if (psx_mod_read_word(B1S_SHIM) != B1S_MAGIC) { last_beat = 0xFFFF; return; }
    const uint32_t stage = psx_mod_read_word(0x80089200u);
    if (stage < 0x80000000u || stage >= 0x80800000u || psx_mod_read_byte(stage) != 0) return;
    const uint16_t beat = psx_mod_read_half(0x8005E2D0u);
    uint32_t flags = 0;
    if (last_beat != 0xFFFF && beat != last_beat) {
        flags |= 1u;
        if (beat == psx_mod_read_half(0x8005E684u)) flags |= 0x10u;
    }
    if (beat != 0 && psx_mod_read_half(0x8005E658u) == 0) flags |= 0x40u;
    last_beat = beat;
    const int32_t s0 = (int32_t)psx_mod_read_word(0x8005E6F8u), s1 = (int32_t)psx_mod_read_word(0x8005E6FCu);
    const int32_t best = s0 > s1 ? s0 : s1;
    const uint8_t level = best >= 45000 ? 2 : best >= 15000 ? 1 : 0;
    psx_mod_write_word(B1S_SHIM + 4u, flags);
    psx_mod_write_byte(B1S_SHIM + 9u, psx_mod_read_byte(B1S_SHIM + 8u));
    psx_mod_write_byte(B1S_SHIM + 8u, level);
}

PSX_MOD_CONSTRUCTOR(bag2jp_register_bag1_stage) {
    (void)psx_mod_register_vblank_plugin("bag2jp.bag1_stage", b1s_vblank);
}
