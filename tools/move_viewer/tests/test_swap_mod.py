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


class GrowthOnDiscTest(unittest.TestCase):
    """Heat entry 95 grown by WAIT(71) <- 0x06: entry overlay plus a 4-byte header size field."""

    def test_grown_entry_patches_only_size_field(self):
        from tools.move_viewer.swap_mod import (ARCHIVE_LBA, ROOT, SECTOR, build,
                                                load_config, require_paths)
        try:
            disc, = require_paths(load_config(repo_root=ROOT), ('inputs.bag2_disc',))
        except Exception as exc:  # disc is a local, untracked input
            self.skipTest(f'BAG2 disc unavailable: {exc}')
        overlays = build(disc, 95, [(71, 6)], copy=True, max_growth=912)
        self.assertEqual(len(overlays), 2)
        offset, stock, patched = overlays[1]
        self.assertEqual(offset, ARCHIVE_LBA * SECTOR + 8 + 8 * 95 + 4)
        self.assertEqual((len(stock), len(patched)), (4, 4))
        self.assertEqual(struct.unpack('<I', patched)[0], len(overlays[0][2]))
        # The regional mod owns header bytes 100..101; the size field must not overlap them.
        self.assertGreaterEqual(offset - ARCHIVE_LBA * SECTOR, 102)


if __name__ == '__main__':
    unittest.main()
