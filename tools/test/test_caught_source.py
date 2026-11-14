"""Original producer-to-consumer provenance; synthetic clocks, not runtime wiring."""
import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.test.test_caught_loan import ROOT, linux_path


class CaughtSourceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        """Compile both real readers and bind fixture code to the original files."""
        cls.main = ROOT / '_work/mainexe/slpm.bin'
        cls.overlay = ROOT / 'assets/archive/system/005.dbi'
        for path, digest in ((cls.main, '143b4bf866bf6e47876f54c9667aa476e178b3aaa1ecf4d8a9f022c7583cc00b'),
                             (cls.overlay, 'bc5f3045084e4b3e19009910441627977863c8b5791b5cdb716a766e68b28fb2')):
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise AssertionError(f'Original fixture hash mismatch: {path}')
        cls.directory = tempfile.TemporaryDirectory(dir=ROOT / '_work')
        cls.addClassCleanup(cls.directory.cleanup)
        cls.binary = linux_path(Path(cls.directory.name) / 'caught-source')
        source = ROOT / 'mods-src/bag2jp.feature.bag1-content'
        subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', 'gcc', '-std=c11',
                        '-Wall', '-Wextra', '-Werror', '-I' + linux_path(source),
                        linux_path(source / 'bag2jp_caught_source.c'),
                        linux_path(source / 'bag2jp_caught_context.c'),
                        linux_path(ROOT / 'tools/test/caught_source_harness.c'),
                        '-o', cls.binary], check=True)

    def run_scenario(self, scenario: int, kind: int, setup: int = 0) -> None:
        """Require assertions on real reader output and complete RAM non-effects."""
        result = subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', self.binary,
                                 str(scenario), str(kind), linux_path(self.main),
                                 linux_path(self.overlay), str(setup)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_source_identity_and_direction_survive_once_including_foreign_and_mirror(self) -> None:
        for setup in range(4):
            for kind in range(3):
                with self.subTest(setup=setup, kind=kind):
                    self.run_scenario(0, kind, setup)

    def test_invalid_producer_invalidates_old_record_without_touching_ram(self) -> None:
        for side in range(2):
            for kind in range(22):
                with self.subTest(side=side, kind=kind):
                    self.run_scenario(1, kind, side)

    def test_stale_clock_identity_wrong_call_and_pending_cannot_reuse_record(self) -> None:
        for side in range(2):
            for kind in range(16):
                with self.subTest(side=side, kind=kind):
                    self.run_scenario(2, kind, side)

    def test_null_and_short_inputs_fail_closed(self) -> None:
        for kind in range(12):
            with self.subTest(kind=kind):
                self.run_scenario(3, kind)

    def test_exact_actor_stack_and_snapshot_boundaries_and_unverified_table_rows(self) -> None:
        for side in range(2):
            for kind in range(12):
                with self.subTest(side=side, kind=kind):
                    self.run_scenario(4, kind, side)


if __name__ == '__main__':
    unittest.main()
