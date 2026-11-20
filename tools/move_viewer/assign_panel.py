"""Reassignment panel (F2): pick a Dance View slot and a motion from the bank, queue swaps,
then generate a disabled disc_user mod with swap_mod.py.

An assignment is a swap inside the motion bank: slot S receives motion M and M's old
position receives S's motion, so the bank keeps its size and fits the stock sectors.
Slots >= the bank length (fever/duet, location unknown) cannot be reassigned.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton,
                               QVBoxLayout, QWidget)

from .swap_mod import split_bank

MOTION_ROLE = Qt.ItemDataRole.UserRole


def motion_rows(bank: bytes) -> list[str]:
    """One label per motion: hex index, byte size and short content hash."""
    motions, _ = split_bank(bank)
    return [f'0x{i:02X}  {len(m) - 4:6d} B  {hashlib.sha256(m[4:]).hexdigest()[:8]}'
            for i, m in enumerate(motions)]


def apply_swaps(order: list[int], pairs: list[tuple[int, int]]) -> list[int]:
    """Original motion index held by each slot after the queued swaps."""
    order = list(order)
    for a, b in pairs:
        order[a], order[b] = order[b], order[a]
    return order


class AssignPanel(QWidget):
    """Motion list + queued assignments for one character."""

    def __init__(self, preview: Callable[[int], None],
                 generate: Callable[[Path, list[tuple[int, int]]], str]):
        super().__init__()
        self._preview, self._generate = preview, generate
        self.bank_path: Path | None = None
        self.slot: int | None = None
        self.pairs: list[tuple[int, int]] = []
        self._count = 0
        self.motions = QListWidget()
        self.motions.currentItemChanged.connect(self._motion_selected)
        self.pending = QListWidget()
        self.target = QLabel('Casilla: -')
        self.assign_button = QPushButton('Asignar a la casilla (intercambia)')
        self.assign_button.clicked.connect(self.assign)
        undo = QPushButton('Deshacer última')
        undo.clicked.connect(self.undo)
        build = QPushButton('Generar mod (desactivado)')
        build.clicked.connect(self.build)
        self.result = QLabel('')
        self.result.setWordWrap(True)
        buttons = QHBoxLayout()
        for button in (self.assign_button, undo, build):
            buttons.addWidget(button)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('Movimientos del banco (001.bin)'))
        layout.addWidget(self.motions, 3)
        layout.addWidget(self.target)
        layout.addLayout(buttons)
        layout.addWidget(QLabel('Asignaciones pendientes'))
        layout.addWidget(self.pending, 1)
        layout.addWidget(self.result)

    def set_character(self, bank_path: Path | None) -> None:
        if bank_path == self.bank_path:
            return
        self.bank_path, self.pairs = bank_path, []
        self.motions.clear()
        self._count = 0
        if bank_path is not None and bank_path.is_file():
            rows = motion_rows(bank_path.read_bytes())
            self._count = len(rows)
            for i, row in enumerate(rows):
                item = QListWidgetItem(row)
                item.setData(MOTION_ROLE, i)
                self.motions.addItem(item)
        self._refresh()

    def set_slot(self, slot: int | None, label: str = '') -> None:
        self.slot = slot
        editable = slot is not None and slot < self._count
        self.target.setText(f'Casilla: {label} (posición 0x{slot:02X})' if slot is not None
                            else 'Casilla: -')
        if slot is not None and not editable:
            self.target.setText(self.target.text() + ' — fuera del banco, solo lectura')
        self.assign_button.setEnabled(editable)

    def _motion_selected(self, item: QListWidgetItem | None, _previous=None) -> None:
        if item is not None:
            self._preview(item.data(MOTION_ROLE))

    def assign(self) -> None:
        item = self.motions.currentItem()
        if item is None or self.slot is None or self.slot >= self._count:
            return
        order = apply_swaps(list(range(self._count)), self.pairs)
        motion = order.index(item.data(MOTION_ROLE))
        if motion != self.slot:
            self.pairs.append((self.slot, motion))
        self._refresh()

    def undo(self) -> None:
        if self.pairs:
            self.pairs.pop()
        self._refresh()

    def build(self) -> None:
        if self.bank_path is None or not self.pairs:
            self.result.setText('Nada que generar.')
            return
        try:
            self.result.setText(self._generate(self.bank_path, list(self.pairs)))
        except (OSError, ValueError) as error:
            self.result.setText(f'Error: {error}')

    def _refresh(self) -> None:
        self.pending.clear()
        order = apply_swaps(list(range(self._count)), self.pairs)
        for a, b in self.pairs:
            self.pending.addItem(f'intercambio 0x{a:02X} <-> 0x{b:02X}')
        changed = [i for i, m in enumerate(order) if m != i]
        if changed:
            self.pending.addItem('resultado: ' + ', '.join(f'0x{i:02X}=mov 0x{order[i]:02X}'
                                                           for i in changed))
