"""Exercise the real stage shim with host RAM, without media dependencies."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class StageShimTests(unittest.TestCase):
    def test_audited_stage_ids_receive_flags_and_level(self):
        source = (ROOT / 'mods-src/bag2jp.feature.bag1-content/bag2jp_bag1_stage.c').read_text()
        shim = source[source.index('#define B1S_SHIM'):source.index('/* ---- song audio ---- */')]
        out = ROOT / '_work/stage_import/strike/shim-tests'
        out.mkdir(parents=True, exist_ok=True)
        harness = '''#include <stdint.h>
#include <assert.h>
#include <string.h>
static uint8_t ram[0x800000];
#define RAM(a) (ram+((a)&0x7fffff))
uint8_t psx_mod_read_byte(uint32_t a) { return *RAM(a); }
uint16_t psx_mod_read_half(uint32_t a) { uint16_t v; memcpy(&v,RAM(a),2); return v; }
uint32_t psx_mod_read_word(uint32_t a) { uint32_t v; memcpy(&v,RAM(a),4); return v; }
void psx_mod_write_byte(uint32_t a,uint8_t v) { *RAM(a)=v; }
void psx_mod_write_word(uint32_t a,uint32_t v) { memcpy(RAM(a),&v,4); }
void half(uint32_t a,uint16_t v) { memcpy(RAM(a),&v,2); }
''' + shim + '''
int main(void) {
  for (unsigned id=0;id<3;id++) {
    memset(ram,0,sizeof ram); b1s_vblank();
    psx_mod_write_word(B1S_SHIM,B1S_MAGIC);
    psx_mod_write_word(0x80089200,0x80200000);
    psx_mod_write_byte(0x80200000,id);
    half(0x8005e2e8,256); half(0x8005e658,100);
    half(0x8005e2d0,1); psx_mod_write_word(0x8005e6f8,20000);
    b1s_vblank();
    half(0x8005e2d0,2); half(0x8005e684,2); b1s_vblank();
    assert(psx_mod_read_byte(B1S_SHIM+8)==(id<2?2:0));
    assert(psx_mod_read_word(B1S_SHIM+4)==(id<2?0x11:0));
    assert(psx_mod_read_byte(B1S_SHIM+9)==0);
  }
  return 0;
}
'''
        (out / 'shim.c').write_text(harness)
        path = '/mnt/d/' + out.as_posix()[3:]
        subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', 'gcc', '-std=c11', '-Wall',
                        '-Werror', f'{path}/shim.c', '-o', f'{path}/shim'], check=True)
        subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', f'{path}/shim'], check=True)
