"""Unit tests for announcer cue renaming used to swap Bi-O name calls for Gas-O."""
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/bag1import"))

from preserve_announcer import (banks, cue_record, cue_records, pack_banks,
                                rename_cue, replace_cue, single_cue)
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


class TestReplaceCue(unittest.TestCase):
    """VS bank P1 holds the name 0x3090 beside 'versus' 0x3130."""

    @classmethod
    def setUpClass(cls):
        pack = ROOT / "_work/stage_import/gaso/stock_bio_entries/pack_a_p1.dfs"
        members = read_members(pack.read_bytes())[0]
        cls.vs = members[5]
        cls.clip = rename_cue(pack_banks([single_cue(members[4], 0x1907)]), 0x1907, 0x2090)
        cls.replaced = replace_cue(cls.vs, 0x3090, cls.clip, 0x2090)

    def test_replace_keeps_every_stock_cue_id(self):
        self.assertEqual(sorted(cue_ids(self.replaced)), sorted(cue_ids(self.vs)))

    def test_replace_takes_stock_record_of_the_replaced_cue(self):
        self.assertEqual(cue_record(self.replaced, 0x3090), cue_record(self.vs, 0x3090))

    def test_replace_swaps_the_sample_and_keeps_other_cues_exact(self):
        self.assertEqual(single_cue(self.replaced, 0x3090)[1], single_cue(self.clip, 0x2090)[1])
        self.assertEqual(single_cue(self.replaced, 0x3130), single_cue(self.vs, 0x3130))

    def test_replace_missing_cue_raises(self):
        with self.assertRaises(ValueError):
            replace_cue(self.vs, 0x3091, self.clip, 0x2090)


if __name__ == "__main__":
    unittest.main()
