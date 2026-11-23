"""Companion scenes use the native extra model and shared bank, not effect003."""
import unittest
import struct
import numpy as np
from pathlib import Path
from unittest.mock import patch

from tools.move_viewer import scene


class SceneLoadingTest(unittest.TestCase):
    def test_joint_pose_uses_distinct_slots_and_explicit_transforms(self):
        from tools.move_viewer.pose import NodePose
        loaded = scene.CharacterScene(('primary', 'companion'), b'bank', ['tim'], [7], 'capoeira')
        first, second = np.eye(4), np.eye(4)
        second[:3, 3] = [12, 0, -4]
        def decode(bank, slot):
            return {'frames': 10, 'slot': slot}
        def sample(motion, frame):
            return np.array([motion['slot'], frame, 0.0])
        def pose(model, sampled, mapping):
            return {0: NodePose(np.eye(3), sampled, np.eye(3))}
        with (patch.object(scene.animlib, 'anim_list', return_value=[None] * 118),
              patch.object(scene, 'decode_motion', side_effect=decode),
              patch.object(scene, 'sample_motion', side_effect=sample),
              patch.object(scene, 'pose_model', side_effect=pose),
              patch.object(scene, 'world_meshes', side_effect=lambda model, poses: poses[0].translation)):
            actors = scene.pose_scene(loaded, 54, (2, 5), (first, second))
        self.assertEqual([actor[0] for actor in actors], ['primary', 'companion'])
        np.testing.assert_array_equal(actors[0][1], [54, 2, 0])
        np.testing.assert_array_equal(actors[1][1], [113, 5, -4])
        np.testing.assert_array_equal(second[:3, 3], [12, 0, -4])

    def test_scene_rejects_malformed_context_before_decoding(self):
        loaded = scene.CharacterScene(('primary', 'companion'), b'bank', [], [], 'capoeira')
        bad = np.eye(4)
        bad[0, 0] = np.nan
        for frames, placements in (((0,), (np.eye(4), np.eye(4))),
                                   ((0, 0), (np.eye(4),)),
                                   ((0, 0), (np.eye(3), np.eye(4))),
                                   ((0, 0), (bad, np.eye(4))),
                                   ((-1, 0), (np.eye(4), np.eye(4)))):
            with self.subTest(frames=frames), self.assertRaises(ValueError):
                scene.pose_scene(loaded, 54, frames, placements)

    def test_joint_pose_requires_explicit_actor_transforms(self):
        loaded = scene.CharacterScene(('primary', 'companion'), b'bank', [], [], 'capoeira')
        with self.assertRaisesRegex(ValueError, 'placement'):
            scene.pose_scene(loaded, 54, (0, 0), None)

    def test_missing_companion_is_not_silently_hidden(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            model_dir = Path(temp) / 'capoeira' / 'model_a_p2'
            model_dir.mkdir(parents=True)
            with (patch.object(scene, 'load_character', return_value=('primary', b'bank', [])),
                  patch('tools.move_viewer.render_offline.character_slot_map', return_value=[])):
                with self.assertRaises(FileNotFoundError):
                    scene.load_scene(model_dir, model_dir.parent / 'pack_a_p2')

    def test_single_actor_keeps_existing_model_and_bank(self):
        with (patch.object(scene, 'load_character', return_value=('primary', b'bank', [])),
              patch('tools.move_viewer.render_offline.character_slot_map', return_value=[1])):
            loaded = scene.load_scene(Path('heat/model_a_p1'), Path('heat/pack_a_p1'))
        self.assertEqual(loaded.models, ('primary',))
        self.assertEqual(loaded.bank, b'bank')
        self.assertEqual(loaded.slot_map, [1])

    def test_native_dance_pair_boundaries_and_missing_bank(self):
        for character in ('chichi_sally', 'capoeira'):
            for primary, companion in ((54, 101), (66, 113), (94, 114), (96, 116)):
                with self.subTest(character=character, primary=primary):
                    self.assertEqual(scene.companion_slot(character, primary, 118), companion)
            for slot in (-1, 0, 53, 67, 93, 97, 118, 126, 132):
                with self.subTest(slot=slot), self.assertRaises(ValueError):
                    scene.companion_slot(character, slot, 118)
            with self.assertRaises(ValueError):
                scene.companion_slot(character, 54, 101)
        with self.assertRaises(ValueError):
            scene.companion_slot('heat', 54, 118)

    def test_both_pairs_load_second_model_with_shared_bank(self):
        import tempfile
        for character in ('chichi_sally', 'capoeira'):
            with self.subTest(character=character), tempfile.TemporaryDirectory() as temp:
                model_dir = Path(temp) / character / 'model_a_p2'
                model_dir.mkdir(parents=True)
                (model_dir / '002.bin').write_bytes(
                    struct.pack('<I4iI', 1, -1, -1, -1, -1, 0) + bytes(40))
                (model_dir / '003.bin').write_bytes(b'effect, not a motion bank')
                with (patch.object(scene, 'load_character', return_value=('primary', b'bank', ['tim'])),
                      patch('tools.move_viewer.render_offline.character_slot_map', return_value=[7])):
                    loaded = scene.load_scene(model_dir, model_dir.parent / 'pack_a_p2')
                self.assertEqual(len(loaded.models), 2)
                self.assertEqual(len(loaded.models[1].nodes), 1)
                self.assertEqual(loaded.bank, b'bank')
                self.assertEqual(loaded.slot_map, [7])
