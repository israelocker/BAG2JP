"""Host-only leaf payload selection, not native event or pose parity."""
import importlib.util
import unittest
from pathlib import Path

import numpy as np

from tools.move_viewer.model_codec import Mesh, Model, Node, Primitive, parse_model
from tools.move_viewer.pose import pose_model, world_meshes
from tools.move_viewer.render_offline import triangles
from tools.workflow.project_config import load_config, require_paths


def select(model, replacements):
    from tools.move_viewer.mesh_selection import select_leaf_meshes
    return select_leaf_meshes(model, replacements)


def fixture():
    mesh = Mesh(np.array([[1, 2, 3]]), 0, [], [(0, 7)], [], [])
    alternate = Mesh(np.array([[9, 8, 7]]), 0, [], [], [(7, 1)], [])
    return Model([
        Node(0, [-1, -1, 1, 2], 1, (0, 0, 0), (4096,) * 3, (0, 0, 0), mesh),
        Node(1, [0, -1, -1, -1], 1, (0, 0, 0), (4096,) * 3, (32, 0, 0), mesh),
        Node(2, [-1, -1, -1, -1], 1, (0, 0, 0), (4096,) * 3, (999, 0, 0), alternate),
    ], [0, 2])


class LeafSelectionTests(unittest.TestCase):
    def test_explicit_api_exists(self):
        self.assertIsNotNone(importlib.util.find_spec('tools.move_viewer.mesh_selection'))

    def test_detached_containers_and_shared_read_only_payload_contract(self):
        model = fixture()
        selected = select(model, {1: 2})
        self.assertIsNot(selected, model)
        self.assertIsNot(selected.nodes, model.nodes)
        self.assertIsNot(selected.roots, model.roots)
        for original, node in zip(model.nodes, selected.nodes):
            self.assertIsNot(node, original)
            self.assertIsNot(node.links, original.links)
            for name in ('links', 'index', 'kind', 'instance_of', 'rest_angles', 'scale', 'translation'):
                self.assertEqual(getattr(node, name), getattr(original, name))
        self.assertIs(selected.nodes[1].mesh, model.nodes[2].mesh)
        self.assertIs(selected.nodes[0].mesh, model.nodes[0].mesh)
        selected.nodes[1].links[0] = -1
        selected.roots.append(1)
        self.assertEqual(model.nodes[1].parent, 0)
        self.assertEqual(model.roots, [0, 2])

    def test_source_pose_imports_and_no_additional_roots(self):
        model = fixture()
        selected = select(model, {1: 2})
        world = world_meshes(selected, pose_model(selected))
        self.assertEqual(list(world.positions), [0, 1])
        np.testing.assert_allclose(world.positions[1], [[1.28125, .25, .21875],
                                                     [.03125, .0625, .09375]])
        self.assertIs(model.nodes[1].mesh, model.nodes[0].mesh)

    def test_empty_selection_is_detached_identity(self):
        model = fixture()
        selected = select(model, {})
        self.assertIsNot(selected.nodes[0], model.nodes[0])
        self.assertEqual(selected.walk(), model.walk())

    def test_selected_triangle_uses_prior_export_not_target_local_vertex(self):
        model = fixture()
        model.nodes[2].mesh = Mesh(np.array([[9, 8, 7], [0, 32, 0], [0, 0, 32]]),
                                 0, [], [], [(7, 0)],
                                 [Primitive(0x30, False, [0, 1, 2], [], rgb=(255, 0, 0))])
        selected = select(model, {1: 2})
        polygons = list(triangles(selected, world_meshes(selected, pose_model(selected))))
        self.assertEqual(len(polygons), 1)
        np.testing.assert_allclose(polygons[0][0],
                                   [[1 / 32, 2 / 32, 3 / 32], [1, 1, 0], [1, 0, 1]])

    def test_invalid_replacements_leave_original_untouched(self):
        model = fixture()
        for replacements in ({0: 2}, {1: 0}, {2: 1}, {1: 1}, {1: 99}, {-1: 2},
                             {True: 2}, {1: False}, {1.0: 2}, {1: '2'}, {1: -1},
                             {99: 2}, {1: 2, 2: 1}):
            with self.subTest(replacements=replacements), self.assertRaises(ValueError):
                select(model, replacements)
        self.assertEqual(model.nodes[1].links, [0, -1, -1, -1])
        self.assertIs(model.nodes[1].mesh, model.nodes[0].mesh)

    def test_nonmesh_types_and_missing_payloads_rejected(self):
        for index in (1, 2):
            for kind in (0, 2, 3, 4):
                model = fixture()
                model.nodes[index].kind = kind
                with self.subTest(index=index, kind=kind), self.assertRaises(ValueError):
                    select(model, {1: 2})
            model = fixture()
            model.nodes[index].mesh = None
            with self.assertRaises(ValueError):
                select(model, {1: 2})

    def test_cyclic_input_rejected(self):
        model = fixture()
        model.nodes[2].links[2] = 2
        with self.assertRaises(ValueError):
            select(model, {1: 2})

    def test_root_chain_matches_roots_and_is_acyclic(self):
        for replacements in ({}, {1: 2}):
            for index, link in ((2, 0), (0, -1)):
                model = fixture()
                model.nodes[index].links[3] = link
                with self.subTest(replacements=replacements, index=index), self.assertRaises(ValueError):
                    select(model, replacements)


class ArchivedLeafSelectionTests(unittest.TestCase):
    def test_verified_pairs_use_source_slots_and_draw_order(self):
        root = Path(__file__).resolve().parents[3]
        assets, = require_paths(load_config(repo_root=root), ('inputs.bag2jp_assets',))
        for character, pairs in (('heat', ((16, 20), (16, 21), (19, 22), (19, 23))),
                                 ('pander', ((18, 19),))):
            model = parse_model((assets / 'archive/characters' / character /
                                 'model_a_p1/000.bin').read_bytes())
            original_links = [list(node.links) for node in model.nodes]
            original_meshes = [node.mesh for node in model.nodes]
            baseline = pose_model(model)
            for source, target in pairs:
                with self.subTest(character=character, source=source, target=target):
                    selected = select(model, {source: target})
                    poses = pose_model(selected)
                    world = world_meshes(selected, poses)
                    self.assertEqual(list(poses), list(baseline))
                    self.assertNotIn(target, world.positions)
                    self.assertIs(selected.nodes[source].mesh, model.nodes[target].mesh)
                    np.testing.assert_array_equal(poses[source].draw, baseline[source].draw)
                    np.testing.assert_array_equal(poses[source].translation, baseline[source].translation)
                    mesh = model.nodes[target].mesh
                    expected = (baseline[source].draw @ mesh.vertices.T).T + baseline[source].translation
                    np.testing.assert_allclose(world.positions[source][:len(expected)], expected)
                    # Import coordinates are pinned independently by the synthetic
                    # triangle test, not reconstructed from final output here.
                    self.assertGreater(len(list(triangles(selected, world))), 0)
            self.assertEqual([node.links for node in model.nodes], original_links)
            for node, mesh in zip(model.nodes, original_meshes):
                self.assertIs(node.mesh, mesh)
            with self.assertRaises(ValueError):
                select(model, {pairs[0][0]: model.roots[2]})


if __name__ == '__main__':
    unittest.main()
