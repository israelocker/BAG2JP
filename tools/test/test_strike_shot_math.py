"""Verify 3D projection, tracer quad geometry and particle math for Strike's shot."""
import math
import unittest


def project_point(point: tuple[int, int, int], cam_rot: list[int], cam_trans: tuple[int, int, int], fov: int = 256, cx: int = 256, cy: int = 120, x_scale: int = 85) -> tuple[int, int, int] | None:
    """Apply the view MATRIX like GTE RTPS (rotate, then add translation) and project.

    Default offset mirrors SetGeomOffset(256, 120) at 0x8002DCF8 (512x240 screen).
    Applies x_scale (default 85%) for dancer model aspect ratio compensation."""
    x, y, z = point
    # cam_rot is a 3x3 matrix in Q12 fixed point (4096 = 1.0)
    # cam_rot = [r00, r01, r02, r10, r11, r12, r20, r21, r22]
    vx = ((cam_rot[0] * x + cam_rot[1] * y + cam_rot[2] * z) >> 12) + cam_trans[0]
    vy = ((cam_rot[3] * x + cam_rot[4] * y + cam_rot[5] * z) >> 12) + cam_trans[1]
    vz = ((cam_rot[6] * x + cam_rot[7] * y + cam_rot[8] * z) >> 12) + cam_trans[2]
    if vz <= 32:
        return None
    raw_sx = (vx * fov) // vz
    sx = cx + (raw_sx * x_scale) // 100
    sy = (vy * fov) // vz + cy
    return (sx, sy, vz)


def comp_matrix(r0: list[int], t0: tuple[int, int, int], r1: list[int], t1: tuple[int, int, int]) -> tuple[list[int], tuple[int, int, int]]:
    """Mirror CompMatrix 0x80043A84: rot = r0*r1 >> 12, trans = (r0*int16(t1) >> 12) + t0."""
    rot = [sum(r0[i * 3 + k] * r1[k * 3 + j] for k in range(3)) >> 12 for i in range(3) for j in range(3)]
    t16 = [((v + 0x8000) & 0xFFFF) - 0x8000 for v in t1]
    trans = tuple((sum(r0[i * 3 + k] * t16[k] for k in range(3)) >> 12) + t0[i] for i in range(3))
    return rot, trans


def build_beam_quad(p0: tuple[int, int], p1: tuple[int, int], width: float = 3.0) -> list[tuple[int, int]]:
    """Compute 4 corner vertices for a line quad from p0 to p1 with given width."""
    dx = p1[0] - p0[0]
    dy = p1[1] - p0[1]
    dist = math.hypot(dx, dy)
    if dist < 1e-4:
        return [(p0[0], p0[1])] * 4
    nx = -dy / dist * (width / 2.0)
    ny = dx / dist * (width / 2.0)
    return [
        (int(round(p0[0] + nx)), int(round(p0[1] + ny))),
        (int(round(p0[0] - nx)), int(round(p0[1] - ny))),
        (int(round(p1[0] + nx)), int(round(p1[1] + ny))),
        (int(round(p1[0] - nx)), int(round(p1[1] - ny))),
    ]


class StrikeShotMathTests(unittest.TestCase):
    def test_project_point_positive_z(self):
        identity_rot = [4096, 0, 0, 0, 4096, 0, 0, 0, 4096]
        cam_pos = (0, 0, 0)
        pt = project_point((0, 0, 1000), identity_rot, cam_pos, fov=256)
        self.assertIsNotNone(pt)
        self.assertEqual((pt[0], pt[1]), (256, 120))
        self.assertEqual(pt[2], 1000)

    def test_project_point_adds_translation_after_rotation(self):
        swap_xz = [0, 0, 4096, 0, 4096, 0, -4096, 0, 0]
        pt = project_point((-500, 0, 100), swap_xz, (0, 0, 1000), fov=256)
        raw_sx = (100 * 256) // 1500
        self.assertEqual(pt, (256 + (raw_sx * 85) // 100, 120, 1500))

    def test_comp_matrix_composes_camera_with_dancer(self):
        cam_rot = [6554, 0, 0, 0, -4096, 63, 0, -63, -4096]
        cam_t = (100, 200, 3000)
        dancer_rot = [-4096, 0, 0, 0, 4096, 0, 0, 0, -4096]
        dancer_t = (10, 20, 30)
        rot, trans = comp_matrix(cam_rot, cam_t, dancer_rot, dancer_t)
        self.assertEqual(rot, [-6554, 0, 0, 0, -4096, -63, 0, -63, 4096])
        self.assertEqual(trans, (((6554 * 10) >> 12) + 100,
                                 ((-4096 * 20 + 63 * 30) >> 12) + 200,
                                 ((-63 * 20 - 4096 * 30) >> 12) + 3000))

    def test_beam_quad_dimensions(self):
        quad = build_beam_quad((100, 100), (200, 100), width=4.0)
        self.assertEqual(len(quad), 4)
        self.assertEqual(quad[0], (100, 102))
        self.assertEqual(quad[1], (100, 98))
        self.assertEqual(quad[2], (200, 102))
        self.assertEqual(quad[3], (200, 98))


if __name__ == '__main__':
    unittest.main()
