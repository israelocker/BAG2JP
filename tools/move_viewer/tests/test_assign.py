import argparse
import hashlib
import struct
import tempfile
import tomllib
import unittest
from pathlib import Path

from tools.move_viewer import swap_mod
from tools.move_viewer.assign_panel import apply_copies, motion_rows


def bank(*bodies: bytes) -> bytes:
    return b''.join(struct.pack('<I', len(b)) + b for b in bodies) + b'\0\0\0\0'


class AssignTests(unittest.TestCase):
    def test_apply_copies_leaves_other_slots(self):
        self.assertEqual(apply_copies([0, 1, 2, 3], [(0, 2), (2, 3)]), [2, 1, 3, 3])

    def test_copy_motions_pads_or_blocks_growth(self):
        stock = bank(b'aaaa', b'bb', b'cc')
        smaller = swap_mod.copy_motions(stock, [(0, 1)])
        self.assertEqual(len(smaller), len(stock))
        motions, _ = swap_mod.split_bank(smaller)
        self.assertEqual([m[4:] for m in motions], [b'bb', b'bb', b'cc'])
        self.assertEqual(swap_mod.copy_growth(stock, [(1, 0)]), 2)
        with self.assertRaises(ValueError):
            swap_mod.copy_motions(stock, [(1, 0)])

    def test_copy_motions_grows_within_budget(self):
        stock = bank(b'aaaa', b'bb', b'cc')
        grown = swap_mod.copy_motions(stock, [(1, 0)], max_growth=2)
        self.assertEqual(len(grown), len(stock) + 2)
        motions, _ = swap_mod.split_bank(grown)
        self.assertEqual([m[4:] for m in motions], [b'aaaa', b'aaaa', b'cc'])

    def test_grow_entry_updates_member_size(self):
        member0 = b'M' * 8
        old = bank(b'bb')
        head = b'DFS_' + struct.pack('<IIIII', 2, 24, 8, 32, len(old))
        container = head + member0 + old
        new = bank(b'bbbb')
        grown = swap_mod.grow_entry(container, new)
        self.assertEqual(struct.unpack_from('<II', grown, 16), (32, len(new)))
        self.assertEqual(grown[32:], new)
        with self.assertRaises(ValueError):
            swap_mod.grow_entry(container + b'x', new)

    def test_assignment_check_respects_budget(self):
        from tools.move_viewer.assign_panel import assignment_check
        stock = bank(b'aaaa', b'bb')
        self.assertFalse(assignment_check(stock, [], 1, 0)[0])
        allowed, message = assignment_check(stock, [], 1, 0, max_growth=2)
        self.assertTrue(allowed)
        self.assertIn('jugador 1 y 2', message)

    def test_motion_rows_hex_index_and_size(self):
        rows = motion_rows(bank(b'ab', b'cdef'))
        self.assertEqual(len(rows), 2)
        self.assertTrue(rows[1].startswith('0x01'))
        self.assertIn(' 4 B', rows[1])

    def test_parse_pair_rejects_bad_text(self):
        self.assertEqual(swap_mod.parse_pair('71:6'), (71, 6))
        for text in ('1:2:3', 'a:b', '-1:2'):
            with self.assertRaises(argparse.ArgumentTypeError):
                swap_mod.parse_pair(text)

    def test_manifest_escapes_and_package_verifies(self):
        overlays = [(4096, b'old0', b'new0'), (8192, b'old1', b'new1')]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            swap_mod.write_package(out, 'bag2jp.test.x', 'name "quoted" \\ ok', overlays)
            data = tomllib.loads((out / 'manifest.toml').read_text(encoding='utf-8'))
            self.assertEqual(data['name'], 'name "quoted" \\ ok')
            self.assertEqual([o['offset'] for o in data['overlay']], [4096, 8192])
            self.assertEqual(data['overlay'][1]['expected_sha256'], hashlib.sha256(b'old1').hexdigest())
            self.assertEqual((out / data['overlay'][1]['file']).read_bytes(), b'new1')
            self.assertFalse(data['feature'][0]['default_enabled'])




class GrowthBudgetCliTest(unittest.TestCase):
    def test_budget_enforced(self) -> None:
        from tools.move_viewer.swap_mod import check_growth_budget
        check_growth_budget([95, 96], 912)
        with self.assertRaises(SystemExit):
            check_growth_budget([95], 913)
        with self.assertRaises(SystemExit):
            check_growth_budget([95, 167], 100)


if __name__ == '__main__':
    unittest.main()
