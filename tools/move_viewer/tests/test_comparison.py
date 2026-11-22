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
        from tools.move_viewer.swap_mod import Skeleton
        source = BankSource('BAG1 original', b'bank', Skeleton((), ()),
                            model_data=b'model', texture_data=(b'texture',))
        view = anim_view.AnimationView(Path('unused'))
        with (patch.object(anim_view, 'parse_model', return_value='native model') as model,
              patch.object(anim_view, 'parse_tim', return_value='native texture'),
              patch.object(anim_view, 'decode_motion', return_value={'frames': 5, 'step': 2}),
              patch.object(view, 'frame_pixmap', return_value=QPixmap(2, 2))):
            self.assertTrue(view.show_source(source, 0))
            self.assertEqual(view._character, ('native model', b'bank', ['native texture'], ()))
            model.assert_called_once_with(b'model', allow_zero_padding=True)
        view.close()

    def test_comparison_uses_shared_clock_and_stops_when_closed(self):
        self.assertTrue(hasattr(anim_view, 'MotionComparison'))
        with patch.object(anim_view.AnimationView, 'show_motion') as show:
            widget = anim_view.MotionComparison(Path('unused'))
            widget.show_banks('Heat', 0, b'source', 2, b'result')
            self.assertEqual(show.call_args_list[0].args, ('Heat', 0, b'source'))
            self.assertEqual(show.call_args_list[1].args, ('Heat', 2, b'result'))
            self.assertFalse(widget.source.timer.isActive())
            self.assertFalse(widget.result.timer.isActive())
            self.assertTrue(widget.timer.isActive())
            widget.close()
            self.assertFalse(widget.timer.isActive())

    def test_failed_load_does_not_start_shared_playback(self):
        with patch.object(anim_view.AnimationView, 'show_motion', return_value=False):
            widget = anim_view.MotionComparison(Path('unused'))
            self.assertFalse(widget.show_banks('Heat', 0, b'bad', 0, b'bad'))
            self.assertFalse(widget.timer.isActive())
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
        view = anim_view.AnimationView(Path('unused'))
        with (patch.object(view, '_load', return_value=(None, b'bank', [], None)),
              patch.object(anim_view, 'decode_motion', return_value={'frames': 5, 'step': 2}),
              patch.object(view, 'frame_pixmap', side_effect=[QPixmap(2, 2), ValueError('bad pose')])):
            self.assertTrue(view.show_motion('Heat', 0))
            self.assertFalse(view.image.pixmap().isNull())
            self.assertFalse(view.show_motion('Heat', 1))
            self.assertTrue(view.image.pixmap().isNull())
            self.assertFalse(view.timer.isActive())
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
