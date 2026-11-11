/* Experimental composition of the pinned CAUGHT loan policy with the paused
 * byte-RAM transaction. NOT included by the runtime.
 *
 * Contract proven by executing the original FUN_8002d06c on the production
 * interpreter (probe13): the entry tick advances and fires the OLD clip's
 * pending events, THEN adopts the requested slot and decodes it in that same
 * tick. Therefore slot1 must be published before the entry request reaches the
 * controller, and retirement may only happen while neither `current` nor
 * `previous` refers to slot1.
 *
 * Return contract
 *   1  the observation was handled and RAM plus loan state stayed consistent;
 *   0  the decided transition could not be completed; nothing changed (except
 *      the infallible writes of a successful transaction), so the caller retries
 *      at the next safe point with the SAME adapter.
 *   out->committed is 1 only when the loan descriptor or the RAM tuple actually
 *   changed. B1C_NONE is handled (return 1) but is never committed.
 *
 * Invariant: phase == B1C_IDLE implies !binding_valid. binding_valid while HELD,
 * RETIRING or ORPHANED means the borrowed tuple may still be installed.
 *
 * ENTER publishes the ten slot bytes before adopting the transition and is
 * requested at most once per hit: binding_valid refuses a second publication and
 * b1cb_publish refuses a slot that no longer holds the original empty tuple.
 * YIELD adopts RETIRING without touching RAM or the incoming request. RESTORE
 * requires a held binding, a paused and quiescent VM and the tuple still ours;
 * failure keeps RETIRING for a later safe point. RETIRING without a binding has
 * nothing installed and is adopted back to IDLE instead of blocking forever.
 *
 * ABANDON is terminal for the descriptor (no re-ENTER). The adapter frees the
 * slot when it can prove the tuple is still ours and the VM is stopped and
 * quiescent; otherwise it DEFERS, so a transient observation cannot destroy the
 * hit. Only a restore failure inside a stopped, quiescent VM leaves the borrowed
 * tuple installed: that slot stays unavailable and caller teardown is owed
 * (explicitly out of scope).
 *
 * paused/quiescent are caller facts. Controller entry, playback, pause
 * ownership, alias freedom and clip authenticity are NOT proven here.
 */
#ifndef BAG2JP_CAUGHT_ADAPTER_H
#define BAG2JP_CAUGHT_ADAPTER_H
#include <stddef.h>
#include <stdint.h>
#include "bag2jp_caught_binding.h"
#include "bag2jp_caught_loan.h"

typedef struct {
    B1CaughtLoan loan;
    B1CaughtBinding binding;
    int binding_valid;
} B1CaughtAdapter;

/* Caller-proven VM facts. They are inputs, not proof produced here. */
typedef struct {
    int paused;    /* an exclusively stopped VM owns the RAM buffer */
    int quiescent; /* decoder/pose/controller idle for the borrowed clip */
} B1CaughtVmFacts;

typedef struct {
    B1CaughtDecision decision;
    int committed;     /* the loan advanced or the RAM tuple changed */
    int request_entry; /* caller must deliver mode=1/slot1 before this tick */
} B1CaughtAdapterResult;

/* A candidate may only publish the tables the observation actually names. The
 * policy already pins the owner, so generation/epoch/tag/version cannot drift
 * into a new ENTER; these seven fields are the ones a binding can carry. */
static int b1ca_matches_identity(const B1CaughtBinding *candidate,
                                const B1CaughtIdentity *id) {
    return candidate->actor == id->actor && candidate->raw_table == id->raw_table &&
        candidate->length_table == id->length_table &&
        candidate->metadata_table == id->metadata_table &&
        candidate->count == id->count && candidate->character == id->character &&
        candidate->side == id->side;
}

/* 1 = slot1 still holds exactly the tuple this binding wrote, 0 = it does not,
 * -1 = the tables/clip cannot be resolved. Deliberately independent of
 * current/previous: a playing CAUGHT clip legitimately makes slot1 current. */
static int b1ca_owns_tuple(const uint8_t *ram, size_t bytes,
                            const B1CaughtBinding *b) {
    B1CaughtWritePlan plan;
    B1CaughtSpan actor, tables[3];
    if (!b1cb_span(bytes, b->clip, b->clip_bytes, 4, &plan.clip) ||
        !b1cb_clip_info(ram, b, &plan) ||
        !b1cb_span(bytes, b->actor, B1CB_ACTOR_BYTES, 4, &actor) ||
        !b1cb_tables(ram, bytes, actor, tables)) return -1;
    return b1cb_read(ram, tables[0].offset + 4u*B1CB_SLOT, 4) == b->clip &&
        b1cb_read(ram, tables[1].offset + 2u*B1CB_SLOT, 2) == B1CB_FRAMES &&
        b1cb_read(ram, tables[2].offset + 4u*B1CB_SLOT, 4) == plan.info;
}

/* Apply the decided action to RAM before adopting the new loan state. A rejected
 * publication, retirement or abandon leaves the previous state and every RAM
 * byte unchanged so the caller can retry at the next safe point.
 */
static int b1ca_apply(B1CaughtAdapter *adapter, const B1CaughtObservation *view,
                      const B1CaughtBinding *candidate, uint8_t *ram, size_t bytes,
                      const B1CaughtVmFacts *vm, B1CaughtAdapterResult *out) {
    B1CaughtAdapterResult result = {0};
    int ok = 1;
    if (out) *out = result;
    if (!adapter || !view || !vm || !ram) return 0;
    B1CaughtDecision decision = b1c_decide(&adapter->loan, view);
    result.decision = decision;
    switch (decision.action) {
    case B1C_ENTER:
        if (adapter->binding_valid || !candidate ||
            !b1ca_matches_identity(candidate, &view->identity)) { ok = 0; break; }
        if (!b1cb_publish(ram, bytes, candidate, vm->paused)) { ok = 0; break; }
        adapter->binding = *candidate;
        adapter->binding_valid = 1;
        adapter->loan = decision.next;
        result.committed = 1;
        result.request_entry = 1;
        break;
    case B1C_YIELD:
        /* The incoming legitimate request is left exactly as delivered. */
        adapter->loan = decision.next;
        result.committed = 1;
        break;
    case B1C_RESTORE:
        if (!adapter->binding_valid) {
            /* Nothing is installed, so there is nothing to retire. */
            adapter->loan = decision.next;
            result.committed = 1;
            break;
        }
        if (!b1cb_restore(ram, bytes, &adapter->binding, vm->paused, vm->quiescent)) {
            ok = 0;
            break;
        }
        adapter->binding_valid = 0;
        adapter->loan = decision.next;
        result.committed = 1;
        break;
    case B1C_ABANDON: {
        if (!adapter->binding_valid) {
            adapter->loan = decision.next;
            result.committed = 1;
            break;
        }
        const int borrowed = b1ca_owns_tuple(ram, bytes, &adapter->binding);
        if (borrowed == 0) {
            /* The slot is no longer ours: nothing can or should be freed. */
            adapter->binding_valid = 0;
            adapter->loan = decision.next;
            result.committed = 1;
            break;
        }
        if (borrowed < 0) { ok = 0; break; }  /* unresolved tables: retry later */
        if (b1c_same_owner(&adapter->loan.owner, &view->identity) &&
            !view->binding_intact) {
            /* RAM still holds the exact tuple, so one observation flag cannot
             * destroy the hit. The next observation decides with fresh facts. */
            ok = 0;
            break;
        }
        if (!vm->paused || !vm->quiescent) { ok = 0; break; }  /* defer, no orphan */
        if (b1cb_restore(ram, bytes, &adapter->binding, vm->paused, vm->quiescent))
            adapter->binding_valid = 0;
        /* ORPHANED is terminal for this descriptor; the tuple may remain
         * installed when retire is refused inside a stopped guest (see header). */
        adapter->loan = decision.next;
        result.committed = 1;
        break;
    }
    case B1C_NONE:
    default:
        adapter->loan = decision.next;
        break;
    }
    if (!ok) result.committed = 0;
    if (out) *out = result;
    return ok;
}

#endif
