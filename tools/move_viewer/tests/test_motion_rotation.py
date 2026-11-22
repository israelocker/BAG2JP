"""Rotation sampling regressions against native matrices, without archive assets."""
import unittest
from types import SimpleNamespace

import numpy as np

from tools.move_viewer import pose


class MotionRotationTests(unittest.TestCase):
    @staticmethod
    def decoded(first: tuple[int, int, int], second: tuple[int, int, int]) -> dict:
        """Make a two-key rotation track with an interior frame."""
        return {'frames': 3, 'step': 2, 'bones': [0],
                'rotations': [[[a, b] for a, b in zip(first, second)]],
                'translation': [[0, 0], [0, 0], [0, 0]]}

    def test_sampled_pose_matches_native_capoeira_leg(self):
        # SLPM_862.19; runtime 94749bfc; RAM gf12004 SHA256
        # 58c4a92b57cbec93ffc5f8c2deb8e129907bf95b5352b11b45f8e2174cd757f1.
        # P2 actor 0x801a5450, slot65, track4, keys5/6, native weight2048.
        # Input angles from matching 001.bin; expected local matrix from
        # actor+0x2c+4*32. Native GTE rounding differs from the float preview.
        decoded = {'frames': 3, 'step': 2, 'bones': [4],
                   'rotations': [[[3255, 1236], [20, 2028], [4081, 2034]]],
                   'translation': [[0, 0], [0, 0], [0, 0]]}
        node = SimpleNamespace(rest_angles=(0, 0, 0), translation=(0, 0, 0),
                               scale=(4096, 4096, 4096), child=-1, sibling=-1)
        model = SimpleNamespace(nodes=[node], roots=[0], walk=lambda: [0])
        actual = pose.pose_model(model, pose.sample_motion(decoded, 1), [4])[0]
        expected = np.array([[4097, -95, 124], [-92, 1224, 3913],
                             [-128, -3912, 1220]]) / 4096
        np.testing.assert_allclose(actual.rotation, expected, atol=0.002, rtol=0)

    def test_equivalent_euler_keys_do_not_create_a_spurious_turn(self):
        decoded = self.decoded((0, 0, 0), (2048, 2048, 2048))
        actual = pose.sample_motion(decoded, 1).slot_rotations[0]
        np.testing.assert_allclose(actual, np.eye(3), atol=1e-12)

    def test_key_endpoints_are_preserved(self):
        decoded = self.decoded((0, 0, 0), (1024, 0, 0))
        np.testing.assert_allclose(pose.sample_motion(decoded, 0).slot_rotations[0],
                                   np.eye(3), atol=1e-12)
        np.testing.assert_allclose(pose.sample_motion(decoded, 2).slot_rotations[0],
                                   [[1, 0, 0], [0, 0, -1], [0, 1, 0]], atol=1e-12)

    def test_blend_is_an_orthonormal_right_handed_rotation(self):
        decoded = self.decoded((300, 700, 1100), (700, 900, 1800))
        actual = pose.sample_motion(decoded, 0.6).slot_rotations[0]
        np.testing.assert_allclose(actual @ actual.T, np.eye(3), atol=1e-12)
        self.assertAlmostEqual(np.linalg.det(actual), 1)

    def test_degenerate_blend_fails_closed_instead_of_emitting_nan(self):
        with self.assertRaisesRegex(ValueError, 'degenerate native rotation blend'):
            pose.sample_motion(self.decoded((0, 0, 0), (2048, 0, 0)), 1)

    def test_degenerate_cross_product_preserves_valid_endpoints(self):
        decoded = self.decoded((0, 0, 0), (0, 2048, 0))
        for frame in (0, 2):
            self.assertTrue(np.isfinite(pose.sample_motion(decoded, frame).slot_rotations[0]).all())
        with self.assertRaisesRegex(ValueError, 'degenerate native rotation blend'):
            pose.sample_motion(decoded, 1)

    def test_matrix_precedence_and_legacy_angle_rest_fallbacks(self):
        node = SimpleNamespace(rest_angles=(0, 1024, 0), translation=(0, 0, 0),
                               scale=(4096, 4096, 4096), child=-1, sibling=-1)
        model = SimpleNamespace(nodes=[node], roots=[0], walk=lambda: [0])
        x_turn = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]])
        y_turn = np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]])
        z_turn = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
        legacy = pose.MotionPose({4: np.array([1024, 0, 0])}, np.array([1, 2, 3]))
        actual = pose.pose_model(model, legacy, [4])[0]
        np.testing.assert_allclose(actual.rotation, x_turn, atol=1e-12)
        np.testing.assert_allclose(actual.translation, [1, 2, 3])
        partial = pose.MotionPose(legacy.slot_angles, legacy.root_translation, {7: z_turn})
        np.testing.assert_allclose(pose.pose_model(model, partial, [4])[0].rotation,
                                   x_turn, atol=1e-12)
        override = pose.MotionPose(legacy.slot_angles, legacy.root_translation, {4: z_turn})
        np.testing.assert_allclose(pose.pose_model(model, override, [4])[0].rotation,
                                   z_turn, atol=1e-12)
        np.testing.assert_allclose(pose.pose_model(model, override, [8])[0].rotation,
                                   y_turn, atol=1e-12)
        unmapped = pose.MotionPose({255: legacy.slot_angles[4]}, legacy.root_translation,
                                   {255: z_turn})
        np.testing.assert_allclose(pose.pose_model(model, unmapped, [255])[0].rotation,
                                   y_turn, atol=1e-12)


if __name__ == '__main__':
    unittest.main()
