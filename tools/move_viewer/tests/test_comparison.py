"""Comparison playback uses one clock and the exact generator output."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap
from tools.move_viewer import anim_view
from tools.move_viewer.assign_panel import AssignPanel, MOTION_ROLE
from tools.move_viewer.swap_mod import BankSource
from PySide6.QtWidgets import QListWidgetItem


class ComparisonTest(unittest.TestCase):
    def test_closed_view_rejects_new_preparation(self):
        view = anim_view.AnimationView(Path('unused'))
        view.close()
        with patch.object(anim_view, 'PreparationWorker') as worker:
            self.assertFalse(view._start_motion({'frames': 1, 'step': 1}))
            worker.assert_not_called()
        self.assertIn('closed', view.status.text())

    def test_close_does_not_wait_for_running_render(self):
        import threading
        import time
        import numpy as np
        from PySide6.QtTest import QTest
        view = anim_view.AnimationView(Path('unused'))
        entered, release = threading.Event(), threading.Event()
        def render(key):
            entered.set()
            release.wait(2)
            return np.zeros((2, 2, 3), dtype=np.uint8)
        try:
            with patch.object(view, '_render_request', return_value=render):
                self.assertTrue(view._start_motion({'frames': 1, 'step': 1}))
            self.assertTrue(entered.wait(1))
            started = time.monotonic()
            view.close()
            elapsed = time.monotonic() - started
            release.set()
            self.assertLess(elapsed, 0.2)
        finally:
            release.set()
            for _ in range(100):
                QApplication.processEvents()
                if not view._workers:
                    break
                QTest.qWait(5)
            view.close()

    def test_single_frame_budget_includes_conversion_copy(self):
        view = anim_view.AnimationView(Path('unused'))
        pixels = anim_view.RENDER_SIZE[0] * anim_view.RENDER_SIZE[1]
        with (patch.object(anim_view, 'require_values', return_value=(pixels * 9,)),
              patch.object(anim_view, 'PreparationWorker') as worker):
            self.assertFalse(view._start_motion({'frames': 1, 'step': 1}))
            worker.assert_not_called()
        view.close()

    def test_finished_worker_result_is_drained_before_successor_starts(self):
        import threading
        import numpy as np
        view = anim_view.AnimationView(Path('unused'))
        replacement_entered = threading.Event()
        motion = {'frames': 2, 'step': 1}
        try:
            with patch.object(view, '_render_request', return_value=lambda key: np.zeros((2, 2, 3), dtype=np.uint8)):
                self.assertTrue(view._start_motion(motion))
                old = view._worker
                self.assertTrue(old.wait(2000))  # Deliberately do not drain GUI signals.
            def replacement(key):
                replacement_entered.set()
                return np.ones((2, 2, 3), dtype=np.uint8)
            with patch.object(view, '_render_request', return_value=replacement):
                self.assertTrue(view._start_motion(motion))
                self.assertFalse(replacement_entered.wait(0.05))
                self.wait_prepared(view)
                self.assertTrue(replacement_entered.is_set())
        finally:
            view.close()

    def test_comparison_budget_is_shared_before_worker_start(self):
        view = anim_view.AnimationView(Path('unused'))
        view.external_clock = True
        frame_allowance = anim_view.RENDER_SIZE[0] * anim_view.RENDER_SIZE[1] * 8
        with (patch.object(anim_view, 'require_values', return_value=(frame_allowance,)),
              patch.object(anim_view, 'PreparationWorker') as worker):
            self.assertFalse(view._start_motion({'frames': 1, 'step': 1}))
            worker.assert_not_called()
        self.assertIn('budget', view.status.text())
        self.assertFalse(view.timer.isActive())

    def test_cancelled_preparation_cannot_replace_new_selection(self):
        import threading
        import numpy as np
        from PySide6.QtTest import QTest
        view = anim_view.AnimationView(Path('unused'))
        entered, release, replacement_entered = threading.Event(), threading.Event(), threading.Event()

        def new_render(frame):
            replacement_entered.set()
            return np.full((2, 2, 3), 200, dtype=np.uint8)

        def old_render(frame):
            entered.set()
            release.wait(2)
            return np.zeros((2, 2, 3), dtype=np.uint8)

        try:
            with patch.object(view, '_render_request', return_value=old_render):
                self.assertTrue(view._start_motion({'frames': 1, 'step': 1}))
            self.assertTrue(entered.wait(1))
            self.assertFalse(view.timer.isActive())
            with patch.object(view, '_render_request', return_value=new_render):
                self.assertTrue(view._start_motion({'frames': 2, 'step': 1}))
            QTest.qWait(30)
            self.assertFalse(replacement_entered.is_set(), 'replacement must wait for cancelled buffers to release')
            with patch.object(view, '_render_request', return_value=new_render):
                self.assertTrue(view._start_motion({'frames': 2, 'step': 1}))
            self.assertEqual(len(view._workers), 2, 'retain only running cancellation and latest pending request')
            release.set()
            self.wait_prepared(view)
            QTest.qWait(30)
            self.assertEqual(len(view._frames), 2)
            self.assertEqual(view._frames[0].toImage().pixelColor(0, 0).red(), 200)
            self.assertEqual(view.progress.value(), 2)
        finally:
            release.set()
            view.close()

    def tearDown(self):
        for widget in QApplication.topLevelWidgets():
            widget.close()
        QApplication.processEvents()

    def wait_prepared(self, view):
        from PySide6.QtTest import QTest
        for _ in range(200):
            QApplication.processEvents()
            if view._prepared or view.status.text().startswith('preparation failed:'):
                return
            QTest.qWait(5)
        self.fail('preparation did not finish')

    def test_cpu_render_request_keeps_original_selection(self):
        import numpy as np
        view = anim_view.AnimationView(Path('unused'))
        original_motion = {'frames': 2}
        view._character = ('original model', b'bank', ['textures'], ['slots'])
        view._motion = original_motion
        request = view._render_request()
        view._character = ('new model', b'other', [], [])
        view._motion = {'frames': 3}
        with (patch.object(anim_view, 'sample_motion', return_value='sample') as sample,
              patch.object(anim_view, 'pose_model', return_value='poses') as poses,
              patch.object(anim_view, 'world_meshes', return_value='world'),
              patch.object(anim_view, 'render', return_value=np.zeros((2, 2, 3), dtype=np.uint8))):
            self.assertEqual(request(1).shape, (2, 2, 3))
        sample.assert_called_once_with(original_motion, 1)
        poses.assert_called_once_with('original model', 'sample', ['slots'])
        view.close()

    def test_reference_load_failure_discards_previous_playback(self):
        view = anim_view.AnimationView(Path('unused'))
        view._scene, view._motion = ('old scene',), {'frames': 2}
        view._frames, view._keys = [None], [0]
        with patch.object(anim_view, 'load_reference', side_effect=ValueError('changed assets')):
            self.assertFalse(view.show_captured_reference())
        self.assertIsNone(view._scene)
        self.assertIsNone(view._motion)
        self.assertEqual(view._frames, [])
        view.close()

    def test_reference_button_dispatches_selected_companion(self):
        view = anim_view.AnimationView(Path('unused'))
        view.show_motion('Capoeira', None)
        self.assertTrue(view.reference_button.isEnabled())
        with (patch.object(anim_view, 'load_reference', return_value=('scene', ('context',), 'gf12401')) as load,
              patch.object(view, 'show_native_snapshot', return_value=True) as show):
            view.reference_button.click()
            load.assert_called_once_with(Path('unused'), 'capoeira')
            show.assert_called_once_with('scene', ('context',), 'gf12401')
        view.close()

    def test_native_snapshot_is_static_and_labels_approximate_rotations(self):
        import numpy as np
        view = anim_view.AnimationView(Path('unused'))
        with (patch.object(anim_view, 'pose_snapshot_scene', return_value=['both actors'], create=True),
              patch.object(anim_view, 'render_scene', return_value=np.zeros((4, 4, 3), dtype=np.uint8))):
            self.assertTrue(view.show_native_snapshot('scene', ('contexts',), 'recorded gf12401'))
        self.assertFalse(view.image.pixmap().isNull())
        self.assertFalse(view.timer.isActive())
        self.assertIn('approximate rotations', view.status.text())
        self.assertIn('static reference', view.status.text())
        self.assertIn('gf12401', view.status.text())
        view.close()

    def test_companion_selection_uses_scene_and_refuses_unknown_placement(self):
        from tools.move_viewer.scene import CharacterScene
        view = anim_view.AnimationView(Path('unused'))
        scene = CharacterScene(('primary', 'companion'), b'bank', [], [], 'capoeira')
        with (patch.object(anim_view, 'load_scene', return_value=scene, create=True) as load,
              patch.object(view, '_load', return_value=('primary', b'bank', [], [])),
              patch.object(anim_view, 'decode_motion', return_value={'frames': 5, 'step': 1}),
              patch.object(view, '_start_motion', return_value=True)):
            self.assertFalse(view.show_motion('Capoeira', 54))
            load.assert_called_once()
        self.assertIn('placement', view.status.text())
        self.assertIn('selected motion', view.status.text())
        self.assertIn('Captured companion reference', view.status.text())
        self.assertFalse(view.timer.isActive())
        view.close()

    def test_failed_scene_render_discards_context_and_cached_frames(self):
        view = anim_view.AnimationView(Path('.'))
        view._scene = ('previous scene', 54, 'previous placement')
        view._frames = [None]
        view._keys = [0]
        with patch.object(view, 'frame_pixmap', side_effect=ValueError('invalid context')):
            self.assertFalse(view.advance())
        self.assertIsNone(view._scene)
        self.assertEqual(view._frames, [])
        self.assertIsNone(view._motion)
        self.assertFalse(view.timer.isActive())
        view.close()

    def test_empty_selection_discards_joint_scene_context(self):
        view = anim_view.AnimationView(Path('unused'))
        view._scene = ('previous scene', 54, 'previous placement')
        self.assertFalse(view.show_motion('Capoeira', None))
        self.assertIsNone(view._scene)
        self.assertFalse(view.timer.isActive())
        self.assertTrue(view.image.pixmap().isNull())
        view.close()

    def test_joint_scene_renders_both_actors_with_explicit_context(self):
        import numpy as np
        from tools.move_viewer.scene import CharacterScene
        view = anim_view.AnimationView(Path('unused'))
        scene = CharacterScene(('primary', 'companion'), b'bank', [], [], 'capoeira')
        placements = (np.eye(4), np.eye(4))
        with (patch.object(anim_view, 'decode_motion', return_value={'frames': 5, 'step': 1}),
              patch.object(anim_view, 'companion_slot', return_value=101),
              patch.object(anim_view, 'anim_list', return_value=[None] * 118),
              patch.object(anim_view, 'reference_matches', return_value=True),
              patch.object(anim_view, 'pose_scene', return_value=['actor1', 'actor2']) as pose,
              patch.object(anim_view, 'render_scene', return_value=np.zeros((4, 4, 3), dtype=np.uint8)) as render):
            self.assertTrue(view.show_scene(scene, 54, placements))
            self.wait_prepared(view)
            self.assertEqual(pose.call_args_list[0].args[:3], (scene, 54, (0, 0)))
            self.assertEqual(render.call_count, len(view._keys))
            self.assertEqual(render.call_args.args[0], ['actor1', 'actor2'])
        view.close()

    def test_joint_scene_refuses_explicit_placement_on_unverified_assets(self):
        import numpy as np
        from tools.move_viewer.scene import CharacterScene
        view = anim_view.AnimationView(Path('unused'))
        scene = CharacterScene(('primary', 'companion'), b'bank', [], [], 'capoeira')
        with (patch.object(anim_view, 'reference_matches', return_value=False),
              patch.object(anim_view, 'pose_scene') as pose,
              patch.object(anim_view, 'decode_motion') as decode):
            self.assertFalse(view.show_scene(scene, 54, (np.eye(4), np.eye(4))))
            pose.assert_not_called()
            decode.assert_not_called()
        self.assertIn('not verified', view.status.text())
        view.close()

    def test_joint_scene_without_placement_clears_previous_preview(self):
        from tools.move_viewer.scene import CharacterScene
        view = anim_view.AnimationView(Path('unused'))
        view.image.setPixmap(QPixmap(2, 2))
        scene = CharacterScene(('primary', 'companion'), b'bank', [], [], 'capoeira')
        self.assertFalse(view.show_scene(scene, 54, None))
        self.assertTrue(view.image.pixmap().isNull())
        self.assertFalse(view.timer.isActive())
        self.assertIn('placement', view.status.text())
        view.close()

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_source_selection_forwards_copy_relation_and_target_slot(self):
        from unittest.mock import Mock
        preview = Mock()
        panel = AssignPanel(preview, Mock())
        panel.source_box.blockSignals(True)
        panel.source_box.addItems(['own', 'variant'])
        panel.source_box.setCurrentIndex(1)
        panel._bank = b'own'
        panel._sources = [BankSource('own', b'own', None),
                          BankSource('variant', b'variant', None)]
        panel.slot = 2
        item = QListWidgetItem('source')
        item.setData(MOTION_ROLE, 7)
        panel._motion_selected(item)
        self.assertEqual(len(preview.call_args.args), 4)
        index, bank, cross, slot = preview.call_args.args
        self.assertEqual((index, bank, slot), (7, b'variant', 2))
        self.assertEqual(cross.source.label, 'variant')
        panel.close()

    def test_model_padding_opt_in_never_accepts_nonzero_tail(self):
        import struct
        from tools.move_viewer.model_codec import parse_model
        data = struct.pack('<I4iI', 1, -1, -1, -1, -1, 0) + bytes(40)
        self.assertEqual(len(parse_model(data).nodes), 1)
        with self.assertRaises(ValueError):
            parse_model(data + bytes(4))
        self.assertEqual(len(parse_model(data + bytes(4), allow_zero_padding=True).nodes), 1)
        with self.assertRaises(ValueError):
            parse_model(data + b'\0\0\1', allow_zero_padding=True)

    def test_native_model_rejects_cycles_and_bad_link_indices(self):
        import struct
        from tools.move_viewer.model_codec import parse_model
        for links in ((-1, -1, -1, 0), (-1, 0, -1, -1), (-1, -1, 2, -1)):
            with self.subTest(links=links), self.assertRaises(ValueError):
                parse_model(struct.pack('<I4iI', 1, *links, 0) + bytes(40))

    def test_truncated_original_source_is_reported_without_stale_image(self):
        from tools.move_viewer.swap_mod import Skeleton
        source = BankSource('broken', b'bank', Skeleton((), ()), model_data=b'\0')
        view = anim_view.AnimationView(Path('unused'))
        view.image.setPixmap(QPixmap(2, 2))
        self.assertFalse(view.show_source(source, 0))
        self.assertTrue(view.image.pixmap().isNull())
        self.assertFalse(view.timer.isActive())
        view.close()

    def test_original_source_model_is_loaded_instead_of_target_model(self):
        import numpy as np
        from tools.move_viewer.swap_mod import Skeleton
        source = BankSource('BAG1 original', b'bank', Skeleton((), ()),
                            model_data=b'model', texture_data=(b'texture',))
        view = anim_view.AnimationView(Path('unused'))
        with (patch.object(anim_view, 'parse_model', return_value='native model') as model,
              patch.object(anim_view, 'parse_tim', return_value='native texture'),
               patch.object(anim_view, 'decode_motion', return_value={'frames': 5, 'step': 2}),
              patch.object(view, '_render_request', return_value=lambda frame: np.zeros((2, 2, 3), dtype=np.uint8)),
               patch.object(view, 'frame_pixmap', return_value=QPixmap(2, 2))):
            self.assertTrue(view.show_source(source, 0))
            self.wait_prepared(view)
            self.assertEqual(view._character, ('native model', b'bank', ['native texture'], ()))
            model.assert_called_once_with(b'model', allow_zero_padding=True)
        view.close()

    def test_comparison_uses_shared_clock_and_stops_when_closed(self):
        import numpy as np
        from unittest.mock import patch
        widget = anim_view.MotionComparison(Path('unused'))
        fake_char = ('model', b'bank', ['tims'], ['slot_map'])
        with (patch.object(widget.source, '_load', return_value=fake_char),
              patch.object(widget.result, '_load', return_value=fake_char),
               patch.object(anim_view, 'decode_motion', return_value={'frames': 5, 'step': 1}),
              patch.object(anim_view.AnimationView, '_render_request', return_value=lambda frame: np.zeros((2, 2, 3), dtype=np.uint8)),
              patch.object(widget.source, 'frame_pixmap', return_value=QPixmap(2, 2)),
              patch.object(widget.result, 'frame_pixmap', return_value=QPixmap(2, 2))):
            self.assertTrue(widget.show_banks('Heat', 0, b'bank', 2, b'bank'))
            self.assertFalse(widget.timer.isActive())
            self.wait_prepared(widget.source)
            self.wait_prepared(widget.result)
            self.assertTrue(widget.source._frames)
            self.assertTrue(widget.result._frames)
            self.assertTrue(widget.timer.isActive())
        widget.close()
        self.assertFalse(widget.timer.isActive())

    def test_failed_load_does_not_start_shared_playback(self):
        with patch.object(anim_view.AnimationView, 'show_motion', return_value=False):
            widget = anim_view.MotionComparison(Path('unused'))
            self.assertFalse(widget.show_banks('Heat', 0, b'bad', 0, b'bad'))
            self.assertFalse(widget.timer.isActive())
            self.assertFalse(widget.source.timer.isActive())
            self.assertFalse(widget.result.timer.isActive())
            widget.close()

    def test_comparison_partial_failure_clears_both_panels(self):
        call = {'n': 0}

        def fake_show(self, character, slot, bank=None):
            call['n'] += 1
            return call['n'] == 1

        with patch.object(anim_view.AnimationView, 'show_motion', fake_show):
            widget = anim_view.MotionComparison(Path('unused'))
            self.assertFalse(widget.show_banks('Heat', 0, b'bank', 2, b'bank'))
            self.assertFalse(widget.timer.isActive())
            self.assertFalse(widget.source.timer.isActive())
            self.assertFalse(widget.result.timer.isActive())
            self.assertTrue(widget.source.image.pixmap().isNull())
            self.assertTrue(widget.result.image.pixmap().isNull())
            self.assertIn('Comparación invalidada', widget.source.status.text())
            self.assertIn('Comparación invalidada', widget.result.status.text())
            widget.close()

    def test_shared_clock_preserves_steps_durations_and_wrap(self):
        widget = anim_view.MotionComparison(Path('unused'))
        for view, frames, step in ((widget.source, 5, 2), (widget.result, 4, 1)):
            view._motion = {'frames': frames, 'step': step}
            view._keys = list(range(0, frames, step))
            view._frames = [None] * len(view._keys)
        source_keys, result_keys = [], []
        with (patch.object(widget.source, 'frame_pixmap', return_value=QPixmap(2, 2)),
              patch.object(widget.result, 'frame_pixmap', return_value=QPixmap(2, 2))):
            for _ in range(7):
                widget.advance()
                source_keys.append(int(widget.source.status.text().split()[1].split('/')[0]))
                result_keys.append(int(widget.result.status.text().split()[1].split('/')[0]))
        self.assertEqual(source_keys, [0, 0, 2, 2, 4, 0, 0])
        self.assertEqual(result_keys, [0, 1, 2, 3, 0, 1, 2])
        widget.close()

    def test_initial_render_failure_clears_previous_image(self):
        import numpy as np
        view = anim_view.AnimationView(Path('unused'))
        with (patch.object(view, '_load', return_value=(None, b'bank', [], None)),
              patch.object(anim_view, 'decode_motion', return_value={'frames': 5, 'step': 2}),
              patch.object(view, '_render_request', return_value=lambda frame: np.zeros((2, 2, 3), dtype=np.uint8))):
            self.assertTrue(view.show_motion('Heat', 0))
            self.wait_prepared(view)
            self.assertFalse(view.image.pixmap().isNull())
        def fail(frame):
            raise ValueError('bad pose')
        with (patch.object(view, '_load', return_value=(None, b'bank', [], None)),
              patch.object(anim_view, 'decode_motion', return_value={'frames': 5, 'step': 2}),
              patch.object(view, '_render_request', return_value=fail)):
            self.assertTrue(view.show_motion('Heat', 1))
            self.wait_prepared(view)
            self.assertTrue(view.image.pixmap().isNull())
            self.assertFalse(view.timer.isActive())
            self.assertIn('bad pose', view.status.text())
        view.close()

    def test_main_window_close_and_selection_invalidate_comparison(self):
        from tools.move_viewer.app import MoveViewer
        for action in ('close', 'selection'):
            with self.subTest(action=action):
                viewer = MoveViewer({'characters': []})
                comparison = viewer._comparison = anim_view.MotionComparison(Path('unused'))
                comparison.show()
                comparison.timer.start(100)
                if action == 'selection':
                    viewer.show_move(None)
                else:
                    viewer.close()
                self.assertFalse(comparison.timer.isActive())
                self.assertFalse(comparison.isVisible())
                comparison.close()
                viewer.close()

    def test_main_close_stops_own_motion_and_late_failure_invalidates_both(self):
        from tools.move_viewer.app import MoveViewer
        viewer = MoveViewer({'characters': []})
        player = anim_view.AnimationView(Path('unused'))
        viewer.set_view_widget(player)
        player.timer.start(100)
        viewer.close()
        self.assertFalse(player.timer.isActive())
        comparison = anim_view.MotionComparison(Path('unused'))
        for view in (comparison.source, comparison.result):
            view._motion = {'frames': 5, 'step': 1}
            view._keys = list(range(5))
            view._frames = [None] * 5
        with (patch.object(comparison.source, 'frame_pixmap', return_value=QPixmap(2, 2)),
              patch.object(comparison.result, 'frame_pixmap', side_effect=[QPixmap(2, 2), ValueError('late')])):
            comparison.advance()
            self.assertFalse(comparison.source.image.pixmap().isNull())
            comparison.advance()
            self.assertTrue(comparison.source.image.pixmap().isNull())
            self.assertTrue(comparison.result.image.pixmap().isNull())
            self.assertIn('invalidada', comparison.source.status.text())
        comparison.close()
