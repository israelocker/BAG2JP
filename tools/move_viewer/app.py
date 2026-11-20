"""BAG2JP move viewer (read-only): Character -> Role -> Move tree with details.

The 3D view is a placeholder; tools/move_viewer/model_codec.py will provide the renderer.
Usage: py -3.13 tools/move_viewer/app.py [--tables move_tables.json] [--smoke]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QApplication, QFormLayout, QLabel, QMainWindow, QSplitter,
                               QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.move_viewer import move_tables  # noqa: E402

MOVE_ROLE = Qt.ItemDataRole.UserRole
DETAIL_FIELDS = ("character", "role", "label", "request", "slot", "frames_a", "frames_b")


def load_tables(path: Path | None) -> dict:
    """Saved JSON if given, otherwise a fresh extraction from the configured binaries."""
    if path is not None:
        return json.loads(path.read_text(encoding="utf-8"))
    return move_tables.load_default()


class MoveViewer(QMainWindow):
    def __init__(self, tables: dict):
        super().__init__()
        self.setWindowTitle("BAG2JP move viewer")
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Move", "Request", "Slot", "Frames A"])
        self.tree.currentItemChanged.connect(self.show_move)
        self.fields = {name: QLabel("-") for name in DETAIL_FIELDS}
        details = QWidget()
        form = QFormLayout()
        for name, label in self.fields.items():
            form.addRow(name, label)
        # Slot for the renderer from model_codec.py; replace via set_view_widget().
        self.view_slot = QVBoxLayout()
        self.view_widget: QWidget = QLabel("3D view: pending (model_codec.py)")
        self.view_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.view_widget.setMinimumSize(320, 240)
        self.view_slot.addWidget(self.view_widget, 1)
        right = QVBoxLayout(details)
        right.addLayout(form)
        right.addLayout(self.view_slot, 1)
        splitter = QSplitter()
        splitter.addWidget(self.tree)
        splitter.addWidget(details)
        splitter.setSizes([420, 580])
        self.setCentralWidget(splitter)
        self.populate(tables)

    def set_view_widget(self, widget: QWidget) -> None:
        self.view_slot.replaceWidget(self.view_widget, widget)
        self.view_widget.deleteLater()
        self.view_widget = widget

    def populate(self, tables: dict) -> None:
        self.tree.clear()
        for char in tables["characters"]:
            char_item = QTreeWidgetItem([f"{char['id']:2d} {char['name']}"])
            roles: dict[str, QTreeWidgetItem] = {}
            for move in char["moves"]:
                role_item = roles.get(move["role"])
                if role_item is None:
                    role_item = roles[move["role"]] = QTreeWidgetItem(char_item, [move["role"]])
                item = QTreeWidgetItem(role_item, [move["label"], str(move["request"]),
                                                   str(move["slot"]), str(move["frames_a"])])
                item.setData(0, MOVE_ROLE, dict(move, character=char["name"]))
            self.tree.addTopLevelItem(char_item)

    def show_move(self, item: QTreeWidgetItem | None, _previous=None) -> None:
        move = item.data(0, MOVE_ROLE) if item is not None else None
        for name, label in self.fields.items():
            label.setText(str(move.get(name)) if move else "-")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tables", type=Path, help="move_tables.json (default: extract now)")
    parser.add_argument("--smoke", action="store_true", help="open, check the tree and quit")
    args = parser.parse_args(argv)
    app = QApplication.instance() or QApplication(sys.argv[:1])
    window = MoveViewer(load_tables(args.tables))
    window.resize(1000, 650)
    window.show()
    if args.smoke:
        count = window.tree.topLevelItemCount()
        first = window.tree.topLevelItem(0).child(0).child(0)
        window.tree.setCurrentItem(first)
        print(f"smoke: {count} characters, first move {window.fields['label'].text()}"
              f" request {window.fields['request'].text()}")
        QTimer.singleShot(0, app.quit)
        app.exec()
        return 0 if count > 0 else 1
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
