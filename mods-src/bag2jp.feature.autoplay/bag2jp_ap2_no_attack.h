/* Two-player autoplay without attacks (overlay system/005.dbi, CPU per-measure block).
 * With the AP2 hooks an autoplayed dancer runs the CPU per-measure code, which also picks
 * attack command 0x6E at 0x8009AFC8..0x8009B078: game state 0x8005E65A == 3, attack stock
 * byte 0x1B($s3) != 0 and two rand() rolls against the skill. At 0x8009AFE0
 * (beqz $v0 = stock) a zero $v0 takes the stock "no attack this measure" path (0x8009B084);
 * the delay slot overwrites $v0 and the stock byte stays in RAM. The two skipped rand() calls
 * (0x8009AFE8/0x8009AFFC) do shift the RNG sequence. $s3/$s5 come from 0x8009AD24..0x8009AD40.
 * Being attacked takes the 0x8009AF00 branch instead (defend 0xAA or counter 0x6E via
 * 0x8009B074); it stays stock. With both sides autoplayed nobody attacks first, so it is not
 * reached; with only one side autoplayed that side can still counter a human attack. */
#ifndef BAG2JP_AP2_NO_ATTACK_H
#define BAG2JP_AP2_NO_ATTACK_H

#include <stdint.h>

#define AP2_ATTACK_SITE      0x8009AFE0u
#define AP2_ATTACK_WORD      0x10400028u   /* beqz $v0, 0x8009B084 */
#define AP2_ATTACK_LOAD_WORD 0x9262001Bu   /* lbu $v0, 0x1b($s3): attack stock (site - 8) */
#define AP2_ATTACK_SLOT_WORD 0x03B21021u   /* addu $v0, $sp, $s2 (delay slot) */
#define AP2_DANCER_CTL       0x8005E728u   /* $s3 = + player * 0x32 */
#define AP2_DANCER_STRIDE    0x32u
#define AP2_CPU_BASE         0x8005CF08u   /* $s5 = + player * 0x24 */
#define AP2_CPU_STRIDE       0x24u

/* `mask`: bit p set when player p is autoplayed; the caller checks two-player mode. */
static int ap2_block_attack(struct CPUState* cpu, uint32_t address, unsigned mask) {
    if (!cpu || address != AP2_ATTACK_SITE) return 0;
    if (psx_mod_read_word(address) != AP2_ATTACK_WORD
        || psx_mod_read_word(address - 8u) != AP2_ATTACK_LOAD_WORD
        || psx_mod_read_word(address + 4u) != AP2_ATTACK_SLOT_WORD) return 0;
    const uint32_t p = cpu->gpr[20];                                   /* $s4 */
    if (p > 1u || !(mask & (1u << p))
        || cpu->gpr[19] != AP2_DANCER_CTL + p * AP2_DANCER_STRIDE      /* $s3 */
        || cpu->gpr[21] != AP2_CPU_BASE + p * AP2_CPU_STRIDE) return 0; /* $s5 */
    if (cpu->gpr[2] == 0) return 0;                                    /* no stock: stock path */
    cpu->gpr[2] = 0;
    return 1;
}

#endif
