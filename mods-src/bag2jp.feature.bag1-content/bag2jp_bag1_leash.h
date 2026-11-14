/* Lateral leash of BAG1-version dancers. Each dancer slot has a control block at
 * 0x8005F820 + slot * 0x4C (FUN_8001E0F4 -> FUN_8002B5BC): word 0 dancer pointer,
 * +0x28 home X, +0x38 radius. FUN_8002D85C stores the radius once (table 0x80051A70,
 * 440 on most stages) and the caller scales it by the stage zoom (0x8002BA20..38).
 * Every frame FUN_8002CD48 (called at 0x8002D818, lw a2,0x38) clamps the root to that
 * radius around home. BAG2 keeps |home X| 520 with radius 440, so dancers may drift
 * to 160 units apart; BAG1 (scus 0x800320C0, 0x80030A30) uses home 784 and radius 480.
 * BAG1 clips walk that far, so BAG1 dancers end shoulder to shoulder in BAG2.
 * This tightens BAG1's radius/home proportion to |home X| * 300 / 784
 * (199 on most stages) so dancers remain close to their initial positions. It
 * only tightens the leash and skips a zero home (stage 0xB).
 * Native unlimited radius is preserved: overlay 005 writes INT_MAX to all four
 * controls at 0x8009CB0C/10 before advancing phase 4 to 5 (0x8005D3DC).
 * Only the completed native zoom-scaled radius is tightened: VBlank can interrupt
 * initialization after the raw store but before the caller's zoom multiply. */
#ifndef BAG2JP_BAG1_LEASH_H
#define BAG2JP_BAG1_LEASH_H

#include <stdint.h>
#include <string.h>

#define B1LEASH_CTL          0x8005F820u
#define B1LEASH_CTL_STRIDE   0x4Cu
#define B1LEASH_HOME_X       0x28u
#define B1LEASH_RADIUS       0x38u
#define B1LEASH_RAW_RADIUS   0x3Cu  /* Unscaled table value, stored at 0x8002D920. */
#define B1LEASH_STAGE_PTR    0x80089200u
#define B1LEASH_STAGE_ZOOM   4u     /* Signed halfword, 256 means 1x. */
#define B1LEASH_RAM_LOW      0x80010000u
#define B1LEASH_RAM_END      0x80800000u
#define B1LEASH_BAG1_RADIUS  300u
#define B1LEASH_BAG1_HOME    784u
#define B1LEASH_UNLIMITED    0x7FFFFFFFu  /* Native transition deliberately releases the leash. */

#include "bag2jp_bag1_home.h"

static uint32_t b1leash_dancer[4], b1leash_radius[4];

/* BAG1-proportioned radius for this home, or `stock` when that would not tighten it. */
static uint32_t b1leash_target(int32_t home_x, uint32_t stock) {
    if (stock == B1LEASH_UNLIMITED) return stock;
    const uint32_t home = home_x < 0 ? 0u - (uint32_t)home_x : (uint32_t)home_x;
    if (home == 0u || home > 0x10000u) return stock;
    const uint32_t radius = (home * B1LEASH_BAG1_RADIUS + B1LEASH_BAG1_HOME / 2u) / B1LEASH_BAG1_HOME;
    return radius < stock ? radius : stock;
}

/* Do not modify a partially initialized radius or an unknown finite override.
 * No latch update on refusal: retry after native 0x8002BA38 completes the zoom. */
static int b1leash_native_radius_ready(uint32_t ctl, uint32_t radius) {
    const uint32_t stage = psx_mod_read_word(B1LEASH_STAGE_PTR);
    if (stage < B1LEASH_RAM_LOW || stage > B1LEASH_RAM_END - 8u || (stage & 3u)) return 0;
    const uint32_t zoom = psx_mod_read_word(stage + B1LEASH_STAGE_ZOOM) & 0xFFFFu;
    const uint32_t raw = psx_mod_read_word(ctl + B1LEASH_RAW_RADIUS);
    if (!zoom || zoom > 0x7FFFu || raw > 0xFFFFu) return 0;
    return radius == ((raw * zoom) >> 8);
}

/* Slot 0..3 holds BAG1 dancer `dancer`. Returns the radius written, or 0 if unchanged. */
static uint32_t b1leash_apply(int slot, uint32_t dancer) {
    if (slot < 0 || slot > 3 || !dancer) return 0;
    const uint32_t ctl = B1LEASH_CTL + B1LEASH_CTL_STRIDE * (uint32_t)slot;
    if (psx_mod_read_word(ctl) != dancer) return 0;
    const uint32_t stock = psx_mod_read_word(ctl + B1LEASH_RADIUS);
    if (b1leash_dancer[slot] == dancer && b1leash_radius[slot] == stock) return 0;
    if (stock != B1LEASH_UNLIMITED && !b1leash_native_radius_ready(ctl, stock)) return 0;
    const int32_t home = (int32_t)psx_mod_read_word(ctl + B1LEASH_HOME_X);
    const uint32_t radius = b1leash_target(b1home_reference(ctl, home), stock);
    b1leash_dancer[slot] = dancer;
    b1leash_radius[slot] = radius;
    if (radius == stock) return 0;
    psx_mod_write_word(ctl + B1LEASH_RADIUS, radius);
    return radius;
}

static void b1leash_forget(void) {
    memset(b1leash_dancer, 0, sizeof b1leash_dancer);
    memset(b1leash_radius, 0, sizeof b1leash_radius);
}

#endif
