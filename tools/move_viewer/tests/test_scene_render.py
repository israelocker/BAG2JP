"""Shared camera/depth behavior independent of archive decoding."""
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import numpy as np

from tools.move_viewer.render_offline import render, render_scene


class SceneRenderTest(unittest.TestCase):
    def test_single_actor_entry_points_have_identical_pixels(self):
        xyz = np.array([[-1., -1., 0.], [1., -1., 0.], [0., 1., 0.]])
        triangle = (xyz, np.tile([80., 160., 240.], (3, 1)), None, None, 0, None)
        with patch('tools.move_viewer.render_offline.triangles',
                   side_effect=lambda model, world: iter([triangle])):
            single = render(None, None, [], size=(30, 30))
            scene = render_scene([(None, None, [])], size=(30, 30))
        self.assertEqual(single.tobytes(), scene.tobytes())
        np.testing.assert_allclose(single.getpixel((15, 15)), (80, 160, 240), atol=1)

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
