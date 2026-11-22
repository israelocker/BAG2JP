"""Regression: the emulated DBI init reproduces Heat's RAM-dumped player+0x7CC map."""
import unittest
from unittest.mock import patch
from tempfile import TemporaryDirectory
from pathlib import Path

from tools.move_viewer.pose import HEAT_SLOT_MAP, UNMAPPED_SLOT
from tools.move_viewer.render_offline import ROOT, character_slot_map

PACK = ROOT / 'assets/archive/characters/heat/pack_a_p1'


class PlayerMapRoutingTests(unittest.TestCase):
    def test_p2_uses_p2_table_and_overlay_base(self):
        with TemporaryDirectory() as directory:
            pack = Path(directory) / 'pack_a_p2'
            pack.mkdir()
            (pack / '000.dbi').write_bytes(b'fixture')
            with patch('tools.move_viewer.slot_map.find_char_id', return_value=[(14, 0)]) as find, \
                    patch('tools.move_viewer.slot_map.derive_slot_map', return_value=[7]) as derive:
                self.assertEqual(character_slot_map(pack, 0), [7])
            find.assert_called_once_with(b'fixture', side=1, base=0x801D37C4)
            derive.assert_called_once_with(b'fixture', 14, costume=0,
                                           side=1, base=0x801D37C4)


@unittest.skipUnless(PACK.exists(), 'Heat pack not extracted')
class SlotMapTests(unittest.TestCase):
    def test_heat_a_matches_ram_dump(self):
        got = character_slot_map(PACK, costume=0)
        self.assertEqual(got[:len(HEAT_SLOT_MAP)], HEAT_SLOT_MAP)
        self.assertTrue(all(t == UNMAPPED_SLOT for t in got[len(HEAT_SLOT_MAP):]))


if __name__ == '__main__':
    unittest.main()
