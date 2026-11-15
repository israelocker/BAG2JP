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
#define RAM_BASE 0x80000000u
#define ENTRY 0x8002d06cu
#define NATIVE_INIT_SITE 0x8002ba18u
#define NATIVE_INIT_WORD 0x0c00b617u
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
#define SECONDARY_EFFECT 0x1724u
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
/* Recipient actor fields and its animation tables (bag2jp_caught_binding.h). */
#define COUNT 0x820u
#define RAW 0x824u
#define LENGTH 0x828u
#define META 0x82cu
#define DECODER 0x830u
#define CURRENT 0x154cu
#define PREVIOUS 0x1550u
#define SLOTS 100u
#define TABLES 0x80110000u                 /* raw, length, metadata per side */
#define EMPTY_WORDS 0x80118000u            /* slot1's original raw target */
#define MOTIONS 0x10u                      /* actor's motion DFS (FUN_80031d3c) */
#define MOTION0_BYTES 8u                   /* entry0 payload before entry1's size */
#define MOTION1_BYTES 4u                   /* entry1 payload: the empty zero word */
#define CLIP_FRAMES 2u

/* Arena already used by other plugins, so the bank never starts at 0. */
#define PRIOR_ARENA_BYTES 0x34u

/* The generated authentic bank, to compare what activation copies. */
typedef struct { uint32_t character, offset, bytes; } B1CaughtBankEntry;
#include "bag2jp_caught_bank_data.inc"

/* Read by the tank visual (bag2jp_gaso_tank.h). */
uint32_t bag2jp_gaso_caught_hits(uint32_t side);
uint32_t bag2jp_gaso_caught_epoch(void);
uint32_t bag2jp_gaso_caught_epoch_hits(uint32_t side);
int bag2jp_gaso_caught_owns_slot1(uint32_t side, uint32_t actor);

static PSXModFunctionEntryCallback entry;
static PSXModFunctionEntryCallback capture_cb;
static PSXModFunctionEntryCallback native_init_cb;
static PSXModActivationCallback activate;
static PSXModActivationCallback session_reset_cb;
static PSXModActivationCallback savestate_cb;
static unsigned guest_accesses, guest_writes, allocations, slot_state_reads;
static unsigned bank_ready, bank_unavailable;
static unsigned capture_stored, capture_rejected, entry_taken;
static unsigned lookup_ready, lookup_rejected;
static unsigned capture_stale;
static unsigned capture_generations;
static unsigned slot1_published, slot1_restored, slot1_dropped, slot1_recovered;
static unsigned log_lines, log_entered, log_restore_refused, log_publish_refused, log_lost;
static unsigned log_reused, log_stale, log_recovered, log_recovery_refused;
static char last_log[256];
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
static uint32_t actor_of[2] = {0x80100000u, 0x80102000u};

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
    if (address == NATIVE_INIT_SITE) {
        assert(strcmp(id, "bag2jp.gaso_caught") == 0);
        assert(expected == NATIVE_INIT_WORD && !native_init_cb && callback);
        native_init_cb = callback;
        return 1;
    }
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
    session_reset_cb = cb;
    return 1;
}
int psx_mod_register_savestate_plugin(const char *id, PSXModActivationCallback cb) {
    assert(strcmp(id, "bag2jp.gaso_caught") == 0);
    savestate_cb = cb;
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
/* Retirement reads of a published recipient: its identity bytes, table
 * pointers, current/previous words and the slot1 tuple at the tables it was
 * published on. The only reads an entry makes for a published slot with no
 * record, so recorded() discounts them. */
static uint32_t table_of(uint32_t side, uint32_t field);
static int is_slot_state(uint32_t address) {
    static const uint32_t fields[] = {4u, 5u, COUNT, RAW, LENGTH, META, CURRENT, PREVIOUS};
    for (uint32_t side = 0; side < 2; ++side) {
        for (unsigned i = 0; i < sizeof fields / sizeof *fields; ++i)
            if (address == actor_of[side] + fields[i]) return 1;
        if (address == table_of(side, RAW) + 4u || address == table_of(side, LENGTH) + 2u ||
            address == table_of(side, META) + 4u) return 1;
    }
    return 0;
}
/* Guest loads are aligned: the plugin must reject odd pointers before reading. */
uint32_t psx_mod_read_word(uint32_t address) {
    assert(address % 4u == 0);
    const uint8_t *p = guest_bytes(address, 4u);
    ++guest_accesses;
    if (is_slot_state(address)) ++slot_state_reads;
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}
uint16_t psx_mod_read_half(uint32_t address) {
    assert(address % 2u == 0);
    const uint8_t *p = guest_bytes(address, 2u);
    ++guest_accesses;
    if (is_slot_state(address)) ++slot_state_reads;
    return (uint16_t)(p[0] | p[1] << 8);
}
uint8_t psx_mod_read_byte(uint32_t address) {
    ++guest_accesses;
    if (is_slot_state(address)) ++slot_state_reads;
    return *guest_bytes(address, 1u);
}
/* Only slot1 tuples and the exact selector1->0 halfword on a main actor are
 * permitted. Never pending+0x18 or a neighbouring actor field. */
static uint32_t ram_word(uint32_t address);
static int is_slot1_entry(uint32_t address, unsigned width) {
    for (uint32_t i = 0; i < 4u; ++i) {
        const uint32_t actor = ram_word(ACTORS + 4u * i);
        if (!actor) continue;
        if ((width == 4u && (address == ram_word(actor + RAW) + 4u ||
                             address == ram_word(actor + META) + 4u)) ||
            (width == 2u && address == ram_word(actor + LENGTH) + 2u)) return 1;
    }
    return 0;
}
static int is_secondary_clear(uint32_t address, uint32_t value, unsigned width) {
    if (!GASO_CAUGHT_CLIP_PUBLISHED || width != 2u || value != 0u) return 0;
    for (uint32_t side = 0; side < 2u; ++side) {
        const uint32_t actor = ram_word(ACTORS + 8u * side);
        if (actor && address == actor + SECONDARY_EFFECT &&
            (ram_word(address) & 0xffffu) == 1u) return 1;
    }
    return 0;
}
static void write_main_ram(uint32_t address, uint32_t value, unsigned width) {
    ++guest_accesses; ++guest_writes;
    assert(address % width == 0 && (is_slot1_entry(address, width) ||
                                   is_secondary_clear(address, value, width)));
    uint8_t *const p = (uint8_t *)guest_bytes(address, width);
    for (unsigned i = 0; i < width; ++i) p[i] = (uint8_t)(value >> (8 * i));
}
void psx_mod_write_word(uint32_t address, uint32_t value) {
    write_main_ram(address, value, 4u);
}
void psx_mod_write_half(uint32_t address, uint16_t value) {
    write_main_ram(address, value, 2u);
}
void psx_mod_counter_add(const char *name, uint32_t delta) {
    assert(delta == 1u);
    if (strcmp(name, "gaso_caught.bank_ready") == 0) ++bank_ready;
    else if (strcmp(name, "gaso_caught.bank_unavailable") == 0) ++bank_unavailable;
    else if (strcmp(name, "gaso_caught.capture_stored") == 0) ++capture_stored;
    else if (strcmp(name, "gaso_caught.capture_rejected") == 0) ++capture_rejected;
    else if (strcmp(name, "gaso_caught.capture_stale") == 0) ++capture_stale;
    else if (strcmp(name, "gaso_caught.capture_generation") == 0) ++capture_generations;
    else if (strcmp(name, "gaso_caught.entry_taken") == 0) ++entry_taken;
    else if (strcmp(name, "gaso_caught.lookup_ready") == 0) ++lookup_ready;
    else if (strcmp(name, "gaso_caught.lookup_rejected") == 0) ++lookup_rejected;
    else if (strcmp(name, "gaso_caught.slot1_published") == 0) ++slot1_published;
    else if (strcmp(name, "gaso_caught.slot1_restored") == 0) ++slot1_restored;
    else if (strcmp(name, "gaso_caught.slot1_recovered") == 0) ++slot1_recovered;
    else if (strcmp(name, "gaso_caught.slot1_lost") == 0 ||
             strcmp(name, "gaso_caught.slot1_abandoned") == 0) ++slot1_dropped;
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
    if (strstr(last_log, "slot1 entered")) ++log_entered;
    if (strstr(last_log, "restore refused")) ++log_restore_refused;
    if (strstr(last_log, "publish refused") || strstr(last_log, "reuse refused")) ++log_publish_refused;
    if (strstr(last_log, "slot1 lost") || strstr(last_log, "restore abandoned")) ++log_lost;
    if (strstr(last_log, "slot1 reused")) ++log_reused;
    if (strstr(last_log, "capture stale")) ++log_stale;
    if (strstr(last_log, "slot1 recovered")) ++log_recovered;
    if (strstr(last_log, "slot1 recovery refused")) ++log_recovery_refused;
}
int bag2jp_bag1_has_version(int chr) {
    return has_version && (chr == GASO || chr == HEAT || chr == STRIKE);
}
int bag2jp_bag1_get_version(int chr, int side) {
    assert(chr >= 0 && chr < 18 && side >= 0 && side < 2);
    return versions[chr][side];
}
/* The tank's cue player lives in bag2jp_bag1_versions.c (tested there). */
void bag2jp_gaso_tank_play_cues(struct CPUState *cpu, uint32_t return_address) {
    assert(cpu && return_address == ENTRY);
}

static void put_byte(uint32_t address, uint32_t value) {
    ram[address & RAM_MASK] = (uint8_t)value;
}
static void put_word(uint32_t address, uint32_t value) {
    const uint32_t o = address & RAM_MASK;
    for (unsigned i = 0; i < 4; ++i) ram[o + i] = (uint8_t)(value >> (8 * i));
}
static uint32_t ram_word(uint32_t address) {
    const uint32_t o = address & RAM_MASK;
    return (uint32_t)ram[o] | (uint32_t)ram[o + 1] << 8 |
           (uint32_t)ram[o + 2] << 16 | (uint32_t)ram[o + 3] << 24;
}
static uint32_t ram_half(uint32_t address) {
    const uint32_t o = address & RAM_MASK;
    return (uint32_t)ram[o] | (uint32_t)ram[o + 1] << 8;
}
static uint32_t table_of(uint32_t side, uint32_t field) {
    return TABLES + 0x1000u * (3u * side + (field - RAW) / 4u);
}
static uint32_t empty_of(uint32_t side) { return EMPTY_WORDS + 0x40u * side; }
/* Native DFS [size][payload]...: raw[0] = motions+4, raw[1] = empty word. */
static uint32_t motions_of(uint32_t side) {
    return empty_of(side) - 8u - MOTION0_BYTES;
}

/* Slot1 of the recipient side: raw word, length half and metadata word. */
typedef struct { uint32_t raw, length, meta; } Slot1;
static Slot1 slot1_of(uint32_t side) {
    const uint32_t actor = actor_of[side];
    return (Slot1){ram_word(ram_word(actor + RAW) + 4u), ram_half(ram_word(actor + LENGTH) + 2u),
                   ram_word(ram_word(actor + META) + 4u)};
}
static int slot1_empty(uint32_t side) {
    const Slot1 s = slot1_of(side);
    return s.raw == empty_of(side) && s.length == 0 && s.meta == 0;
}
/* A published tuple: the bank clip of that character, 2 frames, its info block. */
static int slot1_holds_clip(uint32_t side, uint32_t character) {
    const Slot1 s = slot1_of(side);
    for (unsigned i = 0; i < sizeof b1cc_entries / sizeof *b1cc_entries; ++i) {
        const B1CaughtBankEntry *e = &b1cc_entries[i];
        const uint32_t clip = EXPANSION1 + PRIOR_ARENA_BYTES + e->offset;
        if (e->character == character)
            return s.raw == clip && s.length == CLIP_FRAMES &&
                   s.meta > clip && s.meta < clip + e->bytes;
    }
    return 0;
}
static void set_slot_state(uint32_t side, uint32_t current, uint32_t previous) {
    put_word(actor_of[side] + CURRENT, current);
    put_word(actor_of[side] + PREVIOUS, previous);
}

/* Original code sites, main actors and the 202 table rows for Heat/Strike/Gas-O.
 * Each actor owns SLOTS entries of distinct tables, slot1 holding the empty
 * tuple (a pointer to a zero word, 0, 0) and current = previous = 0. New RAM
 * is a new session, so the plugin's per-session state is reset too. */
static void setup_ram(int side0_character, int side1_character) {
    if (session_reset_cb) session_reset_cb();
    memset(ram, 0, sizeof ram);
    put_word(0x80010ce0u, 0x8008f890u);
    put_word(0x8009b5acu, 0x90420000u);
    put_word(0x8009b5b0u, 0x00000000u);
    put_word(PRODUCER, 0xa6a20018u);
    put_word(NATIVE_INIT_SITE, NATIVE_INIT_WORD);
    const int characters[2] = {side0_character, side1_character};
    for (uint32_t side = 0; side < 2; ++side) {
        put_word(ACTORS + 8u * side, actor_of[side]);
        ram[(actor_of[side] + 4u) & RAM_MASK] = (uint8_t)characters[side];
        ram[(actor_of[side] + 5u) & RAM_MASK] = (uint8_t)side;
        put_word(CONTROLLERS + CONTROLLER_STRIDE * side, actor_of[side]);
        put_word(actor_of[side] + COUNT, SLOTS);
        for (uint32_t field = RAW; field <= META; field += 4u)
            put_word(actor_of[side] + field, table_of(side, field));
        put_word(actor_of[side] + MOTIONS, motions_of(side));
        put_word(motions_of(side), MOTION0_BYTES);
        put_word(motions_of(side) + 4u + MOTION0_BYTES, MOTION1_BYTES);
        put_word(table_of(side, RAW), motions_of(side) + 4u);
        put_word(table_of(side, RAW) + 4u, empty_of(side));
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
 * when some record is stored, so the default build can observe captures.
 * A published slot adds its retirement reads, which are not a record. */
static int recorded(void) {
    CPUState cpu, before;
    const uint32_t accesses = guest_accesses - slot_state_reads;
    memset(&cpu, 0xa5, sizeof cpu);
    cpu.gpr[REG_A0] = 0x80000000u;
    cpu.gpr[REG_A1] = 1;
    cpu.gpr[REG_A2] = HIT_SLOT;
    memcpy(&before, &cpu, sizeof cpu);
    const unsigned taken = entry_taken, lines = log_lines;
    entry(&cpu, ENTRY);
    assert(memcmp(&cpu, &before, sizeof cpu) == 0 && entry_taken == taken);
    assert(log_lines == lines);
    return guest_accesses - slot_state_reads != accesses;
}

/* Enter the controller; return 1 when only a2 became slot1, 0 when untouched.
 * A redirect is always a counted take onto a slot1 that holds a clip; the
 * caller checks takes that leave a2. Retirement runs first, then the take. */
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
    const unsigned pub_before = slot1_published, rest_before = slot1_restored;
    const unsigned entered = log_entered, refused = log_restore_refused, lost = log_lost;
    const unsigned publish_refused = log_publish_refused, dropped = slot1_dropped;
    const unsigned reused_before = log_reused, stale_before = log_stale;
    const uint32_t effect_before = ram_word(actor_of[controller_side] + SECONDARY_EFFECT);
    const Slot1 other_before = slot1_of(controller_side ^ 1u);
    entry(&cpu, ENTRY);
    const Slot1 other_after = slot1_of(controller_side ^ 1u);
    assert(slot1_dropped - dropped == log_lost - lost);  /* one counter per lost/abandoned line */
    const unsigned took = entry_taken == taken + 1u ? 1u : 0u;
    const unsigned published = slot1_published - pub_before;
    const unsigned restored = slot1_restored - rest_before;
    const unsigned retire_logs = (log_entered - entered) + (log_restore_refused - refused) +
                                 (log_lost - lost);
    const unsigned publish_logs = log_publish_refused - publish_refused;
    const unsigned reused = log_reused - reused_before, stale = log_stale - stale_before;
    const uint32_t effect_after = ram_word(actor_of[controller_side] + SECONDARY_EFFECT);
    const unsigned cleared = (effect_before & 0xffffu) == 1u &&
                             effect_after == (effect_before & 0xffff0000u);
    if (cleared) assert(took && GASO_CAUGHT_CLIP_PUBLISHED && cpu.gpr[REG_A2] == 1u);
    /* Tuples use three writes; a cleared owned effect uses one exact halfword. */
    assert(guest_writes == writes + (published + restored) * 3u + cleared && allocations == allocs);
    assert(capture_stored == stored && capture_rejected == rejected);
    assert(entry_taken == taken || entry_taken == taken + 1u);
    assert(published + publish_logs <= took);
    if (!GASO_CAUGHT_CLIP_PUBLISHED)
        assert(!published && !restored && !retire_logs && !publish_logs);
    /* One line per take, publication, refusal, restore and first slot1 sighting. */
    assert(log_lines == lines + took + published + publish_logs + restored + retire_logs + reused + stale);
    if (took)
        assert(strstr(last_log, published ? "slot1 published"
                      : publish_logs ? " refused" : reused ? "slot1 reused" : "entry taken") != NULL);
    else if (stale)
        assert(strstr(last_log, "capture stale") != NULL);
    else if (restored)
        assert(strstr(last_log, "slot1 restored") != NULL);
    if (memcmp(&cpu, &before, sizeof cpu) == 0) return 0;
    assert(took && GASO_CAUGHT_CLIP_PUBLISHED);
    /* The take never writes the other side; only its own retirement may empty it. */
    assert((other_before.raw == other_after.raw && other_before.length == other_after.length &&
            other_before.meta == other_after.meta) ||
           (restored && slot1_empty(controller_side ^ 1u)));
    assert(slot1_holds_clip(controller_side, ram[(actor_of[controller_side] + 4u) & RAM_MASK]));
    before.gpr[REG_A2] = 1;
    assert(memcmp(&cpu, &before, sizeof cpu) == 0);
    return 1;
}

/* What the entry does after a stored take: redirect only in the published
 * build, once the bank is prepared and the recipient picked BAG1. */
static int expect_redirect(int recipient_bag1) {
    return GASO_CAUGHT_CLIP_PUBLISHED && bank_ready && recipient_bag1;
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
 * main controller at mode 1/slot 89, and never while no clip is published:
 * without a prepared bank the take publishes nothing and leaves a2. */
static void gaso_redirects_once(void) {
    for (uint32_t source_side = 0; source_side < 2; ++source_side) {
        const uint32_t recipient = source_side ^ 1u;
        memset(versions, 0, sizeof versions);
        versions[GASO][source_side] = 1;
        versions[HEAT][recipient] = 1;
        setup_ram(source_side ? HEAT : GASO, source_side ? GASO : HEAT);
        assert(publish(source_side, recipient));
        assert(recorded());
        const unsigned taken = entry_taken;
        const uint32_t hits = bag2jp_gaso_caught_hits(recipient);
        const uint32_t source_hits = bag2jp_gaso_caught_hits(source_side);
        assert(!enter(source_side, 1, HIT_SLOT));   /* attacker's controller */
        assert(!enter(recipient, 0, HIT_SLOT));     /* other mode */
        assert(!enter(recipient, 1, HIT_SLOT + 1)); /* exit slot 90 */
        assert(recorded() && entry_taken == taken);
        assert(bag2jp_gaso_caught_hits(recipient) == hits);
        assert(slot1_empty(recipient));
        const int redirect = expect_redirect(1);
        assert(!bag2jp_gaso_caught_owns_slot1(recipient,
                actor_of[recipient]));
        assert(enter(recipient, 1, HIT_SLOT) == redirect);
        assert(redirect ? slot1_holds_clip(recipient, HEAT) : slot1_empty(recipient));
        const unsigned ownership_writes = guest_writes;
        assert(bag2jp_gaso_caught_owns_slot1(recipient,
                actor_of[recipient]) == redirect);
        assert(!bag2jp_gaso_caught_owns_slot1(2u, 0u));
        assert(!bag2jp_gaso_caught_owns_slot1(recipient, 0u));
        assert(guest_writes == ownership_writes);
        assert(entry_taken == taken + 1u);          /* counted in both builds */
        assert(bag2jp_gaso_caught_hits(recipient) == hits + 1u); /* drops the tank */
        assert(bag2jp_gaso_caught_hits(source_side) == source_hits);
        assert(!recorded());                        /* consumed in both builds */
        assert(!enter(recipient, 1, HIT_SLOT));
        assert(entry_taken == taken + 1u && bag2jp_gaso_caught_hits(recipient) == hits + 1u);

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
    assert(guest_writes == writes + (GASO_CAUGHT_CLIP_PUBLISHED ? 6u : 0u) &&
           allocations == 1);
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
            assert(enter(recipient, 1, HIT_SLOT) == expect_redirect(1));
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

/* Exercise the real immutable bank through the recipient entry, not a lookup
 * stub: the attacker's BAG1 choice must never authorize a BAG2 recipient. */
static void recipient_lookup_is_read_only(void) {
    activate();
    for (uint32_t source = 0; source < 2; ++source) {
        const uint32_t recipient = source ^ 1u;
        for (unsigned i = 0; i < sizeof b1cc_entries / sizeof *b1cc_entries; ++i) {
            const B1CaughtBankEntry *expected = &b1cc_entries[i];
            for (unsigned version = 0; version < 2; ++version) {
                memset(versions, 0, sizeof versions);
                versions[GASO][source] = 1;
                versions[expected->character][recipient] = (int)version;
                setup_ram(source ? (int)expected->character : GASO,
                          source ? GASO : (int)expected->character);
                assert(publish(source, recipient));
                const unsigned ready = lookup_ready, rejected = lookup_rejected;
                const unsigned writes = guest_writes;
                const int redirect = expect_redirect((int)version);
                assert(enter(recipient, 1, HIT_SLOT) == redirect);
                assert(lookup_ready == ready + version);
                assert(lookup_rejected == rejected + (1u - version));
                assert(redirect ? slot1_holds_clip(recipient, expected->character)
                                : slot1_empty(recipient));
                char outcome[128];
                snprintf(outcome, sizeof outcome,
                         "lookup char=%u version=%u %s clip=%08x bytes=%u",
                         (unsigned)expected->character, version, version ? "ready" : "rejected",
                         version ? EXPANSION1 + PRIOR_ARENA_BYTES + expected->offset : 0u,
                         version ? expected->bytes : 0u);
                if (!redirect)
                    assert(strstr(last_log, outcome) != NULL);
                assert(!enter(recipient, 1, HIT_SLOT));
                assert(lookup_ready == ready + version &&
                       lookup_rejected == rejected + (1u - version));
                /* Re-read the recipient choice at entry, in either direction;
                 * the attacker's BAG1 choice stays unchanged throughout. A
                 * second take while the clip is still published reuses it. */
                versions[expected->character][recipient] = (int)(version ^ 1u);
                assert(publish(source, recipient));
                versions[expected->character][recipient] = (int)version;
                assert(enter(recipient, 1, HIT_SLOT) == redirect);
                assert(lookup_ready == ready + 2u * version);
                assert(lookup_rejected == rejected + 2u * (1u - version));
                assert(strstr(last_log, redirect ? "slot1 reused" : outcome) != NULL);
                assert(guest_writes == writes + (redirect ? 3u : 0u));
            }
        }
    }
    /* Unsupported character, missing capability, then a changed bank byte. */
    for (unsigned failure = 0; failure < 4; ++failure) {
        const int character = failure == 0 ? 2 : failure == 1 ? 255 : HEAT;
        setup_ram(GASO, character);
        memset(versions, 0, sizeof versions);
        versions[GASO][0] = versions[HEAT][1] = 1;
        assert(publish(0, 1));
        if (failure == 2) has_version = 0;
        if (failure == 3) expansion1[PRIOR_ARENA_BYTES] ^= 1u;
        const unsigned ready = lookup_ready, rejected = lookup_rejected, stale = capture_stale;
        assert(!enter(1, 1, HIT_SLOT) && slot1_empty(1));
        if (failure == 2) {
            /* Capability removal also revokes the captured attacker's authority
             * before the recipient lookup. No lookup is authorized in this case. */
            assert(lookup_ready == ready && lookup_rejected == rejected);
            assert(capture_stale == stale + 1u && strstr(last_log, "capture stale"));
        } else {
            assert(lookup_ready == ready && lookup_rejected == rejected + 1u);
            assert(strstr(last_log, "rejected clip=00000000 bytes=0") != NULL);
        }
        has_version = 1;
        if (failure == 3) expansion1[PRIOR_ARENA_BYTES] ^= 1u;
    }
    const unsigned entries = sizeof b1cc_entries / sizeof *b1cc_entries;
    assert(allocations == 1 && guest_writes == B1CC_BANK_BYTES +
           (GASO_CAUGHT_CLIP_PUBLISHED ? 3u * 2u * entries : 0u));
    assert(memcmp(expansion1 + PRIOR_ARENA_BYTES, b1cc_data, B1CC_BANK_BYTES) == 0);
}

/* A session reset or savestate restore invalidates captured[] so a stale
 * record cannot survive a new match/load. Captured entries persist only
 * within one match lifecycle: phase-3 pair setup resets controller+0x18 to
 * -1 and actor buffers are fixed RAM, so a pre-reset capture no longer
 * matches any live actor. No guest writes, no allocation, no publication. */
static void reset_and_savestate_invalidate_captured(void) {
    assert(activate && session_reset_cb && savestate_cb);
    activate();
    assert(bank_ready == 1 && allocations == 1);
    const unsigned writes = guest_writes, allocs = allocations;

    /* Store one record per recipient side. */
    memset(versions, 0, sizeof versions);
    versions[GASO][0] = 1;   /* source Gas-O BAG1 side 0 */
    versions[HEAT][1] = 1;   /* recipient Heat BAG1 side 1 */
    setup_ram(GASO, HEAT);
    const uint32_t epoch = bag2jp_gaso_caught_epoch();
    assert(publish(0, 1));   /* captured[1] available */
    assert(recorded());
    assert(capture_stored == 1);

    /* Before reset/savestate, entry takes the record. */
    assert(enter(1, 1, HIT_SLOT) == expect_redirect(1));
    assert(GASO_CAUGHT_CLIP_PUBLISHED ? slot1_holds_clip(1, HEAT) : slot1_empty(1));
    assert(entry_taken == 1);
    assert(!recorded());   /* consumed */

    /* Re-store for the reset test. */
    assert(publish(0, 1));
    assert(recorded());
    session_reset_cb();
    assert(bag2jp_gaso_caught_epoch() == epoch + 1u);
    assert(bag2jp_gaso_caught_epoch_hits(1u) == bag2jp_gaso_caught_hits(1u));
    assert(bag2jp_gaso_caught_epoch_hits(2u) == 0u);
    assert(guest_writes == writes + (GASO_CAUGHT_CLIP_PUBLISHED ? 3u : 0u) &&
           allocations == allocs);   /* no guest writes/alloc from reset */
    assert(!recorded());   /* reset invalidated */
    assert(!enter(1, 1, HIT_SLOT));   /* no take after reset */
    assert(entry_taken == 1);

    /* A reset alone recovers nothing: the tuple published before it stays in
     * RAM, so a new take on the same tables is refused and leaves a2. */
    assert(publish(0, 1));
    const unsigned refused = log_publish_refused;
    assert(!enter(1, 1, HIT_SLOT) && entry_taken == 2);
    assert(log_publish_refused == refused + (GASO_CAUGHT_CLIP_PUBLISHED ? 1u : 0u));
    assert(GASO_CAUGHT_CLIP_PUBLISHED ? slot1_holds_clip(1, HEAT) : slot1_empty(1));

    /* Re-store for the savestate test. */
    assert(publish(0, 1));
    assert(recorded());
    const unsigned recovered = slot1_recovered;
    savestate_cb();
    assert(bag2jp_gaso_caught_epoch() == epoch + 2u);
    assert(bag2jp_gaso_caught_epoch_hits(1u) == bag2jp_gaso_caught_hits(1u));
    assert(guest_writes == writes + (GASO_CAUGHT_CLIP_PUBLISHED ? 3u : 0u) &&
           allocations == allocs);
    assert(!recorded());   /* savestate invalidated */
    assert(!enter(1, 1, HIT_SLOT));
    assert(entry_taken == 2);

    /* The load recovered the orphaned tuple (scenario 27), so a new take
     * reuses it after VERIFY instead of being refused. */
    assert(slot1_recovered == recovered + (GASO_CAUGHT_CLIP_PUBLISHED ? 1u : 0u));
    assert(publish(0, 1));
    assert(enter(1, 1, HIT_SLOT) == expect_redirect(1) && entry_taken == 3);
    assert(GASO_CAUGHT_CLIP_PUBLISHED ? slot1_holds_clip(1, HEAT) : slot1_empty(1));

    assert(guest_writes == writes + (GASO_CAUGHT_CLIP_PUBLISHED ? 3u : 0u) &&
           allocations == allocs);
}

/* Publication of slot1 is guarded by GASO_CAUGHT_CLIP_PUBLISHED: while 0 no
 * guest write occurs on entry; while 1 the ten slot bytes are published once
 * per recipient side and a2 becomes slot1. Reset/savestate clear published
 * state without guest writes (retirement is scenario 12). */
static void publication_slot1_guarded_and_restorable(void) {
    assert(activate && session_reset_cb && savestate_cb);
    activate();
    assert(bank_ready == 1);

    memset(versions, 0, sizeof versions);
    versions[GASO][0] = 1;   /* source Gas-O BAG1 side 0 */
    versions[HEAT][1] = 1;   /* recipient Heat BAG1 side 1 */
    setup_ram(GASO, HEAT);
    assert(publish(0, 1));   /* captured[1] available */
    assert(recorded());

    const unsigned writes_before = guest_writes;
    const unsigned taken_before = entry_taken;
    const unsigned lines_before = log_lines;
    const unsigned pub_before = slot1_published;
    const unsigned rest_before = slot1_restored;

    /* Entry take: consume the record. With publish disabled, no slot1 write. */
    assert(enter(1, 1, HIT_SLOT) == GASO_CAUGHT_CLIP_PUBLISHED);
    assert(entry_taken == taken_before + 1u);
    assert(log_lines == lines_before + (GASO_CAUGHT_CLIP_PUBLISHED ? 2u : 1u));

    if (GASO_CAUGHT_CLIP_PUBLISHED) {
        assert(strstr(last_log, "slot1 published side=2 clip=") != NULL);
        /* One tuple written: clip word, 2-frame half, metadata word. */
        assert(guest_writes == writes_before + 3u);
        assert(slot1_holds_clip(1, HEAT));
        assert(slot1_published == pub_before + 1u);
        assert(slot1_restored == rest_before);
    } else {
        assert(strstr(last_log, "slot1 published") == NULL);
        assert(guest_writes == writes_before);
        assert(slot1_published == pub_before);
        assert(slot1_restored == rest_before);
    }

    /* Reset clears published state without guest writes. */
    session_reset_cb();
    assert(guest_writes == writes_before + (GASO_CAUGHT_CLIP_PUBLISHED ? 3u : 0u));

    /* Savestate clears published state without guest writes. */
    savestate_cb();
    assert(guest_writes == writes_before + (GASO_CAUGHT_CLIP_PUBLISHED ? 3u : 0u));

    /* After reset/savestate, no stale record survives. */
    assert(!recorded());
    assert(!enter(1, 1, HIT_SLOT));
    assert(entry_taken == taken_before + 1u);
}

/* Calls without a take: each ticks the plugin and runs retirement. */
static void tick(unsigned calls) {
    for (unsigned i = 0; i < calls; ++i) assert(!enter(0, 0, 0));
}

/* Fresh session in which Gas-O (side 0) catches a BAG1 Heat (side 1). */
static int take_on_fresh_session(void) {
    memset(versions, 0, sizeof versions);
    versions[GASO][0] = 1;
    versions[HEAT][1] = 1;
    setup_ram(GASO, HEAT);
    assert(publish(0, 1) && recorded());
    return enter(1, 1, HIT_SLOT);
}

/* Entry calls a retirement waits for a clip that never reached slot1
 * (GASO_CAUGHT_UNSTARTED_TICKS) and between refused restores (RETRY). */
#define UNSTARTED_CALLS 60u
#define RETRY_CALLS 8u
#define RESTORE_TRIES 32u                    /* refused restores before abandoning */

/* The clip retires when FUN_8002d06c has moved the actor off slot1: seen on
 * slot1 (current or previous == 1), then both elsewhere. The restore puts back
 * the original empty tuple; a decoder still inside the clip refuses it and the
 * restore is retried, throttled. A clip that never started is restored after
 * UNSTARTED_CALLS. A take the contract refuses leaves a2 and RAM untouched. */
static void slot1_retires_after_clip_leaves(void) {
    assert(activate && session_reset_cb && savestate_cb);
    activate();
    assert(bank_ready == 1);
    if (!GASO_CAUGHT_CLIP_PUBLISHED) {
        assert(!take_on_fresh_session() && slot1_empty(1));
        const unsigned writes = guest_writes, lines = log_lines;
        set_slot_state(1, 1, 1);
        tick(2u * UNSTARTED_CALLS);
        assert(guest_writes == writes && log_lines == lines && slot1_empty(1));
        return;
    }

    /* Seen on slot1, then leaving it in two steps. */
    assert(take_on_fresh_session() && slot1_holds_clip(1, HEAT));
    unsigned writes = guest_writes;
    const unsigned entered = log_entered, restored = slot1_restored;
    set_slot_state(1, 1, 1);
    tick(1);
    assert(log_entered == entered + 1u && strstr(last_log, "slot1 entered side=2"));
    tick(2u * UNSTARTED_CALLS);                       /* still on slot1: kept */
    set_slot_state(1, 5, 1);
    tick(1);                                          /* previous still slot1 */
    assert(log_entered == entered + 1u && slot1_restored == restored);
    assert(guest_writes == writes && slot1_holds_clip(1, HEAT));
    set_slot_state(1, 5, 5);
    tick(1);
    assert(slot1_restored == restored + 1u && guest_writes == writes + 3u && slot1_empty(1));
    assert(strstr(last_log, "slot1 restored side=2 (clip left slot1)"));
    tick(2u * UNSTARTED_CALLS);
    assert(slot1_restored == restored + 1u && guest_writes == writes + 3u);

    /* A decoder pointer inside the clip refuses the restore; retried later. */
    assert(take_on_fresh_session());
    writes = guest_writes;
    const unsigned refused = log_restore_refused;
    set_slot_state(1, 1, 1);
    tick(1);
    put_word(actor_of[1] + DECODER, slot1_of(1).raw + 4u);
    set_slot_state(1, 5, 5);
    tick(1);
    assert(log_restore_refused == refused + 1u && guest_writes == writes);
    assert(strstr(last_log, "restore refused side=2 current=5 previous=5"));
    tick(RETRY_CALLS - 2u);                           /* throttled, not relogged */
    assert(log_restore_refused == refused + 1u && slot1_holds_clip(1, HEAT));
    put_word(actor_of[1] + DECODER, 0);
    tick(1);
    assert(slot1_restored == restored + 1u);          /* still waiting to retry */
    tick(1);
    assert(slot1_restored == restored + 2u && slot1_empty(1));
    assert(strstr(last_log, "(clip left slot1)") && guest_writes == writes + 3u);

    /* Never reached slot1: restored after UNSTARTED_CALLS calls. */
    assert(take_on_fresh_session());
    tick(UNSTARTED_CALLS - 1u);
    assert(slot1_restored == restored + 2u && slot1_holds_clip(1, HEAT));
    tick(1);
    assert(slot1_restored == restored + 3u && slot1_empty(1));
    assert(strstr(last_log, "(clip never started)"));

    /* A second take while still published reuses the clip, without writes,
     * and restarts the unstarted wait. */
    assert(take_on_fresh_session());
    writes = guest_writes;
    tick(UNSTARTED_CALLS - 2u);
    assert(publish(0, 1) && enter(1, 1, HIT_SLOT) && guest_writes == writes);
    tick(UNSTARTED_CALLS - 1u);
    assert(slot1_restored == restored + 3u && slot1_holds_clip(1, HEAT));
    tick(1);
    assert(slot1_restored == restored + 4u && slot1_empty(1));

    /* A take whose lookup names another clip never reuses the published one. */
    assert(take_on_fresh_session());
    writes = guest_writes;
    ram[(actor_of[1] + 4u) & RAM_MASK] = STRIKE;
    versions[STRIKE][1] = 1;
    assert(publish(0, 1) && !enter(1, 1, HIT_SLOT));
    assert(guest_writes == writes && slot1_holds_clip(1, HEAT));

    /* The game rewrites slot1 while the clip is published (reload without a
     * plan reset): the publication is forgotten without writing, and a later
     * take publishes afresh instead of redirecting onto the empty tuple. */
    for (unsigned when = 0; when < 2; ++when) {
        assert(take_on_fresh_session());
        if (when) {                                   /* after the clip ran */
            set_slot_state(1, 1, 1);
            tick(1);
        }
        put_word(table_of(1, RAW) + 4u, empty_of(1));
        ram[(table_of(1, LENGTH) + 2u) & RAM_MASK] = 0;
        put_word(table_of(1, META) + 4u, 0);
        set_slot_state(1, 5, 5);
        writes = guest_writes;
        const unsigned lost = log_lost;
        tick(1);
        assert(log_lost == lost + 1u && strstr(last_log, "slot1 lost side=2"));
        assert(guest_writes == writes && slot1_empty(1));
        tick(2u * UNSTARTED_CALLS);                   /* nothing left to retire */
        assert(guest_writes == writes && slot1_restored == restored + 4u);
        assert(publish(0, 1) && enter(1, 1, HIT_SLOT));
        assert(guest_writes == writes + 3u && slot1_holds_clip(1, HEAT));
    }

    /* Rewritten before the next call could notice: the reuse is verified in
     * guest RAM, so the take republishes instead of redirecting onto it. */
    assert(take_on_fresh_session());
    writes = guest_writes;
    put_word(table_of(1, RAW) + 4u, empty_of(1));
    ram[(table_of(1, LENGTH) + 2u) & RAM_MASK] = 0;
    put_word(table_of(1, META) + 4u, 0);
    assert(publish(0, 1) && enter(1, 1, HIT_SLOT));
    assert(guest_writes == writes + 3u && slot1_holds_clip(1, HEAT));

    /* The tuple is intact but the contract no longer holds (the original
     * empty word was overwritten): the reuse is refused, a2 and RAM untouched. */
    assert(take_on_fresh_session());
    writes = guest_writes;
    put_word(empty_of(1), 7u);
    assert(publish(0, 1));
    const unsigned reuse_refused = log_publish_refused;
    assert(!enter(1, 1, HIT_SLOT));
    assert(log_publish_refused == reuse_refused + 1u && strstr(last_log, "reuse refused side=2"));
    assert(guest_writes == writes && slot1_holds_clip(1, HEAT));

    /* Each slot1 field is checked on its own: a rewritten length or metadata
     * word alone is also lost. */
    for (unsigned field = 0; field < 2; ++field) {
        assert(take_on_fresh_session());
        writes = guest_writes;
        if (field) put_word(table_of(1, META) + 4u, 0);
        else ram[(table_of(1, LENGTH) + 2u) & RAM_MASK] = 3u;
        tick(1);
        assert(strstr(last_log, "slot1 lost side=2") && guest_writes == writes);
    }

    /* Moved tables: also lost, never written through the old pointers. */
    assert(take_on_fresh_session());
    writes = guest_writes;
    put_word(actor_of[1] + RAW, table_of(1, RAW) + 0x800u);
    tick(1);
    assert(strstr(last_log, "slot1 lost side=2") && guest_writes == writes);
    put_word(actor_of[1] + RAW, table_of(1, RAW));

    /* A restore refused past its retry budget is abandoned, not retried forever. */
    assert(take_on_fresh_session());
    writes = guest_writes;
    set_slot_state(1, 1, 1);
    tick(1);
    put_word(actor_of[1] + DECODER, slot1_of(1).raw + 4u);
    set_slot_state(1, 5, 5);
    const unsigned lost_before = log_lost;
    tick(RESTORE_TRIES * RETRY_CALLS - RETRY_CALLS);
    assert(log_lost == lost_before && slot1_holds_clip(1, HEAT));
    tick(RETRY_CALLS);
    assert(log_lost == lost_before + 1u && strstr(last_log, "restore abandoned side=2"));
    put_word(actor_of[1] + DECODER, 0);
    tick(2u * RETRY_CALLS);
    assert(guest_writes == writes && slot1_restored == restored + 4u);

    /* Refused publications: the actor on slot1, a non-zero empty word, and
     * unreadable tables. Each leaves a2, writes nothing and is logged. */
    for (unsigned failure = 0; failure < 3; ++failure) {
        memset(versions, 0, sizeof versions);
        versions[GASO][0] = versions[HEAT][1] = 1;
        setup_ram(GASO, HEAT);
        if (failure == 0) set_slot_state(1, 1, 0);
        if (failure == 1) put_word(empty_of(1), 7u);
        if (failure == 2) put_word(actor_of[1] + COUNT, 1u);
        assert(publish(0, 1));
        writes = guest_writes;
        const unsigned publish_refused = log_publish_refused;
        assert(!enter(1, 1, HIT_SLOT));
        assert(log_publish_refused == publish_refused + 1u && guest_writes == writes);
        assert(strstr(last_log, failure == 2 ? "(unreadable)" : "(contract)"));
        tick(2u * UNSTARTED_CALLS);                   /* nothing to retire */
        assert(guest_writes == writes && slot1_restored == restored + 4u);
    }

    /* Live regression: gf8088 entered slot1, and the second catch at gf8292
     * must reuse it even while current/previous and decoder still refer to it.
     * Reuse writes no tuple; restoration remains forbidden until retirement. */
    assert(take_on_fresh_session());
    writes = guest_writes;
    set_slot_state(1, 1, 1);
    put_word(actor_of[1] + DECODER, slot1_of(1).raw + 4u);
    assert(publish(0, 1) && enter(1, 1, HIT_SLOT));
    assert(guest_writes == writes && slot1_holds_clip(1, HEAT));
    tick(UNSTARTED_CALLS);
    assert(guest_writes == writes && slot1_holds_clip(1, HEAT));
    set_slot_state(1, 5, 5);
    put_word(actor_of[1] + DECODER, 0);
    tick(1);
    assert(guest_writes == writes + 3u && slot1_empty(1));
}

static void secondary_effect_only_after_owned_publication(void) {
    activate();
    const uint32_t effects[] = {0u, 1u, 2u, 21u};
    for (uint32_t source = 0; source < 2; ++source) {
        const uint32_t recipient = source ^ 1u;
        for (unsigned i = 0; i < sizeof effects / sizeof *effects; ++i) {
            memset(versions, 0, sizeof versions);
            versions[GASO][source] = versions[HEAT][recipient] = 1;
            setup_ram(source ? HEAT : GASO, source ? GASO : HEAT);
            put_word(actor_of[recipient] + SECONDARY_EFFECT, 0xcafe0000u | effects[i]);
            put_word(actor_of[source] + SECONDARY_EFFECT, 0xbeef0001u);
            assert(publish(source, recipient));
            const int redirect = expect_redirect(1);
            assert(enter(recipient, 1, HIT_SLOT) == redirect);
            const uint32_t expected = redirect && effects[i] == 1u ? 0u : effects[i];
            assert(ram_word(actor_of[recipient] + SECONDARY_EFFECT) == (0xcafe0000u | expected));
            assert(ram_word(actor_of[source] + SECONDARY_EFFECT) == 0xbeef0001u);
            /* A re-hit on an owned active slot must suppress its new effect too. */
            if (redirect) {
                set_slot_state(recipient, 1, 1);
                put_word(actor_of[recipient] + SECONDARY_EFFECT, 0xcafe0001u);
                assert(publish(source, recipient) && enter(recipient, 1, HIT_SLOT));
                assert(ram_word(actor_of[recipient] + SECONDARY_EFFECT) == 0xcafe0000u);
            }
        }
    }
}

static void secondary_effect_survives_rejected_caught(void) {
    activate();
    for (unsigned variant = 0; variant < 7; ++variant) {
        memset(versions, 0, sizeof versions);
        versions[GASO][0] = variant != 4;
        versions[HEAT][1] = variant != 0;
        const unsigned source_char = variant == 2 ? HEAT : variant == 3 ? STRIKE : GASO;
        setup_ram(source_char, HEAT);
        if (variant == 6 && GASO_CAUGHT_CLIP_PUBLISHED) {
            assert(publish(0, 1) && enter(1, 1, HIT_SLOT));
            set_slot_state(1, 1, 1);
            /* The game replaces an owned tuple before the next direct hit. */
            const uint32_t meta = table_of(1, META) + 4u;
            put_word(meta, ram_word(meta) ^ 1u);
        }
        put_word(actor_of[1] + SECONDARY_EFFECT, 0xcafe0001u);
        if (variant == 1) put_word(empty_of(1), 1u); /* binding rejects nonempty raw */
        if (variant == 5) {
            put_word(actor_of[0] + SECONDARY_EFFECT, 0xbeef0001u);
            assert(!publish(0, 0)); /* reflected */
            assert(!enter(0, 1, HIT_SLOT));
            assert(ram_word(actor_of[0] + SECONDARY_EFFECT) == 0xbeef0001u);
        } else {
            const int captured_ok = publish(0, 1);
            assert(captured_ok == (variant < 2 || variant == 6));
            assert(!enter(1, 1, HIT_SLOT));
        }
        assert(ram_word(actor_of[1] + SECONDARY_EFFECT) == 0xcafe0001u);
    }
}

static void secondary_effect_span_respects_ram_end(void) {
    activate();
    const uint32_t original = actor_of[1];
    for (unsigned outside = 0; outside < 2; ++outside) {
        memset(versions, 0, sizeof versions);
        versions[GASO][0] = versions[HEAT][1] = 1;
        /* Highest aligned actor whose selector halfword fits, then next word. */
        actor_of[1] = RAM_BASE + live_ram - 0x1728u + outside * 4u;
        setup_ram(GASO, HEAT);
        const uint32_t selector = outside ? RAM_BASE : actor_of[1] + SECONDARY_EFFECT;
        put_word(selector, 0xcafe0001u); /* RAM_BASE is an alias canary, not a valid field. */
        assert(publish(0, 1));
        const int redirect = expect_redirect(1);
        assert(enter(1, 1, HIT_SLOT) == redirect);
        assert(ram_word(selector) == (redirect && !outside ? 0xcafe0000u : 0xcafe0001u));
    }
    actor_of[1] = original;
}

/* A settled, fully blended CAUGHT hold with the native fixed-rate argument. */
static void compatible_live_pose(CPUState *cpu, uint32_t side) {
    const uint32_t actor = actor_of[side];
    const uint32_t controller = CONTROLLERS + CONTROLLER_STRIDE * side;
    set_slot_state(side, 1, 1);
    put_word(actor + 0x1544u, 0x10001000u); /* animation blend half at+1546 */
    put_word(actor + 0x1554u, 1u);
    put_word(controller + 0x14u, 0x08000000u);
    put_word(controller + 0x18u, 0xffffffffu); /* fixture only, never plugin writes */
    put_word(controller + 0x1cu, 0xf8000000u);
    put_word(controller + 0x20u, 0xf7ffff00u);
    put_word(controller + 0x24u, 0u); /* mode1 copies the already-cleared frame 0 */
    put_word(controller + 0x44u, 217u); /* renewed by native caller before entry */
    put_word(STACK + 0x10u, 0xf8000000u);
    memset(cpu, 0xa5, sizeof *cpu);
    cpu->gpr[REG_A0] = controller;
    cpu->gpr[REG_A1] = 1u;
    cpu->gpr[REG_A2] = HIT_SLOT;
    cpu->gpr[7] = 0x1000u;
    cpu->gpr[REG_SP] = STACK;
}

static void rehit_preserves_only_compatible_live_pose(void) {
    activate();
    if (!GASO_CAUGHT_CLIP_PUBLISHED) {
        assert(!take_on_fresh_session());
        return;
    }
    for (unsigned kind = 0; kind < 15; ++kind) {
        assert(take_on_fresh_session());
        CPUState cpu, expected;
        compatible_live_pose(&cpu, 1);
        const uint32_t actor = actor_of[1];
        const uint32_t controller = CONTROLLERS + CONTROLLER_STRIDE;
        if (kind == 1) put_word(controller + 0x14u, 0x04000000u);
        if (kind == 2) put_word(STACK + 0x10u, 0xf0000000u);
        if (kind == 3) cpu.gpr[7] = 0x800u;
        if (kind == 4) put_word(actor + 0x1544u, 0x08001000u);
        if (kind == 5) put_word(actor + PREVIOUS, 6u);
        if (kind == 6) put_word(actor + 0x1554u, 0u);
        if (kind == 7) cpu.gpr[REG_SP] = RAM_BASE + live_ram - 4u;
        if (kind == 8) {
            cpu.gpr[REG_A0] = RAM_BASE + live_ram - 4u;
            put_word(cpu.gpr[REG_A0], actor); /* actor readable but rest of controller not */
        }
        if (kind == 9) {
            put_word(controller + 0x1cu, 17u);
            put_word(STACK + 0x10u, 17u);
            put_word(controller + 0x14u, 0u - 17u);
        }
        if (kind == 10) put_word(controller + 0x18u, 3u);
        if (kind == 11) put_word(actor + CURRENT, 6u);
        if (kind == 12) ram[(controller + 0x0au) & RAM_MASK] = 1u; /* entry would clear it */
        if (kind == 13) ram[(controller + 0x0bu) & RAM_MASK] = 1u; /* entry would clear it */
        if (kind == 14) put_word(controller + 0x24u, 1u);          /* entry would copy frame 0 */
        assert(publish(0, 1));
        expected = cpu;
        expected.gpr[REG_A2] = 1u;
        if (!kind) expected.gpr[REG_A1] = 0u;
        const unsigned writes = guest_writes;
        entry(&cpu, ENTRY);
        if (memcmp(&cpu, &expected, sizeof cpu))
            fprintf(stderr, "rehit case=%u mode=%u/%u slot=%u/%u\n", kind,
                    cpu.gpr[REG_A1], expected.gpr[REG_A1], cpu.gpr[REG_A2], expected.gpr[REG_A2]);
        assert(memcmp(&cpu, &expected, sizeof cpu) == 0);
        assert(guest_writes == writes); /* no actor/control/timer writes */
        assert(ram_word(controller + 0x20u) == 0xf7ffff00u);
        assert(ram_word(controller + 0x44u) == 217u);
    }
}

/* A fully compatible live pose is not enough: identity, lookup and VERIFY must
 * each still refuse the continuation on their own, leaving a1/a2 untouched. */
static void rehit_barriers_keep_native_entry(void) {
    activate();
    if (!GASO_CAUGHT_CLIP_PUBLISHED) {
        assert(!take_on_fresh_session());
        return;
    }
    for (unsigned barrier = 0; barrier < 3; ++barrier) {
        assert(take_on_fresh_session());
        CPUState cpu;
        compatible_live_pose(&cpu, 1);
        const uint32_t controller = CONTROLLERS + CONTROLLER_STRIDE;
        if (barrier == 0) cpu.gpr[REG_A0] = CONTROLLERS; /* another actor: no record matches */
        if (barrier == 1) versions[HEAT][1] = 0;         /* recipient is no longer BAG1 Heat */
        if (barrier == 2) {
            /* The slot1 tables stay intact (retire passes), but the clamp byte of
             * the live clip does not: lookup's bank match refuses the reuse. VERIFY
             * re-checks the same bank on a fresh copy, so this is the same contract. */
            const uint32_t meta = slot1_of(1).meta;
            assert(meta >= EXPANSION1 && meta - EXPANSION1 + 5u < expansion1_used);
            expansion1[meta - EXPANSION1 + 5u] = 0u;
        }
        assert(publish(0, 1));
        const CPUState expected = cpu;
        const unsigned writes = guest_writes;
        entry(&cpu, ENTRY);
        if (memcmp(&cpu, &expected, sizeof cpu))
            fprintf(stderr, "barrier=%u mode=%u slot=%u\n", barrier,
                    cpu.gpr[REG_A1], cpu.gpr[REG_A2]);
        assert(memcmp(&cpu, &expected, sizeof cpu) == 0);
        assert(cpu.gpr[REG_A1] == 1u && cpu.gpr[REG_A2] == HIT_SLOT);
        assert(guest_writes == writes);
        assert(ram_word(controller + 0x44u) == 217u);
    }
}

/* The mirrored direction: victim on side 0, attacker on side 1. */
static void rehit_preserves_compatible_pose_on_side0(void) {
    activate();
    memset(versions, 0, sizeof versions);
    versions[HEAT][0] = versions[GASO][1] = 1;
    setup_ram(HEAT, GASO);
    assert(publish(1, 0) && recorded());
    if (!GASO_CAUGHT_CLIP_PUBLISHED) {
        assert(!enter(0, 1, HIT_SLOT));
        return;
    }
    assert(enter(0, 1, HIT_SLOT));
    CPUState cpu, expected;
    compatible_live_pose(&cpu, 0);
    const uint32_t controller = CONTROLLERS;
    assert(publish(1, 0));
    expected = cpu;
    expected.gpr[REG_A1] = 0u;
    expected.gpr[REG_A2] = 1u;
    const unsigned writes = guest_writes;
    entry(&cpu, ENTRY);
    if (memcmp(&cpu, &expected, sizeof cpu))
        fprintf(stderr, "side0 mode=%u/%u slot=%u/%u\n", cpu.gpr[REG_A1],
                expected.gpr[REG_A1], cpu.gpr[REG_A2], expected.gpr[REG_A2]);
    assert(memcmp(&cpu, &expected, sizeof cpu) == 0);
    assert(guest_writes == writes);
    assert(ram_word(controller + 0x20u) == 0xf7ffff00u);
    assert(ram_word(controller + 0x44u) == 217u);
}

/* Fixed actor addresses are reused across loads; an old capture must not
 * authorize a recipient after either actor identity or its tables changed. */
static void capture_identity_drift_is_consumed_without_take(void) {
    activate();
    for (uint32_t source = 0; source < 2; ++source) {
        const uint32_t recipient = source ^ 1u;
        for (unsigned change = 0; change < 15; ++change) {
            memset(versions, 0, sizeof versions);
            versions[GASO][source] = versions[HEAT][recipient] = 1;
            setup_ram(source ? HEAT : GASO, source ? GASO : HEAT);
            assert(publish(source, recipient) && recorded());
            switch (change) {
            case 0: ram[(actor_of[source] + 4) & RAM_MASK] = STRIKE; break;
            case 1: versions[GASO][source] = 0; break;
            case 2: put_word(ACTORS + 8u * source, 0); break;
            case 3: put_word(ACTORS + 8u * recipient, 0); break;
            case 4: ram[(actor_of[recipient] + 5) & RAM_MASK] = source; break;
            case 5: put_word(actor_of[source] + RAW, table_of(source, RAW) + 4); break;
            case 6: put_word(actor_of[recipient] + RAW, table_of(recipient, RAW) + 4); break;
            case 7: put_word(actor_of[recipient] + LENGTH, table_of(recipient, LENGTH) + 2); break;
            case 8: put_word(actor_of[recipient] + META, table_of(recipient, META) + 4); break;
            case 9: put_word(actor_of[recipient] + COUNT, SLOTS - 1); break;
            case 10: ram[(actor_of[recipient] + 4) & RAM_MASK] = STRIKE; break;
            case 11: put_word(actor_of[source] + LENGTH, table_of(source, LENGTH) + 2); break;
            case 12: put_word(actor_of[source] + META, table_of(source, META) + 4); break;
            case 13: put_word(actor_of[source] + COUNT, SLOTS - 1); break;
            default: ram[(actor_of[source] + 5) & RAM_MASK] = recipient; break;
            }
            const unsigned taken = entry_taken, writes = guest_writes, stale = capture_stale;
            const unsigned ready = lookup_ready, rejected = lookup_rejected;
            const uint32_t hits = bag2jp_gaso_caught_hits(recipient);
            assert(!enter(recipient, 1, HIT_SLOT));
            assert(entry_taken == taken && guest_writes == writes);
            assert(lookup_ready == ready && lookup_rejected == rejected);
            assert(bag2jp_gaso_caught_hits(recipient) == hits);
            assert(capture_stale == stale + 1u);
            assert(strstr(last_log, "capture stale") != NULL);
            assert(!recorded());
        }
    }
}

static void successful_reuse_is_logged_after_verify(void) {
    activate();
    memset(versions, 0, sizeof versions);
    versions[GASO][0] = versions[HEAT][1] = 1;
    setup_ram(GASO, HEAT);
    assert(publish(0, 1));
    assert(enter(1, 1, HIT_SLOT) == expect_redirect(1));
    if (!GASO_CAUGHT_CLIP_PUBLISHED) return;
    set_slot_state(1, 1, 1);
    assert(publish(0, 1) && enter(1, 1, HIT_SLOT));
    assert(strstr(last_log, "slot1 reused side=2") != NULL);
}

static void replacement_controller_revokes_old_capture(void) {
    activate();
    for (uint32_t source = 0; source < 2; ++source) {
        const uint32_t recipient = source ^ 1u;
        memset(versions, 0, sizeof versions);
        versions[GASO][source] = versions[HEAT][recipient] = 1;
        setup_ram(source ? HEAT : GASO, source ? GASO : HEAT);
        assert(publish(source, recipient) && recorded());
        const uint32_t replacement = actor_of[recipient] + 0x4000u;
        put_word(ACTORS + 8u * recipient, replacement);
        put_word(CONTROLLERS + CONTROLLER_STRIDE * recipient, replacement);
        const unsigned stale = capture_stale, taken = entry_taken, writes = guest_writes;
        const unsigned ready = lookup_ready, rejected = lookup_rejected;
        const uint32_t hits = bag2jp_gaso_caught_hits(recipient);
        assert(!enter(recipient, 1, HIT_SLOT));
        assert(capture_stale == stale + 1u);
        assert(entry_taken == taken && guest_writes == writes);
        assert(lookup_ready == ready && lookup_rejected == rejected);
        assert(bag2jp_gaso_caught_hits(recipient) == hits);
        assert(!recorded());
    }
}

static void retirement_can_precede_stale_capture_rejection(void) {
    activate();
    memset(versions, 0, sizeof versions);
    versions[GASO][0] = versions[HEAT][1] = 1;
    setup_ram(GASO, HEAT);
    assert(publish(0, 1));
    assert(enter(1, 1, HIT_SLOT) == expect_redirect(1));
    if (!GASO_CAUGHT_CLIP_PUBLISHED) return;
    set_slot_state(1, 1, 1);
    tick(1);
    assert(publish(0, 1));
    set_slot_state(1, 5, 5);
    versions[GASO][0] = 0;
    const unsigned restored = slot1_restored, writes = guest_writes, stale = capture_stale;
    const unsigned taken = entry_taken, ready = lookup_ready, rejected = lookup_rejected;
    const uint32_t hits = bag2jp_gaso_caught_hits(1);
    assert(!enter(1, 1, HIT_SLOT));
    assert(slot1_restored == restored + 1u && slot1_empty(1));
    assert(guest_writes == writes + 3u && capture_stale == stale + 1u);
    assert(entry_taken == taken && lookup_ready == ready && lookup_rejected == rejected);
    assert(bag2jp_gaso_caught_hits(1) == hits && !recorded());
}

static CPUState init_arguments(uint32_t side) {
    CPUState cpu;
    memset(&cpu, 0x5a, sizeof cpu);
    cpu.gpr[REG_A0] = CONTROLLERS + CONTROLLER_STRIDE * side;
    cpu.gpr[REG_A1] = actor_of[side];
    cpu.gpr[REG_A2] = STACK + 16u;
    cpu.gpr[17] = actor_of[side]; /* s1, preserved by existing home callback */
    cpu.gpr[REG_S2] = cpu.gpr[REG_A0];
    cpu.gpr[REG_SP] = STACK;
    return cpu;
}

static void observe_init(CPUState *cpu, uint32_t address) {
    const CPUState before = *cpu;
    const unsigned writes = guest_writes, allocs = allocations;
    const uint32_t epoch = bag2jp_gaso_caught_epoch();
    native_init_cb(cpu, address);
    assert(memcmp(cpu, &before, sizeof before) == 0);
    assert(guest_writes == writes && allocations == allocs);
    assert(bag2jp_gaso_caught_epoch() == epoch); /* not the visual tank epoch */
}

static void native_init_revokes_identical_actor_capture(void) {
    assert(native_init_cb);
    activate();
    for (uint32_t init_side = 0; init_side < 2; ++init_side) {
        memset(versions, 0, sizeof versions);
        versions[GASO][0] = versions[HEAT][1] = 1;
        setup_ram(GASO, HEAT);
        assert(publish(0, 1) && recorded());
        CPUState cpu = init_arguments(init_side);
        const unsigned generations = capture_generations, taken = entry_taken;
        const unsigned ready = lookup_ready, rejected = lookup_rejected;
        observe_init(&cpu, NATIVE_INIT_SITE);
        assert(capture_generations == generations + 1u);
        assert(!recorded() && !enter(1, 1, HIT_SLOT));
        assert(entry_taken == taken && lookup_ready == ready && lookup_rejected == rejected);
        assert(publish(0, 1)); /* a new, post-init capture is still allowed */
        assert(enter(1, 1, HIT_SLOT) == expect_redirect(1));
    }
}

static void unauthenticated_init_does_not_revoke_capture(void) {
    assert(native_init_cb);
    activate();
    for (unsigned variant = 0; variant < 19; ++variant) {
        live_ram = variant == 17 ? RAM_BYTES : RETAIL_RAM;
        memset(versions, 0, sizeof versions);
        versions[GASO][0] = versions[HEAT][1] = 1;
        setup_ram(GASO, HEAT);
        assert(publish(0, 1) && recorded());
        const uint32_t side = variant & 1u;
        CPUState cpu = init_arguments(side);
        uint32_t address = NATIVE_INIT_SITE;
        switch (variant) {
        case 0: address += 4u; put_word(address, NATIVE_INIT_WORD); break;
        case 1: put_word(NATIVE_INIT_SITE, 0); break;
        case 2: cpu.gpr[REG_A0] += 4u; cpu.gpr[REG_S2] = cpu.gpr[REG_A0]; break;
        case 3: cpu.gpr[REG_A1] += 0x1728u; cpu.gpr[17] = cpu.gpr[REG_A1]; break;
        case 4: cpu.gpr[17] ^= 4u; break;
        case 5: cpu.gpr[REG_S2] ^= 4u; break;
        case 6: cpu.gpr[REG_A2] += 4u; break;
        case 7: cpu.gpr[REG_SP] = 0; cpu.gpr[REG_A2] = 16u; break;
        case 8: cpu.gpr[REG_A1] = 0x1f801070u; cpu.gpr[17] = cpu.gpr[REG_A1]; break;
        case 9:
            cpu.gpr[REG_SP] = RAM_BASE + live_ram - 24u;
            cpu.gpr[REG_A2] = cpu.gpr[REG_SP] + 16u; break;
        case 10:
            cpu.gpr[REG_SP] = SCRATCHPAD + SCRATCHPAD_BYTES - 24u;
            cpu.gpr[REG_A2] = cpu.gpr[REG_SP] + 16u; break;
        case 11:
            cpu.gpr[REG_A0] = CONTROLLERS + CONTROLLER_STRIDE / 2u;
            cpu.gpr[REG_S2] = cpu.gpr[REG_A0];
            cpu.gpr[REG_A1] = actor_of[0] + 0x1728u;
            cpu.gpr[17] = cpu.gpr[REG_A1]; break;
        case 12:
        case 13:
            cpu.gpr[REG_A1] = variant == 12 ? actor_of[side] + 1u : RAM_BASE + live_ram - 8u;
            cpu.gpr[17] = cpu.gpr[REG_A1];
            put_word(ACTORS + 8u * side, cpu.gpr[REG_A1]);
            put_byte(cpu.gpr[REG_A1] + 4u, side ? HEAT : GASO);
            put_byte(cpu.gpr[REG_A1] + 5u, side);
            break;
        case 14: put_byte(actor_of[side] + 5u, side ^ 1u); break;
        case 15: put_byte(actor_of[side] + 4u, 0xffu); break;
        case 16:
            cpu.gpr[REG_SP] += 1u;
            cpu.gpr[REG_A2] = cpu.gpr[REG_SP] + 16u; break;
        case 17:
            cpu.gpr[REG_SP] = RAM_BASE + RAM_BYTES - 24u;
            cpu.gpr[REG_A2] = cpu.gpr[REG_SP] + 16u; break;
        default: put_word(ACTORS + 8u * side, actor_of[side ^ 1u]); break;
        }
        const unsigned generations = capture_generations;
        observe_init(&cpu, address);
        assert(capture_generations == generations);
        /* Restore adversarial identity bytes before testing the still valid
         * capture; the observer must not consume it while arguments are bad. */
        for (uint32_t actor_side = 0; actor_side < 2; ++actor_side) {
            put_word(ACTORS + 8u * actor_side, actor_of[actor_side]);
            put_byte(actor_of[actor_side] + 4u, actor_side ? HEAT : GASO);
            put_byte(actor_of[actor_side] + 5u, actor_side);
        }
        assert(recorded());
        assert(enter(1, 1, HIT_SLOT) == expect_redirect(1));
    }
}

static void init_observer_keeps_published_binding_and_hits(void) {
    assert(native_init_cb);
    activate();
    for (uint32_t recipient = 0; recipient < 2; ++recipient) {
        const uint32_t source = recipient ^ 1u;
        memset(versions, 0, sizeof versions);
        versions[GASO][source] = versions[HEAT][recipient] = 1;
        setup_ram(source ? HEAT : GASO, source ? GASO : HEAT);
        assert(publish(source, recipient));
        assert(enter(recipient, 1, HIT_SLOT) == expect_redirect(1));
        if (GASO_CAUGHT_CLIP_PUBLISHED) { set_slot_state(recipient, 1, 1); tick(1); }
        const uint32_t hits = bag2jp_gaso_caught_hits(recipient);
        assert(publish(source, recipient) && recorded());
        const Slot1 before = slot1_of(recipient);
        CPUState cpu = init_arguments(recipient);
        observe_init(&cpu, NATIVE_INIT_SITE);
        const Slot1 after = slot1_of(recipient);
        assert(before.raw == after.raw && before.length == after.length && before.meta == after.meta);
        assert(bag2jp_gaso_caught_hits(recipient) == hits && !recorded());
        assert(bag2jp_gaso_caught_owns_slot1(recipient, actor_of[recipient]) == GASO_CAUGHT_CLIP_PUBLISHED);
    }
}

static void init_stack_geometry_and_two_pending_sides(void) {
    assert(native_init_cb);
    activate();
    const uint32_t stacks[] = {RAM_BASE + RETAIL_RAM - 28u,
                              RAM_BASE + RAM_BYTES - 28u,
                              SCRATCHPAD + SCRATCHPAD_BYTES - 28u};
    for (unsigned variant = 0; variant < 3; ++variant) {
        live_ram = variant == 1 ? RAM_BYTES : RETAIL_RAM;
        memset(versions, 0, sizeof versions);
        versions[GASO][0] = versions[GASO][1] = 1;
        setup_ram(GASO, GASO);
        assert(publish(0, 1) && publish(1, 0) && recorded());
        CPUState cpu = init_arguments(variant & 1u);
        cpu.gpr[REG_SP] = stacks[variant];
        cpu.gpr[REG_A2] = stacks[variant] + 16u;
        const unsigned generations = capture_generations, taken = entry_taken;
        observe_init(&cpu, NATIVE_INIT_SITE);
        assert(capture_generations == generations + 1u && !recorded());
        assert(!enter(0, 1, HIT_SLOT) && !enter(1, 1, HIT_SLOT));
        assert(entry_taken == taken);
    }
}

/* Load a savestate: never writes or allocates; one line per recovery or
 * refusal. Returns the recovered publications. */
static unsigned load(void) {
    const unsigned writes = guest_writes, allocs = allocations, lines = log_lines;
    const unsigned recovered = slot1_recovered, logged = log_recovered;
    const unsigned refused = log_recovery_refused;
    savestate_cb();
    assert(guest_writes == writes && allocations == allocs);
    assert(log_recovered - logged == slot1_recovered - recovered);
    assert(log_lines == lines + (log_recovered - logged) + (log_recovery_refused - refused));
    if (!GASO_CAUGHT_CLIP_PUBLISHED) assert(log_lines == lines && slot1_recovered == recovered);
    return slot1_recovered - recovered;
}

/* A savestate taken while slot1 held the clip forgets the host binding. The
 * load re-derives ownership read-only: the slot must hold this bank's exact
 * clip and pass the contract against the native empty tuple, which FUN_8003
 * 1d3c/800319fc/800326d4 derive from the motion DFS (raw[1] = motions+8+size0).
 * The existing retirement then restores it. The shipped default never reads. */
static void savestate_recovers_published_slot1(void) {
    activate();
    for (unsigned entered = 0; entered < 2; ++entered) {
        assert(take_on_fresh_session() == GASO_CAUGHT_CLIP_PUBLISHED);
        if (entered) set_slot_state(1, 1, 1);
        const Slot1 before = slot1_of(1);
        const unsigned accesses = guest_accesses;
        assert(load() == GASO_CAUGHT_CLIP_PUBLISHED);
        const Slot1 after = slot1_of(1);
        assert(before.raw == after.raw && before.length == after.length && before.meta == after.meta);
        assert(slot1_empty(0));
        if (!GASO_CAUGHT_CLIP_PUBLISHED) {
            assert(guest_accesses == accesses && slot1_empty(1));
            continue;
        }
        assert(strstr(last_log, "slot1 recovered side=2"));
        assert(bag2jp_gaso_caught_owns_slot1(1, actor_of[1]));
        const unsigned writes = guest_writes, restored = slot1_restored;
        if (entered) {
            tick(2u * UNSTARTED_CALLS);               /* still decoding slot1 */
            assert(guest_writes == writes && slot1_holds_clip(1, HEAT));
            set_slot_state(1, 5, 5);
            tick(1);
        } else {
            tick(UNSTARTED_CALLS - 1u);               /* a fresh publication's wait */
            assert(guest_writes == writes && slot1_holds_clip(1, HEAT));
            tick(1);
        }
        assert(slot1_restored == restored + 1u && guest_writes == writes + 3u);
        assert(slot1_empty(1) && !bag2jp_gaso_caught_owns_slot1(1, actor_of[1]));
    }
    /* Both sides published (Gas-O mirror match): each is reclaimed and restored. */
    memset(versions, 0, sizeof versions);
    versions[GASO][0] = versions[GASO][1] = 1;
    setup_ram(GASO, GASO);
    assert(publish(0, 1) && enter(1, 1, HIT_SLOT) == expect_redirect(1));
    assert(publish(1, 0) && enter(0, 1, HIT_SLOT) == expect_redirect(1));
    assert(load() == (GASO_CAUGHT_CLIP_PUBLISHED ? 2u : 0u));
    if (GASO_CAUGHT_CLIP_PUBLISHED) {
        assert(bag2jp_gaso_caught_owns_slot1(0, actor_of[0]) &&
               bag2jp_gaso_caught_owns_slot1(1, actor_of[1]));
        const unsigned writes = guest_writes, restored = slot1_restored;
        tick(UNSTARTED_CALLS);
        assert(slot1_restored == restored + 2u && guest_writes == writes + 6u);
    }
    assert(slot1_empty(0) && slot1_empty(1));

    /* Nothing published: the load recovers nothing on either side. */
    setup_ram(GASO, HEAT);
    assert(load() == 0 && slot1_empty(0) && slot1_empty(1));
}

/* Recovery fails closed: anything but this bank's exact clip is not claimed,
 * and a claimed tuple whose native empty or contract does not hold is
 * refused. Either way RAM stays untouched and nothing is restored later. */
#define COMPANION 0x80104000u
static void savestate_recovery_fails_closed(void) {
    activate();
    for (unsigned variant = 0; variant < 20; ++variant) {
        assert(take_on_fresh_session() == GASO_CAUGHT_CLIP_PUBLISHED);
        const uint32_t actor = actor_of[1], motions = motions_of(1);
        const uint32_t clip = slot1_of(1).raw;
        int claimed = 1;
        switch (variant) {
        case 0: put_word(table_of(1, RAW) + 4u, clip + 4u); claimed = 0; break;
        case 1: ram[(table_of(1, LENGTH) + 2u) & RAM_MASK] = 3u; break;
        case 2: put_word(table_of(1, META) + 4u, 0); break;
        case 3: put_word(actor + MOTIONS, motions_of(0)); break;   /* valid DFS, raw[0] differs */
        case 4:                                       /* zero size, entry1 still plausible */
            put_word(motions, 0);
            put_word(motions + 4u, MOTION1_BYTES);
            break;
        case 5: put_word(motions, MOTION0_BYTES + 1u); break;
        case 6: put_word(motions + 4u + MOTION0_BYTES, 0); break;
        case 7: put_word(empty_of(1), 7u); break;
        case 8: put_byte(actor + 5u, 0); claimed = 0; break;
        case 9:                                       /* companion shares tables */
            put_word(ACTORS + 4u, COMPANION);
            put_word(COMPANION + COUNT, SLOTS);
            for (uint32_t field = RAW; field <= META; field += 4u)
                put_word(COMPANION + field, table_of(1, field));
            break;
        case 10: put_word(actor + MOTIONS, 0x7ffffff0u); break;
        case 11: put_word(motions, 0x7ffffff0u); break;
        case 12: put_byte(actor + 4u, STRIKE); claimed = 0; break;
        case 13:                                      /* size wraps below RAM */
            put_word(actor + MOTIONS, RAM_BASE);
            put_word(RAM_BASE, 0xfffffff8u);
            put_word(table_of(1, RAW), RAM_BASE + 4u);
            break;
        case 14: put_word(actor + RAW, table_of(1, RAW) + 2u); claimed = 0; break;
        case 15: put_word(actor + MOTIONS, motions + 2u); break;
        case 16: put_word(motions + 4u + MOTION0_BYTES, MOTION1_BYTES + 1u); break;
        case 17: put_word(motions + 4u + MOTION0_BYTES, 0x7ffffff0u); break;
        case 18:                                      /* legal size0, entry1 past RAM end */
            put_word(actor + MOTIONS, RAM_BASE + live_ram - 8u);
            put_word(RAM_BASE + live_ram - 8u, MOTION0_BYTES);
            put_word(table_of(1, RAW), RAM_BASE + live_ram - 4u);
            break;
        default:                                      /* odd actor with the right side */
            put_word(ACTORS + 8u, actor + 2u);
            put_byte(actor + 2u + 5u, 1u);
            claimed = 0;
            break;
        }
        const Slot1 before = slot1_of(1);
        const unsigned refused = log_recovery_refused;
        assert(load() == 0);
        assert(log_recovery_refused == refused + (GASO_CAUGHT_CLIP_PUBLISHED && claimed ? 1u : 0u));
        if (GASO_CAUGHT_CLIP_PUBLISHED && claimed) assert(strstr(last_log, "recovery refused side=2"));
        assert(!bag2jp_gaso_caught_owns_slot1(1, actor));
        const unsigned writes = guest_writes, restored = slot1_restored;
        tick(2u * UNSTARTED_CALLS);
        const Slot1 after = slot1_of(1);
        assert(guest_writes == writes && slot1_restored == restored);
        assert(before.raw == after.raw && before.length == after.length && before.meta == after.meta);
        put_word(ACTORS + 4u, 0);
    }
}

/* Publication never infers the empty tuple from a zero word: slot1 must hold
 * the native empty derived from the motion DFS, and raw[0] must match it. */
static void publication_requires_native_empty_slot(void) {
    activate();
    for (unsigned variant = 0; variant < 5; ++variant) {
        memset(versions, 0, sizeof versions);
        versions[GASO][0] = versions[HEAT][1] = 1;
        setup_ram(GASO, HEAT);
        const uint32_t zero_word = empty_of(1) + 0x20u;      /* zero, not native */
        if (variant == 0) put_word(table_of(1, RAW) + 4u, zero_word);
        else if (variant == 1) put_word(table_of(1, RAW), 0);
        else if (variant == 2) put_word(actor_of[1] + MOTIONS, motions_of(0));
        else if (variant == 3) put_word(actor_of[1] + RAW, table_of(1, RAW) + 2u);
        else put_word(actor_of[1] + RAW, RAM_BASE - 4u);     /* raw table pointer below RAM */
        assert(publish(0, 1) && recorded());
        const unsigned writes = guest_writes, refused = log_publish_refused;
        assert(!enter(1, 1, HIT_SLOT) && entry_taken > 0);
        assert(guest_writes == writes);
        assert(log_publish_refused == refused + (GASO_CAUGHT_CLIP_PUBLISHED ? 1u : 0u));
    }
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
    case 9:
        recipient_lookup_is_read_only();
        break;
    case 10:
        reset_and_savestate_invalidate_captured();
        break;
    case 11:
        publication_slot1_guarded_and_restorable();
        break;
    case 12:
        slot1_retires_after_clip_leaves();
        break;
    case 13:
        secondary_effect_only_after_owned_publication();
        break;
    case 14:
        secondary_effect_survives_rejected_caught();
        break;
    case 15:
        secondary_effect_span_respects_ram_end();
        break;
    case 16:
        rehit_preserves_only_compatible_live_pose();
        break;
    case 17:
        rehit_barriers_keep_native_entry();
        break;
    case 18:
        rehit_preserves_compatible_pose_on_side0();
        break;
    case 19:
        capture_identity_drift_is_consumed_without_take();
        break;
    case 20:
        successful_reuse_is_logged_after_verify();
        break;
    case 21:
        replacement_controller_revokes_old_capture();
        break;
    case 22:
        retirement_can_precede_stale_capture_rejection();
        break;
    case 23:
        native_init_revokes_identical_actor_capture();
        break;
    case 24:
        unauthenticated_init_does_not_revoke_capture();
        break;
    case 25:
        init_observer_keeps_published_binding_and_hits();
        break;
    case 26:
        init_stack_geometry_and_two_pending_sides();
        break;
    case 27:
        savestate_recovers_published_slot1();
        break;
    case 28:
        savestate_recovery_fails_closed();
        break;
    case 29:
        publication_requires_native_empty_slot();
        break;
    default:
        return 2;
    }
    return 0;
}
