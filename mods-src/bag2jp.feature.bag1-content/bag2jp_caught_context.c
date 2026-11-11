#include "bag2jp_caught_context.h"

enum { B1CR_BASE = 0x80000000u, B1CR_MAX_RAM = 0x800000,
       B1CR_CONTROLLERS = 0x8005f820u, B1CR_CONTROLLER_BYTES = 0x98,
       B1CR_ACTORS = 0x8005f808u, B1CR_MAIN_STRIDE = 8,
       B1CR_ACTOR_BYTES = 0x155c, B1CR_CHARACTER = 4, B1CR_SIDE = 5,
       B1CR_PENDING = 0x8005cf08u, B1CR_PENDING_STRIDE = 0x24,
       B1CR_PENDING_REQUEST = 0x18, B1CR_MODE_ENTRY = 1,
       B1CR_HIT_SLOT = 89, B1CR_REQUEST = 202,
       B1CR_PRIMARY_RA = 0x8002ae68u, B1CR_CONSUMER_RA = 0x8009d0c8u,
       B1CR_FRAME_BYTES = 0xd8, B1CR_SAVED_RA = 0xd4 };

static int b1cr_span(size_t bytes, uint64_t address, size_t width, unsigned alignment) {
    return address >= B1CR_BASE && address % alignment == 0 && width <= bytes &&
        address - B1CR_BASE <= bytes - width;
}
static uint32_t b1cr_value(const uint8_t *ram, uint32_t address, unsigned width) {
    uint32_t value = 0;
    for (unsigned i = 0; i < width; ++i)
        value |= (uint32_t)ram[address - B1CR_BASE + i] << (8 * i);
    return value;
}
static int b1cr_equal_word(const uint8_t *ram, size_t bytes,
                           uint64_t address, uint32_t expected) {
    return b1cr_span(bytes, address, sizeof(uint32_t), 4) &&
        b1cr_value(ram, (uint32_t)address, 4) == expected;
}
static int b1cr_original_sites(const uint8_t *ram, size_t bytes) {
    /* These original words bind the observed call chain, not the entire module.
     * Reject modified callsites rather than guessing an equivalent ABI. */
    static const struct { uint32_t address, word; } sites[] = {
        {0x80010ce0u, 0x8008f890u}, /* fixed overlay base used by this consumer */
        {0x8002ae60u, 0x0c00b41bu}, /* jal controller */
        {0x8002ae64u, 0xafb50010u}, /* fifth argument in its delay slot */
        {0x8009d0bcu, 0x24071000u}, /* a3 = 4096 */
        {0x8009d0c0u, 0x0c00a824u}, /* jal dispatcher */
        {0x8009d0c4u, 0xafa20010u}, /* fifth argument in its delay slot */
    };
    for (size_t i = 0; i < sizeof sites / sizeof sites[0]; ++i)
        if (!b1cr_equal_word(ram, bytes, sites[i].address, sites[i].word)) return 0;
    return 1;
}
static int b1cr_actors(const uint8_t *ram, size_t bytes, uint32_t controller,
                       uint32_t side, B1CaughtCallContext *context) {
    if (!b1cr_span(bytes, controller, B1CR_CONTROLLER_BYTES, 4) ||
        !b1cr_span(bytes, B1CR_ACTORS, 2 * B1CR_MAIN_STRIDE, 4)) return 0;
    const uint32_t actor = b1cr_value(ram, controller, 4);
    const uint32_t opponent = b1cr_value(ram,
        B1CR_ACTORS + (side ^ 1u) * B1CR_MAIN_STRIDE, 4);
    if (!b1cr_span(bytes, actor, B1CR_ACTOR_BYTES, 4) ||
        !b1cr_span(bytes, opponent, B1CR_ACTOR_BYTES, 4) || actor == opponent ||
        b1cr_value(ram, B1CR_ACTORS + side * B1CR_MAIN_STRIDE, 4) != actor ||
        b1cr_value(ram, actor + B1CR_SIDE, 1) != side ||
        b1cr_value(ram, opponent + B1CR_SIDE, 1) != (side ^ 1u)) return 0;
    *context = (B1CaughtCallContext){controller, actor, side,
        b1cr_value(ram, actor + B1CR_CHARACTER, 1), opponent,
        b1cr_value(ram, opponent + B1CR_CHARACTER, 1), B1CR_REQUEST};
    return 1;
}
int b1cr_read_context(const uint8_t *ram, size_t bytes,
                     const B1CaughtCallRegisters *call, B1CaughtCallContext *out) {
    if (!ram || !call || !out || !bytes || bytes > B1CR_MAX_RAM ||
        call->mode != B1CR_MODE_ENTRY || call->slot != B1CR_HIT_SLOT ||
        call->ra != B1CR_PRIMARY_RA) return 0;
    uint32_t side;
    if (call->controller == B1CR_CONTROLLERS) side = 0;
    else if (call->controller == B1CR_CONTROLLERS + B1CR_CONTROLLER_BYTES) side = 1;
    else return 0;
    if (!b1cr_span(bytes, call->sp, B1CR_FRAME_BYTES, 4) ||
        !b1cr_equal_word(ram, bytes, (uint64_t)call->sp + B1CR_SAVED_RA,
                         B1CR_CONSUMER_RA) || !b1cr_original_sites(ram, bytes)) return 0;
    const uint32_t pending = B1CR_PENDING + side * B1CR_PENDING_STRIDE + B1CR_PENDING_REQUEST;
    if (!b1cr_span(bytes, pending, sizeof(uint16_t), 2) ||
        b1cr_value(ram, pending, 2) != B1CR_REQUEST) return 0;
    B1CaughtCallContext context;
    if (!b1cr_actors(ram, bytes, call->controller, side, &context)) return 0;
    *out = context;
    return 1;
}
