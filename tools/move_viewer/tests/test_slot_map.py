"""Regression: the emulated DBI init reproduces Heat's RAM-dumped player+0x7CC map."""
import unittest
from pathlib import Path

from tools.move_viewer.pose import HEAT_SLOT_MAP, UNMAPPED_SLOT
from tools.move_viewer.render_offline import ROOT, character_slot_map

PACK = ROOT / 'assets/archive/characters/heat/pack_a_p1'


@unittest.skipUnless(PACK.exists(), 'Heat pack not extracted')
class SlotMapTests(unittest.TestCase):
    def test_heat_a_matches_ram_dump(self):
        got = character_slot_map(PACK, costume=0)
        self.assertEqual(got[:len(HEAT_SLOT_MAP)], HEAT_SLOT_MAP)
        self.assertTrue(all(t == UNMAPPED_SLOT for t in got[len(HEAT_SLOT_MAP):]))


if __name__ == '__main__':
    unittest.main()
