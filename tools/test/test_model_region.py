"""Compile the real model-region helper against a fake guest RAM and check its contract."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def wsl_path(path: Path) -> str:
    """Return the WSL view of a D: path."""
    return '/mnt/d/' + path.as_posix()[3:]


class ModelRegionTests(unittest.TestCase):
    """BAG1 player buffers move to expanded RAM only when safe and wanted."""

    def test_relocation_rules(self) -> None:
        output = ROOT / '_work/model-region-tests'
        output.mkdir(parents=True, exist_ok=True)
        header = wsl_path(ROOT / 'mods-src/bag2jp.feature.bag1-content/bag2jp_model_region.h')
        source = '''#include <stdint.h>
#include <assert.h>
#include <string.h>
static uint32_t words[0x100000]; static int writes;
static uint32_t* at(uint32_t a) { return &words[(a & 0x3FFFFF) >> 2]; }
uint32_t psx_mod_read_word(uint32_t a) { return *at(a); }
uint8_t psx_mod_read_byte(uint32_t a) { return (uint8_t)(*at(a & ~3u) >> (8 * (a & 3))); }
void psx_mod_write_word(uint32_t a, uint32_t v) { *at(a) = v; ++writes; }
static void set_byte(uint32_t a, uint8_t v) { uint32_t* w = at(a & ~3u); int s = 8 * (a & 3);
 *w = (*w & ~(0xFFu << s)) | ((uint32_t)v << s); }
''' + f'#include "{header}"\n' + '''
static void reset(uint32_t ram, uint8_t state) { memset(words, 0, sizeof words); writes = 0;
 *at(B1R_RAM_SIZE_WORD) = ram; *at(B1R_BASE_P1) = 0x800D1350u; *at(B1R_BASE_P2) = 0x801485ECu;
 set_byte(B1R_LOADER_STATE, state); }
int main(void) {
 const int both[2] = {1, 1}, none[2] = {0, 0}, p2[2] = {0, 1};
 reset(B1R_RAM_8MB, 1); assert(bag2_model_region_tick(both) == 3);
 assert(*at(B1R_BASE_P1) == 0x80200000u && *at(B1R_BASE_P2) == 0x80300000u);
 assert(bag2_model_region_tick(both) == 0 && writes == 2);            /* idempotent */
 reset(0x00200000u, 1); assert(bag2_model_region_tick(both) == 0 && writes == 0);  /* 2 MB: never */
 reset(B1R_RAM_8MB, 1); assert(bag2_model_region_tick(none) == 0 && writes == 0);  /* stock BAG2 */
 reset(B1R_RAM_8MB, 0); assert(bag2_model_region_tick(both) == 0);   /* before pack load */
 reset(B1R_RAM_8MB, 6); assert(bag2_model_region_tick(both) == 2);   /* P1 model read: too late */
 assert(*at(B1R_BASE_P1) == 0x800D1350u && *at(B1R_BASE_P2) == 0x80300000u);
 reset(B1R_RAM_8MB, 8); assert(bag2_model_region_tick(both) == 0);   /* P2 pack read: too late */
 reset(B1R_RAM_8MB, 5); assert(bag2_model_region_tick(p2) == 2 && *at(B1R_BASE_P1) == 0x800D1350u);
 return 0;
}
'''
        (output / 'test.c').write_text(source, encoding='utf-8', newline='\n')
        prefix = ['wsl.exe', '-d', 'Ubuntu', '--exec']
        linux = wsl_path(output)
        subprocess.run(prefix + ['gcc', '-Wall', '-Wextra', '-Werror', linux + '/test.c', '-o', linux + '/test'], check=True)
        subprocess.run(prefix + [linux + '/test'], check=True)


if __name__ == '__main__':
    unittest.main()
