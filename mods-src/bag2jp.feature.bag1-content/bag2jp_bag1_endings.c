/* BAG1 campaign endings: movie, then a native dance on BAG2's final stage.
 * The engine is shared; character/costume/media selection is profile data.
 * All addresses below are audited for SLPM-86219 system/004 only. */
#include "mod_plugins.h"
#include <SDL3/SDL.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include "bag2jp_bag1_ending_data.h"

int bag2jp_bag1_has_version(int chr);
int bag2jp_bag1_get_version(int chr, int side);
int bag2jp_movie_start(const char* path);
int bag2jp_movie_playing(void);
void bag2jp_movie_stop(void);
void bag2jp_movie_tick(void);
void bag2jp_movie_pcm(int16_t*, uint32_t);
typedef struct { unsigned character; uint16_t models[2]; const char* movie; } EndingProfile;
static const EndingProfile profiles[] = {
    {0, {95,167}, "HEAT_END.mpg"},
    {1, {109,181}, "STRI_END.mpg"},
};
enum { SCRIPT = 0x8009635c, DANCE = 0x80096500, STUB = 0x80096630 };
typedef struct { uint32_t address, old, value; unsigned code; } SavedWord;
static SavedWord saved[256];
static unsigned saved_count;
static int active, started, movie_wait;
static char movies[1024];
static FILE* log_file;
static void ending_log(const char* event, unsigned a, unsigned b) {
    if (!log_file) { char p[1024]; snprintf(p,sizeof p,"%sbag2jp_bag1_endings.log",SDL_GetBasePath()); log_file=fopen(p,"w"); }
    if (log_file) { fprintf(log_file,"%s %u %u\n",event,a,b); fflush(log_file); }
}
static int module_matches(void) {
    return psx_mod_read_word(0x8009269cu)==0x27bdffe8u &&
           psx_mod_read_word(0x800929e0u)==0x27bdff38u &&
           psx_mod_read_word(0x800929e4u)==0xafbf00c4u &&
           psx_mod_read_word(0x80092b9cu)==0x0c02486fu &&
           psx_mod_read_word(0x80099c20u)==0x8008fa20u &&
           psx_mod_read_word(0x8009a508u)==0x8008fc5cu &&
           psx_mod_read_word(0x8009a558u)==0x8008fc64u &&
           psx_mod_read_half(0x80055318u)==304 && psx_mod_read_half(0x8005533cu)==305;
}
static void set_word(uint32_t address, uint32_t value, unsigned code) {
    if (saved_count >= sizeof saved/sizeof saved[0]) return;
    saved[saved_count++] = (SavedWord){address,psx_mod_read_word(address),value,code};
    if (code) psx_mod_write_code_word(address,value); else psx_mod_write_word(address,value);
}
static void set_bytes(uint32_t address, const uint8_t* bytes, unsigned size) {
    for (unsigned i=0;i<size;i+=4) {
        uint32_t value=(uint32_t)bytes[i]|(uint32_t)bytes[i+1]<<8|(uint32_t)bytes[i+2]<<16|(uint32_t)bytes[i+3]<<24;
        set_word(address+i,value,0);
    }
}
static void restore(void) {
    /* Never write a stale overlay back over another freshly loaded module. */
    for (unsigned i=saved_count;i>0;--i) {
        const SavedWord* p=&saved[i-1];
        if (psx_mod_read_word(p->address)==p->value) {
            if (p->code) psx_mod_write_code_word(p->address,p->old);
            else psx_mod_write_word(p->address,p->old);
        }
    }
    saved_count=0;
}
static void configure_dance(const EndingProfile* p) {
    set_bytes(SCRIPT,ending_script,sizeof ending_script);
    set_bytes(DANCE,ending_dance,sizeof ending_dance);
    set_word(STUB,0x03e00008u,1); set_word(STUB+4,0,1);
    const uint32_t callbacks[]={0x80099c20u,0x8009a508u,0x8009a558u};
    for (unsigned i=0;i<3;++i) set_word(callbacks[i]+p->character*4,STUB,0);
    /* Suppress the JP story panel's initial load, retaining native credits. */
    set_word(0x80092b9cu,0,1);
    const uint32_t pointers[]={0x801ca138u,0x801ca140u,0x801ca144u,0x801ca148u,
        0x801ca21cu,0x801ca220u,0x801ca224u,0x801ca228u,0x801ca22cu,0x801ca230u};
    const uint32_t offsets[]={0,0x10,0x18,0x30,0x40,0xb8,0x140,0x148,0x150,0x158};
    for (unsigned i=0;i<10;++i) psx_mod_write_word(pointers[i],SCRIPT+offsets[i]);
    psx_mod_write_word(0x801ca234u,DANCE);
    /* Skip character history; the custom dance starts with its own music. */
    const uint32_t times[]={0,620,10270,10320};
    for (unsigned i=0;i<4;++i) set_word(0x8009a5a0u+p->character*16+i*4,times[i],0);
    uint32_t a=0x80055318u+p->character*2;
    set_word(a,(psx_mod_read_word(a)&0xffff0000u)|p->models[0],0);
    a=0x8005533cu+p->character*2;
    set_word(a,(psx_mod_read_word(a)&0xffff0000u)|p->models[1],0);
}
static void ending_vblank(void) {
    bag2jp_movie_tick();
    if (!active) return;
    const unsigned root=psx_mod_read_word(0x8005d3d4u);
    const int in_ending=root==0x1bu && psx_mod_read_word(0x8005d2c4u)==5;
    if (!in_ending) {
        if (started) { bag2jp_movie_stop(); restore(); ending_log("exit",root,0); }
        started=movie_wait=0; return;
    }
    if (!started && module_matches()) {
        const unsigned side=psx_mod_read_byte(0x8005e6c8u);
        if (side>1) return;
        const unsigned chr=psx_mod_read_word(0x8005e6a0u+side*4);
        if (!bag2jp_bag1_has_version(chr)||!bag2jp_bag1_get_version(chr,side)) return;
        for (unsigned i=0;i<sizeof profiles/sizeof profiles[0];++i) if (profiles[i].character==chr) {
            char path[1200]; snprintf(path,sizeof path,"%s/%s",movies,profiles[i].movie);
            if (!movies[0]||!bag2jp_movie_start(path)) { started=-1; ending_log("media-unavailable",chr,side); return; }
            configure_dance(&profiles[i]); started=movie_wait=1;
            /* Hold only the ending update; PCM and host presentation continue. */
            set_word(0x800929e0u,0x03e00008u,1);
            set_word(0x800929e4u,0,1);
            ending_log("movie",chr,psx_mod_read_byte(0x8005e668u+side));
            break;
        }
    }
    if (movie_wait) {
        const unsigned side=psx_mod_read_byte(0x8005e6c8u);
        if (side<2 && (psx_mod_read_half(0x8005e872u+side*8)&0x800u)) bag2jp_movie_stop();
        if (!bag2jp_movie_playing()) {
            psx_mod_write_code_word(0x800929e0u,0x27bdff38u);
            psx_mod_write_code_word(0x800929e4u,0xafbf00c4u);
            movie_wait=0; ending_log("dance",0,0);
        }
    }
}
static void ending_activate(void) {
    movies[0]=0;
    psx_mod_current_resource_path("ending_movies",movies,sizeof movies);
    active=1; started=movie_wait=0; saved_count=0;
}
static void ending_reset(void) {
    bag2jp_movie_stop(); active=started=movie_wait=0; saved_count=0;
}
PSX_MOD_CONSTRUCTOR(bag2jp_register_bag1_endings) {
    (void)psx_mod_register_activation_plugin("bag2jp.bag1_endings",ending_activate);
    (void)psx_mod_register_session_reset_plugin("bag2jp.bag1_endings",ending_reset);
    (void)psx_mod_register_vblank_plugin("bag2jp.bag1_endings",ending_vblank);
    (void)psx_mod_register_pcm_plugin("bag2jp.bag1_endings",bag2jp_movie_pcm);
}
