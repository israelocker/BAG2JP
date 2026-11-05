"""Compile and exercise the ported BAG1 Heat flame attack effect."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / 'mods-src/bag2jp.feature.bag1-content'


def wsl_path(path: Path) -> str:
    return '/mnt/d/' + path.as_posix()[3:]


class HeatFlameEffectTests(unittest.TestCase):
    def test_heat_flame_effect_compiles_and_follows_bag1_lifecycle(self):
        header = PLUGIN / 'bag2jp_heat_flame.h'
        self.assertTrue(header.exists(), 'bag2jp_heat_flame.h does not exist')
        out = ROOT / '_work/character_import/heat/flame-effect-tests'
        out.mkdir(parents=True, exist_ok=True)
        source = f'''#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>

static uint8_t g_ram[0x800000];
#define RAM(a) (g_ram + ((a) & 0x7fffff))
uint8_t psx_mod_read_byte(uint32_t a) {{ return *RAM(a); }}
uint16_t psx_mod_read_half(uint32_t a) {{ return *(uint16_t*)RAM(a); }}
uint32_t psx_mod_read_word(uint32_t a) {{ return *(uint32_t*)RAM(a); }}
void psx_mod_write_byte(uint32_t a, uint8_t v) {{ *RAM(a) = v; }}
void psx_mod_write_half(uint32_t a, uint16_t v) {{ *(uint16_t*)RAM(a) = v; }}
void psx_mod_write_word(uint32_t a, uint32_t v) {{ *(uint32_t*)RAM(a) = v; }}
#define W32(a, v) (*(uint32_t*)RAM(a) = (uint32_t)(v))

static int s_bag1_heat[2] = {{1, 0}};
int bag2jp_bag1_get_version(int chr, int side) {{ return chr == 0 ? s_bag1_heat[side] : 0; }}
void b1v_log(const char* fmt, ...) {{ (void)fmt; }}

#include "{wsl_path(PLUGIN / 'bag2jp_strike_shot.h')}"
#include "{wsl_path(PLUGIN / 'bag2jp_heat_flame.h')}"

static uint32_t ot_a = 0x80250000u, ot_b = 0x80260000u;

static void clear_ot(uint32_t ot) {{
    for (uint32_t i = 0; i < 0x1000u; ++i) W32(ot + i * 4u, 0x00FFFFFFu);
}}

/* Count POLY_FT4 (code 0x2E) primitives reachable from every OT entry. */
static int count_ft4(uint32_t ot, uint16_t* tpage, uint16_t* clut) {{
    int n = 0;
    for (uint32_t i = 0; i < 0x1000u; ++i) {{
        uint32_t p = psx_mod_read_word(ot + i * 4u) & 0xFFFFFFu;
        while (p != 0xFFFFFFu) {{
            uint32_t a = 0x80000000u | p;
            if ((psx_mod_read_word(a + 4u) >> 24) == 0x2Eu) {{
                ++n;
                *clut = (uint16_t)(psx_mod_read_word(a + 12u) >> 16);
                *tpage = (uint16_t)(psx_mod_read_word(a + 20u) >> 16);
            }}
            p = psx_mod_read_word(a) & 0xFFFFFFu;
        }}
    }}
    return n;
}}

int main(void) {{
    /* Pure lifecycle: one flame (life 50) ends with one ring and 24 particles, then everything expires. */
    HeatFxState fx;
    memset(&fx, 0, sizeof(fx));
    HeatVec3 start = {{-300, 0, 0}}, target = {{300, 0, 0}};
    heat_fx_spawn(&fx, &start, &target, 16, 50);
    assert(fx.flames[0].active && fx.flames[0].state == 0);
    int saw_ring = 0, max_particles = 0;
    for (int t = 0; t < 400; ++t) {{
        heat_fx_update(&fx, 1);
        int parts = 0;
        for (int i = 0; i < HEAT_PARTICLE_COUNT; ++i) parts += fx.particles[i].active != 0;
        if (parts > max_particles) max_particles = parts;
        for (int i = 0; i < HEAT_RING_COUNT; ++i) saw_ring |= fx.rings[i].active != 0;
    }}
    assert(saw_ring);
    assert(max_particles == 24);
    assert(!heat_fx_any_active(&fx));

    /* Paused or dt 0 does not advance the simulation. */
    memset(&fx, 0, sizeof(fx));
    heat_fx_spawn(&fx, &start, &target, 16, 50);
    heat_fx_update(&fx, 0);
    assert(fx.flames[0].timer == 12);

    /* Runtime: guards, spawn on anim 74 for a BAG1 Heat side, once-per-OT emission. */
    memset(g_ram, 0, sizeof(g_ram));
    assert(bag2jp_heat_flame_tick(1) == 0);
    W32(0x8005D3D4u, 19); W32(0x8005D2C4u, 2);
    W32(0x8005D3D8u, 1); W32(0x8005D3DCu, 3); W32(0x8005D3E0u, 3);
    W32(0x8005E6A0u, 0); W32(0x8005E6A4u, 1);
    uint32_t d1 = 0x80100000u, d2 = 0x80120000u;
    W32(0x8005F808u, d1); W32(0x8005F810u, d2);
    int16_t* m1 = (int16_t*)RAM(d1 + 0x14C4u); m1[0] = m1[4] = m1[8] = 4096;
    int16_t* m2 = (int16_t*)RAM(d2 + 0x14C4u); m2[0] = m2[4] = m2[8] = 4096;
    W32(d1 + 0x810u, -300); W32(d2 + 0x810u, 300);
    int16_t* cam = (int16_t*)RAM(0x8005D0F0u); cam[0] = 4096; cam[4] = -4096; cam[8] = 4096;
    W32(0x8005D0F0u + 0x1Cu, 6000);
    W32(0x8006D98Cu, 512);
    W32(0x8006D994u, 1);
    W32(0x80051A88u, 0x80200000u);
    uint32_t desc = 0x80180000u;
    W32(0x80053544u, desc);
    *(uint16_t*)RAM(desc + 0x44u) = 0x7F30u;
    *(uint16_t*)RAM(desc + 0x46u) = 0x004Cu;
    clear_ot(ot_a); clear_ot(ot_b);
    W32(0x8006D990u, ot_a);

    W32(d1 + 0x154Cu, 0); W32(d1 + 0x1554u, 0);
    assert(bag2jp_heat_flame_tick(2) == 0);

    W32(d1 + 0x154Cu, 74); W32(d1 + 0x1554u, 1);
    int emitted = bag2jp_heat_flame_tick(3);
    assert(emitted > 0);
    uint16_t tpage = 0, clut = 0;
    assert(count_ft4(ot_a, &tpage, &clut) == emitted);
    assert(tpage == ((0x004Cu & 0xFF9Fu) | 0x20u));
    assert(clut == 0x7F30u);

    /* Same OT buffer: no second emission or step. */
    assert(bag2jp_heat_flame_tick(4) == 0);

    /* BAG2 Heat side never spawns. */
    s_bag1_heat[0] = 0;
    W32(0x8006D990u, ot_b);
    bag2jp_heat_flame_reset();
    assert(bag2jp_heat_flame_tick(5) == 0);

    printf("Heat flame host test passed: emitted %d primitives\\n", emitted);
    return 0;
}}
'''
        (out / 'test.c').write_text(source)
        prefix = ['wsl.exe', '-d', 'Ubuntu', '--exec']
        subprocess.run(prefix + ['gcc', '-Wall', '-Wextra', '-Werror', '-Wno-unused-function', wsl_path(out / 'test.c'),
                                 '-o', wsl_path(out / 'test')], check=True)
        subprocess.run(prefix + [wsl_path(out / 'test')], check=True)


if __name__ == '__main__':
    unittest.main()
