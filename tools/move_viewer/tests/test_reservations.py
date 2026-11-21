"""Package inventory must conservatively protect raw and user overlays."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from tools.move_viewer import reservations


class ReservationInventoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def package(self, target: str, offset: int, payload: bytes = b'abc') -> None:
        (self.root / 'data.bin').write_bytes(payload)
        (self.root / 'manifest.toml').write_text(f'''[[target]]
game_id = "SLPM-86219"
[[overlay]]
target = "{target}"
offset = {offset}
file = "data.bin"
sha256 = "{hashlib.sha256(payload).hexdigest()}"
''', encoding='utf-8')

    def test_user_span_is_exact_even_for_disabled_package(self) -> None:
        self.package('disc_user', 100)
        self.assertEqual(reservations.inventory((self.root,)), ((100, 103),))

    def test_raw_cross_sector_reserves_both_full_user_sectors(self) -> None:
        self.package('disc_raw', 2351)
        self.assertEqual(reservations.inventory((self.root,)), ((0, 4096),))

    def test_missing_root_is_not_empty_inventory(self) -> None:
        with self.assertRaises(ValueError):
            reservations.inventory((self.root / 'missing',))

    def test_bad_hash_is_rejected(self) -> None:
        self.package('disc_user', 100)
        (self.root / 'data.bin').write_bytes(b'changed')
        with self.assertRaises(ValueError):
            reservations.inventory((self.root,))

    def test_unknown_overlay_target_is_not_silently_ignored(self) -> None:
        self.package('disc_other', 100)
        with self.assertRaises(ValueError):
            reservations.inventory((self.root,))

    def test_invalid_offsets_are_refused(self) -> None:
        for literal in ('-1', 'true', '1.5'):
            self.package('disc_user', 100)
            p = self.root / 'manifest.toml'
            p.write_text(p.read_text().replace('offset = 100', f'offset = {literal}'))
            with self.subTest(literal=literal), self.assertRaises(ValueError):
                reservations.inventory((self.root,))

    def test_wrong_region_and_hash_are_refused(self) -> None:
        for replacement in ('game_id = "OTHER"', 'game_id = "SLPM-86219"\ndisc_sha256 = "wrong"'):
            self.package('disc_user', 100)
            p = self.root / 'manifest.toml'
            p.write_text(p.read_text().replace('game_id = "SLPM-86219"', replacement))
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                reservations.inventory((self.root,))

    def test_path_escape_is_refused_before_payload_read(self) -> None:
        self.package('disc_user', 100)
        p = self.root / 'manifest.toml'
        p.write_text(p.read_text().replace('data.bin', '../outside.bin'))
        with self.assertRaisesRegex(ValueError, 'outside package'):
            reservations.inventory((self.root,))

    def test_exact_raw_boundary_does_not_reserve_next_sector(self) -> None:
        self.package('disc_raw', 2351, b'x')
        self.assertEqual(reservations.inventory((self.root,)), ((0, 2048),))

    def test_free_allocation_skips_unaligned_reservations(self) -> None:
        self.assertEqual(reservations.allocate(2, ((2049, 4097),), 0, 5), 3)

    def test_allocation_accepts_exact_end_and_rejects_exhaustion(self) -> None:
        self.assertEqual(reservations.allocate(2, (), 3, 5), 3)
        with self.assertRaises(ValueError):
            reservations.allocate(3, (), 3, 5)

    def test_manifest_collections_require_lists_of_tables(self) -> None:
        for field in ('overlay', 'patch', 'target'):
            for literal in ('""', '{}', '[1]'):
                self.package('disc_user', 100)
                p = self.root / 'manifest.toml'
                # Keep a valid target except when testing target itself.
                body = '[[target]]\ngame_id = "SLPM-86219"\n' if field != 'target' else ''
                p.write_text(f'{field} = {literal}\n' + body)
                with self.subTest(field=field, literal=literal), self.assertRaises(ValueError):
                    reservations.inventory((self.root,))
