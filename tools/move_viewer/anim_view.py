"""Qt widget that plays a character motion with the offline software renderer (F1).

Frames are rendered on demand and cached; playback runs at the motion's key step
(60 Hz game frames). Same assumptions as render_offline.py (orthographic camera,
approximate lighting, linear interpolation).
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from .model_codec import load_character, parse_model, parse_tim
import struct
from .pose import decode_motion, pose_model, sample_motion, world_meshes
from .render_offline import character_slot_map, render

GAME_FRAME_MS = 1000 / 60
RENDER_SIZE = (300, 430)
VIEW_YAW = 180


def asset_folder(name: str) -> str:
    """Move-table character name -> assets/archive/characters folder (e.g. 'KITTY-N' -> 'kitty_n')."""
    return re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')


class AnimationView(QWidget):
    def __init__(self, characters_dir: Path, variant: str = 'a_p1'):
        super().__init__()
        self.characters_dir = characters_dir
        self.variant = variant
        self.image = QLabel()
        self.image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image.setMinimumSize(*RENDER_SIZE)
        self.status = QLabel('-')
        layout = QVBoxLayout(self)
        layout.addWidget(self.image, 1)
        layout.addWidget(self.status)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.advance)
        self._characters: dict[str, tuple] = {}
        self._frames: list[QPixmap | None] = []
        self._keys: list[int] = []
        self._index = 0
        self._motion = None
        self._character = None

    def _load(self, folder: str):
        if folder not in self._characters:
            base = self.characters_dir / folder
            model, bank, tims = load_character(base / f'model_{self.variant}',
                                               base / f'pack_{self.variant}')
            costume = 0 if self.variant.startswith('a') else 1
            slot_map = character_slot_map(base / f'pack_{self.variant}', costume=costume)
            self._characters[folder] = (model, bank, tims, slot_map)
        return self._characters[folder]

    def show_motion(self, character: str, slot: int | None, bank: bytes | None = None) -> bool:
        """Start looping motion `slot` of `character`; shows a message when unavailable.

        `bank` previews that motion of another bank on the character's own model and slot map
        (what copying it into the character's bank produces); default: the character's bank.
        """
        self.timer.stop()
        self._frames, self._keys, self._index = [], [], 0
        self.image.clear()
        self._motion = None
        if slot is None:
            self.image.clear()
            self.status.setText('-')
            return False
        try:
            self._character = self._load(asset_folder(character))
            motion = decode_motion(self._character[1] if bank is None else bank, slot)
        except (OSError, IndexError, ValueError, struct.error, SystemExit) as error:
            self.image.clear()
            self.status.setText(f'{character} slot {slot}: no render ({error})')
            return False
        return self._start_motion(motion)

    def show_source(self, source, slot: int) -> bool:
        """Render raw source motion on its own model, textures and native slot map."""
        self.timer.stop()
        self._frames, self._keys, self._index = [], [], 0
        self._motion = None
        self.image.clear()
        try:
            if source.model_data is None or source.skeleton.slot_map is None:
                raise ValueError('source model or slot map unavailable')
            model = parse_model(source.model_data, allow_zero_padding=True)
            tims = [parse_tim(data) for data in source.texture_data]
            self._character = (model, source.bank, tims, source.skeleton.slot_map)
            motion = decode_motion(source.bank, slot)
        except (OSError, IndexError, ValueError, struct.error, SystemExit) as error:
            self.status.setText(f'{source.label}: no render ({error})')
            return False
        return self._start_motion(motion)

    def _start_motion(self, motion) -> bool:
        self._motion = motion
        self._keys = list(range(0, motion['frames'], max(1, motion['step'])))
        self._frames = [None] * len(self._keys)
        self.timer.start(round(GAME_FRAME_MS * max(1, motion['step'])))
        return self.advance()

    def frame_pixmap(self, i: int) -> QPixmap:
        if self._frames[i] is None:
            model, _, tims, slot_map = self._character
            poses = pose_model(model, sample_motion(self._motion, self._keys[i]), slot_map)
            rgb = np.ascontiguousarray(render(model, world_meshes(model, poses), tims,
                                              size=RENDER_SIZE, yaw_deg=VIEW_YAW))
            h, w, _ = rgb.shape
            self._frames[i] = QPixmap.fromImage(QImage(rgb.data, w, h, 3 * w,
                                                       QImage.Format.Format_RGB888).copy())
        return self._frames[i]

    def advance(self) -> bool:
        if not self._frames:
            return False
        try:
            self.image.setPixmap(self.frame_pixmap(self._index))
        except (IndexError, ValueError, KeyError) as error:
            self.timer.stop()
            self.image.clear()
            self.status.setText(f'render failed: {error}')
            return False
        self.status.setText(f"frame {self._keys[self._index]}/{self._motion['frames'] - 1}"
                            f" (step {self._motion['step']})")
        self._index = (self._index + 1) % len(self._frames)
        return True


class MotionComparison(QWidget):
    """Original source and exact generated motion, driven by one frame clock.

    Without source assets the left view is explicitly labelled as using the target model.
    Different durations loop independently at their original frame counts.
    """

    def __init__(self, characters_dir: Path):
        super().__init__()
        self.setWindowTitle('Comparación de copia — modelo destino en ambas vistas')
        self.source = AnimationView(characters_dir)
        self.result = AnimationView(characters_dir)
        layout = QHBoxLayout(self)
        self.source_label = QLabel('Origen sin adaptar (modelo destino)')
        for title, view in (('Origen sin adaptar (modelo destino)', self.source),
                            ('Resultado exacto del generador', self.result)):
            column = QVBoxLayout()
            column.addWidget(self.source_label if view is self.source else QLabel(title))
            column.addWidget(view)
            layout.addLayout(column)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.advance)
        self.frame = 0

    def show_banks(self, character: str, source_slot: int, source_bank: bytes,
                   target_slot: int, result_bank: bytes, *, source=None) -> bool:
        self.timer.stop()
        self.frame = 0
        self.setWindowTitle(f'{character}: origen 0x{source_slot:02X} → destino 0x{target_slot:02X}'
                            ' — ambas vistas usan modelo destino')
        self.source_label.setText('Origen: modelo original BAG1/BAG2' if source is not None
                                  else 'Origen sin adaptar (modelo destino)')
        ready = True
        for view, slot, bank in ((self.source, source_slot, source_bank),
                                 (self.result, target_slot, result_bank)):
            if view is self.source and source is not None:
                ready = bool(view.show_source(source, slot)) and ready
            else:
                ready = bool(view.show_motion(character, slot, bank)) and ready
            view.timer.stop()
        if source is not None:
            self.setWindowTitle(f'{source.label}: modelo original → {character}: resultado de copia')
        if not ready:
            return False
        self.timer.start(round(GAME_FRAME_MS))
        return True

    def advance(self) -> None:
        for view in (self.source, self.result):
            if view._frames and view._motion:
                local = self.frame % view._motion['frames']
                view._index = min(local // max(1, view._motion['step']), len(view._keys) - 1)
                if not view.advance():
                    self.timer.stop()
                    for panel in (self.source, self.result):
                        panel.image.clear()
                        panel.status.setText('Comparación invalidada: error de renderizado')
                    return
        self.frame += 1

    def closeEvent(self, event) -> None:
        self.timer.stop()
        self.source.timer.stop()
        self.result.timer.stop()
        super().closeEvent(event)
