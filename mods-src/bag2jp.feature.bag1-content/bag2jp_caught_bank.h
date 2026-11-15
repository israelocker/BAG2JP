/* Experimental immutable CAUGHT bank, prepared by the default-off
 * bag2jp.gaso_caught activation (bag2jp_gaso_caught.c); recipient lookup is
 * diagnostic only, not clip publication.
 * One zero-initialized descriptor per process/allocation lifetime; never clear
 * or copy it to reallocate on reset. Call both APIs only on a stopped VM,
 * outside render/host-output scopes; prepare before any loan. Initial failed
 * preparation is terminal. Descriptor provenance/lifetime are caller-owned.
 * Lookup rechecks guest bytes without repairing them: a restored/corrupt arena
 * must not be overwritten while a decoder may still reference it.
 */
#ifndef BAG2JP_CAUGHT_BANK_H
#define BAG2JP_CAUGHT_BANK_H
#include <stdint.h>

#define B1CC_BAG1_VERSION 1u   /* the only version with clips */

typedef struct {
    uint32_t guest_base;
    int attempted, ready;
} B1CaughtBank;
typedef struct {
    const uint8_t *allocation_data;
    uint32_t allocation_base, allocation_bytes, clip, clip_bytes;
} B1CaughtBankClip;

int b1cc_prepare(B1CaughtBank *bank);
int b1cc_lookup(const B1CaughtBank *bank, uint32_t character, uint32_t version,
                B1CaughtBankClip *out);
#endif
