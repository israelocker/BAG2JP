"""Compile the attack-input seam and check all write guards."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class AttackFixtureTests(unittest.TestCase):
    def test_ordered_duel_stops_after_two_attacks_each(self):
        header = ROOT / 'mods-src/bag2jp.debug.anim-trace/bag2jp_attack_fixture.h'
        self.assertIn('bag2_ordered_duel_fixture_tick', header.read_text())
        out = ROOT / '_work/character_import/heat/ordered-duel-tests'
        out.mkdir(parents=True, exist_ok=True)
        source = '''#include <stdint.h>
#include <assert.h>
static unsigned writes, busy;
uint32_t psx_mod_read_word(uint32_t a) {
 switch(a) {
 case 0x8004E2D8:return 0x54535542; case 0x8004E2DC:return 0x4D5F415F;
 case 0x8005D3D4:return 19; case 0x8005D2C4:return 2; case 0x8005D3D8:return 1;
 case 0x8005D3DC:case 0x8005D3E0:return 3; case 0x8009B084:return 0xAC510020;
 case 0x8005E6A0:return 0; case 0x8005E6A4:return 1;
 default: assert(a==0x8005E754 || a==0x8005E786 || a==0x8005E748 || a==0x8005E77A);return busy;
 }
}
uint16_t psx_mod_read_half(uint32_t a){(void)a;return 0;}
void psx_mod_write_half(uint32_t a,uint16_t v){(void)a;(void)v;writes++;}
''' + f'#include "{header.as_posix()}"\n' + '''
int main(void){
 Bag2OrderedDuel state={0,0};
 assert(!bag2_ordered_duel_fixture_tick(0,0,0x8005CF08,100,&state));
 assert(!bag2_ordered_duel_fixture_tick(1,1,0x8005CF2C,100,&state));
 busy=1;assert(!bag2_ordered_duel_fixture_tick(1,0,0x8005CF08,100,&state));
 assert(state.count==0 && writes==0);busy=0;
 assert(bag2_ordered_duel_fixture_tick(1,0,0x8005CF08,100,&state));
 assert(state.count==1 && writes==3);
 assert(!bag2_ordered_duel_fixture_tick(1,0,0x8005CF08,579,&state));
 assert(bag2_ordered_duel_fixture_tick(1,0,0x8005CF08,580,&state));
 assert(state.count==2 && writes==6);
 assert(!bag2_ordered_duel_fixture_tick(1,0,0x8005CF08,1060,&state));
 assert(bag2_ordered_duel_fixture_tick(1,1,0x8005CF2C,1060,&state));
 assert(bag2_ordered_duel_fixture_tick(1,1,0x8005CF2C,1540,&state));
 assert(state.count==4 && writes==12);
 assert(!bag2_ordered_duel_fixture_tick(1,1,0x8005CF2C,3000,&state));
 assert(!bag2_ordered_duel_fixture_tick(1,0,0x8005CF08,3000,&state));
 assert(writes==12);return 0;
}
'''
        source = source.replace(header.as_posix(), '/mnt/d/' + header.as_posix()[3:])
        (out / 'test.c').write_text(source)
        linux = '/mnt/d/' + out.as_posix()[3:]
        prefix = ['wsl.exe', '-d', 'Ubuntu', '--exec']
        subprocess.run(prefix + ['gcc', '-Wall', '-Wextra', '-Werror', linux + '/test.c', '-o', linux + '/test'], check=True)
        subprocess.run(prefix + [linux + '/test'], check=True)

    def test_both_sides_keep_independent_attack_guards(self):
        header = ROOT / 'mods-src/bag2jp.debug.anim-trace/bag2jp_attack_fixture.h'
        out = ROOT / '_work/character_import/heat/duel-fixture-tests'
        out.mkdir(parents=True, exist_ok=True)
        source = '''#include <stdint.h>
#include <assert.h>
static unsigned side, writes, blocked;
uint32_t psx_mod_read_word(uint32_t a) {
 switch(a) {
 case 0x8004E2D8:return 0x54535542; case 0x8004E2DC:return 0x4D5F415F;
 case 0x8005D3D4:return 19; case 0x8005D2C4:return 2; case 0x8005D3D8:return 1;
 case 0x8005D3DC:case 0x8005D3E0:return 3; case 0x8009B084:return 0xAC510020;
 case 0x8005E6A0:return 0; case 0x8005E6A4:return 1;
 default: assert(a==0x8005E754+side*0x32 || a==0x8005E748+side*0x32);return blocked;
 }
}
uint16_t psx_mod_read_half(uint32_t a){(void)a;return 0;}
void psx_mod_write_half(uint32_t a,uint16_t v){
 uint32_t input=0x8005CF08+side*0x24;
 assert((a==input+8 && !v)||(a==input+12 && !v)||(a==input+20 && v==0x6e));writes++;
}
''' + f'#include "{header.as_posix()}"\n' + '''
int main(void){
 for(side=0;side<2;side++){
  uint32_t input=0x8005CF08+side*0x24;
  writes=0;blocked=1;assert(!bag2_side_attack_fixture_tick(1,side,input,side));assert(!writes);
  blocked=0;assert(!bag2_side_attack_fixture_tick(0,side,input,side));
  assert(!bag2_side_attack_fixture_tick(1,side,input,1-side));assert(!writes);
  assert(bag2_side_attack_fixture_tick(1,side,input,side));assert(writes==3);
 }
 assert(!bag2_side_attack_fixture_tick(1,2,0x8005CF50,0));
 return 0;
}
'''
        source = source.replace(header.as_posix(), '/mnt/d/' + header.as_posix()[3:])
        (out / 'test.c').write_text(source)
        linux = '/mnt/d/' + out.as_posix()[3:]
        prefix = ['wsl.exe', '-d', 'Ubuntu', '--exec']
        subprocess.run(prefix + ['gcc', '-Wall', '-Wextra', '-Werror', linux + '/test.c', '-o', linux + '/test'], check=True)
        subprocess.run(prefix + [linux + '/test'], check=True)

    def test_attack_input_and_guards(self):
        header = ROOT / 'mods-src/bag2jp.debug.anim-trace/bag2jp_attack_fixture.h'
        self.assertTrue(header.exists(), 'Attack fixture is not implemented')
        out = ROOT / '_work/character_import/strike/attack-hook-tests'
        out.mkdir(parents=True, exist_ok=True)
        source = '''#include <stdint.h>
#include <assert.h>
static int bad, writes;
static const uint32_t guards[][2] = {
 {0x8004E2D8,0x54535542}, {0x8004E2DC,0x4D5F415F},
 {0x8005D3D4,19}, {0x8005D2C4,2}, {0x8005D3D8,1},
 {0x8005D3DC,3}, {0x8005D3E0,3}, {0x8009B084,0xAC510020},
 {0x8005E6A0,1}, {0x8005E754,0xFF000000}, {0x8005E748,0x12340000}
};
uint32_t psx_mod_read_word(uint32_t a) {
 for(int i=0;i<11;i++) if(a==guards[i][0]) return guards[i][1]^(bad==i+1?1:0);
 assert(0);return 0;
}
uint16_t psx_mod_read_half(uint32_t a) { (void)a; assert(0); return 0; }
void psx_mod_write_half(uint32_t a,uint16_t v) {
 assert((a==0x8005CF1C && v==0x6e)||(a==0x8005CF14 && v==0)||(a==0x8005CF10 && v==0));writes++;
}
''' + f'#include "{header.as_posix()}"\n' + '''
int main(void) {
 for(bad=1;bad<=11;bad++){writes=0;assert(!bag2_attack_fixture_tick(1,0,0x8005CF08));assert(writes==0);}
 bad=0;assert(!bag2_attack_fixture_tick(0,0,0x8005CF08));
 assert(!bag2_attack_fixture_tick(1,1,0x8005CF08));
 assert(!bag2_attack_fixture_tick(1,0,0x8005CF2C));assert(writes==0);
 assert(bag2_attack_fixture_tick(1,0,0x8005CF08));assert(writes==3);
 writes=0;assert(!bag2_heat_attack_fixture_tick(1,0,0x8005CF08));assert(writes==0);
 return 0;
}
'''
        # WSL compiler needs a Linux include path.
        source = source.replace(header.as_posix(), '/mnt/d/' + header.as_posix()[3:])
        (out / 'test.c').write_text(source)
        linux = '/mnt/d/' + out.as_posix()[3:]
        prefix = ['wsl.exe', '-d', 'Ubuntu', '--exec']
        subprocess.run(prefix + ['gcc', '-Wall', '-Wextra', '-Werror', linux + '/test.c', '-o', linux + '/test'], check=True)
        subprocess.run(prefix + [linux + '/test'], check=True)

    def test_p2_defense_cleared_only_under_attack(self):
        header = ROOT / 'mods-src/bag2jp.debug.anim-trace/bag2jp_attack_fixture.h'
        out = ROOT / '_work/character_import/heat/defense-fixture-tests'
        out.mkdir(parents=True, exist_ok=True)
        source = '''#include <stdint.h>
#include <assert.h>
static int bad, writes; static uint16_t command = 0xaa;
static const uint32_t guards[][2] = {
 {0x8004E2D8,0x54535542}, {0x8004E2DC,0x4D5F415F},
 {0x8005D3D4,19}, {0x8005D2C4,2}, {0x8005D3D8,1},
 {0x8005D3DC,3}, {0x8005D3E0,3}, {0x8009B084,0xAC510020}, {0x8005E6A0,0}
};
uint32_t psx_mod_read_word(uint32_t a) {
 for(int i=0;i<9;i++) if(a==guards[i][0]) return guards[i][1]^(bad==i+1?1:0);
 assert(0);return 0;
}
uint16_t psx_mod_read_half(uint32_t a) { assert(a==0x8005CF40); return command; }
void psx_mod_write_half(uint32_t a,uint16_t v) { assert(a==0x8005CF40 && v==0); writes++; }
''' + f'#include "{header.as_posix()}"\n' + '''
int main(void) {
 for(bad=1;bad<=9;bad++){assert(!bag2_heat_defense_fixture_tick(1,1,0x8005CF2C,1));}
 bad=0; assert(writes==0);
 assert(!bag2_heat_defense_fixture_tick(0,1,0x8005CF2C,1));
 assert(!bag2_heat_defense_fixture_tick(1,0,0x8005CF2C,1));
 assert(!bag2_heat_defense_fixture_tick(1,1,0x8005CF08,1));
 assert(!bag2_heat_defense_fixture_tick(1,1,0x8005CF2C,0));
 command=0x12; assert(!bag2_heat_defense_fixture_tick(1,1,0x8005CF2C,1)); assert(writes==0);
 command=0xaa; assert(bag2_heat_defense_fixture_tick(1,1,0x8005CF2C,1)); assert(writes==1);
 command=0x6e; assert(bag2_heat_defense_fixture_tick(1,1,0x8005CF2C,1)); assert(writes==2);
 return 0;
}
'''
        source = source.replace(header.as_posix(), '/mnt/d/' + header.as_posix()[3:])
        (out / 'test.c').write_text(source)
        linux = '/mnt/d/' + out.as_posix()[3:]
        prefix = ['wsl.exe', '-d', 'Ubuntu', '--exec']
        subprocess.run(prefix + ['gcc', '-Wall', '-Wextra', '-Werror', linux + '/test.c', '-o', linux + '/test'], check=True)
        subprocess.run(prefix + [linux + '/test'], check=True)


if __name__ == '__main__':
    unittest.main()
