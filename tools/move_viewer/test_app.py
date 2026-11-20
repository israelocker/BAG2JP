"""Headless smoke test of the move viewer window."""
import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from PySide6.QtWidgets import QApplication, QLabel  # noqa: E402
from tools.move_viewer.app import MoveViewer  # noqa: E402

TABLES = {"characters": [{"id": 0, "name": "HEAT", "moves": [
    {"role": "Start", "label": "WAIT", "request": 106, "slot": 0, "frames_a": 53, "frames_b": 53},
    {"role": "Pose", "label": "POSE1", "request": 101, "slot": 90, "frames_a": 40, "frames_b": None}]}]}


class AppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_tree_and_details(self):
        window = MoveViewer(TABLES)
        char = window.tree.topLevelItem(0)
        self.assertEqual(char.childCount(), 2)
        window.tree.setCurrentItem(char.child(1).child(0))
        self.assertEqual(window.fields["request"].text(), "101")
        self.assertEqual(window.fields["character"].text(), "HEAT")

    def test_view_widget_slot_is_replaceable(self):
        window = MoveViewer(TABLES)
        view = QLabel("renderer")
        window.set_view_widget(view)
        self.assertIs(window.view_widget, view)


if __name__ == "__main__":
    unittest.main()
