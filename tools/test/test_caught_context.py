"""Read-only original-call context; not attacker/version authorization or gameplay."""
import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.test.test_caught_loan import ROOT, linux_path


class CaughtContextTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        """Compile the real reader and pin the original main/005 fixture code."""
        cls.main = ROOT / '_work/mainexe/slpm.bin'
        cls.overlay = ROOT / 'assets/archive/system/005.dbi'
        for path, digest in ((cls.main, '143b4bf866bf6e47876f54c9667aa476e178b3aaa1ecf4d8a9f022c7583cc00b'),
                             (cls.overlay, 'bc5f3045084e4b3e19009910441627977863c8b5791b5cdb716a766e68b28fb2')):
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise AssertionError(f'Original fixture hash mismatch: {path}')
        cls.directory = tempfile.TemporaryDirectory(dir=ROOT / '_work')
        cls.addClassCleanup(cls.directory.cleanup)
        cls.binary = linux_path(Path(cls.directory.name) / 'caught-context')
        source = ROOT / 'mods-src/bag2jp.feature.bag1-content'
        subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', 'gcc', '-std=c11',
                        '-Wall', '-Wextra', '-Werror', '-I' + linux_path(source),
                        linux_path(source / 'bag2jp_caught_context.c'),
                        linux_path(ROOT / 'tools/test/caught_context_harness.c'),
                        '-o', cls.binary], check=True)

    def run_scenario(self, scenario: int, kind: int, setup: int = 0) -> None:
        """Check context values or exact non-effects using the production reader."""
        result = subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', self.binary,
                                 str(scenario), str(kind), linux_path(self.main),
                                 linux_path(self.overlay), str(setup)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_main_controller_resolves_actor_on_both_sides_and_above_two_megabytes(self) -> None:
        for kind in range(16):
            with self.subTest(kind=kind):
                self.run_scenario(0, kind, kind)

    def test_actor_as_a0_companions_wrong_arguments_return_addresses_and_stack_are_rejected(self) -> None:
        for kind in range(14):
            with self.subTest(kind=kind):
                self.run_scenario(1, kind)

    def test_identity_pending_outer_caller_and_code_drift_are_rejected(self) -> None:
        for side in range(2):
            for kind in range(23):
                with self.subTest(side=side, kind=kind):
                    self.run_scenario(2, kind, side)

    def test_null_short_oversized_and_truncated_stack_inputs_leave_output_unchanged(self) -> None:
        for kind in range(7):
            with self.subTest(kind=kind):
                self.run_scenario(3, kind)

    def test_inclusive_actor_opponent_and_stack_boundaries_and_isolated_invalid_actors(self) -> None:
        for side in range(2):
            for kind in range(14):
                with self.subTest(side=side, kind=kind):
                    self.run_scenario(4, kind, side)


if __name__ == '__main__':
    unittest.main()
