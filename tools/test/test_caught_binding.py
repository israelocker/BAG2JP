"""Byte-RAM publication tests; not a live controller or safe-hook acceptance."""
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.test.test_caught_loan import ROOT, linux_path


class CaughtBindingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        """Compile the candidate RAM transaction, not a Python copy of its logic."""
        cls.directory = tempfile.TemporaryDirectory(dir=ROOT / '_work')
        cls.addClassCleanup(cls.directory.cleanup)
        cls.binary = linux_path(Path(cls.directory.name) / 'caught-binding')
        subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', 'gcc', '-std=c11',
                        '-Wall', '-Wextra', '-Werror',
                        '-I' + linux_path(ROOT / 'mods-src/bag2jp.feature.bag1-content'),
                        linux_path(ROOT / 'tools/test/caught_binding_harness.c'),
                        '-o', cls.binary], check=True)

    def run_scenario(self, scenario: int, value: int = 0) -> None:
        """Run the real C component against independent byte-level assertions."""
        result = subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', self.binary,
                                 str(scenario), str(value)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_publishes_and_retires_only_ten_slot_bytes(self) -> None:
        self.run_scenario(0)

    def test_failed_validation_preserves_all_ram(self) -> None:
        for field in range(25):
            with self.subTest(field=field):
                self.run_scenario(1, field)

    def test_shared_partial_cross_kind_tables_and_bad_actor_list_are_rejected(self) -> None:
        for kind in range(11):
            with self.subTest(kind=kind):
                self.run_scenario(2, kind)

    def test_retirement_checks_owned_tuple_and_sampled_references(self) -> None:
        for field in range(12):
            with self.subTest(field=field):
                self.run_scenario(3, field)

    def test_additional_loaded_actors_cannot_share_table_ranges(self) -> None:
        self.run_scenario(4)

    def test_four_other_loaded_actors_do_not_overflow_alias_inventory(self) -> None:
        self.run_scenario(5)


if __name__ == '__main__':
    unittest.main()
