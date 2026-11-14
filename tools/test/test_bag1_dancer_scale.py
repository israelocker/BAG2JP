"""Exercise the actual runtime scale seam against bounded mock actor RAM."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class DancerScaleTest(unittest.TestCase):
    def test_gaso_native_relative_scale_is_uniform_guarded_and_applied_once(self):
        source = (ROOT / 'mods-src/bag2jp.feature.bag1-content/bag2jp_bag1_versions.c').read_text()
        block = source[source.index('#define B1V_SCALE_CUR'):source.index('static void b1v_dancer_leash')]
        harness = r'''
#include <assert.h>
#include <stdint.h>
#include <stdarg.h>
#define B1V_CHARS 19
#define B1V_DANCERS 0x8005F808u
#define B1V_SELECTED 0x80089250u
#define B1V_CHAR_MASK 31u
#define ACTOR0 0x80200000u
#define ACTOR1 0x80202000u
static uint32_t actors[2][0x1600/4], pointers[4] = {ACTOR0,0,ACTOR1,0};
static uint8_t selected[2] = {9,41};
static int b1v_version[19][2], b1v_force_stock;
static unsigned b1v_frame;
static uint32_t psx_mod_read_word(uint32_t a) {
 if(a>=B1V_DANCERS && a<B1V_DANCERS+16)return pointers[(a-B1V_DANCERS)/4];
 assert((a>=ACTOR0 && a<ACTOR0+0x1600)||(a>=ACTOR1 && a<ACTOR1+0x1600));
 return actors[a>=ACTOR1][(a-(a>=ACTOR1?ACTOR1:ACTOR0))/4];
}
static uint8_t psx_mod_read_byte(uint32_t a) {
 if(a>=B1V_SELECTED && a<B1V_SELECTED+2)return selected[a-B1V_SELECTED];
 assert(a==ACTOR0+4||a==ACTOR1+4);return actors[a>=ACTOR1][1];
}
static void psx_mod_write_word(uint32_t a,uint32_t v) {
 assert((a>=ACTOR0 && a<ACTOR0+0x1600)||(a>=ACTOR1 && a<ACTOR1+0x1600));
 actors[a>=ACTOR1][(a-(a>=ACTOR1?ACTOR1:ACTOR0))/4]=v;
}
static int b1v_has_alt(unsigned c){return c==1||c==9;}
static void b1v_log(const char *f,...){(void)f;}
'''
        scenario = r'''
static void seed(unsigned side, unsigned chr) {
 actors[side][1]=chr;
 for(unsigned k=0;k<3;k++) {
  actors[side][(B1V_SCALE_BASE+4*k)/4]=98;
  actors[side][(B1V_SCALE_CUR+4*k)/4]=98;
 }
}
int main(void) {
 seed(0,9);seed(1,9);b1v_version[9][0]=b1v_version[9][1]=1;
 b1v_dancer_scale();
 /* Native BAG1 Gas/Strike=116/127, anchored to corrected Strike scale82. */
 for(unsigned s=0;s<2;s++)for(unsigned k=0;k<3;k++) {
  assert(actors[s][(B1V_SCALE_BASE+4*k)/4]==75);
  assert(actors[s][(B1V_SCALE_CUR+4*k)/4]==75);
 }
 b1v_dancer_scale();assert(actors[0][B1V_SCALE_BASE/4]==75);
 seed(0,9);b1v_force_stock=1;b1v_dancer_scale();assert(actors[0][B1V_SCALE_BASE/4]==98);
 b1v_force_stock=0;b1v_version[9][0]=0;b1v_dancer_scale();assert(actors[0][B1V_SCALE_BASE/4]==98);
 seed(0,1);selected[0]=1;b1v_version[1][0]=1;b1v_dancer_scale();
 assert(actors[0][B1V_SCALE_BASE/4]==82); /* Existing Strike correction unchanged. */
 return 0;
}
'''
        with tempfile.TemporaryDirectory(dir=ROOT / '_work') as directory:
            path = Path(directory)
            (path / 'scale.c').write_text(harness + block + scenario, encoding='utf-8')
            linux = '/mnt/' + directory[0].lower() + directory[2:].replace('\\', '/')
            subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', 'gcc', '-std=c11',
                            '-Wall', '-Werror', linux + '/scale.c', '-o', linux + '/scale'], check=True)
            subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', linux + '/scale'], check=True)


if __name__ == '__main__':
    unittest.main()
