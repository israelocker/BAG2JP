"""Combos view: pure row data (grid, labels, BAG1 ladder/origin) and the widget wiring."""
import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from PySide6.QtWidgets import QApplication  # noqa: E402
from tools.move_viewer import combo_view  # noqa: E402
from tools.move_viewer.move_tables import FINISH_REQUESTS  # noqa: E402

SLOTS = {str(r): 100 + r for r in range(1, 43)}
BAG1_LADDER = ["L0: A C F J O U ZZZ | FINISH7", "L1: B E I N T ZZ | FINISH6", "L2: D H M S Z | FINISH5",
               "L3: G L R Y | FINISH4", "L4: K Q X | FINISH3", "L5: P W | FINISH2", "L6: V | FINISH1"]


class DataTests(unittest.TestCase):
    def test_grid_shape_and_finishes(self):
        rows = combo_view.bag2_rows(SLOTS)
        self.assertEqual([r.request for r in rows], list(range(1, 43)))
        self.assertEqual([r.request for r in rows if r.finish], list(FINISH_REQUESTS))
        self.assertEqual([r.label for r in rows if r.finish], [f"FINISH{n}" for n in range(8, 0, -1)])
        self.assertEqual([len([r for r in rows if r.level == lv]) for lv in range(8)],
                         list(combo_view.LEVEL_LENGTHS))
        self.assertEqual(rows[0].bar, 0)
        self.assertEqual([r.bar for r in rows if r.level == 5], [2, 3, 4, 5, 6, 7])
        self.assertEqual([r.bar for r in rows if r.level == 7], [6, 7])

    def test_dance_view_letters(self):
        labels = combo_view.dance_view_labels()
        self.assertEqual(len(labels), 34)
        self.assertEqual(set(labels), set(range(1, 43)) - set(FINISH_REQUESTS))
        self.assertEqual((labels[23], labels[1], labels[29], labels[9], labels[41]), ("A", "E", "HH", "AA", "EE"))

    def test_slot_comes_from_table_and_finish_note(self):
        rows = combo_view.bag2_rows({"1": 6, "4": 53})
        self.assertEqual((rows[0].slot, rows[3].slot, rows[1].slot), (6, 53, None))
        self.assertIn("Groovin'", rows[3].note)
        self.assertEqual(rows[0].note, "")

    def test_bag1_ladder_matches_verified_text(self):
        text = combo_view.bag1_ladder_text()
        for line in BAG1_LADDER:
            self.assertIn(line, text)
        self.assertIn("A B D G K P V FINISH1", text)

    def test_non_imported_character_has_no_origin(self):
        rows = combo_view.bag2_rows(SLOTS, "KELLY")
        self.assertTrue(all(r.bag1_cell == "" and r.bag1_anim is None for r in rows))

    def test_imported_origin_follows_b1_path(self):
        remap = combo_view.load_remap()
        self.assertIsNotNone(remap)
        for name in sorted(combo_view.BAG1_IMPORTED):
            rows = combo_view.bag2_rows(SLOTS, name)
            for level in range(8):
                path = remap.B1_PATHS[level]
                got = [r.bag1_cell for r in rows if r.level == level]
                self.assertEqual(got, [combo_view.bag1_cell_label(*c) for c in path])
        rows = combo_view.bag2_rows(SLOTS, "HEAT")
        self.assertEqual(rows[0].bag1_cell, "A")             # first step is the clap
        self.assertTrue(all(r.bag1_anim for r in rows))
        self.assertTrue(all(r.bag1_cell.startswith("FINISH") == r.finish for r in rows))

    def test_levels_agree_with_import_plan(self):
        remap = combo_view.load_remap()
        for level, (start, row) in remap.B2_ROWS.items():
            self.assertEqual((start, len(row)), (combo_view.LEVEL_START_BAR[level], combo_view.LEVEL_LENGTHS[level]))


class WidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_table_and_signal(self):
        view = combo_view.ComboView()
        view.set_tables({"global": {"request_slot": SLOTS},
                         "characters": [{"name": "KELLY"}, {"name": "HEAT"}]})
        self.assertEqual(view.table.rowCount(), 42)
        self.assertEqual(view.table.item(0, 5).text(), "")
        view.set_character("HEAT")
        self.assertEqual(view.table.item(0, 5).text(), "A")
        got = []
        view.slot_selected.connect(lambda c, s: got.append((c, s)))
        view.table.setCurrentCell(3, 0)
        self.assertEqual(got, [("HEAT", 104)])


if __name__ == "__main__":
    unittest.main()
