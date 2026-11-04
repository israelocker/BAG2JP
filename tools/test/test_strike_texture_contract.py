"""Scope the atlas-copy suppression to recognized alternate-B Strike DBIs."""
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/bag1import'))
from dbi_word_contract import apply_word_contract


class StrikeTextureContractTests(unittest.TestCase):
    """Preserve all instructions except the two demonstrated destructive copies."""

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
                with self.assertRaises(ValueError):
                    apply_word_contract(stock, contract)


if __name__ == '__main__':
    unittest.main()
