"""Exercise Qt destruction in subprocesses so a thread abort cannot kill the suite."""
import os
import subprocess
import sys
import unittest


class PreparationLifetimeTest(unittest.TestCase):
    def test_real_view_parent_deletion_cancels_frames_before_successor(self):
        code = '''
import threading, time
import numpy as np
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication, QWidget
from tools.move_viewer.anim_view import AnimationView
from pathlib import Path
app = QApplication([])
parent = QWidget()
view = AnimationView(Path('unused'))
view.setParent(parent)
entered, release, successor = threading.Event(), threading.Event(), threading.Event()
calls = []
def old_render(key):
    calls.append(key)
    entered.set()
    assert release.wait(3)
    return np.zeros((2, 2, 3), np.uint8)
view._render_request = lambda: old_render
assert view._start_motion({'frames': 3, 'step': 1})
assert entered.wait(2)
parent.deleteLater()
QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
new = AnimationView(Path('unused'))
def new_render(key):
    successor.set()
    return np.zeros((2, 2, 3), np.uint8)
new._render_request = lambda: new_render
assert new._start_motion({'frames': 1, 'step': 1})
assert not successor.wait(.05), 'successor overlapped orphan render'
release.set()
deadline = time.monotonic() + 3
while not new._prepared and time.monotonic() < deadline:
    app.processEvents()
    time.sleep(.005)
assert new._prepared
assert calls == [0], calls
new.close()
app.processEvents()
print('safe real view replacement', flush=True)
'''
        result = subprocess.run([sys.executable, '-c', code],
            env={**os.environ, 'QT_QPA_PLATFORM': 'offscreen'},
            capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_parent_destruction_and_application_quit_keep_running_worker_alive(self):
        for action in ('parent', 'quit'):
            with self.subTest(action=action):
                code = '''
import gc, time, threading
import numpy as np
from PySide6.QtCore import QTimer, QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication, QWidget
from tools.move_viewer.preparation_worker import PreparationWorker
app = QApplication([])
parent = QWidget()
entered = threading.Event()
def render(key):
    entered.set()
    time.sleep(.15)
    return np.zeros((2, 2, 3), np.uint8)
worker = PreparationWorker([0], render, 12)
parent.worker = worker
worker.start()
assert entered.wait(2)
if ACTION == 'parent':
    parent.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    del parent, worker
    gc.collect()
    QTimer.singleShot(250, app.quit)
else:
    QTimer.singleShot(0, app.quit)
app.exec()
print('safe shutdown', flush=True)
'''.replace('ACTION', repr(action))
                result = subprocess.run([sys.executable, '-c', code],
                    env={**os.environ, 'QT_QPA_PLATFORM': 'offscreen'},
                    capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('safe shutdown', result.stdout)
