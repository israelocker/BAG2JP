import struct
import unittest

from tools.move_viewer.swap_mod import patch_entry, split_bank, swap_motions


def bank(*motions: bytes) -> bytes:
    return b''.join(struct.pack('<I', len(m)) + m for m in motions) + b'\0\0\0\0PAD'


class SwapModTest(unittest.TestCase):
    def test_swap_keeps_size_and_tail(self):
        original = bank(b'aaaa', b'bb', b'cccccc')
        swapped = swap_motions(original, [(0, 2)])
        self.assertEqual(len(swapped), len(original))
        motions, tail = split_bank(swapped)
        self.assertEqual([m[4:] for m in motions], [b'cccccc', b'bb', b'aaaa'])
        self.assertEqual(tail, b'\0\0\0\0PAD')

    def test_patch_entry_rejects_size_change(self):
        container = b'DFS_' + struct.pack('<III', 1, 16, 4) + b'xxxx'
        self.assertEqual(patch_entry(container, 0, b'yyyy')[-4:], b'yyyy')
        with self.assertRaises(ValueError):
            patch_entry(container, 0, b'yy')


if __name__ == '__main__':
    unittest.main()
