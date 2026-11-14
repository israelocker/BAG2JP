/* Real overlay bytes, synthetic per-measure registers, production 2P no-attack hook. */
#undef NDEBUG
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

struct CPUState { uint32_t gpr[32]; };
enum { BASE = 0x80000000u, SIZE = 0x800000u };
static uint8_t ram[SIZE];
static uint32_t psx_mod_read_word(uint32_t a) {
    assert(a >= BASE && a - BASE <= SIZE - 4u);
    uint32_t v; memcpy(&v, ram + (a - BASE), 4); return v;
}
static void put(uint32_t a, uint32_t v) { memcpy(ram + (a - BASE), &v, 4); }
#include "bag2jp_ap2_no_attack.h"

static void load(const char *overlay) {
    memset(ram, 0, sizeof ram);
    FILE *file = fopen(overlay, "rb");
    assert(file && !fseek(file, 12, SEEK_SET));
    assert(fread(ram + 0x8F890, 1, 61675, file) == 61675);
    assert(!fclose(file));
}

/* Registers at 0x8009AFE0 for player p with `stock` attacks in hand. Literal addresses, not the
 * header macros: $s5 from 0x8009AD24..0x8009AD34, $s3 from 0x8009AD38..0x8009AD40. */
static const uint32_t DANCER_CTL[2] = {0x8005E728u, 0x8005E75Au};
static const uint32_t CPU_STATE[2] = {0x8005CF08u, 0x8005CF2Cu};
static struct CPUState at_site(unsigned p, uint32_t stock) {
    struct CPUState cpu;
    for (unsigned i = 0; i < 32; ++i) cpu.gpr[i] = 0xA5A50000u + i;
    cpu.gpr[2] = stock;
    cpu.gpr[19] = DANCER_CTL[p];
    cpu.gpr[20] = p;
    cpu.gpr[21] = CPU_STATE[p];
    return cpu;
}

static void untouched(struct CPUState cpu, uint32_t address, unsigned mask) {
    const struct CPUState original = cpu;
    assert(!ap2_block_attack(&cpu, address, mask));
    assert(!memcmp(&original, &cpu, sizeof cpu));
}

int main(int argc, char **argv) {
    assert(argc == 2);
    load(argv[1]);
    for (unsigned p = 0; p < 2; ++p) for (unsigned mask = 0; mask < 4; ++mask) {
        struct CPUState cpu = at_site(p, 2), expected = cpu;
        if (mask & (1u << p)) {
            assert(ap2_block_attack(&cpu, AP2_ATTACK_SITE, mask));
            expected.gpr[2] = 0;   /* only $v0: the branch now skips the attack roll */
            assert(!memcmp(&expected, &cpu, sizeof cpu));
        } else {
            untouched(cpu, AP2_ATTACK_SITE, mask);   /* human or non-autoplayed side keeps attacking */
        }
        untouched(at_site(p, 0), AP2_ATTACK_SITE, mask);   /* no stock: already the stock path */
    }
    /* Refusals: other site, code not resident, other registers. */
    struct CPUState cpu = at_site(0, 1);
    untouched(cpu, AP2_ATTACK_SITE + 4u, 3);
    for (unsigned kind = 0; kind < 6; ++kind) {
        load(argv[1]);
        struct CPUState c = cpu;
        switch (kind) {
        case 0: put(AP2_ATTACK_SITE, 0); break;
        case 1: put(AP2_ATTACK_SITE - 8u, 0); break;
        case 2: put(AP2_ATTACK_SITE + 4u, 0); break;
        case 3: c.gpr[20] = 2; break;
        case 4: c.gpr[19] = DANCER_CTL[1]; break;
        case 5: c.gpr[21] = CPU_STATE[1]; break;
        }
        untouched(c, AP2_ATTACK_SITE, 3);
    }
    /* Same words at another address: only the registered site counts. */
    load(argv[1]);
    put(0x80030000u, AP2_ATTACK_LOAD_WORD); put(0x80030008u, AP2_ATTACK_WORD); put(0x8003000Cu, AP2_ATTACK_SLOT_WORD);
    untouched(cpu, 0x80030008u, 3);
    assert(!ap2_block_attack(NULL, AP2_ATTACK_SITE, 3));
    puts("AP2 no-attack: 2 players x 4 masks, stock-0 passthrough, 9 refusal guards; only $v0 changes");
    return 0;
}
