/* Exercise the actual reducer. No RAM/controller/animation behavior is mocked. */
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include "bag2jp_caught_loan.h"

static B1CaughtObservation seed(void) {
    return (B1CaughtObservation){
        .identity = {.generation = 1, .scene_epoch = 4, .actor = 0x80200000u,
            .raw_table = 0x80300000u, .length_table = 0x80301000u,
            .metadata_table = 0x80302000u, .count = 101, .content_tag = 123,
            .character = 9, .side = 0, .version = 1},
        .attack_id = 10, .module = 5, .safe_point = 1, .exclusive_tables = 1,
        .empty_slot = 1, .verified_clip = 1, .hit_active = 1, .binding_intact = 1
    };
}

static B1CaughtAction apply(B1CaughtLoan *loan, B1CaughtObservation *view) {
    B1CaughtDecision decision = b1c_decide(loan, view);
    *loan = decision.next;
    return decision.action;
}

static void enter(B1CaughtLoan *loan, B1CaughtObservation *view) {
    assert(apply(loan, view) == B1C_ENTER);
}

static void lifecycle(void) {
    B1CaughtLoan loan = {0};
    B1CaughtObservation view = seed();
    enter(&loan, &view);
    view.empty_slot = 0; /* The published slot is not empty while lent. */
    view.references = B1C_REF_CURRENT;
    for (unsigned tick = 0; tick < 12; ++tick)
        assert(apply(&loan, &view) == B1C_NONE);
    view.hit_active = 0;
    assert(apply(&loan, &view) == B1C_YIELD);
    assert(apply(&loan, &view) == B1C_NONE);
    view.references = 0;
    assert(apply(&loan, &view) == B1C_RESTORE);
    view.empty_slot = 1;
    view.hit_active = 1;
    assert(apply(&loan, &view) == B1C_NONE); /* Same hit must not retrigger. */
    ++view.attack_id;
    enter(&loan, &view);
}

static void gate(unsigned gate) {
    B1CaughtLoan loan = {0};
    B1CaughtObservation view = seed();
    switch (gate) {
        case 0: view.module = 4; break;
        case 1: view.identity.character = 6; break;
        case 2: view.identity.version = 0; break;
        case 3: view.exclusive_tables = 0; break;
        case 4: view.empty_slot = 0; break;
        case 5: view.verified_clip = 0; break;
        case 6: view.safe_point = 0; break;
        case 7: view.hit_active = 0; break;
        case 8: view.incoming_reaction = 1; break;
        case 9: view.references = B1C_REF_PREVIOUS; break;
        case 10: view.identity.count = 1; break;
        case 11: view.identity.side = 2; break;
        case 12: view.attack_id = 0; break;
        case 13: view.identity.actor = 0; break;
        case 14: view.identity.generation = 0; break;
        case 15: view.identity.scene_epoch = 0; break;
        case 16: view.identity.raw_table = 0; break;
        case 17: view.identity.length_table = 0; break;
        case 18: view.identity.metadata_table = 0; break;
        case 19: view.identity.content_tag = 0; break;
        case 20: view.identity.version = 2; break;
        case 21: view.identity.character = 18; break;
        default: abort();
    }
    assert(apply(&loan, &view) == B1C_NONE);
    assert(loan.phase == B1C_IDLE && loan.attack_id == 0);
}

static void yield_to_request(void) {
    B1CaughtLoan loan = {0};
    B1CaughtObservation view = seed();
    enter(&loan, &view);
    view.incoming_reaction = 1;
    view.references = B1C_REF_CURRENT;
    assert(apply(&loan, &view) == B1C_YIELD);
    view.incoming_reaction = 0;
    view.references = 0;
    assert(apply(&loan, &view) == B1C_RESTORE);
    assert(apply(&loan, &view) == B1C_NONE);
}

static void retain(unsigned reference) {
    B1CaughtLoan loan = {0};
    B1CaughtObservation view = seed();
    enter(&loan, &view);
    view.hit_active = 0;
    assert(apply(&loan, &view) == B1C_YIELD);
    view.references = reference;
    assert(apply(&loan, &view) == B1C_NONE);
    view.references = 0;
    assert(apply(&loan, &view) == B1C_RESTORE);
}

static void invalidate(unsigned field) {
    B1CaughtLoan loan = {0};
    B1CaughtObservation view = seed();
    enter(&loan, &view);
    if (field >= 20) {
        field -= 20;
        view.hit_active = 0;
        assert(apply(&loan, &view) == B1C_YIELD);
    }
    switch (field) {
        case 0: ++view.identity.actor; break;
        case 1: ++view.identity.generation; break;
        case 2: ++view.identity.scene_epoch; break;
        case 3: ++view.identity.raw_table; break;
        case 4: ++view.identity.length_table; break;
        case 5: ++view.identity.metadata_table; break;
        case 6: ++view.identity.count; break;
        case 7: ++view.identity.content_tag; break;
        case 8: view.identity.character = 1; break;
        case 9: ++view.identity.side; break;
        case 10: view.identity.version = 0; break;
        case 11: view.exclusive_tables = 0; break;
        case 12: view.module = 4; break;
        case 13: view.binding_intact = 0; break;
        default: abort();
    }
    assert(apply(&loan, &view) == B1C_ABANDON);
    assert(loan.phase == B1C_ORPHANED);
    /* Orphaning cannot restore into a new owner, re-enter, or release storage. */
    view = seed();
    ++view.attack_id;
    for (unsigned tick = 0; tick < 3; ++tick)
        assert(apply(&loan, &view) == B1C_NONE);
}

static void deferred_commit(void) {
    B1CaughtLoan loan = {0};
    B1CaughtObservation view = seed();
    B1CaughtDecision proposal = b1c_decide(&loan, &view);
    assert(proposal.action == B1C_ENTER);
    assert(loan.phase == B1C_IDLE); /* Failed publication must not consume entry. */
    enter(&loan, &view);
}

static void unsafe_exit(void) {
    B1CaughtLoan loan = {0};
    B1CaughtObservation view = seed();
    enter(&loan, &view);
    view.safe_point = 0;
    view.hit_active = 0;
    assert(apply(&loan, &view) == B1C_NONE);
    view.safe_point = 1;
    assert(apply(&loan, &view) == B1C_YIELD);
    view.safe_point = 0;
    assert(apply(&loan, &view) == B1C_NONE);
    view.safe_point = 1;
    assert(apply(&loan, &view) == B1C_RESTORE);
}

static void all_imports(void) {
    const unsigned characters[] = {0, 1, 9};
    for (unsigned c = 0; c < 3; ++c) for (unsigned side = 0; side < 2; ++side) {
        B1CaughtLoan loan = {0};
        B1CaughtObservation view = seed();
        view.identity.character = characters[c];
        view.identity.side = side;
        enter(&loan, &view);
    }
}

static void entry_reference(unsigned reference) {
    B1CaughtLoan loan = {0};
    B1CaughtObservation view = seed();
    view.references = reference;
    assert(apply(&loan, &view) == B1C_NONE);
    assert(loan.phase == B1C_IDLE && loan.attack_id == 0);
}

static void identity_replay(void) {
    B1CaughtLoan loan = {0};
    B1CaughtObservation view = seed();
    enter(&loan, &view);
    view.hit_active = 0;
    assert(apply(&loan, &view) == B1C_YIELD);
    assert(apply(&loan, &view) == B1C_RESTORE);
    view.hit_active = 1;
    ++view.identity.actor; /* Do not retarget an idle descriptor to B. */
    ++view.attack_id; /* Even a newer B hit must not erase A's history. */
    assert(apply(&loan, &view) == B1C_NONE);
    --view.identity.actor;
    --view.attack_id;
    assert(apply(&loan, &view) == B1C_NONE); /* A10 is still consumed. */
    --view.attack_id;
    assert(apply(&loan, &view) == B1C_NONE); /* A9 cannot replay either. */
    view.attack_id += 2;
    enter(&loan, &view); /* A11 remains legitimate. */
}

static void new_attack(void) {
    B1CaughtLoan loan = {0};
    B1CaughtObservation view = seed();
    enter(&loan, &view);
    ++view.attack_id;
    assert(apply(&loan, &view) == B1C_YIELD);
    assert(apply(&loan, &view) == B1C_RESTORE);
    enter(&loan, &view);
}

static void immutable_proposal(unsigned transition) {
    B1CaughtLoan loan = {0};
    B1CaughtObservation view = seed();
    if (transition) enter(&loan, &view);
    if (transition == 1 || transition == 2) view.hit_active = 0;
    if (transition == 2) assert(apply(&loan, &view) == B1C_YIELD);
    if (transition == 3) ++view.identity.generation;
    unsigned char loan_bytes[sizeof loan], view_bytes[sizeof view];
    memcpy(loan_bytes, &loan, sizeof loan);
    memcpy(view_bytes, &view, sizeof view);
    B1CaughtDecision first = b1c_decide(&loan, &view);
    B1CaughtDecision second = b1c_decide(&loan, &view);
    const B1CaughtAction expected[] = {B1C_ENTER, B1C_YIELD, B1C_RESTORE, B1C_ABANDON};
    assert(first.action == expected[transition] && second.action == first.action);
    assert(first.next.phase == second.next.phase);
    assert(first.next.attack_id == second.next.attack_id);
    assert(first.next.owner.actor == second.next.owner.actor);
    assert(memcmp(loan_bytes, &loan, sizeof loan) == 0);
    assert(memcmp(view_bytes, &view, sizeof view) == 0);
}

int main(int argc, char **argv) {
    assert(argc >= 2);
    unsigned scenario = (unsigned)atoi(argv[1]);
    unsigned value = argc > 2 ? (unsigned)atoi(argv[2]) : 0;
    switch (scenario) {
        case 0: lifecycle(); break;
        case 1: gate(value); break;
        case 2: yield_to_request(); break;
        case 3: retain(value); break;
        case 4: invalidate(value); break;
        case 5: deferred_commit(); break;
        case 6: unsafe_exit(); break;
        case 7: all_imports(); break;
        case 8: entry_reference(value); break;
        case 9: identity_replay(); break;
        case 10: new_attack(); break;
        case 11: immutable_proposal(value); break;
        default: abort();
    }
    return 0;
}
