"""Real-model regression for profile-scoped native FT4 subdivision."""
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/bag1import'))
from animlib import dfs_entries
import model_bag1_to_bag2 as model
import stage_geometry


def nodes(data: bytes) -> dict[int, bytes]:
    """Extract each fixture mesh and its transform, keyed by native node index."""
    words = struct.unpack(f'<{len(data)//4}I', data)
    count = words[0]
    links = [struct.unpack_from('<4i', data, 4+16*i) for i in range(count)]
    cursor, result = (1+4*count)*4, {}
    for node in model.walk_order(links):
        kind = words[cursor//4]
        if kind == 1:
            size = model.mesh_len_bag2(words, cursor//4)
        elif kind == 3:
            size = (3+words[cursor//4+2]*2)*4
        else:
            raise AssertionError(f'Unexpected fixture node {kind}')
        result[node] = data[cursor:cursor+size+40]
        cursor += size+40
    return result


class StageGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        native = dfs_entries((ROOT / '_work/bag1_disc_full/STAGEE/ST_GAS.DFS').read_bytes())[5]
        cls.source = model.convert(native, flatten_type2=True)[0]
        cls.specs = [
            {'node': 23, 'quad': 1, 'divisions': 2,
             'expected_words': [84148225, 8355711, 4275093200, 3204382462, 1793]},
            {'node': 26, 'quad': 1, 'divisions': 2,
             'expected_words': [67109125, 8355711, 4278124240, 3201351422, 1793]},
            {'node': 30, 'quad': 5, 'divisions': 2,
             'expected_words': [134481161, 8355711, 4278124240, 3201351422, 1793]},
        ]

    def test_empty_profile_keeps_model_byte_identical(self):
        self.assertEqual(stage_geometry.subdivide_ft4_meshes(self.source, []), self.source)

    def test_only_three_panels_change_with_native_vertices_and_transforms_preserved(self):
        before = nodes(self.source)
        result = stage_geometry.subdivide_ft4_meshes(self.source, self.specs)
        after = nodes(result)
        self.assertEqual(model.check_bag2(result), 0)
        self.assertEqual([node for node in before if before[node] != after[node]], [23, 26, 30])
        for node in (23, 26, 30):
            self.assertEqual(after[node][-40:], before[node][-40:])
            self.assertEqual(struct.unpack_from('<I', after[node], 0x25*4)[0], 21)
            self.assertEqual(struct.unpack_from('<I', after[node], 0x30*4)[0], 9 << 16)
            self.assertEqual(after[node][0x120:0x180], before[node][0x120:0x180])
            quads = after[node][0x120+21*8:-40]
            self.assertEqual(len(quads), 9*20)
            spec = next(spec for spec in self.specs if spec['node'] == node)
            split = spec['quad']*20
            original_quads = before[node][0x120+12*8:-40]
            self.assertEqual(quads[:split], original_quads[:split])
            self.assertEqual(quads[split+80:], original_quads[split+20:])
            for offset in range(split, split+80, 20):
                words = struct.unpack_from('<5I', quads, offset)
                self.assertEqual(words[1], 0x7f7f7f)
                self.assertEqual(words[4], 0x701)

    def test_surface_and_uv_midpoints_follow_native_corner_correspondence(self):
        after = nodes(stage_geometry.subdivide_ft4_meshes(self.source, self.specs))[23]
        vertices = [struct.unpack_from('<4h', after, 0x120+index*8) for index in range(21)]
        before, native = nodes(self.source)[23], self.specs[0]['expected_words']
        indices = [(native[0] >> shift) & 255 for shift in (0, 8, 16, 24)]
        corners = [struct.unpack_from('<4h', before, 0x120+indices[i]*8) for i in (3, 0, 2, 1)]
        for target, corner in zip((12, 14, 18, 20), corners):
            self.assertEqual(vertices[target], corner)
        self.assertEqual(vertices[16][:3], tuple(sum(c[i] for c in corners)//4 for i in range(3)))
        first_tile = struct.unpack_from('<5I', after, 0x120+21*8+20)
        self.assertEqual([(first_tile[0] >> shift) & 255 for shift in (0, 8, 16, 24)], [13, 16, 15, 12])
        self.assertEqual(first_tile[2] & 0xffff, native[2] & 0xffff)

    def test_stale_primitive_guard_refuses_patch(self):
        spec = json.loads(json.dumps(self.specs))
        spec[0]['expected_words'][0] ^= 1
        with self.assertRaisesRegex(ValueError, 'primitive guard'):
            stage_geometry.subdivide_ft4_meshes(self.source, spec)

    def test_duplicate_node_refuses_ambiguous_patch(self):
        with self.assertRaisesRegex(ValueError, 'duplicate node'):
            stage_geometry.subdivide_ft4_meshes(self.source, [self.specs[0]]*2)

    def test_invalid_division_counts_are_rejected(self):
        for divisions in (0, 1, 9, 2.0, True):
            with self.subTest(divisions=divisions):
                spec = dict(self.specs[0], divisions=divisions)
                with self.assertRaisesRegex(ValueError, 'divisions'):
                    stage_geometry.subdivide_ft4_meshes(self.source, [spec])

    def test_missing_node_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'missing node'):
            stage_geometry.subdivide_ft4_meshes(self.source, [dict(self.specs[0], node=99)])

    def test_non_mesh_node_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'full mesh'):
            stage_geometry.subdivide_ft4_meshes(self.source, [dict(self.specs[0], node=16)])

    def test_quad_outside_mesh_is_rejected(self):
        for quad in (-1, 6):
            with self.subTest(quad=quad):
                with self.assertRaisesRegex(ValueError, 'quad index'):
                    stage_geometry.subdivide_ft4_meshes(self.source, [dict(self.specs[0], quad=quad)])

    def test_maximum_division_count_remains_structurally_valid(self):
        result = stage_geometry.subdivide_ft4_meshes(self.source, [dict(self.specs[0], divisions=8)])
        self.assertEqual(model.check_bag2(result), 0)
        self.assertEqual(struct.unpack_from('<I', nodes(result)[23], 0x25*4)[0], 93)


if __name__ == '__main__':
    unittest.main()
