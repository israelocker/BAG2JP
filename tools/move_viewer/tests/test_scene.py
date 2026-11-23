"""Companion scenes use the native extra model and shared bank, not effect003."""
import unittest
import struct
import numpy as np
from pathlib import Path
from unittest.mock import patch

from tools.move_viewer import scene


class SceneLoadingTest(unittest.TestCase):
    def test_snapshot_forwards_distinct_local_state_after_root_correction(self):
        from tools.move_viewer.pose import MotionPose, NodePose
        loaded = scene.CharacterScene(('first', 'second'), b'bank', [], [7], 'capoeira')
        contexts = tuple(scene.NativeActorContext(i, 0, 1, 2048, scale, (0, 0, 0))
                         for i, scale in enumerate((128, 256)))
        previous = ({0: np.eye(3)}, {0: np.eye(3) * 2})
        from tools.move_viewer.gte_lighting import NodeLighting
        zero = ((0, 0, 0),) * 3
        lights = ({0: NodeLighting(zero, zero, (0,) * 3, (0,) * 3, 0)},
                  {0: NodeLighting(zero, zero, (1,) * 3, (0,) * 3, 0)})
        def pose(model, sampled, mapping, *, player_scale, previous_local_rotations):
            index = loaded.models.index(model)
            self.assertIs(previous_local_rotations, previous[index])
            self.assertEqual(player_scale, contexts[index].scale)
            return {0: NodePose(np.eye(3), np.array([3., 4., 5.]), np.eye(3))}
        def meshes(model, placed, *, lighting):
            index = loaded.models.index(model)
            self.assertIs(lighting, lights[index])
            np.testing.assert_array_equal(placed[0].translation,
                                          np.array([3., 4., 5.]) + 10 - (index + 1))
            return placed
        with (patch.object(scene, 'decode_motion', return_value={}),
              patch.object(scene, 'snapshot_world_root', return_value=np.full(3, 10.)),
              patch.object(scene, 'sample_motion', return_value=MotionPose({}, np.ones(3))),
              patch.object(scene, 'pose_model', side_effect=pose) as posed,
              patch.object(scene, 'world_meshes', side_effect=meshes)):
            actors = scene.pose_snapshot_scene(loaded, contexts,
                                              previous_local_rotations=previous, lighting=lights)
        self.assertEqual(len(actors), 2)
        self.assertEqual(posed.call_count, 2)

    def test_snapshot_malformed_state_fails_before_decode(self):
        loaded = scene.CharacterScene(('first', 'second'), b'bank', [], [], 'capoeira')
        contexts = (scene.NativeActorContext(0, 0, 0, 0, 128, (0, 0, 0)),) * 2
        with patch.object(scene, 'decode_motion') as decode:
            for field in ('previous_local_rotations', 'lighting'):
                for states in (({},), ({}, None), ({}, {}, {})):
                    with self.subTest(field=field, states=states), self.assertRaises(ValueError):
                        scene.pose_snapshot_scene(loaded, contexts, **{field: states})
            decode.assert_not_called()

    def test_snapshot_invalid_node_light_fails_before_decode(self):
        loaded = scene.CharacterScene(('first',), b'bank', [], [], 'heat')
        contexts = (scene.NativeActorContext(0, 0, 0, 0, 128, (0, 0, 0)),)
        with patch.object(scene, 'decode_motion') as decode:
            for value in (None, 'not lighting', object()):
                with self.subTest(value=type(value)), self.assertRaisesRegex(ValueError, 'lighting'):
                    scene.pose_snapshot_scene(loaded, contexts, lighting=({0: value},))
            decode.assert_not_called()

    def test_explicit_actor_state_reaches_real_pose_and_lighting_paths(self):
        from types import SimpleNamespace
        from tools.move_viewer.pose import MotionPose, rotation
        from tools.move_viewer.gte_lighting import NodeLighting
        from tools.move_viewer.model_codec import Primitive

        group = SimpleNamespace(color=(128, 128, 128),
                                normals=np.array([[2048, 2048, 2048]]), specular=None)
        mesh = SimpleNamespace(color_base=0, groups=[group],
                               vertices=np.array([[32, 0, 0], [0, 32, 0], [0, 0, 0]]),
                               imports=[], exports=[],
                               primitives=[Primitive(0x2E, False, [0, 1, 2], [0, 0, 0])])
        node = SimpleNamespace(mesh=mesh, rest_angles=(0, 0, 0),
                               translation=(0, 0, 0), scale=(4096,) * 3,
                               child=-1, sibling=-1)
        model = SimpleNamespace(nodes=[node], roots=[0], walk=lambda: [0])
        loaded = scene.CharacterScene((model, model), b'bank', [], [15], 'capoeira')
        identity = ((4096, 0, 0), (0, 4096, 0), (0, 0, 4096))
        zero = ((0, 0, 0),) * 3
        lights = ({0: NodeLighting(identity, identity, (0,) * 3, (0,) * 3, 0)},
                  {0: NodeLighting(zero, zero, (1600, 800, 400), (0,) * 3, 0)})
        previous = ({0: np.eye(3)}, {0: rotation((0, 0, 1024))})
        transforms = (np.eye(4), np.eye(4))
        transforms[1][:3, 3] = [10, 20, 30]
        with (patch.object(scene.animlib, 'anim_list', return_value=[None] * 118),
              patch.object(scene, 'decode_motion', return_value={'frames': 4, 'step': 2,
                                                               'translation': [[0, 0]] * 3}),
              patch.object(scene, 'sample_motion', return_value=MotionPose({}, np.zeros(3)))):
            actors = scene.pose_scene(loaded, 54, (0, 0), transforms,
                                      previous_local_rotations=previous, lighting=lights)
            contexts = (scene.NativeActorContext(54, 0, 0, 0, 128, (0, 0, 0)),
                        scene.NativeActorContext(101, 0, 0, 0, 256, (10, 20, 30)))
            snapshots = scene.pose_snapshot_scene(loaded, contexts,
                                                  previous_local_rotations=previous, lighting=lights)
        np.testing.assert_allclose(snapshots[0][1].positions[0][0], [1, 0, 0], atol=1e-12)
        np.testing.assert_allclose(snapshots[1][1].positions[0][0], [10, 22, 30], atol=1e-12)
        np.testing.assert_array_equal(snapshots[0][1].colors[0], [64, 64, 64])
        np.testing.assert_array_equal(snapshots[1][1].colors[0], [50, 25, 12])
        np.testing.assert_allclose(actors[0][1].positions[0][0], [1, 0, 0], atol=1e-12)
        np.testing.assert_allclose(actors[1][1].positions[0][0], [10, 21, 30], atol=1e-12)
        np.testing.assert_array_equal(actors[0][1].colors[0], [64, 64, 64])
        np.testing.assert_array_equal(actors[1][1].colors[0], [50, 25, 12])
        np.testing.assert_array_equal(previous[0][0], np.eye(3))

        # Real pose -> GTE colours -> shared scene raster -> owned RGB cache.
        # Synthetic static geometry, not captured placement or native playback.
        from threading import Event
        from tools.move_viewer.frame_preparation import prepare_frames
        from tools.move_viewer.render_offline import render_scene

        keys, seen, progress = list(range(0, 264, 3)), [], []
        def render_key(key):
            seen.append(key)
            return np.asarray(render_scene(actors, size=(64, 64)))
        budget = len(keys) * 64 * 64 * 3
        buffers = prepare_frames(keys, render_key, budget, Event(),
                                 lambda done, total: progress.append((done, total)))
        self.assertEqual(seen, keys)
        self.assertEqual(progress[-1], (88, 88))
        self.assertEqual(sum(frame.nbytes for frame in buffers), budget)
        self.assertFalse(np.shares_memory(buffers[0], buffers[1]))
        colours = set(map(tuple, buffers[0].reshape(-1, 3).tolist()))
        self.assertTrue({(64, 64, 64), (50, 25, 12)} <= colours)
        with self.assertRaisesRegex(ValueError, 'budget'):
            prepare_frames(keys, render_key, budget - 1, Event(), lambda *_: None)

    def test_actor_state_count_mismatch_fails_before_decoding(self):
        loaded = scene.CharacterScene(('first', 'second'), b'bank', [], [], 'capoeira')
        with (patch.object(scene.animlib, 'anim_list', return_value=[None] * 118),
              patch.object(scene, 'decode_motion') as decode):
            for field in ('previous_local_rotations', 'lighting'):
                for states in (({},), ({}, None)):
                    with self.subTest(field=field, states=states), self.assertRaises(ValueError):
                        scene.pose_scene(loaded, 54, (0, 0), (np.eye(4), np.eye(4)),
                                         **{field: states})
            decode.assert_not_called()

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
