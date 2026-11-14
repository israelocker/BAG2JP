/* Synthetic snapshots, real production readers, pinned original code inputs. */
#undef NDEBUG
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "bag2jp_caught_source.h"

enum { BASE = 0x80000000u, RAM_BYTES = 0x800000,
       LIST = 0x8005f808u, CONTROLLERS = 0x8005f820u, STATE = 0x8005e728u,
       PENDING = 0x8005cf08u, STACK = 0x807ffe00u, ACTOR = 0x80410000u,
       OTHER = 0x800c0000u, SITE = 0x8009b5b4u, LAST_ACTOR = 0x807feaa4u };
static uint8_t ram[RAM_BYTES], before[RAM_BYTES];
static B1CaughtSourceRegisters producer;
static B1CaughtCallRegisters consumer;
static B1CaughtSourceClock clock_value;
static B1CaughtSource record;

static void put(uint32_t address, uint32_t value, unsigned width) {
    assert(address >= BASE && address - BASE <= RAM_BYTES - width);
    for (unsigned i = 0; i < width; ++i) ram[address - BASE + i] = (uint8_t)(value >> (8 * i));
}
static void load(const char *path, uint32_t address, long skip, size_t bytes) {
    FILE *file = fopen(path, "rb");
    assert(file && !fseek(file, skip, SEEK_SET));
    assert(fread(ram + address - BASE, 1, bytes, file) == bytes);
    assert(!fclose(file));
}
static void fixture(const char *main, const char *overlay, unsigned side,
                     unsigned self, unsigned source_character) {
    memset(ram, 0, sizeof ram); memset(&record, 0, sizeof record);
    load(main, 0x80010000u, 0, 0x4d000); load(overlay, 0x8008f890u, 12, 61675);
    put(0x80010ce0u, 0x8008f890u, 4);
    put(LIST + 8 * side, ACTOR, 4); put(LIST + 8 * (side ^ 1u), OTHER, 4);
    put(ACTOR + 4, self ? source_character : 0, 1); put(ACTOR + 5, side, 1);
    put(OTHER + 4, self ? 9 : source_character, 1); put(OTHER + 5, side ^ 1u, 1);
    put(CONTROLLERS + side * 0x98, ACTOR, 4);
    put(STACK + 0x30 + side, self ? 2 : 1, 1);
    put(STACK + 0xd4, 0x8009d0c8u, 4);
    put(PENDING + side * 0x24 + 0x18, 0xffff, 2);
    producer = (B1CaughtSourceRegisters){SITE, 202, self ? side : side ^ 1u,
        side, PENDING + side * 0x24, STACK};
    consumer = (B1CaughtCallRegisters){CONTROLLERS + side * 0x98, 1, 89, STACK, 0x8002ae68u};
    clock_value = (B1CaughtSourceClock){17, 120};
}
static int capture(size_t bytes) {
    return b1cs_capture(&record, ram, bytes, &producer, &clock_value);
}
static int take(B1CaughtSource *out) {
    return b1cs_take(&record, ram, sizeof ram, &consumer, &clock_value, out);
}
static void publish(void) {
    /* ONLY the fixture models the original sh. Production must not write it. */
    put(producer.pending + 0x18, 202, 2);
}
static void positive(unsigned side, unsigned self, unsigned character) {
    memcpy(before, ram, sizeof ram);
    assert(capture(sizeof ram) && record.available);
    assert(!memcmp(before, ram, sizeof ram));
    assert(record.actor == ACTOR && record.side == side && record.source_side == (self ? side : side ^ 1u));
    assert(record.source_actor == (self ? ACTOR : OTHER));
    assert(record.source_character == character && record.request == 202 && record.reflected == self);
    publish(); memcpy(before, ram, sizeof ram);
    B1CaughtSource out = {0}; assert(take(&out));
    assert(!record.available && out.available && out.source_character == character && out.reflected == self);
    assert(!memcmp(before, ram, sizeof ram));
    memset(&out, 0xa5, sizeof out); B1CaughtSource old = out;
    assert(!take(&out) && !memcmp(&old, &out, sizeof out));
}
static void bad_capture(unsigned kind) {
    switch (kind) {
        case 0: producer.pc += 4; break;
        case 1: producer.request = 201; break;
        case 2: producer.source_side = 2; break;
        case 3: producer.recipient_side = 2; break;
        case 4: producer.pending += 0x24; break;
        case 5: producer.sp = 0xfffffffcu; break;
        case 6: producer.sp += 1; break;
        case 7: put(STACK + 0x30 + producer.recipient_side, 0, 1); break;
        case 8: put(STACK + 0x30 + producer.recipient_side, 2, 1); break;
        case 9: put(LIST + 8 * producer.source_side, ACTOR, 4); break;
        case 10: put(OTHER + 5, producer.recipient_side, 1); break;
        case 11: put(OTHER + 4, 8, 1); break;
        case 12: put(SITE, 0, 4); break;
        case 13: put(0x80010ce0u, 0, 4); break;
        case 14: put(0x80051458u + 18, 201, 1); break;
        case 15: clock_value.generation = 0; break;
        case 16: put(LIST + 8 * producer.source_side, 0xfffffffcu, 4); break;
        case 17: put(LIST + 8 * producer.recipient_side, 0xfffffffcu, 4); break;
        case 18: put(OTHER + 5, 2, 1); break;
        case 19: put(0x8009b5acu, 0, 4); break;
        case 20: put(0x8009b5b0u, 1, 4); break;
        case 21: put(STACK + 0x30 + producer.recipient_side, 3, 1); break;
        default: assert(0);
    }
    memset(&record, 0xa5, sizeof record); memcpy(before, ram, sizeof ram); const B1CaughtSource empty = {0};
    assert(!capture(sizeof ram) && !memcmp(&record, &empty, sizeof record));
    assert(!memcmp(before, ram, sizeof ram));
}
static void bad_take(unsigned kind) {
    assert(capture(sizeof ram)); publish();
    switch (kind) {
        case 0: ++clock_value.generation; break;
        case 1: ++clock_value.tick; break;
        case 2: --clock_value.tick; break;
        case 3: consumer.ra = 0x8002afe4u; break;
        case 4: put(producer.pending + 0x18, 172, 2); break;
        case 5: put(OTHER + 4, 0, 1); break;
        case 6: put(ACTOR + 4, 1, 1); break;
        case 7: put(LIST + 8 * producer.source_side, 0, 4); break;
        case 8: consumer.slot = 90; break;
        case 9: record.request = 201; break;
        case 10: record.side ^= 1u; break;
        case 11: record.source_side ^= 1u; break;
        case 12: record.source_actor += 4; break;
        case 13: record.actor += 4; break;
        case 14: record.reflected = 1; break;
        case 15: put(0x8009d0c0u, 0, 4); break;
        default: assert(0);
    }
    B1CaughtSource out; memset(&out, 0xa5, sizeof out); B1CaughtSource old = out;
    memcpy(before, ram, sizeof ram);
    assert(!take(&out) && !record.available && !memcmp(&out, &old, sizeof out));
    assert(!memcmp(before, ram, sizeof ram));
}
static void null_and_bounds(unsigned kind) {
    B1CaughtSource out = {0}; assert(capture(sizeof ram));
    switch (kind) {
        case 0: assert(!b1cs_capture(NULL, ram, sizeof ram, &producer, &clock_value)); break;
        case 1: assert(!b1cs_capture(&record, NULL, sizeof ram, &producer, &clock_value)); break;
        case 2: assert(!b1cs_capture(&record, ram, sizeof ram, NULL, &clock_value)); break;
        case 3: assert(!b1cs_capture(&record, ram, sizeof ram, &producer, NULL)); break;
        case 4: assert(!capture(0)); break;
        case 5: assert(!capture(RAM_BYTES + 1)); break;
        case 6: assert(!capture(ACTOR - BASE + 0x155b)); break;
        case 7: assert(!b1cs_take(&record, NULL, sizeof ram, &consumer, &clock_value, &out)); break;
        case 8: assert(!b1cs_take(&record, ram, sizeof ram, NULL, &clock_value, &out)); break;
        case 9: assert(!b1cs_take(&record, ram, sizeof ram, &consumer, NULL, &out)); break;
        case 10: assert(!b1cs_take(&record, ram, sizeof ram, &consumer, &clock_value, NULL)); break;
        case 11: assert(!b1cs_take(NULL, ram, sizeof ram, &consumer, &clock_value, &out)); break;
        default: assert(0);
    }
    if (kind != 0 && kind != 11) assert(!record.available);
}
static void move_main(unsigned side, uint32_t address, unsigned character) {
    put(LIST + side * 8, address, 4);
    if (address >= BASE && address <= BASE + RAM_BYTES - 6) {
        put(address + 4, character, 1); put(address + 5, side, 1);
    }
}
static void boundaries(unsigned kind) {
    size_t bytes = sizeof ram; int expected = 0;
    producer.sp = 0x80070000u;
    put(producer.sp + 0x30 + producer.recipient_side, 1, 1);
    switch (kind) {
        case 0: move_main(producer.source_side, LAST_ACTOR, 9); expected = 1; break;
        case 1: move_main(producer.source_side, LAST_ACTOR + 4, 9); break;
        case 2: move_main(producer.recipient_side, LAST_ACTOR, 0); expected = 1; break;
        case 3: move_main(producer.recipient_side, LAST_ACTOR + 4, 0); break;
        case 4: bytes = ACTOR - BASE + 0x155c; expected = 1; break;
        case 5: bytes = ACTOR - BASE + 0x155b; break;
        case 6: producer.sp = 0x807fffccu; put(producer.sp + 0x30 + producer.recipient_side, 1, 1);
            expected = 1; break;
        case 7: producer.sp = 0x807fffd0u; break;
        case 8: put(OTHER + 4, 18, 1); break;
        case 9: put(OTHER + 4, 255, 1); break;
        case 10: move_main(producer.source_side, OTHER + 1, 9); break;
        case 11: clock_value.tick = 0; expected = 1; break;
        default: assert(0);
    }
    memcpy(before, ram, sizeof ram);
    assert(capture(bytes) == expected && record.available == expected);
    assert(!memcmp(before, ram, sizeof ram));
}
int main(int argc, char **argv) {
    assert(argc == 6);
    unsigned scenario = (unsigned)strtoul(argv[1], NULL, 10);
    unsigned kind = (unsigned)strtoul(argv[2], NULL, 10);
    unsigned setup = (unsigned)strtoul(argv[5], NULL, 10);
    unsigned side = setup & 1u, self = (setup >> 1) & 1u;
    unsigned character = kind == 0 ? 0 : kind == 1 ? 1 : 9;
    fixture(argv[3], argv[4], side, self, scenario == 0 ? character : 9);
    if (scenario == 0) positive(side, self, character);
    else if (scenario == 1) bad_capture(kind);
    else if (scenario == 2) bad_take(kind);
    else if (scenario == 3) null_and_bounds(kind);
    else if (scenario == 4) boundaries(kind);
    else assert(0);
    return 0;
}
