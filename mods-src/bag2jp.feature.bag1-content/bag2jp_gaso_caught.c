/* Experimental CAUGHT entry seam, default-off (feature bag1-gaso-caught) and
 * inert while GASO_CAUGHT_CLIP_PUBLISHED is 0: no build publishes an authentic
 * guest clip yet, so a2 is never changed. Request 202 has already become slot
 * 89 before FUN_8002d06c; it must not be matched as a controller-entry request.
 *
 * Hook contract: publish borrowed slot1 before the original controller body,
 * then change a2=1; never write the actor's pending at +0x18. A record is taken
 * only by the recipient main actor's entry with mode 1 and slot 89, and it is
 * consumed by that take whether or not a2 changes.
 *
 * Producer-site capture: runs immediately before sh v0,0x18(s5) at 0x8009b5b4,
 * reads the original registers (v0=request, s2=source_side, s4=recipient_side,
 * s5=pending, sp=stack) and guest RAM through psx_mod_read_*, validates against
 * the pinned original code sites, and stores one record per recipient side in
 * captured[] only for a direct (non-reflected) request whose source main actor
 * is Gas-O with the BAG1 version selected. Heat and Strike publish the same
 * request 202; their publications only invalidate the recipient's record.
 * Hooks never write guest RAM, allocate, or change CPU registers (except a2 in
 * the entry callback). Host-only counters (TCP mod_counters) report every
 * producer-site call as capture_stored/capture_rejected and every take as
 * entry_taken; the same events and the rejection reason go to
 * bag2jp_bag1_versions.log, the only channel in builds without debug tools.
 *
 * Activation (P1) prepares the authentic 1048-byte clip bank once per process
 * in Expansion 1 (bag2jp_caught_bank.c): one allocation, a verified copy, and
 * no retry or repair on later activations. P2a looks up the recipient's clip
 * at entry for diagnostics only: readiness is not permission to publish it.
 *
 * Required before GASO_CAUGHT_CLIP_PUBLISHED: authenticated recipient/table
 * generation, bounded exclusive RAM access, persistent loan ownership, safe
 * retirement and reset/savestate handling. Do not allocate placeholder clips
 * or publish slot1 here without a captured record.
 * See notes/gaso-import.md, caught-entry-recovery-20261111.
 */
#include <stdint.h>
#include <string.h>
#include "mod_plugins.h"
#include "cpu_state.h"
#include "bag2jp_caught_source.h"
#include "bag2jp_caught_bank.h"
#include "bag2jp_caught_binding.h"

/* The bank is resident, but no clip is bound to the recipient's slot1. Host
 * tests build with 1 to exercise the old redirect; runtime builds must keep 0. */
#ifndef GASO_CAUGHT_CLIP_PUBLISHED
#define GASO_CAUGHT_CLIP_PUBLISHED 0
#endif

#define GASO_CAUGHT_ENTRY_ADDRESS 0x8002d06cu
#define GASO_CAUGHT_SIDES 2
#define GASO_CAUGHT_REG_A0 4                 /* controller; actor at word[a0] */
#define GASO_CAUGHT_REG_A1 5                 /* controller mode */
#define GASO_CAUGHT_REG_A2 6                 /* destination slot */
#define GASO_CAUGHT_MODE_ENTRY 1u
#define GASO_CAUGHT_HIT_SLOT 89u             /* request 202 translated */
#define GASO_CAUGHT_ARG_A2 1                 /* borrowed slot1 */
#define GASO_CAUGHT_CHARACTER 9              /* Gas-O, GASO_CHAR_ID */

int bag2jp_bag1_has_version(int chr);
int bag2jp_bag1_get_version(int chr, int side);
void b1v_log(const char* fmt, ...) __attribute__((format(printf, 1, 2)));

/* Producer site: sh v0,0x18(s5) publishes request202 to the recipient's
 * pending field. Instruction word verified against Ghidra raw and original
 * overlay; registration rejects drift. */
#define GASO_PRODUCER_SITE 0x8009b5b4u
#define GASO_PRODUCER_EXPECTED 0xa6a20018u

/* Original code sites validated before accepting a capture. These are the same
 * sites checked by b1cs_capture; they bind the callsite, they do not
 * authenticate an entire module. */
#define GASO_CS_OVERLAY_BASE_PTR 0x80010ce0u
#define GASO_CS_OVERLAY_BASE 0x8008f890u
#define GASO_CS_LOAD_CHAR_BYTE 0x8009b5acu   /* lbu v0,0(v0) */
#define GASO_CS_LOAD_CHAR_BYTE_EXPECTED 0x90420000u
#define GASO_CS_LOAD_DELAY_NOP 0x8009b5b0u   /* nop load delay */
#define GASO_CS_LOAD_DELAY_NOP_EXPECTED 0x00000000u
#define GASO_CS_ACTORS 0x8005f808u           /* main actor list */
#define GASO_CS_MAIN_STRIDE 8
#define GASO_CS_ACTOR_BYTES 0x155c
#define GASO_CS_CHARACTER 4
#define GASO_CS_SIDE 5
#define GASO_CS_TABLE 0x80051458u            /* source char -> request table */
#define GASO_CS_VERIFIED_TABLE_ROWS 18
#define GASO_CS_PENDING 0x8005cf08u          /* pending global */
#define GASO_CS_PENDING_STRIDE 0x24
#define GASO_CS_REQUEST 202
#define GASO_CS_STACK_FLAGS 0x30             /* sp + 0x30 + side = direct/reflected flag */
#define GASO_CS_STACK_BYTES 0x32
#define GASO_CS_FLAG_DIRECT 1u
#define GASO_CS_FLAG_REFLECTED 2u
#define GASO_CS_TABLE_ROW_STRIDE 2u

/* One captured source record per recipient side, populated by the producer-site
 * capture hook at 0x8009b5b4. Zero-initialised: available==0 means no record,
 * so the entry callback stays inert. */
static B1CaughtSource captured[GASO_CAUGHT_SIDES];

/* Process-lifetime: the Expansion 1 arena is never freed, so a bank prepared
 * by one session's activation stays owned across later sessions. */
static B1CaughtBank bank;

/* Slot1 publication / restore state, one per recipient side.
 * Guarded by GASO_CAUGHT_CLIP_PUBLISHED: while 0 no guest write is ever
 * issued and a2 is never changed. Publication writes the ten slot bytes
 * (clip, frames=2, info) before the controller consumes slot 89; restore
 * writes the original empty tuple back when the clip retires. */
static B1CaughtBinding gaso_caught_binding[GASO_CAUGHT_SIDES];
static int gaso_caught_published[GASO_CAUGHT_SIDES];

/* Forward declarations: defined below, used by the entry callback. */
static int gaso_caught_build_binding(uint32_t side, const B1CaughtBankClip *clip,
                                     B1CaughtBinding *b) __attribute__((unused));
static void gaso_caught_publish_slot1(uint32_t side) __attribute__((unused));
static void gaso_caught_restore_slot1(uint32_t side) __attribute__((unused));

/* ---- Guest RAM reads through the runtime API ---- */

static uint32_t guest_read_word(uint32_t addr) {
    return psx_mod_read_word(addr);
}

static uint8_t guest_read_byte(uint32_t addr) {
    return psx_mod_read_byte(addr);
}

/* psx_mod_read_* is the traced path (MMIO, unmapped_fatal, lockstep), so a
 * guest pointer is read only when [addr, addr+bytes) lies in live KSEG0 main
 * RAM (2 MiB retail, 8 MiB with expanded RAM: the 8 MiB install keeps its
 * stack above 2 MiB), or in the scratchpad when it may hold the stack. */
#define GASO_CS_RAM 0x80000000u
#define GASO_CS_SCRATCHPAD 0x1f800000u
#define GASO_CS_SCRATCHPAD_BYTES 0x400u

uint32_t memory_get_ram_bytes(void);

static int guest_range_ok(uint32_t addr, uint32_t bytes, int scratchpad) {
    const uint32_t ram_bytes = memory_get_ram_bytes();
    if (addr >= GASO_CS_RAM && bytes <= ram_bytes && addr - GASO_CS_RAM <= ram_bytes - bytes)
        return 1;
    return scratchpad && addr >= GASO_CS_SCRATCHPAD &&
           addr - GASO_CS_SCRATCHPAD <= GASO_CS_SCRATCHPAD_BYTES - bytes;
}

/* ---- Producer-site capture ---- */

/* Capture the original request202 source before sh v0,0x18(s5) publishes it.
 * Reads guest RAM through psx_mod_read_* since we don't have a full RAM buffer.
 * Returns NULL if a record was stored, otherwise the rejection reason. Never
 * writes guest RAM or CPU registers. */
static const char *capture_producer_source(struct CPUState *cpu) {
    /* Registers visible before the original instruction executes: */
    /*   v0  = request value loaded from the source table (should be 202)   */
    /*   s2  = source side (0 or 1)                                         */
    /*   s4  = recipient side (0 or 1)                                      */
    /*   s5  = recipient pending address                                    */
    /*   sp  = stack pointer (flag at sp+0x30+side: 1 direct, 2 reflected)  */
    const uint32_t request = cpu->gpr[2];
    const uint32_t source_side = cpu->gpr[18];
    const uint32_t recipient_side = cpu->gpr[20];
    const uint32_t pending = cpu->gpr[21];
    const uint32_t sp = cpu->gpr[29];

    /* Any later publication to this recipient supersedes an older record. */
    if (recipient_side > 1u) return "recipient side";
    captured[recipient_side].available = 0;

    /* Register validation */
    if (request != GASO_CS_REQUEST) return "request";
    if (source_side > 1u) return "source side";
    if (pending != GASO_CS_PENDING + GASO_CS_PENDING_STRIDE * recipient_side) return "pending";
    if (!guest_range_ok(sp, GASO_CS_STACK_BYTES, 1)) return "stack";

    /* Validate original code sites haven't drifted */
    if (guest_read_word(GASO_CS_OVERLAY_BASE_PTR) != GASO_CS_OVERLAY_BASE ||
        guest_read_word(GASO_CS_LOAD_CHAR_BYTE) != GASO_CS_LOAD_CHAR_BYTE_EXPECTED ||
        guest_read_word(GASO_CS_LOAD_DELAY_NOP) != GASO_CS_LOAD_DELAY_NOP_EXPECTED ||
        guest_read_word(GASO_PRODUCER_SITE) != GASO_PRODUCER_EXPECTED) return "code drift";

    /* Stack flag: reflected=2 when source==recipient, else 1 (direct) */
    const uint32_t reflected = (source_side == recipient_side) ? 1u : 0u;
    const uint32_t expected_flag = reflected ? GASO_CS_FLAG_REFLECTED : GASO_CS_FLAG_DIRECT;
    if (guest_read_byte(sp + GASO_CS_STACK_FLAGS + recipient_side) != expected_flag) return "stack flag";

    /* Validate actors: main list at 0x8005f808, each 8 bytes */
    uint32_t actors[2];
    for (uint32_t side = 0; side < 2; ++side) {
        actors[side] = guest_read_word(GASO_CS_ACTORS + side * GASO_CS_MAIN_STRIDE);
        if (!guest_range_ok(actors[side], GASO_CS_SIDE + 1u, 0)) return "actor pointer";
        if (guest_read_byte(actors[side] + GASO_CS_SIDE) != (uint8_t)side) return "actor side";
    }
    if (actors[0] == actors[1]) return "same actor";

    const uint32_t recipient_actor = actors[recipient_side];
    const uint32_t source_actor = actors[source_side];
    const uint8_t recipient_char = guest_read_byte(recipient_actor + GASO_CS_CHARACTER);
    const uint8_t source_char = guest_read_byte(source_actor + GASO_CS_CHARACTER);

    if (source_char >= GASO_CS_VERIFIED_TABLE_ROWS) return "source character";
    const uint32_t table_row = GASO_CS_TABLE + GASO_CS_TABLE_ROW_STRIDE * (uint32_t)source_char;
    if (guest_read_byte(table_row) != request) return "request table";

    /* Request 202 is shared with Heat and Strike: only a direct Gas-O BAG1
     * attacker may own a record. */
    if (reflected) return "reflected";
    if (source_char != GASO_CAUGHT_CHARACTER) return "not Gas-O";
    if (!bag2jp_bag1_has_version(GASO_CAUGHT_CHARACTER) ||
        !bag2jp_bag1_get_version(GASO_CAUGHT_CHARACTER, (int)source_side)) return "not BAG1";

    /* Store the captured record (one per recipient side) */
    B1CaughtSource value = {0};
    value.clock.generation = 1;   /* TODO: real generation from load/reset lifecycle */
    value.clock.tick = 0;         /* TODO: real tick from frame counter */
    value.actor = recipient_actor;
    value.character = recipient_char;
    value.side = recipient_side;
    value.source_actor = source_actor;
    value.source_character = source_char;
    value.source_side = source_side;
    value.request = request;
    value.reflected = reflected;
    value.available = 1;

    captured[recipient_side] = value;
    return NULL;
}

/* ---- Entry callback: take the recipient's record once ---- */

static void gaso_caught_entry_cb(struct CPUState *cpu, uint32_t address) {
    int side;
    uint32_t actor;
    if (address != GASO_CAUGHT_ENTRY_ADDRESS) return;
    for (side = 0; side < GASO_CAUGHT_SIDES; ++side)
        if (captured[side].available) break;
    /* No record: leave the controller untouched without reading guest RAM. */
    if (side == GASO_CAUGHT_SIDES) return;
    if (cpu->gpr[GASO_CAUGHT_REG_A1] != GASO_CAUGHT_MODE_ENTRY ||
        cpu->gpr[GASO_CAUGHT_REG_A2] != GASO_CAUGHT_HIT_SLOT) return;
    actor = guest_read_word(cpu->gpr[GASO_CAUGHT_REG_A0]);
    for (side = 0; side < GASO_CAUGHT_SIDES; ++side) {
        if (!captured[side].available || captured[side].actor != actor) continue;
        /* Consume once, even while no clip is published. */
        captured[side].available = 0;
        psx_mod_counter_add("gaso_caught.entry_taken", 1u);
        /* Captured recipient identity is only a diagnostic snapshot until P2b
         * proves its load generation. Never use the attacker's BAG1 choice. */
        const uint32_t character = captured[side].character;
        const uint32_t version = character < GASO_CS_VERIFIED_TABLE_ROWS &&
            bag2jp_bag1_has_version((int)character) ?
            (uint32_t)bag2jp_bag1_get_version((int)character, side) : 0u;
        B1CaughtBankClip clip = {0};
        const int ready = b1cc_lookup(&bank, character, version, &clip);
        psx_mod_counter_add(ready ? "gaso_caught.lookup_ready" : "gaso_caught.lookup_rejected", 1u);
        b1v_log("gaso_caught: entry taken by side %d actor %08x, a2 %s; "
                "lookup char=%u version=%u %s clip=%08x bytes=%u", side + 1,
                (unsigned)actor, GASO_CAUGHT_CLIP_PUBLISHED ? "-> 1" : "unchanged",
                (unsigned)character, (unsigned)version, ready ? "ready" : "rejected",
                (unsigned)clip.clip, (unsigned)clip.clip_bytes);
        /* Construye el binding y publica slot1 (diez bytes) antes de cambiar
         * a2. Nada se escribe mientras GASO_CAUGHT_CLIP_PUBLISHED es 0. */
        if (GASO_CAUGHT_CLIP_PUBLISHED && !gaso_caught_published[side]) {
            if (gaso_caught_build_binding(side, &clip,
                                          &gaso_caught_binding[side])) {
                gaso_caught_publish_slot1(side);
            }
        }
        if (GASO_CAUGHT_CLIP_PUBLISHED)
            cpu->gpr[GASO_CAUGHT_REG_A2] = GASO_CAUGHT_ARG_A2;
        return;
    }
}

/* Construye el binding del slot1 para el lado dado a partir del registro
 * capturado y el resultado del lookup. Devuelve 0 si las tablas del actor
 * no son legibles en guest RAM. */
static int gaso_caught_build_binding(uint32_t side, const B1CaughtBankClip *clip,
                                     B1CaughtBinding *b) {
    uint32_t actor = captured[side].actor;
    if (!guest_range_ok(actor, B1CB_ACTOR_BYTES, 0)) return 0;
    b->actor = actor;
    b->character = captured[side].character;
    b->side = captured[side].side;
    b->count = guest_read_word(actor + B1CB_COUNT);
    b->raw_table = guest_read_word(actor + B1CB_RAW);
    b->length_table = guest_read_word(actor + B1CB_LENGTH);
    b->metadata_table = guest_read_word(actor + B1CB_META);
    b->empty_raw = b->raw_table + 4u * B1CB_SLOT;
    b->clip = clip->clip;
    b->clip_bytes = clip->clip_bytes;
    return 1;
}

/* Publica los diez bytes del slot1 (clip, frames=2, info) antes de que el
 * controller consuma la entrada. Nunca escribe mientras GASO_CAUGHT_CLIP_PUBLISHED=0. */
static void gaso_caught_publish_slot1(uint32_t side) {
    if (!GASO_CAUGHT_CLIP_PUBLISHED || gaso_caught_published[side]) return;
    const B1CaughtBinding *b = &gaso_caught_binding[side];
    psx_mod_write_word(b->raw_table + 4u * B1CB_SLOT, b->clip);
    psx_mod_write_half(b->length_table + 2u * B1CB_SLOT, (uint16_t)B1CB_FRAMES);
    psx_mod_write_word(b->metadata_table + 4u * B1CB_SLOT, b->clip);
    gaso_caught_published[side] = 1;
    psx_mod_counter_add("gaso_caught.slot1_published", 1u);
    b1v_log("gaso_caught: slot1 published side=%u clip=%08x bytes=%u", side + 1,
            (unsigned)b->clip, (unsigned)b->clip_bytes);
}

/* Restaura la tupla vacía original del slot1 cuando el clip se retira.
 * Nunca escribe mientras GASO_CAUGHT_CLIP_PUBLISHED=0. */
static void gaso_caught_restore_slot1(uint32_t side) {
    if (!GASO_CAUGHT_CLIP_PUBLISHED || !gaso_caught_published[side]) return;
    const B1CaughtBinding *b = &gaso_caught_binding[side];
    psx_mod_write_word(b->raw_table + 4u * B1CB_SLOT, b->empty_raw);
    psx_mod_write_half(b->length_table + 2u * B1CB_SLOT, 0);
    psx_mod_write_word(b->metadata_table + 4u * B1CB_SLOT, 0);
    gaso_caught_published[side] = 0;
    psx_mod_counter_add("gaso_caught.slot1_restored", 1u);
    b1v_log("gaso_caught: slot1 restored side=%u", side + 1);
}

/* ---- Producer-site instruction callback ---- */

static void gaso_caught_capture_cb(struct CPUState *cpu, uint32_t address) {
    if (address != GASO_PRODUCER_SITE) return;
    const char *rejected = capture_producer_source(cpu);
    psx_mod_counter_add(rejected ? "gaso_caught.capture_rejected"
                                 : "gaso_caught.capture_stored", 1u);
    b1v_log("gaso_caught: request %u s2=%u -> s4=%u sp=%08x %s%s",
            (unsigned)cpu->gpr[2], (unsigned)cpu->gpr[18], (unsigned)cpu->gpr[20],
            (unsigned)cpu->gpr[29],
            rejected ? "rejected: " : "stored", rejected ? rejected : "");
}

/* ---- Session reset / savestate: invalidate captured records ---- */

/* Session reset runs before each plan activates, with emulation stopped and no
 * feature/resource context; it never mutates guest state. Clearing captured[]
 * here drops any stale record from the previous match/session so an entry take
 * cannot consume an obsolete snapshot whose actor+0x18 was already reset to -1.
 * The bank itself stays owned (Expansion 1 arena never freed) and needs no
 * repair: lookup re-verifies guest bytes on every call.
 */
static void gaso_caught_session_reset(void) {
    for (uint32_t side = 0; side < GASO_CAUGHT_SIDES; ++side) {
        captured[side].available = 0;
        gaso_caught_published[side] = 0;
        gaso_caught_binding[side] = (B1CaughtBinding){0};
    }
}

/* Savestate runs after successful guest-state restore, before the restored PC
 * resumes. Rebind host hooks here; do not advance guest gameplay. Clearing
 * captured[] keeps an obsolete record from surviving a load: actor buffers are
 * fixed RAM and controller+0x18 is reset to -1 at every phase-3 pair setup, so
 * a pre-load capture no longer matches any live actor. No guest writes, no
 * allocation, no publication.
 */
static void gaso_caught_savestate(void) {
    for (uint32_t side = 0; side < GASO_CAUGHT_SIDES; ++side) {
        captured[side].available = 0;
        gaso_caught_published[side] = 0;
        gaso_caught_binding[side] = (B1CaughtBinding){0};
    }
}

/* ---- Activation: prepare the clip bank once, never repair it ---- */

static void gaso_caught_activate(void) {
    const int ready = b1cc_prepare(&bank);
    psx_mod_counter_add(ready ? "gaso_caught.bank_ready" : "gaso_caught.bank_unavailable", 1u);
    b1v_log("gaso_caught: clip bank %s at %08x (%s)", ready ? "ready" : "unavailable",
            (unsigned)bank.guest_base,
            GASO_CAUGHT_CLIP_PUBLISHED ? "clip published" : "observe-only, a2 never changed");
}

PSX_MOD_CONSTRUCTOR(bag2jp_register_gaso_caught) {
    (void)psx_mod_register_activation_plugin("bag2jp.gaso_caught", gaso_caught_activate);
    (void)psx_mod_register_session_reset_plugin("bag2jp.gaso_caught",
                                                gaso_caught_session_reset);
    (void)psx_mod_register_savestate_plugin("bag2jp.gaso_caught",
                                            gaso_caught_savestate);
    (void)psx_mod_register_function_entry_plugin(
        "bag2jp.gaso_caught", GASO_CAUGHT_ENTRY_ADDRESS, gaso_caught_entry_cb);
    (void)psx_mod_register_instruction_plugin(
        "bag2jp.gaso_caught_capture", GASO_PRODUCER_SITE, GASO_PRODUCER_EXPECTED,
        gaso_caught_capture_cb);
}
