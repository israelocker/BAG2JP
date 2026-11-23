"""Explicit-state colour arithmetic; not evidence of a captured stage profile."""
import unittest
from types import SimpleNamespace

import numpy as np

from tools.move_viewer.gte_lighting import ncds, specular_colour


IDENTITY = ((4096, 0, 0), (0, 4096, 0), (0, 0, 4096))
ZERO = ((0, 0, 0),) * 3


class GteLightingTests(unittest.TestCase):
    def test_world_meshes_uses_explicit_node_gte_state_for_both_groups(self):
        from tools.move_viewer.pose import NodePose, world_meshes
        from tools.move_viewer.gte_lighting import NodeLighting
        groups = [SimpleNamespace(color=(128, 128, 128),
                                  normals=np.array([[2048, 2048, 2048]]), specular=count)
                  for count in (None, 1)]
        mesh = SimpleNamespace(color_base=0, groups=groups, vertices=np.array([[0, 0, 0]]),
                               imports=[], exports=[])
        model = SimpleNamespace(nodes=[SimpleNamespace(mesh=mesh)], walk=lambda: [0])
        poses = {0: NodePose(np.eye(3), np.zeros(3), np.eye(3))}
        state = NodeLighting(IDENTITY, IDENTITY, (0, 0, 0), (0, 0, 0), 0)
        result = world_meshes(model, poses, lighting={0: state})
        # Existing world-mesh colour allocation retains one trailing scratch slot.
        np.testing.assert_array_equal(result.colors, [[64, 64, 64], [32, 32, 32], [0, 0, 0]])
        poses[0].rotation = np.diag([-1., -1., 1.])
        np.testing.assert_array_equal(world_meshes(model, poses, lighting={0: state}).colors,
                                      result.colors)
        # A present first node must not hide missing state on a second drawn mesh.
        model.nodes.append(SimpleNamespace(mesh=mesh))
        model.walk = lambda: [0, 1]
        poses[1] = poses[0]
        with self.assertRaisesRegex(ValueError, 'node 1'):
            world_meshes(model, poses, lighting={0: state})
        model.walk = lambda: [0]
        with self.assertRaises(ValueError):
            world_meshes(model, poses, lighting={})
        for normals in (np.array([[2048.9, 2048, 2048]]), np.array([[True, False, True]])):
            groups[0].normals = normals
            with self.subTest(normals=normals), self.assertRaises(ValueError):
                world_meshes(model, poses, lighting={0: state})

    def test_specular_repeats_square_before_colour(self):
        for repeats, expected in ((1, 32), (2, 8), (3, 0)):
            with self.subTest(repeats=repeats):
                self.assertEqual(specular_colour((2048, 2048, 2048), (128, 128, 128),
                                                  IDENTITY, IDENTITY, (0, 0, 0),
                                                  (0, 0, 0), 0, repeats),
                                 (expected,) * 3)

    def test_specular_requires_positive_byte_repeat_count(self):
        for repeats in (0, -1, 256, 1.5):
            with self.subTest(repeats=repeats), self.assertRaises(ValueError):
                specular_colour((0, 0, 0), (128, 128, 128), ZERO, ZERO,
                                (0, 0, 0), (0, 0, 0), 0, repeats)

    def test_specular_clamps_between_repeated_squares(self):
        self.assertEqual(specular_colour((32767,) * 3, (1,) * 3, IDENTITY,
                                         IDENTITY, (0,) * 3, (0,) * 3, 0, 2), (7,) * 3)

    def test_specular_non_diagonal_colour_and_depth(self):
        swap = ((0, 4096, 0), (0, 0, 4096), (4096, 0, 0))
        self.assertEqual(specular_colour((4096, 2048, 0), (128,) * 3, IDENTITY,
                                         swap, (0,) * 3, (0,) * 3, 2048, 1),
                         (16, 0, 64))

    def test_identity_light_preserves_rgb_at_full_normal(self):
        self.assertEqual(ncds((4096, 4096, 4096), (200, 100, 50),
                              IDENTITY, IDENTITY, (0, 0, 0), (0, 0, 0), 0),
                         (200, 100, 50))

    def test_background_uses_register_units_not_rgb_bytes(self):
        self.assertEqual(ncds((0, 0, 0), (128, 128, 128),
                              ZERO, ZERO, (1600, 800, 400), (0, 0, 0), 0),
                         (50, 25, 12))

    def test_negative_light_clamps_before_colour_matrix(self):
        self.assertEqual(ncds((-4096, 4096, 0), (128, 128, 128),
                              IDENTITY, IDENTITY, (0, 0, 0), (0, 0, 0), 0),
                         (0, 128, 0))

    def test_depth_cue_interpolates_to_far_colour(self):
        self.assertEqual(ncds((4096, 4096, 4096), (200, 100, 50),
                              IDENTITY, IDENTITY, (0, 0, 0), (320, 640, 960), 2048),
                         (110, 70, 55))

    def test_depth_difference_saturates_before_interpolation(self):
        # FC difference exceeds signed IR range: it must clamp before IR0 multiply.
        self.assertEqual(ncds((0, 0, 0), (0, 0, 0), ZERO, ZERO,
                              (0, 0, 0), (100000, 100000, 100000), 4096),
                         (255, 255, 255))
        # A small IR0 distinguishes the intermediate clamp from final RGB clipping.
        self.assertEqual(ncds((0, 0, 0), (0, 0, 0), ZERO, ZERO,
                              (0, 0, 0), (100000, 100000, 100000), 1),
                         (0, 0, 0))

    def test_rejects_non_register_inputs(self):
        for normal, ir0 in (((0.5, 0, 0), 0), ((32768, 0, 0), 0), ((0, 0, 0), 4097)):
            with self.subTest(normal=normal, ir0=ir0), self.assertRaises(ValueError):
                ncds(normal, (128, 128, 128), IDENTITY, IDENTITY,
                     (0, 0, 0), (0, 0, 0), ir0)

    def test_mac_wrap_precedes_ir_saturation(self):
        self.assertEqual(ncds((4096, 4096, 4096), (128, 128, 128),
                              IDENTITY, IDENTITY, (2147483647,) * 3, (0, 0, 0), 0),
                         (0, 0, 0))


if __name__ == '__main__':
    unittest.main()
