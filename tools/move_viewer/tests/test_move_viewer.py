"""Host tests for tools.move_viewer (synthetic records + the archived Heat package)."""
import struct
import unittest
from pathlib import Path

import numpy as np

from tools.move_viewer import model_codec as mc
from tools.move_viewer import pose

ROOT = Path(__file__).resolve().parents[3]
HEAT = ROOT / 'assets/archive/characters/heat'


class PrimitiveDecodeTests(unittest.TestCase):
    def test_index_bytes_and_quad_gpu_order(self):
        w0 = 0x04030201          # d=1 a=2 b=3 c=4
        rec = struct.pack('<II', w0, 7)
        tri = mc.decode_primitive(0x2B, False, rec)
        quad = mc.decode_primitive(0x2B, True, rec)
        self.assertEqual(tri.vertices, [2, 3, 4])
        self.assertEqual(quad.vertices, [4, 1, 3, 2])     # emitter 0x80028510: c, d, b, a
        self.assertEqual(quad.colors, [7] * 4)

    def test_gouraud_quad_colour_order(self):
        rec = struct.pack('<III', 0, 0x00020001, 0x00040003)
        p = mc.decode_primitive(0x2E, True, rec)
        self.assertEqual(p.colors, [1, 4, 2, 3])         # 0x8002860C packet colour slots

    def test_textured_slot_and_clut_row(self):
        rec = bytearray(24)
        rec[0xC:0x14] = bytes([10, 11, 12, 13, 14, 15, 16, 17])
        rec[0x14], rec[0x15] = 0x22, 5                  # slot 2, semi-transparency 1
        p = mc.decode_primitive(0x2D, True, bytes(rec))
        self.assertEqual((p.texture_slot, p.semi_transparency, p.clut_row), (2, 1, 5))
        self.assertEqual(p.uvs, [(10, 11), (16, 17), (12, 13), (14, 15)])

    def test_unsupported_kind(self):
        with self.assertRaises(mc.UnsupportedPrimitive):
            mc.decode_primitive(0x34, False, bytes(8))

    def test_direct_rgb_textured_quad(self):
        # Sushi Boy record: indices, RGB word, four UV pairs, slot/clut word.
        rec = bytes.fromhex('03052726' 'b3b3b300' '03bf3dbf' '3e8f038f' '00000000')
        p = mc.decode_primitive(0x30, True, rec)
        self.assertEqual(p.vertices, [0x26, 0x03, 0x27, 0x05])
        self.assertEqual(p.rgb, (0xB3, 0xB3, 0xB3))
        self.assertEqual(p.uvs, [(3, 0xBF), (3, 0x8F), (0x3D, 0xBF), (0x3E, 0x8F)])
        self.assertEqual(p.texture_slot, 0)

    def test_kind_38_direct_vertex_rgb_quad(self):
        # Strike record: indices, four RGB words, UV pairs at 0x14..0x1B, slot/clut word.
        rec = bytes.fromhex('02010003' '777777ff' '444444ff' '828282ff' '777777ff'
                            '6801681f' '711f7101' '01010000')
        p = mc.decode_primitive(0x38, True, rec)
        self.assertEqual(p.vertex_rgb, [(0x77,) * 3, (0x77,) * 3, (0x44,) * 3, (0x82,) * 3])
        self.assertEqual(p.uvs, [(0x68, 0x01), (0x71, 0x01), (0x68, 0x1F), (0x71, 0x1F)])
        self.assertEqual((p.texture_slot, p.clut_row), (1, 1))

    def test_kind_31_uses_gt_layout(self):
        rec = bytes.fromhex('00011614' '01000400' '03000000' 'b749bb4a' 'ba492000')
        p = mc.decode_primitive(0x31, False, rec)
        self.assertEqual((p.kind, p.colors, p.semi_transparency), (0x31, [1, 4, 3], 1))
        self.assertEqual(p.uvs, [(0xB7, 0x49), (0xBB, 0x4A), (0xBA, 0x49)])


class PoseTests(unittest.TestCase):
    def test_rotation_matches_fun_8001f004_terms(self):
        x, y, z = 300, 700, 1100
        r = pose.rotation((x, y, z))
        s = lambda a: np.sin(a * 2 * np.pi / 4096)
        c = lambda a: np.cos(a * 2 * np.pi / 4096)
        self.assertAlmostEqual(r[0, 0], c(y) * c(z))
        self.assertAlmostEqual(r[1, 0], c(y) * s(z))
        self.assertAlmostEqual(r[2, 0], -s(y))
        self.assertAlmostEqual(r[2, 1], c(y) * s(x))
        self.assertAlmostEqual(r[2, 2], c(y) * c(x))

    def test_keyframe_position(self):
        self.assertEqual(pose.keyframe_position(54, 55, 3), 18)   # last frame: extra keyframe
        self.assertEqual(pose.keyframe_position(6, 55, 3), 2)
        self.assertEqual(pose.keyframe_position(5, 10, 1), 5)

    def test_angle_lerp_wraps(self):
        self.assertAlmostEqual(pose._lerp_angles(np.array([4000.]), np.array([100.]), .5)[0], 4098)


class TimTests(unittest.TestCase):
    def test_4bpp_tim(self):
        clut = struct.pack('<4H', 0, 0x001F, 0x03E0, 0x7C00)
        img = bytes([0x10, 0x32])
        data = (struct.pack('<II', 0x10, 8) + struct.pack('<IHHHH', 12 + 8, 0, 0, 4, 1) + clut
                + struct.pack('<IHHHH', 12 + 2, 0, 0, 1, 1) + img)
        tim = mc.parse_tim(data)
        self.assertEqual(tim.pixels.tolist(), [[0, 1, 2, 3]])
        rgba = mc.tim_rgba(tim)
        self.assertEqual(rgba[0, 0, 3], 0)                # colour 0 is transparent
        self.assertEqual(rgba[0, 1].tolist(), [255, 0, 0, 255])


@unittest.skipUnless((HEAT / 'model_a_p1/000.bin').exists(), 'archived Heat package missing')
class HeatPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model, cls.bank, cls.tims = mc.load_character(HEAT / 'model_a_p1', HEAT / 'pack_a_p1')

    def test_model_parses_exactly(self):
        self.assertEqual(len(self.model.nodes), 38)
        self.assertEqual(self.model.roots, [0, 20, 24])
        meshes = [n for n in self.model.nodes if n.mesh]
        self.assertEqual(len(meshes), 24)
        self.assertFalse(any(m.mesh.unsupported for m in meshes))
        self.assertEqual([len(self.model.nodes[k].mesh.vertices) for k in (11, 12, 13)], [33, 42, 171])

    def test_primitive_references_in_range(self):
        for n in self.model.nodes:
            if not n.mesh:
                continue
            slots = max([len(n.mesh.vertices)] + [s + 1 for _, s in n.mesh.imports])
            for p in n.mesh.primitives:
                self.assertLess(max(p.vertices), slots)
                if p.texture_slot is not None:
                    self.assertLess(p.texture_slot, len(self.tims))

    def test_wait_motion_poses(self):
        motion = pose.decode_motion(self.bank, 71)
        self.assertEqual((motion['frames'], motion['step'], len(motion['bones'])), (55, 3, 19))
        poses = pose.pose_model(self.model, pose.sample_motion(motion, 0), pose.HEAT_SLOT_MAP)
        world = pose.world_meshes(self.model, poses)
        allp = np.concatenate(list(world.positions.values()))
        height = allp[:, 1].max() - allp[:, 1].min()
        self.assertTrue(1000 < height < 2000, height)    # ~1.5k world units at scale 128


if __name__ == '__main__':
    unittest.main()
