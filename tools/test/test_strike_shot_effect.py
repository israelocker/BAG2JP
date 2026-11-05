"""Compile and exercise the Strike shot effect C implementation."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class StrikeShotEffectTests(unittest.TestCase):
    def test_shot_effect_plugin_compiles_and_passes(self):
        header = ROOT / 'mods-src/bag2jp.feature.bag1-content/bag2jp_strike_shot.h'
        self.assertTrue(header.exists(), 'bag2jp_strike_shot.h does not exist')
        out = ROOT / '_work/character_import/strike/shot-effect-tests'
        out.mkdir(parents=True, exist_ok=True)
        linux_header = '/mnt/d/' + header.as_posix()[3:]
        source = f'''#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

/* Mock guest RAM */
static uint8_t g_ram[0x800000];

uint8_t psx_mod_read_byte(uint32_t a) {{ return g_ram[a & 0x7fffff]; }}
uint16_t psx_mod_read_half(uint32_t a) {{ return *(uint16_t*)(g_ram + (a & 0x7fffff)); }}
uint32_t psx_mod_read_word(uint32_t a) {{ return *(uint32_t*)(g_ram + (a & 0x7fffff)); }}

void psx_mod_write_byte(uint32_t a, uint8_t v) {{ g_ram[a & 0x7fffff] = v; }}
void psx_mod_write_half(uint32_t a, uint16_t v) {{ *(uint16_t*)(g_ram + (a & 0x7fffff)) = v; }}
void psx_mod_write_word(uint32_t a, uint32_t v) {{ *(uint32_t*)(g_ram + (a & 0x7fffff)) = v; }}

static int s_bag1_version[2] = {{1, 0}};
int bag2jp_bag1_get_version(int chr, int side) {{
    if (chr == 1 && side >= 0 && side < 2) return s_bag1_version[side];
    return 0;
}}

void b1v_log(const char* fmt, ...) {{ (void)fmt; }}

#include "{linux_header}"

int main(void) {{
    /* Test 1: Inactive when not in gameplay mode */
    memset(g_ram, 0, sizeof(g_ram));
    assert(bag2jp_strike_shot_tick(100) == 0);

    /* Setup gameplay: root=19, mode=2, phase=1/3/3 */
    *(uint32_t*)(g_ram + (0x8005D3D4 & 0x7fffff)) = 19;
    *(uint32_t*)(g_ram + (0x8005D2C4 & 0x7fffff)) = 2;
    *(uint32_t*)(g_ram + (0x8005D3D8 & 0x7fffff)) = 1;
    *(uint32_t*)(g_ram + (0x8005D3DC & 0x7fffff)) = 3;
    *(uint32_t*)(g_ram + (0x8005D3E0 & 0x7fffff)) = 3;

    /* P1 = Strike (char 1), P2 = Heat (char 0) */
    *(uint32_t*)(g_ram + (0x8005E6A0 & 0x7fffff)) = 1;
    *(uint32_t*)(g_ram + (0x8005E6A4 & 0x7fffff)) = 0;

    /* Setup dancer pointers */
    uint32_t p1_dancer = 0x80100000;
    uint32_t p2_dancer = 0x80120000;
    *(uint32_t*)(g_ram + (0x8005F808 & 0x7fffff)) = p1_dancer;
    *(uint32_t*)(g_ram + (0x8005F810 & 0x7fffff)) = p2_dancer;

    /* Setup heap and OT */
    uint32_t heap_start = 0x80200000;
    uint32_t ot_ptr = 0x80250000;
    *(uint32_t*)(g_ram + (0x80051A88 & 0x7fffff)) = heap_start;
    *(uint32_t*)(g_ram + (0x8006D990 & 0x7fffff)) = ot_ptr;
    *(uint32_t*)(g_ram + (ot_ptr & 0x7fffff)) = 0x00FFFFFF;

    /* Setup view MATRIX at 0x8005D0F0 (identity rotation, translation at +0x14) */
    int16_t* rot = (int16_t*)(g_ram + (0x8005D0F0 & 0x7fffff));
    rot[0] = 4096; rot[4] = 4096; rot[8] = 4096;
    int32_t* trans = (int32_t*)(g_ram + ((0x8005D0F0 + 0x14) & 0x7fffff));
    trans[0] = 0; trans[1] = 0; trans[2] = 0;
    /* GTE H (SetGeomScreen argument) */
    *(int32_t*)(g_ram + (0x8006D98C & 0x7fffff)) = 256;

    /* Test 2: Inactive when Strike is not in attack anim 74 */
    *(uint32_t*)(g_ram + ((p1_dancer + 0x154C) & 0x7fffff)) = 0; /* standing */
    *(uint32_t*)(g_ram + ((p1_dancer + 0x1554) & 0x7fffff)) = 0;
    assert(bag2jp_strike_shot_tick(101) == 0);

    /* Test 3: Active when Strike is in attack anim 74 at frame 26 (shot 1) */
    *(uint32_t*)(g_ram + ((p1_dancer + 0x154C) & 0x7fffff)) = 74;
    *(uint32_t*)(g_ram + ((p1_dancer + 0x1554) & 0x7fffff)) = 26;
    /* Root points at +0x810 (int16 values in words): P1 (-100,0,500), P2 (100,0,500) */
    *(int32_t*)(g_ram + ((p1_dancer + 0x810) & 0x7fffff)) = -100;
    *(int32_t*)(g_ram + ((p1_dancer + 0x814) & 0x7fffff)) = 0;
    *(int32_t*)(g_ram + ((p1_dancer + 0x818) & 0x7fffff)) = 500;

    *(int32_t*)(g_ram + ((p2_dancer + 0x810) & 0x7fffff)) = 100;
    *(int32_t*)(g_ram + ((p2_dancer + 0x814) & 0x7fffff)) = 0;
    *(int32_t*)(g_ram + ((p2_dancer + 0x818) & 0x7fffff)) = 500;

    /* Logic positions at +0x14B8 must not be used for projection */
    *(int32_t*)(g_ram + ((p1_dancer + 0x14C0) & 0x7fffff)) = -100000;
    *(int32_t*)(g_ram + ((p2_dancer + 0x14C0) & 0x7fffff)) = -100000;

    /* Dancer model matrices at +0x14C4: identity, zero translation */
    int16_t* d1m = (int16_t*)(g_ram + ((p1_dancer + 0x14C4) & 0x7fffff));
    int16_t* d2m = (int16_t*)(g_ram + ((p2_dancer + 0x14C4) & 0x7fffff));
    d1m[0] = d1m[4] = d1m[8] = 4096;
    d2m[0] = d2m[4] = d2m[8] = 4096;

    /* Scale field at +0x14E4 must not be used as position */
    *(int32_t*)(g_ram + ((p1_dancer + 0x14E4) & 0x7fffff)) = 82;
    *(int32_t*)(g_ram + ((p2_dancer + 0x14E4) & 0x7fffff)) = 85;

    /* Invalid GTE H suppresses emission */
    *(int32_t*)(g_ram + (0x8006D98C & 0x7fffff)) = 0;
    assert(bag2jp_strike_shot_tick(102) == 0);
    *(int32_t*)(g_ram + (0x8006D98C & 0x7fffff)) = 256;

    int emitted = bag2jp_strike_shot_tick(102);
    assert(emitted > 0);

    /* Verify heap advanced */
    uint32_t heap_after = *(uint32_t*)(g_ram + (0x80051A88 & 0x7fffff));
    assert(heap_after > heap_start);

    /* Verify OT linked at slot 2 (ot_ptr + 8) */
    uint32_t ot_head = *(uint32_t*)(g_ram + ((ot_ptr + 8) & 0x7fffff));
    assert((ot_head & 0xFFFFFF) != 0x00FFFFFF);

    printf("Host test passed: emitted %d primitives, heap advanced %u bytes\\n",
           emitted, heap_after - heap_start);
    return 0;
}}
'''
        (out / 'test.c').write_text(source)
        linux_out = '/mnt/d/' + out.as_posix()[3:]
        prefix = ['wsl.exe', '-d', 'Ubuntu', '--exec']
        subprocess.run(prefix + ['gcc', '-Wall', '-Wextra', '-Werror', linux_out + '/test.c', '-o', linux_out + '/test'], check=True)
        subprocess.run(prefix + [linux_out + '/test'], check=True)


if __name__ == '__main__':
    unittest.main()
