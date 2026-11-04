"""Guarded native DBI adaptation, never a mutation of stock source files."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/bag1import'))
from dbi_word_contract import apply_word_contract


class DbiWordContractTests(unittest.TestCase):
    """Apply/restore must be exact and reject all unrecognized inputs."""

    def setUp(self) -> None:
        self.data = struct.pack('<4sIIIII', b'DBI_', 12, 0, 0x11111111, 0x22222222, 0x33333333)
        self.contract = {'source_sha256': [hashlib.sha256(self.data).hexdigest()],
                         'word_guards': {'0': '11111111', '4': '22222222'},
                         'patches': [{'offset': 4, 'expected': '22222222', 'replacement': '00000000'}]}

    def test_exact_change_and_restoration(self) -> None:
        result = apply_word_contract(self.data, self.contract)
        self.assertEqual(result, self.data[:16] + bytes(4) + self.data[20:])
        self.assertEqual(apply_word_contract(result, self.contract, restore=True), self.data)

    def test_unknown_input_and_tampered_restoration_rejected(self) -> None:
        for data in (b'not a DBI', self.data[:-1], self.data[:-1] + b'\xff'):
            with self.subTest(data=data), self.assertRaises(ValueError):
                apply_word_contract(data, self.contract)
        result = apply_word_contract(self.data, self.contract)
        with self.assertRaises(ValueError):
            apply_word_contract(result[:-1] + b'\xff', self.contract, restore=True)

    def test_hash_does_not_override_word_or_bounds_guards(self) -> None:
        for change in ({'offset': 4, 'expected': '99999999', 'replacement': '00000000'},
                       {'offset': 3, 'expected': '22222222', 'replacement': '00000000'},
                       {'offset': 12, 'expected': '22222222', 'replacement': '00000000'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                apply_word_contract(self.data, {**self.contract, 'patches': [change]})

    def test_duplicate_patches_and_modified_context_guards_rejected(self) -> None:
        """A valid source hash does not bypass contract context validation."""
        with self.assertRaises(ValueError):
            apply_word_contract(self.data, {**self.contract, 'patches': self.contract['patches'] * 2})
        with self.assertRaises(ValueError):
            apply_word_contract(self.data, {**self.contract, 'word_guards': {'0': '99999999'}})

    @unittest.skipUnless((ROOT / '_work/character_import/strike/hand_contract/bag2_a_p1.dbi').is_file(),
                         'Requires local original DBI extracts')
    def test_strike_native_words_only_and_both_player_sides(self) -> None:
        contract = json.loads((ROOT / 'tools/bag1import/profiles/strike-skeleton-contract.json').read_text(encoding='utf-8'))
        for side in ('p1', 'p2'):
            with self.subTest(side=side):
                data = (ROOT / f'_work/character_import/strike/hand_contract/bag2_a_{side}.dbi').read_bytes()
                result = apply_word_contract(data, contract)
                changed = [i for i, (a, b) in enumerate(zip(data, result)) if a != b]
                self.assertTrue(changed)
                self.assertTrue(set(changed) <= {12 + offset + byte for offset in (0x1AE0, 0x28E4) for byte in range(4)})
                self.assertEqual(struct.unpack_from('<I', result, 12 + 0x1AE0)[0], 0)
                self.assertEqual(struct.unpack_from('<I', result, 12 + 0x28E4)[0], 0)
                self.assertEqual(apply_word_contract(result, contract, restore=True), data)


if __name__ == '__main__':
    unittest.main()
