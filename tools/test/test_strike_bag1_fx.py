"""Exercise Strike's native shot/particle timing without a game process."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HEADER = ROOT / 'mods-src/bag2jp.feature.bag1-content/bag2jp_strike_bag1_fx.h'


def wsl_path(path: Path) -> str:
    """Convert an absolute project path to the verified WSL mount."""
    return '/mnt/d/' + path.as_posix()[3:]


class StrikeNativeEffectTests(unittest.TestCase):
    def test_native_renderer_is_wired_once(self) -> None:
        """The live callback must replace, not layer over, the approximate effect."""
        source = (HEADER.parent / 'bag2jp_bag1_versions.c').read_text()
        self.assertIn('#include "bag2jp_strike_bag1_draw.h"', source)
        self.assertEqual(source.count('bag2jp_strike_bag1_tick(b1v_frame);'), 1)
        self.assertNotIn('bag2jp_strike_shot_tick(b1v_frame);', source)

    def test_runtime_rendering(self) -> None:
        """Exercise native FT4 emission, five double shots and match/version/pause guards."""
        plugin = HEADER.parent
        out = ROOT / '_work/strikedbi/runtime-tests'
        out.mkdir(parents=True, exist_ok=True)
        source = r'''#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
static uint8_t ram[0x800000];
#define P(a) (ram + ((a)&0x7fffff))
uint8_t psx_mod_read_byte(uint32_t a) { return *P(a); }
uint16_t psx_mod_read_half(uint32_t a) { uint16_t v; memcpy(&v,P(a),2); return v; }
uint32_t psx_mod_read_word(uint32_t a) { uint32_t v; memcpy(&v,P(a),4); return v; }
void psx_mod_write_word(uint32_t a,uint32_t v) { memcpy(P(a),&v,4); }
#define W(a,v) psx_mod_write_word(a,(uint32_t)(v))
static int version=1;
int bag2jp_bag1_get_version(int chr,int side) { return chr==1 && side==0 && version; }
void b1v_log(const char* fmt,...) { (void)fmt; }
#include "PLUGIN/bag2jp_strike_shot.h"
#include "PLUGIN/bag2jp_heat_flame.h"
#include "PLUGIN/bag2jp_strike_bag1_draw.h"
static void identity(uint32_t p) {
    int16_t r[9]={4096,0,0,0,4096,0,0,0,4096}; memcpy(P(p),r,sizeof(r));
}
static void next_ot(unsigned frame) {
    uint32_t ot=frame&1 ? 0x80250000u : 0x80260000u;
    for (unsigned i=0;i<4096;++i) W(ot+i*4,0xffffff);
    W(B2_OT_ADDR,ot); W(B2_HEAP_ADDR,0x80300000);
}
int main(void) {
    assert(bag2jp_strike_bag1_tick(1)==0);
    W(B2_ROOT_ADDR,19); W(B2_MODE_ADDR,2); W(B2_PHASE1_ADDR,1);
    W(B2_PHASE2_ADDR,3); W(B2_PHASE3_ADDR,3);
    W(B2_CHAR_P1_ADDR,1); W(B2_CHAR_P2_ADDR,0);
    uint32_t d=0x80100000, o=0x80120000, bones=0x80140000, desc=0x80180000, stage=0x80190000;
    W(B2_DANCER_BASE,d); W(B2_DANCER_BASE+8,o); W(d+STRIKE_B1_BONES_OFF,bones);
    identity(B2_CAM_ROT_ADDR); W(B2_CAM_ROT_ADDR+0x1c,6000);
    identity(d+B2_DANCER_MTX_OFF); identity(o+B2_DANCER_MTX_OFF);
    W(d+B2_DANCER_MTX_OFF+0x14,2000);
    identity(stage+STRIKE_B1_STAGE_MATRIX); W(STRIKE_B1_STAGE_PTR,stage);
    for (unsigned bone=26;bone<28;++bone) {
        uint32_t m=bones+bone*STRIKE_B1_BONE_STRIDE+STRIKE_B1_BONE_MATRIX;
        identity(m); W(m+0x18,4000);
    }
    /* FUN_80031DAC's table is [side*19 + character], not just [side*19]. */
    W(B2_GEOM_H_ADDR,384); W(B2_DT_ADDR,2); W(0x80053548u,desc);
    W(desc+0x44,0x003c003d); W(d+0x154c,74); W(o+0x810,500);
    for (unsigned f=1;f<=46;++f) {
        next_ot(f); W(d+0x1554,f);
        int n=bag2jp_strike_bag1_tick(f);
        if(f==26) {
            assert(n==2);
            assert(psx_mod_read_word(0x80300004)==0x2e808080);
            assert(psx_mod_read_half(0x8030000e)==0x3d);
            assert(psx_mod_read_half(0x80300016)==0x3c);
            assert(psx_mod_read_byte(0x8030001c)==0xc0);
            /* FUN_8002C404 temporarily composes the dancer into the camera for DBI callbacks.
             * Vblank must reproduce that actor frame: 256 + 2000*384/6000*.85 - 6 = 358. */
            assert(psx_mod_read_half(0x80300008)==358);
            assert(bag2jp_strike_bag1_tick(f)==0);
        }
    }
    assert(s_strike_b1_fx[0].next_shot==10);
    int before=s_strike_b1_fx[0].shots[8].life;
    W(B2_PAUSE_ADDR,1); next_ot(47); bag2jp_strike_bag1_tick(47);
    assert(s_strike_b1_fx[0].shots[8].life==before);
    W(B2_PAUSE_ADDR,0); version=0; next_ot(48);
    assert(bag2jp_strike_bag1_tick(48)==0 && !strike_b1_any_active(&s_strike_b1_fx[0]));
    W(B2_ROOT_ADDR,0); assert(bag2jp_strike_bag1_tick(49)==0);
    assert(s_strike_b1_last_ot==0);
    puts("Strike runtime guards and FT4 passed");
    return 0;
}
'''.replace('PLUGIN', wsl_path(plugin))
        (out / 'test.c').write_text(source)
        prefix = ['wsl.exe', '-d', 'Ubuntu', '--exec']
        subprocess.run(prefix + ['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                                '-Wno-unused-function', '-fsanitize=undefined',
                                wsl_path(out / 'test.c'), '-o', wsl_path(out / 'test')], check=True)
        subprocess.run(prefix + [wsl_path(out / 'test')], check=True)

    def test_native_lifecycle(self) -> None:
        """Native beams last three draws; delayed impacts emit three four-frame particles."""
        self.assertTrue(HEADER.exists(), 'Native Strike effect module missing')
        out = ROOT / '_work/strikedbi/effect-tests'
        out.mkdir(parents=True, exist_ok=True)
        source = r'''#include <assert.h>
#include <stdio.h>
#include "HEADER"
int main(void) {
    StrikeB1Fx fx = {0};
    StrikeB1Vec a = {10,20,30}, b = {40,50,60}, target = {300,1000,-100};
    strike_b1_spawn(&fx, &a, &b, &target, 1);
    assert(fx.shots[0].state == 1 && fx.shots[0].life == 20);
    strike_b1_update_shots(&fx, 0);
    assert(fx.shots[0].count == 0 && fx.shots[0].life == 20);
    for (int i=0; i<3; ++i) {
        assert(fx.shots[0].state == 1 && fx.shots[0].count == i);
        strike_b1_update_shots(&fx, 2);
    }
    assert(fx.shots[0].state == 2 && fx.shots[0].life == 14);
    for (int i=0; i<6; ++i) strike_b1_update_shots(&fx, 2);
    assert(fx.shots[0].life == 2 && fx.particles[0].active == 0);
    strike_b1_update_shots(&fx, 2);
    assert(!fx.shots[0].state);
    int n=0;
    for (int i=0; i<40; ++i) n += fx.particles[i].active != 0;
    assert(n==3);
    assert(fx.particles[0].pos.y == 100 && fx.particles[1].pos.y == 100);
    assert(fx.particles[2].pos.y >= 744*4096 && fx.particles[2].pos.y < 1256*4096);
    int x=fx.particles[0].pos.x, vx=fx.particles[0].vel.x;
    strike_b1_update_particles(&fx, 0);
    assert(fx.particles[0].frame == 0);
    strike_b1_update_particles(&fx, 2);
    assert(fx.particles[0].frame == 1 && fx.particles[0].pos.x == x+2*vx);
    for (int i=0; i<3; ++i) strike_b1_update_particles(&fx, 2);
    assert(!strike_b1_any_active(&fx));

    /* Non-impact shots never emit dust; ring wrap remains bounded. */
    for (int i=0; i<25; ++i) strike_b1_spawn(&fx, &a, &b, &target, 0);
    assert(fx.next_shot == 6);
    strike_b1_update_shots(&fx, 20);
    assert(!strike_b1_any_active(&fx));

    /* Crossings reproduce all five events, even if animation frames are skipped. */
    assert(strike_b1_crossings(25, 26) == 1);
    assert(strike_b1_crossings(26, 26) == 0);
    assert(strike_b1_crossings(26, 36) == 6);
    assert(strike_b1_crossings(0, 58) == 31);
    puts("Strike native lifecycle passed");
    return 0;
}
'''.replace('HEADER', wsl_path(HEADER))
        (out / 'test.c').write_text(source)
        prefix = ['wsl.exe', '-d', 'Ubuntu', '--exec']
        subprocess.run(prefix + ['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                                '-fsanitize=undefined', wsl_path(out / 'test.c'),
                                '-o', wsl_path(out / 'test')], check=True)
        subprocess.run(prefix + [wsl_path(out / 'test')], check=True)


if __name__ == '__main__':
    unittest.main()
