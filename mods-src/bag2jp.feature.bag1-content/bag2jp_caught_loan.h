/* Experimental decision seam only: no RAM access and not wired to the runtime.
 * A future controller adapter must apply an action atomically before adopting
 * next. Keeping the old state on publication failure permits a safe retry.
 */
#ifndef BAG2JP_CAUGHT_LOAN_H
#define BAG2JP_CAUGHT_LOAN_H

#include <stdint.h>

enum { B1C_COMBAT_MODULE = 5, B1C_SLOT = 1 };
enum { B1C_REF_CURRENT = 1, B1C_REF_PREVIOUS = 2,
       B1C_REF_DECODER = 4, B1C_REF_POSE = 8 };
typedef enum { B1C_IDLE, B1C_HELD, B1C_RETIRING, B1C_ORPHANED } B1CaughtPhase;
typedef enum { B1C_NONE, B1C_ENTER, B1C_YIELD, B1C_RESTORE, B1C_ABANDON } B1CaughtAction;

/* Generation must change even when an allocation reuses the same actor address.
 * Scene epoch and content tag identify a load, not just a scene number/region.
 */
typedef struct {
    uint64_t generation, scene_epoch;
    uint32_t actor, raw_table, length_table, metadata_table, count, content_tag;
    uint32_t character, side, version;
} B1CaughtIdentity;

typedef struct {
    B1CaughtIdentity identity;
    uint64_t attack_id;
    uint32_t module, references;
    int safe_point, exclusive_tables, empty_slot, verified_clip;
    int hit_active, incoming_reaction, binding_intact;
} B1CaughtObservation;

typedef struct {
    /* One descriptor belongs to one identity after first entry, even in IDLE.
     * Do not reset/retarget it to clear replay history. A future adapter owes
     * quiescent teardown before disposing of a descriptor for an unloaded actor.
     */
    B1CaughtIdentity owner;
    uint64_t attack_id;
    B1CaughtPhase phase;
} B1CaughtLoan;

typedef struct {
    B1CaughtLoan next;
    B1CaughtAction action;
} B1CaughtDecision;

static int b1c_same_owner(const B1CaughtIdentity *a, const B1CaughtIdentity *b) {
    return a->generation == b->generation && a->scene_epoch == b->scene_epoch &&
        a->actor == b->actor && a->raw_table == b->raw_table &&
        a->length_table == b->length_table && a->metadata_table == b->metadata_table &&
        a->count == b->count && a->content_tag == b->content_tag &&
        a->character == b->character && a->side == b->side && a->version == b->version;
}

static int b1c_eligible(const B1CaughtObservation *view) {
    const B1CaughtIdentity *id = &view->identity;
    return view->module == B1C_COMBAT_MODULE && view->exclusive_tables &&
        view->verified_clip && id->version == 1 && id->side < 2 &&
        (id->character == 0 || id->character == 1 || id->character == 9) &&
        id->generation && id->scene_epoch && id->content_tag && id->actor &&
        id->raw_table && id->length_table && id->metadata_table && id->count > B1C_SLOT;
}

static void b1c_offer_entry(B1CaughtDecision *result, const B1CaughtObservation *view) {
    if (!b1c_eligible(view) || !view->safe_point || !view->hit_active ||
        view->incoming_reaction || !view->empty_slot || view->references || !view->attack_id)
        return;
    if (result->next.owner.actor &&
        (!b1c_same_owner(&result->next.owner, &view->identity) ||
         view->attack_id <= result->next.attack_id)) return;
    result->next.owner = view->identity;
    result->next.attack_id = view->attack_id;
    result->next.phase = B1C_HELD;
    result->action = B1C_ENTER;
}

/* ENTER grants a single controller entry, never a per-frame slot/frame write.
 * YIELD leaves an incoming legitimate request untouched; it is not a request to
 * restore the pre-hit animation. RESTORE is slot-content retirement only.
 * ABANDON pins the reservation: no restore/free/reuse, even if identity returns.
 * The adapter still owes RAM bounds, actual alias checks and an authentic clip;
 * these observation facts are not verified by this pure policy.
 */
static B1CaughtDecision b1c_decide(const B1CaughtLoan *loan,
                                  const B1CaughtObservation *view) {
    B1CaughtDecision result = {0};
    if (loan) result.next = *loan;
    if (!loan || !view || loan->phase == B1C_ORPHANED) return result;
    if (loan->phase == B1C_IDLE) {
        b1c_offer_entry(&result, view);
        return result;
    }
    if (!b1c_same_owner(&loan->owner, &view->identity) ||
        !b1c_eligible(view) || !view->binding_intact) {
        result.next.phase = B1C_ORPHANED;
        result.action = B1C_ABANDON;
    } else if (view->safe_point && loan->phase == B1C_HELD &&
               (!view->hit_active || view->incoming_reaction ||
                view->attack_id != loan->attack_id)) {
        result.next.phase = B1C_RETIRING;
        result.action = B1C_YIELD;
    } else if (view->safe_point && loan->phase == B1C_RETIRING && !view->references) {
        result.next.phase = B1C_IDLE;
        result.action = B1C_RESTORE;
    }
    return result;
}

#endif
