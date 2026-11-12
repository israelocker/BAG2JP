/* Compile the actual plugin against the framework ABI. Runtime APIs are a
 * counted boundary: only activation may write, and only its own Expansion 1
 * clip bank; callbacks never write guest state, and without a captured record
 * the entry callback must not even read it. Named counters must match what the
 * hooks did (one stored/rejected per producer call, one entry_taken per take).
 * A simulated main RAM drives the producer-site capture; it is not evidence
 * of in-game routing. */
#undef NDEBUG
#include <assert.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "mod_plugins.h"
#include "cpu_state.h"

#ifndef GASO_CAUGHT_CLIP_PUBLISHED
#define GASO_CAUGHT_CLIP_PUBLISHED 0
#endif

/* Backing for the largest geometry; live_ram selects 2 MiB retail or 8 MiB. */
#define RAM_BYTES 0x800000u
#define RETAIL_RAM 0x200000u
#define RAM_MASK (RAM_BYTES - 1u)
#define ENTRY 0x8002d06cu
#define PRODUCER 0x8009b5b4u
#define ACTORS 0x8005f808u
#define CONTROLLERS 0x8005f820u
#define CONTROLLER_STRIDE 0x98u
#define TABLE 0x80051458u
#define PENDING 0x8005cf08u
#define PENDING_STRIDE 0x24u
#define STACK 0x801ff000u
#define REQUEST 202u
#define HIT_SLOT 89u
#define HEAT 0
#define STRIKE 1
#define GASO 9
#define REG_V0 2
#define REG_A0 4
#define REG_A1 5
#define REG_A2 6
#define REG_S2 18
#define REG_S4 20
#define REG_S5 21
#define REG_SP 29

#define SCRATCHPAD 0x1f800000u
#define SCRATCHPAD_BYTES 0x400u
#define EXPANSION1 0x9f000000u
#define EXPANSION1_BYTES 0x100000u
/* Arena already used by other plugins, so the bank never starts at 0. */
#define PRIOR_ARENA_BYTES 0x34u

/* The generated authentic bank, to compare what activation copies. */
typedef struct { uint32_t character, offset, bytes; } B1CaughtBankEntry;
#include "bag2jp_caught_bank_data.inc"

static PSXModFunctionEntryCallback entry;
static PSXModFunctionEntryCallback capture_cb;
static PSXModActivationCallback activate;
static unsigned guest_accesses, guest_writes, allocations;
static unsigned bank_ready, bank_unavailable;
static unsigned capture_stored, capture_rejected, entry_taken;
static unsigned log_lines;
static char last_log[160];
static int fail_allocation;
static uint32_t expansion1_used = PRIOR_ARENA_BYTES;
static uint8_t ram[RAM_BYTES];
static uint8_t scratchpad[SCRATCHPAD_BYTES];
static uint8_t expansion1[EXPANSION1_BYTES];
static uint32_t stack = STACK;
static uint32_t live_ram = RETAIL_RAM;
uint32_t memory_get_ram_bytes(void) { return live_ram; }
static int has_version = 1;
static int versions[18][2];
static const uint32_t actor_of[2] = {0x80100000u, 0x80102000u};

int psx_mod_register_function_entry_plugin(
    const char *id, uint32_t address, PSXModFunctionEntryCallback callback) {
    assert(strcmp(id, "bag2jp.gaso_caught") == 0);
    assert(address == ENTRY && !entry && callback);
    entry = callback;
    return 1;
}
int psx_mod_register_instruction_plugin(
    const char *id, uint32_t address, uint32_t expected,
    PSXModFunctionEntryCallback callback) {
    assert(strcmp(id, "bag2jp.gaso_caught_capture") == 0);
    assert(address == PRODUCER && expected == 0xa6a20018u && !capture_cb && callback);
    capture_cb = callback;
    return 1;
}
int psx_mod_register_activation_plugin(const char *id, PSXModActivationCallback cb) {
    assert(strcmp(id, "bag2jp.gaso_caught") == 0);
    activate = cb;
    return 1;
}
/* Bump arena like the runtime: zeroed, never freed, 0 on failure. */
uint32_t psx_mod_alloc_guest_memory(uint32_t size, uint32_t alignment) {
    assert(size == B1CC_BANK_BYTES && alignment == 4u);
    ++allocations;
    if (fail_allocation) return 0;
    const uint32_t start = expansion1_used;
    expansion1_used += size;
    return EXPANSION1 + start;
}
static int in_expansion1(uint32_t address) {
    return address >= EXPANSION1 && address - EXPANSION1 < expansion1_used;
}
void psx_mod_write_byte(uint32_t address, uint8_t value) {
    ++guest_accesses; ++guest_writes;
    /* Only this plugin's own allocation, never the earlier owners' bytes. */
    assert(in_expansion1(address) && address - EXPANSION1 >= PRIOR_ARENA_BYTES);
    expansion1[address - EXPANSION1] = value;
}
/* Reads reach the traced runtime path (MMIO, unmapped_fatal), so only live
 * KSEG0 RAM, the scratchpad and this bank's arena are acceptable addresses. */
static const uint8_t *guest_bytes(uint32_t address, uint32_t bytes) {
    if (address >= 0x80000000u && bytes <= live_ram &&
        address - 0x80000000u <= live_ram - bytes)
        return &ram[address - 0x80000000u];
    if (address >= SCRATCHPAD && address - SCRATCHPAD <= SCRATCHPAD_BYTES - bytes)
        return &scratchpad[address - SCRATCHPAD];
    if (in_expansion1(address) && in_expansion1(address + bytes - 1u))
        return &expansion1[address - EXPANSION1];
    assert(!"guest read outside RAM, scratchpad and bank");
    return NULL;
}
uint32_t psx_mod_read_word(uint32_t address) {
    const uint8_t *p = guest_bytes(address & ~3u, 4u);
    ++guest_accesses;
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}
uint16_t psx_mod_read_half(uint32_t address) {
    const uint8_t *p = guest_bytes(address & ~1u, 2u);
    ++guest_accesses;
    return (uint16_t)(p[0] | p[1] << 8);
}
uint8_t psx_mod_read_byte(uint32_t address) {
    ++guest_accesses;
    return *guest_bytes(address, 1u);
}
void psx_mod_write_word(uint32_t address, uint32_t value) {
    (void)address; (void)value; ++guest_accesses; ++guest_writes;
}
void psx_mod_write_half(uint32_t address, uint16_t value) {
    (void)address; (void)value; ++guest_accesses; ++guest_writes;
}
void psx_mod_counter_add(const char *name, uint32_t delta) {
    assert(delta == 1u);
    if (strcmp(name, "gaso_caught.bank_ready") == 0) ++bank_ready;
    else if (strcmp(name, "gaso_caught.bank_unavailable") == 0) ++bank_unavailable;
    else if (strcmp(name, "gaso_caught.capture_stored") == 0) ++capture_stored;
    else if (strcmp(name, "gaso_caught.capture_rejected") == 0) ++capture_rejected;
    else if (strcmp(name, "gaso_caught.entry_taken") == 0) ++entry_taken;
    else assert(!"unexpected counter");
}
/* Mirrors every counted event to the versions log; keep the last line. */
void b1v_log(const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    const int n = vsnprintf(last_log, sizeof last_log, fmt, ap);
    va_end(ap);
    assert(n > 0 && (size_t)n < sizeof last_log);
    ++log_lines;
}
int bag2jp_bag1_has_version(int chr) {
    return has_version && chr == GASO;
}
int bag2jp_bag1_get_version(int chr, int side) {
    assert(chr >= 0 && chr < 18 && side >= 0 && side < 2);
    return versions[chr][side];
}

static void put_word(uint32_t address, uint32_t value) {
    const uint32_t o = address & RAM_MASK;
    for (unsigned i = 0; i < 4; ++i) ram[o + i] = (uint8_t)(value >> (8 * i));
}

/* Original code sites, main actors and the 202 table rows for Heat/Strike/Gas-O. */
static void setup_ram(int side0_character, int side1_character) {
    memset(ram, 0, sizeof ram);
    put_word(0x80010ce0u, 0x8008f890u);
    put_word(0x8009b5acu, 0x90420000u);
    put_word(0x8009b5b0u, 0x00000000u);
    put_word(PRODUCER, 0xa6a20018u);
    const int characters[2] = {side0_character, side1_character};
    for (uint32_t side = 0; side < 2; ++side) {
        put_word(ACTORS + 8u * side, actor_of[side]);
        ram[(actor_of[side] + 4u) & RAM_MASK] = (uint8_t)characters[side];
        ram[(actor_of[side] + 5u) & RAM_MASK] = (uint8_t)side;
        put_word(CONTROLLERS + CONTROLLER_STRIDE * side, actor_of[side]);
    }
    ram[(TABLE + 2u * HEAT) & RAM_MASK] = REQUEST;
    ram[(TABLE + 2u * STRIKE) & RAM_MASK] = REQUEST;
    ram[(TABLE + 2u * GASO) & RAM_MASK] = REQUEST;
}

/* Run the producer hook with explicit registers and stack flag. Every call is
 * counted exactly once, as stored or rejected; the result says which. */
static int publish_with(uint32_t request, uint32_t source, uint32_t recipient,
                        uint32_t pending, uint8_t flag) {
    CPUState cpu, before;
    memset(&cpu, 0x5a, sizeof cpu);
    cpu.gpr[REG_V0] = request;
    cpu.gpr[REG_S2] = source;
    cpu.gpr[REG_S4] = recipient;
    cpu.gpr[REG_S5] = pending;
    cpu.gpr[REG_SP] = stack;
    if (stack >= SCRATCHPAD && stack < SCRATCHPAD + SCRATCHPAD_BYTES)
        scratchpad[stack - SCRATCHPAD + 0x30u + (recipient & 1u)] = flag;
    else
        ram[(stack + 0x30u + (recipient & 1u)) & RAM_MASK] = flag;
    memcpy(&before, &cpu, sizeof cpu);
    const unsigned writes = guest_writes, allocs = allocations;
    const unsigned stored = capture_stored, rejected = capture_rejected;
    const unsigned taken = entry_taken, lines = log_lines;
    capture_cb(&cpu, PRODUCER);
    assert(memcmp(&cpu, &before, sizeof cpu) == 0);
    assert(guest_writes == writes && allocations == allocs);
    assert(entry_taken == taken);
    assert(capture_stored + capture_rejected == stored + rejected + 1u);
    assert(log_lines == lines + 1u);
    assert(strstr(last_log, capture_stored != stored ? " stored" : " rejected: ") != NULL);
    return capture_stored != stored;
}

/* Run the producer hook as the original publishes request202 to recipient. */
static int publish(uint32_t source, uint32_t recipient) {
    return publish_with(REQUEST, source, recipient, PENDING + PENDING_STRIDE * recipient,
                 source == recipient ? 2 : 1);
}

/* Probe without consuming: an entry naming no actor reads guest RAM only
 * when some record is stored, so the default build can observe captures. */
static int recorded(void) {
    CPUState cpu, before;
    const uint32_t accesses = guest_accesses;
    memset(&cpu, 0xa5, sizeof cpu);
    cpu.gpr[REG_A0] = 0x80000000u;
    cpu.gpr[REG_A1] = 1;
    cpu.gpr[REG_A2] = HIT_SLOT;
    memcpy(&before, &cpu, sizeof cpu);
    const unsigned taken = entry_taken, lines = log_lines;
    entry(&cpu, ENTRY);
    assert(memcmp(&cpu, &before, sizeof cpu) == 0 && entry_taken == taken);
    assert(log_lines == lines);
    return guest_accesses != accesses;
}

/* Enter the controller; return 1 when only a2 became slot1, 0 when untouched.
 * A redirect is always a counted take; the caller checks takes that leave a2. */
static int enter(uint32_t controller_side, uint32_t mode, uint32_t slot) {
    CPUState cpu, before;
    memset(&cpu, 0xa5, sizeof cpu);
    cpu.gpr[REG_A0] = CONTROLLERS + CONTROLLER_STRIDE * controller_side;
    cpu.gpr[REG_A1] = mode;
    cpu.gpr[REG_A2] = slot;
    memcpy(&before, &cpu, sizeof cpu);
    const unsigned writes = guest_writes, allocs = allocations;
    const unsigned stored = capture_stored, rejected = capture_rejected;
    const unsigned taken = entry_taken, lines = log_lines;
    entry(&cpu, ENTRY);
    assert(guest_writes == writes && allocations == allocs);
    assert(capture_stored == stored && capture_rejected == rejected);
    assert(entry_taken == taken || entry_taken == taken + 1u);
    assert(log_lines == lines + (entry_taken - taken));
    if (entry_taken != taken) assert(strstr(last_log, "entry taken") != NULL);
    if (memcmp(&cpu, &before, sizeof cpu) == 0) return 0;
    assert(entry_taken == taken + 1u);
    before.gpr[REG_A2] = 1;
    assert(memcmp(&cpu, &before, sizeof cpu) == 0);
    return 1;
}

static void call_matrix(void) {
    const unsigned accesses = guest_accesses, allocs = allocations;
    const unsigned taken = entry_taken, lines = log_lines;
    const uint32_t actors[] = {0, 0x80090000u, 0x801ffffcu, 0x80400000u, 0xffffffffu};
    const uint32_t slots[] = {1, 73, 89, 90, 202, 0xffffffffu};
    for (unsigned a = 0; a < sizeof actors / sizeof *actors; ++a) {
        for (unsigned s = 0; s < sizeof slots / sizeof *slots; ++s) {
            for (uint32_t mode = 0; mode < 4; ++mode) {
                CPUState cpu, before;
                memset(&cpu, 0xa5, sizeof cpu);
                cpu.gpr[REG_A0] = actors[a]; cpu.gpr[REG_A1] = mode; cpu.gpr[REG_A2] = slots[s];
                memcpy(&before, &cpu, sizeof cpu);
                entry(&cpu, ENTRY);
                assert(memcmp(&cpu, &before, sizeof cpu) == 0);
                assert(guest_accesses == accesses && allocations == allocs);
                assert(entry_taken == taken && log_lines == lines);
            }
        }
    }
}

/* Repeated activation (one per session) prepares the process-lifetime bank:
 * one allocation and one copy, then only re-verification. */
static void activation_prepares_bank_once(void) {
    assert(activate);
    for (unsigned cycle = 0; cycle < 3; ++cycle) {
        activate();
        assert(allocations == 1);
        assert(expansion1_used == PRIOR_ARENA_BYTES + B1CC_BANK_BYTES);
        assert(guest_writes == B1CC_BANK_BYTES);
        assert(memcmp(expansion1 + PRIOR_ARENA_BYTES, b1cc_data, B1CC_BANK_BYTES) == 0);
        assert(bank_ready == cycle + 1u && bank_unavailable == 0);
        assert(log_lines == cycle + 1u && strstr(last_log, "clip bank ready at 9f0000") != NULL);
        call_matrix();
    }
}

/* A failed allocation is terminal: no guest write and no retry. */
static void failed_allocation_is_not_retried(void) {
    fail_allocation = 1;
    for (unsigned cycle = 0; cycle < 3; ++cycle) {
        activate();
        assert(allocations == 1 && guest_writes == 0 && guest_accesses == 0);
        assert(bank_ready == 0 && bank_unavailable == cycle + 1u);
        assert(log_lines == cycle + 1u &&
               strstr(last_log, "clip bank unavailable at 00000000") != NULL);
        call_matrix();
    }
}

/* A corrupted or restored-different arena is reported, never repaired. */
static void corruption_is_reported_not_repaired(void) {
    activate();
    assert(bank_ready == 1);
    const uint32_t clip = 700u;   /* Gas-O clip offset in the bank */
    uint8_t *const byte = &expansion1[PRIOR_ARENA_BYTES + clip];
    *byte ^= 0xffu;
    activate();
    assert(allocations == 1 && guest_writes == B1CC_BANK_BYTES);
    assert(*byte == (uint8_t)(b1cc_data[clip] ^ 0xffu));
    assert(bank_ready == 1 && bank_unavailable == 1);
    assert(strstr(last_log, "clip bank unavailable at 9f0000") != NULL);
    /* A savestate restoring the authentic bytes makes it ready again. */
    *byte = b1cc_data[clip];
    activate();
    assert(allocations == 1 && guest_writes == B1CC_BANK_BYTES);
    assert(bank_ready == 2 && bank_unavailable == 1);
    call_matrix();
}

/* Heat/Strike share request202; Gas-O BAG2, reflected Gas-O and a disabled
 * version table must not redirect either. Every source sides with every rival. */
static void foreign_sources_never_redirect(void) {
    const int sources[] = {HEAT, STRIKE, GASO};
    for (unsigned s = 0; s < sizeof sources / sizeof *sources; ++s) {
        for (uint32_t source_side = 0; source_side < 2; ++source_side) {
            for (unsigned variant = 0; variant < 3; ++variant) {
                const int gaso = sources[s] == GASO;
                /* variant 0: BAG1 picked; 1: BAG2 picked; 2: BAG1 but no version table */
                if (!gaso && variant) continue;
                /* The Gas-O option is per side, not per played character: a
                 * Heat/Strike attacker may sit on a side whose Gas-O is BAG1,
                 * so only the source character check can reject it. */
                memset(versions, 0, sizeof versions);
                versions[GASO][source_side] = !gaso || variant != 1;
                has_version = variant != 2;
                setup_ram(source_side ? GASO : sources[s], source_side ? sources[s] : GASO);
                if (gaso && variant == 0) {
                    /* Reflected Gas-O publication to its own side. */
                    assert(!publish(source_side, source_side));
                    assert(strstr(last_log, "rejected: reflected") != NULL);
                    assert(!recorded());
                    for (uint32_t c = 0; c < 2; ++c) assert(!enter(c, 1, HIT_SLOT));
                    continue;
                }
                assert(!publish(source_side, source_side ^ 1u));
                assert(strstr(last_log, gaso ? "rejected: not BAG1" : "rejected: not Gas-O") != NULL);
                assert(!recorded());
                for (uint32_t c = 0; c < 2; ++c) assert(!enter(c, 1, HIT_SLOT));
            }
        }
    }
    has_version = 1;
}

/* A direct Gas-O BAG1 publication redirects once, only for the recipient's
 * main controller at mode 1/slot 89, and never while no clip is published. */
static void gaso_redirects_once(void) {
    for (uint32_t source_side = 0; source_side < 2; ++source_side) {
        const uint32_t recipient = source_side ^ 1u;
        memset(versions, 0, sizeof versions);
        versions[GASO][source_side] = 1;
        setup_ram(source_side ? HEAT : GASO, source_side ? GASO : HEAT);
        assert(publish(source_side, recipient));
        assert(recorded());
        const unsigned taken = entry_taken;
        assert(!enter(source_side, 1, HIT_SLOT));   /* attacker's controller */
        assert(!enter(recipient, 0, HIT_SLOT));     /* other mode */
        assert(!enter(recipient, 1, HIT_SLOT + 1)); /* exit slot 90 */
        assert(recorded() && entry_taken == taken);
        assert(enter(recipient, 1, HIT_SLOT) == GASO_CAUGHT_CLIP_PUBLISHED);
        assert(entry_taken == taken + 1u);          /* counted in both builds */
        assert(!recorded());                        /* consumed in both builds */
        assert(!enter(recipient, 1, HIT_SLOT));
        assert(entry_taken == taken + 1u);

        /* Every rejected later publication to the same recipient supersedes
         * the stored record. */
        const uint32_t pending = PENDING + PENDING_STRIDE * recipient;
        static const char *const reasons[] = {
            "rejected: request", "rejected: source side", "rejected: pending",
            "rejected: stack flag", "rejected: code drift", "rejected: not Gas-O",
        };
        char stored_line[64];
        snprintf(stored_line, sizeof stored_line, "request %u s2=%u -> s4=%u sp=%08x stored",
                 (unsigned)REQUEST, (unsigned)source_side, (unsigned)recipient, (unsigned)STACK);
        for (unsigned rejection = 0; rejection < 6; ++rejection) {
            assert(publish(source_side, recipient));
            assert(strstr(last_log, stored_line) != NULL);
            assert(recorded());
            switch (rejection) {
            case 0: assert(!publish_with(REQUEST + 1u, source_side, recipient, pending, 1)); break;
            case 1: assert(!publish_with(REQUEST, 2u, recipient, pending, 1)); break;
            case 2: assert(!publish_with(REQUEST, source_side, recipient, pending + 4u, 1)); break;
            case 3: assert(!publish_with(REQUEST, source_side, recipient, pending, 2)); break;
            case 4:
                put_word(PRODUCER, 0);
                assert(!publish(source_side, recipient));
                put_word(PRODUCER, 0xa6a20018u);
                break;
            default:
                ram[(actor_of[source_side] + 4u) & RAM_MASK] = HEAT;
                assert(!publish(source_side, recipient));
                ram[(actor_of[source_side] + 4u) & RAM_MASK] = GASO;
                break;
            }
            assert(strstr(last_log, reasons[rejection]) != NULL);
            assert(!recorded());
            assert(!enter(recipient, 1, HIT_SLOT));
        }
    }
}

/* With the bank prepared, capture and entry still neither write nor
 * allocate, and leave the bank bytes untouched. */
static void prepared_bank_keeps_hooks_read_only(void) {
    activate();
    assert(bank_ready == 1 && allocations == 1);
    const unsigned writes = guest_writes;
    foreign_sources_never_redirect();
    gaso_redirects_once();
    assert(guest_writes == writes && allocations == 1);
    assert(memcmp(expansion1 + PRIOR_ARENA_BYTES, b1cc_data, B1CC_BANK_BYTES) == 0);
    activate();
    assert(bank_ready == 2 && bank_unavailable == 0);
}

/* Hook reads go through the traced runtime path, so an actor or stack pointer
 * outside retail RAM (or the scratchpad for sp) is rejected before any read;
 * the strict read stubs fail on MMIO, unmapped or past-the-end addresses. */
static void unsafe_pointers_are_never_read(void) {
    const uint32_t bad_actors[] = {0x1f801070u, 0x80200000u, 0x801ffffcu, 0xfffffffcu};
    const uint32_t bad_stacks[] = {0x1f801000u, 0x801fffd0u, 0x00000000u, 0xfffffff0u};
    memset(versions, 0, sizeof versions);
    versions[GASO][0] = 1;
    for (unsigned i = 0; i < sizeof bad_actors / sizeof *bad_actors; ++i) {
        for (uint32_t side = 0; side < 2; ++side) {
            setup_ram(GASO, HEAT);
            assert(publish(0, 1) && recorded());
            put_word(ACTORS + 8u * side, bad_actors[i]);
            assert(!publish(0, 1));
            assert(strstr(last_log, "rejected: actor pointer") != NULL && !recorded());
        }
    }
    for (unsigned i = 0; i < sizeof bad_stacks / sizeof *bad_stacks; ++i) {
        setup_ram(GASO, HEAT);
        assert(publish(0, 1) && recorded());
        stack = bad_stacks[i];
        assert(!publish(0, 1));
        assert(strstr(last_log, "rejected: stack") != NULL && !recorded());
        stack = STACK;
    }
    /* A scratchpad stack is a valid guest stack. */
    setup_ram(GASO, HEAT);
    stack = SCRATCHPAD + 0x100u;
    assert(publish(0, 1) && recorded());
    stack = STACK;

    /* Any other instruction address is not the producer: no counter, no read. */
    CPUState cpu, before;
    memset(&cpu, 0x5a, sizeof cpu);
    memcpy(&before, &cpu, sizeof cpu);
    const unsigned accesses = guest_accesses;
    const unsigned stored = capture_stored, rejected = capture_rejected, lines = log_lines;
    capture_cb(&cpu, PRODUCER + 4u);
    assert(memcmp(&cpu, &before, sizeof cpu) == 0 && guest_accesses == accesses);
    assert(log_lines == lines);
    assert(capture_stored == stored && capture_rejected == rejected);
}

/* The same KSEG0 stack is valid only while its entire span is live. */
static void stack_range_follows_live_geometry(void) {
    const uint32_t expanded = RAM_BYTES;
    const uint32_t valid_stacks[] = {0x807fff00u, 0x807fffceu, 0x801fffd0u};
    const uint32_t invalid_stacks[] = {0x807fffcfu, 0x80800000u, 0xfffffff0u};
    memset(versions, 0, sizeof versions);
    versions[GASO][0] = versions[GASO][1] = 1;
    live_ram = expanded;
    for (uint32_t source = 0; source < 2; ++source) {
        const uint32_t recipient = source ^ 1u;
        for (unsigned i = 0; i < sizeof valid_stacks / sizeof *valid_stacks; ++i) {
            setup_ram(GASO, GASO);
            stack = valid_stacks[i];
            assert(publish(source, recipient) && recorded());
            const unsigned taken = entry_taken;
            assert(enter(recipient, 1, HIT_SLOT) == GASO_CAUGHT_CLIP_PUBLISHED);
            assert(entry_taken == taken + 1u && !recorded());
        }
        for (unsigned i = 0; i < sizeof invalid_stacks / sizeof *invalid_stacks; ++i) {
            stack = STACK;
            assert(publish(source, recipient) && recorded());
            stack = invalid_stacks[i];
            assert(!publish(source, recipient));
            assert(strstr(last_log, "rejected: stack") != NULL && !recorded());
        }
    }
    live_ram = RETAIL_RAM;
    stack = valid_stacks[0];
    assert(!publish(0, 1));
    assert(strstr(last_log, "rejected: stack") != NULL && !recorded());
    stack = STACK;
    assert(publish(0, 1) && recorded());
}

int main(int argc, char **argv) {
    assert(argc == 2 && entry && capture_cb);
    switch (atoi(argv[1])) {
    case 0:
        call_matrix();
        break;
    case 1:
        activation_prepares_bank_once();
        break;
    case 2:
        foreign_sources_never_redirect();
        break;
    case 3:
        gaso_redirects_once();
        break;
    case 4:
        failed_allocation_is_not_retried();
        break;
    case 5:
        corruption_is_reported_not_repaired();
        break;
    case 6:
        prepared_bank_keeps_hooks_read_only();
        break;
    case 7:
        unsafe_pointers_are_never_read();
        break;
    case 8:
        stack_range_follows_live_geometry();
        break;
    default:
        return 2;
    }
    return 0;
}
