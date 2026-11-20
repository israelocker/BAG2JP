"""Combos view of the move viewer: BAG2 level grid, BAG1 reference ladder and BAG1 origin cells.

The data functions are pure (no Qt) so tests can check them; ComboView only shows their rows.
BAG2 request numbers per level and Dance View letters come from the Dance View screen; the slot of
each request is read from the extracted exe table (move_tables.resolve_slot), never retyped here.
The BAG1 origin column is the import plan of tools/bag1import/anim_remap.py (b1_path), not a game
dump: it says which BAG1 cell's animation each BAG2 box plays for a BAG1-imported character.
"""
from __future__ import annotations

import logging
import re
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import Mapping

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QPlainTextEdit, QTableWidget,
                               QTableWidgetItem, QVBoxLayout, QWidget)

logger = logging.getLogger("move_viewer.combo_view")

REMAP_DIR = Path(__file__).resolve().parents[1] / "bag1import"
LEVEL_LENGTHS = (4, 6, 6, 6, 8, 6, 4, 2)       # requests per BAG2 level L0..L7 (last one is FINISH)
LEVEL_START_BAR = (0, 0, 0, 0, 0, 2, 4, 6)     # first active bar (compas) of each level
# Dance View letter -> request, in the order the screen shows them (letter = request number).
DANCE_VIEW_LETTERS = ("A23 B17 C11 D5 E1 F24 G18 H12 I6 J2 K31 L25 M19 N13 O7 P3 Q32 R26 S20 T14 "
                      "U8 V37 W33 X27 Y21 Z15 AA9 BB38 CC34 DD28 EE41 FF39 GG35 HH29")
FINISH_NOTE = "FINISH -> Groovin' si quedan >=4 tiempos, si no POSE"
# BAG1 characters imported into BAG2 with the shared scaled-grid plan (character names as in the exe).
BAG1_IMPORTED = frozenset({"HEAT", "STRIKE", "BI-O"})
BAG1_LAST_BAR = 7                               # bar 7 holds the level's FINISH ("double") cell
BAG1_LEVELS = 7                                 # BAG1 levels L0..L6, FINISH7..FINISH1


def dance_view_labels() -> dict[int, str]:
    """Request -> Dance View letter(s) (A..Z, AA..HH) for the 34 non-FINISH grid requests."""
    pairs = re.findall(r"([A-Z]+)(\d+)", DANCE_VIEW_LETTERS)
    return {int(request): letter for letter, request in pairs}


def level_requests() -> list[list[int]]:
    """Requests of each BAG2 level: L0 1-4, L1 5-10 ... L7 41-42."""
    levels, first = [], 1
    for length in LEVEL_LENGTHS:
        levels.append(list(range(first, first + length)))
        first += length
    return levels


@dataclass(frozen=True)
class ComboRow:
    """One box of the BAG2 grid. bag1_* stay empty for characters without a BAG1 origin."""
    level: int
    bar: int
    request: int
    label: str
    slot: int | None
    finish: bool
    note: str
    bag1_cell: str = ""
    bag1_anim: int | None = None


def bag1_cell_label(bar: int, level: int) -> str:
    """BAG1 cell name: A..Z, ZZ, ZZZ for bars 0-6 (index follows the BAG1 request order), FINISHn at bar 7."""
    if bar == BAG1_LAST_BAR:
        return f"FINISH{BAG1_LEVELS - level}"
    index = bar * (bar + 1) // 2 + (bar - level) + 1
    return chr(ord("A") + index - 1) if index <= 26 else "Z" * (index - 25)


def bag1_ladder() -> list[tuple[int, list[str]]]:
    """BAG1 reference: per level L0..L6 the cell names left to right, FINISH last."""
    return [(level, [bag1_cell_label(bar, level) for bar in range(level, BAG1_LAST_BAR)]
             + [bag1_cell_label(BAG1_LAST_BAR, level)]) for level in range(BAG1_LEVELS)]


def bag1_ladder_text() -> str:
    """Printable BAG1 ladder plus the maximum combo (first step is always A, the clap)."""
    lines = [f"L{level}: " + " ".join(cells[:-1]) + f" | {cells[-1]}" for level, cells in bag1_ladder()]
    maximum = [bag1_cell_label(bar, bar) for bar in range(BAG1_LAST_BAR)] + [bag1_cell_label(BAG1_LAST_BAR, 6)]
    return "BAG1 (referencia, PCSX-Redux)\n" + "\n".join(lines) + "\nCombo maximo: " + " ".join(maximum)


@lru_cache(maxsize=1)
def load_remap() -> ModuleType | None:
    """Import tools/bag1import/anim_remap.py (it needs its own folder on sys.path); None if unavailable."""
    if str(REMAP_DIR) not in sys.path:
        sys.path.insert(0, str(REMAP_DIR))
    try:
        import anim_remap
    except (ImportError, OSError, ValueError) as error:
        logger.warning("BAG1 origin unavailable: %s", error)
        return None
    return anim_remap


def bag2_rows(request_slot: Mapping[str, int], character: str | None = None) -> list[ComboRow]:
    """Grid rows for one character; request_slot is tables['global']['request_slot'] (str keys)."""
    labels = dance_view_labels()
    remap = load_remap() if character in BAG1_IMPORTED else None
    rows: list[ComboRow] = []
    for level, requests in enumerate(level_requests()):
        path = remap.B1_PATHS[level] if remap else []
        for index, request in enumerate(requests):
            finish = index == len(requests) - 1
            cell, anim = "", None
            if path:
                cell = bag1_cell_label(*path[index])
                anim = remap.b1_anim(path[index], path[index - 1] if index else None)
            rows.append(ComboRow(level, LEVEL_START_BAR[level] + index, request,
                                 f"FINISH{len(LEVEL_LENGTHS) - level}" if finish else labels[request],
                                 request_slot.get(str(request)), finish,
                                 FINISH_NOTE if finish else "", cell, anim))
    return rows


COLUMNS = ("Level", "Bar", "Request", "Label", "Slot", "BAG1 origin", "BAG1 anim", "Note")


class ComboView(QWidget):
    """Character picker + BAG2 grid table + BAG1 reference text. Emits (character, slot) on selection."""
    slot_selected = Signal(str, int)

    def __init__(self) -> None:
        super().__init__()
        self._request_slot: Mapping[str, int] = {}
        self._rows: list[ComboRow] = []
        self.picker = QComboBox()
        self.picker.currentTextChanged.connect(self.refresh)
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(list(COLUMNS))
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.currentCellChanged.connect(self._on_row)
        self.reference = QPlainTextEdit(bag1_ladder_text())
        self.reference.setReadOnly(True)
        self.reference.setMaximumHeight(150)
        layout = QVBoxLayout(self)
        layout.addWidget(self.picker)
        layout.addWidget(self.table, 1)
        layout.addWidget(self.reference)

    def set_tables(self, tables: Mapping) -> None:
        """Load the character list and the global request->slot table from move_tables.json data."""
        self._request_slot = tables.get("global", {}).get("request_slot", {})
        self.picker.blockSignals(True)
        self.picker.clear()
        self.picker.addItems([char["name"] for char in tables["characters"]])
        self.picker.blockSignals(False)
        self.refresh(self.picker.currentText())

    def set_character(self, name: str) -> None:
        if name and self.picker.findText(name) >= 0:
            self.picker.setCurrentText(name)

    def refresh(self, character: str) -> None:
        self._rows = bag2_rows(self._request_slot, character)
        self.table.setRowCount(len(self._rows))
        for r, row in enumerate(self._rows):
            cells = (f"L{row.level}", row.bar, row.request, row.label,
                     "-" if row.slot is None else row.slot, row.bag1_cell,
                     "" if row.bag1_anim is None else row.bag1_anim, row.note)
            for c, value in enumerate(cells):
                self.table.setItem(r, c, QTableWidgetItem(str(value)))
        self.table.resizeColumnsToContents()

    def _on_row(self, row: int, *_ignored: int) -> None:
        if 0 <= row < len(self._rows) and self._rows[row].slot is not None:
            self.slot_selected.emit(self.picker.currentText(), self._rows[row].slot)

