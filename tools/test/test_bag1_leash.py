"""Exercise the BAG1 leash proportion and check its addresses against SLPM_862.19."""
from pathlib import Path
import subprocess
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[2]


def linux_path(path: Path) -> str:
    """Translate canonical Windows paths for the recorded WSL gcc harness."""
    return '/mnt/' + path.drive[0].lower() + path.as_posix()[2:]


class Bag1LeashTest(unittest.TestCase):
    def test_widened_homes_preserve_existing_tight_radius(self) -> None:
        self.run_harness('wide-radius')

    def run_harness(self, *arguments: str) -> None:
        """Compile real leash/centering code against synthetic control RAM."""
        with tempfile.TemporaryDirectory(dir=ROOT / '_work') as folder:
            binary = Path(folder) / 'leash'
            subprocess.run([
                'wsl.exe', '-d', 'Ubuntu', '--exec', 'gcc', '-std=c11',
                '-Wall', '-Wextra', '-Werror',
                '-I' + linux_path(ROOT / 'mods-src/bag2jp.feature.bag1-content'),
                linux_path(ROOT / 'tools/test/bag1_leash_harness.c'), '-o', linux_path(binary),
            ], check=True, capture_output=True, text=True)
            result = subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', linux_path(binary), *arguments],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_radius_follows_bag1_proportion_only_for_given_slot(self) -> None:
        self.run_harness()

    def test_measured_final_poses_converge_without_changing_y_or_radius(self) -> None:
        self.run_harness('center')

    def test_center_refuses_special_phases_clips_pause_and_unknown_actors(self) -> None:
        self.run_harness('exclusions')

    def test_center_resumes_after_guest_restore_despite_stale_radius_cache(self) -> None:
        self.run_harness('restore')

    def test_center_step_rounding_and_cap_at_signed_boundaries(self) -> None:
        self.run_harness('steps')

    def test_dance_centering_pulls_gently_with_deadzone_and_excludes_attacks(self) -> None:
        self.run_harness('dance')

    def test_center_callback_only_dispatches_selected_bag1_main_actor(self) -> None:
        """Compile the production version selection and callback, not a copied guard."""
        source = (ROOT / 'mods-src/bag2jp.feature.bag1-content/bag2jp_bag1_versions.c').read_text()
        selection = source[source.index('static uint32_t b1v_bag1_dancer('):
                           source.index('static void b1v_dancer_scale(')]
        callback = source[source.index('static void b1v_end_center_hook('):
                          source.index('static void b1v_activate(')]
        prefix = r'''
#include <assert.h>
#include <stdint.h>
#include <string.h>
#define B1V_CHARS 18
#define B1V_DANCERS 0x8005F808u
#define B1V_SELECTED 0x80089250u
#define B1V_CHAR_MASK 31u
#define B1CENTER_SITE 0x8002D818u
#define B1LEASH_CTL 0x8005F820u
#define B1LEASH_CTL_STRIDE 0x4Cu
#define B1LEASH_RAM_LOW 0x80010000u
#define B1LEASH_RAM_END 0x80800000u
#define B1CENTER_ACTOR_SIZE 0x155Cu
struct CPUState { uint32_t gpr[32]; };
static int b1v_active = 1, b1v_force_stock, b1v_version[18][2];
static uint32_t b1v_frame = 7, selected[2] = {9,9}, calls, last_slot;
static uint32_t pointer_override;
static unsigned load_forgets, leash_forgets, center_forgets;
static void b1load_forget(void) { ++load_forgets; }
static void b1leash_forget(void) { ++leash_forgets; }
static void b1center_forget(void) { ++center_forgets; }
static uint32_t psx_mod_read_word(uint32_t a) {
    assert(a >= B1V_DANCERS && a < B1V_DANCERS + 16);
    return pointer_override ? pointer_override : 0x80100000u + ((a-B1V_DANCERS)/4u)*0x2000u;
}
static uint8_t psx_mod_read_byte(uint32_t a) {
    if (a >= B1V_SELECTED && a < B1V_SELECTED+2) return selected[a-B1V_SELECTED];
    assert(a == 0x80100004u || a == 0x80104004u); return 9;
}
static int b1v_has_alt(uint32_t chr) { return chr == 9; }
static void b1center_apply(int slot, uint32_t dancer, uint32_t tick) {
    assert(dancer == 0x80100000u + (uint32_t)slot*0x2000u && tick == 7);
    ++calls; last_slot = (uint32_t)slot;
}
'''
        scenario = r'''
int main(void) {
    struct CPUState cpu = {{0}}, before;
    b1v_version[9][0] = b1v_version[9][1] = 1;
    for (unsigned slot=0; slot<4; ++slot) {
        cpu.gpr[19] = B1LEASH_CTL + slot*0x4Cu;
        cpu.gpr[16] = 0x80100000u + slot*0x2000u;
        before = cpu; calls = 0;
        b1v_end_center_hook(&cpu, B1CENTER_SITE);
        assert(calls == (slot%2u == 0));
        if (calls) assert(last_slot == slot);
        assert(memcmp(&cpu, &before, sizeof cpu) == 0);
    }
    cpu.gpr[19] = B1LEASH_CTL; cpu.gpr[16] = 0x80100000u; calls = 0;
    b1v_active = 0; b1v_end_center_hook(&cpu, B1CENTER_SITE); b1v_active = 1;
    b1v_end_center_hook(&cpu, B1CENTER_SITE+4);
    b1v_force_stock = 1; b1v_end_center_hook(&cpu, B1CENTER_SITE); b1v_force_stock = 0;
    b1v_version[9][0] = 0; b1v_end_center_hook(&cpu, B1CENTER_SITE); b1v_version[9][0] = 1;
    selected[0] = 0; b1v_end_center_hook(&cpu, B1CENTER_SITE); selected[0] = 9;
    cpu.gpr[16] += 4; b1v_end_center_hook(&cpu, B1CENTER_SITE);
    assert(calls == 0);
    const uint32_t invalid[] = {0x807FFFFCu, 0x807FEAA8u, 0x80100001u, 0x8000FFFCu};
    for (unsigned i=0; i<sizeof invalid/sizeof invalid[0]; ++i) {
        pointer_override = invalid[i]; cpu.gpr[16] = invalid[i];
        b1v_end_center_hook(&cpu, B1CENTER_SITE);
        assert(calls == 0);  /* read_byte also asserts no invalid actor+4 read */
    }
    pointer_override = 0;
    b1v_restore();
    assert(load_forgets == 1 && leash_forgets == 1 && center_forgets == 1);
    return 0;
}
'''
        with tempfile.TemporaryDirectory(dir=ROOT / '_work') as directory:
            path = Path(directory)
            harness = path / 'callback.c'
            harness.write_text(prefix + selection + callback + scenario, encoding='utf-8')
            subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', 'gcc', '-std=c11',
                            '-Wall', '-Wextra', '-Werror', linux_path(harness),
                            '-o', linux_path(path / 'callback')], check=True, capture_output=True)
            result = subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec',
                                     linux_path(path / 'callback')], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_center_registration_reset_and_native_aot_site_are_wired(self) -> None:
        source = (ROOT / 'mods-src/bag2jp.feature.bag1-content/bag2jp_bag1_versions.c').read_text()
        self.assertIn('B1CENTER_SITE, B1CENTER_WORD, b1v_end_center_hook)', source)
        self.assertNotIn('psx_mod_register_savestate_load_plugin', source)
        self.assertIn('psx_mod_register_savestate_plugin("bag2jp.bag1_versions", b1v_restore)', source)
        restore = source[source.index('static void b1v_restore('):source.index('static void b1v_activate(')]
        self.assertIn('b1load_forget();', restore)
        self.assertIn('b1leash_forget();', restore)
        self.assertIn('b1center_forget();', restore)
        reset = source[source.index('static void b1v_reset('):source.index('int bag2jp_bag1_has_version(')]
        self.assertIn('b1center_forget();', reset)
        config = tomllib.loads((ROOT / 'patches/BAG2JP-game.toml').read_text())
        sites = {int(value, 16) for value in config['recompiler']['mod_instruction_sites']}
        self.assertIn(0x8002D818, sites)
        self.assertFalse(sites & {0x80014FB8, 0x80014FD4})

    def test_control_block_layout_matches_original_executable(self) -> None:
        """The harness lays out control blocks itself; check that layout in SLPM_862.19."""
        exe = (ROOT / 'assets/disc_files/SLPM_862.19').read_bytes()
        self.assertEqual(exe[:8], b'PS-X EXE')
        text = int.from_bytes(exe[0x18:0x1C], 'little')
        word = lambda address: int.from_bytes(exe[0x800 + address - text:][:4], 'little')
        # FUN_8001E0F4: ctl 0x8005F820 + {0, 0x98, 0x4C, 0xE4} for dancers +0, +8, +4, +0xC.
        self.assertEqual(word(0x8001E410), 0x3C118006)   # lui s1,0x8006
        self.assertEqual(word(0x8001E414), 0x2631F820)   # addiu s1,s1,-0x7e0
        self.assertEqual(word(0x8001E420), 0x8E05F808)   # lw a1,-0x7f8(s0)
        self.assertEqual(word(0x8001E42C), 0x8E050008)   # lw a1,8(s0)
        self.assertEqual(word(0x8001E434), 0x26240098)   # addiu a0,s1,0x98
        self.assertEqual(word(0x8001E438), 0x8E050004)   # lw a1,4(s0)
        self.assertEqual(word(0x8001E440), 0x2624004C)   # addiu a0,s1,0x4c
        self.assertEqual(word(0x8001E444), 0x8E05000C)   # lw a1,0xc(s0)
        self.assertEqual(word(0x8001E44C), 0x262400E4)   # addiu a0,s1,0xe4
        # Leash call reads the radius word; the init caller stores the zoom-scaled radius.
        self.assertEqual(word(0x8002D810), 0x26640028)   # addiu a0,s3,0x28 (home)
        self.assertEqual(word(0x8002D818), 0x8E660038)   # lw a2,0x38(s3)
        self.assertEqual(word(0x8002D81C), 0x0C00B352)   # jal 0x8002cd48
        self.assertEqual(word(0x8002BA38), 0xAE420038)   # sw v0,0x38(s2)
        self.assertEqual(word(0x8002D920), 0xAD02003C)   # sw v0,0x3c(t0), raw table radius
        self.assertEqual(word(0x8002D7A0), 0x96620004)   # lhu v0,4(s3) blend
        self.assertEqual(word(0x8002D7C0), 0x24021000)   # addiu v0,zero,0x1000 settled blend
        self.assertEqual(word(0x8002D7F4), 0x92020003)   # lbu v0,3(s0) actor active byte
        self.assertEqual(word(0x8002D804), 0x9262000C)   # lbu v0,0xc(s3) clamp enable
        self.assertEqual(word(0x8002D814), 0x26050810)   # addiu a1,s0,0x810 root
        self.assertEqual(word(0x8002D820), 0x260714B8)   # addiu a3,s0,0x14b8 base
        self.assertEqual(word(0x8002D824), 0x0C00B101)   # jal 0x8002c404 pose consumer
        self.assertEqual(word(0x8002D8CC), 0x3C028009)   # lui v0,0x8009 stage ptr hi
        self.assertEqual(word(0x8002D8D4), 0x8C439200)   # lw v1,-0x6e00(v0) -> 0x80089200
        header = (ROOT / 'mods-src/bag2jp.feature.bag1-content/bag2jp_bag1_leash.h').read_text()
        for name, value in (('B1LEASH_CTL', '0x8005F820u'), ('B1LEASH_CTL_STRIDE', '0x4Cu'),
                            ('B1LEASH_HOME_X', '0x28u'), ('B1LEASH_RADIUS', '0x38u'),
                            ('B1LEASH_RAW_RADIUS', '0x3Cu'), ('B1LEASH_STAGE_PTR', '0x80089200u'),
                            ('B1LEASH_BAG1_RADIUS', '300u'), ('B1LEASH_BAG1_HOME', '784u')):
            self.assertRegex(header, rf'#define {name}\s+{value}')

    def test_original_combat_overlay_deliberately_releases_all_four_radii(self) -> None:
        """Native phase 4->5 writes INT_MAX, not a fresh finite initialization radius."""
        overlay = (ROOT / 'assets/archive/system/005.dbi').read_bytes()
        expected = {
            0x8009CAC4: 0x3C077FFF,   # lui a3,0x7fff
            0x8009CAC8: 0x34E7FFFF,   # ori a3,a3,0xffff
            0x8009CAD4: 0x3C028006,   # lui v0,0x8006
            0x8009CAD8: 0x2445F820,   # addiu a1,v0,-0x7e0
            0x8009CB0C: 0xACA70038,   # sw a3,0x38(a1), primary radius
            0x8009CB10: 0xACA70084,   # sw a3,0x84(a1), partner radius
            0x8009CB1C: 0x24A50098,   # addiu a1,a1,0x98, next side
            0x8009CB44: 0xAC62D3DC,   # sw v0,-0x2c24(v1), advance phase
            0x8009A548: 0xA462E77A,   # sh v0,-0x1886(v1) -> 0x8005E77A P2 attack active
            0x8009A560: 0xA462E748,   # sh v0,-0x18B8(v1) -> 0x8005E748 P1 attack active
            0x8009A5A0: 0x2453F808,   # addiu s3,v0,-0x7f8 -> 0x8005F808 actors
        }
        for address, instruction in expected.items():
            with self.subTest(address=hex(address)):
                offset = 12 + address - 0x8008F890
                self.assertEqual(int.from_bytes(overlay[offset:offset + 4], 'little'), instruction)


if __name__ == '__main__':
    unittest.main()
