import os
import struct
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from tools.move_viewer import bank_source, swap_mod  # noqa: E402
from tools.move_viewer.assign_panel import AssignPanel, assignment_check  # noqa: E402
from tools.move_viewer.swap_mod import BankSource, CrossBank, Skeleton  # noqa: E402

LINKS = ((-1, -1, 1, -1), (0, -1, -1, -1))
MAP = (0, 1) + (0xFF,) * 28


def motion(frames: int, tracks: tuple[int, ...] = (0, 1), pad: int = 0) -> bytes:
    """Sized motion with a syntactically valid header (streams are not decoded here)."""
    body = struct.pack('<IHBB', 0, frames, 2, len(tracks)) + bytes(tracks) + bytes(pad)
    return struct.pack('<I', len(body)) + body


def bank(*motions: bytes) -> bytes:
    return b''.join(motions) + bytes(4)


def source(label: str, *motions: bytes, links=LINKS, slot_map=MAP) -> BankSource:
    return BankSource(label, bank(*motions), Skeleton(tuple(links), slot_map))


class CompatTests(unittest.TestCase):
    def test_dfs_member_directory_must_fit_container(self):
        invalid = (b'DFS_', b'DFS_' + struct.pack('<I', 1),
                   b'DFS_' + struct.pack('<III', 1, 16, 99) + b'x',
                   b'DFS_' + struct.pack('<III', 1, 8, 1))
        for data in invalid:
            with self.subTest(data=data), self.assertRaises(ValueError):
                bank_source._members(data)

    def setUp(self):
        self.target = source('own', motion(40), motion(50), motion(60))
        self.variant = source('variant', motion(41), motion(52, pad=8), motion(60))

    def test_ui_budget_counts_adapted_motion_not_raw_source(self):
        from dataclasses import replace
        from unittest.mock import patch
        variant = replace(source('variant', motion(40)), retarget=object())
        cross = CrossBank(source('own', motion(40)), variant)
        with patch('tools.move_viewer.retarget.apply', return_value=motion(40, pad=8)):
            allowed, message = assignment_check(cross.target.bank, [], 0, 0, 7, cross)
            self.assertFalse(allowed, message)
            self.assertTrue(assignment_check(cross.target.bank, [], 0, 0, 8, cross)[0])

    def test_matching_skeleton_and_map_is_compatible(self):
        self.assertEqual(swap_mod.incompatibilities(self.target, self.variant), [])
        swap_mod.require_compatible(CrossBank(self.target, self.variant), [(0, 1)])

    def test_node_count_hierarchy_and_map_block(self):
        cases = {
            'node count': source('v', motion(40), links=LINKS[:1]),
            'hierarchy': source('v', motion(40), links=(LINKS[0], (0, -1, -1, 5))),
            'node->track map': source('v', motion(40), slot_map=(1, 0) + (0xFF,) * 28),
            'could not be derived': source('v', motion(40), slot_map=None),
        }
        for text, src in cases.items():
            with self.subTest(text):
                with self.assertRaisesRegex(ValueError, text):
                    swap_mod.copy_motions(self.target.bank, [(0, 0)], 1 << 20,
                                          CrossBank(self.target, src))

    def test_wrong_tracks_and_empty_source_motion_block(self):
        bad = source('v', motion(40, tracks=(0, 1, 2)), motion(40, tracks=(0, 5)))
        for index in (0, 1):
            self.assertIsNotNone(swap_mod.motion_incompatibility(self.target, bad, index))
        empty = BankSource('v', struct.pack('<I', 4) + bytes(4) + bytes(4), self.target.skeleton)
        self.assertIn('empty', swap_mod.motion_incompatibility(self.target, empty, 0))
        self.assertIn('not in', swap_mod.motion_incompatibility(self.target, self.variant, 9))

    def test_copy_takes_source_bytes_and_leaves_other_slots(self):
        result = swap_mod.copy_motions(self.target.bank, [(1, 0)], max_growth=16,
                                       cross=CrossBank(self.target, self.variant))
        motions, _ = swap_mod.split_bank(result)
        original, _ = swap_mod.split_bank(self.target.bank)
        copied, _ = swap_mod.split_bank(self.variant.bank)
        self.assertEqual(motions, [original[0], copied[0], original[2]])

    def test_growth_counts_source_sizes_and_respects_budget(self):
        cross = CrossBank(self.target, self.variant)
        growth = swap_mod.copy_growth(self.target.bank, [(1, 1)], self.variant.bank)
        self.assertEqual(growth, 8)
        with self.assertRaisesRegex(ValueError, 'does not fit'):
            swap_mod.copy_motions(self.target.bank, [(1, 1)], 7, cross)
        grown = swap_mod.copy_motions(self.target.bank, [(1, 1)], 8, cross)
        self.assertEqual(len(grown), len(self.target.bank) + 8)

    def test_target_bank_must_match_the_patched_bank(self):
        with self.assertRaisesRegex(ValueError, 'target bank differs'):
            swap_mod.copy_motions(bank(motion(40)), [(0, 0)], 0, CrossBank(self.target, self.variant))

    def test_warnings_report_duration_and_unverified_events(self):
        notes = swap_mod.copy_warnings(CrossBank(self.target, self.variant), 0, 0)
        self.assertIn('duration 41 frames vs 40', notes[0])
        self.assertIn('event table', notes[-1])

    def test_assignment_check_blocks_or_warns(self):
        bad = source('v', motion(40), slot_map=None)
        allowed, message = assignment_check(self.target.bank, [], 0, 0, 0, CrossBank(self.target, bad))
        self.assertFalse(allowed)
        self.assertIn('incompatible', message)
        allowed, message = assignment_check(self.target.bank, [], 1, 2, 0,
                                            CrossBank(self.target, self.variant))
        self.assertTrue(allowed)
        self.assertIn('sin verificar', message)

    def test_skeleton_of_reads_the_model_header(self):
        model = struct.pack('<I', 2) + b''.join(struct.pack('<4i', *link) for link in LINKS)
        self.assertEqual(swap_mod.skeleton_of(model, list(MAP)), Skeleton(LINKS, MAP))
        with self.assertRaises(ValueError):
            swap_mod.skeleton_of(struct.pack('<I', 99), None)


class PanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_source_selector_copies_from_variant_and_blocks_mixing(self):
        own = source('own', motion(40), motion(50), motion(60))
        variant = source('variant', motion(41), motion(52), motion(60, pad=4))
        previews, generated = [], []
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'x/model_a_p1/001.bin'
            path.parent.mkdir(parents=True)
            path.write_bytes(own.bank)
            panel = AssignPanel(lambda *a: previews.append(a), lambda *a: generated.append(a) or 'ok')
            panel.set_character(path, [own, variant])
            self.assertEqual(panel.source_box.count(), 2)
            panel.set_slot(0, 'move')
            panel.source_box.setCurrentIndex(1)
            panel.motions.setCurrentRow(1)
            self.assertEqual(previews[-1], (1, variant.bank, CrossBank(own, variant), 0))
            panel.assign()
            self.assertEqual(panel.pairs, [(0, 1)])
            self.assertIn('de variant', panel.pending.item(0).text())
            panel.source_box.setCurrentIndex(0)
            panel.motions.setCurrentRow(2)
            self.assertEqual(previews[-1], (2,))
            panel.set_slot(1, 'other')
            panel.assign()
            self.assertEqual(panel.pairs, [(0, 1)])
            self.assertIn('otro banco origen', panel.result.text())
            panel.source_box.setCurrentIndex(1)
            panel.build()
            path_arg, pairs, cross = generated[0]
            self.assertEqual((path_arg, pairs), (path, [(0, 1)]))
            self.assertIs(cross.source, variant)
            self.assertEqual(cross.target.bank, own.bank)

    def test_incompatible_source_is_never_queued(self):
        own = source('own', motion(40), motion(50))
        wrong = source('wrong', motion(40), motion(50), slot_map=None)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'x/model_a_p1/001.bin'
            path.parent.mkdir(parents=True)
            path.write_bytes(own.bank)
            panel = AssignPanel(lambda *a: None, lambda *a: 'ok')
            panel.set_character(path, [own, wrong])
            panel.set_slot(0, 'move')
            panel.source_box.setCurrentIndex(1)
            panel.motions.setCurrentRow(0)
            panel.assign()
            self.assertEqual(panel.pairs, [])
            self.assertIn('incompatible', panel.result.text())


class RealDataTests(unittest.TestCase):
    """Accepted BAG1 payload vs stock banks (see _work/move-viewer/f3/compat.md); skipped if absent."""

    @classmethod
    def setUpClass(cls):
        from tools.workflow.project_config import load_config, require_paths
        root = Path(__file__).resolve().parents[3]
        try:
            assets, cls.payload = require_paths(load_config(repo_root=root),
                                                ('inputs.bag2jp_assets', 'inputs.bag1_alt_payload'))
        except Exception as error:  # noqa: BLE001 - any config problem means no real data
            raise unittest.SkipTest(f'configuration unavailable: {error}')
        cls.characters = assets / 'archive/characters'
        if not (cls.payload / 'payload/bag1_alt.bin').is_file():
            raise unittest.SkipTest('BAG1 payload not built')

    def test_variant_preview_carries_its_original_model_and_textures(self):
        from tools.move_viewer.model_codec import parse_model, parse_tim
        for folder in ('heat', 'bi_o', 'strike'):
            with self.subTest(folder=folder):
                own, variant = bank_source.sources_for(self.characters, self.payload, folder)
                self.assertIsNotNone(variant.model_data)
                model = parse_model(variant.model_data, allow_zero_padding=True)
                self.assertEqual(len(model.nodes), len(variant.skeleton.links))
                self.assertTrue(variant.texture_data)
                self.assertTrue(all(parse_tim(data).pixels.size for data in variant.texture_data))
                self.assertNotEqual(variant.model_data, own.model_data)

    def test_reviewed_retarget_is_assignable_through_ui_check(self):
        from tools.move_viewer.assign_panel import assignment_check
        for folder in ('heat', 'bi_o'):
            with self.subTest(folder=folder):
                own, variant = bank_source.sources_for(self.characters, self.payload, folder)
                cross = CrossBank(own, variant)
                budget = swap_mod.GROWTH_BUDGET[folder][1]
                swap_mod.copy_motions(own.bank, [(0, 0)], budget, cross)
                allowed, message = assignment_check(own.bank, [], 0, 0, budget, cross)
                self.assertTrue(allowed, message)

    def test_ui_comparison_receives_exact_generated_retarget_bank(self):
        from unittest.mock import Mock
        from PySide6.QtWidgets import QApplication
        from tools.move_viewer.app import MoveViewer
        from tools.move_viewer.anim_view import AnimationView
        app = QApplication.instance() or QApplication([])
        viewer = MoveViewer({'characters': []})
        viewer.set_view_widget(AnimationView(self.characters))
        for folder in ('heat', 'bi_o'):
            with self.subTest(folder=folder):
                own, variant = bank_source.sources_for(self.characters, self.payload, folder)
                viewer._character = folder
                expected = swap_mod.copy_motions(own.bank, [(0, 0)],
                    swap_mod.GROWTH_BUDGET[folder][1], CrossBank(own, variant))
                viewer._comparison = Mock()
                viewer.preview_motion(0, variant.bank, CrossBank(own, variant), 0)
                viewer._comparison.show_banks.assert_called_once_with(
                    folder, 0, variant.bank, 0, expected, source=variant)
                viewer._comparison.show.assert_called_once()
        viewer.close()

    def test_strike_variant_is_compatible_and_heat_and_gaso_are_blocked(self):
        strike = bank_source.sources_for(self.characters, self.payload, 'strike')
        self.assertEqual(len(strike), 2)
        self.assertEqual(swap_mod.incompatibilities(*strike), [])
        swap_mod.require_compatible(CrossBank(*strike), [(2, 2)])
        own, variant = bank_source.sources_for(self.characters, self.payload, 'heat')
        self.assertTrue(swap_mod.incompatibilities(own, variant))
        self.assertIsNotNone(variant.retarget)  # reviewed profile: copy allowed via retarget
        swap_mod.copy_motions(own.bank, [(2, 2)], 1 << 20, CrossBank(own, variant))
        own, variant = bank_source.sources_for(self.characters, self.payload, 'bi_o')
        self.assertIsNotNone(variant.retarget)  # reviewed profile (BAG1 sb map writer)
        swap_mod.copy_motions(own.bank, [(2, 2)], 1 << 20, CrossBank(own, variant))

    def test_reverse_direction_has_the_same_verdict(self):
        own, variant = bank_source.sources_for(self.characters, self.payload, 'strike')
        swap_mod.require_compatible(CrossBank(variant, own), [(2, 2)])


if __name__ == '__main__':
    unittest.main()

class MuteVariantCuesTest(unittest.TestCase):
    def test_variant_cues_muted_others_kept(self):
        import struct
        from tools.move_viewer.swap_mod import mute_variant_cues, MUTED_CUE
        # body: u32 a=4 | at 4: u32 rel=4 -> info at 8: u16 0, u16 n=0 | events | 0
        events = [(2, 5, 0x6103), (3, 6, 0x1101), (1, 7, 0x6100), (2, 8, 0x0002)]
        body = struct.pack('<II', 4, 4) + struct.pack('<HH', 0, 0)
        body += b''.join(struct.pack('<HHH', *e) for e in events) + bytes(2)
        motion = struct.pack('<I', len(body)) + body
        out = mute_variant_cues(motion)
        got = [struct.unpack_from('<HHH', out, 16 + 6 * i) for i in range(4)]
        self.assertEqual(got, [(2, 5, MUTED_CUE), (3, 6, 0x1101), (1, 7, 0x6100), (2, 8, 2)])
        self.assertEqual(mute_variant_cues(b'\x04\x00\x00\x00abcd'), b'\x04\x00\x00\x00abcd')
