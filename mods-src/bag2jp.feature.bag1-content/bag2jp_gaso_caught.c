/* Experimental CAUGHT entry seam, default-off (feature bag1-gaso-caught) and
 * inert while GASO_CAUGHT_CLIP_PUBLISHED is 0: the shipped source never writes
 * guest RAM from a hook and never changes a2. Request 202 has already become
 * slot 89 before FUN_8002d06c; it must not be matched as a controller-entry
 * request.
 *
 * Hook contract: publish borrowed slot1 before the original controller body,
 * then change a2=1; never write the actor's pending at +0x18. A record is taken
 * only by the recipient main actor's entry with mode 1 and slot 89, and it is
 * consumed by that take whether or not a2 changes.
 *
 * Experimental publication (CLIP_PUBLISHED=1 build-tree only): the take runs
 * the bag2jp_caught_binding.h publish on a host copy of the spans it checks
 * and mirrors its three slot1 writes; a2 becomes 1 only when slot1 holds this
 * clip. Every later entry call checks retirement first and restores the empty
 * tuple through the same contract once the actor left slot1 (see
 * GASO_CAUGHT_UNSTARTED_TICKS). Unproven in game; P2b generation is open.
 * A verified take also clears the recipient's native secondary selector1 at
 * +0x1724 (one halfword), including its generic impact cue; not visual-only.
 *
 * Producer-site capture: runs immediately before sh v0,0x18(s5) at 0x8009b5b4,
 * reads the original registers (v0=request, s2=source_side, s4=recipient_side,
 * s5=pending, sp=stack) and guest RAM through psx_mod_read_*, validates against
 * the pinned original code sites, and stores one record per recipient side in
 * captured[] only for a direct (non-reflected) request whose source main actor
 * is Gas-O with the BAG1 version selected. Heat and Strike publish the same
 * request 202; their publications only invalidate the recipient's record.
 * Hooks never allocate; they write guest RAM and a2 only in the published
 * build, as described above. Host-only counters (TCP mod_counters) report every
 * producer-site call as capture_stored/capture_rejected and every take as
 * entry_taken; the same events and the rejection reason go to
 * bag2jp_bag1_versions.log, the only channel in builds without debug tools.
 *
 * Activation (P1) prepares the authentic 1048-byte clip bank once per process
 * in Expansion 1 (bag2jp_caught_bank.c): one allocation, a verified copy, and
 * no retry or repair on later activations. P2a looks up the recipient's clip
 * at entry for diagnostics only: readiness is not permission to publish it.
 *
 * Still required before the source default may become 1: authenticated
 * recipient/table generation (P2b), in-game evidence of the retirement and
 * owner acceptance. A load reclaims a published tuple read-only against the
 * native empty tuple (gaso_caught_recover_slot1); a reset does not, and a
 * later publication on those tables fails closed.
 * Do not allocate placeholder clips or publish slot1 without a captured record.
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
#define GASO_CAUGHT_REG_A3 7                 /* requested blend cap */
#define GASO_CAUGHT_REG_SP 29
#define GASO_CAUGHT_MODE_ADVANCE 0u
#define GASO_CAUGHT_MODE_ENTRY 1u
#define GASO_CAUGHT_FULL_BLEND 0x1000u
#define GASO_CAUGHT_BLEND_OFF 0x1546u
#define GASO_CAUGHT_FRAME_OFF 0x1554u
#define GASO_CAUGHT_LAST_FRAME 1u
#define GASO_CAUGHT_CTRL_FLAG_A 0x0au          /* entry clears; must already be 0 */
#define GASO_CAUGHT_CTRL_FLAG_B 0x0bu          /* entry clears; must already be 0 */
#define GASO_CAUGHT_CTRL_RATE 0x14u
#define GASO_CAUGHT_CTRL_TICKS 0x18u
#define GASO_CAUGHT_CTRL_SPEED_ARG 0x1cu
#define GASO_CAUGHT_CTRL_FRAME_COPY 0x24u       /* entry copies frame 0 here */
#define GASO_CAUGHT_ENTRY_FRAME_COPY 0u
#define GASO_CAUGHT_CTRL_BYTES 0x28u
#define GASO_CAUGHT_STACK_SPEED_ARG 0x10u
#define GASO_CAUGHT_STACK_ARG_BYTES 0x14u
#define GASO_CAUGHT_FIXED_SPEED_BIT 0x80000000u
#define GASO_CAUGHT_NO_TICK_TIMER 0xffffffffu
#define GASO_CAUGHT_HIT_SLOT 89u             /* request 202 translated */
#define GASO_CAUGHT_SECONDARY_EFFECT 0x1724u /* native visual/audio selector */
#define GASO_CAUGHT_SECONDARY_HIT 1u         /* eight hit particles, including stars */
#define GASO_CAUGHT_ARG_A2 1                 /* borrowed slot1 */
#define GASO_CAUGHT_CHARACTER 9              /* Gas-O, GASO_CHAR_ID */
#define GASO_CAUGHT_INIT_SITE 0x8002ba18u     /* Before JAL to native controller init. */
#define GASO_CAUGHT_INIT_WORD 0x0c00b617u     /* jal 0x8002d85c, JP main executable. */
#define GASO_CAUGHT_CONTROLLERS 0x8005f820u
#define GASO_CAUGHT_CONTROLLER_STRIDE 0x98u  /* Main actors at control slots 0 and 2. */
#define GASO_CAUGHT_REG_S1 17
#define GASO_CAUGHT_REG_S2 18
#define GASO_CAUGHT_INIT_VECTOR 16u          /* a2 = sp+16 before native JAL. */
#define GASO_CAUGHT_INIT_STACK_BYTES 28u     /* Three-word home vector at sp+16. */
#define GASO_CAUGHT_MOTIONS 0x10u            /* actor's motion DFS, source of raw[] */

int bag2jp_bag1_has_version(int chr);
int bag2jp_bag1_get_version(int chr, int side);
/* Plays the tank cues requested by the tank visual (bag2jp_bag1_versions.c). */
void bag2jp_gaso_tank_play_cues(struct CPUState *cpu, uint32_t return_address);
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
/* Capture-to-entry drift guard, NOT proof of a load generation: a reload can
 * recreate identical pointers and bytes. The lifecycle ownership gate remains. */
#define GASO_CAUGHT_CAPTURE_ACTORS 2u         /* source and recipient */
#define GASO_CAUGHT_TABLE_FIELDS 4u           /* count, raw, length, metadata */
static uint32_t captured_tables[GASO_CAUGHT_SIDES]
                               [GASO_CAUGHT_CAPTURE_ACTORS][GASO_CAUGHT_TABLE_FIELDS];

/* Process-lifetime: the Expansion 1 arena is never freed, so a bank prepared
 * by one session's activation stays owned across later sessions. */
static B1CaughtBank bank;

/* Slot1 publication / restore state, one per recipient side.
 * Guarded by GASO_CAUGHT_CLIP_PUBLISHED: while 0 no guest write is ever
 * issued and a2 is never changed. Both directions run the validated
 * bag2jp_caught_binding.h transaction on a host copy of the spans it reads,
 * then mirror its three slot writes (raw word, length half, metadata word). */
static B1CaughtBinding gaso_caught_binding[GASO_CAUGHT_SIDES];
static B1CaughtBankClip gaso_caught_clip[GASO_CAUGHT_SIDES];
static int gaso_caught_published[GASO_CAUGHT_SIDES];
static int gaso_caught_entered[GASO_CAUGHT_SIDES];      /* actor seen on slot1 */
static int gaso_caught_restore_refused[GASO_CAUGHT_SIDES];
static uint32_t gaso_caught_restore_tries[GASO_CAUGHT_SIDES];
static uint32_t gaso_caught_info[GASO_CAUGHT_SIDES];     /* published metadata word */
static uint32_t gaso_caught_publish_tick[GASO_CAUGHT_SIDES];
static uint32_t gaso_caught_retry_tick[GASO_CAUGHT_SIDES];
static uint32_t gaso_caught_ticks;
/* Gas-O hits taken per recipient side, monotonic: the tank visual
 * (bag2jp_gaso_tank.h) drops a tank when this changes, the moment BAG1's
 * trap starts. Never reset, so a reader only compares against its own copy. */
static uint32_t gaso_caught_hits[GASO_CAUGHT_SIDES];
static uint32_t gaso_caught_epoch;
static uint32_t gaso_caught_epoch_hits[GASO_CAUGHT_SIDES];
/* Host serial of observed native init/reset/load boundaries. It revokes capture
 * authorization only, and is NOT serialized ownership of a published tuple. */
static uint64_t gaso_caught_capture_generation = 1u;

uint32_t bag2jp_gaso_caught_hits(uint32_t side) {
    return side < GASO_CAUGHT_SIDES ? gaso_caught_hits[side] : 0u;
}

uint32_t bag2jp_gaso_caught_epoch(void) {
    return gaso_caught_epoch;
}

/* Snapshot at the callback boundary, not at the next visual tick: a fresh
 * hit can arrive between those events and must not be mistaken for an old one. */
uint32_t bag2jp_gaso_caught_epoch_hits(uint32_t side) {
    return side < GASO_CAUGHT_SIDES ? gaso_caught_epoch_hits[side] : 0u;
}

/* Retirement (FUN_8002d06c, read 2026-11-12 in Ghidra/SLPM_862.19): the
 * controller stores current = a2 inside the same entry call (0x8002d4b8) and
 * previous = current when it returns (0x8002d6cc); it divides by
 * length[current] every tick (0x8002d644/0x8002d684) and when leaving the slot
 * (0x8002d494). So the clip has retired once the actor was seen on slot1 and
 * both current and previous left it; the contract refuses the restore while
 * either is still 1 or a decoder/pose word points into the clip.
 * If the actor is never seen on slot1 (the redirected call returned early),
 * the slot is restored after this many entry calls; calls, not frames. */
#define GASO_CAUGHT_UNSTARTED_TICKS 60u
#define GASO_CAUGHT_RETRY_TICKS 8u           /* calls between refused restores */
/* Refused restores before the publication is abandoned without writing. The
 * tuple left behind points into the never-freed bank with length 2, so the
 * controller cannot divide by zero on it; a later publication fails closed. */
#define GASO_CAUGHT_RESTORE_TRIES 32u

/* Sparse host copy of guest main RAM: only the spans the contract reads
 * (actor list, listed actors, their three tables, the original empty word).
 * Every other byte stays zero and is never read by b1cb_plan. */
#define GASO_CAUGHT_COPY_SPANS (2u + 4u * B1CB_ACTOR_COUNT)
#define GASO_CAUGHT_MAX_SLOTS 0x1000u        /* bound on copied table entries */
static uint8_t gaso_caught_ram[B1CB_MAX_RAM];
static struct { uint32_t offset, bytes; } gaso_caught_spans[GASO_CAUGHT_COPY_SPANS];
static unsigned gaso_caught_span_count;

/* Forward declarations: defined below, used by the entry callback. */
static int gaso_caught_build_binding(uint32_t side, const B1CaughtBankClip *clip,
                                     B1CaughtBinding *b) __attribute__((unused));
static void gaso_caught_publish_slot1(uint32_t side) __attribute__((unused));
static void gaso_caught_retire_slot1(void) __attribute__((unused));
static void gaso_caught_suppress_secondary(uint32_t side, uint32_t actor);
/* Contract directions: publish and restore write the slot1 tuple; verify only
 * confirms that slot1 still holds this clip for this actor. */
enum { GASO_CAUGHT_PUBLISH, GASO_CAUGHT_RESTORE, GASO_CAUGHT_VERIFY };
static int gaso_caught_transact(uint32_t side, int mode);

/* ---- Guest RAM reads through the runtime API ---- */

static uint32_t guest_read_word(uint32_t addr) {
    return psx_mod_read_word(addr);
}

static uint16_t guest_read_half(uint32_t addr) {
    return psx_mod_read_half(addr);
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

static void gaso_caught_invalidate_captures(void) {
    ++gaso_caught_capture_generation;
    for (uint32_t side = 0; side < GASO_CAUGHT_SIDES; ++side)
        captured[side].available = 0;
}

/* Observe the already instrumented native call; do not run init, change its
 * arguments/home vector, retire bindings or reset the tank's visual epoch. */
static void gaso_caught_init_cb(struct CPUState *cpu, uint32_t address) {
    if (address != GASO_CAUGHT_INIT_SITE ||
        guest_read_word(address) != GASO_CAUGHT_INIT_WORD ||
        cpu->gpr[GASO_CAUGHT_REG_A0] != cpu->gpr[GASO_CAUGHT_REG_S2] ||
        cpu->gpr[GASO_CAUGHT_REG_A1] != cpu->gpr[GASO_CAUGHT_REG_S1]) return;
    const uint32_t stack = cpu->gpr[GASO_CAUGHT_REG_SP];
    if ((stack & 3u) || !guest_range_ok(stack, GASO_CAUGHT_INIT_STACK_BYTES, 1) ||
        cpu->gpr[GASO_CAUGHT_REG_A2] != stack + GASO_CAUGHT_INIT_VECTOR) return;
    for (uint32_t side = 0; side < GASO_CAUGHT_SIDES; ++side) {
        if (cpu->gpr[GASO_CAUGHT_REG_A0] != GASO_CAUGHT_CONTROLLERS +
                                            side * GASO_CAUGHT_CONTROLLER_STRIDE) continue;
        const uint32_t actor = cpu->gpr[GASO_CAUGHT_REG_A1];
        if ((actor & 3u) || !guest_range_ok(actor, B1CB_ACTOR_BYTES, 0) ||
            guest_read_word(GASO_CS_ACTORS + side * GASO_CS_MAIN_STRIDE) != actor ||
            guest_read_byte(actor + GASO_CS_SIDE) != side ||
            guest_read_byte(actor + GASO_CS_CHARACTER) == 0xffu) return;
        gaso_caught_invalidate_captures();
        psx_mod_counter_add("gaso_caught.capture_generation", 1u);
        b1v_log("gaso_caught: capture generation=%llu side=%u (native init)",
                (unsigned long long)gaso_caught_capture_generation, (unsigned)side + 1u);
        return;
    }
}

static int gaso_caught_snapshot_tables(uint32_t side, const B1CaughtSource *record) {
    const uint32_t actors[GASO_CAUGHT_CAPTURE_ACTORS] = {record->source_actor, record->actor};
    for (uint32_t i = 0; i < GASO_CAUGHT_CAPTURE_ACTORS; ++i) {
        if (!guest_range_ok(actors[i], B1CB_META + sizeof(uint32_t), 0)) return 0;
        for (uint32_t field = 0; field < GASO_CAUGHT_TABLE_FIELDS; ++field)
            captured_tables[side][i][field] = guest_read_word(actors[i] + B1CB_COUNT +
                                                              field * sizeof(uint32_t));
    }
    return 1;
}

static int gaso_caught_capture_matches(uint32_t side) {
    const B1CaughtSource *r = &captured[side];
    const uint32_t actors[GASO_CAUGHT_CAPTURE_ACTORS] = {r->source_actor, r->actor};
    const uint32_t sides[GASO_CAUGHT_CAPTURE_ACTORS] = {r->source_side, r->side};
    const uint32_t characters[GASO_CAUGHT_CAPTURE_ACTORS] = {r->source_character, r->character};
    if (r->clock.generation != gaso_caught_capture_generation ||
        !bag2jp_bag1_has_version(GASO_CAUGHT_CHARACTER) ||
        !bag2jp_bag1_get_version(GASO_CAUGHT_CHARACTER, (int)r->source_side)) return 0;
    for (uint32_t i = 0; i < GASO_CAUGHT_CAPTURE_ACTORS; ++i) {
        if (sides[i] >= GASO_CAUGHT_SIDES ||
            !guest_range_ok(actors[i], B1CB_META + sizeof(uint32_t), 0) ||
            guest_read_word(GASO_CS_ACTORS + sides[i] * GASO_CS_MAIN_STRIDE) != actors[i] ||
            guest_read_byte(actors[i] + GASO_CS_CHARACTER) != characters[i] ||
            guest_read_byte(actors[i] + GASO_CS_SIDE) != sides[i]) return 0;
        for (uint32_t field = 0; field < GASO_CAUGHT_TABLE_FIELDS; ++field)
            if (guest_read_word(actors[i] + B1CB_COUNT + field * sizeof(uint32_t)) !=
                captured_tables[side][i][field]) return 0;
    }
    return 1;
}

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
    /* This is the host native-init/reset/load serial and controller-call serial, not a
     * native content generation or a game-frame clock. */
    value.clock.generation = gaso_caught_capture_generation;
    value.clock.tick = gaso_caught_ticks;
    value.actor = recipient_actor;
    value.character = recipient_char;
    value.side = recipient_side;
    value.source_actor = source_actor;
    value.source_character = source_char;
    value.source_side = source_side;
    value.request = request;
    value.reflected = reflected;
    value.available = 1;

    if (!gaso_caught_snapshot_tables(recipient_side, &value)) return "actor tables";
    captured[recipient_side] = value;
    return NULL;
}

/* ---- Entry callback: take the recipient's record once ---- */

/* Only called after VERIFY of an already published tuple. The caller has
 * renewed the capture lifetime (+0x44) before reaching this entry. For the
 * same settled static pose and unchanged fixed rate, advance mode keeps that
 * lifetime while avoiding a second entry reanchor (8002d06c). Any uncertain
 * timing/phase retains native entry. Never write a controller or actor timer.
 *
 * Known residuals of advance: it does not zero the sub-frame accumulator
 * (+0x10) nor the countdown (+0x20), and it does not run the character entry
 * callbacks (8003190c, which include the native cue for Gas-O 0x782). The
 * three guarded writes below (+0x0a, +0x0b, +0x24=0) are proven no-ops only
 * when the live values already match what mode1 would write. */
static int gaso_caught_can_continue(const struct CPUState *cpu, uint32_t actor) {
    const uint32_t controller = cpu->gpr[GASO_CAUGHT_REG_A0];
    const uint32_t stack = cpu->gpr[GASO_CAUGHT_REG_SP];
    if (!guest_range_ok(controller, GASO_CAUGHT_CTRL_BYTES, 0) ||
        !guest_range_ok(stack, GASO_CAUGHT_STACK_ARG_BYTES, 0) ||
        cpu->gpr[GASO_CAUGHT_REG_A3] != GASO_CAUGHT_FULL_BLEND ||
        guest_read_word(actor + B1CB_CURRENT) != B1CB_SLOT ||
        guest_read_word(actor + B1CB_PREVIOUS) != B1CB_SLOT ||
        guest_read_word(actor + GASO_CAUGHT_FRAME_OFF) != GASO_CAUGHT_LAST_FRAME ||
        guest_read_half(actor + GASO_CAUGHT_BLEND_OFF) != GASO_CAUGHT_FULL_BLEND)
        return 0;
    const uint32_t speed = guest_read_word(controller + GASO_CAUGHT_CTRL_SPEED_ARG);
    return (speed & GASO_CAUGHT_FIXED_SPEED_BIT) &&
           speed == guest_read_word(stack + GASO_CAUGHT_STACK_SPEED_ARG) &&
           guest_read_word(controller + GASO_CAUGHT_CTRL_RATE) == 0u - speed &&
           guest_read_word(controller + GASO_CAUGHT_CTRL_TICKS) == GASO_CAUGHT_NO_TICK_TIMER &&
           guest_read_byte(controller + GASO_CAUGHT_CTRL_FLAG_A) == 0u &&
           guest_read_byte(controller + GASO_CAUGHT_CTRL_FLAG_B) == 0u &&
           guest_read_word(controller + GASO_CAUGHT_CTRL_FRAME_COPY) == GASO_CAUGHT_ENTRY_FRAME_COPY;
}

static void gaso_caught_entry_cb(struct CPUState *cpu, uint32_t address) {
    int side;
    uint32_t actor;
    int continuing = 0;
    if (address != GASO_CAUGHT_ENTRY_ADDRESS) return;
    ++gaso_caught_ticks;
    bag2jp_gaso_tank_play_cues(cpu, address);
    if (GASO_CAUGHT_CLIP_PUBLISHED) gaso_caught_retire_slot1();
    for (side = 0; side < GASO_CAUGHT_SIDES; ++side)
        if (captured[side].available) break;
    /* No record: leave the controller untouched; only a published slot's
     * retirement above reads guest RAM. */
    if (side == GASO_CAUGHT_SIDES) return;
    if (cpu->gpr[GASO_CAUGHT_REG_A1] != GASO_CAUGHT_MODE_ENTRY ||
        cpu->gpr[GASO_CAUGHT_REG_A2] != GASO_CAUGHT_HIT_SLOT) return;
    if (!guest_range_ok(cpu->gpr[GASO_CAUGHT_REG_A0], 4u, 0)) return;
    actor = guest_read_word(cpu->gpr[GASO_CAUGHT_REG_A0]);
    for (side = 0; side < GASO_CAUGHT_SIDES; ++side) {
        if (!captured[side].available) continue;
        /* A replacement controller no longer names the captured actor. Revoke
         * drift before matching the incoming actor, but leave valid records
         * for the other actor available until their own entry arrives. */
        if (!gaso_caught_capture_matches((uint32_t)side)) {
            captured[side].available = 0;
            psx_mod_counter_add("gaso_caught.capture_stale", 1u);
            b1v_log("gaso_caught: capture stale side=%u actor=%08x (identity/tables)",
                    (unsigned)side + 1u, (unsigned)captured[side].actor);
            continue;
        }
        if (captured[side].actor != actor) continue;
        /* Consume once, even while no clip is published. */
        captured[side].available = 0;
        ++gaso_caught_hits[side];
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
                (unsigned)actor, GASO_CAUGHT_CLIP_PUBLISHED ? "pending publication" : "unchanged",
                (unsigned)character, (unsigned)version, ready ? "ready" : "rejected",
                (unsigned)clip.clip, (unsigned)clip.clip_bytes);
        /* Publish slot1 before changing a2; redirect only onto a slot that holds
         * this clip for this actor, never onto the empty tuple (length 0 is a
         * divisor). Retirement ran first in this call and forgot a tuple the
         * game rewrote; a second take reuses a still-published clip only after
         * the contract confirms it in guest RAM. */
        if (!GASO_CAUGHT_CLIP_PUBLISHED || !ready) return;
        if (gaso_caught_published[side]) {
            if (gaso_caught_binding[side].actor != actor ||
                gaso_caught_clip[side].clip != clip.clip) return;
            if (!gaso_caught_transact((uint32_t)side, GASO_CAUGHT_VERIFY)) {
                b1v_log("gaso_caught: slot1 reuse refused side=%u actor=%08x (contract)",
                        (unsigned)side + 1u, (unsigned)actor);
                return;
            }
            gaso_caught_publish_tick[side] = gaso_caught_ticks;
            continuing = gaso_caught_can_continue(cpu, actor);
            b1v_log("gaso_caught: slot1 reused side=%u actor=%08x mode=%u (verified)",
                    (unsigned)side + 1u, (unsigned)actor,
                    continuing ? GASO_CAUGHT_MODE_ADVANCE : GASO_CAUGHT_MODE_ENTRY);
        } else {
            if (!gaso_caught_build_binding(side, &clip, &gaso_caught_binding[side])) {
                b1v_log("gaso_caught: slot1 publish refused side=%u actor=%08x (unreadable)",
                        (unsigned)side + 1u, (unsigned)actor);
                return;
            }
            gaso_caught_clip[side] = clip;
            gaso_caught_publish_slot1(side);
        }
        if (gaso_caught_published[side]) {
            cpu->gpr[GASO_CAUGHT_REG_A2] = GASO_CAUGHT_ARG_A2;
            if (continuing) cpu->gpr[GASO_CAUGHT_REG_A1] = GASO_CAUGHT_MODE_ADVANCE;
            gaso_caught_suppress_secondary((uint32_t)side, actor);
        }
        return;
    }
}

/* Slot1's native empty raw word, derived like the table builders (FUN_80031d3c,
 * 800319fc and 800326d4 via FUN_800125fc, read 2026-11-15): the motion DFS at
 * actor+0x10 is [size][payload]... ending in size 0, and raw[i] = &payload i.
 * Its payload's first word 0 makes FUN_8001262c/800126a4 store length 0 and
 * metadata 0. raw[0] must still match. The contract checks the zero word.
 * Never inferred from a zero word or from host state older than a load. */
static int gaso_caught_native_empty(uint32_t actor, uint32_t raw_table, uint32_t *empty) {
    const uint32_t ram_bytes = memory_get_ram_bytes();
    const uint32_t motions = guest_read_word(actor + GASO_CAUGHT_MOTIONS);
    if ((motions & 3u) || !guest_range_ok(motions, 4u, 0)) return 0;
    const uint32_t size0 = guest_read_word(motions);
    if (!size0 || (size0 & 3u) || size0 >= ram_bytes ||
        !guest_range_ok(motions, 8u + size0, 0) ||
        guest_read_word(raw_table) != motions + 4u) return 0;
    const uint32_t entry1 = motions + 4u + size0;
    const uint32_t size1 = guest_read_word(entry1);
    if (size1 < 4u || (size1 & 3u) || !guest_range_ok(entry1 + 4u, size1, 0)) return 0;
    *empty = entry1 + 4u;
    return 1;
}

/* Binding facts from a main actor and its live tables. The contract then
 * requires the native empty tuple (empty_raw, 0, 0) before any publication.
 * Returns 0 when the actor or its tables cannot be read or derived. */
static int gaso_caught_bind(uint32_t actor, uint32_t character, uint32_t side,
                            const B1CaughtBankClip *clip, B1CaughtBinding *b) {
    if ((actor & 3u) || !guest_range_ok(actor, B1CB_ACTOR_BYTES, 0)) return 0;
    *b = (B1CaughtBinding){0};
    b->actor = actor;
    b->character = character;
    b->side = side;
    b->count = guest_read_word(actor + B1CB_COUNT);
    b->raw_table = guest_read_word(actor + B1CB_RAW);
    b->length_table = guest_read_word(actor + B1CB_LENGTH);
    b->metadata_table = guest_read_word(actor + B1CB_META);
    if (b->count <= B1CB_SLOT || (b->raw_table & 3u) ||
        !guest_range_ok(b->raw_table, 4u * (B1CB_SLOT + 1u), 0) ||
        !gaso_caught_native_empty(actor, b->raw_table, &b->empty_raw)) return 0;
    b->clip = clip->clip;
    b->clip_bytes = clip->clip_bytes;
    return 1;
}

static int gaso_caught_build_binding(uint32_t side, const B1CaughtBankClip *clip,
                                     B1CaughtBinding *b) {
    return gaso_caught_bind(captured[side].actor, captured[side].character,
                            captured[side].side, clip, b);
}

/* ---- Host copy of the contract's main-RAM spans ---- */

static void gaso_caught_copy_clear(void) {
    for (unsigned i = 0; i < gaso_caught_span_count; ++i)
        memset(gaso_caught_ram + gaso_caught_spans[i].offset, 0, gaso_caught_spans[i].bytes);
    gaso_caught_span_count = 0;
}

static int gaso_caught_copy(uint32_t addr, uint32_t bytes) {
    if (!bytes || !guest_range_ok(addr, bytes, 0) ||
        gaso_caught_span_count >= GASO_CAUGHT_COPY_SPANS) return 0;
    const uint32_t offset = addr - GASO_CS_RAM;
    uint32_t i = 0;
    /* Aligned words where possible: a quarter of the traced reads. */
    for (; i < bytes && (addr + i) % 4u; ++i)
        gaso_caught_ram[offset + i] = guest_read_byte(addr + i);
    for (; bytes - i >= 4u; i += 4u)
        b1cb_write(gaso_caught_ram, offset + i, guest_read_word(addr + i), 4);
    for (; i < bytes; ++i)
        gaso_caught_ram[offset + i] = guest_read_byte(addr + i);
    gaso_caught_spans[gaso_caught_span_count].offset = offset;
    gaso_caught_spans[gaso_caught_span_count].bytes = bytes;
    ++gaso_caught_span_count;
    return 1;
}

static uint32_t gaso_caught_copied_word(uint32_t addr) {
    return b1cb_read(gaso_caught_ram, addr - GASO_CS_RAM, 4);
}

/* A listed actor and its three tables. Fails like the contract would on an
 * unreadable entry; count is bounded so a corrupt actor cannot stall a frame. */
static int gaso_caught_copy_actor(uint32_t actor) {
    if (!gaso_caught_copy(actor, B1CB_ACTOR_BYTES)) return 0;
    const uint32_t count = gaso_caught_copied_word(actor + B1CB_COUNT);
    if (count <= B1CB_SLOT || count > GASO_CAUGHT_MAX_SLOTS) return 0;
    return gaso_caught_copy(gaso_caught_copied_word(actor + B1CB_RAW), 4u * count) &&
           gaso_caught_copy(gaso_caught_copied_word(actor + B1CB_LENGTH), 2u * count) &&
           gaso_caught_copy(gaso_caught_copied_word(actor + B1CB_META), 4u * count);
}

static int gaso_caught_copy_load(const B1CaughtBinding *b) {
    gaso_caught_copy_clear();
    if (!gaso_caught_copy(B1CB_ACTORS, 4u * B1CB_ACTOR_COUNT)) return 0;
    for (uint32_t i = 0; i < B1CB_ACTOR_COUNT; ++i) {
        const uint32_t actor = gaso_caught_copied_word(B1CB_ACTORS + 4u * i);
        if (actor && !gaso_caught_copy_actor(actor)) return 0;
    }
    return gaso_caught_copy(b->empty_raw, 4u);
}

/* Run one contract direction and mirror its three slot writes to the guest.
 * The entry callback runs inside the guest's own call, so the guest is
 * stopped between the copy, the checks and the writes (paused = 1); the
 * restore's quiescence is the caller's slot1-left observation. Verify runs
 * the same identity/layout and tuple checks, without the restore-only
 * retirement guards: reuse is valid while the actor decodes this clip. */
static int gaso_caught_transact(uint32_t side, int mode) {
    const B1CaughtBinding *b = &gaso_caught_binding[side];
    const B1CaughtBankClip *clip = &gaso_caught_clip[side];
    const B1CaughtClipRegion region = {clip->allocation_data, clip->allocation_base,
                                       clip->allocation_bytes};
    const uint32_t ram_bytes = memory_get_ram_bytes();
    B1CaughtWritePlan plan;
    int ok = ram_bytes <= B1CB_MAX_RAM && gaso_caught_copy_load(b);
    if (ok && mode == GASO_CAUGHT_VERIFY)
        ok = b1cb_inspect(gaso_caught_ram, ram_bytes, b, 1, &region, &plan) &&
             b1cb_tuple(gaso_caught_ram, &plan, b->clip, B1CB_FRAMES, plan.info);
    else if (ok)
        ok = mode == GASO_CAUGHT_RESTORE
                 ? b1cb_restore_in(gaso_caught_ram, ram_bytes, b, 1, 1, &region)
                 : b1cb_publish_in(gaso_caught_ram, ram_bytes, b, 1, &region);
    if (ok && mode != GASO_CAUGHT_VERIFY) {
        const uint32_t raw = b->raw_table + 4u * B1CB_SLOT;
        const uint32_t length = b->length_table + 2u * B1CB_SLOT;
        const uint32_t meta = b->metadata_table + 4u * B1CB_SLOT;
        psx_mod_write_word(raw, gaso_caught_copied_word(raw));
        psx_mod_write_half(length, (uint16_t)b1cb_read(gaso_caught_ram, length - GASO_CS_RAM, 2));
        psx_mod_write_word(meta, gaso_caught_copied_word(meta));
        if (mode == GASO_CAUGHT_PUBLISH) gaso_caught_info[side] = gaso_caught_copied_word(meta);
    }
    gaso_caught_copy_clear();
    return ok;
}

/* The published tuple and the actor words the binding fixed are unchanged.
 * Twelve reads of addresses the contract validated at publication (RAM size
 * is fixed per session); any change means the game rewrote or moved them,
 * e.g. a character reload without a plan reset. */
static int gaso_caught_slot1_intact(uint32_t side) {
    const B1CaughtBinding *b = &gaso_caught_binding[side];
    return guest_read_byte(b->actor + 4u) == b->character &&
           guest_read_byte(b->actor + 5u) == b->side &&
           guest_read_word(b->actor + B1CB_COUNT) == b->count &&
           guest_read_word(b->actor + B1CB_RAW) == b->raw_table &&
           guest_read_word(b->actor + B1CB_LENGTH) == b->length_table &&
           guest_read_word(b->actor + B1CB_META) == b->metadata_table &&
           guest_read_word(b->raw_table + 4u * B1CB_SLOT) == b->clip &&
           guest_read_half(b->length_table + 2u * B1CB_SLOT) == B1CB_FRAMES &&
           guest_read_word(b->metadata_table + 4u * B1CB_SLOT) == gaso_caught_info[side];
}

/* Read-only ownership query for the tank visual. An ordinary slot1 is not
 * CAUGHT; require both the publication and its original live tuple. */
int bag2jp_gaso_caught_owns_slot1(uint32_t side, uint32_t actor) {
    return GASO_CAUGHT_CLIP_PUBLISHED && side < GASO_CAUGHT_SIDES &&
           gaso_caught_published[side] &&
           gaso_caught_binding[side].actor == actor && gaso_caught_slot1_intact(side);
}

/* The producer has already initialised this independent native effect before
 * controller entry. Clear it only after publication/VERIFY succeeded: doing
 * it at the producer would erase native feedback even when CAUGHT fails closed.
 * Selector1 includes its generic sound0x0e; this is not a visual-only change. */
static void gaso_caught_suppress_secondary(uint32_t side, uint32_t actor) {
    if (!bag2jp_gaso_caught_owns_slot1(side, actor) ||
        !guest_range_ok(actor, GASO_CAUGHT_SECONDARY_EFFECT + sizeof(uint16_t), 0)) return;
    const uint32_t selector = actor + GASO_CAUGHT_SECONDARY_EFFECT;
    if (guest_read_half(selector) == GASO_CAUGHT_SECONDARY_HIT)
        psx_mod_write_half(selector, 0u);
}

/* Publish (clip, 2 frames, info) into the recipient's empty slot1 before the
 * controller consumes the entry. Never writes while CLIP_PUBLISHED is 0. */
static void gaso_caught_publish_slot1(uint32_t side) {
    if (!GASO_CAUGHT_CLIP_PUBLISHED || gaso_caught_published[side]) return;
    const B1CaughtBinding *b = &gaso_caught_binding[side];
    if (!gaso_caught_transact(side, GASO_CAUGHT_PUBLISH)) {
        b1v_log("gaso_caught: slot1 publish refused side=%u actor=%08x (contract)",
                side + 1, (unsigned)b->actor);
        return;
    }
    gaso_caught_published[side] = 1;
    gaso_caught_entered[side] = 0;
    gaso_caught_restore_refused[side] = 0;
    gaso_caught_restore_tries[side] = 0;
    gaso_caught_publish_tick[side] = gaso_caught_ticks;
    psx_mod_counter_add("gaso_caught.slot1_published", 1u);
    b1v_log("gaso_caught: slot1 published side=%u clip=%08x bytes=%u, a2 -> 1", side + 1,
            (unsigned)b->clip, (unsigned)b->clip_bytes);
}

/* Restore the original empty tuple once the clip retired (see
 * GASO_CAUGHT_UNSTARTED_TICKS). A tuple the game rewrote is forgotten without
 * writing. A refused restore is logged once per publication, retried on later
 * calls and abandoned without writing after GASO_CAUGHT_RESTORE_TRIES. */
static void gaso_caught_retire_slot1(void) {
    for (uint32_t side = 0; side < GASO_CAUGHT_SIDES; ++side) {
        if (!gaso_caught_published[side]) continue;
        const uint32_t actor = gaso_caught_binding[side].actor;
        if (!gaso_caught_slot1_intact(side)) {
            gaso_caught_published[side] = 0;
            psx_mod_counter_add("gaso_caught.slot1_lost", 1u);
            b1v_log("gaso_caught: slot1 lost side=%u actor=%08x (rewritten by the game)",
                    side + 1, (unsigned)actor);
            continue;
        }
        const uint32_t current = guest_read_word(actor + B1CB_CURRENT);
        const uint32_t previous = guest_read_word(actor + B1CB_PREVIOUS);
        if (current == B1CB_SLOT || previous == B1CB_SLOT) {
            if (!gaso_caught_entered[side])
                b1v_log("gaso_caught: slot1 entered side=%u", side + 1);
            gaso_caught_entered[side] = 1;
            continue;
        }
        if (!gaso_caught_entered[side] &&
            gaso_caught_ticks - gaso_caught_publish_tick[side] < GASO_CAUGHT_UNSTARTED_TICKS)
            continue;
        if (gaso_caught_restore_refused[side] &&
            gaso_caught_ticks - gaso_caught_retry_tick[side] < GASO_CAUGHT_RETRY_TICKS)
            continue;
        if (!gaso_caught_transact(side, GASO_CAUGHT_RESTORE)) {
            if (++gaso_caught_restore_tries[side] >= GASO_CAUGHT_RESTORE_TRIES) {
                gaso_caught_published[side] = 0;
                psx_mod_counter_add("gaso_caught.slot1_abandoned", 1u);
                b1v_log("gaso_caught: slot1 restore abandoned side=%u after %u refusals",
                        side + 1, (unsigned)GASO_CAUGHT_RESTORE_TRIES);
                continue;
            }
            if (!gaso_caught_restore_refused[side])
                b1v_log("gaso_caught: slot1 restore refused side=%u current=%u previous=%u; retrying",
                        side + 1, (unsigned)current, (unsigned)previous);
            gaso_caught_restore_refused[side] = 1;
            gaso_caught_retry_tick[side] = gaso_caught_ticks;
            continue;
        }
        gaso_caught_published[side] = 0;
        psx_mod_counter_add("gaso_caught.slot1_restored", 1u);
        b1v_log("gaso_caught: slot1 restored side=%u (%s)", side + 1,
                gaso_caught_entered[side] ? "clip left slot1" : "clip never started");
    }
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
static void gaso_caught_forget(void) {
    ++gaso_caught_epoch;
    gaso_caught_invalidate_captures();
    for (uint32_t side = 0; side < GASO_CAUGHT_SIDES; ++side) {
        gaso_caught_epoch_hits[side] = gaso_caught_hits[side];
        gaso_caught_published[side] = 0;
        gaso_caught_entered[side] = 0;
        gaso_caught_restore_refused[side] = 0;
        gaso_caught_restore_tries[side] = 0;
        gaso_caught_info[side] = 0;
        gaso_caught_publish_tick[side] = 0;
        gaso_caught_retry_tick[side] = 0;
        gaso_caught_binding[side] = (B1CaughtBinding){0};
        gaso_caught_clip[side] = (B1CaughtBankClip){0};
    }
}

/* Known limit: a reset does not recover a tuple published before it (a real
 * reset rebuilds the tables). If one survives, a later publication on the
 * same tables fails closed: slot1 no longer holds the native empty tuple. */
static void gaso_caught_session_reset(void) {
    gaso_caught_forget();
}

/* The binding left behind is unused: the side stays unpublished. */
static void gaso_caught_recovery_refused(uint32_t side, uint32_t actor, const char *reason) {
    b1v_log("gaso_caught: slot1 recovery refused side=%u actor=%08x (%s)",
            (unsigned)side + 1u, (unsigned)actor, reason);
}

/* Reclaim a tuple published before the loaded snapshot was taken. Read-only:
 * only this bank's exact clip in a main actor's slot1 is claimed, and only
 * when the contract VERIFY holds against the native empty tuple. Anything
 * else is not ours and stays untouched. The retirement on later entry calls
 * restores it, so a load never writes guest RAM. Known limit: with the bank
 * not ready or at another base (load before activation, other process), a
 * tuple of ours is not recognised and stays unrecovered without a log. */
static void gaso_caught_recover_slot1(void) {
    for (uint32_t side = 0; side < GASO_CAUGHT_SIDES; ++side) {
        const uint32_t actor = guest_read_word(GASO_CS_ACTORS + side * GASO_CS_MAIN_STRIDE);
        if ((actor & 3u) || !guest_range_ok(actor, B1CB_ACTOR_BYTES, 0) ||
            guest_read_byte(actor + GASO_CS_SIDE) != side) continue;
        const uint32_t character = guest_read_byte(actor + GASO_CS_CHARACTER);
        const uint32_t raw_table = guest_read_word(actor + B1CB_RAW);
        B1CaughtBankClip clip = {0};
        if ((raw_table & 3u) || !guest_range_ok(raw_table + 4u * B1CB_SLOT, 4u, 0) ||
            !b1cc_lookup(&bank, character, B1CC_BAG1_VERSION, &clip) ||
            guest_read_word(raw_table + 4u * B1CB_SLOT) != clip.clip) continue;
        if (!gaso_caught_bind(actor, character, side, &clip, &gaso_caught_binding[side])) {
            gaso_caught_recovery_refused(side, actor, "native tables");
            continue;
        }
        gaso_caught_clip[side] = clip;
        if (!gaso_caught_transact(side, GASO_CAUGHT_VERIFY)) {
            gaso_caught_recovery_refused(side, actor, "contract");
            continue;
        }
        /* VERIFY matched the metadata word; retirement observes slot1 entry and
         * waits GASO_CAUGHT_UNSTARTED_TICKS like a fresh publication. */
        gaso_caught_info[side] = guest_read_word(gaso_caught_binding[side].metadata_table +
                                                 4u * B1CB_SLOT);
        gaso_caught_published[side] = 1;
        gaso_caught_publish_tick[side] = gaso_caught_ticks;
        psx_mod_counter_add("gaso_caught.slot1_recovered", 1u);
        b1v_log("gaso_caught: slot1 recovered side=%u actor=%08x clip=%08x after load",
                (unsigned)side + 1u, (unsigned)actor, (unsigned)clip.clip);
    }
}

/* Savestate runs after successful guest-state restore, before the restored PC
 * resumes. Rebind host hooks here; do not advance guest gameplay. Clearing
 * captured[] keeps an obsolete record from surviving a load: actor buffers are
 * fixed RAM and controller+0x18 is reset to -1 at every phase-3 pair setup, so
 * a pre-load capture no longer matches any live actor. The published build
 * then reclaims a loaded tuple read-only. No guest writes, no allocation, no
 * publication; the shipped default does not read guest RAM here.
 */
static void gaso_caught_savestate(void) {
    gaso_caught_forget();
    if (GASO_CAUGHT_CLIP_PUBLISHED) gaso_caught_recover_slot1();
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
    (void)psx_mod_register_instruction_plugin(
        "bag2jp.gaso_caught", GASO_CAUGHT_INIT_SITE, GASO_CAUGHT_INIT_WORD,
        gaso_caught_init_cb);
}
