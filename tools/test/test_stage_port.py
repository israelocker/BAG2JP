"""Real stage fixtures: shared relocation must preserve the admitted Heat blob."""
import hashlib
from pathlib import Path
import sys
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/bag1import'))
from animlib import dfs_entries
if sys.platform != 'win32':
    import port_bag1_stage as stage


def load_tests(loader, tests, pattern):
    """Use the recorded Capstone environment, including in Windows discovery."""
    if sys.platform != 'win32':
        return tests

    def run_wsl():
        subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', 'python3', '-m',
                        'unittest', 'tools.test.test_stage_port'], cwd=ROOT, check=True)

    return unittest.TestSuite([unittest.FunctionTestCase(run_wsl)])


class StagePortTests(unittest.TestCase):
    def test_strike_package_has_native_textures_and_safe_empty_animation_list(self):
        import build_stage_package as package
        result, report = package.build_from_project(ROOT, 'strike')
        entries = dfs_entries(result)
        native = dfs_entries((ROOT / '_work/stage_import/strike/disc/ST_STRI.DFS').read_bytes())
        self.assertEqual(len(entries), 14)
        self.assertEqual(entries[2:5], native[2:5])
        self.assertEqual(entries[13], bytes(4))
        self.assertEqual(report['unmapped_calls'], [])
        import tim_retarget as tim
        _, palette, image = tim.parse(entries[5])
        self.assertEqual((image['x'], image['y']), (640, 256))
        _, palette, _ = tim.parse(entries[6])
        self.assertEqual((palette['x'], palette['y']), (992, 48))
        self.assertEqual(entries[7:11], [native[4]] * 4)

    def test_heat_profile_is_byte_identical_to_admitted_stage(self):
        self.assertTrue(hasattr(stage, 'load_profile'), 'Stage profiles are not implemented')
        profile = stage.load_profile('heat')
        entries = dfs_entries((ROOT / '_work/bag1_disc/STAGEE/ST_HEAT.DFS').read_bytes())
        chart = stage.bag1_chart((ROOT / '_work/bag1/scus.bin').read_bytes(), 0)
        result, _, _, unknown = stage.build(entries[0],
            (ROOT / 'assets/archive/stages/200_wood_workshop/000.dbi').read_bytes(), chart, profile)
        admitted = dfs_entries((ROOT / '_work/character_import/strike/alt_exact/heat_entries/heat_200_3.bin').read_bytes())[0]
        self.assertEqual(unknown, [])
        self.assertEqual(result, admitted)
        self.assertEqual(hashlib.sha256(result).hexdigest(),
            'e4551322b1d96eaf9e781613633aa1bebd966510e807b070d0f3fb9f974fb85f')

    def test_strike_profile_preserves_tail_and_has_no_unmapped_references(self):
        self.assertTrue(hasattr(stage, 'load_profile'), 'Stage profiles are not implemented')
        profile = stage.load_profile('strike')
        entries = dfs_entries((ROOT / '_work/stage_import/strike/disc/ST_STRI.DFS').read_bytes())
        chart = stage.bag1_chart((ROOT / '_work/stage_import/strike/disc/SLPS_012.32').read_bytes(), 1,
                                table=0x8004D980, header=0x800)
        stock = (ROOT / 'assets/archive/stages/209_vault_factory/000.dbi').read_bytes()
        result, _, _, unknown = stage.build(entries[0], stock, chart, profile,
            main_exe=(ROOT / '_work/mainexe/slpm.bin').read_bytes())
        self.assertEqual(unknown, [])
        self.assertEqual(result[12 + 0x801E3490 - stage.B2_BASE:],
                         stock[12 + 0x801E3490 - stage.B2_BASE:])
        self.assertEqual(len(result), len(stock))


if __name__ == '__main__':
    unittest.main()
