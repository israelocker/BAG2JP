/* Composition tests: policy state may only advance after the RAM step succeeds.
 * Scenarios are numbered because five methods are not enough to pin every guard;
 * see the per-scenario comments for the regression each one owns.
 */
#undef NDEBUG /* never let a release build turn this file into a green no-op */
#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "bag2jp_caught_adapter.h"

enum { RAM_BYTES = 0x200000, ACTOR = 0x80090000u, RAW = 0x800b0000u,
       LENGTH = 0x800b0200u, META = 0x800b0300u, EMPTY = 0x800c0000u,
       CLIP = 0x800d0000u, CLIP_BYTES = 64, INFO = CLIP + 48, COUNT = 101,
       MODULE = 5, VERSION = 1 };
static uint8_t ram[RAM_BYTES], before[RAM_BYTES];

static void put32(uint32_t a, uint32_t v) {
    for (unsigned i = 0; i < 4; ++i) ram[a - 0x80000000u + i] = (uint8_t)(v >> (8*i));
}
static void put16(uint32_t a, uint16_t v) {
    ram[a - 0x80000000u] = (uint8_t)v;
    ram[a - 0x80000000u + 1] = (uint8_t)(v >> 8);
}
static uint32_t get32(uint32_t a) {
    uint32_t v = 0;
    for (unsigned i = 0; i < 4; ++i) v |= (uint32_t)ram[a - 0x80000000u + i] << (8*i);
    return v;
}
static B1CaughtBinding candidate_value(void) {
    B1CaughtBinding b = {ACTOR, RAW, LENGTH, META, COUNT, 9, 0, EMPTY, CLIP, CLIP_BYTES};
    return b;
}
static B1CaughtObservation observation(void) {
    B1CaughtObservation v = {0};
    v.identity.generation = 11;
    v.identity.scene_epoch = 22;
    v.identity.actor = ACTOR;
    v.identity.raw_table = RAW;
    v.identity.length_table = LENGTH;
    v.identity.metadata_table = META;
    v.identity.count = COUNT;
    v.identity.content_tag = 33;
    v.identity.character = 9;
    v.identity.side = 0;
    v.identity.version = VERSION;
    v.attack_id = 7001;
    v.module = MODULE;
    v.exclusive_tables = 1;
    v.empty_slot = 1;
    v.verified_clip = 1;
    v.safe_point = 1;
    v.hit_active = 1;
    v.incoming_reaction = 0;
    v.binding_intact = 1;
    return v;
}
static void fixture(void) {
    memset(ram, 0, sizeof ram);
    put32(0x8005f808u, ACTOR);
    ram[ACTOR - 0x80000000u + 4] = 9;
    put32(ACTOR + 0x820, COUNT); put32(ACTOR + 0x824, RAW);
    put32(ACTOR + 0x828, LENGTH); put32(ACTOR + 0x82c, META);
    put32(EMPTY, 0);
    put32(RAW + 4, EMPTY); /* slot 1 starts as the original empty tuple */
    put32(ACTOR + 0x154c, 73); put32(ACTOR + 0x1550, 73);
    put32(CLIP, 32); put16(CLIP + 4, 2);
    put32(CLIP + 32, 16); put16(INFO + 2, 4);
    ram[INFO - 0x80000000u + 5] = 1; /* runtime hold-last-frame metadata */
    memcpy(before, ram, sizeof ram);
}
static void unchanged(void) { assert(memcmp(ram, before, sizeof ram) == 0); }
static void observe(void) { memcpy(before, ram, sizeof ram); }
/* A publication may move exactly the ten slot bytes and nothing else. */
static void only_entry_changed(void) {
    memcpy(before + RAW - 0x80000000u + 4, ram + RAW - 0x80000000u + 4, 4);
    memcpy(before + LENGTH - 0x80000000u + 2, ram + LENGTH - 0x80000000u + 2, 2);
    memcpy(before + META - 0x80000000u + 4, ram + META - 0x80000000u + 4, 4);
    unchanged();
}
static void invariant(const B1CaughtAdapter *a) {
    assert(a->loan.phase != B1C_IDLE || !a->binding_valid);
}
static B1CaughtVmFacts vm_value(int paused, int quiescent) {
    B1CaughtVmFacts facts = {paused, quiescent};
    return facts;
}
/* Enter once, leaving the adapter HELD and slot1 published. */
static void enter(B1CaughtAdapter *adapter) {
    B1CaughtObservation v = observation();
    B1CaughtBinding b = candidate_value();
    B1CaughtVmFacts ok = vm_value(1, 1);
    B1CaughtAdapterResult r;
    assert(b1ca_apply(adapter, &v, &b, ram, sizeof ram, &ok, &r));
    assert(r.decision.action == B1C_ENTER && r.request_entry);
    invariant(adapter);
}
/* Inline VM facts cannot be addressed, so retries build a real object. */
static int apply_vm(B1CaughtAdapter *adapter, const B1CaughtObservation *v,
                    const B1CaughtBinding *b, int paused, int quiescent,
                    B1CaughtAdapterResult *r) {
    B1CaughtVmFacts facts = vm_value(paused, quiescent);
    return b1ca_apply(adapter, v, b, ram, sizeof ram, &facts, r);
}

/* 0: ENTER publishes before adopting, then YIELD and RESTORE follow in order. */
static void lifecycle(void) {
    fixture();
    B1CaughtAdapter adapter = {0};
    B1CaughtObservation v = observation();
    B1CaughtBinding b = candidate_value();
    B1CaughtVmFacts vm = vm_value(1, 1);
    B1CaughtAdapterResult r;
    observe();
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(r.committed && r.request_entry && r.decision.action == B1C_ENTER);
    assert(adapter.loan.phase == B1C_HELD && adapter.binding_valid);
    assert(get32(RAW + 4) == CLIP && get32(META + 4) == INFO);
    assert(ram[LENGTH - 0x80000000u + 2] == 2);
    only_entry_changed();
    invariant(&adapter);
    /* Same hit again: handled but nothing happens and nothing is requested. */
    observe();
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(r.decision.action == B1C_NONE && !r.request_entry && !r.committed);
    unchanged();
    /* A legitimate reaction yields without touching RAM or the request. */
    v.hit_active = 0;
    observe();
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(r.decision.action == B1C_YIELD && r.committed);
    assert(adapter.loan.phase == B1C_RETIRING);
    unchanged();
    invariant(&adapter);
    /* Retirement empties slot1 and returns to IDLE. */
    v.references = 0;
    put32(ACTOR + 0x154c, 89); put32(ACTOR + 0x1550, 89);
    observe();
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(r.decision.action == B1C_RESTORE && r.committed);
    assert(adapter.loan.phase == B1C_IDLE);
    /* Retiring restores the original empty tuple (EMPTY,0,0), not zeroes. */
    assert(!adapter.binding_valid && get32(RAW + 4) == EMPTY && !get32(META + 4));
    assert(ram[LENGTH - 0x80000000u + 2] == 0);
    only_entry_changed(); /* Retirement writes the same ten slot bytes back. */
    invariant(&adapter);
    /* A later hit may borrow again; the retired tuple left nothing behind. */
    v.hit_active = 1;
    v.attack_id = 7002;
    observe();
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(r.decision.action == B1C_ENTER && r.request_entry);
    only_entry_changed();
}

/* 1: a failed publication must not advance the loan, request entry or RAM, and
 * the SAME adapter must still be able to enter once the defect is fixed. */
static void publish_failure(int kind) {
    fixture();
    B1CaughtAdapter adapter = {0};
    B1CaughtObservation v = observation();
    B1CaughtBinding b = candidate_value();
    B1CaughtBinding zero = {0};
    B1CaughtVmFacts vm = vm_value(1, 1);
    B1CaughtAdapterResult r;
    const B1CaughtBinding *offered = &b;
    switch (kind) {
    case 0: put32(EMPTY, 1); break;                 /* slot is not empty */
    case 1: b.character = 0; break;                 /* not the observed tables */
    case 2: vm = vm_value(0, 1); break;             /* VM not stopped */
    case 3: put32(ACTOR + 0x154c, 1); break;        /* slot1 is current */
    case 4: put16(INFO + 2, 5); break;              /* not a 2-frame CAUGHT */
    case 5: offered = NULL; break;                  /* no candidate offered */
    case 6: put32(RAW + 4, CLIP + 4); break;        /* slot1 holds another clip */
    default: assert(0);
    }
    observe();
    assert(!b1ca_apply(&adapter, &v, offered, ram, sizeof ram, &vm, &r));
    assert(!r.committed && !r.request_entry && !adapter.binding_valid);
    assert(adapter.loan.phase == B1C_IDLE && adapter.loan.owner.actor == 0);
    assert(memcmp(&adapter.binding, &zero, sizeof zero) == 0);
    unchanged();
    /* Undo the single defect and retry on the same adapter. */
    put32(EMPTY, 0);
    put32(ACTOR + 0x154c, 73);
    put16(INFO + 2, 4);
    put32(RAW + 4, EMPTY);
    b = candidate_value(); /* also undo the candidate mutation, not just RAM */
    observe();
    assert(apply_vm(&adapter, &v, &b, 1, 1, &r));
    assert(r.decision.action == B1C_ENTER && r.request_entry);
    only_entry_changed();
}

/* 2: retirement requires ownership plus real quiescence; failure keeps RETIRING
 * with the binding intact, and the SAME adapter retires after the fix. */
static void retire_failure(int kind) {
    fixture();
    B1CaughtAdapter adapter = {0};
    B1CaughtObservation v = observation();
    B1CaughtBinding b = candidate_value();
    B1CaughtVmFacts vm = vm_value(1, 1);
    B1CaughtAdapterResult r;
    enter(&adapter);
    v.hit_active = 0;
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(adapter.loan.phase == B1C_RETIRING);
    put32(ACTOR + 0x154c, 89); put32(ACTOR + 0x1550, 89);
    switch (kind) {
    case 0: vm = vm_value(1, 0); break;      /* not quiescent */
    case 1: vm = vm_value(0, 1); break;      /* not stopped */
    case 2: put32(ACTOR + 0x154c, 1); break; /* slot1 still current */
    case 3: put32(ACTOR + 0x1550, 1); break; /* slot1 still previous */
    case 4: put32(RAW + 4, CLIP + 4); break; /* borrowed tuple replaced */
    case 5: put32(ACTOR + 0x830, CLIP + 8); break; /* decoder inside clip */
    case 6: put32(ACTOR + 0x1494, CLIP + 8); break; /* pose A inside clip */
    case 7: put32(ACTOR + 0x1498, CLIP + 8); break; /* pose B inside clip */
    default: assert(0);
    }
    observe();
    assert(!b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(!r.committed && adapter.loan.phase == B1C_RETIRING && adapter.binding_valid);
    unchanged();
    /* Undo the single defect and retry on the SAME adapter. */
    put32(ACTOR + 0x154c, 89); put32(ACTOR + 0x1550, 89);
    put32(ACTOR + 0x830, 0); put32(ACTOR + 0x1494, 0); put32(ACTOR + 0x1498, 0);
    put32(RAW + 4, CLIP);
    observe();
    assert(apply_vm(&adapter, &v, &b, 1, 1, &r));
    assert(r.decision.action == B1C_RESTORE && adapter.loan.phase == B1C_IDLE);
    assert(!adapter.binding_valid);
    only_entry_changed();
    invariant(&adapter);
}

/* 3: ABANDON is terminal, but it must not leak slot1: while the VM cannot be
 * retired the adapter defers, and a stopped+quiescent VM frees the tuple. */
static void abandon(int kind) {
    fixture();
    B1CaughtAdapter adapter = {0};
    B1CaughtObservation v = observation();
    B1CaughtBinding b = candidate_value();
    B1CaughtVmFacts vm = vm_value(1, 1);
    B1CaughtAdapterResult r;
    enter(&adapter);
    v.identity.actor = ACTOR + 0x2000; /* different owner: cannot be retargeted */
    if (kind == 0) {
        observe();
        assert(!apply_vm(&adapter, &v, &b, 1, 0, &r));
        assert(r.decision.action == B1C_ABANDON && !r.committed);
        assert(adapter.loan.phase == B1C_HELD && adapter.binding_valid);
        unchanged();
        invariant(&adapter);
    }
    observe();
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(r.decision.action == B1C_ABANDON && r.committed);
    assert(adapter.loan.phase == B1C_ORPHANED);
    assert(!adapter.binding_valid && get32(RAW + 4) == EMPTY && !get32(META + 4));
    assert(ram[LENGTH - 0x80000000u + 2] == 0);
    only_entry_changed();
    invariant(&adapter);
    /* Terminal: the original identity and a new hit cannot re-enter. */
    v.identity.actor = ACTOR;
    v.attack_id = 7002;
    observe();
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(r.decision.action == B1C_NONE && !r.committed);
    unchanged();
}

/* 4: losing the adapter state must not publish the borrowed slot twice. */
static void restart_cannot_publish(void) {
    fixture();
    B1CaughtAdapter first = {0};
    B1CaughtAdapter restarted = {0};
    B1CaughtObservation v = observation();
    B1CaughtBinding b = candidate_value();
    B1CaughtVmFacts vm = vm_value(1, 1);
    B1CaughtAdapterResult r;
    enter(&first);
    observe();
    assert(!b1ca_apply(&restarted, &v, &b, ram, sizeof ram, &vm, &r));
    assert(r.decision.action == B1C_ENTER && !r.committed && !r.request_entry);
    assert(!restarted.binding_valid && restarted.loan.phase == B1C_IDLE);
    unchanged();
}

/* 5: a candidate may only publish the tables the observation names. Each case
 * leaves RAM publishable, so only the identity matcher can refuse it. */
static void identity_case(int kind) {
    fixture();
    B1CaughtAdapter adapter = {0};
    B1CaughtObservation v = observation();
    B1CaughtBinding b = candidate_value();
    B1CaughtVmFacts vm = vm_value(1, 1);
    B1CaughtAdapterResult r;
    switch (kind) {
    case 0: ram[ACTOR - 0x80000000u + 5] = 1; b.side = 1; break;
    case 1: put32(RAW + 0x1000 + 4, EMPTY); put32(ACTOR + 0x824, RAW + 0x1000);
        b.raw_table = RAW + 0x1000; break;
    case 2: put16(LENGTH + 0x1000 + 2, 0); put32(ACTOR + 0x828, LENGTH + 0x1000);
        b.length_table = LENGTH + 0x1000; break;
    case 3: put32(META + 0x1000 + 4, EMPTY); put32(ACTOR + 0x82c, META + 0x1000);
        b.metadata_table = META + 0x1000; break;
    case 4: put32(ACTOR + 0x820, COUNT + 1); b.count = COUNT + 1; break;
    case 5: ram[ACTOR - 0x80000000u + 4] = 1; b.character = 1; break;
    default: assert(0);
    }
    observe();
    assert(!b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(!r.committed && !r.request_entry && !adapter.binding_valid);
    assert(adapter.loan.phase == B1C_IDLE);
    unchanged();
}

/* 6: every legitimate incoming reaction yields without rewriting it. */
static void yield_trigger(int kind) {
    fixture();
    B1CaughtAdapter adapter = {0};
    B1CaughtObservation v = observation();
    B1CaughtBinding b = candidate_value();
    B1CaughtVmFacts vm = vm_value(1, 1);
    B1CaughtAdapterResult r;
    enter(&adapter);
    if (kind == 0) v.hit_active = 0;
    else if (kind == 1) v.incoming_reaction = 1;
    else v.attack_id = 7002;
    observe();
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(r.decision.action == B1C_YIELD && r.committed);
    assert(adapter.loan.phase == B1C_RETIRING && adapter.binding_valid);
    unchanged(); /* the request is neither rewritten nor applied by us */
    invariant(&adapter);
}

/* 7: a refused retirement keeps the borrow intact, byte for byte. */
static void binding_integrity(void) {
    fixture();
    B1CaughtAdapter adapter = {0};
    B1CaughtObservation v = observation();
    B1CaughtBinding b = candidate_value();
    B1CaughtVmFacts vm = vm_value(1, 1);
    B1CaughtAdapterResult r;
    B1CaughtBinding saved;
    enter(&adapter);
    saved = adapter.binding;
    v.hit_active = 0;
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    put32(ACTOR + 0x154c, 89); put32(ACTOR + 0x1550, 89);
    observe();
    assert(!apply_vm(&adapter, &v, &b, 1, 0, &r));
    assert(!r.committed && adapter.binding_valid);
    assert(memcmp(&saved, &adapter.binding, sizeof saved) == 0);
    unchanged();
}

/* 8: a live reference forbids retirement until it clears. */
static void references_block_restore(void) {
    fixture();
    B1CaughtAdapter adapter = {0};
    B1CaughtObservation v = observation();
    B1CaughtBinding b = candidate_value();
    B1CaughtVmFacts vm = vm_value(1, 1);
    B1CaughtAdapterResult r;
    enter(&adapter);
    v.hit_active = 0;
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    v.references = 1;
    observe();
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(r.decision.action == B1C_NONE && !r.committed);
    assert(adapter.loan.phase == B1C_RETIRING && adapter.binding_valid);
    unchanged();
    v.references = 0;
    observe();
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(r.decision.action == B1C_RESTORE);
    only_entry_changed();
}

/* 9: another loaded actor sharing the borrowed tables forbids publication,
 * while a disjoint companion must not. */
static void exclusive_tables(int kind) {
    fixture();
    B1CaughtAdapter adapter = {0};
    B1CaughtObservation v = observation();
    B1CaughtBinding b = candidate_value();
    B1CaughtVmFacts vm = vm_value(1, 1);
    B1CaughtAdapterResult r;
    const uint32_t actor2 = ACTOR + 0x4000u;
    put32(0x8005f80cu, actor2);
    ram[actor2 - 0x80000000u + 4] = 9;
    put32(actor2 + 0x154c, 73); put32(actor2 + 0x1550, 73);
    if (kind == 0) { /* same tables as the owner: not exclusive */
        put32(actor2 + 0x820, COUNT); put32(actor2 + 0x824, RAW);
        put32(actor2 + 0x828, LENGTH); put32(actor2 + 0x82c, META);
        observe();
        assert(!b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
        assert(!r.committed && !r.request_entry && !adapter.binding_valid);
        assert(adapter.loan.phase == B1C_IDLE);
        unchanged();
        return;
    }
    /* Companion with its own empty tables: the borrow stays legal. Tables are
     * spaced 0x1000 apart so they cannot overlap the owner's 0x194-byte ones. */
    put32(actor2 + 0x820, COUNT); put32(actor2 + 0x824, RAW + 0x1000);
    put32(actor2 + 0x828, LENGTH + 0x1000); put32(actor2 + 0x82c, META + 0x1000);
    put32(RAW + 0x1000 + 4, EMPTY);
    observe();
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(r.decision.action == B1C_ENTER && r.request_entry);
    only_entry_changed();
}

/* 10: a retired descriptor may not replay the same attack id. */
static void replay_guard(void) {
    fixture();
    B1CaughtAdapter adapter = {0};
    B1CaughtObservation v = observation();
    B1CaughtBinding b = candidate_value();
    B1CaughtVmFacts vm = vm_value(1, 1);
    B1CaughtAdapterResult r;
    enter(&adapter);
    v.hit_active = 0;
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    put32(ACTOR + 0x154c, 89); put32(ACTOR + 0x1550, 89);
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(adapter.loan.phase == B1C_IDLE);
    v.hit_active = 1;
    v.attack_id = 7001; /* same hit as the retired one */
    observe();
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(r.decision.action == B1C_NONE && !r.request_entry && !r.committed);
    unchanged();
    v.attack_id = 7002; /* a new hit may borrow again */
    observe();
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(r.decision.action == B1C_ENTER && r.request_entry);
    only_entry_changed();
}

/* 11: one stale observation flag cannot destroy a loan whose RAM is intact. */
static void transient_binding_flag(void) {
    fixture();
    B1CaughtAdapter adapter = {0};
    B1CaughtObservation v = observation();
    B1CaughtBinding b = candidate_value();
    B1CaughtVmFacts vm = vm_value(1, 1);
    B1CaughtAdapterResult r;
    enter(&adapter);
    v.binding_intact = 0;
    observe();
    assert(!b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(r.decision.action == B1C_ABANDON && !r.committed);
    assert(adapter.loan.phase == B1C_HELD && adapter.binding_valid);
    unchanged();
    invariant(&adapter);
    v.binding_intact = 1;
    observe();
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(r.decision.action == B1C_NONE && !r.committed);
    unchanged();
}

/* 12: every entry precondition must keep the descriptor idle and RAM untouched. */
static void offer_gate(int kind) {
    fixture();
    B1CaughtAdapter adapter = {0};
    B1CaughtObservation v = observation();
    B1CaughtBinding b = candidate_value();
    B1CaughtVmFacts vm = vm_value(1, 1);
    B1CaughtAdapterResult r;
    switch (kind) {
    case 0: v.empty_slot = 0; break;
    case 1: v.safe_point = 0; break;
    case 2: v.module = 4; break;
    case 3: v.references = 1; break;
    case 4: v.attack_id = 0; break;
    case 5: v.hit_active = 0; break;
    case 6: v.incoming_reaction = 1; break;
    case 7: v.identity.version = 2; break;
    case 8: v.identity.character = 3; break;
    case 9: v.identity.side = 2; break;
    case 10: v.identity.count = 1; break;
    default: assert(0);
    }
    observe();
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(r.decision.action == B1C_NONE && !r.committed && !r.request_entry);
    assert(adapter.loan.phase == B1C_IDLE && !adapter.binding_valid);
    unchanged();
    invariant(&adapter);
}

/* 13: un clip owned (Expansion1) respalda binding.clip; publicar y restaurar
 * tocan solo los diez bytes de ranura de RAM principal y nunca el área. */
static void owned_region_lifecycle(void) {
    enum { REGION_BASE = 0x9f001000u, REGION_BYTES = 256, CLIP_OFF = 32 };
    static uint8_t region[REGION_BYTES], region_before[REGION_BYTES];
    fixture();
    memset(region, 0xa5, sizeof region);
    memcpy(region + CLIP_OFF, ram + CLIP - 0x80000000u, CLIP_BYTES);
    memcpy(region_before, region, sizeof region);
    /* El binding apunta al área; las tablas siguen en RAM principal. */
    B1CaughtBinding b = candidate_value();
    b.clip = REGION_BASE + CLIP_OFF;
    const B1CaughtClipRegion region_obj = {region, REGION_BASE, sizeof region};
    B1CaughtAdapter adapter = {0};
    adapter.region = &region_obj;
    B1CaughtObservation v = observation();
    B1CaughtVmFacts vm = vm_value(1, 1);
    B1CaughtAdapterResult r;
    observe();
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(r.decision.action == B1C_ENTER && r.request_entry && r.committed);
    assert(adapter.binding_valid && adapter.loan.phase == B1C_HELD);
    /* Solo los diez bytes de ranura cambian en RAM principal, apuntando al área. */
    assert(get32(RAW + 4) == REGION_BASE + CLIP_OFF);
    assert(get32(META + 4) == REGION_BASE + CLIP_OFF + (INFO - CLIP));
    assert(ram[LENGTH - 0x80000000u + 2] == 2);
    only_entry_changed();
    /* El área nunca se modifica por la transacción de bytes. */
    assert(memcmp(region, region_before, sizeof region) == 0);
    /* Jubilación: primero se cede para entrar en RETIRING, luego se restaura. */
    v.hit_active = 0;
    observe();
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(r.decision.action == B1C_YIELD && r.committed);
    assert(adapter.loan.phase == B1C_RETIRING && adapter.binding_valid);
    v.references = 0;
    put32(ACTOR + 0x154c, 89); put32(ACTOR + 0x1550, 89);
    observe();
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(r.decision.action == B1C_RESTORE && r.committed);
    assert(adapter.loan.phase == B1C_IDLE && !adapter.binding_valid);
    assert(get32(RAW + 4) == EMPTY && !get32(META + 4));
    assert(ram[LENGTH - 0x80000000u + 2] == 0);
    only_entry_changed();
    assert(memcmp(region, region_before, sizeof region) == 0);
    invariant(&adapter);
}

/* 15: retire_failure_owned — retirement with an owned region requires paused
 * and quiescent VM plus slot1 neither current nor previous. Each defect keeps
 * the borrow intact and RAM unchanged; fixing it lets the same adapter retire. */
static void retire_failure_owned(int kind) {
    enum { REGION_BASE = 0x9f001000u, REGION_BYTES = 256, CLIP_OFF = 32 };
    static uint8_t region[REGION_BYTES], region_before[REGION_BYTES];
    fixture();
    memset(region, 0xa5, sizeof region);
    memcpy(region + CLIP_OFF, ram + CLIP - 0x80000000u, CLIP_BYTES);
    memcpy(region_before, region, sizeof region);
    /* Binding apunta al área owned; enter() no sirve porque reusa candidate_value()
     * con clip en main-RAM. Se construye la entrada a mano igual que scenario 13. */
    B1CaughtBinding b = candidate_value();
    b.clip = REGION_BASE + CLIP_OFF;
    const B1CaughtClipRegion region_obj = {region, REGION_BASE, sizeof region};
    B1CaughtAdapter adapter = {0};
    adapter.region = &region_obj;
    B1CaughtObservation v = observation();
    B1CaughtVmFacts vm = vm_value(1, 1);
    B1CaughtAdapterResult r;
    observe();
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(r.decision.action == B1C_ENTER && r.request_entry && r.committed);
    assert(adapter.binding_valid && adapter.loan.phase == B1C_HELD);
    only_entry_changed();
    assert(memcmp(region, region_before, sizeof region) == 0);
    /* Ceder para entrar en RETIRING. */
    v.hit_active = 0;
    observe();
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(r.decision.action == B1C_YIELD && r.committed);
    assert(adapter.loan.phase == B1C_RETIRING && adapter.binding_valid);
    put32(ACTOR + 0x154c, 89); put32(ACTOR + 0x1550, 89);
    switch (kind) {
    case 0: vm = vm_value(1, 0); break;      /* not quiescent */
    case 1: vm = vm_value(0, 1); break;      /* not stopped */
    case 2: put32(ACTOR + 0x154c, 1); break; /* slot1 still current */
    case 3: put32(ACTOR + 0x1550, 1); break; /* slot1 still previous */
    default: assert(0);
    }
    observe();
    assert(!b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(!r.committed && adapter.loan.phase == B1C_RETIRING && adapter.binding_valid);
    unchanged(); assert(memcmp(region, region_before, sizeof region) == 0);
    /* Deshacer el defecto y reintentar con el mismo adapter. */
    put32(ACTOR + 0x154c, 89); put32(ACTOR + 0x1550, 89);
    observe();
    assert(apply_vm(&adapter, &v, &b, 1, 1, &r));
    assert(r.decision.action == B1C_RESTORE && r.committed);
    assert(adapter.loan.phase == B1C_IDLE && !adapter.binding_valid);
    assert(get32(RAW + 4) == EMPTY && !get32(META + 4));
    assert(ram[LENGTH - 0x80000000u + 2] == 0);
    only_entry_changed();
    assert(memcmp(region, region_before, sizeof region) == 0);
    invariant(&adapter);
}

static void retire_owned_region_defect(int kind) {
    /* Same setup as scenario 15, but a defect intrinsic to the owned region
     * makes RESTORE fail while the VM stays paused and quiescent. */
    enum { REGION_BASE = 0x9f001000u, REGION_BYTES = 256, CLIP_OFF = 32 };
    static uint8_t region[REGION_BYTES], region_before[REGION_BYTES];
    fixture();
    memset(region, 0xa5, sizeof region);
    memcpy(region + CLIP_OFF, ram + CLIP - 0x80000000u, CLIP_BYTES);
    memcpy(region_before, region, sizeof region);
    B1CaughtBinding b = candidate_value();
    b.clip = REGION_BASE + CLIP_OFF;
    const B1CaughtClipRegion region_obj = {region, REGION_BASE, sizeof region};
    B1CaughtAdapter adapter = {0};
    adapter.region = &region_obj;
    B1CaughtObservation v = observation();
    B1CaughtVmFacts vm = vm_value(1, 1);
    B1CaughtAdapterResult r;
    observe();
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(r.decision.action == B1C_ENTER && r.request_entry && r.committed);
    assert(adapter.binding_valid && adapter.loan.phase == B1C_HELD);
    only_entry_changed();
    assert(memcmp(region, region_before, sizeof region) == 0);
    v.hit_active = 0;
    observe();
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(r.decision.action == B1C_YIELD && r.committed);
    assert(adapter.loan.phase == B1C_RETIRING && adapter.binding_valid);
    switch (kind) {
    case 4: { B1CaughtClipRegion region_mut = region_obj;
              region_mut.guest_base = 0x9f002000u;
              adapter.region = &region_mut; break; } /* region identity changed */
    case 5: { const B1CaughtClipRegion null_region = {NULL, REGION_BASE, sizeof region};
              adapter.region = &null_region; break; }   /* region data NULL */
    case 6: put32(ACTOR + 0x824, 0x9f100000u); break;  /* actor tables out of range */
    case 7: adapter.binding.clip = REGION_BASE - 4u; break;   /* installed clip below base */
    case 8: adapter.binding.clip_bytes = (uint32_t)(REGION_BYTES - CLIP_OFF + 1); break; /* installed clip overflows */
    default: assert(0);
    }
    observe();
    assert(!b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(!r.committed && adapter.loan.phase == B1C_RETIRING && adapter.binding_valid);
    unchanged(); assert(memcmp(region, region_before, sizeof region) == 0);
    /* Undo the defect and retry on the same adapter. */
    put32(ACTOR + 0x154c, 89); put32(ACTOR + 0x1550, 89);
    put32(ACTOR + 0x824, RAW);                          /* undo actor tables defect */
    adapter.binding.clip = REGION_BASE + CLIP_OFF;     /* undo installed clip */
    adapter.binding.clip_bytes = CLIP_BYTES;
    const B1CaughtClipRegion region_obj2 = {region, REGION_BASE, sizeof region};
    adapter.region = &region_obj2;
    observe();
    assert(apply_vm(&adapter, &v, &b, 1, 1, &r));
    assert(r.decision.action == B1C_RESTORE && r.committed);
    assert(adapter.loan.phase == B1C_IDLE && !adapter.binding_valid);
    assert(get32(RAW + 4) == EMPTY && !get32(META + 4));
    assert(ram[LENGTH - 0x80000000u + 2] == 0);
    only_entry_changed();
    assert(memcmp(region, region_before, sizeof region) == 0);
    invariant(&adapter);
}

/* 16: partner_exclusion_owned — a companion whose tables alias the owned
 * region cannot be mistaken for the owner: identity mismatch blocks ENTER. */
static void partner_exclusion_owned(int kind) {
    enum { REGION_BASE = 0x9f001000u, REGION_BYTES = 256, CLIP_OFF = 32 };
    static uint8_t region[REGION_BYTES], region_before[REGION_BYTES];
    fixture();
    memset(region, 0xa5, sizeof region);
    memcpy(region + CLIP_OFF, ram + CLIP - 0x80000000u, CLIP_BYTES);
    memcpy(region_before, region, sizeof region);
    B1CaughtBinding b = candidate_value();
    b.clip = REGION_BASE + CLIP_OFF;
    const B1CaughtClipRegion region_obj = {region, REGION_BASE, sizeof region};
    B1CaughtAdapter adapter = {0};
    adapter.region = &region_obj;
    B1CaughtObservation v = observation();
    B1CaughtVmFacts vm = vm_value(1, 1);
    B1CaughtAdapterResult r;
    const uint32_t actor2 = ACTOR + 0x4000u;
    put32(0x8005f80cu, actor2);
    ram[actor2 - 0x80000000u + 4] = 9;
    put32(actor2 + 0x154c, 73); put32(actor2 + 0x1550, 73);
    if (kind == 0) { /* companion tables alias the owned region: not exclusive */
        put32(actor2 + 0x820, COUNT); put32(actor2 + 0x824, REGION_BASE + CLIP_OFF);
        put32(actor2 + 0x828, REGION_BASE + CLIP_OFF + 48);
        put32(actor2 + 0x82c, REGION_BASE + CLIP_OFF + 96);
        observe();
        assert(!b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
        assert(!r.committed && !r.request_entry && !adapter.binding_valid);
        assert(adapter.loan.phase == B1C_IDLE);
        unchanged(); assert(memcmp(region, region_before, sizeof region) == 0);
        return;
    }
    if (kind == 1) { /* companion with disjoint own tables: borrow stays legal. */
        put32(actor2 + 0x820, COUNT); put32(actor2 + 0x824, RAW + 0x1000);
        put32(actor2 + 0x828, LENGTH + 0x1000); put32(actor2 + 0x82c, META + 0x1000);
        put32(RAW + 0x1000 + 4, EMPTY);
        observe();
        assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
        assert(r.decision.action == B1C_ENTER && r.request_entry);
        only_entry_changed();
        assert(memcmp(region, region_before, sizeof region) == 0);
        invariant(&adapter);
        return;
    }
    if (kind == 2) { /* companion with disjoint tables; owner can still borrow */
        put32(actor2 + 0x820, COUNT); put32(actor2 + 0x824, RAW + 0x1000);
        put32(actor2 + 0x828, LENGTH + 0x1000); put32(actor2 + 0x82c, META + 0x1000);
        put32(RAW + 0x1000 + 4, EMPTY);
        observe();
        assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
        assert(r.decision.action == B1C_ENTER && r.request_entry && r.committed);
        assert(adapter.binding_valid && adapter.loan.phase == B1C_HELD);
        v.hit_active = 0;
        observe();
        assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
        assert(r.decision.action == B1C_YIELD && r.committed);
        assert(adapter.loan.phase == B1C_RETIRING);
        put32(ACTOR + 0x154c, 89); put32(ACTOR + 0x1550, 89);
        observe();
        assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
        assert(r.decision.action == B1C_RESTORE && r.committed);
        assert(adapter.loan.phase == B1C_IDLE && !adapter.binding_valid);
        assert(get32(RAW + 4) == EMPTY && !get32(META + 4));
        assert(ram[LENGTH - 0x80000000u + 2] == 0);
        only_entry_changed();
        invariant(&adapter);
        return;
    }
    if (kind == 3) { /* after full retire, same owner may borrow again with new hit */
        put32(actor2 + 0x820, COUNT); put32(actor2 + 0x824, RAW + 0x1000);
        put32(actor2 + 0x828, LENGTH + 0x1000); put32(actor2 + 0x82c, META + 0x1000);
        put32(RAW + 0x1000 + 4, EMPTY);
        /* First borrow + retire. */
        observe();
        assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
        assert(r.decision.action == B1C_ENTER && r.committed);
        v.hit_active = 0;
        observe();
        assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
        assert(r.decision.action == B1C_YIELD && r.committed);
        put32(ACTOR + 0x154c, 89); put32(ACTOR + 0x1550, 89);
        observe();
        assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
        assert(r.decision.action == B1C_RESTORE && r.committed);
        assert(adapter.loan.phase == B1C_IDLE && !adapter.binding_valid);
        /* New hit with new attack_id: re-borrow on the same adapter. */
        v.hit_active = 1;
        v.attack_id = 7002;
        observe();
        assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
        assert(r.decision.action == B1C_ENTER && r.request_entry && r.committed);
        assert(adapter.binding_valid && adapter.loan.phase == B1C_HELD);
        only_entry_changed();
        invariant(&adapter);
        return;
    }
    assert(0);
}

/* 14: owned-region negatives — publish with region, then refuse restore when
 * quiescent=false, when the region identity changed, or when tables alias the
 * region. RAM must stay byte-for-byte unchanged on every refusal. */
static void owned_region_negatives(int kind) {
    enum { REGION_BASE = 0x9f001000u, REGION_BYTES = 256, CLIP_OFF = 32 };
    static uint8_t region[REGION_BYTES], region_before[REGION_BYTES];
    fixture();
    memset(region, 0xa5, sizeof region);
    memcpy(region + CLIP_OFF, ram + CLIP - 0x80000000u, CLIP_BYTES);
    memcpy(region_before, region, sizeof region);
    B1CaughtBinding b = candidate_value();
    b.clip = REGION_BASE + CLIP_OFF;
    const B1CaughtClipRegion region_obj = {region, REGION_BASE, sizeof region};
    B1CaughtAdapter adapter = {0};
    adapter.region = &region_obj;
    B1CaughtObservation v = observation();
    B1CaughtVmFacts vm = vm_value(1, 1);
    B1CaughtAdapterResult r;
    observe();
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(r.decision.action == B1C_ENTER && r.request_entry && r.committed);
    assert(adapter.binding_valid && adapter.loan.phase == B1C_HELD);
    only_entry_changed();
    assert(memcmp(region, region_before, sizeof region) == 0);

    /* Yield to enter RETIRING; only then does restore consult quiescence. */
    v.hit_active = 0;
    observe();
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(r.decision.action == B1C_YIELD && r.committed);
    assert(adapter.loan.phase == B1C_RETIRING && adapter.binding_valid);
    v.references = 0;
    put32(ACTOR + 0x154c, 89); put32(ACTOR + 0x1550, 89);

    switch (kind) {
    case 0: /* restore with quiescent=false must refuse, binding intact */
        observe();
        assert(!b1ca_apply(&adapter, &v, &b, ram, sizeof ram,
                           &(B1CaughtVmFacts){1, 0}, &r));
        assert(!r.committed && adapter.binding_valid && adapter.loan.phase == B1C_RETIRING);
        unchanged(); assert(memcmp(region, region_before, sizeof region) == 0);
        break;
    case 1: /* restore with a different region identity must refuse */
        observe();
        {
            uint8_t other_region[REGION_BYTES];
            memcpy(other_region, region, sizeof region);
            const B1CaughtClipRegion other = {other_region, REGION_BASE + 16, REGION_BYTES - 16};
            B1CaughtAdapter alt = adapter;
            alt.region = &other;
            assert(!b1ca_apply(&alt, &v, &b, ram, sizeof ram, &vm, &r));
            assert(!r.committed && adapter.binding_valid && adapter.loan.phase == B1C_RETIRING);
        }
        unchanged(); assert(memcmp(region, region_before, sizeof region) == 0);
        break;
    case 2: /* restore OK with the same region after YIELD + correct VM facts */
        observe();
        assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
        assert(r.decision.action == B1C_RESTORE && r.committed);
        assert(adapter.loan.phase == B1C_IDLE && !adapter.binding_valid);
        assert(get32(RAW + 4) == EMPTY && !get32(META + 4));
        assert(ram[LENGTH - 0x80000000u + 2] == 0);
        only_entry_changed();
        assert(memcmp(region, region_before, sizeof region) == 0);
        break;
    default: assert(0);
    }
}

/* 18: reset on IDLE with no binding succeeds and clears everything.
 * Full flow: ENTER -> YIELD (hit no longer active) -> RESTORE (no references)
 * leaves IDLE with no binding and RAM restored to fixture state. */
static void reset_idle_ok(void) {
    fixture();
    B1CaughtAdapter adapter = {0};
    B1CaughtObservation v = observation();
    B1CaughtBinding b = candidate_value();
    B1CaughtVmFacts vm = vm_value(1, 1);
    B1CaughtAdapterResult r;
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(r.decision.action == B1C_ENTER);
    assert(adapter.binding_valid && adapter.loan.phase == B1C_HELD);
    /* YIELD: the hit is no longer active */
    v.hit_active = 0;
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(r.decision.action == B1C_YIELD);
    assert(adapter.loan.phase == B1C_RETIRING);
    /* RESTORE: no remaining references retires the slot */
    v.references = 0;
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(r.decision.action == B1C_RESTORE);
    assert(adapter.loan.phase == B1C_IDLE && !adapter.binding_valid);
    /* Now reset on IDLE without binding succeeds and clears everything. */
    assert(b1ca_reset(&adapter));
    assert(adapter.loan.phase == B1C_IDLE && !adapter.binding_valid);
    assert(adapter.binding.actor == 0 && adapter.binding.clip == 0);
    unchanged();
}

/* 19: reset with an installed binding must fail. */
static void reset_with_binding_fails(void) {
    fixture();
    B1CaughtAdapter adapter = {0};
    B1CaughtObservation v = observation();
    B1CaughtBinding b = candidate_value();
    B1CaughtVmFacts vm = vm_value(1, 1);
    B1CaughtAdapterResult r;
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(adapter.binding_valid);
    observe(); /* ENTER changed RAM; unchanged() compares against this state */
    assert(!b1ca_reset(&adapter));
    assert(adapter.binding_valid && adapter.loan.phase == B1C_HELD);
    unchanged();
}

/* 20: save/load roundtrip preserves loan, binding and binding_valid. */
static void save_load_roundtrip(void) {
    fixture();
    B1CaughtAdapter adapter = {0};
    B1CaughtObservation v = observation();
    B1CaughtBinding b = candidate_value();
    B1CaughtVmFacts vm = vm_value(1, 1);
    B1CaughtAdapterResult r;
    assert(b1ca_apply(&adapter, &v, &b, ram, sizeof ram, &vm, &r));
    assert(adapter.binding_valid && adapter.loan.phase == B1C_HELD);
    observe(); /* ENTER changed RAM; unchanged() compares against this state */
    uint8_t state[B1CA_STATE_SIZE];
    memset(state, 0x5a, sizeof state);
    assert(b1ca_state_size() == (int)sizeof state);
    assert(b1ca_save_state(&adapter, state, sizeof state));
    /* A second adapter loads the exact same state. */
    B1CaughtAdapter loaded = {0};
    assert(b1ca_load_state(&loaded, state, sizeof state));
    assert(loaded.loan.owner.generation == adapter.loan.owner.generation);
    assert(loaded.loan.owner.scene_epoch == adapter.loan.owner.scene_epoch);
    assert(loaded.loan.owner.actor == adapter.loan.owner.actor);
    assert(loaded.loan.owner.raw_table == adapter.loan.owner.raw_table);
    assert(loaded.loan.owner.length_table == adapter.loan.owner.length_table);
    assert(loaded.loan.owner.metadata_table == adapter.loan.owner.metadata_table);
    assert(loaded.loan.owner.count == adapter.loan.owner.count);
    assert(loaded.loan.owner.content_tag == adapter.loan.owner.content_tag);
    assert(loaded.loan.owner.character == adapter.loan.owner.character);
    assert(loaded.loan.owner.side == adapter.loan.owner.side);
    assert(loaded.loan.owner.version == adapter.loan.owner.version);
    assert(loaded.loan.attack_id == adapter.loan.attack_id);
    assert(loaded.loan.phase == adapter.loan.phase);
    assert(loaded.binding_valid == adapter.binding_valid);
    assert(loaded.binding.actor == adapter.binding.actor);
    assert(loaded.binding.raw_table == adapter.binding.raw_table);
    assert(loaded.binding.length_table == adapter.binding.length_table);
    assert(loaded.binding.metadata_table == adapter.binding.metadata_table);
    assert(loaded.binding.count == adapter.binding.count);
    assert(loaded.binding.character == adapter.binding.character);
    assert(loaded.binding.side == adapter.binding.side);
    assert(loaded.binding.empty_raw == adapter.binding.empty_raw);
    assert(loaded.binding.clip == adapter.binding.clip);
    assert(loaded.binding.clip_bytes == adapter.binding.clip_bytes);
    unchanged();
}

static void save_fail_closed(void) {
    B1CaughtAdapter adapter = {0};
    uint8_t state[B1CA_STATE_SIZE];
    /* NULL output buffer. */
    assert(!b1ca_save_state(&adapter, NULL, sizeof state));
    /* Too-small output buffers. */
    assert(!b1ca_save_state(&adapter, state, 0));
    assert(!b1ca_save_state(&adapter, state, 1));
    assert(!b1ca_save_state(&adapter, state, B1CA_STATE_SIZE - 1));
    /* Exact size must succeed and leave no dirty output. */
    assert(b1ca_save_state(&adapter, state, sizeof state));
    assert(adapter.binding_valid == 0);
    assert(adapter.loan.phase == B1C_IDLE);
}

static void load_fail_closed(void) {
    B1CaughtAdapter adapter = {0};
    uint8_t state[B1CA_STATE_SIZE];
    /* NULL input buffer. */
    assert(!b1ca_load_state(&adapter, NULL, sizeof state));
    /* Too-small input buffers. */
    assert(!b1ca_load_state(&adapter, state, 0));
    assert(!b1ca_load_state(&adapter, state, 1));
    assert(!b1ca_load_state(&adapter, state, B1CA_STATE_SIZE - 1));
}

static void save_load_region_not_restored(void) {
    B1CaughtAdapter adapter = {0};
    uint8_t state[B1CA_STATE_SIZE];
    B1CaughtAdapter loaded = {0};
    /* Set a region on the source adapter (metadata only, region->data const). */
    static uint8_t region_data[64] = {0};
    adapter.region = &(const B1CaughtClipRegion){region_data, 0x9f001000u, 64};
    assert(b1ca_save_state(&adapter, state, sizeof state));
    /* Load into a fresh adapter without a region: region must stay NULL. */
    loaded.region = NULL;
    assert(b1ca_load_state(&loaded, state, sizeof state));
    assert(loaded.region == NULL);
    assert(loaded.binding_valid == adapter.binding_valid);
    assert(loaded.loan.phase == adapter.loan.phase);
    assert(loaded.loan.owner.generation == adapter.loan.owner.generation);
}

static void save_exact_128_bytes(void) {
    B1CaughtAdapter adapter = {0};
    uint8_t state[B1CA_STATE_SIZE];
    memset(state, 0x5a, sizeof state);
    assert(b1ca_save_state(&adapter, state, sizeof state));
    /* bytes after binding.clip_bytes are padding (region not serialized): all zero.
     * Layout: owner(56) + attack_id(8) + phase(4) + binding_valid(4) + binding(40)
     * + has_region(4) = 116; save_state pads to B1CA_STATE_SIZE(128) with zeros. */
    for (size_t i = B1CA_STATE_SIZE - 16; i < B1CA_STATE_SIZE; ++i)
        assert(state[i] == 0);
    assert(adapter.region == NULL);
}

int main(int argc, char **argv) {
    assert(argc == 3);
    int scenario = atoi(argv[1]), value = atoi(argv[2]);
    switch (scenario) {
    case 0: lifecycle(); break;
    case 1: publish_failure(value); break;
    case 2: retire_failure(value); break;
    case 3: abandon(value); break;
    case 4: restart_cannot_publish(); break;
    case 5: identity_case(value); break;
    case 6: yield_trigger(value); break;
    case 7: binding_integrity(); break;
    case 8: references_block_restore(); break;
    case 9: exclusive_tables(value); break;
    case 10: replay_guard(); break;
    case 11: transient_binding_flag(); break;
    case 12: offer_gate(value); break;
    case 13: owned_region_lifecycle(); break;
    case 14: owned_region_negatives(value); break;
    case 15: retire_failure_owned(value); break;
    case 16: partner_exclusion_owned(value); break;
    case 17: retire_owned_region_defect(value); break;
    case 18: reset_idle_ok(); break;
    case 19: reset_with_binding_fails(); break;
    case 20: save_load_roundtrip(); break;
    case 21: save_fail_closed(); break;
    case 22: load_fail_closed(); break;
    case 23: save_load_region_not_restored(); break;
    case 24: save_exact_128_bytes(); break;
    default: assert(0);
    }
    return 0;
}
