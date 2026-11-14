#include "bag2jp_caught_source.h"
#include <string.h>

enum { B1CS_BASE = 0x80000000u, B1CS_MAX_RAM = 0x800000,
       B1CS_SITE = 0x8009b5b4u, B1CS_OVERLAY_BASE_PTR = 0x80010ce0u,
       B1CS_OVERLAY_BASE = 0x8008f890u,
       B1CS_LOAD_CHAR_BYTE = 0x8009b5acu, B1CS_LOAD_DELAY_NOP = 0x8009b5b0u,
       B1CS_ACTORS = 0x8005f808u,
       B1CS_MAIN_STRIDE = 8, B1CS_ACTOR_BYTES = 0x155c,
       B1CS_CHARACTER = 4, B1CS_SIDE = 5, B1CS_TABLE = 0x80051458u,
       B1CS_VERIFIED_TABLE_ROWS = 18, B1CS_PENDING = 0x8005cf08u,
       B1CS_PENDING_STRIDE = 0x24, B1CS_REQUEST = 202,
       B1CS_STACK_FLAGS = 0x30, B1CS_STACK_BYTES = 0x32 };

static int b1cs_span(size_t bytes, uint64_t address, size_t width, unsigned alignment) {
    return address >= B1CS_BASE && address % alignment == 0 && width <= bytes &&
        address - B1CS_BASE <= bytes - width;
}
static uint32_t b1cs_value(const uint8_t *ram, uint32_t address, unsigned width) {
    uint32_t value = 0;
    for (unsigned i = 0; i < width; ++i)
        value |= (uint32_t)ram[address - B1CS_BASE + i] << (8 * i);
    return value;
}
static int b1cs_sites(const uint8_t *ram, size_t bytes) {
    /* Partial original-code drift filter, not module authentication. */
    static const struct { uint32_t address, word; } sites[] = {
        {B1CS_OVERLAY_BASE_PTR, B1CS_OVERLAY_BASE},
        {B1CS_LOAD_CHAR_BYTE, 0x90420000u}, /* lbu v0,0(v0) */
        {B1CS_LOAD_DELAY_NOP, 0x00000000u}, /* load delay */
        {B1CS_SITE, 0xa6a20018u},   /* sh v0,0x18(s5), NOT executed here */
    };
    for (size_t i = 0; i < sizeof sites / sizeof sites[0]; ++i)
        if (!b1cs_span(bytes, sites[i].address, 4, 4) ||
            b1cs_value(ram, sites[i].address, 4) != sites[i].word) return 0;
    return 1;
}
static int b1cs_actors(const uint8_t *ram, size_t bytes,
                       const B1CaughtSourceRegisters *r, B1CaughtSource *value) {
    if (!b1cs_span(bytes, B1CS_ACTORS, 2 * B1CS_MAIN_STRIDE, 4)) return 0;
    uint32_t actors[2];
    for (uint32_t side = 0; side < 2; ++side) {
        actors[side] = b1cs_value(ram, B1CS_ACTORS + side * B1CS_MAIN_STRIDE, 4);
        if (!b1cs_span(bytes, actors[side], B1CS_ACTOR_BYTES, 4) ||
            b1cs_value(ram, actors[side] + B1CS_SIDE, 1) != side) return 0;
    }
    if (actors[0] == actors[1]) return 0;
    value->actor = actors[r->recipient_side];
    value->character = b1cs_value(ram, value->actor + B1CS_CHARACTER, 1);
    value->source_actor = actors[r->source_side];
    value->source_character = b1cs_value(ram, value->source_actor + B1CS_CHARACTER, 1);
    if (value->source_character >= B1CS_VERIFIED_TABLE_ROWS) return 0;
    const uint32_t row = B1CS_TABLE + 2 * value->source_character;
    return b1cs_span(bytes, row, 1, 1) && b1cs_value(ram, row, 1) == r->request;
}

int b1cs_capture(B1CaughtSource *record, const uint8_t *ram, size_t bytes,
                 const B1CaughtSourceRegisters *registers,
                 const B1CaughtSourceClock *clock) {
    if (!record) return 0;
    memset(record, 0, sizeof *record);
    if (!ram || !registers || !clock || !clock->generation || !bytes ||
        bytes > B1CS_MAX_RAM) return 0;
    const B1CaughtSourceRegisters *r = registers;
    if (r->pc != B1CS_SITE || r->request != B1CS_REQUEST || r->source_side > 1 ||
        r->recipient_side > 1 || r->pending != B1CS_PENDING +
        B1CS_PENDING_STRIDE * r->recipient_side ||
        !b1cs_span(bytes, r->sp, B1CS_STACK_BYTES, 4) || !b1cs_sites(ram, bytes)) return 0;
    const uint32_t reflected = r->source_side == r->recipient_side;
    if (b1cs_value(ram, r->sp + B1CS_STACK_FLAGS + r->recipient_side, 1) !=
        (reflected ? 2u : 1u)) return 0;
    B1CaughtSource value = {0};
    if (!b1cs_actors(ram, bytes, r, &value)) return 0;
    value.clock = *clock; value.side = r->recipient_side;
    value.source_side = r->source_side; value.request = r->request;
    value.reflected = reflected; value.available = 1;
    *record = value;
    return 1;
}
int b1cs_take(B1CaughtSource *record, const uint8_t *ram, size_t bytes,
              const B1CaughtCallRegisters *call, const B1CaughtSourceClock *clock,
              B1CaughtSource *out) {
    if (!record) return 0;
    const B1CaughtSource value = *record;
    record->available = 0; /* Refusal must not leave a stale retry authorization. */
    if (!out || !clock || !clock->generation || value.available != 1 ||
        value.clock.generation != clock->generation || value.clock.tick != clock->tick ||
        value.side > 1 || value.source_side > 1 || value.request != B1CS_REQUEST ||
        value.reflected != (uint32_t)(value.side == value.source_side)) return 0;
    B1CaughtCallContext context;
    if (!b1cr_read_context(ram, bytes, call, &context) || value.side != context.side ||
        value.actor != context.actor || value.character != context.character) return 0;
    const uint32_t source = value.reflected ? context.actor : context.opponent;
    const uint32_t character = value.reflected ? context.character : context.opponent_character;
    if (value.source_actor != source || value.source_character != character) return 0;
    *out = value;
    return 1;
}
