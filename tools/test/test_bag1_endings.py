"""Compile and test bag2jp_bag1_endings logic under host emulation."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class Bag1EndingsTests(unittest.TestCase):
    def test_endings_support_both_ending_view_and_campaign_modes(self):
        source = (ROOT / 'mods-src/bag2jp.feature.bag1-content/bag2jp_bag1_endings.c').read_text()
        out = ROOT / '_work/endings-tests'
        out.mkdir(parents=True, exist_ok=True)
        # Include bag2jp_bag1_ending_data.h content
        data_h = (ROOT / 'mods-src/bag2jp.feature.bag1-content/bag2jp_bag1_ending_data.h').read_text()
        harness = '''#include <stdint.h>
#include <assert.h>
#include <string.h>
#include <stdio.h>

''' + data_h + '''

static uint8_t ram[0x800000];
#define RAM(a) (ram+((a)&0x7fffff))
uint8_t psx_mod_read_byte(uint32_t a) { return *RAM(a); }
uint16_t psx_mod_read_half(uint32_t a) { uint16_t v; memcpy(&v,RAM(a),2); return v; }
uint32_t psx_mod_read_word(uint32_t a) { uint32_t v; memcpy(&v,RAM(a),4); return v; }
void psx_mod_write_byte(uint32_t a,uint8_t v) { *RAM(a)=v; }
void psx_mod_write_half(uint32_t a,uint16_t v) { memcpy(RAM(a),&v,2); }
void psx_mod_write_word(uint32_t a,uint32_t v) { memcpy(RAM(a),&v,4); }
void psx_mod_write_code_word(uint32_t a,uint32_t v) { memcpy(RAM(a),&v,4); }
int psx_mod_current_resource_path(const char* name, char* buf, size_t sz) {
    snprintf(buf, sz, "/mock/movies");
    return 1;
}

static int s_movie_started = 0;
static char s_last_movie[256] = {0};
int bag2jp_movie_start(const char* path) {
    s_movie_started = 1;
    strncpy(s_last_movie, path, sizeof s_last_movie - 1);
    return 1;
}
int bag2jp_movie_playing(void) { return s_movie_started; }
void bag2jp_movie_stop(void) { s_movie_started = 0; }
void bag2jp_movie_tick(void) {}
void bag2jp_movie_pcm(int16_t* pcm, uint32_t frames) {}

static int s_chr_version[2][2] = {{1, 0}, {1, 0}};
int bag2jp_bag1_has_version(int chr) { return chr < 2; }
int bag2jp_bag1_get_version(int chr, int side) { return (chr < 2 && side < 2) ? s_chr_version[chr][side] : 0; }

const char* SDL_GetBasePath(void) { return "/tmp/"; }
'''
        # Extract code from typedef struct { unsigned character... to ending_reset
        code_start = source.index('typedef struct { unsigned character;')
        code_end = source.index('static void ending_reset(void)')
        test_c = harness + source[code_start:code_end] + '''
static void setup_module_words(void) {
    psx_mod_write_word(0x8009269cu, 0x27bdffe8u);
    psx_mod_write_word(0x800929e0u, 0x27bdff38u);
    psx_mod_write_word(0x800929e4u, 0xafbf00c4u);
    psx_mod_write_word(0x80092b9cu, 0x0c02486fu);
    psx_mod_write_word(0x80099c20u, 0x8008fa20u);
    psx_mod_write_word(0x8009a508u, 0x8008fc5cu);
    psx_mod_write_word(0x8009a558u, 0x8008fc64u);
    psx_mod_write_half(0x80055318u, 304);
    psx_mod_write_half(0x8005533cu, 305);
}

int main(void) {
    ending_activate();
    setup_module_words();

    /* Mode 5 (Ending View) with Strike BAG1 */
    memset(ram, 0, 0x1000);
    setup_module_words();
    psx_mod_write_word(0x8005d3d4u, 0x1bu); /* root 27 */
    psx_mod_write_word(0x8005d2c4u, 5);     /* Ending View */
    psx_mod_write_byte(0x8005e6c8u, 0);     /* side 0 */
    psx_mod_write_word(0x8005e6a0u, 1);     /* char 1 = Strike */
    s_movie_started = 0;
    ending_vblank();
    assert(s_movie_started == 1);
    assert(strstr(s_last_movie, "STRI_END.mpg") != NULL);
    assert(started == 1);
    assert(movie_wait == 1);

    /* End movie, advance to dance */
    s_movie_started = 0;
    ending_vblank();
    assert(movie_wait == 0);

    /* Return to menu: root changes to 7 */
    psx_mod_write_word(0x8005d3d4u, 7);
    ending_vblank();
    assert(started == 0);

    /* Mode 1 (Campaign Mode) with Strike BAG1 */
    memset(ram, 0, 0x1000);
    setup_module_words();
    psx_mod_write_word(0x8005d3d4u, 0x1bu); /* root 27 */
    psx_mod_write_word(0x8005d2c4u, 1);     /* Campaign mode */
    psx_mod_write_byte(0x8005e6c8u, 0);     /* side 0 */
    psx_mod_write_word(0x8005e6a0u, 1);     /* char 1 = Strike */
    s_movie_started = 0;
    ending_vblank();
    assert(s_movie_started == 1);
    assert(strstr(s_last_movie, "STRI_END.mpg") != NULL);

    /* Stock character version: should NOT trigger BAG1 ending */
    memset(ram, 0, 0x1000);
    setup_module_words();
    s_chr_version[1][0] = 0; /* Strike BAG2 */
    psx_mod_write_word(0x8005d3d4u, 0x1bu);
    psx_mod_write_word(0x8005d2c4u, 1);
    psx_mod_write_byte(0x8005e6c8u, 0);
    psx_mod_write_word(0x8005e6a0u, 1);
    s_movie_started = 0;
    ending_vblank();
    assert(s_movie_started == 0);

    return 0;
}
'''
        (out / 'endings_test.c').write_text(test_c)
        path = '/mnt/d/' + out.as_posix()[3:]
        subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', 'gcc', '-std=c11', '-Wall',
                        '-Werror', '-Wno-unused-const-variable', f'{path}/endings_test.c', '-o', f'{path}/endings_test'], check=True)
        subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', f'{path}/endings_test'], check=True)


if __name__ == '__main__':
    unittest.main()
