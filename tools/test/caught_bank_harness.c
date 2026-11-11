/* Actual allocator/arena/snapshot implementation; only the title API adapters
 * below are test doubles. This does not exercise mod-manager callback scopes,
 * the complete CPU bus, or the decoder. No game or installation is accessed.
 */
/* Existing framework warnings are outside this title change. Keep -Werror for
 * our harness and production bank; suppress only while parsing memory.c. */
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wcomment"
#pragma GCC diagnostic ignored "-Wunused-function"
#include "memory.c"
#pragma GCC diagnostic pop
#include "bag2jp_caught_bank.h"
#undef NDEBUG
#include <assert.h>

enum { BANK_BYTES = 1048, GUARD_BYTES = 16 };
int g_psx_render_pass_active;
static unsigned allocations, reads, writes;
static uint32_t forced_base;
static int fail_alloc, drop_write;

uint32_t psx_mod_alloc_guest_memory(uint32_t size, uint32_t alignment) {
    ++allocations;
    assert(size == BANK_BYTES && alignment == 4);
    if (fail_alloc) return 0;
    if (forced_base) return forced_base;
    return psx_mod_memory_alloc(size, alignment);
}
uint8_t psx_mod_read_byte(uint32_t address) {
    uint32_t offset;
    ++reads;
    assert(mod_memory_offset(address & 0x1fffffffu, 1, &offset));
    return mod_memory[offset];
}
void psx_mod_write_byte(uint32_t address, uint8_t value) {
    uint32_t offset;
    ++writes;
    assert(mod_memory_offset(address & 0x1fffffffu, 1, &offset));
    if (!drop_write) mod_memory[offset] = value;
}
static void expected_bank(const char *path, uint8_t out[BANK_BYTES]) {
    FILE *file = fopen(path, "rb");
    assert(file);
    assert(fread(out, 1, BANK_BYTES, file) == BANK_BYTES);
    assert(fgetc(file) == EOF && !ferror(file));
    fclose(file);
}
static B1CaughtBank prepare(void) {
    B1CaughtBank bank = {0};
    assert(psx_mod_memory_alloc(GUARD_BYTES, 4) == 0x9f000000u);
    memset(mod_memory, 0xa5, GUARD_BYTES);
    assert(b1cc_prepare(&bank));
    assert(bank.ready && bank.attempted && bank.guest_base == 0x9f000010u);
    assert(allocations == 1 && writes == BANK_BYTES);
    for (unsigned i = 0; i < GUARD_BYTES; ++i) assert(mod_memory[i] == 0xa5);
    return bank;
}
static void exact_clips(const char *path) {
    uint8_t expected[BANK_BYTES];
    expected_bank(path, expected);
    B1CaughtBank bank = prepare();
    const uint32_t ids[] = {0, 1, 9}, offsets[] = {0, 348, 700};
    const uint32_t sizes[] = {348, 352, 348};
    assert(memcmp(mod_memory + GUARD_BYTES, expected, BANK_BYTES) == 0);
    for (unsigned i = 0; i < 3; ++i) {
        B1CaughtBankClip clip;
        assert(b1cc_lookup(&bank, ids[i], 1, &clip));
        assert(clip.allocation_base == bank.guest_base);
        assert(clip.allocation_bytes == BANK_BYTES && clip.clip_bytes == sizes[i]);
        assert(clip.clip == bank.guest_base + offsets[i]);
        assert(memcmp(clip.allocation_data, expected, BANK_BYTES) == 0);
    }
    uint32_t cookie = psx_mod_memory_layout_cookie();
    for (unsigned i = 0; i < 3; ++i) assert(b1cc_prepare(&bank));
    assert(allocations == 1 && writes == BANK_BYTES && reads >= BANK_BYTES);
    assert(psx_mod_memory_layout_cookie() == cookie);
}
static void failed_allocation(unsigned kind) {
    B1CaughtBank bank = {0};
    const uint32_t invalid[] = {0x80400000u, 0x9f000001u, 0x9f0ffc00u, 0xffffffffu};
    if (kind == 4) fail_alloc = 1;
    else forced_base = invalid[kind];
    assert(!b1cc_prepare(&bank) && !bank.ready && bank.attempted);
    assert(!b1cc_prepare(&bank));
    assert(allocations == 1 && !reads && !writes);
}
static void failed_copy(void) {
    B1CaughtBank bank = {0};
    drop_write = 1;
    assert(!b1cc_prepare(&bank) && !bank.ready && bank.attempted);
    assert(!b1cc_prepare(&bank));
    assert(allocations == 1 && writes == BANK_BYTES);
    B1CaughtBankClip out;
    memset(&out, 0xa5, sizeof out);
    B1CaughtBankClip before = out;
    assert(!b1cc_lookup(&bank, 0, 1, &out));
    assert(memcmp(&out, &before, sizeof out) == 0);
}
static void snapshot_and_corruption(unsigned kind) {
    B1CaughtBank bank = prepare();
    uint32_t bytes = psx_mod_memory_snapshot_bytes();
    uint32_t cookie = psx_mod_memory_layout_cookie();
    uint8_t *saved = malloc(bytes);
    assert(saved);
    psx_mod_memory_snapshot_write(saved);
    mod_memory[GUARD_BYTES + (kind ? BANK_BYTES - 1 : 0)] ^= 0xff;
    B1CaughtBankClip out, before;
    memset(&out, 0xa5, sizeof out); before = out;
    assert(!b1cc_lookup(&bank, 0, 1, &out));
    assert(!b1cc_prepare(&bank));
    assert(memcmp(&out, &before, sizeof out) == 0);
    assert(allocations == 1 && writes == BANK_BYTES);
    assert(psx_mod_memory_snapshot_read(saved, bytes));
    assert(b1cc_lookup(&bank, 0, 1, &out) && b1cc_prepare(&bank));
    assert(allocations == 1 && writes == BANK_BYTES);
    assert(psx_mod_memory_layout_cookie() == cookie);
    free(saved);
}
static void invalid_lookup(unsigned kind) {
    B1CaughtBank bank = prepare(), empty = {0};
    B1CaughtBankClip out, before;
    memset(&out, 0xa5, sizeof out); before = out;
    unsigned prior_reads = reads;
    if (kind == 0) assert(!b1cc_lookup(&bank, 2, 1, &out));
    if (kind == 1) assert(!b1cc_lookup(&bank, 0, 0, &out));
    if (kind == 2) assert(!b1cc_lookup(&empty, 0, 1, &out));
    if (kind == 3) assert(!b1cc_lookup(NULL, 0, 1, &out));
    if (kind == 4) assert(!b1cc_lookup(&bank, 0, 1, NULL));
    assert(memcmp(&out, &before, sizeof out) == 0);
    assert(reads == prior_reads && allocations == 1 && writes == BANK_BYTES);
    assert(!b1cc_prepare(NULL));
}
int main(int argc, char **argv) {
    assert(argc == 4);
    unsigned scenario = (unsigned)strtoul(argv[1], NULL, 10);
    unsigned kind = (unsigned)strtoul(argv[2], NULL, 10);
    if (scenario == 0) exact_clips(argv[3]);
    else if (scenario == 1) { assert(kind < 5); failed_allocation(kind); }
    else if (scenario == 2) failed_copy();
    else if (scenario == 3) snapshot_and_corruption(kind);
    else if (scenario == 4) { assert(kind < 5); invalid_lookup(kind); }
    else assert(0);
    return 0;
}
