/* Which version of each Gas-O HUD pack was actually read from the disc.
 * Every archive read goes through FUN_8001F874(entry, dest); at 0x8001F8A4
 * (lw s0,0x8(a0)) a0 = DF2_ table + entry * 8 and the offset is consumed.
 * Ghidra: besides the table loader FUN_8001F6FC it is the only reader of
 * *(0x8005D410), and nothing references entries 53/54/125/126 directly.
 * The DF2_ table is rewritten every frame, so its current state cannot tell
 * which pack is resident; stock Bi-O and Gas-O body2 TIMs share geometry too.
 * Reset and savestate restore (the callback runs after a load, not a save)
 * forget the latch: the stock label stays until the pack is read again. */
#ifndef BAG2JP_BAG1_LOAD_LATCH_H
#define BAG2JP_BAG1_LOAD_LATCH_H

#include <stdint.h>
#include <string.h>

#define B1LOAD_SITE       0x8001F8A4u
#define B1LOAD_WORD       0x8C900008u   /* lw s0,0x8(a0) */
#define B1LOAD_PREV_WORD  0x3C028006u   /* lui v0,0x8006 */
#define B1LOAD_NEXT_WORD  0x8C92000Cu   /* lw s2,0xc(a0) */
#define B1LOAD_TABLE_PTR  0x8005D410u
#define B1LOAD_TABLE      0x8005D418u
#define B1LOAD_MAGIC      0x5F324644u   /* 'DF2_' */

int bag2jp_bag1_offset_is_alt(unsigned entry, uint32_t offset);

/* Gas-O packs: entries 53/54 (costume A, P1/P2) and 125/126 (costume B). */
static uint8_t b1load_hud_alt[4];

static int b1load_hud_slot(unsigned entry) {
    switch (entry) {
    case 53u: return 0;
    case 54u: return 1;
    case 125u: return 2;
    case 126u: return 3;
    default: return -1;
    }
}

static void b1load_read_hook(struct CPUState* cpu, uint32_t address) {
    if (!cpu || address != B1LOAD_SITE) return;
    if (psx_mod_read_word(address) != B1LOAD_WORD
        || psx_mod_read_word(address - 4u) != B1LOAD_PREV_WORD
        || psx_mod_read_word(address + 4u) != B1LOAD_NEXT_WORD) return;
    /* Other archives would give the index another meaning: ignore them. */
    if (psx_mod_read_word(B1LOAD_TABLE_PTR) != B1LOAD_TABLE
        || psx_mod_read_word(B1LOAD_TABLE) != B1LOAD_MAGIC) return;
    const uint32_t rel = cpu->gpr[4] - B1LOAD_TABLE;
    if (rel & 7u) return;
    const uint32_t entry = rel >> 3;
    if (entry >= psx_mod_read_word(B1LOAD_TABLE + 4u)) return;
    const int slot = b1load_hud_slot(entry);
    if (slot < 0) return;
    const uint32_t offset = psx_mod_read_word(cpu->gpr[4] + 8u);
    b1load_hud_alt[slot] = (uint8_t)(bag2jp_bag1_offset_is_alt(entry, offset) != 0);
}

static int b1load_hud_loaded_alt(unsigned entry) {
    const int slot = b1load_hud_slot(entry);
    return slot >= 0 && b1load_hud_alt[slot];
}

static void b1load_forget(void) {
    memset(b1load_hud_alt, 0, sizeof b1load_hud_alt);
}

#endif
