/* Authentic immutable CAUGHT clips. No constructor: bag2jp_gaso_caught.c
 * prepares the bank from its activation callback. */
#include "bag2jp_caught_bank.h"
#include "mod_plugins.h"
#include <stddef.h>

typedef struct { uint32_t character, offset, bytes; } B1CaughtBankEntry;
#include "bag2jp_caught_bank_data.inc"

#define B1CC_GUEST_BASE 0x9f000000u
#define B1CC_GUEST_BYTES 0x00100000u
#define B1CC_BAG1_VERSION 1u

static int b1cc_valid_base(uint32_t base) {
    return base >= B1CC_GUEST_BASE && !(base & 3u) &&
           base - B1CC_GUEST_BASE <= B1CC_GUEST_BYTES - B1CC_BANK_BYTES;
}
static int b1cc_matches(uint32_t base) {
    if (!b1cc_valid_base(base)) return 0;
    for (uint32_t i = 0; i < B1CC_BANK_BYTES; ++i)
        if (psx_mod_read_byte(base + i) != b1cc_data[i]) return 0;
    return 1;
}
int b1cc_prepare(B1CaughtBank *bank) {
    if (!bank) return 0;
    if (bank->attempted) return bank->ready && b1cc_matches(bank->guest_base);
    bank->attempted = 1;
    bank->ready = 0;
    bank->guest_base = psx_mod_alloc_guest_memory(B1CC_BANK_BYTES, 4u);
    if (!b1cc_valid_base(bank->guest_base)) return 0;
    for (uint32_t i = 0; i < B1CC_BANK_BYTES; ++i)
        psx_mod_write_byte(bank->guest_base + i, b1cc_data[i]);
    bank->ready = b1cc_matches(bank->guest_base);
    return bank->ready;
}
int b1cc_lookup(const B1CaughtBank *bank, uint32_t character, uint32_t version,
                B1CaughtBankClip *out) {
    if (!bank || !out || !bank->attempted || !bank->ready ||
        version != B1CC_BAG1_VERSION) return 0;
    for (size_t i = 0; i < sizeof b1cc_entries / sizeof b1cc_entries[0]; ++i) {
        const B1CaughtBankEntry *entry = &b1cc_entries[i];
        if (entry->character != character) continue;
        if (!b1cc_matches(bank->guest_base)) return 0;
        *out = (B1CaughtBankClip){b1cc_data, bank->guest_base, B1CC_BANK_BYTES,
                                bank->guest_base + entry->offset, entry->bytes};
        return 1;
    }
    return 0;
}
