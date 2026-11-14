"""Exercise the real transaction with disjoint main-RAM and owned clip buffers."""
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.test.test_caught_loan import ROOT, linux_path


class CaughtOwnedClipTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        """Compile the production binding and independent arena assertions."""
        cls.directory = tempfile.TemporaryDirectory(dir=ROOT / '_work')
        cls.addClassCleanup(cls.directory.cleanup)
        cls.binary = linux_path(Path(cls.directory.name) / 'caught-owned-clip')
        subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', 'gcc', '-std=c11',
                        '-D_DEFAULT_SOURCE', '-Wall', '-Wextra', '-Werror',
                        '-I' + linux_path(ROOT / 'mods-src/bag2jp.feature.bag1-content'),
                        linux_path(ROOT / 'tools/test/caught_owned_clip_harness.c'),
                        '-o', cls.binary], check=True)

    def run_scenario(self, scenario: int, field: int = 0) -> None:
        """Check process assertions, including untouched RAM and arena canaries."""
        result = subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', self.binary,
                                 str(scenario), str(field)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_owned_clip_publishes_and_retires_only_ten_main_slot_bytes(self) -> None:
        self.run_scenario(0)

    def test_bad_region_metadata_or_main_actor_alias_never_writes(self) -> None:
        for field in range(21):
            with self.subTest(field=field):
                self.run_scenario(1, field)

    def test_live_owned_clip_references_and_unproven_quiescence_block_restore(self) -> None:
        for field in range(8):
            with self.subTest(field=field):
                self.run_scenario(2, field)

    def test_clip_may_end_exactly_at_allocated_region_boundary(self) -> None:
        self.run_scenario(3)

    def test_legacy_entry_point_still_rejects_expansion_addresses(self) -> None:
        self.run_scenario(4)

    def test_allocation_may_end_exactly_at_expansion_aperture_boundary(self) -> None:
        self.run_scenario(5)

    def test_relative_metadata_is_not_tied_to_the_fixture_layout(self) -> None:
        self.run_scenario(6)

    def test_aligned_tail_outside_clip_is_rejected_before_read(self) -> None:
        self.run_scenario(7)

    def test_restore_refused_when_not_quiescent_owned_region(self) -> None:
        self.run_scenario(8)

    def test_restore_refused_when_region_identity_changed(self) -> None:
        self.run_scenario(9)

    def test_publication_refused_when_owner_tables_inside_owned_region(self) -> None:
        self.run_scenario(10)


if __name__ == '__main__':
    unittest.main()
