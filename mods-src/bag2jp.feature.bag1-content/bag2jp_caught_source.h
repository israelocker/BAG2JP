/* Experimental stopped-snapshot provenance only; NOT runtime authorization.
 * Registers must come from BEFORE the original producer instruction executes.
 * Keep one record per recipient. Capture invalidates the supplied record even
 * on refusal; take consumes it even on mismatch. RAM/register/output buffers
 * must not alias. Available RAM length and coherent stopped execution are caller
 * preconditions, as are trustworthy generation/tick values. Generation must
 * change on load/reset/content changes; rollback must restore the record with
 * its RAM and clock. Neither lifecycle nor effective BAG1 version is established
 * here. No runtime hooks, guest writes, clip publication or pose changes. */
#ifndef BAG2JP_CAUGHT_SOURCE_H
#define BAG2JP_CAUGHT_SOURCE_H
#include <stddef.h>
#include <stdint.h>
#include "bag2jp_caught_context.h"

typedef struct {
    uint32_t pc, request, source_side, recipient_side, pending, sp;
} B1CaughtSourceRegisters;
typedef struct { uint64_t generation, tick; } B1CaughtSourceClock;
typedef struct {
    B1CaughtSourceClock clock;
    uint32_t actor, character, side, source_actor, source_character, source_side;
    uint32_t request, reflected;
    int available;
} B1CaughtSource;

/* Return 1 only for a verified request202 publication, irrespective of attacker
 * version. A Heat/Strike publication must NOT become Gas-O authorization. */
int b1cs_capture(B1CaughtSource *record, const uint8_t *ram, size_t bytes,
                 const B1CaughtSourceRegisters *registers,
                 const B1CaughtSourceClock *clock);
int b1cs_take(B1CaughtSource *record, const uint8_t *ram, size_t bytes,
              const B1CaughtCallRegisters *call, const B1CaughtSourceClock *clock,
              B1CaughtSource *out);
#endif
