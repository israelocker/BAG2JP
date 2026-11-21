import struct
import unittest

from tools.move_viewer.swap_mod import GROWTH_BUDGET, check_growth_budget, main, patch_entry, split_bank, swap_motions


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


class GrowthBudgetTest(unittest.TestCase):
    def test_measured_budget_accepts_both_sides(self) -> None:
        entries, budget = GROWTH_BUDGET['comet']
        check_growth_budget(list(entries), budget)

    def test_bag1_variant_characters_grow_within_measured_budget(self) -> None:
        # bag1-content keeps the disc size since 2026-11-21 (LOSE3 hang fix).
        for character in ('heat', 'strike', 'bi_o'):
            entries, budget = GROWTH_BUDGET[character]
            check_growth_budget(list(entries), budget)

    def test_plugin_growth_bound_covers_bag1_variant_budgets(self) -> None:
        """bag1-content rejects disc sizes above stock + B1V_MAX_GROWTH."""
        import re
        from tools.move_viewer.swap_mod import ROOT
        source = (ROOT / 'mods-src/bag2jp.feature.bag1-content/bag2jp_bag1_versions.c').read_text()
        bound = int(re.search(r'#define B1V_MAX_GROWTH (\d+)u', source).group(1))
        for character in ('heat', 'strike', 'bi_o'):
            self.assertLessEqual(GROWTH_BUDGET[character][1], bound, character)

    def test_grow_shifts_members_after_bank(self) -> None:
        from tools.move_viewer.swap_mod import grow_entry
        members = [b'A' * 8, b'B' * 8, b'C' * 4]
        offset, header = 8 + 8 * 3, b''
        for m in members:
            header += struct.pack('<II', offset, len(m))
            offset += len(m)
        container = b'DFS_' + struct.pack('<I', 3) + header + b''.join(members)
        grown = grow_entry(container, b'X' * 12)
        self.assertEqual(struct.unpack_from('<II', grown, 8 + 16), (8 + 24 + 20, 4))
        self.assertEqual(grown[-4:], b'CCCC')
        self.assertEqual(struct.unpack_from('<I', grown, 8 + 12)[0], 12)

    def test_growth_over_budget_rejected(self) -> None:
        entries, budget = GROWTH_BUDGET['comet']
        with self.assertRaisesRegex(ValueError, 'outside'):
            check_growth_budget([entries[0]], budget + 1)

    def test_unmeasured_entry_rejected(self) -> None:
        entries, _ = GROWTH_BUDGET['heat']
        with self.assertRaisesRegex(ValueError, 'no measured'):
            check_growth_budget([entries[0], 167], 4)

    def test_cli_requires_copy_for_growth(self) -> None:
        with self.assertRaises(SystemExit):
            main(['--entry', '95', '--swap', '71:6', '--max-growth', '4', '--id', 'x', '--out', '_work/x'])


if __name__ == '__main__':
    unittest.main()
