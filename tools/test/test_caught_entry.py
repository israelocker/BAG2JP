"""Stopped-RAM entry transaction, not runtime integration or gameplay proof."""
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.test.test_caught_loan import ROOT, linux_path


class CaughtEntryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        """Compile the real entry/adapter/binding headers with a synthetic fixture."""
        cls.directory = tempfile.TemporaryDirectory(dir=ROOT / '_work')
        cls.addClassCleanup(cls.directory.cleanup)
        cls.binary = linux_path(Path(cls.directory.name) / 'caught-entry')
        subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', 'gcc', '-std=c11',
                        '-Wall', '-Wextra', '-Werror',
                        '-I' + linux_path(ROOT / 'mods-src/bag2jp.feature.bag1-content'),
                        linux_path(ROOT / 'tools/test/caught_entry_harness.c'),
                        '-o', cls.binary], check=True)

    def run_scenario(self, scenario: int, kind: int = 0) -> None:
        """Run a case checking exact RAM, entry and persistent descriptor effects."""
        result = subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', self.binary,
                                 str(scenario), str(kind)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_publish_and_redirect_once_for_both_sides_and_three_rivals(self) -> None:
        for kind in range(12):
            with self.subTest(kind=kind):
                self.run_scenario(0, kind)

    def test_invalid_attack_identity_request_and_memory_leave_everything_unchanged(self) -> None:
        for kind in range(32):
            with self.subTest(kind=kind):
                self.run_scenario(1, kind)

    def test_retry_retire_and_new_hit_use_the_same_adapter(self) -> None:
        self.run_scenario(2)

    def test_null_and_bounded_inputs_are_refused_without_side_effects(self) -> None:
        for kind in (*range(7), 8, 9):
            with self.subTest(kind=kind):
                self.run_scenario(3, kind)

    def test_retirement_checks_pause_and_actual_ram_references(self) -> None:
        for kind in range(6):
            with self.subTest(kind=kind):
                self.run_scenario(4, kind)


if __name__ == '__main__':
    unittest.main()
