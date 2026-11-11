/* Experimental stopped-RAM entry transaction, NOT included by the runtime.
 * Request provenance, versions, authentic clip residency and VM ownership must
 * be established by the caller. No CPU, decoder or savestate integration here.
 */
#ifndef BAG2JP_CAUGHT_ENTRY_H
#define BAG2JP_CAUGHT_ENTRY_H
#include "bag2jp_caught_adapter.h"

enum { B1CE_MODE_ENTRY = 1, B1CE_GASO_HIT_SLOT = 89, B1CE_GASO_REQUEST = 202,
       B1CE_GASO_CHARACTER = 9, B1CE_BAG1_VERSION = 1,
       B1CE_MAIN_STRIDE = 8, B1CE_CHARACTER = 4, B1CE_SIDE = 5 };
typedef struct {
    uint32_t actor, mode, slot;
} B1CaughtControllerEntry;
typedef struct {
    /* Provenance from the dispatcher and version selection, NOT from a2 or a
     * guessed pending +0x18 value. The transaction cannot establish these facts. */
    uint32_t source_request, attacker_version;
} B1CaughtAttackFacts;

/* The four loaded pointers interleave main/companion for each side. Checking
 * the main pointer rejects a companion even when its tables are independent. */
static int b1ce_main_rivals(const uint8_t *ram, size_t bytes,
                            const B1CaughtIdentity *id) {
    B1CaughtSpan list, attacker;
    if (id->side >= 2 || !b1cb_span(bytes, B1CB_ACTORS,
            B1CB_ACTOR_COUNT * sizeof(uint32_t), 4, &list)) return 0;
    if (b1cb_read(ram, list.offset + B1CE_MAIN_STRIDE * id->side, 4) != id->actor)
        return 0;
    const uint32_t other_side = id->side ^ 1u;
    const uint32_t other = b1cb_read(ram,
        list.offset + B1CE_MAIN_STRIDE * other_side, 4);
    if (other == id->actor || !b1cb_span(bytes, other, B1CB_ACTOR_BYTES, 4, &attacker))
        return 0;
    return ram[attacker.offset + B1CE_CHARACTER] == B1CE_GASO_CHARACTER &&
        ram[attacker.offset + B1CE_SIDE] == other_side;
}

/* Returns 1 only after publication and slot redirection together succeed.
 * Returns 0 without changing entry, adapter or RAM. Buffers must not alias.
 * Keep the same adapter and immutable region alive through safe retirement.
 */
static int b1ce_redirect(B1CaughtAdapter *adapter, const B1CaughtObservation *view,
                         const B1CaughtBinding *candidate, uint8_t *ram, size_t bytes,
                         const B1CaughtVmFacts *vm, const B1CaughtAttackFacts *attack,
                         B1CaughtControllerEntry *entry) {
    if (!adapter || !view || !candidate || !ram || !vm || !attack || !entry ||
        !bytes || bytes > B1CB_MAX_RAM || adapter->loan.phase != B1C_IDLE ||
        adapter->binding_valid || entry->actor != view->identity.actor ||
        entry->mode != B1CE_MODE_ENTRY || entry->slot != B1CE_GASO_HIT_SLOT ||
        attack->source_request != B1CE_GASO_REQUEST ||
        attack->attacker_version != B1CE_BAG1_VERSION ||
        !b1ce_main_rivals(ram, bytes, &view->identity)) return 0;
    B1CaughtAdapterResult result;
    if (!b1ca_apply(adapter, view, candidate, ram, bytes, vm, &result) ||
        !result.request_entry) return 0;
    /* No fallible work after publishing: change only the translated argument,
     * never the actor's current/previous/frame/pending fields. */
    entry->slot = B1C_SLOT;
    return 1;
}
#endif
