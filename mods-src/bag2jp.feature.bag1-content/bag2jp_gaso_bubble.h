/* Presentation-aware screen radii for custom (non-GTE) bubble packets. */
#ifndef BAG2JP_GASO_BUBBLE_H
#define BAG2JP_GASO_BUBBLE_H

#include <stdint.h>

#define GASO_BUBBLE_SCREEN_MIN 2
#define GASO_BUBBLE_SCREEN_MAX 96

static inline int gaso_bubble_screen_radii(int32_t radius, int32_t h, int32_t z,
                                          int32_t *rx, int32_t *ry) {
    if (!rx || !ry || radius <= 0 || h <= 0 || z <= 0) return 0;
    *rx = *ry = 0;
#if defined(PSX_MOD_DISPLAY_PIXEL_ASPECT)
    uint32_t pixel_num = 0, pixel_den = 0;
    if (!psx_mod_display_pixel_aspect(&pixel_num, &pixel_den) ||
        !pixel_num || !pixel_den) return 0;
    int64_t y = ((int64_t)radius * h) / z;
    if (y < GASO_BUBBLE_SCREEN_MIN || y > GASO_BUBBLE_SCREEN_MAX) return 0;
    /* Pixel width/height comes from the actual presentation, not actor scale
     * or strike_project's 0.85 world-X adjustment. Check y before multiplying
     * by the uint32 denominator so an extreme aspect cannot overflow. */
    int64_t x = y * pixel_den / pixel_num;
    if (x < GASO_BUBBLE_SCREEN_MIN || x > GASO_BUBBLE_SCREEN_MAX) return 0;
    *rx = (int32_t)x;
    *ry = (int32_t)y;
    return 1;
#else
    /* Older framework: no verified presentation geometry, so skip bubbles
     * rather than silently assume 16:9. The tank itself still renders. */
    return 0;
#endif
}

#endif
