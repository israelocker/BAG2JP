"""Exercise the opt-in screen-culling experiment against JP instruction guards."""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


class StageVisibilityTests(unittest.TestCase):
    def test_patch_is_opt_in_guarded_and_restores_only_owned_code(self) -> None:
        """Keep depth/GTE guards and unrelated modifications intact."""
        header = (ROOT / 'mods-src/bag2jp.feature.bag1-content/'
                  'bag2jp_stage_visibility_test.h').read_text()
        harness = r'''
#include <assert.h>
#include <stdint.h>
#include <string.h>
static uint8_t ram[0x200000];
static unsigned writes;
static uint32_t psx_mod_read_word(uint32_t a) {
    uint32_t v; memcpy(&v, ram+(a&0x1fffff), 4); return v;
}
static void put(uint32_t a, uint32_t v) {memcpy(ram+(a&0x1fffff), &v, 4);}
static void psx_mod_write_code_word(uint32_t a, uint32_t v) {writes++;put(a,v);}
''' + header + r'''
static void native(void) {
    put(0x80030574,0x2c421000);put(0x80030578,0x10400018);
    put(0x80030588,0x04400014);put(0x80030590,0x0243001b);
    put(0x80030594,0x00002012);put(0x800305d4,0x24020001);
    put(0x800305d8,0xa2020000);
}
int main(void) {
    native();b1sv_update(0,1);b1sv_update(1,0);assert(writes==0);
    b1sv_update(1,1);assert(writes==1);
    assert(psx_mod_read_word(0x80030590)==0x0800c175);
    assert(psx_mod_read_word(0x80030578)==0x10400018);
    assert(psx_mod_read_word(0x80030588)==0x04400014);
    b1sv_update(1,1);assert(writes==1);
    b1sv_update(0,1);assert(writes==2);
    assert(psx_mod_read_word(0x80030590)==0x0243001b);
    b1sv_update(1,1);b1sv_update(1,0);assert(writes==4);
    put(0x80030588,0);b1sv_update(1,1);assert(writes==4);
    native();put(0x80030590,0xdeadbeef);b1sv_update(1,1);assert(writes==4);
    native();put(0x80030590,0x0800c175);b1sv_update(0,1);assert(writes==4);
    native();b1sv_update(1,1);assert(writes==5);
    put(0x80030590,0xdeadbeef);b1sv_update(0,1);assert(writes==5);
    assert(psx_mod_read_word(0x80030590)==0xdeadbeef);
    return 0;
}
'''
        out = ROOT / '_work/stage_import/strike/visibility-tests'
        out.mkdir(parents=True, exist_ok=True)
        (out / 'visibility.c').write_text(harness)
        path = '/mnt/d/' + out.as_posix()[3:]
        subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', 'gcc', '-std=c11',
                        '-Wall', f'{path}/visibility.c', '-o',
                        f'{path}/visibility'], check=True)
        subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec',
                        f'{path}/visibility'], check=True)
