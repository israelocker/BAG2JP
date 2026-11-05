/* Opt-in diagnostic VRAM snapshot (BAG2JP_VRAM_DUMP=frame[,frame...]).
 * Reads the runtime's CPU-side VRAM copy, which holds every LoadImage upload
 * (CLUTs, texture pages). It does not read GL framebuffer-only rendering. */
#ifndef BAG2JP_VRAM_DUMP_H
#define BAG2JP_VRAM_DUMP_H

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define BAG2_VRAM_DUMP_MAX 8     /* frames accepted from the environment list */
#define BAG2_VRAM_W 1024         /* PSX VRAM width in 16-bit pixels */
#define BAG2_VRAM_H 512          /* PSX VRAM height */

void gr_vram_transfer_out(int x, int y, int w, int h, uint16_t *dst);

/* Parse "f1,f2,...": stops at the first invalid or zero entry. */
static int bag2_vram_dump_parse(const char *spec, uint32_t frames[BAG2_VRAM_DUMP_MAX]) {
    int count = 0;
    while (spec && *spec && count < BAG2_VRAM_DUMP_MAX) {
        char *end = NULL;
        unsigned long value = strtoul(spec, &end, 10);
        if (end == spec || value == 0 || (*end && *end != ',')) break;
        frames[count++] = (uint32_t)value;
        spec = *end ? end + 1 : end;
    }
    return count;
}

/* Write raw little-endian 1024x512 16-bit VRAM; returns 1 on success. */
static int bag2_vram_dump_write(FILE *file) {
    if (!file) return 0;
    uint16_t *pixels = (uint16_t *)malloc((size_t)BAG2_VRAM_W * BAG2_VRAM_H * sizeof(uint16_t));
    if (!pixels) return 0;
    gr_vram_transfer_out(0, 0, BAG2_VRAM_W, BAG2_VRAM_H, pixels);
    size_t written = 0;
    for (size_t i = 0; i < (size_t)BAG2_VRAM_W * BAG2_VRAM_H; ++i) {
        uint8_t bytes[2] = {(uint8_t)(pixels[i] & 0xFF), (uint8_t)(pixels[i] >> 8)};
        written += fwrite(bytes, 1, 2, file);
    }
    free(pixels);
    return written == (size_t)BAG2_VRAM_W * BAG2_VRAM_H * 2;
}

#endif
