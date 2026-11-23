"""CPU worker completion is all-or-nothing and runs outside the caller thread."""
import threading
import struct
import unittest

import numpy as np
from PySide6.QtCore import Qt

from tools.move_viewer.preparation_worker import PreparationWorker


class WorkerTest(unittest.TestCase):
    def test_decode_failure_reports_error_without_publishing_frames(self):
        for error in (struct.error('invalid record'), OverflowError('invalid coordinates'),
                      SystemExit('renderer exited'), RuntimeError('renderer failed'),
                      MemoryError('allocation failed')):
            with self.subTest(error=type(error).__name__):
                def render(key):
                    raise error

                worker = PreparationWorker([0], render, 12)
                output, failures = [], []
                worker.prepared.connect(output.append, Qt.ConnectionType.DirectConnection)
                worker.failed.connect(failures.append, Qt.ConnectionType.DirectConnection)
                worker.start()
                self.assertTrue(worker.wait(5000))
                self.assertEqual(output, [])
                self.assertEqual(failures, [str(error)])

    def test_worker_prepares_off_caller_thread(self):
        caller = threading.get_ident()
        threads, output, progress = [], [], []

        def render(key):
            threads.append(threading.get_ident())
            return np.full((2, 2, 3), key, dtype=np.uint8)

        worker = PreparationWorker([1, 2], render, 24)
        worker.prepared.connect(output.append, Qt.ConnectionType.DirectConnection)
        worker.progress.connect(lambda done, total: progress.append((done, total)),
                                Qt.ConnectionType.DirectConnection)
        worker.start()
        self.assertTrue(worker.wait(5000))
        self.assertTrue(all(value != caller for value in threads))
        self.assertEqual(progress, [(1, 2), (2, 2)])
        self.assertEqual(len(output[0]), 2)

    def test_cancelled_worker_never_publishes(self):
        worker = PreparationWorker([0], lambda key: np.zeros((2, 2, 3), np.uint8), 12)
        output = []
        worker.prepared.connect(output.append, Qt.ConnectionType.DirectConnection)
        worker.cancel()
        worker.start()
        self.assertTrue(worker.wait(5000))
        self.assertEqual(output, [])
