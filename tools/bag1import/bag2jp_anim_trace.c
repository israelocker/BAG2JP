/* Animation trace (debug only, env BAG2JP_ANIM_TRACE=1): logs each dancer's current model anim index
 * (dancer + 0x154C), the last motion request code (0x8005CF22 + p*0x24) and the match phase
 * (0x8005D3D8/DC/E0, fever type 0x8005E6C0) to bag2jp_anim_trace.log whenever one changes.
 * Env BAG2JP_RAM_DUMP=n writes main RAM (2 MB) at trace frame n.
 * Env BAG2JP_CPU_SKILL=n keeps the CPU skill byte at n (n >= 140: the CPU attacks whenever it can).
 * Used to map BAG2 anim slots to game states for the BAG1 character import. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <SDL3/SDL.h>
#include "mod_plugins.h"

static FILE* s_log;
static int s_on = -1;
static int s_skill = -1;
static long s_dump_at = -1;  /* BAG2JP_RAM_DUMP=frame: write main RAM (2 MB) to bag2jp_ram_<frame>.bin */   /* BAG2JP_CPU_SKILL=n forces the CPU skill byte 0x8005E661 (test attacks) */

static void at_vblank(void) {
    static uint32_t frame, last[16];
    if (s_on < 0) {
        const char* e = getenv("BAG2JP_ANIM_TRACE"); s_on = (e && *e == '1');
        if (s_on) {
            const char* b = SDL_GetBasePath(); char p[1024];
            snprintf(p, sizeof p, "%sbag2jp_anim_trace.log", b ? b : "");
            s_log = fopen(p, "w");
            if (!s_log) s_on = 0;
        }
    }
    if (s_skill == -1) { const char* k = getenv("BAG2JP_CPU_SKILL"); s_skill = (k && *k) ? atoi(k) : -2; }
    if (s_skill >= 0 && psx_mod_read_byte(0x8005E661u) != (uint32_t)s_skill) psx_mod_write_byte(0x8005E661u, (uint8_t)s_skill);
    if (s_dump_at == -1) { const char* k = getenv("BAG2JP_RAM_DUMP"); s_dump_at = (k && *k) ? atol(k) : -2; }
    if (!s_on) return;
    ++frame;
    if (s_dump_at > 0 && frame == (uint32_t)s_dump_at) {
        const char* b = SDL_GetBasePath(); char p[1024];
        snprintf(p, sizeof p, "%sbag2jp_ram_%u.bin", b ? b : "", frame);
        FILE* f = fopen(p, "wb");
        if (f) {
            for (uint32_t a = 0x80000000u; a < 0x80200000u; a += 4) { uint32_t w = psx_mod_read_word(a); fwrite(&w, 4, 1, f); }
            fclose(f);
        }
    }
    uint32_t cur[16] = {0};
    for (uint32_t p = 0; p < 2; ++p) {
        const uint32_t d = psx_mod_read_word(0x8005F808u + p * 8u);
        cur[p * 4 + 0] = d;
        if (d >= 0x80000000u && d < 0x80800000u) {
            cur[p * 4 + 1] = psx_mod_read_byte(d + 4u);
            cur[p * 4 + 2] = psx_mod_read_word(d + 0x154Cu);
        }
        cur[p * 4 + 3] = psx_mod_read_half(0x8005CF22u + p * 0x24u);
    }
    cur[8] = psx_mod_read_word(0x8005D3D8u); cur[9] = psx_mod_read_word(0x8005D3DCu);
    cur[10] = psx_mod_read_word(0x8005D3E0u); cur[11] = psx_mod_read_byte(0x8005E6C0u);
    cur[12] = psx_mod_read_word(0x8005D2C4u);
    int changed = 0;
    for (int i = 0; i < 13; ++i) if (cur[i] != last[i]) changed = 1;
    if (!changed) return;
    fprintf(s_log, "f%06u mode%u phase %u/%u/%u fever%u | P1 ch%u anim%u req%u | P2 ch%u anim%u req%u\n",
            frame, cur[12], cur[8], cur[9], cur[10], cur[11], cur[1], cur[2], cur[3], cur[5], cur[6], cur[7]);
    fflush(s_log);
    for (int i = 0; i < 16; ++i) last[i] = cur[i];
}

PSX_MOD_CONSTRUCTOR(bag2jp_register_anim_trace) {
    (void)psx_mod_register_vblank_plugin("bag2jp.anim_trace", at_vblank);
}
