/* BAG1 stage support (package bag2jp.feature.bag1-content, feature "bag1-stage").
 *
 * The BAG1 Heat stage program is ported to a BAG2 stage DBI by tools/bag1import/port_bag1_stage.py.
 * It reads a few BAG1 game variables that BAG2 does not have; the port points them at a shim block
 * inside the DBI image (0x801E0100: 'B1ST', beat flags u32, score level u8, previous level u8) and
 * this plugin fills it once per frame while that DBI is resident and stage id 0 is loaded:
 *   beat flags (BAG1 0x80068704): bit 0 = a beat happened this frame (BAG2 beat counter 0x8005E2D0
 *   changed), bit 4 = it is the first beat of a bar (= bar start 0x8005E684), bit 6 = song over
 *   (beats left 0x8005E658 reached 0);
 *   score level (BAG1 0x80068714): 1 from 15000 points, 2 from 45000 (best of 0x8005E6F8/FC);
 *   previous level (BAG1 0x800979D0, set by BAG1 after each stage update): last frame's level.
 *
 * Song: the ported stage keeps BAG2's song slot (stage 0 = XA/BUST2_01.XA channel 0) with a BAG1
 * chart in the DBI tail; the audio is swapped here through the XA host filter (wrapping whatever
 * filter is installed, e.g. bag2jp.hq_songs): every sector of that channel gets the same span of
 * <bag1_music>/<song>_<audio>.flac (sector k = frames k*2352 at 44.1 kHz, silence past the end).
 * audio option: "cd" = soundtrack CD re-aligned to the BAG1 in-game edit, "game" = BAG1's own XA.
 * The game stops a song when its play time reaches the main exe table 0x800555A8[song] (u16 s); BAG2
 * Heat's slot says 152 s, BAG1 2Bad (dance ends 123 s) is faded out by 129 s, so while the BAG1 stage
 * is loaded that entry is set to 129 (restored afterwards). Otherwise the result/fever phase waits
 * ~25 s of silence for BAG2's length (tools/bag1import/song_ending.py makes the matching fade). */
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <SDL3/SDL.h>
#include "mod_plugins.h"
#include "cdrom.h"
#include <dr_libs/dr_flac.h>

#define B1S_SHIM   0x801E0100u
#define B1S_MAGIC  0x54533142u   /* 'B1ST' */

static void b1s_vblank(void) {
    static uint16_t last_beat = 0xFFFF;
    if (psx_mod_read_word(B1S_SHIM) != B1S_MAGIC) { last_beat = 0xFFFF; return; }
    const uint32_t stage = psx_mod_read_word(0x80089200u);
    if (stage < 0x80000000u || stage >= 0x80800000u || psx_mod_read_byte(stage) != 0) return;
    const uint16_t beat = psx_mod_read_half(0x8005E2D0u);
    uint32_t flags = 0;
    if (last_beat != 0xFFFF && beat != last_beat) {
        flags |= 1u;
        if (beat == psx_mod_read_half(0x8005E684u)) flags |= 0x10u;
    }
    if (beat != 0 && psx_mod_read_half(0x8005E658u) == 0) flags |= 0x40u;
    last_beat = beat;
    const int32_t s0 = (int32_t)psx_mod_read_word(0x8005E6F8u), s1 = (int32_t)psx_mod_read_word(0x8005E6FCu);
    const int32_t best = s0 > s1 ? s0 : s1;
    const uint8_t level = best >= 45000 ? 2 : best >= 15000 ? 1 : 0;
    psx_mod_write_word(B1S_SHIM + 4u, flags);
    psx_mod_write_byte(B1S_SHIM + 9u, psx_mod_read_byte(B1S_SHIM + 8u));
    psx_mod_write_byte(B1S_SHIM + 8u, level);
}

/* ---- song audio ---- */
static FILE* b1m_logf;
static void b1m_log(const char* fmt, ...) {
    if (!b1m_logf) {
        const char* base = SDL_GetBasePath(); char p[1024];
        snprintf(p, sizeof p, "%sbag2jp_bag1_content.log", base ? base : "");
        b1m_logf = fopen(p, "w"); if (!b1m_logf) return;
    }
    va_list ap; va_start(ap, fmt); vfprintf(b1m_logf, fmt, ap); va_end(ap);
    fputc('\n', b1m_logf); fflush(b1m_logf);
}
static size_t b1m_rd(void* u, void* out, size_t n) { return fread(out, 1, n, (FILE*)u); }
static drflac_bool32 b1m_sk(void* u, int off, drflac_seek_origin o) {
    int w = o == DRFLAC_SEEK_SET ? SEEK_SET : o == DRFLAC_SEEK_END ? SEEK_END : SEEK_CUR;
    return fseek((FILE*)u, off, w) == 0;
}
static drflac_bool32 b1m_tl(void* u, drflac_int64* c) { long p = ftell((FILE*)u); if (p < 0) return 0; *c = p; return 1; }

#define B1M_FRAMES_PER_SECTOR 2352u
static char b1m_dir[1024], b1m_audio[16] = "cd";
static uint32_t b1m_lba, b1m_end;          /* XA/BUST2_01.XA extent */
static FILE* b1m_fp; static drflac* b1m_flac; static int b1m_failed;
static uint64_t b1m_cursor;
static int16_t b1m_tmp[9408 * 2];
static CdromXaHostFilter b1m_prev;

static int b1m_stage_active(void) {
    if (psx_mod_read_word(B1S_SHIM) != B1S_MAGIC) return 0;
    const uint32_t stage = psx_mod_read_word(0x80089200u);
    return stage >= 0x80000000u && stage < 0x80800000u && psx_mod_read_byte(stage) == 0;
}
static int b1m_open(void) {
    if (b1m_flac) return 1;
    if (b1m_failed || !b1m_dir[0]) return 0;
    char p[1200];
    snprintf(p, sizeof p, "%s/heat_2bad_%s.flac", b1m_dir, b1m_audio);
    b1m_fp = fopen(p, "rb");
    b1m_flac = b1m_fp ? drflac_open(b1m_rd, b1m_sk, b1m_tl, b1m_fp, NULL) : NULL;
    if (!b1m_flac || b1m_flac->sampleRate != 44100 || b1m_flac->channels != 2) {
        if (b1m_flac) { drflac_close(b1m_flac); b1m_flac = NULL; }
        if (b1m_fp) { fclose(b1m_fp); b1m_fp = NULL; }
        b1m_failed = 1; b1m_log("missing or unsupported: %s", p); return 0;
    }
    b1m_cursor = 0; b1m_log("song %s", p); return 1;
}
static void b1m_filter(int lba, int file, int channel, int16_t* pcm, int frames) {
    if (b1m_prev) b1m_prev(lba, file, channel, pcm, frames);
    if (lba < 0 || frames <= 0 || frames > 9408 || (uint32_t)lba < b1m_lba || (uint32_t)lba >= b1m_end) return;
    const uint32_t rel = (uint32_t)lba - b1m_lba;
    if ((rel & 7u) != 0 || channel != 0 || !b1m_stage_active() || !b1m_open()) return;
    const uint64_t pos = (uint64_t)(rel >> 3) * B1M_FRAMES_PER_SECTOR;
    if (b1m_cursor != pos) {
        if (!drflac_seek_to_pcm_frame(b1m_flac, pos)) { memset(pcm, 0, (size_t)frames * 4u); b1m_cursor = ~0ull; return; }
        b1m_cursor = pos;
    }
    const drflac_uint64 got = drflac_read_pcm_frames_s16(b1m_flac, (drflac_uint64)frames, b1m_tmp);
    b1m_cursor += got;
    memcpy(pcm, b1m_tmp, (size_t)got * 4u);
    if (got < (drflac_uint64)frames) memset(pcm + got * 2u, 0, (size_t)(frames - (int)got) * 4u);
}
static void b1m_activate(void) {
    if (b1m_flac) { drflac_close(b1m_flac); b1m_flac = NULL; }
    if (b1m_fp) { fclose(b1m_fp); b1m_fp = NULL; }
    b1m_failed = 0; b1m_dir[0] = 0;
    char v[16] = {0};
    if (psx_mod_current_option_value("bag1_song_audio", v, sizeof v) > 0) snprintf(b1m_audio, sizeof b1m_audio, "%s", v);
    if (psx_mod_current_resource_path("bag1_music", b1m_dir, sizeof b1m_dir) <= 0) b1m_dir[0] = 0;
    uint32_t size = 0;
    if (!psx_mod_disc_file_extent("XA/BUST2_01.XA", &b1m_lba, &size) || !size) b1m_lba = b1m_end = 0;
    else b1m_end = b1m_lba + size / 2048u;
    b1m_log("activate: dir '%s', audio %s, BUST2_01 lba %u..%u", b1m_dir, b1m_audio, b1m_lba, b1m_end);
}

#define B1M_SONG_LEN_TABLE 0x800555A8u   /* u16 seconds per XA song; Heat's BAG2 slot = entry 0 */
#define B1M_HEAT_SONG_LEN  129u
static int b1m_len_saved = -1;
static void b1m_song_length(void) {
    const uint32_t cur = psx_mod_read_half(B1M_SONG_LEN_TABLE);
    if (b1m_stage_active()) {
        if (cur != B1M_HEAT_SONG_LEN) {
            if (b1m_len_saved < 0) b1m_len_saved = (int)cur;
            psx_mod_write_half(B1M_SONG_LEN_TABLE, B1M_HEAT_SONG_LEN);
            b1m_log("song length %u -> %u s", cur, B1M_HEAT_SONG_LEN);
        }
    } else if (b1m_len_saved >= 0) {
        if (cur == B1M_HEAT_SONG_LEN) psx_mod_write_half(B1M_SONG_LEN_TABLE, (uint16_t)b1m_len_saved);
        b1m_len_saved = -1;
    }
}

static void b1s_vblank_all(void) {
    b1s_vblank();
    b1m_song_length();
    if (g_cdrom_xa_host_filter != b1m_filter) {         /* (re)wrap after other plugins set theirs */
        b1m_prev = g_cdrom_xa_host_filter;
        cdrom_set_xa_host_filter(b1m_filter);
    }
}

PSX_MOD_CONSTRUCTOR(bag2jp_register_bag1_stage) {
    (void)psx_mod_register_vblank_plugin("bag2jp.bag1_stage", b1s_vblank_all);
    (void)psx_mod_register_activation_plugin("bag2jp.bag1_stage", b1m_activate);
}
