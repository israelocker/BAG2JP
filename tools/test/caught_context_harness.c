/* Real reader and pinned original code, synthetic actors/stack/pending state. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "bag2jp_caught_context.h"
#undef NDEBUG
#include <assert.h>

enum { RAM_BYTES = 0x800000, RAM_BASE = 0x80000000u, ACTOR_BYTES = 0x155c,
       LOW_ACTOR = 0x800b0000u, HIGH_ACTOR = 0x80410000u,
       OTHER_ACTOR = 0x800c0000u, STACK = 0x807ffe00u,
       CONTROLLERS = 0x8005f820u, LIST = 0x8005f808u,
       MODULE_BASE = 0x8008f890u, MODULE_POINTER = 0x80010ce0u,
       PENDING = 0x8005cf08u, CONTROLLER_STRIDE = 0x98, SIDE_STRIDE = 0x24,
       LOW_STACK = 0x80070000u, FRAME_BYTES = 0xd8, SAVED_RA = 0xd4,
       LAST_ACTOR = RAM_BASE + RAM_BYTES - ACTOR_BYTES,
       LAST_FRAME = RAM_BASE + RAM_BYTES - FRAME_BYTES };
static uint8_t ram[RAM_BYTES], before[RAM_BYTES];
static B1CaughtCallRegisters call;
static B1CaughtCallContext context;
static uint32_t actor, side, controller, pending;

static void put(uint32_t address, uint32_t value, unsigned width) {
    assert(address >= RAM_BASE && (uint64_t)address - RAM_BASE + width <= RAM_BYTES);
    for (unsigned i = 0; i < width; ++i)
        ram[address - RAM_BASE + i] = (uint8_t)(value >> (8 * i));
}
static void load_code(const char *main_path, const char *overlay_path) {
    memset(ram, 0, sizeof ram);
    FILE *file = fopen(main_path, "rb"); assert(file);
    size_t bytes = fread(ram + 0x10000, 1, 0x4d000, file);
    assert(bytes == 0x4d000 && !ferror(file)); fclose(file);
    file = fopen(overlay_path, "rb"); assert(file);
    assert(fseek(file, 12, SEEK_SET) == 0);
    bytes = fread(ram + MODULE_BASE - RAM_BASE, 1, 0x20000, file);
    assert(bytes > 0 && bytes < 0x20000 && !ferror(file)); fclose(file);
}
static void setup(unsigned kind) {
    side = kind & 1u; actor = kind & 2u ? HIGH_ACTOR : LOW_ACTOR;
    controller = CONTROLLERS + side * CONTROLLER_STRIDE;
    pending = PENDING + side * SIDE_STRIDE + 0x18;
    put(MODULE_POINTER, MODULE_BASE, 4);
    put(controller, actor, 4); put(LIST + side * 8, actor, 4);
    put(LIST + (side ^ 1u) * 8, OTHER_ACTOR, 4);
    put(actor + 4, 0, 1); put(actor + 5, side, 1);
    put(OTHER_ACTOR + 4, 9, 1); put(OTHER_ACTOR + 5, side ^ 1u, 1);
    put(pending, 202, 2); put(STACK + 0xd4, 0x8009d0c8u, 4);
    call = (B1CaughtCallRegisters){controller, 1, 89, STACK, 0x8002ae68u};
    memset(&context, 0xa5, sizeof context);
}
static void assert_read(int expected, size_t bytes) {
    B1CaughtCallContext old = context;
    B1CaughtCallRegisters old_call = call;
    memcpy(before, ram, sizeof ram);
    assert(b1cr_read_context(ram, bytes, &call, &context) == expected);
    assert(!memcmp(before, ram, sizeof ram));
    assert(!memcmp(&old_call, &call, sizeof call));
    if (!expected) assert(!memcmp(&old, &context, sizeof context));
}
static void success(unsigned kind) {
    if (kind & 4u) put(OTHER_ACTOR + 4, 0, 1);
    if (kind & 8u) put(actor + 4, 1, 1);
    assert_read(1, RAM_BYTES);
    assert(context.controller == controller && context.actor == actor);
    assert(context.side == side && context.character == (kind & 8u ? 1u : 0u));
    assert(context.opponent == OTHER_ACTOR);
    assert(context.opponent_character == (kind & 4u ? 0u : 9u));
    assert(context.source_request == 202);
}
static void corrupt_call(unsigned kind) {
    switch (kind) {
    case 0: call.controller = actor; break; /* a0 is NOT the actor */
    case 1: call.controller += 0x4c; break;
    case 2: call.controller = 0xffffffffu; break;
    case 3: call.mode = 0; break;
    case 4: call.mode = 2; break;
    case 5: call.slot = 202; break;
    case 6: call.slot = 1; break;
    case 7: call.slot = 90; break;
    case 8: call.ra = 0x8002afe4u; break;
    case 9: call.ra = 0x8002b06cu; break;
    case 10: call.ra = 0; break;
    case 11: call.sp = 0xffffff80u; break; /* would wrap sp+d4 */
    case 12: call.sp = 0x807fff80u; break;
    case 13: call.sp += 2; break;
    default: abort();
    }
}
static void corrupt_memory(unsigned kind) {
    switch (kind) {
    case 0: put(controller, 0, 4); break;
    case 1: put(controller, 0x807ff000u, 4); break;
    case 2: put(controller, actor + 1, 4); break;
    case 3: put(LIST + side * 8, OTHER_ACTOR, 4); break;
    case 4: put(actor + 5, 2, 1); break;
    case 5: put(actor + 5, side ^ 1u, 1); break;
    case 6: put(LIST + (side ^ 1u) * 8, 0, 4); break;
    case 7: put(LIST + (side ^ 1u) * 8, actor, 4); break;
    case 8: put(LIST + (side ^ 1u) * 8, 0x807ff000u, 4); break;
    case 9: put(OTHER_ACTOR + 5, side, 1); break;
    case 10: put(pending, 200, 2); break;
    case 11: put(pending, 201, 2); break;
    case 12: put(pending, 203, 2); break;
    case 13: put(pending, 204, 2); break;
    case 14: put(pending, 0xffff, 2); break;
    case 15: put(STACK + 0xd4, 0x8009d000u, 4); break;
    case 16: put(MODULE_POINTER, MODULE_BASE + 4, 4); break;
    case 17: put(0x8002ae60u, 0, 4); break;
    case 18: put(0x8002ae64u, 0, 4); break;
    case 19: put(0x8009d0bcu, 0, 4); break;
    case 20: put(0x8009d0c0u, 0, 4); break;
    case 21: put(0x8009d0c4u, 0, 4); break;
    case 22: put(pending, 0x01ca, 2); break; /* low byte 202 is insufficient */
    default: abort();
    }
}
static void null_and_bounds(unsigned kind) {
    B1CaughtCallContext old = context;
    memcpy(before, ram, sizeof ram);
    int result = -1;
    switch (kind) {
    case 0: result = b1cr_read_context(NULL, RAM_BYTES, &call, &context); break;
    case 1: result = b1cr_read_context(ram, RAM_BYTES, NULL, &context); break;
    case 2: result = b1cr_read_context(ram, RAM_BYTES, &call, NULL); break;
    case 3: result = b1cr_read_context(ram, 0, &call, &context); break;
    case 4: result = b1cr_read_context(ram, RAM_BYTES + 1, &call, &context); break;
    case 5: result = b1cr_read_context(ram, 16, &call, &context); break;
    case 6: result = b1cr_read_context(ram, STACK - RAM_BASE + 0xd7, &call, &context); break;
    default: abort();
    }
    assert(result == 0 && !memcmp(&old, &context, sizeof context));
    assert(!memcmp(before, ram, sizeof ram));
}
static void move_actor(uint32_t address) {
    put(controller, address, 4); put(LIST + side * 8, address, 4);
    if (address >= RAM_BASE && address <= RAM_BASE + RAM_BYTES - 6) {
        put(address + 4, 0, 1); put(address + 5, side, 1);
    }
}
static void move_opponent(uint32_t address) {
    put(LIST + (side ^ 1u) * 8, address, 4);
    put(address + 4, 9, 1); put(address + 5, side ^ 1u, 1);
}
static void boundaries(unsigned kind) {
    size_t bytes = RAM_BYTES;
    int expected = 0;
    call.sp = LOW_STACK; put(call.sp + SAVED_RA, 0x8009d0c8u, 4);
    switch (kind) {
    case 0: move_actor(LAST_ACTOR); expected = 1; break;
    case 1: move_actor(LAST_ACTOR + 4); break;
    case 2: move_opponent(LAST_ACTOR); expected = 1; break;
    case 3: move_opponent(LAST_ACTOR + 4); break;
    case 4: call.sp = LAST_FRAME; expected = 1; break;
    case 5: call.sp = LAST_FRAME; --bytes; break;
    case 6: move_actor(HIGH_ACTOR); bytes = HIGH_ACTOR - RAM_BASE + ACTOR_BYTES;
        expected = 1; break;
    case 7: move_actor(HIGH_ACTOR); bytes = HIGH_ACTOR - RAM_BASE + ACTOR_BYTES - 1; break;
    case 8: move_opponent(HIGH_ACTOR); bytes = HIGH_ACTOR - RAM_BASE + ACTOR_BYTES;
        expected = 1; break;
    case 9: move_opponent(HIGH_ACTOR); bytes = HIGH_ACTOR - RAM_BASE + ACTOR_BYTES - 1; break;
    case 10: move_opponent(OTHER_ACTOR + 1); break;
    case 11: move_actor(0); break;
    case 12: move_actor(0xfffffffcu); break;
    case 13: move_actor(actor + 1); break;
    default: abort();
    }
    put(call.sp + SAVED_RA, 0x8009d0c8u, 4);
    assert_read(expected, bytes);
}
int main(int argc, char **argv) {
    assert(argc == 6);
    unsigned scenario = (unsigned)atoi(argv[1]), kind = (unsigned)atoi(argv[2]);
    load_code(argv[3], argv[4]); setup((unsigned)atoi(argv[5]));
    switch (scenario) {
    case 0: success(kind); break;
    case 1: corrupt_call(kind); assert_read(0, RAM_BYTES); break;
    case 2: corrupt_memory(kind); assert_read(0, RAM_BYTES); break;
    case 3: null_and_bounds(kind); break;
    case 4: boundaries(kind); break;
    default: abort();
    }
    return 0;
}
