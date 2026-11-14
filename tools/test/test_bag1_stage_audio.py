"""Exercise stage audio routing and duration restoration in the real C plugin."""
from pathlib import Path
import subprocess
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[2]


class StageAudioTests(unittest.TestCase):
    def _run_audio_harness(self, scenario: str | None = None) -> None:
        source = (ROOT / 'mods-src/bag2jp.feature.bag1-content/bag2jp_bag1_stage.c').read_text()
        audio = source[source.index('#define B1M_FRAMES_PER_SECTOR'):source.index('static void b1s_vblank_all')]
        harness = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#define B1S_SHIM 0x801e0100u
#define B1S_MAGIC 0x54533142u
#define B1S_ROOT_GAMEPLAY 0x13u
static uint8_t ram[0x800000];
#define RAM(a) (ram+((a)&0x7fffff))
uint32_t psx_mod_read_word(uint32_t a) {uint32_t v;memcpy(&v,RAM(a),4);return v;}
uint16_t psx_mod_read_half(uint32_t a) {uint16_t v;memcpy(&v,RAM(a),2);return v;}
uint8_t psx_mod_read_byte(uint32_t a) {return *RAM(a);}
void psx_mod_write_word(uint32_t a,uint32_t v) {memcpy(RAM(a),&v,4);}
void psx_mod_write_half(uint32_t a,uint16_t v) {memcpy(RAM(a),&v,2);}
typedef uint64_t drflac_uint64;
typedef struct {int sampleRate,channels;} drflac;
typedef void (*CdromXaHostFilter)(int,int,int,int16_t*,int);
static drflac decoder={44100,2};
static int seek_ok=1, short_read=0, closes=0, chained=0;
static int resources_enabled, missing_file;
static int missing_extent;
static const char* song_choice="japanese";
static uint64_t seek_position;
static int trace_enabled, trace_logs;
static const char* test_env(const char* key) {return trace_enabled ? "1" : NULL;}
#define getenv test_env
#define b1m_log(...) (trace_logs++)
#define b1m_rd NULL
#define b1m_sk NULL
#define b1m_tl NULL
drflac* drflac_open(void*a,void*b,void*c,void*d,void*e) {return &decoder;}
void drflac_close(drflac*f) {closes++;}
int drflac_seek_to_pcm_frame(drflac*f,uint64_t p) {seek_position=p;return seek_ok;}
uint64_t drflac_read_pcm_frames_s16(drflac*f,uint64_t n,int16_t*out) {
  if(short_read) n=1;
  for(uint64_t i=0;i<n*2;i++) out[i]=321; return n;
}
int psx_mod_current_option_value(const char*a,char*b,size_t n) {return 0;}
int psx_mod_option_value(const char*p,const char*f,const char*o,char*out,uint32_t n) {
 assert(!strcmp(p,"bag2jp.localization.regional"));
 assert(!strcmp(f,"regional") && !strcmp(o,"songs"));
 if(!song_choice) return 0;
 snprintf(out,n,"%s",song_choice);return 1;
}
int psx_mod_current_resource_path(const char*a,char*b,size_t n) {
 if(!resources_enabled) return 0;
 snprintf(b,n,"test-music");return 1;
}
int psx_mod_disc_file_extent(const char*a,uint32_t*b,uint32_t*c) {
 if(!resources_enabled) return 0;
 if(missing_extent && !strcmp(a,"XA/BUST2_02.XA")) return 0;
 if(!strcmp(a,"XA/BUST2_01.XA")) {*b=100;*c=900*2048;return 1;}
 if(!strcmp(a,"XA/BUST2_02.XA")) {*b=2000;*c=1000*2048;return 1;}
 assert(0);return 0;
}
static char opened[1200];
FILE* test_open(const char*path,const char*mode) {
 snprintf(opened,sizeof opened,"%s",path);return missing_file ? NULL : tmpfile();
}
#define fopen test_open
static int gaso_bag1=1; /* Gas-O stage 9 is the BAG1 import in these fixtures */
static int b1s_is_gaso_bag1(void) {return gaso_bag1;}
static int timing_enabled;
static int b1m_timing_on(void) {return timing_enabled;}
static double b1m_wall(void) {return 0.0;}
''' + audio + r'''
static void stage(int id,int bag1) {
 psx_mod_write_word(0x8005d3d4u, 0x13u);
 psx_mod_write_word(B1S_SHIM,bag1?B1S_MAGIC:0);
 psx_mod_write_word(0x80089200,0x80200000);*RAM(0x80200000)=id;
}
static void previous(int l,int f,int c,int16_t*p,int n) {chained++;}
int main(void) {
 psx_mod_write_half(B1M_SONG_LEN_TABLE,152);
 psx_mod_write_half(B1M_SONG_LEN_TABLE+2,136);
 stage(1,1); b1m_song_length();
 assert(psx_mod_read_half(B1M_SONG_LEN_TABLE+2)==129);
 assert(psx_mod_read_half(B1M_SONG_LEN_TABLE)==152);
 psx_mod_write_word(0x8005d3d4u, 0x0du);
 b1m_song_length();
 assert(psx_mod_read_half(B1M_SONG_LEN_TABLE+2)==136);
 assert(psx_mod_read_half(B1M_SONG_LEN_TABLE)==152);
 stage(0,1); b1m_song_length();
 assert(psx_mod_read_half(B1M_SONG_LEN_TABLE+2)==136);
 assert(psx_mod_read_half(B1M_SONG_LEN_TABLE)==129);
 stage(1,0); b1m_song_length();
 assert(psx_mod_read_half(B1M_SONG_LEN_TABLE)==152);
 assert(psx_mod_read_half(B1M_SONG_LEN_TABLE+2)==136);
  b1m_lba[0]=100; b1m_end[0]=1000;
 int16_t pcm[4]={9,9,9,9};
 stage(1,1);snprintf(b1m_dir,sizeof b1m_dir,"test-music");
 b1m_filter(101,1,1,pcm,2); assert(pcm[0]==321);
  assert(strstr(opened,"strike_japanese.flac"));
 pcm[0]=9;b1m_filter(100,1,0,pcm,2);assert(pcm[0]==9);
 pcm[0]=9;b1m_filter(101,1,0,pcm,2);assert(pcm[0]==9);
 stage(1,0); b1m_filter(101,1,1,pcm,2);assert(pcm[0]==9);
  stage(2,1); b1m_filter(102,1,2,pcm,2);assert(pcm[0]==9);
  stage(0,1); b1m_filter(100,1,0,pcm,2);
   assert(strstr(opened,"heat_2bad_japanese.flac") && closes==1);
  stage(1,1); b1m_filter(109,1,1,pcm,2);
   assert(strstr(opened,"strike_japanese.flac") && closes==2);
  assert(seek_position==2352);
  seek_ok=0; b1m_filter(117,1,1,pcm,2);
  assert(pcm[0]==0 && pcm[3]==0);
  seek_ok=1;short_read=1;b1m_filter(125,1,1,pcm,2);
  assert(pcm[0]==321 && pcm[2]==0 && pcm[3]==0);
  b1m_prev=previous;stage(1,0);pcm[0]=9;
  b1m_filter(101,1,1,pcm,2);assert(chained==1 && pcm[0]==9);
  stage(1,1);b1m_song_length();
  psx_mod_write_half(B1M_SONG_LEN_TABLE+2,140);
  stage(1,0);b1m_song_length();
  assert(psx_mod_read_half(B1M_SONG_LEN_TABLE+2)==140);
  b1m_activate();
  /* Diagnostics must observe the viewer without changing routing or PCM. */
  stage(1,1); psx_mod_write_word(0x8005d2c4u,4);
   b1m_lba[0]=100;b1m_end[0]=1000;
  int before=trace_logs;
  b1m_trace_viewer_audio(101,1,1);
  assert(trace_logs==before);
  trace_enabled=1;
  b1m_trace_viewer_audio(101,1,1);
  assert(trace_logs==before+1);
  b1m_trace_viewer_audio(109,1,1);
  assert(trace_logs==before+1);
  b1m_trace_viewer_audio(102,1,2);
  assert(trace_logs==before+2);
  psx_mod_write_word(0x8005d2c4u,2);
  b1m_trace_viewer_audio(103,1,3);
  assert(trace_logs==before+2);
  /* Dance View has a different root state (0x19), despite sharing the stage. */
  stage(1,1);psx_mod_write_word(0x8005d3d4u,0x19);
  psx_mod_write_word(0x8005d2c4u,4);
  snprintf(b1m_dir,sizeof b1m_dir,"test-music");
  short_read=0;pcm[0]=9;
  b1m_filter(101,1,1,pcm,2);assert(pcm[0]==321);
  b1m_song_length();assert(psx_mod_read_half(B1M_SONG_LEN_TABLE+2)==129);
  psx_mod_write_word(B1S_SHIM,0);pcm[0]=9;
  b1m_filter(101,1,1,pcm,2);assert(pcm[0]==9);
  psx_mod_write_word(B1S_SHIM,B1S_MAGIC);
  psx_mod_write_word(0x8005d2c4u,2);
  b1m_filter(101,1,1,pcm,2);assert(pcm[0]==9);
  psx_mod_write_word(0x8005d2c4u,4);*RAM(0x80200000)=2;
  b1m_filter(102,1,2,pcm,2);assert(pcm[0]==9);
  return 0;
}
'''
        if scenario is not None:
            harness = harness[:harness.index('int main(void) {')] + scenario
        out = ROOT / '_work/stage_import/strike/audio-tests'
        out.mkdir(parents=True, exist_ok=True)
        (out / 'audio.c').write_text(harness)
        path = '/mnt/d/' + out.as_posix()[3:]
        subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', 'gcc', '-std=c11',
                        f'{path}/audio.c', '-o', f'{path}/audio'], check=True)
        subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', f'{path}/audio'], check=True)

    def test_strike_channel_and_duration_are_isolated_from_heat_and_stock(self) -> None:
        self._run_audio_harness()

    def test_existing_songs_option_routes_three_imports_and_isolates_xa_extents(self) -> None:
        self._run_audio_harness(r'''
int main(void) {
 const int ids[]={0,1,9};
 const char* names[]={"heat_2bad","strike","gaso"};
 const char* choices[]={"japanese","international","cd"};
 resources_enabled=1;
 for(int choice=0;choice<3;choice++) {
  song_choice=choices[choice];b1m_activate();
  for(int song=0;song<3;song++) {
   int16_t pcm[4]={9,9,9,9};
   const int lba=song==2?2001:100+song;
   stage(ids[song],1);b1m_filter(lba,1,song==0?0:1,pcm,2);
   char expected[128];snprintf(expected,sizeof expected,"/%s_%s.flac",names[song],choices[choice]);
   assert(strstr(opened,expected));assert(pcm[0]==321);
   /* Matching channel in the other file must not consume this song. */
   pcm[0]=9;b1m_filter(song==2?101:2000+song,1,song==0?0:1,pcm,2);
   assert(pcm[0]==9);
   stage(ids[song],0);b1m_filter(lba,1,song==0?0:1,pcm,2);assert(pcm[0]==9);
  }
 }
 /* Missing/invalid options reset to Japanese rather than retaining CD. */
 song_choice=NULL;b1m_activate();stage(1,1);
 int16_t pcm[4]={9,9,9,9};b1m_filter(101,1,1,pcm,2);
 assert(strstr(opened,"strike_japanese.flac"));
 song_choice="bad";b1m_activate();b1m_filter(101,1,1,pcm,2);
 assert(strstr(opened,"strike_japanese.flac"));
 /* No mislabeled fallback to XA-derived files when CD is absent. */
 song_choice="cd";missing_file=1;b1m_activate();pcm[0]=9;
 b1m_filter(101,1,1,pcm,2);assert(pcm[0]==9 && strstr(opened,"strike_cd.flac"));
 missing_file=0;b1m_activate();b1m_filter(101,1,1,pcm,2);assert(pcm[0]==321);
 psx_mod_write_half(B1M_SONG_LEN_TABLE+18,160);
 stage(9,1);b1m_song_length();assert(psx_mod_read_half(B1M_SONG_LEN_TABLE+18)==150);
 stage(9,0);b1m_song_length();assert(psx_mod_read_half(B1M_SONG_LEN_TABLE+18)==160);
 b1m_activate();return 0;
}
''')

    def test_missing_resources_bad_decoder_and_second_extent_fail_safely(self) -> None:
        self._run_audio_harness(r'''
int main(void) {
 int16_t pcm[4]={9,9,9,9};
 b1m_prev=previous;stage(1,1);b1m_activate();
 b1m_filter(101,1,1,pcm,2);assert(pcm[0]==9 && chained==1);
 resources_enabled=1;missing_extent=1;b1m_activate();stage(9,1);
 b1m_filter(2001,1,1,pcm,2);assert(pcm[0]==9);
 stage(1,1);b1m_filter(101,1,1,pcm,2);assert(pcm[0]==321);
 decoder.sampleRate=37800;b1m_activate();pcm[0]=9;
 b1m_filter(101,1,1,pcm,2);assert(pcm[0]==9);
 decoder.sampleRate=44100;decoder.channels=1;b1m_activate();
 b1m_filter(101,1,1,pcm,2);assert(pcm[0]==9);
 decoder.channels=2;missing_extent=0;b1m_activate();stage(9,1);
 b1m_filter(2009,1,1,pcm,2);assert(pcm[0]==321 && seek_position==2352);
 pcm[0]=9;b1m_filter(-1,1,1,pcm,2);assert(pcm[0]==9);
 b1m_filter(2009,1,1,pcm,0);assert(pcm[0]==9);
 b1m_filter(2009,1,1,pcm,9409);assert(pcm[0]==9);
 /* Stage 9 with the stock Gas-O entry is not the BAG1 import: no replacement. */
 gaso_bag1=0;pcm[0]=9;b1m_filter(2009,1,1,pcm,2);assert(pcm[0]==9);
 gaso_bag1=1;
 b1m_activate();return 0;
}
''')

    def test_opt_in_timing_logs_seeks_only_and_keeps_pcm(self) -> None:
        self._run_audio_harness(r'''
int main(void) {
 int16_t pcm[4]={9,9,9,9};
 resources_enabled=1;b1m_activate();stage(1,1);
 timing_enabled=1;int before=trace_logs;
 /* Open logs the song; cursor 0 matches sector 0, so no timing line. */
 b1m_filter(101,1,1,pcm,2);assert(pcm[0]==321 && trace_logs==before+1);
 /* Sector 1 needs a seek: one timing line, same PCM. */
 pcm[0]=9;b1m_filter(109,1,1,pcm,2);
 assert(pcm[0]==321 && seek_position==2352 && trace_logs==before+2);
 seek_ok=0;b1m_filter(117,1,1,pcm,2);assert(pcm[0]==0 && trace_logs==before+3);
 seek_ok=1;timing_enabled=0;pcm[0]=9;b1m_filter(125,1,1,pcm,2);
 assert(pcm[0]==321 && trace_logs==before+3);
 b1m_activate();return 0;
}
''')

    def test_only_existing_song_mod_exposes_audio_choice(self) -> None:
        bag1 = tomllib.loads((ROOT / 'mods-src/bag2jp.feature.bag1-content/1.0.0/manifest.toml').read_text())
        self.assertNotIn('bag1_song_audio', [option['id'] for option in bag1['option']])
        regional = tomllib.loads((ROOT / 'mods-src/bag2jp.localization.regional/1.0.0/manifest.toml').read_text())
        songs = next(option for option in regional['option'] if option['id'] == 'songs')
        self.assertEqual({'japanese', 'international', 'cd'}, {choice['value'] for choice in songs['choice']})
