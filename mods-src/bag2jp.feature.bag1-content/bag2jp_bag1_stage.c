/* BAG1 stage support (package bag2jp.feature.bag1-content, feature "bag1-stage").
 *
 * The BAG1 Heat stage program is ported to a BAG2 stage DBI by tools/bag1import/port_bag1_stage.py.
 * It reads a few BAG1 game variables that BAG2 does not have; the port points them at a shim block
 * inside the DBI image (0x801E0100: 'B1ST', beat flags u32, score level u8, previous level u8) and
 * this plugin fills it once per frame while that DBI is resident and stage id 0 or 1 is loaded, or
 * stage id 9 with the BAG1 Gas-O stage selected (it also zeroes that stage's fan at match start):
 *   beat flags (BAG1 0x80068704): bit 0 = a beat happened this frame (BAG2 beat counter 0x8005E2D0
 *   changed), bit 4 = it is the first beat of a bar (= bar start 0x8005E684), bit 6 = song over
 *   (beats left 0x8005E658 reached 0);
 *   score level (BAG1 0x80068714): 0/1/2 from the best score (see b1s_vblank);
 *   previous level (BAG1 0x800979D0): written by a helper in the DBI right after each stage update.
 *
 * Song: the ported stage keeps BAG2's song slot (stages 0/1 = XA/BUST2_01.XA channels 0/1) with a BAG1
 * chart in the DBI tail; the audio is swapped here through the XA host filter (wrapping whatever
 * filter is installed, e.g. bag2jp.hq_songs): every sector of that channel gets the same span of
 * <bag1_music>/<song>_<audio>.flac (sector k = frames k*2352 at 44.1 kHz, silence past the end).
 * Heat audio option: "cd" = soundtrack CD re-aligned to the BAG1 in-game edit, "game" = BAG1's own XA.
 * Strike always uses its game XA edit; its native JP duration is 129 s (u32 0x800553F4[1]).
 * The game stops a song when its play time reaches the main exe table 0x800555A8[song] (u16 s); BAG2
 * Heat's slot says 152 s, BAG1 2Bad (dance ends 123 s) is faded out by 129 s, so while the BAG1 stage
 * is loaded that entry is set to 129 (restored afterwards). Otherwise the result/fever phase waits
 * ~25 s of silence for BAG2's length (tools/bag1import/song_ending.py makes the matching fade). */
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <stdlib.h>
#include <time.h>
#include <SDL3/SDL.h>
#include "mod_plugins.h"
#include "cpu_state.h"
#include "cdrom.h"
#include <dr_libs/dr_flac.h>
#include "bag2jp_stage_visibility_test.h"

#define B1S_SHIM   0x801E0100u
#define B1S_MAGIC  0x54533142u   /* 'B1ST' */
#define B1S_ROOT_GAMEPLAY 0x13u

#define B1S_GASO_STAGE_ENTRY 197u

int bag2jp_bag1_entry_is_alt(unsigned entry);

/* Stage 9 (Gas-O vs Bi-O) runs the imported BAG1 stage only while DF2_ entry 197 points at
 * its BAG1 file (exact offset from bag2jp_bag1_alt_index.h, international or JP). */
static int b1s_is_gaso_bag1(void) {
    return bag2jp_bag1_entry_is_alt(B1S_GASO_STAGE_ENTRY);
}

static void b1s_vblank(void) {
    static uint16_t last_beat = 0xFFFF;
    const uint32_t root = psx_mod_read_word(0x8005D3D4u);
    if (root != B1S_ROOT_GAMEPLAY) { last_beat = 0xFFFF; return; }

    const uint32_t stage = psx_mod_read_word(0x80089200u);
    if (stage < 0x80000000u || stage >= 0x80800000u) return;
    const uint8_t stage_id = psx_mod_read_byte(stage);
    if (stage_id != 0 && stage_id != 1 && stage_id != 9) return;

    /* Stage 9 needs the imported BAG1 stage selected (entry 197 -> ALT) as well. */
    if (stage_id == 9 && !b1s_is_gaso_bag1()) { last_beat = 0xFFFF; return; }
    /* 'B1ST' comes from the ported DBI image itself (image offset 0x51F0), so this read
     * is the residency test. Never write the magic from the plugin: before the stage DBI
     * is loaded that address belongs to other game data, and corrupting it crashed the
     * emulated game right after the stage-select screen. */
    if (psx_mod_read_word(B1S_SHIM) != B1S_MAGIC) { last_beat = 0xFFFF; return; }

    const uint16_t beat = psx_mod_read_half(0x8005E2D0u);
    uint32_t flags = 0;
    if (last_beat == 0xFFFF) {
        /* New match start: reset score level and fan speed so the ventilation fan starts stationary */
        psx_mod_write_byte(B1S_SHIM + 8u, 0);
        psx_mod_write_byte(B1S_SHIM + 9u, 0);
        if (stage_id == 9) {
            psx_mod_write_half(0x801DECC0u, 0); /* stage fan angle */
            psx_mod_write_half(0x801DECC2u, 0); /* stage fan speed */
        }
    } else if (beat != last_beat) {
        flags |= 1u;
        if (beat == psx_mod_read_half(0x8005E684u)) flags |= 0x10u;
    }
    if (beat != 0 && psx_mod_read_half(0x8005E658u) == 0) flags |= 0x40u;
    last_beat = beat;
    /* BAG1 uses 15000/45000 on its own score scale (a BAG2 match ends around 25-30k, so 45000 would
     * never happen); BAG2's dance-level thresholds (0x8005141C: 4500/9300/14100/18900 x play beats
     * 0x8005E2E8 / 256) are used instead: level 1 from dance level 2, level 2 from dance level 4. */
    const int32_t s0 = (int32_t)psx_mod_read_word(0x8005E6F8u), s1 = (int32_t)psx_mod_read_word(0x8005E6FCu);
    const int32_t best = s0 > s1 ? s0 : s1;
    const int32_t beats = (int16_t)psx_mod_read_half(0x8005E2E8u);
    const int32_t t1 = 9300 * beats / 256, t2 = 18900 * beats / 256;
    uint8_t level = psx_mod_read_byte(B1S_SHIM + 8u);           /* never goes down, as in BAG1 */
    if (beats > 0) { if (best >= t2) level = 2; else if (best >= t1 && level < 1) level = 1; }
    psx_mod_write_word(B1S_SHIM + 4u, flags);
    psx_mod_write_byte(B1S_SHIM + 8u, level);   /* previous level (+9) is set by the DBI update helper */
}

/* ---- song audio ---- */
static void b1sv_experiment(void);
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
/* Opt-in stall diagnostic (BAG2JP_TEST_B1M_TIMING=1): logs FLAC seeks and slow
 * reads with the UTC wall time, to align them with recorder heartbeats. */
static int b1m_timing_on(void) {
    static int on = -1;
    if (on < 0) { const char* e = getenv("BAG2JP_TEST_B1M_TIMING"); on = e && !strcmp(e, "1"); }
    return on;
}
static double b1m_wall(void) {
    struct timespec ts;
    return timespec_get(&ts, TIME_UTC) ? (double)ts.tv_sec + ts.tv_nsec / 1e9 : 0.0;
}

#define B1M_FRAMES_PER_SECTOR 2352u
#define B1M_XA_FILES 2u
#define B1M_XA_CHANNELS 8u
#define B1M_MAX_FRAMES 9408
#define B1M_SECTOR_BYTES 2048u
static char b1m_dir[1024], b1m_audio[16] = "japanese";
static uint32_t b1m_lba[B1M_XA_FILES], b1m_end[B1M_XA_FILES];
static FILE* b1m_fp; static drflac* b1m_flac; static int b1m_failed;
static uint64_t b1m_cursor;
static int16_t b1m_tmp[B1M_MAX_FRAMES * 2];
static CdromXaHostFilter b1m_prev;

typedef struct {
    uint8_t stage, channel, length_index;
    uint16_t seconds;
    const char* name;
} B1MusicProfile;
/* Native stage id selects the BAG2 XA extent/channel. JP BAG1 durations
 * are from 0x800553F4; regional timing and Gas-O still need game acceptance. */
static const B1MusicProfile b1m_profiles[] = {
    {0, 0, 0, 129, "heat_2bad"},
    {1, 1, 1, 129, "strike"},
    {9, 1, 9, 150, "gaso"},
};
#define B1M_PROFILE_COUNT (sizeof b1m_profiles / sizeof b1m_profiles[0])
static const B1MusicProfile* b1m_loaded;

static const B1MusicProfile* b1m_stage_profile(void) {
    const uint32_t root = psx_mod_read_word(0x8005D3D4u);
    /* Dance View uses root 0x19 (mode 4) and Practice root 0x17 (mode 3), not the
     * match root 0x13. Retain all imported-stage guards so native music is not replaced. */
    const uint32_t mode = psx_mod_read_word(0x8005D2C4u);
    if (root != B1S_ROOT_GAMEPLAY && !(root == 0x19u && mode == 4u) &&
        !(root == 0x17u && mode == 3u)) return NULL;

    const uint32_t stage = psx_mod_read_word(0x80089200u);
    if (stage < 0x80000000u || stage >= 0x80800000u) return NULL;
    const uint8_t id = psx_mod_read_byte(stage);

    if (id == 9 && !b1s_is_gaso_bag1()) return NULL;
    /* Same residency test as b1s_vblank: the DBI image supplies the magic. */
    if (psx_mod_read_word(B1S_SHIM) != B1S_MAGIC) return NULL;

    for (unsigned i = 0; i < sizeof b1m_profiles / sizeof b1m_profiles[0]; ++i)
        if (b1m_profiles[i].stage == id) return &b1m_profiles[i];
    return NULL;
}
static int b1m_open(const B1MusicProfile* profile) {
    if (b1m_loaded != profile) {
        if (b1m_flac) { drflac_close(b1m_flac); b1m_flac = NULL; }
        if (b1m_fp) { fclose(b1m_fp); b1m_fp = NULL; }
        b1m_failed = 0;
        b1m_loaded = profile;
    }
    if (b1m_flac) return 1;
    if (b1m_failed || !b1m_dir[0]) return 0;
    char p[1200];
    snprintf(p, sizeof p, "%s/%s_%s.flac", b1m_dir, profile->name,
             b1m_audio);
    b1m_fp = fopen(p, "rb");
    b1m_flac = b1m_fp ? drflac_open(b1m_rd, b1m_sk, b1m_tl, b1m_fp, NULL) : NULL;
    if (!b1m_flac || b1m_flac->sampleRate != 44100 || b1m_flac->channels != 2) {
        if (b1m_flac) { drflac_close(b1m_flac); b1m_flac = NULL; }
        if (b1m_fp) { fclose(b1m_fp); b1m_fp = NULL; }
        b1m_failed = 1; b1m_log("missing or unsupported: %s", p); return 0;
    }
    b1m_cursor = 0; b1m_log("song %s", p); return 1;
}
static void b1m_trace_viewer_audio(int lba, int file, int channel) {
    /* Bounded opt-in observation only: never broaden the replacement guards. */
    static uint32_t seen[32];
    static unsigned count;
    const char* enabled = getenv("BAG2JP_TEST_VIEWER_AUDIO");
    if (!enabled || strcmp(enabled, "1") != 0 || count == 32 ||
        psx_mod_read_word(0x8005D2C4u) != 4) return;
    const B1MusicProfile* profile = b1m_stage_profile();
    const unsigned xa = profile ? profile->stage / B1M_XA_CHANNELS : 0u;
    if (xa >= B1M_XA_FILES) return;
    const uint32_t start = b1m_lba[xa], end = b1m_end[xa];
    const int in_extent = lba >= 0 && (uint32_t)lba >= start && (uint32_t)lba < end;
    const uint32_t rel = (uint32_t)lba - start;
    const uint32_t key = (profile ? (uint32_t)profile->stage + 1u : 0u) |
        ((uint32_t)in_extent << 8) | (((uint32_t)channel & 255u) << 16) |
        ((rel & 7u) << 24);
    for (unsigned i = 0; i < count; ++i) if (seen[i] == key) return;
    seen[count++] = key;
    const uint32_t model = psx_mod_read_word(0x80089200u);
    const int model_id = model >= 0x80000000u && model < 0x80800000u ? psx_mod_read_byte(model) : -1;
    b1m_log("viewer XA lba=%d file=%d channel=%d extent=%u..%u inside=%d sector_channel=%u profile=%d root=%x shim=%x model=%x model_id=%d",
        lba, file, channel, start, end, in_extent, rel & 7u,
        profile ? profile->stage : -1, psx_mod_read_word(0x8005D3D4u),
        psx_mod_read_word(B1S_SHIM), model, model_id);
}
static void b1m_filter(int lba, int file, int channel, int16_t* pcm, int frames) {
    if (b1m_prev) b1m_prev(lba, file, channel, pcm, frames);
    b1m_trace_viewer_audio(lba, file, channel);
    if (lba < 0 || frames <= 0 || frames > B1M_MAX_FRAMES) return;
    const B1MusicProfile* profile = b1m_stage_profile();
    if (!profile) return;
    const unsigned xa = profile->stage / B1M_XA_CHANNELS;
    if (xa >= B1M_XA_FILES || (uint32_t)lba < b1m_lba[xa] || (uint32_t)lba >= b1m_end[xa]) return;
    const uint32_t rel = (uint32_t)lba - b1m_lba[xa];
    if ((rel % B1M_XA_CHANNELS) != profile->channel || channel != profile->channel) return;
    const int timing = b1m_timing_on();
    const double t0 = timing ? b1m_wall() : 0.0;
    const uint64_t prev = b1m_cursor;
    const int opened = b1m_flac == NULL || b1m_loaded != profile;
    if (!b1m_open(profile)) return;
    const uint64_t pos = (uint64_t)(rel / B1M_XA_CHANNELS) * B1M_FRAMES_PER_SECTOR;
    if (b1m_cursor != pos) {
        if (!drflac_seek_to_pcm_frame(b1m_flac, pos)) {
            memset(pcm, 0, (size_t)frames * 4u); b1m_cursor = ~0ull;
            if (timing) b1m_log("timing wall=%.3f lba=%d pos=%llu seek failed ms=%.2f", t0, lba,
                                (unsigned long long)pos, (b1m_wall() - t0) * 1000.0);
            return;
        }
        b1m_cursor = pos;
    }
    const drflac_uint64 got = drflac_read_pcm_frames_s16(b1m_flac, (drflac_uint64)frames, b1m_tmp);
    b1m_cursor += got;
    memcpy(pcm, b1m_tmp, (size_t)got * 4u);
    if (got < (drflac_uint64)frames) memset(pcm + got * 2u, 0, (size_t)(frames - (int)got) * 4u);
    if (timing) {
        const double ms = (b1m_wall() - t0) * 1000.0;
        if (prev != pos || ms >= 5.0)
            b1m_log("timing wall=%.3f lba=%d pos=%llu prev=%llu open=%d frames=%d got=%llu ms=%.2f", t0, lba,
                    (unsigned long long)pos, (unsigned long long)prev, opened, frames,
                    (unsigned long long)got, ms);
    }
}
static void b1m_read_extents(void) {
    for (unsigned i = 0; i < B1M_XA_FILES; ++i) {
        char path[32]; uint32_t size = 0;
        b1m_lba[i] = b1m_end[i] = 0;
        snprintf(path, sizeof path, "XA/BUST2_%02u.XA", i + 1u);
        if (psx_mod_disc_file_extent(path, &b1m_lba[i], &size) && size &&
            b1m_lba[i] <= UINT32_MAX - size / B1M_SECTOR_BYTES)
            b1m_end[i] = b1m_lba[i] + size / B1M_SECTOR_BYTES;
        b1m_log("activate: %s lba %u..%u", path, b1m_lba[i], b1m_end[i]);
    }
}
static void b1m_activate(void) {
    if (b1m_flac) { drflac_close(b1m_flac); b1m_flac = NULL; }
    if (b1m_fp) { fclose(b1m_fp); b1m_fp = NULL; }
    b1m_failed = 0; b1m_dir[0] = 0; b1m_loaded = NULL;
    char v[16] = {0};
    snprintf(b1m_audio, sizeof b1m_audio, "%s", "japanese");
    if (psx_mod_option_value("bag2jp.localization.regional", "regional", "songs", v, sizeof v) > 0 &&
        (!strcmp(v, "japanese") || !strcmp(v, "international") || !strcmp(v, "cd")))
        snprintf(b1m_audio, sizeof b1m_audio, "%s", v);
    if (psx_mod_current_resource_path("bag1_music", b1m_dir, sizeof b1m_dir) <= 0) b1m_dir[0] = 0;
    b1m_read_extents();
    b1m_log("activate: dir '%s', audio %s", b1m_dir, b1m_audio);
}

#define B1M_SONG_LEN_TABLE 0x800555A8u   /* u16 seconds per XA song */
static uint16_t b1m_len_saved[B1M_PROFILE_COUNT];
static uint8_t b1m_len_valid[B1M_PROFILE_COUNT];
static void b1m_song_length(void) {
    const B1MusicProfile* active = b1m_stage_profile();
    for (unsigned i = 0; i < sizeof b1m_profiles / sizeof b1m_profiles[0]; ++i) {
        const B1MusicProfile* profile = &b1m_profiles[i];
        const uint32_t address = B1M_SONG_LEN_TABLE + 2u * profile->length_index;
        const uint16_t cur = psx_mod_read_half(address);
        if (active == profile) {
            if (cur != profile->seconds) {
                if (!b1m_len_valid[i]) { b1m_len_saved[i] = cur; b1m_len_valid[i] = 1; }
                psx_mod_write_half(address, profile->seconds);
                b1m_log("song %s length %u -> %u s", profile->name, cur, profile->seconds);
            }
        } else if (b1m_len_valid[i]) {
            if (cur == profile->seconds) psx_mod_write_half(address, (uint16_t)b1m_len_saved[i]);
            b1m_len_valid[i] = 0;
        }
    }
}

/* Song names for settings.toml [song_sync] per-song offsets. The seek happens before the
 * game stores the song index, so the index is derived from the XA file holding the target
 * LBA (BUST2_01/02.XA) and the Setfilter channel: song = file * 8 + channel. While an
 * imported BAG1 stage owns that song slot the name is bag1_<character>. */
static const char* const b1n_bag2[] = {
    "heat", "strike", "comet", "tsutomu", "kelly", "shorty", "pander", "kitty_n",
    "hiro", "bi_o", "capoeira", "robo_z", "columbo", "sushi_boy", "chichi_sally", "michael_doi",
};
static const char* b1n_song(int lba, int file, int channel) {
    (void)file;
    if (lba < 0 || channel < 0 || channel >= (int)B1M_XA_CHANNELS) return NULL;
    for (unsigned i = 0; i < B1M_XA_FILES; ++i) {
        if ((uint32_t)lba < b1m_lba[i] || (uint32_t)lba >= b1m_end[i]) continue;
        const unsigned song = i * B1M_XA_CHANNELS + (unsigned)channel;
        const B1MusicProfile* profile = b1m_stage_profile();
        if (profile && profile->stage / B1M_XA_CHANNELS == i && profile->channel == (unsigned)channel)
            return profile->stage == 0 ? "bag1_heat" : profile->stage == 1 ? "bag1_strike" : "bag1_gaso";
        return song < sizeof b1n_bag2 / sizeof b1n_bag2[0] ? b1n_bag2[song] : NULL;
    }
    return NULL;
}

static void b1s_vblank_all(void) {
    static int named;
    if (!named) { cdrom_set_xa_song_namer(b1n_song); named = 1; }
    b1s_vblank();
    b1m_song_length();
    b1sv_experiment();
    if (g_cdrom_xa_host_filter != b1m_filter) {         /* (re)wrap after other plugins set theirs */
        b1m_prev = g_cdrom_xa_host_filter;
        cdrom_set_xa_host_filter(b1m_filter);
    }
}

/* Opt-in experiment, not a shipping fix. Missing control file means baseline.
 * A running test can switch modes without restarting or reseeding its camera. */
#define B1SV_CONTROL_INTERVAL 15u
static void b1sv_experiment(void) {
    static int enabled = -1, requested, last_result;
    static unsigned poll;
    if (enabled < 0) {
        const char* value = getenv("BAG2JP_TEST_STAGE_VISIBILITY");
        enabled = value && strcmp(value, "1") == 0;
    }
    if (!enabled) return;
    if (poll++ % B1SV_CONTROL_INTERVAL == 0) {
        char path[1024];
        const char* base = SDL_GetBasePath();
        snprintf(path, sizeof path, "%sbag2jp_stage_visibility.mode", base ? base : "");
        FILE* control = fopen(path, "r");
        requested = control && fgetc(control) == '1';
        if (control) fclose(control);
    }
    const B1MusicProfile* profile = b1m_stage_profile();
    const int result = b1sv_update(requested, profile && profile->stage == 1);
    if (result && result != last_result)
        b1m_log("experimental stage visibility result=%d (1=screen bypass,2=native,-1=refused)", result);
    last_result = result;
}

/* ---- BAG1 stage camera adjustment (balanced focus: winner highlighted but rival and background fully visible) ---- */
static void b1s_camera_clamp_hook(struct CPUState* cpu, uint32_t address) {
    (void)address;
    /* Only adjust when an imported BAG1 stage is active */
    if (psx_mod_read_word(B1S_SHIM) != B1S_MAGIC) return;

    /* cpu->gpr[16] ($s0) is the camera target interpolation weight towards the leader.
     * Stock BAG2 clamps this to 0x800 (50%). In narrower BAG1 stages, reduce max bias to 0x380 (~22%)
     * so the camera gently frames the leader while keeping the second player and background in frame. */
    if (cpu->gpr[16] > 0x380u) {
        cpu->gpr[16] = 0x380u;
    }
}

static void b1s_camera_offset_hook(struct CPUState* cpu, uint32_t address) {
    (void)address;
    if (psx_mod_read_word(B1S_SHIM) != B1S_MAGIC) return;

    /* cpu->gpr[2] ($v0) is the target X offset (+0x140 / -0x140 = +/-320 units).
     * Scale to +/-160 units (+/-0xA0) to avoid pushing the second player off-screen. */
    int32_t val = (int32_t)cpu->gpr[2];
    if (val == 0x140) cpu->gpr[2] = 0xA0u;
    else if (val == -0x140) cpu->gpr[2] = (uint32_t)(int32_t)-0xA0;
}

PSX_MOD_CONSTRUCTOR(bag2jp_register_bag1_stage) {
    (void)psx_mod_register_vblank_plugin("bag2jp.bag1_stage", b1s_vblank_all);
    (void)psx_mod_register_activation_plugin("bag2jp.bag1_stage", b1m_activate);
    /* Camera hooks at 0x80014FB8 (bias weight clamp) and 0x80014FD4 (lateral X offset) */
    (void)psx_mod_register_instruction_plugin("bag2jp.bag1_stage", 0x80014FB8u, 0x9202D047u, b1s_camera_clamp_hook);
    (void)psx_mod_register_instruction_plugin("bag2jp.bag1_stage", 0x80014FD4u, 0xAF82D158u, b1s_camera_offset_hook);
}
