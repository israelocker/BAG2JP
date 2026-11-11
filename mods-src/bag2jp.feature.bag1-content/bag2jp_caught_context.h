/* Experimental read-only snapshot reader, NOT wired to the runtime.
 * Success identifies one conservative original request202 callsite, NOT a
 * Gas-O attack: versions, reflection exclusion and generation remain unproven.
 * Caller owns a stopped coherent main-RAM snapshot and non-aliasing output.
 * Registers belong to that same instant; sp is the controller-callee entry sp.
 * The declared byte count must not exceed the actual buffer's available length.
 */
#ifndef BAG2JP_CAUGHT_CONTEXT_H
#define BAG2JP_CAUGHT_CONTEXT_H
#include <stddef.h>
#include <stdint.h>

typedef struct {
    uint32_t controller, mode, slot, sp, ra;
} B1CaughtCallRegisters;
typedef struct {
    uint32_t controller, actor, side, character;
    uint32_t opponent, opponent_character, source_request;
} B1CaughtCallContext;

/* On refusal, output is unchanged. This never writes RAM or CPU registers.
 * Partial code fingerprints reject drift; they do not authenticate an entire
 * module or establish its lifetime. Do not convert this result into attack facts.
 */
int b1cr_read_context(const uint8_t *ram, size_t bytes,
                     const B1CaughtCallRegisters *call, B1CaughtCallContext *out);
#endif
