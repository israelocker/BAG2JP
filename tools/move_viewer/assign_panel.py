"""Reassignment panel (F2): pick a Dance View slot and a motion from the bank, queue
assignments, then generate a disabled disc_user mod with swap_mod.py.

An assignment copies the original motion M into slot S; every other slot is untouched.
A duration different from the slot's original only warns (it may look cut or frozen).
Growth of the bank is blocked: the entry must fit its stock disc extent and the in-RAM
motion buffer size is not verified. Slots >= the bank length (fever/duet) are read-only.
"""
from __future__ import annotations

import hashlib
import struct
from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton,
                               QVBoxLayout, QWidget)

from .pose import decode_motion
from .swap_mod import GROWTH_BUDGET, copy_growth, split_bank

MOTION_ROLE = Qt.ItemDataRole.UserRole


def motion_rows(bank: bytes) -> list[str]:
    """One label per motion: hex index, byte size and short content hash."""
    motions, _ = split_bank(bank)
    return [f'0x{i:02X}  {len(m) - 4:6d} B  {hashlib.sha256(m[4:]).hexdigest()[:8]}'
            for i, m in enumerate(motions)]


def apply_copies(order: list[int], pairs: list[tuple[int, int]]) -> list[int]:
    """Original motion index held by each slot after the queued slot<-source copies."""
    order = list(order)
    for slot, source in pairs:
        order[slot] = source
    return order


def motion_frames(bank: bytes, index: int) -> int | None:
    try:
        return decode_motion(bank, index)['frames']
    except (IndexError, ValueError, KeyError, struct.error):
        return None


def assignment_check(bank: bytes, pairs: list[tuple[int, int]], slot: int,
                     source: int, max_growth: int = 0) -> tuple[bool, str]:
    """(allowed, message) for adding slot <- source to the queued pairs.

    max_growth is the character's measured budget (swap_mod.GROWTH_BUDGET), 0 if none.
    """
    growth = copy_growth(bank, [*pairs, (slot, source)])
    if growth > max_growth:
        return False, (f'No cabe: el banco crecería {growth} bytes (permitido {max_growth}) y '
                       f'se escribiría sobre memoria o datos del disco. Bloqueado.')
    notes = []
    if growth > 0:
        notes.append(f'Crece {growth} de {max_growth} bytes medidos: solo jugador 1, '
                     f'jugador 2 conserva el original.')
    want, got = motion_frames(bank, slot), motion_frames(bank, source)
    if want is not None and got is not None and want != got:
        notes.append(f'Aviso: 0x{source:02X} dura {got} fotogramas y la casilla original '
                     f'{want}; puede verse cortado, congelado o con un salto.')
    return True, ' '.join(notes) or 'OK: misma duración.'


class AssignPanel(QWidget):
    """Motion list + queued assignments for one character."""

    def __init__(self, preview: Callable[[int], None],
                 generate: Callable[[Path, list[tuple[int, int]]], str]):
        super().__init__()
        self._preview, self._generate = preview, generate
        self.bank_path: Path | None = None
        self._bank = b''
        self.slot: int | None = None
        self.pairs: list[tuple[int, int]] = []
        self._count = 0
        self.motions = QListWidget()
        self.motions.currentItemChanged.connect(self._motion_selected)
        self.pending = QListWidget()
        self.target = QLabel('Casilla: -')
        self.assign_button = QPushButton('Asignar a la casilla (copia)')
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
        self._bank = b''
        if bank_path is not None and bank_path.is_file():
            self._bank = bank_path.read_bytes()
            rows = motion_rows(self._bank)
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
        source = item.data(MOTION_ROLE)
        pairs = [p for p in self.pairs if p[0] != self.slot]
        budget = GROWTH_BUDGET.get(self.bank_path.parents[1].name) if self.bank_path else None
        allowed, message = assignment_check(self._bank, pairs, self.slot, source,
                                            budget[1] if budget else 0)
        if allowed:
            self.pairs = pairs + ([(self.slot, source)] if source != self.slot else [])
        self._refresh()
        self.result.setText(message)

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
        for slot, source in self.pairs:
            self.pending.addItem(f'casilla 0x{slot:02X} <- copia de 0x{source:02X}')
        if self.pairs:
            self.pending.addItem(f'margen: {-copy_growth(self._bank, self.pairs)} bytes libres')
