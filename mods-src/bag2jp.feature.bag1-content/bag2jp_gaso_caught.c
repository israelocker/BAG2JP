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
 * Never writes guest RAM, CPU registers (except a2 in the entry callback), or
 * allocates guest memory.
 *
 * Required before GASO_CAUGHT_CLIP_PUBLISHED: authentic per-rival guest clip
 * bytes, bounded exclusive RAM access, persistent loan ownership, safe
 * retirement and reset/savestate handling. Do not allocate placeholder clips
 * or publish slot1 here without a captured record.
 * See notes/gaso-import.md, caught-entry-recovery-20261111.
 */
#include <stdint.h>
#include <string.h>
#include "mod_plugins.h"
#include "cpu_state.h"
#include "bag2jp_caught_source.h"

/* No authentic clip is resident in guest RAM yet (P1). Host tests build with 1
 * to exercise the redirect; every runtime build must keep 0. */
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

/* ---- Guest RAM reads through the runtime API ---- */

static uint32_t guest_read_word(uint32_t addr) {
    return psx_mod_read_word(addr);
}

static uint8_t guest_read_byte(uint32_t addr) {
    return psx_mod_read_byte(addr);
}

/* ---- Producer-site capture ---- */

/* Capture the original request202 source before sh v0,0x18(s5) publishes it.
 * Reads guest RAM through psx_mod_read_* since we don't have a full RAM buffer.
 * Returns 1 if a record was stored, 0 otherwise. Never writes guest RAM or CPU
 * registers. */
static int capture_producer_source(struct CPUState *cpu) {
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
    if (recipient_side > 1u) return 0;
    captured[recipient_side].available = 0;

    /* Register validation */
    if (request != GASO_CS_REQUEST) return 0;
    if (source_side > 1u) return 0;
    if (pending != GASO_CS_PENDING + GASO_CS_PENDING_STRIDE * recipient_side) return 0;
    if (sp < GASO_CS_STACK_BYTES) return 0;

    /* Validate original code sites haven't drifted */
    if (guest_read_word(GASO_CS_OVERLAY_BASE_PTR) != GASO_CS_OVERLAY_BASE) return 0;
    if (guest_read_word(GASO_CS_LOAD_CHAR_BYTE) != GASO_CS_LOAD_CHAR_BYTE_EXPECTED) return 0;
    if (guest_read_word(GASO_CS_LOAD_DELAY_NOP) != GASO_CS_LOAD_DELAY_NOP_EXPECTED) return 0;
    if (guest_read_word(GASO_PRODUCER_SITE) != GASO_PRODUCER_EXPECTED) return 0;

    /* Stack flag: reflected=2 when source==recipient, else 1 (direct) */
    const uint32_t reflected = (source_side == recipient_side) ? 1u : 0u;
    const uint32_t expected_flag = reflected ? GASO_CS_FLAG_REFLECTED : GASO_CS_FLAG_DIRECT;
    if (guest_read_byte(sp + GASO_CS_STACK_FLAGS + recipient_side) != expected_flag) return 0;

    /* Validate actors: main list at 0x8005f808, each 8 bytes */
    uint32_t actors[2];
    for (uint32_t side = 0; side < 2; ++side) {
        actors[side] = guest_read_word(GASO_CS_ACTORS + side * GASO_CS_MAIN_STRIDE);
        if (actors[side] == 0u) return 0;
        if (guest_read_byte(actors[side] + GASO_CS_SIDE) != (uint8_t)side) return 0;
    }
    if (actors[0] == actors[1]) return 0;

    const uint32_t recipient_actor = actors[recipient_side];
    const uint32_t source_actor = actors[source_side];
    const uint8_t recipient_char = guest_read_byte(recipient_actor + GASO_CS_CHARACTER);
    const uint8_t source_char = guest_read_byte(source_actor + GASO_CS_CHARACTER);

    if (source_char >= GASO_CS_VERIFIED_TABLE_ROWS) return 0;
    const uint32_t table_row = GASO_CS_TABLE + GASO_CS_TABLE_ROW_STRIDE * (uint32_t)source_char;
    if (guest_read_byte(table_row) != request) return 0;

    /* Request 202 is shared with Heat and Strike: only a direct Gas-O BAG1
     * attacker may own a record. */
    if (reflected || source_char != GASO_CAUGHT_CHARACTER) return 0;
    if (!bag2jp_bag1_has_version(GASO_CAUGHT_CHARACTER) ||
        !bag2jp_bag1_get_version(GASO_CAUGHT_CHARACTER, (int)source_side)) return 0;

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
    return 1;
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
        if (GASO_CAUGHT_CLIP_PUBLISHED)
            cpu->gpr[GASO_CAUGHT_REG_A2] = GASO_CAUGHT_ARG_A2;
        return;
    }
}

/* ---- Producer-site instruction callback ---- */

static void gaso_caught_capture_cb(struct CPUState *cpu, uint32_t address) {
    if (address != GASO_PRODUCER_SITE) return;
    capture_producer_source(cpu);
}

PSX_MOD_CONSTRUCTOR(bag2jp_register_gaso_caught) {
    (void)psx_mod_register_function_entry_plugin(
        "bag2jp.gaso_caught", GASO_CAUGHT_ENTRY_ADDRESS, gaso_caught_entry_cb);
    (void)psx_mod_register_instruction_plugin(
        "bag2jp.gaso_caught_capture", GASO_PRODUCER_SITE, GASO_PRODUCER_EXPECTED,
        gaso_caught_capture_cb);
}
