"""Tests for decoding the original character archive lookup tables."""
import importlib.util
from pathlib import Path
import struct
import unittest

MODULE_PATH = Path(__file__).parents[1] / "bag1import/inspect_character_entries.py"
SPEC = importlib.util.spec_from_file_location("inspect_character_entries", MODULE_PATH)
character_entries = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(character_entries)


class CharacterEntryTableTests(unittest.TestCase):
    def test_character_one_uses_direct_low_five_bit_index(self):
        table = list(range(72))
        self.assertEqual(
            character_entries.entries_for_character(table, character_id=1),
            {"costume_a_p1": 1, "costume_a_p2": 19, "costume_b_p1": 37, "costume_b_p2": 55},
        )

    def test_loader_byte_selects_character_and_36_halfword_block(self):
        table = list(range(72))
        self.assertEqual(character_entries.entry_for_loader_byte(table, 0x01), 1)
        self.assertEqual(character_entries.entry_for_loader_byte(table, 0x21), 19)
        self.assertEqual(character_entries.entry_for_loader_byte(table, 0x41), 37)
        self.assertEqual(character_entries.entry_for_loader_byte(table, 0x61), 55)

    def test_rejects_character_outside_native_table(self):
        with self.assertRaisesRegex(ValueError, "character_id"):
            character_entries.entries_for_character(list(range(72)), character_id=18)

    def test_reads_psx_exe_halfword_table(self):
        image = bytearray(0x1000)
        image[:8] = b"PS-X EXE"
        struct.pack_into("<I", image, 0x18, 0x80010000)
        struct.pack_into("<72H", image, 0x900, *range(100, 172))
        self.assertEqual(
            character_entries.read_halfword_table(bytes(image), 0x80010100),
            list(range(100, 172)),
        )


if __name__ == "__main__":
    unittest.main()
