"""Exercise stage audio routing and duration restoration in the real C plugin."""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


class StageAudioTests(unittest.TestCase):
    def test_strike_channel_and_duration_are_isolated_from_heat_and_stock(self):
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
static uint64_t seek_position;
#define b1m_log(...) ((void)0)
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
int psx_mod_current_resource_path(const char*a,char*b,size_t n) {return 0;}
int psx_mod_disc_file_extent(const char*a,uint32_t*b,uint32_t*c) {return 0;}
static char opened[1200];
FILE* test_open(const char*path,const char*mode) {
 snprintf(opened,sizeof opened,"%s",path);return tmpfile();
}
#define fopen test_open
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
 b1m_lba=100; b1m_end=1000;
 int16_t pcm[4]={9,9,9,9};
 stage(1,1);snprintf(b1m_dir,sizeof b1m_dir,"test-music");
 b1m_filter(101,1,1,pcm,2); assert(pcm[0]==321);
 assert(strstr(opened,"strike_game.flac"));
 pcm[0]=9;b1m_filter(100,1,0,pcm,2);assert(pcm[0]==9);
 pcm[0]=9;b1m_filter(101,1,0,pcm,2);assert(pcm[0]==9);
 stage(1,0); b1m_filter(101,1,1,pcm,2);assert(pcm[0]==9);
  stage(2,1); b1m_filter(102,1,2,pcm,2);assert(pcm[0]==9);
  stage(0,1); b1m_filter(100,1,0,pcm,2);
  assert(strstr(opened,"heat_2bad_cd.flac") && closes==1);
  stage(1,1); b1m_filter(109,1,1,pcm,2);
  assert(strstr(opened,"strike_game.flac") && closes==2);
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
 return 0;
}
'''
        out = ROOT / '_work/stage_import/strike/audio-tests'
        out.mkdir(parents=True, exist_ok=True)
        (out / 'audio.c').write_text(harness)
        path = '/mnt/d/' + out.as_posix()[3:]
        subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', 'gcc', '-std=c11',
                        f'{path}/audio.c', '-o', f'{path}/audio'], check=True)
        subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', f'{path}/audio'], check=True)
