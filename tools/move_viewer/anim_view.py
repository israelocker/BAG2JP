"""Qt widget that plays a character motion with the offline software renderer (F1).

Frames are rendered on demand and cached; playback runs at the motion's key step
(60 Hz game frames). Same assumptions as render_offline.py (orthographic camera,
approximate lighting, linear interpolation).
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
from PySide6.QtCore import Qt, QSignalBlocker, QTimer, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget
from .preparation_worker import PreparationWorker
from tools.workflow.project_config import load_config, require_values

from .model_codec import load_character, parse_model, parse_tim
import struct
from .pose import decode_motion, pose_model, sample_motion, world_meshes
from .render_offline import character_slot_map, render
from .scene import (COMPANION_CHARACTERS, CharacterScene, companion_slot, load_scene,
                    pose_scene, pose_snapshot_scene)
from .render_offline import render_scene
from .pose import animlib
from .companion_reference import load_reference, reference_matches

anim_list = animlib.anim_list

GAME_FRAME_MS = 1000 / 60
RENDER_SIZE = (300, 430)
VIEW_YAW = 180
# Render/parse failures that must stop playback and report instead of leaving a timer alive.
RENDER_ERRORS = (OSError, IndexError, KeyError, TypeError, ValueError, ArithmeticError,
                 struct.error, SystemExit)


def asset_folder(name: str) -> str:
    """Move-table character name -> assets/archive/characters folder (e.g. 'KITTY-N' -> 'kitty_n')."""
    return re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')


class AnimationView(QWidget):
    static_reference_shown = Signal()
    preparation_ready = Signal()
    preparation_failed = Signal()

    def show_native_snapshot(self, scene, contexts, evidence: str) -> bool:
        """Display an explicitly captured reference, never start inferred playback."""
        self.cancel_preparation()
        self.timer.stop()
        self._scene = self._motion = None
        self._frames, self._keys, self._index = [], [], 0
        self.image.clear()
        try:
            actors = pose_snapshot_scene(scene, contexts)
            rgb = np.ascontiguousarray(render_scene(actors, size=RENDER_SIZE, yaw_deg=VIEW_YAW))
            height, width, _ = rgb.shape
            image = QImage(rgb.data, width, height, rgb.strides[0], QImage.Format.Format_RGB888)
            self.image.setPixmap(QPixmap.fromImage(image.copy()))
            self.status.setText(f'{evidence} — captured roots; approximate rotations; static reference')
            self.static_reference_shown.emit()
            return True
        except RENDER_ERRORS as error:
            self.status.setText(f'snapshot unavailable: {error}')
            self.static_reference_shown.emit()
            return False

    def __init__(self, characters_dir: Path, variant: str = 'a_p1'):
        super().__init__()
        self.characters_dir = characters_dir
        self.variant = variant
        self.image = QLabel()
        self.image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image.setMinimumSize(*RENDER_SIZE)
        self.status = QLabel('-')
        self.progress = QProgressBar()
        self.progress.hide()
        self._worker = None
        self._workers = set()
        self._prepared = False
        self.external_clock = False
        self.reference_button = QPushButton('Captured companion reference (A/P1)')
        self.reference_button.setEnabled(False)
        self.reference_button.clicked.connect(self.show_captured_reference)
        self._reference_character = None
        layout = QVBoxLayout(self)
        layout.addWidget(self.image, 1)
        layout.addWidget(self.status)
        layout.addWidget(self.progress)
        layout.addWidget(self.reference_button)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.advance)
        self._characters: dict[str, tuple] = {}
        self._frames: list[QPixmap | None] = []
        self._keys: list[int] = []
        self._index = 0
        self._motion = None
        self._character = None
        self._scene = None

    def show_captured_reference(self) -> bool:
        """Open the verified static reference separately from selected-motion playback."""
        self.cancel_preparation()
        self.timer.stop()
        self._scene = self._motion = None
        self._frames, self._keys, self._index = [], [], 0
        self.image.clear()
        try:
            scene, contexts, label = load_reference(self.characters_dir, self._reference_character)
            return self.show_native_snapshot(scene, contexts, label)
        except RENDER_ERRORS as error:
            self.timer.stop()
            self._scene = self._motion = None
            self._frames, self._keys, self._index = [], [], 0
            self.image.clear()
            self.status.setText(f'reference unavailable: {error}')
            self.static_reference_shown.emit()
            return False

    def show_scene(self, scene: CharacterScene, slot: int, placements) -> bool:
        """Preview an explicit actor scene without guessing native placement."""
        self.cancel_preparation()
        self.timer.stop()
        self._frames, self._keys, self._index = [], [], 0
        self._motion = None
        self.image.clear()
        self._scene = None
        try:
            if len(scene.models) == 2:
                if placements is None:
                    raise ValueError('selected motion has no verified joint placement; '
                                     'use Captured companion reference (A/P1) for a separate '
                                     'static reference, not playback of this motion')
                if not reference_matches(self.characters_dir, scene.character):
                    raise ValueError('scene assets not verified for explicit placement')
            slots = [slot]
            if len(scene.models) == 2:
                slots.append(companion_slot(scene.character, slot, len(anim_list(scene.bank))))
            motions = [decode_motion(scene.bank, index) for index in slots]
            duration = min(motion['frames'] for motion in motions)
            if duration <= 0:
                raise ValueError('scene has no shared frames')
            self._scene = (scene, slot, placements)
            return self._start_motion(dict(motions[0], frames=duration))
        except RENDER_ERRORS as error:
            self._scene = None
            self.status.setText(f'scene unavailable: {error}')
            return False

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
        self.cancel_preparation()
        self._frames, self._keys, self._index = [], [], 0
        self.image.clear()
        self._motion = None
        self._scene = None
        self._reference_character = asset_folder(character)
        self.reference_button.setEnabled(self._reference_character in COMPANION_CHARACTERS)
        if slot is None:
            self.image.clear()
            self.status.setText('-')
            return False
        try:
            self._scene = None
            folder = asset_folder(character)
            if folder in COMPANION_CHARACTERS:
                base = self.characters_dir / folder
                scene = load_scene(base / f'model_{self.variant}', base / f'pack_{self.variant}')
                return self.show_scene(scene, slot, placements=None)
            self._character = self._load(folder)
            motion = decode_motion(self._character[1] if bank is None else bank, slot)
        except RENDER_ERRORS as error:
            self.image.clear()
            self._scene = self._motion = None
            self._frames, self._keys, self._index = [], [], 0
            self._reference_character = None
            self.reference_button.setEnabled(False)
            self.status.setText(f'{character} slot {slot}: no render ({error})')
            return False
        return self._start_motion(motion)

    def show_source(self, source, slot: int) -> bool:
        """Render raw source motion on its own model, textures and native slot map."""
        self.cancel_preparation()
        self._reference_character = None
        self.reference_button.setEnabled(False)
        self.timer.stop()
        self._frames, self._keys, self._index = [], [], 0
        self._motion = None
        self.image.clear()
        try:
            self._scene = None
            if source.model_data is None or source.skeleton.slot_map is None:
                raise ValueError('source model or slot map unavailable')
            model = parse_model(source.model_data, allow_zero_padding=True)
            tims = [parse_tim(data) for data in source.texture_data]
            self._character = (model, source.bank, tims, source.skeleton.slot_map)
            motion = decode_motion(source.bank, slot)
        except RENDER_ERRORS as error:
            self.status.setText(f'{source.label}: no render ({error})')
            return False
        return self._start_motion(motion)

    def _start_motion(self, motion) -> bool:
        if getattr(self, '_close_pending', False):
            self.status.setText('view closed; preparation rejected')
            return False
        self.cancel_preparation()
        frames = motion.get('frames', 0)
        if not frames:
            self.timer.stop()
            self._motion = None
            self._frames, self._keys, self._index = [], [], 0
            self.status.setText('motion has no frames')
            return False
        self._motion = motion
        self._keys = list(range(0, motion['frames'], max(1, motion['step'])))
        self._frames = [None] * len(self._keys)
        try:
            budget, = require_values(load_config(repo_root=Path(__file__).resolve().parents[2]),
                                      ('viewer.preparation_cache_bytes',))
            if self.external_clock:
                budget //= 2  # Both comparison panels share the configured allowance.
            # RGB (3) + pixmap (4) per frame, plus one RGB conversion copy (3).
            # Renderer geometry, z-buffer and allocator overhead are not cache bytes.
            required = (len(self._keys) * 7 + 3) * RENDER_SIZE[0] * RENDER_SIZE[1]
            if required > budget:
                raise ValueError('selected motion exceeds preparation cache budget')
            worker = PreparationWorker(tuple(self._keys), self._render_request(), budget // 2)
            self.destroyed.connect(worker.cancel)
            self._worker = worker
            self._workers.add(worker)
            worker.progress.connect(self._preparation_progress)
            worker.prepared.connect(self._preparation_complete)
            worker.failed.connect(self._preparation_error)
            worker.finished.connect(self._preparation_finished)
            self.progress.setRange(0, len(self._keys))
            self.progress.setValue(0)
            self.progress.show()
            self.status.setText('Preparing selected motion…')
            if not any(old is not worker for old in self._workers):
                worker.start()
            else:
                self.status.setText('Waiting for cancelled preparation to release buffers…')
            return True
        except RENDER_ERRORS as error:
            self.status.setText(f'preparation unavailable: {error}')
            self._frames = []
            return False

    def cancel_preparation(self) -> None:
        """Discard stale output without waiting for CPU work on the GUI thread."""
        self.timer.stop()
        if self._worker is not None:
            self._worker.cancel()
            if not self._worker.isRunning() and not self._worker.isFinished():
                self._workers.discard(self._worker)
                self._worker.deleteLater()
        self._worker = None
        self._prepared = False
        self.progress.hide()

    def _preparation_progress(self, done: int, total: int) -> None:
        if self.sender() is self._worker:
            self.progress.setRange(0, total)
            self.progress.setValue(done)

    def _preparation_complete(self, buffers: list[np.ndarray]) -> None:
        if self.sender() is not self._worker:
            buffers.clear()
            return
        try:
            pixmaps = []
            for rgb in buffers:
                h, w, _ = rgb.shape
                image = QImage(rgb.data, w, h, rgb.strides[0], QImage.Format.Format_RGB888)
                pixmaps.append(QPixmap.fromImage(image.copy()))
            self._frames = pixmaps
            self._prepared = True
            self.progress.setValue(self.progress.maximum())
            if not self.advance():
                self._preparation_error('prepared frame could not be displayed')
                return
            if not self.external_clock:
                self.timer.start(round(GAME_FRAME_MS * max(1, self._motion['step'])))
            self.preparation_ready.emit()
        except RENDER_ERRORS as error:
            self._preparation_error(str(error))
        finally:
            # Release queued RGB ownership before a finished worker starts its successor.
            buffers.clear()

    def _preparation_error(self, message: str) -> None:
        if self.sender() is not self._worker:
            return
        self.cancel_preparation()
        self._frames = []
        self.image.clear()
        self.status.setText(f'preparation failed: {message}')
        self.preparation_failed.emit()

    def _preparation_finished(self) -> None:
        worker = self.sender()
        pending = self._worker
        resume_pending = pending is not None and pending is not worker and not pending.isRunning()
        if worker is self._worker:
            self._worker = None
        self._workers.discard(worker)
        worker.deleteLater()
        if getattr(self, '_close_pending', False):
            if not self._workers:
                self.close()
            return
        if resume_pending and not any(old is not pending for old in self._workers):
            self.status.setText('Preparing selected motion…')
            pending.start()

    def closeEvent(self, event) -> None:
        """Keep worker objects alive until their cooperative shutdown completes."""
        self._close_pending = True
        self.cancel_preparation()
        for worker in tuple(self._workers):
            worker.cancel()
        if self._workers:
            self.hide()
            event.ignore()
            return
        super().closeEvent(event)

    def frame_pixmap(self, i: int) -> QPixmap:
        if self._frames[i] is None:
            rgb = self._render_request()(self._keys[i])
            h, w, _ = rgb.shape
            self._frames[i] = QPixmap.fromImage(QImage(rgb.data, w, h, 3 * w,
                                                        QImage.Format.Format_RGB888).copy())
        return self._frames[i]

    def _render_request(self):
        """Capture request inputs so CPU rendering never reads changing widget state."""
        selected_scene = self._scene
        character, motion = self._character, self._motion

        def render_frame(frame: int) -> np.ndarray:
            if selected_scene is not None:
                scene, slot, placements = selected_scene
                actors = pose_scene(scene, slot, (float(frame),) * len(scene.models), placements)
                return np.ascontiguousarray(render_scene(actors, size=RENDER_SIZE, yaw_deg=VIEW_YAW))
            model, _, tims, slot_map = character
            poses = pose_model(model, sample_motion(motion, frame), slot_map)
            return np.ascontiguousarray(render(model, world_meshes(model, poses), tims,
                                              size=RENDER_SIZE, yaw_deg=VIEW_YAW))

        return render_frame

    def advance(self) -> bool:
        if not self._frames:
            return False
        try:
            self.image.setPixmap(self.frame_pixmap(self._index))
        except RENDER_ERRORS as error:
            self.timer.stop()
            self._scene = None
            self._motion = None
            self._frames, self._keys, self._index = [], [], 0
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
        for view in (self.source, self.result):
            view.external_clock = True
            view.preparation_ready.connect(self._start_when_ready)
            view.preparation_failed.connect(self.invalidate)
            view.static_reference_shown.connect(self.invalidate)

    def _start_when_ready(self) -> None:
        """The shared comparison clock starts only after both caches are complete."""
        if self.source._prepared and self.result._prepared:
            self.timer.start(round(GAME_FRAME_MS))

    def invalidate(self) -> None:
        """A static reference replaces the moving comparison; never leave a live clock."""
        self.timer.stop()
        origin = self.sender()
        for panel in (self.source, self.result):
            panel.cancel_preparation()
            panel.timer.stop()
            if panel is origin:
                continue
            panel._scene = panel._motion = None
            panel._frames, panel._keys, panel._index = [], [], 0
            panel.image.clear()
            panel.status.setText('Comparación invalidada: vista estática')

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
            self.timer.stop()
            for panel in (self.source, self.result):
                panel.cancel_preparation()
                panel.timer.stop()
                panel._scene = panel._motion = None
                panel._frames, panel._keys, panel._index = [], [], 0
                panel.image.clear()
                panel.status.setText('Comparación invalidada: vista incompleta')
            return False
        self._start_when_ready()
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
        self.source.close()
        self.result.close()
        super().closeEvent(event)
