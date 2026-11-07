"""Unit tests for announcer cue renaming used to swap Bi-O name calls for Gas-O."""
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/bag1import"))

from preserve_announcer import (banks, cue_record, cue_records, pack_banks,
                                rename_cue, single_cue)
from rebuild_dfs_members import read_members


def cue_ids(data: bytes) -> list[int]:
    return [struct.unpack_from("<H", rec)[0]
            for _, _, table in banks(data) for rec in cue_records(table)]


class TestRenameCue(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pack = ROOT / "_work/stage_import/gaso/stock_bio_entries/pack_a_p1.dfs"
        cls.stock = read_members(pack.read_bytes())[0][4]
        cls.single = pack_banks([single_cue(cls.stock, 0x1907)])

    def test_rename_changes_only_the_cue_id(self):
        renamed = rename_cue(self.single, 0x1907, 0x2091)
        self.assertEqual(cue_ids(renamed), [0x2091])
        self.assertEqual(cue_record(renamed, 0x2091)[2:],
                         cue_record(self.single, 0x1907)[2:])

    def test_rename_keeps_vab_head_and_body_byte_exact(self):
        renamed = rename_cue(self.single, 0x1907, 0x2091)
        self.assertEqual([b[:2] for b in banks(renamed)],
                         [b[:2] for b in banks(self.single)])

    def test_rename_with_record_takes_stock_fields(self):
        stock_record = cue_record(self.stock, 0x1908)
        renamed = rename_cue(self.single, 0x1907, 0x1908, stock_record)
        self.assertEqual(cue_record(renamed, 0x1908), stock_record)

    def test_rename_missing_cue_raises(self):
        with self.assertRaises(ValueError):
            rename_cue(self.single, 0x2090, 0x1907)

    def test_cue_record_missing_raises(self):
        with self.assertRaises(ValueError):
            cue_record(self.single, 0x2090)


if __name__ == "__main__":
    unittest.main()
