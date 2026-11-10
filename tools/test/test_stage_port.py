"""Real stage fixtures: shared relocation must preserve the admitted Heat blob."""
import hashlib
import copy
import struct
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
    def test_gaso_package_preserves_native_assets_and_stock_song_tail(self):
        import build_stage_package as package
        import preserve_announcer as pa

        result, report = package.build_from_project(ROOT, 'gaso')
        entries = dfs_entries(result)
        native = dfs_entries((ROOT / '_work/bag1_disc_full/STAGEE/ST_GAS.DFS').read_bytes())
        stock = (ROOT / '_work/stage_import/gaso/stock_197_graveyard/000.dbi').read_bytes()
        self.assertEqual(len(entries), 13)
        self.assertEqual(entries[2:5], native[2:5])
        import tim_retarget as tim
        _, palette, image = tim.parse(entries[5])
        self.assertEqual((image['x'], image['y']), (640, 256))
        self.assertEqual((palette['x'], palette['y']), (960, 48))
        _, palette, _ = tim.parse(entries[6])
        self.assertEqual((palette['x'], palette['y']), (992, 48))
        self.assertEqual(entries[7:11], [native[4]] * 4)
        self.assertEqual(pa.banks(entries[1])[0], pa.banks(native[1])[0])
        self.assertEqual(report['unmapped_calls'], [])
        self.assertEqual(report['model'], {1: 32, 3: 1})
        from tools.test.test_stage_geometry import nodes
        converted_nodes = nodes(entries[11])
        for panel in (23, 26, 30):
            self.assertEqual(struct.unpack_from('<I', converted_nodes[panel], 0x25*4)[0], 21)
            self.assertEqual(struct.unpack_from('<I', converted_nodes[panel], 0x30*4)[0], 9 << 16)
        # Fresh Ghidra MCP: id9 callbacks and chart pointer (2026-11-06).
        self.assertEqual(struct.unpack_from('<2I', entries[0], 12 + 0x801E25C4 - stage.B2_BASE),
                         (0x03E00008, 0x24020001))
        tail_offset = 12 + 0x801E268C - stage.B2_BASE
        self.assertEqual(entries[0][tail_offset:], stock[tail_offset:])
        self.assertEqual(len(entries[0]), len(stock))

    def test_gaso_rejects_a_wrong_callback_within_the_image(self):
        import build_stage_package as package
        from unittest.mock import patch

        profile = copy.deepcopy(stage.load_profile('gaso'))
        profile['callbacks'][0] += 4  # In bounds, but overwrites init's delay slot.
        with patch.object(stage, 'load_profile', return_value=profile):
            with self.assertRaisesRegex(ValueError, 'callback'):
                package.build_from_project(ROOT, 'gaso')

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
        import preserve_announcer as pa
        self.assertEqual(pa.banks(entries[1])[0], pa.banks(native[1])[0])

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
