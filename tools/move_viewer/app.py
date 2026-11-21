"""BAG2JP move viewer (read-only): Character -> Role -> Move tree with details.

The view plays the selected motion with the software renderer (anim_view.py).
Usage: py -3.13 tools/move_viewer/app.py [--tables move_tables.json] [--smoke]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (QApplication, QFormLayout, QLabel, QMainWindow, QSplitter,
                               QTabWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.move_viewer import move_tables  # noqa: E402
from tools.move_viewer import bank_source, package_plan, reservations, selector_policy, swap_mod  # noqa: E402

# Native selector authority; checked byte-identical to the installed BAG2JP.exe table (2026-11-21).
SELECTOR_TABLE = ROOT / "mods-src/bag2jp.feature.bag1-content/bag2jp_bag1_alt_index.h"
from tools.move_viewer.anim_view import AnimationView, asset_folder  # noqa: E402
from tools.move_viewer.assign_panel import AssignPanel  # noqa: E402
from tools.move_viewer.combo_view import ComboView  # noqa: E402
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
        self.combos = ComboView()
        self.combos.slot_selected.connect(self.show_combo_slot)
        self.tabs = QTabWidget()
        self.tabs.addTab(self.tree, "Moves")
        self.tabs.addTab(self.combos, "Combos")
        splitter = QSplitter()
        splitter.addWidget(self.tabs)
        splitter.addWidget(details)
        self.assign = AssignPanel(self.preview_motion, generate_mod)
        splitter.addWidget(self.assign)
        splitter.setStretchFactor(0, 5)     # Moves/Combos tabs get the extra width
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 3)
        self.splitter = splitter
        self._character = ""
        self.setCentralWidget(splitter)
        self.populate(tables)

    def showEvent(self, event: QShowEvent) -> None:
        """Split the first time by weight; the layout ignores setSizes made before show."""
        super().showEvent(event)
        if not getattr(self, "_sized", False):
            self._sized = True
            self.splitter.setSizes([520, 340, 340])

    def set_view_widget(self, widget: QWidget) -> None:
        self.view_slot.insertWidget(0, widget, 1)
        self.view_slot.removeWidget(self.view_widget)
        self.view_widget.hide()     # deleteLater runs later; hide so it does not paint meanwhile
        self.view_widget.deleteLater()
        self.view_widget = widget

    def show_combo_slot(self, character: str, slot: int) -> None:
        """Preview the slot of the selected Combos row (same renderer as the Moves tree)."""
        self._character = character
        move = next((m for c in self._tables.get("characters", []) if c["name"] == character
                     for m in c["moves"] if m["slot"] == slot), None)
        for name, label in self.fields.items():
            label.setText(str(move.get(name)) if move else "-")
        self.fields["character"].setText(character)
        self.fields["slot"].setText(str(slot))
        self.assign.set_character(character_bank(character), character_sources(character))
        self.assign.set_slot(slot, move["label"] if move else "")
        self.preview_motion(slot)

    def populate(self, tables: dict) -> None:
        self._tables = tables
        self.combos.set_tables(tables)
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
            self.combos.set_character(move["character"])
            self.assign.set_character(character_bank(move["character"]),
                                      character_sources(move["character"]))
        self.assign.set_slot(move["slot"] if move else None, move["label"] if move else "")
        if isinstance(self.view_widget, AnimationView):
            self.view_widget.show_motion(move["character"] if move else "",
                                         move["slot"] if move else None)

    def preview_motion(self, index: int, bank: bytes | None = None) -> None:
        if isinstance(self.view_widget, AnimationView) and self._character:
            self.view_widget.show_motion(self._character, index, bank)


def character_bank(name: str) -> Path | None:
    config = load_config(repo_root=ROOT)
    assets, = require_paths(config, ("inputs.bag2jp_assets",))
    path = assets / "archive/characters" / asset_folder(name) / "model_a_p1/001.bin"
    return path if path.is_file() else None


def character_sources(name: str) -> list[swap_mod.BankSource]:
    """Source banks of the Assign panel: own bank, BAG1 variant, compatible other characters."""
    config = load_config(repo_root=ROOT)
    assets, payload = require_paths(config, ("inputs.bag2jp_assets", "inputs.bag1_alt_payload"))
    return bank_source.sources_for(assets / "archive/characters", payload, asset_folder(name))


def generate_mod(bank: Path, pairs: list[tuple[int, int]],
                 cross: swap_mod.CrossBank | None = None) -> str:
    """Write a disabled copy package (slot <- source) for every disc entry holding `bank`.

    With `cross` the sources are motions of cross.source (BAG1 variant / other character).
    """
    config = load_config(repo_root=ROOT)
    disc, work = require_paths(config, ("inputs.bag2_disc", "paths.move_viewer_work"))
    swap_mod.check_disc(disc)
    folder = bank.parents[1].name
    package_id = f"bag2jp.test.move-assign-{folder.replace('_', '-')}"
    if cross:       # a distinct id keeps it from overwriting the own-bank package
        package_id += "-from-" + re.sub(r"[^a-z0-9]+", "-", cross.source.label.lower()).strip("-")
    out = assert_write_target(config, (work / "f2/pkg" / package_id / "1.0.0").resolve(), role="work")
    data = bank.read_bytes()
    entries = swap_mod.find_entries(disc, data)
    max_growth = 0
    if swap_mod.copy_growth(data, pairs, cross.source.bank if cross else None) > 0:
        entries, max_growth = swap_mod.GROWTH_BUDGET[folder]
        entries = list(entries)
    elif cross:
        # Compatibility was checked against costume A only; costume 4 has another skeleton.
        entries = list(swap_mod.GROWTH_BUDGET[folder][0])
    origin = f" from {cross.source.label}" if cross else ""
    name = f"Move assign {folder}{origin}: " + ", ".join(f"{a}<-{b}" for a, b in pairs)
    install, = require_paths(config, ("paths.experimental_install",))
    spans = reservations.inventory((work / 'f2/pkg', install / 'mods/installed'))
    # BAG1 selector entries may only move when the installed exe follows relocated offsets
    # (b1v_bag2_off, bag2jp_bag1_versions.c; recorded take f3-bag1reloc-strike-20261121c).
    blocked = selector_policy.blocked_entries(SELECTOR_TABLE.read_text(encoding="utf-8"))
    if selector_policy.exe_follows_relocation(install / "BAG2JP.exe"):
        blocked = frozenset()
    overlays = package_plan.plan(disc, entries, pairs, spans, max_growth=max_growth,
                                 cross=cross, relocation_blocked=blocked)
    if out.exists():
        raise ValueError(f'Package already exists; preserved: {out}')
    swap_mod.write_package(out, package_id, name, overlays)
    note = " (jugador 1 y 2, traje A; traje 4 queda stock)" if max_growth or cross else ""
    return f"Mod generado (desactivado) en {out} — entradas BUST2.BIN {entries}{note}"


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
