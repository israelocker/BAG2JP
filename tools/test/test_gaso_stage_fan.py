"""Gas-O stage generator regression against the original fan instructions."""
import copy
import struct
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/bag1import'))
from animlib import dfs_entries
import build_stage_package as package
import port_bag1_stage as stage

FAN_SITE = 0x801E2448


def word(blob: bytes, offset: int) -> int:
    """Read an instruction without disassembler normalisation."""
    return struct.unpack_from('<I', blob, offset)[0]


class GasoStageFanTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = stage.load_profile('gaso')
        cls.native = dfs_entries((ROOT / cls.profile['package']['source']).read_bytes())[0]
        result, _ = package.build_from_project(ROOT, 'gaso')
        cls.ported = dfs_entries(result)[0]

    def test_generated_stage_keeps_the_native_divide_by_sixteen(self) -> None:
        offset = 12 + FAN_SITE - self.profile['source_base']
        self.assertEqual(word(self.native, offset), 0x00031903)  # sra v1,v1,4
        self.assertEqual(word(self.ported, offset), word(self.native, offset))

    def test_fan_calculation_only_relocates_its_memory_addresses(self) -> None:
        # Generator without any override at the fan site is the exact baseline,
        # including multiply, signed rounding, delta load and angle halfword store.
        profile = copy.deepcopy(self.profile)
        profile['patches'] = [p for p in profile['patches'] if p[0] != FAN_SITE]
        with patch.object(stage, 'load_profile', return_value=profile):
            result, _ = package.build_from_project(ROOT, 'gaso')
        baseline = dfs_entries(result)
        offset = 12 + 0x801E23B0 - self.profile['source_base']
        end = 12 + 0x801E2460 - self.profile['source_base']
        self.assertEqual(self.ported[offset:end], baseline[0][offset:end])

    def test_score_speed_thresholds_remain_native(self) -> None:
        # Native update caps speed at 0x80 for level1 and 0x200 for level2.
        for address, instruction in ((0x801E23D0, 0x2C620080), (0x801E2404, 0x2C620200)):
            offset = 12 + address - self.profile['source_base']
            with self.subTest(address=hex(address)):
                self.assertEqual(word(self.native, offset), instruction)
                self.assertEqual(word(self.ported, offset), instruction)

    def test_both_score_paths_read_the_relocated_level_not_80070108(self) -> None:
        # bne's delay-slot LUI covers the taken path; a second LUI is reached
        # only after level1 processing. Both must feed the common lb v0,0x108(v0).
        for address in (0x801E23C0, 0x801E23E0):
            offset = 12 + address - self.profile['source_base']
            with self.subTest(path_lui=hex(address)):
                self.assertEqual(word(self.native, offset), 0x3C028007)
                self.assertEqual(word(self.ported, offset), 0x3C02801E)
        load = 12 + 0x801E23E4 - self.profile['source_base']
        self.assertEqual(word(self.ported, load), 0x80420108)

    def test_japanese_source_uses_the_same_divisor(self) -> None:
        # JP native layout differs; inspect its verified file offset, NOT the USA VA.
        blob = dfs_entries((ROOT / '_work/bag1jp_disc_full/STAGE/ST_GAS.DFS').read_bytes())[0]
        self.assertEqual(word(blob, 0xCB8), 0x00032103)  # sra a0,v1,4
        self.assertEqual(word(blob, 0xCA4), 0x00620018)  # mult v1,v0

    def test_generator_rejects_a_changed_source_fan_instruction(self) -> None:
        stock = (ROOT / self.profile['package']['stock'] / '000.dbi').read_bytes()
        for site, bad_word in ((FAN_SITE, 0x00031843), (0x801E23E0, 0x3C028006)):
            with self.subTest(site=hex(site)):
                changed = bytearray(self.native)
                offset = 12 + site - self.profile['source_base']
                struct.pack_into('<I', changed, offset, bad_word)
                with self.assertRaisesRegex(ValueError, f'Unexpected stage instruction at {site:08X}'):
                    stage.build(bytes(changed), stock, profile=self.profile,
                                main_exe=(ROOT / '_work/mainexe/slpm.bin').read_bytes())


if __name__ == '__main__':
    unittest.main()
