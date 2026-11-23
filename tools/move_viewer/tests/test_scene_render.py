"""Shared camera/depth behavior independent of archive decoding."""
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import numpy as np

from tools.move_viewer.render_offline import render, render_scene


class SceneRenderTest(unittest.TestCase):
    def test_untextured_semitransparency_blends_with_background(self):
        xyz = np.array([[-1., -1., 0.], [1., -1., 0.], [0., 1., 0.]])
        from tools.move_viewer import render_offline as renderer
        expected = ((60, 70, 84), (120, 140, 168), (0, 0, 0), (60, 65, 78))
        for mode, pixel in enumerate(expected, 1):
            triangle = (xyz, np.tile([80., 100., 120.], (3, 1)),
                        None, None, 0, None, mode)
            with self.subTest(mode=mode), patch.object(renderer, 'triangles',
                                                      return_value=iter([triangle])):
                image = render(None, None, [], size=(30, 30))
                self.assertEqual(image.getpixel((15, 15)), pixel)

    def test_single_actor_entry_points_have_identical_pixels(self):
        xyz = np.array([[-1., -1., 0.], [1., -1., 0.], [0., 1., 0.]])
        triangle = (xyz, np.tile([80., 160., 240.], (3, 1)), None, None, 0, None)
        with patch('tools.move_viewer.render_offline.triangles',
                   side_effect=lambda model, world: iter([triangle])):
            single = render(None, None, [], size=(30, 30))
            scene = render_scene([(None, None, [])], size=(30, 30))
        self.assertEqual(single.tobytes(), scene.tobytes())
        np.testing.assert_allclose(single.getpixel((15, 15)), (80, 160, 240), atol=1)

    def test_texture_blends_only_stp_texels_and_preserves_zero_holes(self):
        xyz = np.array([[-1., -1., 0.], [1., -1., 0.], [0., 1., 0.]])
        triangle = (xyz, np.full((3, 3), 128.), np.zeros((3, 2)), 0, 0, None, 2)
        for word, expected in ((0x001F, (255, 0, 0)),
                               (0x801F, (255, 40, 48)),
                               (0x0000, (40, 40, 48)),
                               (0x8000, (40, 40, 48))):
            tim = SimpleNamespace(clut=np.array([[word]], np.uint16),
                                  pixels=np.zeros((1, 1), int))
            with self.subTest(word=hex(word)), patch(
                    'tools.move_viewer.render_offline.triangles',
                    return_value=iter([triangle])):
                image = render(None, None, [tim], size=(30, 30))
                self.assertEqual(image.getpixel((15, 15)), expected)

    def test_blend_saturates_and_rejects_unknown_modes(self):
        from tools.move_viewer.render_offline import blend_colors
        np.testing.assert_array_equal(blend_colors(np.array([[250, 20, 0]]),
                                                  np.array([[50, 40, 30]]), 2),
                                      [[255, 60, 30]])
        np.testing.assert_array_equal(blend_colors(np.array([[10, 20, 30]]),
                                                  np.array([[50, 40, 10]]), 3),
                                      [[0, 0, 20]])
        with self.assertRaisesRegex(ValueError, 'unsupported semi-transparency'):
            blend_colors(np.zeros((1, 3)), np.zeros((1, 3)), 5)

    def test_invalid_mode_is_rejected_even_without_stp_or_visible_pixels(self):
        xyz = np.array([[-1., -1., 0.], [1., -1., 0.], [0., 1., 0.]])
        triangle = (xyz, np.full((3, 3), 128.), np.zeros((3, 2)), 0, 0, None, 5)
        tim = SimpleNamespace(clut=np.array([[0x001f]], np.uint16),
                              pixels=np.zeros((1, 1), int))
        with patch('tools.move_viewer.render_offline.triangles', return_value=iter([triangle])):
            with self.assertRaisesRegex(ValueError, 'unsupported semi-transparency'):
                render(None, None, [tim], size=(30, 30))

    def test_gouraud_underlayer_is_blend_destination_and_fills_texture_holes(self):
        xyz = np.array([[-1., -1., 0.], [1., -1., 0.], [0., 1., 0.]])
        base = np.tile([0., 100., 80.], (3, 1))
        triangle = (xyz, np.full((3, 3), 128.), np.zeros((3, 2)), 0, 0, base, 2)
        for word, expected in ((0x801f, (255, 100, 80)), (0, (0, 100, 80))):
            tim = SimpleNamespace(clut=np.array([[word]], np.uint16),
                                  pixels=np.zeros((1, 1), int))
            with self.subTest(word=word), patch('tools.move_viewer.render_offline.triangles',
                                                return_value=iter([triangle])):
                image = render(None, None, [tim], size=(30, 30))
                np.testing.assert_allclose(image.getpixel((15, 15)), expected, atol=1)

    def test_missing_or_negative_texture_slot_is_rejected(self):
        xyz = np.array([[-1., -1., 0.], [1., -1., 0.], [0., 1., 0.]])
        for slot in (None, -1, 0):
            triangle = (xyz, np.full((3, 3), 128.), np.zeros((3, 2)), slot, 0, None, 1)
            with self.subTest(slot=slot), patch('tools.move_viewer.render_offline.triangles',
                                                return_value=iter([triangle])):
                with self.assertRaisesRegex(ValueError, 'texture slot'):
                    render(None, None, [], size=(30, 30))

    def test_unrelated_blending_preserves_opaque_depth_tie(self):
        xyz = np.array([[-1., -1., 0.], [1., -1., 0.], [0., 1., 0.]])
        first = (xyz, np.tile([80., 0, 0], (3, 1)), None, None, 0, None, 0)
        tilted = xyz.copy()
        tilted[:, 2] = [1, 1, -1]
        other = (tilted, np.tile([0., 100, 0], (3, 1)), None, None, 0, None, 0)
        invisible = (xyz + [10, 0, 0], np.full((3, 3), 80.), None, None, 0, None, 1)
        bounds = (np.array([0., 0.05, 0.]), 3.)
        with patch('tools.move_viewer.render_offline.triangles', return_value=iter([first, other])):
            baseline = render(None, None, [], size=(30, 30), bounds=bounds)
        with patch('tools.move_viewer.render_offline.triangles',
                   return_value=iter([first, other, invisible])):
            mixed = render(None, None, [], size=(30, 30), bounds=bounds)
        self.assertEqual(baseline.tobytes(), mixed.tobytes())

    def test_back_facing_triangle_is_culled(self):
        xyz = np.array([[-1., -1., 0.], [0., 1., 0.], [1., -1., 0.]])
        triangle = (xyz, np.tile([80., 160., 240.], (3, 1)), None, None, 0, None)
        with patch('tools.move_viewer.render_offline.triangles',
                   side_effect=lambda model, world: iter([triangle])):
            image = render(None, None, [], size=(30, 30), bounds=(np.zeros(3), 3.))
        self.assertNotEqual(image.getpixel((15, 15)), (80, 160, 240))

    def test_texture_palette_is_owned_by_each_actor(self):
        xyz = np.array([[-1., -1., 0.], [1., -1., 0.], [0., 1., 0.]])
        triangle = (xyz, np.full((3, 3), 128.), np.zeros((3, 2)), 0, 0, None)
        red = SimpleNamespace(clut=np.array([[1]]), pixels=np.zeros((1, 1), int))
        green = SimpleNamespace(clut=np.array([[2]]), pixels=np.zeros((1, 1), int))
        def actor_triangle(model, world):
            offset = -1.5 if model == 'left' else 1.5
            return iter([(triangle[0] + [offset, 0, 0], *triangle[1:])])
        with patch('tools.move_viewer.render_offline.triangles', side_effect=actor_triangle), \
                patch('tools.move_viewer.render_offline.clut_to_rgba',
                      side_effect=lambda row: np.array([[255, 0, 0, 255]
                                                       if row[0] == 1 else [0, 255, 0, 255]])):
            image = render_scene([('left', None, [red]), ('right', None, [green])],
                                 size=(60, 30), bounds=(np.zeros(3), 6.))
        self.assertEqual(image.getpixel((15, 15)), (255, 0, 0))
        self.assertEqual(image.getpixel((45, 15)), (0, 255, 0))

    def test_nearer_actor_occludes_far_actor_in_either_order(self):
        xyz = np.array([[-1., -1., 0.], [1., -1., 0.], [0., 1., 0.]])
        red = (xyz + [0, 0, 1], np.tile([255., 0, 0], (3, 1)), None, None, 0, None)
        green = (xyz, np.tile([0., 255, 0], (3, 1)), None, None, 0, None)
        bounds = (np.zeros(3), 3.)
        with patch('tools.move_viewer.render_offline.triangles',
                   side_effect=lambda model, world: iter([red if model == 'far' else green])):
            for order in (('far', 'near'), ('near', 'far')):
                image = render_scene([(name, None, []) for name in order],
                                     size=(30, 30), bounds=bounds)
                self.assertEqual(image.getpixel((15, 15)), (0, 255, 0))

    def test_near_translucent_actor_blends_far_opaque_in_either_order(self):
        xyz = np.array([[-1., -1., 0.], [1., -1., 0.], [0., 1., 0.]])
        far = (xyz + [0, 0, 1], np.tile([80., 0, 0], (3, 1)), None, None, 0, None, 0)
        near = (xyz, np.tile([0., 100., 0], (3, 1)), None, None, 0, None, 2)
        with patch('tools.move_viewer.render_offline.triangles',
                   side_effect=lambda model, world: iter([far if model == 'far' else near])):
            for order in (('near', 'far'), ('far', 'near')):
                with self.subTest(order=order):
                    image = render_scene([(name, None, []) for name in order],
                                         size=(30, 30), bounds=(np.zeros(3), 3.))
                    np.testing.assert_allclose(image.getpixel((15, 15)), (80, 100, 0), atol=1)
