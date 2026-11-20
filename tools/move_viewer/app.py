"""BAG2JP move viewer (read-only): Character -> Role -> Move tree with details.

The view plays the selected motion with the software renderer (anim_view.py).
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
from tools.move_viewer import swap_mod  # noqa: E402
from tools.move_viewer.anim_view import AnimationView, asset_folder  # noqa: E402
from tools.move_viewer.assign_panel import AssignPanel  # noqa: E402
from tools.workflow.project_config import (assert_write_target, load_config,  # noqa: E402
                                           require_paths)

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
        self.assign = AssignPanel(self.preview_motion, generate_mod)
        splitter.addWidget(self.assign)
        splitter.setSizes([380, 420, 380])
        self._character = ""
        self.setCentralWidget(splitter)
        self.populate(tables)

    def set_view_widget(self, widget: QWidget) -> None:
        self.view_slot.insertWidget(0, widget, 1)
        self.view_slot.removeWidget(self.view_widget)
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
        if move:
            self._character = move["character"]
            self.assign.set_character(character_bank(move["character"]))
        self.assign.set_slot(move["slot"] if move else None, move["label"] if move else "")
        if isinstance(self.view_widget, AnimationView):
            self.view_widget.show_motion(move["character"] if move else "",
                                         move["slot"] if move else None)

    def preview_motion(self, index: int) -> None:
        if isinstance(self.view_widget, AnimationView) and self._character:
            self.view_widget.show_motion(self._character, index)


def character_bank(name: str) -> Path | None:
    config = load_config(repo_root=ROOT)
    assets, = require_paths(config, ("inputs.bag2jp_assets",))
    path = assets / "archive/characters" / asset_folder(name) / "model_a_p1/001.bin"
    return path if path.is_file() else None


def generate_mod(bank: Path, pairs: list[tuple[int, int]]) -> str:
    """Write a disabled copy package (slot <- source) for every disc entry holding `bank`."""
    config = load_config(repo_root=ROOT)
    disc, work = require_paths(config, ("inputs.bag2_disc", "paths.move_viewer_work"))
    swap_mod.check_disc(disc)
    folder = bank.parents[1].name
    package_id = f"bag2jp.test.move-assign-{folder.replace('_', '-')}"
    out = assert_write_target(config, (work / "f2/pkg" / package_id / "1.0.0").resolve(), role="work")
    entries = swap_mod.find_entries(disc, bank.read_bytes())
    name = f"Move assign {folder}: " + ", ".join(f"{a}<-{b}" for a, b in pairs)
    swap_mod.generate(disc, entries, pairs, package_id, name, out, copy=True)
    return f"Mod generado (desactivado) en {out} — entradas BUST2.BIN {entries}"


def animation_view() -> AnimationView:
    config = load_config(repo_root=ROOT)
    assets, = require_paths(config, ("inputs.bag2jp_assets",))
    return AnimationView(assets / "archive/characters")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tables", type=Path, help="move_tables.json (default: extract now)")
    parser.add_argument("--smoke", action="store_true", help="open, check the tree and quit")
    args = parser.parse_args(argv)
    app = QApplication.instance() or QApplication(sys.argv[:1])
    window = MoveViewer(load_tables(args.tables))
    window.set_view_widget(animation_view())
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
