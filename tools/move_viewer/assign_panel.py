"""Reassignment panel (F2): pick a Dance View slot and a motion from the bank, queue
assignments, then generate a disabled disc_user mod with swap_mod.py.

An assignment copies the original motion M into slot S; every other slot is untouched.
A duration different from the slot's original only warns (it may look cut or frozen).
A "Banco origen" selector copies from another bank instead (the BAG1 variant of the same
character, or another character); swap_mod.require_compatible blocks sources whose skeleton,
node->track map or tracks differ, except for reviewed retarget profiles. Comparison uses
the original source model beside the exact generated result on the target model.
Growth uses each character's measured RAM budget;
disc placement and reservations are checked by the package planner before writing.
Slots >= the bank length (fever/duet) are read-only.
"""
from __future__ import annotations

import hashlib
import struct
from dataclasses import replace
from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
                               QPushButton, QVBoxLayout, QWidget)

from .pose import decode_motion, is_empty_motion
from .swap_mod import (GROWTH_BUDGET, BankSource, CrossBank, copy_growth,
                       require_compatible, split_bank)

MOTION_ROLE = Qt.ItemDataRole.UserRole


def motion_rows(bank: bytes) -> list[str]:
    """One label per motion: hex index, byte size and short content hash."""
    motions, _ = split_bank(bank)
    return [f'0x{i:02X}  {len(m) - 4:6d} B  {hashlib.sha256(m[4:]).hexdigest()[:8]}'
            + ('  (vacío)' if is_empty_motion(m[4:]) else '')
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
                     source: int, max_growth: int = 0,
                     cross: CrossBank | None = None) -> tuple[bool, str]:
    """(allowed, message) for adding slot <- source to the queued pairs.

    max_growth is the character's measured budget (swap_mod.GROWTH_BUDGET), 0 if none.
    With `cross`, `source` indexes cross.source.bank and incompatible banks are blocked.
    """
    if cross is not None:
        try:
            require_compatible(cross, [*pairs, (slot, source)])
        except ValueError as error:
            return False, ('Banco origen incompatible, bloqueado: ' + str(error))
    try:
        growth = copy_growth(bank, [*pairs, (slot, source)], cross=cross)
    except ValueError as error:
        return False, f'Copia bloqueada: {error}'
    if growth > max_growth:
        return False, (f'No cabe: el banco crecería {growth} bytes (permitido {max_growth}) y '
                       f'se escribiría sobre memoria o datos del disco. Bloqueado.')
    notes = []
    if growth > 0:
        notes.append(f'Crece {growth} de {max_growth} bytes medidos: jugador 1 y 2 con traje A, '
                     f'los otros trajes conservan el original.')
    want = motion_frames(bank, slot)
    got = motion_frames(cross.source.bank if cross else bank, source)
    if want is not None and got is not None and want != got:
        notes.append(f'Aviso: 0x{source:02X} dura {got} fotogramas y la casilla original '
                     f'{want}; puede verse cortado, congelado o con un salto.')
    if cross is not None:
        notes.append('Aviso: proporciones, traslación de raíz y eventos (golpes, sonidos) vienen '
                     f'de {cross.source.label}; sin verificar en partida.')
    return True, ' '.join(notes) or 'OK: misma duración.'


class AssignPanel(QWidget):
    """Motion list + queued assignments for one character.

    preview(index) draws an own motion; preview(index, bank, cross, slot) compares a copy.
    preview(None) invalidates a comparison after a selection change.
    generate(bank_path, pairs) builds the mod; generate(bank_path, pairs, cross) when the
    pairs copy from another bank.
    """

    def __init__(self, preview: Callable[..., None], generate: Callable[..., str]):
        super().__init__()
        self._preview, self._generate = preview, generate
        self.bank_path: Path | None = None
        self._bank = b''
        self._sources: list[BankSource] = []
        self._pair_source = 0          # combo index every queued pair copies from
        self.source_box = QComboBox()
        self.source_box.currentIndexChanged.connect(self._source_changed)
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
        layout.addWidget(QLabel('Banco origen'))
        layout.addWidget(self.source_box)
        layout.addWidget(QLabel('Movimientos del banco origen (001.bin)'))
        layout.addWidget(self.motions, 3)
        layout.addWidget(self.target)
        layout.addLayout(buttons)
        layout.addWidget(QLabel('Asignaciones pendientes'))
        layout.addWidget(self.pending, 1)
        layout.addWidget(self.result)

    def set_character(self, bank_path: Path | None,
                      sources: list[BankSource] | None = None) -> None:
        """Show `bank_path`'s motions; `sources` = [own, BAG1 variant, others...] when known."""
        if bank_path == self.bank_path:
            return
        self.bank_path, self.pairs, self._pair_source = bank_path, [], 0
        self._bank = bank_path.read_bytes() if bank_path is not None and bank_path.is_file() else b''
        self._sources = list(sources) if sources and self._bank else []
        self.source_box.blockSignals(True)
        self.source_box.clear()
        self.source_box.addItems([s.label for s in self._sources] or ['banco propio'])
        self.source_box.blockSignals(False)
        self._count = len(motion_rows(self._bank)) if self._bank else 0
        self._fill_motions(self._bank)
        self._refresh()

    def _fill_motions(self, bank: bytes) -> None:
        self.motions.clear()
        for i, row in enumerate(motion_rows(bank) if bank else []):
            item = QListWidgetItem(row)
            item.setData(MOTION_ROLE, i)
            self.motions.addItem(item)

    def _selected(self) -> int:
        return max(0, self.source_box.currentIndex())

    def _source_bank(self) -> bytes:
        index = self._selected()
        return self._sources[index].bank if index and index < len(self._sources) else self._bank

    def _cross(self, index: int) -> CrossBank | None:
        """Copy relation for combo `index` (None: copies inside the own bank)."""
        if not index or index >= len(self._sources):
            return None
        return CrossBank(replace(self._sources[0], bank=self._bank), self._sources[index])

    def _source_changed(self, _index: int) -> None:
        self._preview(None)
        self._fill_motions(self._source_bank())
        self.result.setText('')

    def set_slot(self, slot: int | None, label: str = '') -> None:
        self.slot = slot
        editable = slot is not None and slot < self._count
        self.target.setText(f'Casilla: {label} (posición 0x{slot:02X})' if slot is not None
                            else 'Casilla: -')
        if slot is not None and not editable:
            self.target.setText(self.target.text() + ' — fuera del banco, solo lectura')
        self.assign_button.setEnabled(editable)

    def _motion_selected(self, item: QListWidgetItem | None, _previous=None) -> None:
        if item is None:
            self._preview(None)
            return
        if self._selected():
            self._preview(item.data(MOTION_ROLE), self._source_bank(),
                          self._cross(self._selected()), self.slot)
        else:
            self._preview(item.data(MOTION_ROLE))

    def assign(self) -> None:
        item = self.motions.currentItem()
        if item is None or self.slot is None or self.slot >= self._count:
            return
        source, chosen = item.data(MOTION_ROLE), self._selected()
        if self.pairs and chosen != self._pair_source:
            self.result.setText('Las asignaciones pendientes usan otro banco origen; genera el mod '
                                'o deshazlas antes de cambiar de banco.')
            return
        pairs = [p for p in self.pairs if p[0] != self.slot]
        cross = self._cross(chosen)
        budget = GROWTH_BUDGET.get(self.bank_path.parents[1].name) if self.bank_path else None
        allowed, message = assignment_check(self._bank, pairs, self.slot, source,
                                            budget[1] if budget else 0, cross)
        if allowed:
            self._pair_source = chosen
            self.pairs = pairs + ([(self.slot, source)] if cross or source != self.slot else [])
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
            cross = self._cross(self._pair_source)
            args = (self.bank_path, list(self.pairs)) + ((cross,) if cross else ())
            self.result.setText(self._generate(*args))
        except (OSError, ValueError) as error:
            self.result.setText(f'Error: {error}')

    def _refresh(self) -> None:
        self.pending.clear()
        cross = self._cross(self._pair_source)
        origin = f' de {cross.source.label}' if cross else ''
        for slot, source in self.pairs:
            self.pending.addItem(f'casilla 0x{slot:02X} <- copia de 0x{source:02X}{origin}')
        if self.pairs:
            free = -copy_growth(self._bank, self.pairs, cross=cross)
            self.pending.addItem(f'margen: {free} bytes libres')
