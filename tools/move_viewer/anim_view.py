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
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from .model_codec import load_character
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

    def show_motion(self, character: str, slot: int | None) -> None:
        """Start looping motion `slot` of `character`; shows a message when unavailable."""
        self.timer.stop()
        self._frames, self._keys, self._index = [], [], 0
        if slot is None:
            self.image.clear()
            self.status.setText('-')
            return
        try:
            self._character = self._load(asset_folder(character))
            motion = decode_motion(self._character[1], slot)
        except (OSError, IndexError, ValueError, SystemExit) as error:
            self.image.clear()
            self.status.setText(f'{character} slot {slot}: no render ({error})')
            return
        self._motion = motion
        self._keys = list(range(0, motion['frames'], max(1, motion['step'])))
        self._frames = [None] * len(self._keys)
        self.timer.start(round(GAME_FRAME_MS * max(1, motion['step'])))
        self.advance()

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

    def advance(self) -> None:
        if not self._frames:
            return
        self.image.setPixmap(self.frame_pixmap(self._index))
        self.status.setText(f"frame {self._keys[self._index]}/{self._motion['frames'] - 1}"
                            f" (step {self._motion['step']})")
        self._index = (self._index + 1) % len(self._frames)
