/* Entry transaction tests: real production headers, synthetic clips/VM facts.
 * No controller execution, authentic assets, live pause or lifecycle proof.
 */
#undef NDEBUG
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include "bag2jp_caught_entry.h"

enum { RAM_BYTES = 0x800000, LOW_ACTOR = 0x80090000u, HIGH_ACTOR = 0x80410000u,
       ATTACKER = 0x800a0000u, RAW = 0x800b0000u, LENGTH = 0x800b0200u,
       META = 0x800b0300u, EMPTY = 0x800c0000u, OTHER_RAW = 0x800e0000u,
       OTHER_LENGTH = 0x800e0200u, OTHER_META = 0x800e0300u,
       LIST = 0x8005f808u, COUNT = 101, CLIP = 0x9f001000u, CLIP_BYTES = 64,
       SLOT_CURRENT = 0x154c, SLOT_PREVIOUS = 0x1550, FRAME = 0x1554,
       PENDING = 0x18 };
static uint8_t ram[RAM_BYTES], before[RAM_BYTES], clip[CLIP_BYTES], clip_before[CLIP_BYTES];
static B1CaughtClipRegion region = {clip, CLIP, CLIP_BYTES};
static B1CaughtAdapter adapter;
static B1CaughtObservation view;
static B1CaughtBinding binding;
static B1CaughtControllerEntry entry;
static B1CaughtAttackFacts attack;
static B1CaughtVmFacts vm;

static void put(uint32_t address, uint32_t value, unsigned width) {
    for (unsigned i = 0; i < width; ++i)
        ram[address - 0x80000000u + i] = (uint8_t)(value >> (8*i));
}
static uint32_t get(uint32_t address, unsigned width) {
    uint32_t value = 0;
    for (unsigned i = 0; i < width; ++i)
        value |= (uint32_t)ram[address - 0x80000000u + i] << (8*i);
    return value;
}
static void actor_tables(uint32_t actor, uint32_t raw, uint32_t length, uint32_t meta) {
    put(actor + 0x820, COUNT, 4); put(actor + 0x824, raw, 4);
    put(actor + 0x828, length, 4); put(actor + 0x82c, meta, 4);
    put(actor + SLOT_CURRENT, 73, 4); put(actor + SLOT_PREVIOUS, 73, 4);
}
static void observe(void) {
    memcpy(before, ram, sizeof ram);
    memcpy(clip_before, clip, sizeof clip);
}
static void fixture(int high, unsigned side, unsigned character) {
    uint32_t actor = high ? HIGH_ACTOR : LOW_ACTOR;
    memset(ram, 0, sizeof ram); memset(clip, 0, sizeof clip);
    memset(&adapter, 0, sizeof adapter); memset(&view, 0, sizeof view);
    actor_tables(actor, RAW, LENGTH, META);
    actor_tables(ATTACKER, OTHER_RAW, OTHER_LENGTH, OTHER_META);
    put(actor + 4, character, 1); put(actor + 5, side, 1);
    put(ATTACKER + 4, 9, 1); put(ATTACKER + 5, side ^ 1u, 1);
    put(LIST + 8*side, actor, 4); put(LIST + 8*(side ^ 1u), ATTACKER, 4);
    put(RAW + 4, EMPTY, 4);
    put(actor + PENDING, 202, 2); put(actor + FRAME, 37, 4);
    /* Structurally valid two-frame clip; NOT authentic CAUGHT bytes. */
    clip[0] = 32; clip[4] = 2; clip[32] = 16; clip[50] = 4;
    view.identity = (B1CaughtIdentity){11, 22, actor, RAW, LENGTH, META, COUNT,
                                     33, character, side, 1};
    view.attack_id = 7001; view.module = 5;
    view.safe_point = view.exclusive_tables = view.empty_slot = view.verified_clip = 1;
    view.hit_active = view.binding_intact = 1;
    binding = (B1CaughtBinding){actor, RAW, LENGTH, META, COUNT, character, side,
                                EMPTY, CLIP, CLIP_BYTES};
    adapter.region = &region;
    entry = (B1CaughtControllerEntry){actor, 1, 89};
    attack = (B1CaughtAttackFacts){202, 1}; vm = (B1CaughtVmFacts){1, 1};
    observe();
}
static int redirect(void) {
    return b1ce_redirect(&adapter, &view, &binding, ram, sizeof ram, &vm, &attack, &entry);
}
static void only_slot_bytes(void) {
    memcpy(before + RAW - 0x80000000u + 4, ram + RAW - 0x80000000u + 4, 4);
    memcpy(before + LENGTH - 0x80000000u + 2, ram + LENGTH - 0x80000000u + 2, 2);
    memcpy(before + META - 0x80000000u + 4, ram + META - 0x80000000u + 4, 4);
    assert(memcmp(before, ram, sizeof ram) == 0);
    assert(memcmp(clip_before, clip, sizeof clip) == 0);
}
static void refused(void) {
    B1CaughtAdapter saved = adapter;
    B1CaughtControllerEntry saved_entry = entry;
    observe();
    assert(!redirect());
    assert(memcmp(&saved, &adapter, sizeof saved) == 0);
    assert(memcmp(&saved_entry, &entry, sizeof saved_entry) == 0);
    assert(memcmp(before, ram, sizeof ram) == 0);
    assert(memcmp(clip_before, clip, sizeof clip) == 0);
}
static void success(int high, unsigned side, unsigned character) {
    fixture(high, side, character);
    assert(redirect());
    assert(entry.actor == binding.actor && entry.mode == 1 && entry.slot == 1);
    assert(adapter.loan.phase == B1C_HELD && adapter.binding_valid);
    assert(adapter.loan.attack_id == 7001 && adapter.binding.clip == CLIP);
    assert(get(RAW + 4, 4) == CLIP && get(LENGTH + 2, 2) == 2);
    assert(get(META + 4, 4) == CLIP + 48);
    assert(get(binding.actor + PENDING, 2) == 202 && get(binding.actor + FRAME, 4) == 37);
    only_slot_bytes();
    /* Repeated controller delivery must not reset the clip or re-publish. */
    entry.slot = 89; refused();
}
static void invalid_request(int kind) {
    switch (kind) {
    case 0: entry.mode = 0; break;
    case 1: entry.slot = 202; break;
    case 2: entry.slot = 78; break;
    case 3: entry.actor = ATTACKER; break;
    case 4: attack.source_request = 123; break;
    case 5: attack.attacker_version = 2; break;
    case 6: put(ATTACKER + 4, 1, 1); break;
    case 7: put(ATTACKER + 5, 0, 1); break;
    case 8: put(LIST, 0, 4); put(LIST + 4, binding.actor, 4); break;
    case 9: put(LIST + 8, 0, 4); break;
    case 10: put(LIST + 8, 0x807ffffcu, 4); break;
    case 11: put(LIST + 8, binding.actor, 4); break;
    case 12: view.identity.version = 2; break;
    case 13: view.identity.side = 2; break;
    case 14: view.hit_active = 0; break;
    case 15: view.incoming_reaction = 1; break;
    case 22: entry.mode = 2; break;
    case 23: entry.slot = 1; break;
    case 24: entry.slot = 0xffffffffu; break;
    default: assert(0);
    }
}
static void invalid_memory_or_facts(int kind) {
    switch (kind) {
    case 16: view.verified_clip = 0; break;
    case 17: vm.paused = 0; break;
    case 18: put(ATTACKER + 0x824, RAW, 4); break;
    case 19: binding.clip = 0x80400000u; break;
    case 20: binding.actor = ATTACKER; break;
    case 21: view.references = B1C_REF_DECODER; break;
    case 25:
        entry.actor = binding.actor = view.identity.actor = 0x807ff000u;
        put(LIST, entry.actor, 4); break;
    case 26:
        binding.count = view.identity.count = 0xffffffffu;
        put(binding.actor + 0x820, binding.count, 4); break;
    case 27: view.module = 7; break;
    case 28: view.exclusive_tables = 0; break;
    case 29: view.safe_point = 0; break;
    case 30: put(LENGTH + 2, 7, 2); break;
    case 31: put(EMPTY, 7, 4); break;
    default: assert(0);
    }
}
static void negative(int kind) {
    fixture(0, 0, 0);
    if (kind < 16 || (kind >= 22 && kind < 25)) invalid_request(kind);
    else invalid_memory_or_facts(kind);
    refused();
}
static void retry_and_retire(void) {
    B1CaughtAdapterResult result;
    fixture(1, 1, 1);
    vm.paused = 0; refused(); vm.paused = 1;
    assert(redirect());
    view.hit_active = 0; view.references = B1C_REF_CURRENT;
    put(binding.actor + SLOT_CURRENT, 1, 4); observe();
    assert(b1ca_apply(&adapter, &view, &binding, ram, sizeof ram, &vm, &result));
    assert(adapter.loan.phase == B1C_RETIRING && !result.request_entry);
    assert(memcmp(before, ram, sizeof ram) == 0);
    /* A legitimate request is never redirected during retirement. */
    entry.slot = 90; refused();
    view.references = 0;
    put(binding.actor + SLOT_CURRENT, 90, 4); put(binding.actor + SLOT_PREVIOUS, 90, 4);
    vm.quiescent = 0; observe();
    assert(!b1ca_apply(&adapter, &view, &binding, ram, sizeof ram, &vm, &result));
    assert(adapter.loan.phase == B1C_RETIRING && adapter.binding_valid);
    assert(memcmp(before, ram, sizeof ram) == 0);
    vm.quiescent = 1;
    assert(b1ca_apply(&adapter, &view, &binding, ram, sizeof ram, &vm, &result));
    assert(adapter.loan.phase == B1C_IDLE && !adapter.binding_valid);
    assert(get(RAW + 4, 4) == EMPTY && !get(LENGTH + 2, 2) && !get(META + 4, 4));
    only_slot_bytes();
    view.hit_active = 1; entry.slot = 89; refused(); /* same hit cannot replay */
    ++view.attack_id;
    assert(redirect());
}
static void nulls_and_bounds(int kind) {
    fixture(0, 0, 9); observe();
    B1CaughtAdapter saved = adapter;
    B1CaughtControllerEntry saved_entry = entry;
    assert(!b1ce_redirect(kind == 0 ? NULL : &adapter, kind == 1 ? NULL : &view,
        kind == 2 ? NULL : &binding, kind == 3 ? NULL : ram,
        kind == 8 ? 16 : (kind == 9 ? (size_t)RAM_BYTES + 1 : sizeof ram),
        kind == 4 ? NULL : &vm, kind == 5 ? NULL : &attack,
        kind == 6 ? NULL : &entry));
    assert(memcmp(&saved, &adapter, sizeof saved) == 0);
    assert(memcmp(&saved_entry, &entry, sizeof saved_entry) == 0);
    assert(memcmp(before, ram, sizeof ram) == 0);
}
static void retirement_refused(void) {
    B1CaughtAdapter saved = adapter;
    B1CaughtControllerEntry saved_entry = entry;
    B1CaughtAdapterResult result;
    observe();
    assert(!b1ca_apply(&adapter, &view, &binding, ram, sizeof ram, &vm, &result));
    assert(!result.committed && !result.request_entry);
    assert(memcmp(&saved, &adapter, sizeof saved) == 0);
    assert(memcmp(&saved_entry, &entry, sizeof saved_entry) == 0);
    assert(memcmp(before, ram, sizeof ram) == 0);
    assert(memcmp(clip_before, clip, sizeof clip) == 0);
}
static void real_retirement_references(int kind) {
    const unsigned offsets[] = {0, SLOT_CURRENT, SLOT_PREVIOUS, 0x830, 0x1494, 0x1498};
    B1CaughtAdapterResult result;
    fixture(1, 1, 9);
    assert(redirect());
    view.hit_active = 0; view.references = 0;
    assert(b1ca_apply(&adapter, &view, &binding, ram, sizeof ram, &vm, &result));
    assert(adapter.loan.phase == B1C_RETIRING);
    if (!kind) vm.paused = 0;
    else put(binding.actor + offsets[kind], kind < 3 ? 1 : CLIP + 8, 4);
    retirement_refused();
    /* Same descriptor retries only after the actual residual reference clears. */
    vm.paused = 1;
    if (kind) put(binding.actor + offsets[kind], kind < 3 ? 90 : 0, 4);
    observe();
    assert(b1ca_apply(&adapter, &view, &binding, ram, sizeof ram, &vm, &result));
    assert(adapter.loan.phase == B1C_IDLE && !adapter.binding_valid);
    assert(get(RAW + 4, 4) == EMPTY && !get(LENGTH + 2, 2) && !get(META + 4, 4));
    only_slot_bytes();
}
int main(int argc, char **argv) {
    assert(argc == 3);
    int scenario = atoi(argv[1]), kind = atoi(argv[2]);
    switch (scenario) {
    case 0: success(kind / 6, (unsigned)(kind / 3) % 2, (unsigned[]){0, 1, 9}[kind % 3]); break;
    case 1: negative(kind); break;
    case 2: retry_and_retire(); break;
    case 3: nulls_and_bounds(kind); break;
    case 4: real_retirement_references(kind); break;
    default: assert(0);
    }
    return 0;
}
