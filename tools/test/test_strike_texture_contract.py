"""Scope atlas-copy suppression to recognized A/B Strike DBI copies."""
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/bag1import'))
from dbi_word_contract import apply_word_contract
from alternate_payload import BASE, ROW
from rebuild_dfs_members import read_members


class StrikeTextureContractTests(unittest.TestCase):
    """Preserve all instructions except the two demonstrated destructive copies."""

    @unittest.skipUnless((ROOT / 'mods-src/bag2jp.feature.bag1-content/1.0.0/payload/bag1_alt.bin').is_file(),
                         'Requires local assembled alternate payload')
    def test_assembled_alternate_packs_disable_both_copy_calls(self) -> None:
        """The deployed assembly must wire the contract into A as well as B."""
        package = ROOT / 'mods-src/bag2jp.feature.bag1-content'
        payload = (package / '1.0.0/payload/bag1_alt.bin').read_bytes()
        rows = {int(row[1]): row for row in ROW.finditer(
            (package / 'bag2jp_bag1_alt_index.h').read_text(encoding='utf-8'))}
        contract = json.loads((ROOT / 'tools/bag1import/profiles/strike-texture-contract.json').read_text())
        self.assertEqual(contract['alternate_entries'], [73, 74, 145, 146])
        for entry in (73, 74, 145, 146):
            with self.subTest(entry=entry):
                row = rows[entry]
                start = int(row[6], 16) - BASE
                members, _ = read_members(payload[start:start + int(row[7])])
                dbi = next(member for member in members if member[:4] == b'DBI_')
                for offset in (0x2358, 0x23D4):
                    self.assertEqual(struct.unpack_from('<I', dbi, 12 + offset)[0], 0)

    @unittest.skipUnless((ROOT / '_work/character_import/strike/hand_contract/bag2_a_p1.dbi').is_file(),
                         'Requires local original DBI extracts')
    def test_costume_a_suppresses_copies_without_skeleton_changes(self) -> None:
        """Native A also lacks these BAG2 copies; retain its original skeleton branch."""
        path = ROOT / 'tools/bag1import/profiles/strike-texture-contract.json'
        contract = json.loads(path.read_text(encoding='utf-8'))
        for side in ('p1', 'p2'):
            with self.subTest(side=side):
                source = (ROOT / f'_work/character_import/strike/hand_contract/bag2_a_{side}.dbi').read_bytes()
                result = apply_word_contract(source, contract)
                expected = bytearray(source)
                for offset in (0x2358, 0x23D4):
                    struct.pack_into('<I', expected, 12 + offset, 0)
                self.assertEqual(result, bytes(expected))
                self.assertEqual(apply_word_contract(result, contract, restore=True), source)

    @unittest.skipUnless((ROOT / '_work/character_import/strike/hand_contract/bag2_a_p1.dbi').is_file(),
                         'Requires local original DBI extracts')
    def test_both_sides_only_suppress_atlas_copies_and_restore_exactly(self) -> None:
        """Palette handlers and existing skeleton adaptations must remain intact."""
        path = ROOT / 'tools/bag1import/profiles/strike-texture-contract.json'
        self.assertTrue(path.is_file(), 'Missing guarded atlas-copy contract')
        contract = json.loads(path.read_text(encoding='utf-8'))
        skeleton = json.loads((path.parent / 'strike-skeleton-contract.json').read_text(encoding='utf-8'))
        for side in ('p1', 'p2'):
            with self.subTest(side=side):
                stock = (ROOT / f'_work/character_import/strike/hand_contract/bag2_a_{side}.dbi').read_bytes()
                source = apply_word_contract(stock, skeleton)
                result = apply_word_contract(source, contract)
                expected = bytearray(source)
                for offset in (0x2358, 0x23D4):
                    struct.pack_into('<I', expected, 12 + offset, 0)
                self.assertEqual(result, bytes(expected))
                self.assertEqual(apply_word_contract(result, contract, restore=True), source)
                unrelated = bytearray(stock)
                unrelated[-1] ^= 1
                with self.assertRaises(ValueError):
                    apply_word_contract(bytes(unrelated), contract)


if __name__ == '__main__':
    unittest.main()
