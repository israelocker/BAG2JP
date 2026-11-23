"""CPU preparation must be bounded and discard canceled work."""
import threading
import unittest

import numpy as np

from tools.move_viewer.frame_preparation import prepare_frames


class FramePreparationTest(unittest.TestCase):
    def test_progress_reaches_total_only_after_all_frames(self):
        progress = []
        frames = prepare_frames([0, 3], lambda key: np.full((2, 2, 3), key, np.uint8),
                                24, threading.Event(), lambda done, total: progress.append((done, total)))
        self.assertEqual(len(frames), 2)
        self.assertEqual(progress, [(1, 2), (2, 2)])
        self.assertEqual(int(frames[1][0, 0, 0]), 3)

    def test_budget_failure_does_not_report_completion(self):
        progress = []
        with self.assertRaises(ValueError):
            prepare_frames([0, 1], lambda key: np.zeros((2, 2, 3), np.uint8),
                           12, threading.Event(), lambda *value: progress.append(value))
        self.assertNotIn((2, 2), progress)

    def test_cancellation_discards_partial_frames(self):
        cancel = threading.Event()

        def render(key):
            cancel.set()
            return np.zeros((2, 2, 3), np.uint8)

        self.assertIsNone(prepare_frames([0, 1], render, 24, cancel, lambda *_: None))
