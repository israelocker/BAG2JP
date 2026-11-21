"""Planning must reserve both sides and fail before any package writes."""
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.move_viewer import package_plan, swap_mod


class PackagePlanTest(unittest.TestCase):
    def test_default_policy_allows_in_place_copy(self):
        expected = [(10000, b'old', b'new')]
        with patch.object(swap_mod, 'build', return_value=expected):
            self.assertEqual(package_plan.plan(Path('unused'), [109], [], ()),
                             expected)

    def test_relocation_requires_explicit_selector_policy(self):
        with patch.object(swap_mod, 'build', side_effect=self.build):
            with self.assertRaisesRegex(ValueError, 'BAG1/BAG2'):
                package_plan.plan(Path('unused'), [109], [], ())

    def test_invalid_reservations_fail_before_reading_disc(self):
        for spans in (((True, 8),), ((8, 8),), ((-1, 8),)):
            with self.subTest(spans=spans), patch.object(swap_mod, 'build') as build:
                with self.assertRaisesRegex(ValueError, 'invalid reservation'):
                    package_plan.plan(Path('unused'), [109], [], spans)
                build.assert_not_called()

    def build(self, disc, entry, pairs, **kwargs):
        lba = kwargs['relocate_lba']
        return [(lba * 2048, b'\0' * 3000, b'x' * 3000),
                (entry * 8, b'0' * 8, b'1' * 8)]

    def test_second_side_skips_reserved_gap(self):
        first = swap_mod.RELOCATE_FIRST_LBA
        spans = (((first + 2) * 2048, (first + 4) * 2048),)
        with patch.object(swap_mod, 'build', side_effect=self.build):
            overlays = package_plan.plan(Path('unused'), [109, 110], [], spans,
                                         relocation_blocked=frozenset())
        self.assertEqual([o[0] for o in overlays[::2]],
                         [first * 2048, (first + 4) * 2048])

    def test_blocked_relocation_and_header_collision_are_refused(self):
        with patch.object(swap_mod, 'build', side_effect=self.build):
            with self.assertRaisesRegex(ValueError, 'BAG1/BAG2'):
                package_plan.plan(Path('unused'), [109], [], (),
                                  relocation_blocked=frozenset({109}))
            with self.assertRaisesRegex(ValueError, 'reserved'):
                package_plan.plan(Path('unused'), [109], [], ((872, 880),),
                                  relocation_blocked=frozenset())
