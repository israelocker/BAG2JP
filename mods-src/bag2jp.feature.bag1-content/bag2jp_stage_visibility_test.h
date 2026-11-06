/* Experimental visibility-only A/B seam; disabled unless explicitly requested. */
#ifndef BAG2JP_STAGE_VISIBILITY_TEST_H
#define BAG2JP_STAGE_VISIBILITY_TEST_H

#define B1SV_PATCH_ADDRESS 0x80030590u
#define B1SV_NATIVE_WORD 0x0243001bu /* divu s2,v1: screen margin / valid depth */
#define B1SV_SCREEN_BYPASS 0x0800c175u /* j 0x800305d4: set visibility byte */

static int b1sv_owned;

static int b1sv_guards_match(void) {
    return psx_mod_read_word(0x80030574u) == 0x2c421000u && /* valid depth */
           psx_mod_read_word(0x80030578u) == 0x10400018u && /* reject depth */
           psx_mod_read_word(0x80030588u) == 0x04400014u && /* reject GTE flag */
           psx_mod_read_word(0x80030594u) == 0x00002012u && /* safe delay slot */
           psx_mod_read_word(0x800305d4u) == 0x24020001u && /* visibility=1 */
           psx_mod_read_word(0x800305d8u) == 0xa2020000u;   /* store visibility */
}

/* Restore only our word, never an unknown patch installed by another owner.
 * The jump's mflo delay slot changes a0, which is dead before the next use.
 * Depth and GTE rejection precede this jump and remain native. */
static int b1sv_update(int requested, int strike_loaded) {
    const uint32_t current = psx_mod_read_word(B1SV_PATCH_ADDRESS);
    if (!requested || !strike_loaded) {
        const int restore = b1sv_owned && current == B1SV_SCREEN_BYPASS;
        b1sv_owned = 0;
        if (!restore) return 0;
        psx_mod_write_code_word(B1SV_PATCH_ADDRESS, B1SV_NATIVE_WORD);
        return psx_mod_read_word(B1SV_PATCH_ADDRESS) == B1SV_NATIVE_WORD ? 2 : -1;
    }
    if (b1sv_owned && current == B1SV_SCREEN_BYPASS) return 0;
    b1sv_owned = 0;
    if (current != B1SV_NATIVE_WORD || !b1sv_guards_match()) return -1;
    psx_mod_write_code_word(B1SV_PATCH_ADDRESS, B1SV_SCREEN_BYPASS);
    b1sv_owned = psx_mod_read_word(B1SV_PATCH_ADDRESS) == B1SV_SCREEN_BYPASS;
    return b1sv_owned ? 1 : -1;
}

#endif
