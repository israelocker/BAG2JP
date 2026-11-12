/* Compile the actual plugin against the framework ABI. Runtime APIs are a
 * counted boundary: the quarantined candidate must not write guest state, and
 * without a captured record it must not even read it. A simulated main RAM
 * drives the producer-site capture; it is not evidence of in-game routing. */
#undef NDEBUG
#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "mod_plugins.h"
#include "cpu_state.h"

#ifndef GASO_CAUGHT_CLIP_PUBLISHED
#define GASO_CAUGHT_CLIP_PUBLISHED 0
#endif

#define RAM_BYTES 0x200000u
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

static PSXModFunctionEntryCallback entry;
static PSXModFunctionEntryCallback capture_cb;
static PSXModActivationCallback activate, reset;
static unsigned guest_accesses, guest_writes, allocations;
static uint8_t ram[RAM_BYTES];
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
int psx_mod_register_session_reset_plugin(const char *id, PSXModActivationCallback cb) {
    assert(strcmp(id, "bag2jp.gaso_caught") == 0);
    reset = cb;
    return 1;
}
uint32_t psx_mod_alloc_guest_memory(uint32_t size, uint32_t alignment) {
    (void)size; (void)alignment;
    ++allocations;
    return 0x9f000000u;
}
uint32_t psx_mod_read_word(uint32_t address) {
    const uint32_t o = address & RAM_MASK & ~3u;
    ++guest_accesses;
    return (uint32_t)ram[o] | (uint32_t)ram[o + 1] << 8 |
        (uint32_t)ram[o + 2] << 16 | (uint32_t)ram[o + 3] << 24;
}
uint16_t psx_mod_read_half(uint32_t address) {
    const uint32_t o = address & RAM_MASK & ~1u;
    ++guest_accesses;
    return (uint16_t)(ram[o] | ram[o + 1] << 8);
}
uint8_t psx_mod_read_byte(uint32_t address) {
    ++guest_accesses;
    return ram[address & RAM_MASK];
}
void psx_mod_write_word(uint32_t address, uint32_t value) {
    (void)address; (void)value; ++guest_accesses; ++guest_writes;
}
void psx_mod_write_half(uint32_t address, uint16_t value) {
    (void)address; (void)value; ++guest_accesses; ++guest_writes;
}
void psx_mod_counter_add(const char *name, uint32_t delta) {
    (void)name; (void)delta;
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

/* Run the producer hook with explicit registers and stack flag. */
static void publish_with(uint32_t request, uint32_t source, uint32_t recipient,
                         uint32_t pending, uint8_t flag) {
    CPUState cpu, before;
    memset(&cpu, 0x5a, sizeof cpu);
    cpu.gpr[REG_V0] = request;
    cpu.gpr[REG_S2] = source;
    cpu.gpr[REG_S4] = recipient;
    cpu.gpr[REG_S5] = pending;
    cpu.gpr[REG_SP] = STACK;
    ram[(STACK + 0x30u + (recipient & 1u)) & RAM_MASK] = flag;
    memcpy(&before, &cpu, sizeof cpu);
    capture_cb(&cpu, PRODUCER);
    assert(memcmp(&cpu, &before, sizeof cpu) == 0);
    assert(guest_writes == 0 && allocations == 0);
}

/* Run the producer hook as the original publishes request202 to recipient. */
static void publish(uint32_t source, uint32_t recipient) {
    publish_with(REQUEST, source, recipient, PENDING + PENDING_STRIDE * recipient,
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
    entry(&cpu, ENTRY);
    assert(memcmp(&cpu, &before, sizeof cpu) == 0);
    return guest_accesses != accesses;
}

/* Enter the controller; return 1 when only a2 became slot1, 0 when untouched. */
static int enter(uint32_t controller_side, uint32_t mode, uint32_t slot) {
    CPUState cpu, before;
    memset(&cpu, 0xa5, sizeof cpu);
    cpu.gpr[REG_A0] = CONTROLLERS + CONTROLLER_STRIDE * controller_side;
    cpu.gpr[REG_A1] = mode;
    cpu.gpr[REG_A2] = slot;
    memcpy(&before, &cpu, sizeof cpu);
    entry(&cpu, ENTRY);
    assert(guest_writes == 0 && allocations == 0);
    if (memcmp(&cpu, &before, sizeof cpu) == 0) return 0;
    before.gpr[REG_A2] = 1;
    assert(memcmp(&cpu, &before, sizeof cpu) == 0);
    return 1;
}

static void call_matrix(void) {
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
                assert(guest_accesses == 0 && allocations == 0);
            }
        }
    }
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
                    publish(source_side, source_side);
                    assert(!recorded());
                    for (uint32_t c = 0; c < 2; ++c) assert(!enter(c, 1, HIT_SLOT));
                    continue;
                }
                publish(source_side, source_side ^ 1u);
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
        publish(source_side, recipient);
        assert(recorded());
        assert(!enter(source_side, 1, HIT_SLOT));   /* attacker's controller */
        assert(!enter(recipient, 0, HIT_SLOT));     /* other mode */
        assert(!enter(recipient, 1, HIT_SLOT + 1)); /* exit slot 90 */
        assert(recorded());
        assert(enter(recipient, 1, HIT_SLOT) == GASO_CAUGHT_CLIP_PUBLISHED);
        assert(!recorded());                        /* consumed in both builds */
        assert(!enter(recipient, 1, HIT_SLOT));

        /* Every rejected later publication to the same recipient supersedes
         * the stored record. */
        const uint32_t pending = PENDING + PENDING_STRIDE * recipient;
        for (unsigned rejection = 0; rejection < 6; ++rejection) {
            publish(source_side, recipient);
            assert(recorded());
            switch (rejection) {
            case 0: publish_with(REQUEST + 1u, source_side, recipient, pending, 1); break;
            case 1: publish_with(REQUEST, 2u, recipient, pending, 1); break;
            case 2: publish_with(REQUEST, source_side, recipient, pending + 4u, 1); break;
            case 3: publish_with(REQUEST, source_side, recipient, pending, 2); break;
            case 4:
                put_word(PRODUCER, 0);
                publish(source_side, recipient);
                put_word(PRODUCER, 0xa6a20018u);
                break;
            default:
                ram[(actor_of[source_side] + 4u) & RAM_MASK] = HEAT;
                publish(source_side, recipient);
                ram[(actor_of[source_side] + 4u) & RAM_MASK] = GASO;
                break;
            }
            assert(!recorded());
            assert(!enter(recipient, 1, HIT_SLOT));
        }
    }
}

int main(int argc, char **argv) {
    assert(argc == 2 && entry && capture_cb);
    switch (atoi(argv[1])) {
    case 0:
        call_matrix();
        break;
    case 1:
        for (unsigned cycle = 0; cycle < 3; ++cycle) {
            if (reset) reset();
            if (activate) activate();
            assert(allocations == 0 && guest_accesses == 0);
            call_matrix();
        }
        break;
    case 2:
        foreign_sources_never_redirect();
        break;
    case 3:
        gaso_redirects_once();
        break;
    default:
        return 2;
    }
    return 0;
}
