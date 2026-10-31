/* Animation trace (debug only, env BAG2JP_ANIM_TRACE=1): logs each dancer's current model anim index
 * (dancer + 0x154C), the last motion request code (0x8005CF22 + p*0x24) and the match phase
 * (0x8005D3D8/DC/E0, fever type 0x8005E6C0) to bag2jp_anim_trace.log whenever one changes.
 * Env BAG2JP_TEST_DANCE_VIEW_CHAR=0..13 temporarily enables that character in Dance View
 * (requires BAG2JP_ANIM_TRACE=1; use isolated test cards, never save test unlocks).
 * Env BAG2JP_RAM_DUMP=n writes main RAM (2 MB) at trace frame n.
 * Env BAG2JP_CPU_SKILL=n keeps the CPU skill byte at n (n >= 140: the CPU attacks whenever it can).
 * Env BAG2JP_AUDIO_DUMP=1 records the final audio mix (44.1 kHz stereo, after XA/CD/SPU mixing and
 * the other PCM plugins) to bag2jp_audio.wav, plus bag2jp_audio_sync.log ("frame sample" per vblank,
 * same frame numbering as the trace / watch logs) so sounds can be located against game events.
 * With the trace on, bag2jp_frame.txt holds the current frame and phase (rewritten every 6 frames).
 * Used to map BAG2 anim slots to game states for the BAG1 character import. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <SDL3/SDL.h>
#include "mod_plugins.h"

static FILE* s_log;
static int s_on = -1;
static int s_skill = -1;
static long s_dump_at = -1;
/* BAG2JP_WATCH=addr:size,... (hex addr, size 1/2/4): logs those RAM values to bag2jp_watch.log on change */
static int s_nwatch = -1; static uint32_t s_wa[16], s_ws[16], s_wv[16]; static FILE* s_wlog;  /* BAG2JP_RAM_DUMP=frame: write main RAM (2 MB) to bag2jp_ram_<frame>.bin */   /* BAG2JP_CPU_SKILL=n forces the CPU skill byte 0x8005E661 (test attacks) */

/* ---- audio recorder ---- */
static int s_audio = -1; static FILE* s_wav; static FILE* s_async;
static volatile uint64_t s_samples; static uint64_t s_hdr_at;
static void wav_header(FILE* f, uint64_t frames) {
    const uint32_t data = (uint32_t)(frames * 4u > 0xFFFFFFF0u ? 0xFFFFFFF0u : frames * 4u);
    uint8_t h[44] = {'R','I','F','F',0,0,0,0,'W','A','V','E','f','m','t',' ',16,0,0,0,1,0,2,0,
                     0x44,0xAC,0,0, 0x10,0xB1,2,0, 4,0,16,0,'d','a','t','a',0,0,0,0};
    const uint32_t riff = data + 36;
    for (int i = 0; i < 4; ++i) { h[4 + i] = (uint8_t)(riff >> (8 * i)); h[40 + i] = (uint8_t)(data >> (8 * i)); }
    long pos = ftell(f); fseek(f, 0, SEEK_SET); fwrite(h, 1, 44, f); fseek(f, pos, SEEK_SET);
}
static void at_pcm(int16_t* stereo, uint32_t frames) {
    if (!s_wav || !frames) return;
    fwrite(stereo, 4, frames, s_wav);
    s_samples += frames;
    if (s_samples - s_hdr_at >= 44100u) { wav_header(s_wav, s_samples); fflush(s_wav); s_hdr_at = s_samples; }
}
static void audio_vblank(void) {
    static uint32_t af;
    if (s_audio < 0) {
        const char* e = getenv("BAG2JP_AUDIO_DUMP"); s_audio = (e && *e == '1');
        if (s_audio) {
            const char* b = SDL_GetBasePath(); char p[1024];
            snprintf(p, sizeof p, "%sbag2jp_audio_sync.log", b ? b : ""); s_async = fopen(p, "w");
            snprintf(p, sizeof p, "%sbag2jp_audio.wav", b ? b : ""); s_wav = fopen(p, "wb");
            if (s_wav) wav_header(s_wav, 0); else s_audio = 0;
        }
    }
    ++af;
    if (s_async) { fprintf(s_async, "%u %llu\n", af, (unsigned long long)s_samples); if ((af & 63) == 0) fflush(s_async); }
}

static void at_vblank(void) {
    static uint32_t frame, last[16];
    audio_vblank();
    if (s_on < 0) {
        const char* e = getenv("BAG2JP_ANIM_TRACE"); s_on = (e && *e == '1');
        if (s_on) {
            const char* b = SDL_GetBasePath(); char p[1024];
            snprintf(p, sizeof p, "%sbag2jp_anim_trace.log", b ? b : "");
            s_log = fopen(p, "w");
            if (!s_log) s_on = 0;
        }
    }
    /* Test-only native viewer access; never active during a normal launch. */
    static int view_char = -2;
    if (view_char == -2) {
        const char* value = getenv("BAG2JP_TEST_DANCE_VIEW_CHAR"); char* end = NULL;
        long parsed = value && *value ? strtol(value, &end, 10) : -1;
        view_char = (value && *value && end && !*end && parsed >= 0 && parsed < 14) ? (int)parsed : -1;
    }
    if (s_on && view_char >= 0 && psx_mod_read_word(0x8004E2D8u) == 0x54535542u &&
        psx_mod_read_word(0x8004E2DCu) == 0x4D5F415Fu &&
        psx_mod_read_byte(0x8004E2F7u + (uint32_t)view_char) == 0)
        psx_mod_write_byte(0x8004E2F7u + (uint32_t)view_char, 1);
    if (s_skill == -1) { const char* k = getenv("BAG2JP_CPU_SKILL"); s_skill = (k && *k) ? atoi(k) : -2; }
    if (s_skill >= 0 && psx_mod_read_byte(0x8005E661u) != (uint32_t)s_skill) psx_mod_write_byte(0x8005E661u, (uint8_t)s_skill);
    if (s_dump_at == -1) { const char* k = getenv("BAG2JP_RAM_DUMP"); s_dump_at = (k && *k) ? atol(k) : -2; }
    if (s_nwatch < 0) {
        s_nwatch = 0; const char* w = getenv("BAG2JP_WATCH");
        while (w && *w && s_nwatch < 16) {
            char* e; s_wa[s_nwatch] = (uint32_t)strtoul(w, &e, 16); s_ws[s_nwatch] = 4;
            if (*e == ':') s_ws[s_nwatch] = (uint32_t)strtoul(e + 1, &e, 10);
            s_wv[s_nwatch] = 0xDEADBEEFu; ++s_nwatch; w = (*e == ',') ? e + 1 : NULL;
        }
        if (s_nwatch) { const char* b = SDL_GetBasePath(); char p[1024]; snprintf(p, sizeof p, "%sbag2jp_watch.log", b ? b : ""); s_wlog = fopen(p, "w"); }
    }
    if (s_wlog) {
        static uint32_t wf; ++wf; int ch = 0; uint32_t v[16];
        for (int i = 0; i < s_nwatch; ++i) {
            v[i] = s_ws[i] == 1 ? psx_mod_read_byte(s_wa[i]) : s_ws[i] == 2 ? psx_mod_read_half(s_wa[i]) : psx_mod_read_word(s_wa[i]);
            if (v[i] != s_wv[i]) ch = 1;
        }
        if (ch) {
            fprintf(s_wlog, "f%06u", wf);
            for (int i = 0; i < s_nwatch; ++i) { fprintf(s_wlog, " %08X=%X", s_wa[i], v[i]); s_wv[i] = v[i]; }
            fputc('\n', s_wlog); fflush(s_wlog);
        }
    }
    if (!s_on) return;
    ++frame;
    {   /* bag2jp_frame.txt: "frame phase a/b/c", every 6 frames, for scripted frame-exact screenshots */
        static FILE* ff;
        if (!ff) { const char* b = SDL_GetBasePath(); char p[1024]; snprintf(p, sizeof p, "%sbag2jp_frame.txt", b ? b : ""); ff = fopen(p, "w"); }
        if (ff && frame % 6 == 0) {
            rewind(ff);
            fprintf(ff, "%07u %u/%u/%u          \n", frame, psx_mod_read_word(0x8005D3D8u), psx_mod_read_word(0x8005D3DCu), psx_mod_read_word(0x8005D3E0u));
            fflush(ff);
        }
    }
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
    (void)psx_mod_register_pcm_plugin("bag2jp.anim_trace", at_pcm);
}
