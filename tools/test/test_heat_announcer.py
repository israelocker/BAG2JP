"""Check the imported Heat voices retain only the shared stock victory-name cue."""
from pathlib import Path
import sys
import unittest
import re
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/bag1import"))
from preserve_announcer import append_cue, banks, cue_records, single_cue
from rebase_cues import rebase_sedt
from animlib import dfs_entries

class HeatAnnouncerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stock = (ROOT / "assets/archive/characters/heat/pack_a_p1/005.sedt").read_bytes()
        original = (ROOT / "_work/bag1_assets/heat/PLAYER1E_P_HEATA1/007.sedt").read_bytes()
        cls.rebased, _ = rebase_sedt(original, 0x1000, 0x6000)

    def test_rebased_voices_are_preserved_byte_for_byte(self):
        result = append_cue(self.rebased, self.stock, 0x1007)
        self.assertEqual(len(banks(result)), 1)
        self.assertTrue(banks(result)[0][1].startswith(banks(self.rebased)[0][1]))
        for cue in range(0x6000, 0x6008):
            self.assertEqual(single_cue(result, cue), single_cue(self.rebased, cue))
        self.assertEqual(single_cue(result, 0x1007), single_cue(self.stock, 0x1007))

    def test_only_the_stock_name_is_added(self):
        result = append_cue(self.rebased, self.stock, 0x1007)
        ids = [int.from_bytes(r[:2], "little") for _, _, t in banks(result) for r in cue_records(t)]
        self.assertEqual(ids, list(range(0x6000, 0x6008)) + [0x1007])
        self.assertLess(len(banks(result)[0][1])-len(banks(self.rebased)[0][1]), len(banks(self.stock)[0][1]))

    def test_missing_or_duplicate_name_fails(self):
        with self.assertRaises(ValueError):
            single_cue(self.stock, 0x7777)
        result = append_cue(self.rebased, self.stock, 0x1007)
        with self.assertRaises(ValueError):
            append_cue(result, self.stock, 0x1007)

    def test_current_payload_covers_both_costumes_and_players(self):
        package = ROOT / "mods-src/bag2jp.feature.bag1-content"
        payload = (package / "1.0.0/payload/bag1_alt.bin").read_bytes()
        header = (package / "bag2jp_bag1_alt_index.h").read_text()
        rows = re.findall(r"\{(\d+), 0, [01], 0x[0-9A-F]+u, \d+u, 0x([0-9A-F]+)u, (\d+)u\}", header)
        entries = {int(e): (int(a, 16)-(224035-179)*2048, int(s)) for e, a, s in rows}
        for entry, slot in ((59,5),(60,4),(131,5),(132,4)):
            with self.subTest(entry=entry):
                offset, size = entries[entry]
                voices = dfs_entries(payload[offset:offset+size])[slot]
                self.assertEqual(len(banks(voices)), 1)
                for cue in range(0x6000, 0x6008):
                    self.assertEqual(single_cue(voices, cue), single_cue(self.rebased, cue))
                self.assertEqual(single_cue(voices, 0x1007), single_cue(self.stock, 0x1007))

    def test_invalid_bank_fails(self):
        with self.assertRaises(ValueError):
            banks(b"not a SEDT")

if __name__ == "__main__":
    unittest.main()
