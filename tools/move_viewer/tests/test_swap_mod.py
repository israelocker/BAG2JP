import struct
import unittest

from tools.move_viewer import swap_mod

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
        source = (ROOT / 'mods-src/bag2jp.feature.bag1-content/bag2jp_bag1_size.h').read_text()
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


class RelocationBoundsTest(unittest.TestCase):
    def test_relocation_outside_free_dummy_area_is_refused(self) -> None:
        from pathlib import Path
        for lba in (swap_mod.RELOCATE_FIRST_LBA - 1, swap_mod.RELOCATE_END_LBA - 1):
            with self.assertRaises(ValueError):
                swap_mod.relocated(Path('missing.bin'), 109, 10, b'\0' * 4096, lba)

    def test_truncated_destination_is_not_treated_as_zero_padding(self) -> None:
        from pathlib import Path
        from unittest.mock import patch

        with patch.object(swap_mod, 'read_user', return_value=b''), \
                patch.object(swap_mod, 'entry_extent', return_value=(20168704, 10)):
            with self.assertRaisesRegex(ValueError, 'incomplete relocation target'):
                swap_mod.relocated(Path('truncated.bin'), 109, 10, b'x' * 20, 228920)

    def test_nonzero_destination_is_refused(self) -> None:
        from pathlib import Path
        from unittest.mock import patch

        with patch.object(swap_mod, 'read_user', return_value=b'\0' * 19 + b'x'):
            with self.assertRaisesRegex(ValueError, 'not zero padding'):
                swap_mod.relocated(Path('occupied.bin'), 109, 10, b'x' * 20, 228920)


class RelocationGenerationTest(unittest.TestCase):
    def test_two_sides_get_distinct_sector_aligned_destinations(self) -> None:
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from tools.move_viewer import app

        disc, = swap_mod.require_paths(swap_mod.load_config(), ('inputs.bag2_disc',))
        own, variant = app.character_sources('STRIKE')[:2]
        with TemporaryDirectory() as directory:
            overlays = swap_mod.generate(
                disc, [109, 110], [(73, 73)], 'bag2jp.test.relocation', 'Relocation test',
                Path(directory), copy=True, max_growth=4388,
                cross=swap_mod.CrossBank(own, variant), relocate_lba=228920)
        self.assertEqual([offset for offset, _, _ in overlays],
                         [468828160, 367472, 469168128, 367480])
        self.assertEqual([len(data) for _, _, data in overlays], [338696, 8, 338696, 8])
        self.assertLessEqual(overlays[0][0] + len(overlays[0][2]), overlays[2][0])

    def test_insufficient_space_does_not_write_a_partial_package(self) -> None:
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from tools.move_viewer import app

        disc, = swap_mod.require_paths(swap_mod.load_config(), ('inputs.bag2_disc',))
        own, variant = app.character_sources('STRIKE')[:2]
        with TemporaryDirectory() as directory:
            out = Path(directory) / 'package'
            with self.assertRaisesRegex(ValueError, 'outside free DUMMY area'):
                swap_mod.generate(
                    disc, [109, 110], [(73, 73)], 'bag2jp.test.relocation', 'Relocation test',
                    out, copy=True, max_growth=4388,
                    cross=swap_mod.CrossBank(own, variant), relocate_lba=237369)
            self.assertFalse(out.exists())


class PackageReservationTest(unittest.TestCase):
    """Absolute disc_user half-open reservations cover header and payload writes."""

    def generate_fixture(self, out, reserved):
        from pathlib import Path
        from unittest.mock import patch

        with patch.object(swap_mod, 'build', return_value=[(100, b'aaa', b'bbb')]):
            return swap_mod.generate(Path('unused.bin'), [109], [], 'test', 'Test', out,
                                     reserved_spans=reserved)

    def test_collision_refuses_write_even_inside_an_existing_package(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as directory:
            out = Path(directory)
            sentinel = out / 'manifest.toml'
            sentinel.write_bytes(b'preserve existing package')
            for reserved in (((100, 103),), ((99, 101),), ((102, 104),)):
                with self.subTest(reserved=reserved):
                    with self.assertRaisesRegex(ValueError, 'reserved disc span'):
                        self.generate_fixture(out, reserved)
                    self.assertEqual(sentinel.read_bytes(), b'preserve existing package')
                    self.assertFalse((out / 'payload').exists())

    def test_adjacent_half_open_ranges_are_allowed(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as directory:
            out = Path(directory) / 'package'
            self.generate_fixture(out, ((90, 100), (103, 104)))
            self.assertTrue((out / 'manifest.toml').is_file())

    def test_second_header_overlay_collision_preserves_existing_package(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch

        with TemporaryDirectory() as directory:
            out = Path(directory)
            sentinel = out / 'manifest.toml'
            sentinel.write_bytes(b'preserve header collision')
            # Sorted spans put this header *after* the payload: both must be checked.
            overlays = [(100, b'aaa', b'bbb'), (500, b'12345678', b'abcdefgh')]
            with patch.object(swap_mod, 'build', return_value=overlays):
                with self.assertRaisesRegex(ValueError, 'reserved disc span'):
                    swap_mod.generate(Path('unused.bin'), [109], [], 'test', 'Test', out,
                                      reserved_spans=((500, 508),))
            self.assertEqual(sentinel.read_bytes(), b'preserve header collision')
            self.assertFalse((out / 'payload').exists())

    def test_invalid_reservations_fail_before_build_or_write(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch

        with TemporaryDirectory() as directory:
            out = Path(directory) / 'package'
            for reserved in (((100, 100),), ((103, 100),), ((-1, 100),), ((True, 4),)):
                with self.subTest(reserved=reserved), patch.object(
                        swap_mod, 'build', return_value=[(100, b'aaa', b'bbb')]) as build:
                    with self.assertRaisesRegex(ValueError, 'invalid reserved disc span'):
                        swap_mod.generate(Path('unused.bin'), [109], [], 'test', 'Test', out,
                                          reserved_spans=reserved)
                    build.assert_not_called()
                    self.assertFalse(out.exists())


if __name__ == '__main__':
    unittest.main()
