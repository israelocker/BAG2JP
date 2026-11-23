"""Qt worker for CPU-only frame preparation; never creates GUI pixmaps."""
from collections.abc import Callable, Sequence
from threading import Event, Lock
import struct

import numpy as np
from PySide6.QtCore import QCoreApplication, QObject, QThread, Signal, Slot

from .frame_preparation import prepare_frames

# Cross-view serialization also covers jobs whose requesting QWidget was destroyed.
_RENDER_LOCK = Lock()


class _WorkerLifetime(QObject):
    """Application-owned retention independent of any view's destruction."""

    def __init__(self, application: QCoreApplication) -> None:
        super().__init__(application)
        self.workers: set[PreparationWorker] = set()
        application.aboutToQuit.connect(self.shutdown)

    @Slot()
    def release(self) -> None:
        """Release a finished worker without relying on a surviving view."""
        self.workers.discard(self.sender())

    @Slot()
    def shutdown(self) -> None:
        """Cancel and join at application exit, when queued GUI cleanup stops."""
        workers = tuple(self.workers)
        for worker in workers:
            worker.cancel()
        for worker in workers:
            worker.wait()
        self.workers.clear()


def _retain_worker(worker: 'PreparationWorker') -> None:
    """Keep active Qt workers alive even if their requesting widget is deleted."""
    application = QCoreApplication.instance()
    if application is None:
        return
    lifetime = getattr(application, '_frame_preparation_lifetime', None)
    if lifetime is None:
        lifetime = _WorkerLifetime(application)
        application._frame_preparation_lifetime = lifetime
    lifetime.workers.add(worker)
    worker.finished.connect(lifetime.release)


class PreparationWorker(QThread):
    """Prepare one immutable rendering request with cooperative cancellation."""

    progress = Signal(int, int)
    prepared = Signal(object)
    failed = Signal(str)

    def __init__(self, keys: Sequence[int], render: Callable[[int], np.ndarray],
                 max_bytes: int) -> None:
        super().__init__()
        self._keys = tuple(keys)
        self._render = render
        self._max_bytes = max_bytes
        self._cancel = Event()

    def start(self, priority: QThread.Priority = QThread.Priority.InheritPriority) -> None:
        """Retain only started jobs; pending requests can still be discarded safely."""
        _retain_worker(self)
        super().start(priority)

    def cancel(self) -> None:
        """Discard this request after the current CPU render returns."""
        self._cancel.set()

    def run(self) -> None:
        """Emit complete RGB buffers only; cancellation never emits partial output."""
        try:
            with _RENDER_LOCK:
                frames = prepare_frames(self._keys, self._render, self._max_bytes,
                                        self._cancel, self.progress.emit)
                if frames is not None and not self._cancel.is_set():
                    self.prepared.emit(frames)
        except (OSError, ValueError, IndexError, KeyError, TypeError,
                  ArithmeticError, struct.error, SystemExit, RuntimeError, MemoryError) as error:
            if not self._cancel.is_set():
                self.failed.emit(str(error))
