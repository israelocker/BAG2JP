"""Actor-only native lighting contract; retain stage, rival and timed light transitions."""
import subprocess
import struct
import tomllib
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class StrikeLightingTests(unittest.TestCase):
    def test_native_lighting_is_disabled_per_owner_decision(self):
        """Owner discarded native lighting due to visual clashes with stage lighting."""
        config = tomllib.loads((ROOT / 'patches/BAG2JP-game.toml').read_text())
        self.assertNotIn('0x8002C404', config['recompiler'].get('mod_function_entry_funcs', []),
                         'Native Strike lighting should not be opted into codegen')
        source = (ROOT / 'mods-src/bag2jp.feature.bag1-content/bag2jp_bag1_versions.c').read_text()
        self.assertNotIn('b1v_strike_lighting', source,
                         'Native Strike lighting callback should not be registered')

    def test_actor_lighting_guards(self):
        header = ROOT / 'mods-src/bag2jp.feature.bag1-content/bag2jp_strike_lighting.h'
        out = ROOT / '_work/character_import/strike/lighting-tests'
        out.mkdir(parents=True, exist_ok=True)
        source = r'''
#include <stdint.h>
#include <string.h>
#include <assert.h>
static unsigned char ram[0x800000];
static int versions[2] = {1,1};
uint32_t psx_mod_read_word(uint32_t a) {uint32_t v; memcpy(&v,ram+(a&0x7fffff),4); return v;}
void psx_mod_write_half(uint32_t a,uint16_t v) {memcpy(ram+(a&0x7fffff),&v,2);}
void psx_mod_write_word(uint32_t a,uint32_t v) {memcpy(ram+(a&0x7fffff),&v,4);}
int bag2jp_bag1_get_version(int c,int s) {return c==1&&versions[s];}
#include "HEADER"
int main(void) {
 const uint32_t a=0x80200000,b=0x80208000;
 psx_mod_write_word(0x8005D3D4,19); psx_mod_write_word(0x8005D2C4,2);
 psx_mod_write_word(0x8005D3D8,1); psx_mod_write_word(0x8005D3DC,3); psx_mod_write_word(0x8005D3E0,3);
 psx_mod_write_word(0x8005F808,a); psx_mod_write_word(0x8005F810,b);
 psx_mod_write_word(0x8005E6A0,1); psx_mod_write_word(0x8005E6A4,0);
 psx_mod_write_word(b+0x159C,0x11223344); psx_mod_write_word(0x8005F3D4,0x55667788);
 assert(bag2jp_strike_lighting_apply()==1);
 assert((int16_t)psx_mod_read_word(a+0x157C)==-2816);
 assert((int16_t)psx_mod_read_word(a+0x155C)==-1099);
 assert(psx_mod_read_word(a+0x159C)==0x00A8A8A8);
 assert(psx_mod_read_word(b+0x159C)==0x11223344);
 assert(psx_mod_read_word(0x8005F3D4)==0x55667788);
 for(int side=0;side<2;side++) for(int costume=0;costume<2;costume++) {
  psx_mod_write_word(0x8005E6A0+side*4,1);
  psx_mod_write_word((side?b:a)+4,(unsigned)costume<<16);
  assert(bag2jp_strike_lighting_apply()>=1);
  assert(psx_mod_read_word((side?b:a)+0x159C)==0x00A8A8A8);
 }
 versions[0]=versions[1]=0; assert(bag2jp_strike_lighting_apply()==0);
 versions[0]=versions[1]=1;
 for(int i=0;i<3;i++) {
  uint32_t counter=0x8005F2CC+i*0x10;
  /* Direction/color/ambient counters are at CC/DC/FC, not an evenly spaced tuple. */
  if(i==2)counter=0x8005F2FC;
  psx_mod_write_word(counter,1); psx_mod_write_word(counter+4,1);
  assert(bag2jp_strike_lighting_apply()==0);
  psx_mod_write_word(counter,0); psx_mod_write_word(counter+4,0);
 }
 psx_mod_write_word(0x8005D3D4,20); assert(bag2jp_strike_lighting_apply()==0);
 psx_mod_write_word(0x8005D3D4,19); psx_mod_write_word(0x8005D3DC,4);
 assert(bag2jp_strike_lighting_apply()==0);
 psx_mod_write_word(0x8005D3DC,3); psx_mod_write_word(0x8005F808,0);
 psx_mod_write_word(0x8005F810,0); assert(bag2jp_strike_lighting_apply()==0);
 return 0;
}
'''.replace('HEADER', '/mnt/d/' + header.as_posix()[3:])
        c = out / 'test.c'
        c.write_text(source)
        linux = '/mnt/d/' + c.as_posix()[3:]
        subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', 'gcc', '-std=c11', '-Wall', '-Wextra',
                        '-Werror', '-fsanitize=undefined', linux, '-o', linux + '.bin'], check=True)
        subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', linux + '.bin'], check=True)


if __name__ == '__main__':
    unittest.main()
