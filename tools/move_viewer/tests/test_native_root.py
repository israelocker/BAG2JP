"""Native root arithmetic pinned to the recorded Chichi actor context."""
import unittest
from unittest.mock import patch

import numpy as np

from tools.move_viewer import pose


class NativeRootTest(unittest.TestCase):
    def test_active_capoeira_pair_matches_recorded_ram_roots(self):
        from tools.move_viewer.scene import NativeActorContext, snapshot_world_root
        for slot, first, second, blend, parent, keys, samples, expected in (
                (66, 27, 28, 2558, (-725, 0, -240), 6,
                 [[-1152, -1262], [1285, 1243], [47, 157]], [-1088, 359, -199]),
                (113, 28, 29, 2612, (-860, 0, -237), 7,
                 [[615, 669], [1203, 1130], [-75, -177]], [-681, 343, -265])):
            with self.subTest(slot=slot):
                motion = {'frames': 264, 'step': 4,
                          'translation': [[0] * keys + axis for axis in samples]}
                context = NativeActorContext(slot, first, second, blend, 74, parent)
                self.assertEqual(snapshot_world_root(motion, context).tolist(), expected)

    def test_snapshot_scene_places_each_actor_at_its_recorded_root(self):
        from tools.move_viewer import scene
        motion = {'frames': 64, 'step': 3, 'translation':
                  [[0] * 18 + [-2728, -2678], [0] * 18 + [1240, 1278],
                   [0] * 18 + [-286, -346]]}
        contexts = (scene.NativeActorContext(26, 56, 57, 3458, 53, (-315, -88, -159)),
                    scene.NativeActorContext(26, 56, 57, 3458, 60, (22, -136, -159)))
        source = scene.CharacterScene(('primary', 'companion'), b'bank', [], [], 'chichi_sally')
        sampled = pose.MotionPose({}, np.array([-1340., 638., -172.]))

        def preview(model, sample, slots, player_scale):
            return {0: pose.NodePose(np.eye(3), sample.root_translation * player_scale / 128,
                                     np.eye(3))}

        with patch.object(scene, 'decode_motion', return_value=motion), \
                patch.object(scene, 'sample_motion', return_value=sampled), \
                patch.object(scene, 'pose_model', side_effect=preview), \
                patch.object(scene, 'world_meshes', side_effect=lambda model, poses: poses):
            actors = scene.pose_snapshot_scene(source, contexts)
        np.testing.assert_array_equal(actors[0][1][0].translation, [-871, 175, -231])
        np.testing.assert_array_equal(actors[1][1][0].translation, [-607, 162, -241])

    def test_snapshot_scene_requires_one_context_per_actor(self):
        from tools.move_viewer.scene import CharacterScene, pose_snapshot_scene
        scene = CharacterScene(('primary', 'companion'), b'', [], [], 'chichi_sally')
        with self.assertRaises(ValueError):
            pose_snapshot_scene(scene, ())

    def test_snapshot_actor_context_rejects_invalid_fields(self):
        from tools.move_viewer.scene import NativeActorContext
        with self.assertRaises(ValueError):
            NativeActorContext(slot=-1, first_frame=56, second_frame=57,
                                blend=3458, scale=53, parent=(-315, -88, -159))

    def test_snapshot_context_combines_recorded_sampling_and_placement(self):
        from tools.move_viewer.scene import NativeActorContext, snapshot_world_root
        context = NativeActorContext(26, 56, 57, 3458, 53, (-315, -88, -159))
        translation = [[0] * 18 + [-2728, -2678],
                       [0] * 18 + [1240, 1278],
                       [0] * 18 + [-286, -346]]
        motion = {'frames': 64, 'step': 3, 'translation': translation}
        self.assertEqual(snapshot_world_root(motion, context).tolist(), [-871, 175, -231])

    def test_native_key_context_rejects_unsupported_boundaries(self):
        for context in ((56, 57, -1, 3, 64), (56, 57, 4097, 3, 64),
                        (-1, 1, 0, 3, 64), (1, 63, 0, 3, 64),
                        (1, 2, 0, 1, 64), (0, 0, 0, 3, 1),
                        (61, 61, 0, 3, 63)):
            with self.subTest(context=context), self.assertRaises(ValueError):
                pose.native_key_context(*context)

    def test_captured_frame_blend_selects_native_keys_and_weight(self):
        self.assertEqual(pose.native_key_context(56, 57, 3458, 3, 64),
                         (18, 19, 3883))

    def test_captured_actor_scales_and_parents_match_ram_roots(self):
        for scale, parent, expected in (
                (53, [-315, -88, -159], [-871, 175, -231]),
                (60, [22, -136, -159], [-607, 162, -241]),
                (53, [753, -88, -41], [197, 175, -113]),
                (60, [1091, -136, -42], [462, 162, -124])):
            with self.subTest(scale=scale, parent=parent):
                self.assertEqual(
                    pose.native_world_root([-1341, 637, -173], scale, parent).tolist(),
                    expected)

    def test_captured_root_uses_separate_signed_shifts(self):
        translation = [[-2728, -2678], [1240, 1278], [-286, -346]]
        self.assertEqual(
            pose.native_root_translation(translation, 0, 1, 3883).tolist(),
            [-1341, 637, -173])

    def test_invalid_weight_and_keys_are_rejected(self):
        for weight in (-1, 4097):
            with self.subTest(weight=weight), self.assertRaises(ValueError):
                pose.native_root_translation([[0, 0]] * 3, 0, 1, weight)
        with self.assertRaises(ValueError):
            pose.native_root_translation([[0]] * 3, -1, 0, 0)

    def test_invalid_root_placement_is_rejected(self):
        for root, scale, parent in (([1, 2], 53, [0, 0, 0]),
                                    ([1, 2, 3], 0, [0, 0, 0]),
                                    ([1, 2, 3], 4097, [0, 0, 0]),
                                    ([1, 2, 3], 53, [0, 0])):
            with self.subTest(root=root, scale=scale, parent=parent):
                with self.assertRaises(ValueError):
                    pose.native_world_root(root, scale, parent)
