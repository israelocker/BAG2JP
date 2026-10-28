/* CD-quality songs for BAG2JP (SLPM-86219).
 *
 * Package bag2jp.localization.regional, option songs = "cd". Each in-game song is an XA channel
 * (BUST2_01 ch0-7, BUST2_02 ch0-3, BUST2_04 ch7; interleave 8). For every XA sector the emulator
 * decodes, cdrom.c hands this plugin the 44.1 kHz PCM before the CD decode volume
 * (cdrom_set_xa_host_filter). Sector k of a channel covers song frames [k*2352, (k+1)*2352)
 * (2016 samples at 37.8 kHz = 2352 at 44.1 kHz), so the plugin copies that span from
 * <music_hq>/<XA>_ch<N>.flac: the game's soundtrack CD re-aligned offline to the in-game edit
 * (tools in mods-src/bag2jp.localization.regional/tools/hq). Sound effects, music volume,
 * pauses and timing stay the game's own. Missing files leave the original XA audio. */
#include "mod_plugins.h"
#include "cdrom.h"

#include <SDL3/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>

/* dr_flac's implementation is already linked from libchdr (built with DR_FLAC_NO_STDIO),
 * so files are read through stdio callbacks here. */
#include <dr_libs/dr_flac.h>

static size_t hq_rd(void* u, void* out, size_t n) { return fread(out, 1, n, (FILE*)u); }
static drflac_bool32 hq_sk(void* u, int off, drflac_seek_origin o) {
    int w = o == DRFLAC_SEEK_SET ? SEEK_SET : o == DRFLAC_SEEK_END ? SEEK_END : SEEK_CUR;
    return fseek((FILE*)u, off, w) == 0;
}
static drflac_bool32 hq_tl(void* u, drflac_int64* c) { long p = ftell((FILE*)u); if (p < 0) return 0; *c = p; return 1; }
static FILE* hq_fp;

#define HQ_XA_FILES 3
#define HQ_FRAMES_PER_SECTOR 2352u
static const char* const hq_xa_name[HQ_XA_FILES] = { "BUST2_01", "BUST2_02", "BUST2_04" };
static const uint8_t hq_xa_channels[HQ_XA_FILES] = { 0xFF, 0x0F, 0x80 };  /* songs per file */
static uint32_t hq_lba[HQ_XA_FILES], hq_end[HQ_XA_FILES];
static char hq_dir[1024];
static int hq_active;

static drflac* hq_flac;            /* current song */
static int hq_cur_file = -1, hq_cur_ch = -1;
static uint64_t hq_cursor;
static int16_t hq_tmp[9408 * 2];
static unsigned char hq_missing[HQ_XA_FILES][8];

static FILE* hq_logf;
static void hq_log(const char* fmt, ...) {
    if (!hq_logf) {
        const char* base = SDL_GetBasePath(); char p[1024];
        snprintf(p, sizeof p, "%sbag2jp_hq_songs.log", base ? base : "");
        hq_logf = fopen(p, "w"); if (!hq_logf) return;
    }
    va_list ap; va_start(ap, fmt); vfprintf(hq_logf, fmt, ap); va_end(ap);
    fputc('\n', hq_logf); fflush(hq_logf);
}

static int hq_open(int f, int ch) {
    if (hq_flac && hq_cur_file == f && hq_cur_ch == ch) return 1;
    if (hq_flac) { drflac_close(hq_flac); hq_flac = NULL; }
    if (hq_fp) { fclose(hq_fp); hq_fp = NULL; }
    hq_cur_file = f; hq_cur_ch = ch; hq_cursor = 0;
    if (hq_missing[f][ch]) return 0;
    char p[1200];
    snprintf(p, sizeof p, "%s/%s_ch%d.flac", hq_dir, hq_xa_name[f], ch);
    hq_fp = fopen(p, "rb");
    hq_flac = hq_fp ? drflac_open(hq_rd, hq_sk, hq_tl, hq_fp, NULL) : NULL;
    if (!hq_flac || hq_flac->sampleRate != 44100 || hq_flac->channels != 2) {
        if (hq_flac) { drflac_close(hq_flac); hq_flac = NULL; }
        if (hq_fp) { fclose(hq_fp); hq_fp = NULL; }
        hq_missing[f][ch] = 1; hq_log("missing or unsupported: %s", p); return 0;
    }
    hq_log("song %s ch%d", hq_xa_name[f], ch);
    return 1;
}

static void hq_filter(int lba, int file, int channel, int16_t* pcm, int frames) {
    (void)file;
    if (!hq_active || lba < 0 || frames <= 0 || frames > 9408) return;
    for (int f = 0; f < HQ_XA_FILES; ++f) {
        if ((uint32_t)lba < hq_lba[f] || (uint32_t)lba >= hq_end[f]) continue;
        const uint32_t rel = (uint32_t)lba - hq_lba[f];
        const int ch = (int)(rel & 7u);
        if (ch != channel || !(hq_xa_channels[f] & (1u << ch))) return;
        if (!hq_open(f, ch)) return;
        const uint64_t pos = (uint64_t)(rel >> 3) * HQ_FRAMES_PER_SECTOR;
        const uint64_t t0 = SDL_GetPerformanceCounter();
        if (hq_cursor > pos + 4 || pos > hq_cursor + 4) {       /* jump (restart/seek) */
            const uint64_t from = hq_cursor;
            if (!drflac_seek_to_pcm_frame(hq_flac, pos)) { hq_log("seek FAILED to sector %u", rel >> 3); return; }
            hq_cursor = pos;
            hq_log("jump sector %llu -> %u (%+.3f s)", (unsigned long long)(from / HQ_FRAMES_PER_SECTOR), rel >> 3,
                   ((double)pos - (double)from) / 44100.0);
        }
        const drflac_uint64 got = drflac_read_pcm_frames_s16(hq_flac, (drflac_uint64)frames, hq_tmp);
        hq_cursor += got;
        const double ms = (double)(SDL_GetPerformanceCounter() - t0) * 1000.0 / (double)SDL_GetPerformanceFrequency();
        if (ms > 4.0 || got != (drflac_uint64)frames)
            hq_log("sector %u: %.1f ms, got %llu/%d", rel >> 3, ms, (unsigned long long)got, frames);
        if (got) memcpy(pcm, hq_tmp, (size_t)got * 4u);
        return;
    }
}

static void bag2jp_hq_songs_activate(void) {
    char v[32] = {0};
    hq_active = 0;
    cdrom_set_xa_host_filter(NULL);
    if (psx_mod_current_option_value("songs", v, sizeof v) <= 0 || strcmp(v, "cd") != 0) return;
    if (psx_mod_current_resource_path("music_hq", hq_dir, sizeof hq_dir) <= 0) {
        hq_log("songs=cd but no music_hq folder"); return;
    }
    int ok = 0;
    for (int f = 0; f < HQ_XA_FILES; ++f) {
        char path[32]; uint32_t lba = 0, size = 0;
        snprintf(path, sizeof path, "XA/%s.XA", hq_xa_name[f]);
        if (psx_mod_disc_file_extent(path, &lba, &size) && lba && size) {
            hq_lba[f] = lba; hq_end[f] = lba + size / 2048u; ok++;
        }
    }
    memset(hq_missing, 0, sizeof hq_missing);
    if (hq_flac) { drflac_close(hq_flac); hq_flac = NULL; }
    hq_cur_file = hq_cur_ch = -1;
    hq_active = ok == HQ_XA_FILES;
    hq_log("activate: dir '%s', xa extents %d/%d -> %s", hq_dir, ok, HQ_XA_FILES, hq_active ? "on" : "off");
    if (hq_active) cdrom_set_xa_host_filter(hq_filter);
}

PSX_MOD_CONSTRUCTOR(bag2jp_register_hq_songs) {
    (void)psx_mod_register_activation_plugin("bag2jp.hq_songs", bag2jp_hq_songs_activate);
}
