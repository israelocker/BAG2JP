/* Player model buffers in expanded RAM for BAG1 characters.
 *
 * The loader state machine (main exe 0x800342DC) loads each side's pack and then its model file
 * at a fixed base, followed by the runtime dancer struct: P1 0x80089248, P2 0x8008924C. Stock
 * gives every side 488092 bytes (VS 0x800DDB18..0x80154DB4, Dance View 0x800D1350..0x801485EC).
 * BAG1 Strike's full 101-slot animation list overruns that and corrupts the next side
 * (notes/strike-recovery.md, motion_recovery/memory-budget.json). With the 8 MB map active, nothing
 * in the main exe or any DBI addresses 0x80200000..0x807F0000 and the BIOS heap is never used, so
 * a BAG1 side's base moves there once per load, after the pack phase began and before the model
 * (P1, state 6) or the P2 pack (state 8) reads it. Never active with 2 MB: those pages mirror. */
#ifndef BAG2JP_MODEL_REGION_H
#define BAG2JP_MODEL_REGION_H

#include <stdint.h>

#define B1R_RAM_SIZE_WORD 0x80035E48u   /* startup RAM size, patched by the expanded-ram package */
#define B1R_RAM_8MB       0x00800000u
#define B1R_BASE_P1       0x80089248u   /* side load base; P2 at +4 */
#define B1R_BASE_P2       0x8008924Cu
#define B1R_LOADER_STATE  0x80089215u   /* byte: 1..5 pack phase, 6 P1 model, 8 P2 pack */
#define B1R_STOCK_LIMIT   0x80200000u   /* any base below this is a stock 2 MB address */
#define B1R_LAST_STATE_P1 5
#define B1R_LAST_STATE_P2 7

uint32_t psx_mod_read_word(uint32_t address);
uint8_t psx_mod_read_byte(uint32_t address);
void psx_mod_write_word(uint32_t address, uint32_t value);

/* wanted[s]: side s plays a BAG1 version. Returns bit s set for each base moved now. */
static int bag2_model_region_tick(const int wanted[2]) {
    static const uint32_t base_word[2] = {B1R_BASE_P1, B1R_BASE_P2};
    static const uint32_t high_base[2] = {0x80200000u, 0x80300000u};   /* 1 MB each */
    static const int last_state[2] = {B1R_LAST_STATE_P1, B1R_LAST_STATE_P2};
    if (psx_mod_read_word(B1R_RAM_SIZE_WORD) != B1R_RAM_8MB) return 0;
    const int state = psx_mod_read_byte(B1R_LOADER_STATE);
    int moved = 0;
    for (int s = 0; s < 2; ++s) {
        if (!wanted[s] || state < 1 || state > last_state[s]) continue;
        const uint32_t base = psx_mod_read_word(base_word[s]);
        if (base < 0x80000000u || base >= B1R_STOCK_LIMIT) continue;   /* unset or already moved */
        psx_mod_write_word(base_word[s], high_base[s]);
        moved |= 1 << s;
    }
    return moved;
}

#endif
