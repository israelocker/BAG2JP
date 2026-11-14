/* Byte-addressed PSX RAM tests of the real binding transaction. */
#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "bag2jp_caught_binding.h"

enum { RAM_BYTES = 0x200000, ACTOR = 0x80090000u, OTHER = 0x800a0000u,
       RAW = 0x800b0000u, LENGTH = 0x800b0200u, META = 0x800b0300u,
       EMPTY = 0x800c0000u, CLIP = 0x800d0000u, CLIP_BYTES = 64,
       INFO = CLIP + 48, COUNT = 101 };
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
static B1CaughtBinding setup(void) {
    memset(ram, 0, sizeof ram);
    put32(0x8005f808u, ACTOR);
    ram[ACTOR - 0x80000000u + 4] = 9;
    put32(ACTOR + 0x820, COUNT); put32(ACTOR + 0x824, RAW);
    put32(ACTOR + 0x828, LENGTH); put32(ACTOR + 0x82c, META);
    put32(RAW + 4, EMPTY);
    put32(ACTOR + 0x154c, 73); put32(ACTOR + 0x1550, 73);
    put32(CLIP, 32); put16(CLIP + 4, 2);
    put32(CLIP + 32, 16); put16(INFO + 2, 4);
    ram[INFO - 0x80000000u + 5] = 1; /* runtime hold-last-frame metadata */
    B1CaughtBinding b = {ACTOR, RAW, LENGTH, META, COUNT, 9, 0,
                         EMPTY, CLIP, CLIP_BYTES};
    return b;
}
static void unchanged(void) { assert(memcmp(ram, before, sizeof ram) == 0); }
static void only_entry_changed(const B1CaughtBinding *b) {
    memcpy(before + b->raw_table - 0x80000000u + 4,
           ram + b->raw_table - 0x80000000u + 4, 4);
    memcpy(before + b->length_table - 0x80000000u + 2,
           ram + b->length_table - 0x80000000u + 2, 2);
    memcpy(before + b->metadata_table - 0x80000000u + 4,
           ram + b->metadata_table - 0x80000000u + 4, 4);
    unchanged();
}
static void rejects_publish(B1CaughtBinding b, int paused) {
    memcpy(before, ram, sizeof ram);
    assert(!b1cb_publish(ram, sizeof ram, &b, paused));
    unchanged();
}
static void lifecycle(void) {
    B1CaughtBinding b = setup();
    memcpy(before, ram, sizeof ram);
    assert(b1cb_publish(ram, sizeof ram, &b, 1));
    assert(get32(RAW + 4) == CLIP && get32(META + 4) == INFO);
    assert(ram[LENGTH - 0x80000000u + 2] == 2);
    only_entry_changed(&b);
    rejects_publish(b, 1); /* A second publication is not an entry/reset. */
    put32(ACTOR + 0x154c, 89); put32(ACTOR + 0x1550, 89);
    put32(ACTOR + 0x1554, 17); /* A legitimate reaction survives retirement. */
    memcpy(before, ram, sizeof ram);
    assert(b1cb_restore(ram, sizeof ram, &b, 1, 1));
    assert(get32(RAW + 4) == EMPTY && get32(META + 4) == 0);
    assert(ram[LENGTH - 0x80000000u + 2] == 0);
    only_entry_changed(&b);
    assert(get32(ACTOR + 0x154c) == 89 && get32(ACTOR + 0x1554) == 17);
}
static void invalid_entry(int field) {
    B1CaughtBinding b = setup();
    switch (field) {
    case 0: rejects_publish(b, 0); return;
    case 1: put32(ACTOR + 0x820, COUNT + 1); break;
    case 2: put32(ACTOR + 0x824, RAW + 8); put32(RAW + 12, EMPTY); break;
    case 3: put32(ACTOR + 0x828, LENGTH + 8); break;
    case 4: put32(ACTOR + 0x82c, META + 8); break;
    case 5: ram[ACTOR - 0x80000000u + 4] = 1; break;
    case 6: ram[ACTOR - 0x80000000u + 5] = 1; break;
    case 7: put32(ACTOR + 0x154c, 1); break;
    case 8: put32(ACTOR + 0x1550, 1); break;
    case 9: put16(LENGTH + 2, 1); break;
    case 10: put32(META + 4, INFO); break;
    case 11: put32(EMPTY, 1); break;
    case 12: b.actor = 0xfffffffcu; break;
    case 13: b.count = 0xffffffffu; put32(ACTOR + 0x820, b.count); break;
    case 14: b.clip = 0xfffffffcu; break;
    case 15: b.clip_bytes = 0xffffffffu; break;
    case 16: put32(CLIP, CLIP_BYTES - 1); break;
    case 17: put32(CLIP + 32, 0xfffffffcu); break;
    case 18: put16(CLIP + 4, 0); break;
    case 19: put16(INFO + 2, 5); break;
    case 20: ram[INFO - 0x80000000u + 5] = 0; break; /* looping bank is refused */
    case 21: put16(INFO + 10, 1); break;
    case 22: b.length_table = RAW; put32(ACTOR + 0x828, RAW); break;
    case 23: b.clip = RAW; break;
    case 24: put32(0x8005f808u, OTHER); break;
    default: assert(0);
    }
    rejects_publish(b, 1);
}
static void aliases(int kind) {
    B1CaughtBinding b = setup();
    put32(0x8005f80cu, OTHER);
    put32(OTHER + 0x820, COUNT);
    put32(OTHER + 0x824, 0x800e0000u);
    put32(OTHER + 0x828, 0x800e0200u);
    put32(OTHER + 0x82c, 0x800e0300u);
    const uint32_t destinations[] = {RAW+4, LENGTH+4, META+4};
    if (kind < 9) put32(OTHER + 0x824 + (uint32_t)(kind%3)*4, destinations[kind/3]);
    else if (kind == 9) put32(0x8005f80cu, 0xfffffffcu);
    else put32(0x8005f80cu, ACTOR);
    rejects_publish(b, 1);
}
static void retirement(int field) {
    B1CaughtBinding b = setup();
    assert(b1cb_publish(ram, sizeof ram, &b, 1));
    switch (field) {
    case 0: put32(ACTOR + 0x154c, 1); break;
    case 1: put32(ACTOR + 0x1550, 1); break;
    case 2: put32(ACTOR + 0x830, CLIP); break;
    case 3: put32(ACTOR + 0x1494, CLIP + 8); break;
    case 4: put32(ACTOR + 0x1498, INFO); break;
    case 5: put32(META + 4, INFO + 4); break;
    case 6: put32(ACTOR + 0x824, RAW + 8); break;
    case 7: break; /* caller cannot prove decoder/pose quiescence */
    case 8: break; /* VM not paused */
    case 9: put32(0x8005f80cu, OTHER); put32(OTHER + 0x820, COUNT);
            put32(OTHER + 0x824, RAW);
            put32(OTHER + 0x828, 0x800e0200u);
            put32(OTHER + 0x82c, 0x800e0300u); break;
    case 10: put32(RAW + 4, CLIP + 4); break;
    case 11: put16(LENGTH + 2, 3); break;
    default: assert(0);
    }
    memcpy(before, ram, sizeof ram);
    /* Read-only inspection accepts an active owned tuple, but not changed
     * identity/tables/tuple, shared tables, or a running guest. Publish/restore
     * below must still reject every one of these retirement cases. */
    B1CaughtWritePlan plan;
    const int inspected = b1cb_inspect(ram, sizeof ram, &b, field != 8, NULL, &plan) &&
        b1cb_tuple(ram, &plan, CLIP, 2, INFO);
    assert(inspected == (field <= 4 || field == 7));
    unchanged();
    assert(!b1cb_publish(ram, sizeof ram, &b, 1));
    unchanged();
    assert(!b1cb_restore(ram, sizeof ram, &b, field != 8, field != 7));
    unchanged();
    if (field >= 2 && field <= 4) {
        /* Keep the slot empty so only the reference guard can refuse publish. */
        const unsigned references[] = {B1CB_DECODER, B1CB_POSE_A, B1CB_POSE_B};
        b = setup();
        put32(ACTOR + references[field - 2], CLIP + 8);
        rejects_publish(b, 1);
    }
}
static void foreign_pair(void) {
    B1CaughtBinding b = setup();
    for (unsigned i = 0; i < 2; ++i) {
        uint32_t actor = OTHER + i*0x2000;
        put32(0x8005f80cu+4*i, actor);
        put32(actor + 0x820, COUNT);
        put32(actor + 0x824, 0x800e0000u);
        put32(actor + 0x828, 0x800e0200u);
        put32(actor + 0x82c, 0x800e0300u);
    }
    rejects_publish(b, 1);
}
static void missing_owner(void) {
    B1CaughtBinding b = setup();
    for (unsigned i = 0; i < 4; ++i) {
        uint32_t actor = OTHER + i*0x2000, tables = 0x800e0000u+i*0x1000;
        put32(0x8005f808u+4*i, actor);
        put32(actor + 0x820, COUNT);
        put32(actor + 0x824, tables);
        put32(actor + 0x828, tables+0x200);
        put32(actor + 0x82c, tables+0x300);
    }
    rejects_publish(b, 1);
}
int main(int argc, char **argv) {
    assert(argc == 3);
    int scenario = atoi(argv[1]), value = atoi(argv[2]);
    switch (scenario) {
    case 0: lifecycle(); break;
    case 1: invalid_entry(value); break;
    case 2: aliases(value); break;
    case 3: retirement(value); break;
    case 4: foreign_pair(); break;
    case 5: missing_owner(); break;
    default: assert(0);
    }
    return 0;
}
