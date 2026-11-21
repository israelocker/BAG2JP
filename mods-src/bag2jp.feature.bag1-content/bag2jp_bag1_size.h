#ifndef BAG2JP_BAG1_SIZE_H
#define BAG2JP_BAG1_SIZE_H

#include <stdint.h>

/* Largest in-place growth a disc_user mod may give a BAG2 entry that has a BAG1 variant.
 * Keep >= the max swap_mod GROWTH_BUDGET of those characters (Strike 4388 B). */
#define B1V_MAX_GROWTH 4388u

/* BAG2 size to restore for an entry whose disc table reports `seen`: in-place growth
 * within the budget is kept; anything else falls back to the compiled stock size.
 * Pure so host tests (tools/move_viewer/tests/test_bag1_size.py) exercise the real code. */
static inline uint32_t b1v_accept_size(uint32_t seen, uint32_t stock) {
    return seen >= stock && seen - stock <= B1V_MAX_GROWTH ? seen : stock;
}

#endif
