/* HD intro replacement for BAG2JP (SLPM-86219).
 *
 * The game plays its opening movie STR/BUST2_OP.STR (MDEC, 320x240) straight
 * from the disc. While the CD is delivering sectors of that file, this plugin
 * shows an HD movie instead:
 *   - video: <exe dir>/movies/BUST2_OP.mpg (MPEG-1 + MP2, decoded with
 *     pl_mpeg on a worker thread) drawn over the whole window through the
 *     title HUD layer (psx_host_set_hud_draw_cb + gl_renderer_draw_host_movie);
 *   - audio: the movie's MP2 track replaces the game's mix in the PCM plugin
 *     callback (44.1 kHz stereo, same rate as the SPU output). The audio
 *     sample count is the clock the video follows.
 * The game keeps running its own movie underneath, so its timing, Start-to-skip
 * and what comes after are untouched. Playback stops as soon as the CD leaves
 * the STR extent (or stops advancing inside it, e.g. after Start).
 *
 * No movie file -> the plugin does nothing and the original intro plays. */
#include "mod_plugins.h"
#include "host_overlay.h"
#include "cdrom.h"
#include "gpu_gl_renderer.h"
#include "bag2jp_hud.h"

#include <SDL3/SDL.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>

#define PL_MPEG_IMPLEMENTATION
#include "pl_mpeg.h"

#define HD_STR_PATH       "STR/BUST2_OP.STR"
#define HD_STR_LBA_FALLBK 214715u
#define HD_STR_SECTORS    9320u
#define HD_MOVIE_NAME     "BUST2_OP.mpg"
#define HD_START_WINDOW   600u   /* only start near the beginning of the STR */
#define HD_STALL_FRAMES   30     /* CD idle inside the STR this long = ended */

enum { HD_IDLE = 0, HD_PLAYING = 1 };

static uint32_t s_str_lba = HD_STR_LBA_FALLBK, s_str_end = HD_STR_LBA_FALLBK + HD_STR_SECTORS;
static char s_movie_path[1024];
static char s_intro_path[1024];
static int  s_movie_ok;

/* emulation thread */
static int s_state = HD_IDLE;
static int s_last_lba = -1, s_stall;
static plm_t* s_audio;                         /* audio-only decoder */
static float s_abuf[PLM_AUDIO_SAMPLES_PER_FRAME * 2];
static int s_abuf_len, s_abuf_pos;             /* in stereo frames */

/* shared */
static atomic_int  s_active;                   /* drawing + audio replacement on */
static atomic_int  s_generation;               /* bumps per start/stop */
static atomic_llong s_audio_frames;            /* clock: stereo frames played */
static SDL_Mutex*  s_lock;
static SDL_Condition* s_wake;
static SDL_Thread* s_thread;
static uint8_t* s_front;                       /* BGRA, guarded by s_lock */
static int s_w, s_h;                           /* movie size */
static uint64_t s_front_seq, s_drawn_seq;      /* s_drawn_seq: render thread */
static int s_have_front;
static int s_external, s_hud_registered;
static atomic_int s_audio_done;

/* Small diagnostic log next to the executable (bag2jp_hd_intro.log). */
static FILE* s_log;
static void hd_log(const char* fmt, ...) {
    if (!s_log) {
        const char* base = SDL_GetBasePath();
        char path[1024];
        snprintf(path, sizeof path, "%sbag2jp_hd_intro.log", base ? base : "");
        s_log = fopen(path, "w");
        if (!s_log) return;
    }
    va_list ap;
    va_start(ap, fmt);
    vfprintf(s_log, fmt, ap);
    va_end(ap);
    fputc('\n', s_log);
    fflush(s_log);
}
static atomic_int s_draw_calls, s_frames_shown, s_frames_dropped;

static double clock_seconds(void) {
    return (double)atomic_load(&s_audio_frames) / 44100.0;
}

/* ---------------------------------------------------------------- video */
static int video_worker(void* unused) {
    (void)unused;
    int seen_gen = 0;
    for (;;) {
        SDL_LockMutex(s_lock);
        while (!atomic_load(&s_active) || atomic_load(&s_generation) == seen_gen)
            SDL_WaitCondition(s_wake, s_lock);
        seen_gen = atomic_load(&s_generation);
        char movie_path[sizeof s_movie_path];
        memcpy(movie_path, s_movie_path, sizeof movie_path);
        SDL_UnlockMutex(s_lock);

        plm_t* v = plm_create_with_filename(movie_path);
        if (!v) { psx_mod_counter_add("bag2jp.hd_intro.video_open_failed", 1); continue; }
        plm_set_audio_enabled(v, 0);
        plm_set_loop(v, 0);
        const int w = plm_get_width(v), h = plm_get_height(v);
        if (w <= 0 || h <= 0 || w > 4096 || h > 4096) { plm_destroy(v); continue; }
        uint8_t* pixels = (uint8_t*)malloc((size_t)w * h * 4);
        if (!pixels) { plm_destroy(v); continue; }
        plm_frame_t* f;
        while (atomic_load(&s_active) && atomic_load(&s_generation) == seen_gen &&
               (f = plm_decode_video(v)) != NULL) {
            /* frames already late by more than one frame are decoded only */
            const double frame_dur = 1.0 / plm_get_framerate(v);
            if (f->time + frame_dur < clock_seconds()) {
                psx_mod_counter_add("bag2jp.hd_intro.frames_dropped", 1);
                atomic_fetch_add(&s_frames_dropped, 1);
                continue;
            }
            plm_frame_to_bgra(f, pixels, w * 4);
            while (atomic_load(&s_active) && atomic_load(&s_generation) == seen_gen &&
                   clock_seconds() < f->time)
                SDL_Delay(2);
            SDL_LockMutex(s_lock);
            if (atomic_load(&s_active) && atomic_load(&s_generation) == seen_gen) {
                if (!s_front || w != s_w || h != s_h) {
                    uint8_t* resized = (uint8_t*)realloc(s_front, (size_t)w * h * 4);
                    if (resized) { s_front = resized; s_w = w; s_h = h; }
                }
                if (s_front && s_w == w && s_h == h) {
                    memcpy(s_front, pixels, (size_t)w * h * 4);
                    s_front_seq++;
                    s_have_front = 1;
                    atomic_fetch_add(&s_frames_shown, 1);
                }
            }
            SDL_UnlockMutex(s_lock);
        }
        free(pixels);
        plm_destroy(v);
    }
    return 0;
}

/* ---------------------------------------------------------------- draw (render thread) */
static void hd_draw(int width, int height, void* ctx) {
    (void)ctx;
    if (!atomic_load(&s_active)) return;
    if (atomic_fetch_add(&s_draw_calls, 1) == 0) hd_log("first draw %dx%d", width, height);
    SDL_LockMutex(s_lock);
    if (s_have_front) {
        const int upload = s_front_seq != s_drawn_seq;
        gl_renderer_draw_host_movie((const uint32_t*)s_front, s_w, s_h, upload, width, height);
        s_drawn_seq = s_front_seq;
    } else {
        gl_renderer_draw_host_movie(NULL, 0, 0, 0, width, height);   /* black */
    }
    SDL_UnlockMutex(s_lock);
}

/* ---------------------------------------------------------------- audio (emulation thread) */
static void hd_pcm(int16_t* stereo, uint32_t frames) {
    if (!atomic_load(&s_active)) return;
    for (uint32_t i = 0; i < frames; ++i) {
        float l = 0.f, r = 0.f;
        if (s_audio) {
            if (s_abuf_pos >= s_abuf_len) {
                plm_samples_t* smp = plm_decode_audio(s_audio);
                if (smp) {
                    memcpy(s_abuf, smp->interleaved, sizeof(float) * smp->count * 2);
                    s_abuf_len = (int)smp->count;
                } else {
                    s_abuf_len = 0;
                    atomic_store(&s_audio_done, 1);
                }
                s_abuf_pos = 0;
            }
            if (s_abuf_pos < s_abuf_len) {
                l = s_abuf[s_abuf_pos * 2];
                r = s_abuf[s_abuf_pos * 2 + 1];
                s_abuf_pos++;
            }
        }
        int li = (int)(l * 32767.f), ri = (int)(r * 32767.f);
        if (li > 32767) li = 32767; if (li < -32768) li = -32768;
        if (ri > 32767) ri = 32767; if (ri < -32768) ri = -32768;
        stereo[i * 2] = (int16_t)li;
        stereo[i * 2 + 1] = (int16_t)ri;
    }
    atomic_fetch_add(&s_audio_frames, (long long)frames);
}

/* ---------------------------------------------------------------- control (emulation thread) */
static void hd_start(void) {
    if (s_audio) plm_destroy(s_audio);
    s_audio = plm_create_with_filename(s_movie_path);
    if (s_audio) {
        plm_set_video_enabled(s_audio, 0);
        plm_set_loop(s_audio, 0);
    }
    s_abuf_len = s_abuf_pos = 0;
    atomic_store(&s_audio_frames, 0);
    atomic_store(&s_audio_done, 0);
    atomic_store(&s_frames_shown, 0);
    atomic_store(&s_frames_dropped, 0);
    atomic_store(&s_draw_calls, 0);
    SDL_LockMutex(s_lock);
    s_have_front = 0;
    atomic_store(&s_active, 1);
    psx_host_set_hud_continuous_present(1);
    atomic_fetch_add(&s_generation, 1);
    SDL_SignalCondition(s_wake);
    SDL_UnlockMutex(s_lock);
    s_state = HD_PLAYING;
    psx_mod_counter_add("bag2jp.hd_intro.started", 1);
    hd_log("start (lba %d) audio=%s", s_last_lba, s_audio ? "ok" : "FAILED");
}

static void hd_stop(void) {
    SDL_LockMutex(s_lock);
    atomic_store(&s_active, 0);
    psx_host_set_hud_continuous_present(0);
    atomic_fetch_add(&s_generation, 1);
    s_have_front = 0;
    SDL_UnlockMutex(s_lock);
    if (s_audio) { plm_destroy(s_audio); s_audio = NULL; }
    s_state = HD_IDLE;
    psx_mod_counter_add("bag2jp.hd_intro.stopped", 1);
    hd_log("stop: lba %d, audio %.2f s, video frames shown %d dropped %d draw_calls %d",
           cdrom_get_delivered_lba(), clock_seconds(),
           atomic_load(&s_frames_shown), atomic_load(&s_frames_dropped), atomic_load(&s_draw_calls));
}

static void hd_vblank(void) {
    if (s_external) {
        if (atomic_load(&s_audio_done)) { hd_stop(); s_external = 0; }
        return;
    }
    if (!s_movie_ok) return;
    const int lba = cdrom_get_delivered_lba();
    const int in_str = lba >= (int)s_str_lba && lba < (int)s_str_end;
    if (s_state == HD_IDLE) {
        if (in_str && (uint32_t)lba < s_str_lba + HD_START_WINDOW && lba != s_last_lba) {
            SDL_LockMutex(s_lock);
            memcpy(s_movie_path, s_intro_path, sizeof s_movie_path);
            SDL_UnlockMutex(s_lock);
            hd_start();
            s_stall = 0;
        }
    } else {
        if (!in_str) {
            hd_stop();
        } else if (lba == s_last_lba) {
            if (++s_stall > HD_STALL_FRAMES) hd_stop();
        } else {
            s_stall = 0;
        }
    }
    s_last_lba = lba;
}

/* ---------------------------------------------------------------- setup */
static int probe_movie(void) {
    plm_t* p = plm_create_with_filename(s_movie_path);
    if (!p) return 0;
    const int w = plm_get_width(p), h = plm_get_height(p);
    const int rate = plm_get_samplerate(p);
    plm_destroy(p);
    if (w <= 0 || h <= 0 || w > 4096 || h > 4096) return 0;
    if (rate != 44100) psx_mod_counter_add("bag2jp.hd_intro.samplerate_not_44100", 1);
    return rate == 44100;
}

/* Shared player: called on the emulation thread with a trusted absolute resource path.
 * Independent of the optional HD-opening feature. Returns zero before changing playback
 * if media cannot be opened; the caller can retain its original game flow. */
int bag2jp_movie_start(const char* path) {
    if (!path || !*path || strlen(path) >= sizeof s_movie_path) return 0;
    if (atomic_load(&s_active)) return 0;
    if (!s_lock) s_lock = SDL_CreateMutex();
    if (!s_wake) s_wake = SDL_CreateCondition();
    if (!s_lock || !s_wake) return 0;
    SDL_LockMutex(s_lock);
    snprintf(s_movie_path, sizeof s_movie_path, "%s", path);
    SDL_UnlockMutex(s_lock);
    if (!probe_movie()) return 0;
    if (!s_thread) s_thread = SDL_CreateThread(video_worker, "bag2jp-movie", NULL);
    if (!s_thread) return 0;
    if (!s_hud_registered) { bag2jp_hud_add(hd_draw, NULL); s_hud_registered = 1; }
    s_external = 1;
    hd_start();
    if (!s_audio) { hd_stop(); s_external = 0; return 0; }
    return 1;
}
int bag2jp_movie_playing(void) { return s_external && atomic_load(&s_active); }
void bag2jp_movie_stop(void) {
    if (s_external) { hd_stop(); s_external = 0; }
}
/* Ending plugin owns these calls even when the opening-movie plugin is disabled. */
void bag2jp_movie_tick(void) {
    if (s_external && atomic_load(&s_audio_done)) bag2jp_movie_stop();
}
void bag2jp_movie_pcm(int16_t* stereo, uint32_t frames) {
    if (s_external) hd_pcm(stereo, frames);
}
static void hd_intro_pcm(int16_t* stereo, uint32_t frames) {
    if (!s_external) hd_pcm(stereo, frames);
}

static void bag2jp_hd_intro_activate(void) {
    if (!s_lock) {
        s_lock = SDL_CreateMutex();
        s_wake = SDL_CreateCondition();
    }
    const char* base = SDL_GetBasePath();
    snprintf(s_movie_path, sizeof s_movie_path, "%smovies/%s", base ? base : "", HD_MOVIE_NAME);
    memcpy(s_intro_path, s_movie_path, sizeof s_intro_path);
    uint32_t lba = 0, size = 0;
    if (psx_mod_disc_file_extent(HD_STR_PATH, &lba, &size) && lba && size) {
        s_str_lba = lba;
        s_str_end = lba + (size + 2047u) / 2048u;
    }
    s_movie_ok = s_lock && s_wake && probe_movie();
    hd_log("activate: movie '%s' ok=%d %dx%d, STR lba %u..%u", s_movie_path, s_movie_ok, s_w, s_h, s_str_lba, s_str_end);
    if (!s_movie_ok) { psx_mod_counter_add("bag2jp.hd_intro.no_movie", 1); return; }
    if (!s_thread) s_thread = SDL_CreateThread(video_worker, "bag2jp-hd-intro", NULL);
    if (!s_thread) { s_movie_ok = 0; return; }
    s_state = HD_IDLE;
    s_last_lba = -1;
    atomic_store(&s_active, 0);
    if (!s_hud_registered) { bag2jp_hud_add(hd_draw, NULL); s_hud_registered = 1; }
}

PSX_MOD_CONSTRUCTOR(bag2jp_register_hd_intro) {
    (void)psx_mod_register_activation_plugin("bag2jp.hd_intro", bag2jp_hd_intro_activate);
    (void)psx_mod_register_vblank_plugin("bag2jp.hd_intro", hd_vblank);
    (void)psx_mod_register_pcm_plugin("bag2jp.hd_intro", hd_intro_pcm);
}
