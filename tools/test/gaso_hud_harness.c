/* Real overlay bytes, synthetic per-draw registers, production callback. */
#undef NDEBUG
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

struct CPUState { uint32_t gpr[32]; };
enum { BASE = 0x80000000u, SIZE = 0x800000u, SPRITE = 0x8007F6B8u,
       DANCER = 0x80410000u, TEXTURES = 0x800C0000u, TEXTURE = TEXTURES + 48u };
static uint8_t ram[SIZE], saved[SIZE];
static int versions[2];
static uint32_t reads, writes, offset_queries;
static uint32_t read_value(uint32_t address, unsigned bytes) {
    assert(address >= BASE && address - BASE <= SIZE - bytes);
    ++reads;
    uint32_t value = 0;
    for (unsigned i = 0; i < bytes; ++i) value |= (uint32_t)ram[address - BASE + i] << (i * 8u);
    return value;
}
static void put(uint32_t address, uint32_t value, unsigned bytes) {
    assert(address >= BASE && address - BASE <= SIZE - bytes);
    for (unsigned i = 0; i < bytes; ++i) ram[address - BASE + i] = (uint8_t)(value >> (i * 8u));
}
static uint32_t psx_mod_read_word(uint32_t a) { return read_value(a, 4); }
static uint16_t psx_mod_read_half(uint32_t a) { return (uint16_t)read_value(a, 2); }
static uint8_t psx_mod_read_byte(uint32_t a) { return (uint8_t)read_value(a, 1); }
static void psx_mod_write_half(uint32_t a, uint16_t v) { ++writes; put(a, v, 2); }
static void psx_mod_write_byte(uint32_t a, uint8_t v) { ++writes; put(a, v, 1); }
int bag2jp_bag1_get_version(int chr, int side) { assert(chr == 9 && side >= 0 && side <= 1); return versions[side]; }
/* Synthetic BAG1 offsets; the real index lookup is covered by test_bag1_stage_shim. */
static uint32_t alt_offset(unsigned entry) { return 0x01000000u + entry * 0x800u; }
static uint32_t stock_offset(unsigned entry) { return 0x00100000u + entry * 0x800u; }
int bag2jp_bag1_offset_is_alt(unsigned entry, uint32_t offset) {
    assert(entry == 53u || entry == 54u || entry == 125u || entry == 126u);
    ++offset_queries;
    return offset == alt_offset(entry);
}
#include "bag2jp_bag1_hud.h"

enum { ENTRIES = 400 };
static const unsigned hud_entries[4] = {53u, 54u, 125u, 126u};

/* FUN_8001F874's site and a DF2_ table where every entry holds `offset_of(entry)`. */
static void loader(uint32_t (*offset_of)(unsigned)) {
    put(B1LOAD_SITE - 4u, B1LOAD_PREV_WORD, 4);
    put(B1LOAD_SITE, B1LOAD_WORD, 4);
    put(B1LOAD_SITE + 4u, B1LOAD_NEXT_WORD, 4);
    put(B1LOAD_TABLE_PTR, B1LOAD_TABLE, 4);
    put(B1LOAD_TABLE, B1LOAD_MAGIC, 4);
    put(B1LOAD_TABLE + 4u, ENTRIES, 4);
    for (unsigned e = 0; e < ENTRIES; ++e) {
        put(B1LOAD_TABLE + 8u + 8u * e, offset_of(e), 4);
        put(B1LOAD_TABLE + 12u + 8u * e, 0x800u, 4);
    }
}

/* One archive read of `entry` as FUN_8001F874 performs it (a0 = table + entry * 8). */
static void read_entry(unsigned entry) {
    struct CPUState cpu = {{0}};
    cpu.gpr[4] = B1LOAD_TABLE + entry * 8u;
    const struct CPUState original = cpu;
    const uint32_t before = writes;
    b1load_read_hook(&cpu, B1LOAD_SITE);
    assert(writes == before && !memcmp(&original, &cpu, sizeof cpu));
}

static unsigned latched(void) {
    unsigned mask = 0;
    for (unsigned i = 0; i < 4; ++i) mask |= (unsigned)b1load_hud_loaded_alt(hud_entries[i]) << i;
    return mask;
}

static struct CPUState fixture(const char *overlay, unsigned side, unsigned costume) {
    memset(ram, 0, sizeof ram);
    FILE *file = fopen(overlay, "rb");
    assert(file && !fseek(file, 12, SEEK_SET));
    assert(fread(ram + 0x8F890, 1, 61675, file) == 61675);
    assert(!fclose(file));
    /* The pack this side draws was read from its BAG1 offset. */
    b1load_forget();
    loader(alt_offset);
    read_entry(53u + side + costume * 72u);
    loader(stock_offset);   /* the per-frame table may point anywhere at draw time */
    struct CPUState cpu = {{0}};
    cpu.gpr[17] = SPRITE; cpu.gpr[18] = TEXTURE;
    cpu.gpr[19] = 0x8009E6D6u + costume * 0x6Cu;
    cpu.gpr[20] = 0x8005E6CCu + side;
    put(0x8005F808u + side * 8u, DANCER, 4);
    put(DANCER + 4u, 9, 1); put(DANCER + 6u, costume, 1);
    put(0x80053544u + (side * 19u + 9u) * 4u, TEXTURES, 4);
    put(0x80051A88u, SPRITE + 20u, 4);
    for (unsigned i = 0; i < 20; ++i) put(SPRITE + i, 0x60u + i, 1);
    put(TEXTURE + 14, 16, 1); put(TEXTURE + 15, 32, 1);
    put(SPRITE + 8, 420 - 45 * side, 2);
    put(SPRITE + 12, 48, 1); put(SPRITE + 13, 144, 1);
    put(SPRITE + 16, 45, 2); put(SPRITE + 18, 7, 2);
    versions[side] = 1; versions[side ^ 1u] = 0;
    reads = writes = 0;
    return cpu;
}

static void denied(struct CPUState *cpu, uint32_t site) {
    const struct CPUState original = *cpu;
    memcpy(saved, ram, SIZE); writes = 0;
    b1hud_sprite_hook(cpu, site);
    assert(writes == 0 && !memcmp(saved, ram, SIZE) && !memcmp(&original, cpu, sizeof original));
}

/* A refused read must leave every latch as it was (here: 53 loaded as BAG1). */
static void read_refused(struct CPUState *cpu, uint32_t site) {
    b1load_forget(); loader(alt_offset); read_entry(53);
    put(B1LOAD_TABLE + 8u + 8u * 53u, stock_offset(53), 4);
    const uint32_t queries = offset_queries;
    b1load_read_hook(cpu, site);
    assert(latched() == 1u && offset_queries == queries);
}

static void latch_tests(void) {
    memset(ram, 0, sizeof ram);
    b1load_forget(); loader(alt_offset);
    assert(latched() == 0);
    /* Each HUD pack latches alone, from the offset read. */
    for (unsigned i = 0; i < 4; ++i) { read_entry(hud_entries[i]); assert(latched() == (2u << i) - 1u); }
    loader(stock_offset);
    read_entry(54); assert(latched() == 0xDu);
    read_entry(125); assert(latched() == 0x9u);
    /* Rewriting the table without a read changes nothing. */
    loader(alt_offset); assert(latched() == 0x9u);
    /* Other entries (choreography, models, stage, neighbours) never query or latch. */
    const unsigned others[] = {0, 17, 52, 55, 89, 90, 124, 127, 161, 162, 197, ENTRIES - 1};
    const uint32_t queries = offset_queries;
    for (unsigned i = 0; i < sizeof others / sizeof others[0]; ++i) read_entry(others[i]);
    assert(latched() == 0x9u && offset_queries == queries);
    b1load_forget(); assert(latched() == 0);
    assert(!b1load_hud_loaded_alt(17) && !b1load_hud_loaded_alt(55));

    /* Guards: site, fingerprints, table identity, alignment and bounds. */
    struct CPUState cpu = {{0}};
    cpu.gpr[4] = B1LOAD_TABLE + 53u * 8u;
    read_refused(NULL, B1LOAD_SITE);
    /* Same three words at another address: only the registered site counts. */
    put(0x80030000u, B1LOAD_PREV_WORD, 4); put(0x80030004u, B1LOAD_WORD, 4); put(0x80030008u, B1LOAD_NEXT_WORD, 4);
    read_refused(&cpu, 0x80030004u);
    for (unsigned kind = 0; kind < 9; ++kind) {
        struct CPUState c = cpu;
        b1load_forget(); loader(alt_offset); read_entry(53);
        put(B1LOAD_TABLE + 8u + 8u * 53u, stock_offset(53), 4);
        switch (kind) {
        case 0: put(B1LOAD_SITE, 0, 4); break;
        case 1: put(B1LOAD_SITE - 4u, 0, 4); break;
        case 2: put(B1LOAD_SITE + 4u, 0, 4); break;
        case 3: put(B1LOAD_TABLE_PTR, 0x80100000u, 4); break;
        case 4: put(B1LOAD_TABLE, 0, 4); break;
        case 5: c.gpr[4] += 4u; break;
        case 6: put(B1LOAD_TABLE + 4u, 53, 4); break;
        case 7: c.gpr[4] = B1LOAD_TABLE - 8u; break;
        case 8: c.gpr[4] = B1LOAD_TABLE + ENTRIES * 8u; break;
        }
        const uint32_t queries2 = offset_queries;
        b1load_read_hook(&c, B1LOAD_SITE);
        assert(latched() == 1u && offset_queries == queries2);
    }
}

int main(int argc, char **argv) {
    assert(argc == 2);
    latch_tests();
    for (unsigned side = 0; side < 2; ++side) for (unsigned costume = 0; costume < 2; ++costume) {
        struct CPUState cpu = fixture(argv[1], side, costume), original = cpu;
        memcpy(saved, ram, SIZE);
        b1hud_sprite_hook(&cpu, 0x80093F6C);
        assert(writes == 5 && !memcmp(&cpu, &original, sizeof cpu));
        assert(psx_mod_read_half(SPRITE + 8) == 420 - 69 * side);
        assert(psx_mod_read_byte(SPRITE + 12) == 16 && psx_mod_read_byte(SPRITE + 13) == 32);
        assert(psx_mod_read_half(SPRITE + 16) == 69 && psx_mod_read_half(SPRITE + 18) == 7);
        /* Restore exactly the five owned fields; every other byte must match.
         * This pins CLUT, Y, RGB, TPAGE, allocator, code and shared descriptors. */
        for (unsigned i = 0; i < 20; ++i)
            if (i == 8 || i == 9 || i == 12 || i == 13 || i >= 16)
                ram[SPRITE - BASE + i] = saved[SPRITE - BASE + i];
        assert(!memcmp(saved, ram, SIZE));
        versions[side] = 0; versions[side ^ 1u] = 1; denied(&cpu, 0x80093F6C);
    }
    for (unsigned kind = 0; kind < 18; ++kind) {
        struct CPUState cpu = fixture(argv[1], 0, 0);
        switch (kind) {
        case 0: denied(&cpu, 0); continue;
        case 1: cpu.gpr[20] = 0x8005E6CE; break;
        case 2: put(0x80093F6C, 0, 4); break;
        case 3: put(0x80093F64, 0, 4); break;
        case 4: put(0x80093F68, 0, 4); break;
        case 5: put(DANCER + 4, 0, 1); break;
        case 6: put(DANCER + 6, 2, 1); break;
        /* Bi-O's stock pack was read; the DF2_ table pointing at BAG1 now must not matter. */
        case 7: loader(stock_offset); read_entry(53); loader(alt_offset); break;
        case 8: cpu.gpr[19] += 6; break;
        case 9: put(cpu.gpr[19], 0, 4); break;
        case 10: put(cpu.gpr[19] + 4, 2, 2); break;
        case 11: cpu.gpr[17] = 0xFFFFFFFF; break;
        case 12: cpu.gpr[18] = 0xFFFFFFFF; break;
        case 13: put(0x80051A88, SPRITE + 21, 4); break;
        case 14: put(TEXTURE + 14, 188, 1); break;
        case 15: put(TEXTURE + 15, 250, 1); break;
        case 16: put(SPRITE + 16, 69, 2); break;
        case 17: put(SPRITE + 12, 49, 1); break;
        }
        denied(&cpu, 0x80093F6C);
    }
    puts("HUD: load latch (4 packs, 11 refusal guards), four side/costume cases, mixed versions, "
         "18 refusal guards; CPU/CLUT/descriptors preserved");
    return 0;
}
