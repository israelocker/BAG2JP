"""Host-only CAUGHT loan decisions, not guest publication or controller playback."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


def linux_path(path: Path) -> str:
    """Map the Windows checkout to the recorded WSL compiler mount."""
    return '/mnt/' + path.drive[0].lower() + path.as_posix()[2:]


class CaughtLoanTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        """Compile the actual candidate header with the neighboring host pattern."""
        cls.directory = tempfile.TemporaryDirectory(dir=ROOT / '_work')
        cls.addClassCleanup(cls.directory.cleanup)
        cls.binary = linux_path(Path(cls.directory.name) / 'caught-loan')
        subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', 'gcc', '-std=c11',
                        '-Wall', '-Wextra', '-Werror',
                        '-I' + linux_path(ROOT / 'mods-src/bag2jp.feature.bag1-content'),
                        linux_path(ROOT / 'tools/test/caught_loan_harness.c'),
                        '-o', cls.binary], check=True)

    def run_scenario(self, scenario: int, value: int = 0) -> None:
        """Check reducer actions without replacing the component under test."""
        result = subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', self.binary,
                                 str(scenario), str(value)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_enters_once_retires_then_requires_new_attack(self) -> None:
        self.run_scenario(0)

    def test_entry_rejects_unsafe_or_unverified_scope(self) -> None:
        for gate in range(22):
            with self.subTest(gate=gate):
                self.run_scenario(1, gate)

    def test_new_reaction_yields_without_reentering_same_hit(self) -> None:
        self.run_scenario(2)

    def test_each_reference_blocks_retirement_including_unknown_bits(self) -> None:
        for reference in (1, 2, 4, 8, 16, 15):
            with self.subTest(reference=reference):
                self.run_scenario(3, reference)

    def test_lost_identity_or_binding_never_restores_or_reuses_orphan(self) -> None:
        for field in (*range(14), *range(20, 34)):
            with self.subTest(field=field):
                self.run_scenario(4, field)

    def test_uncommitted_entry_does_not_mutate_state(self) -> None:
        self.run_scenario(5)

    def test_yield_and_restore_wait_for_safe_point(self) -> None:
        self.run_scenario(6)

    def test_three_supported_imports_can_enter_on_either_side(self) -> None:
        self.run_scenario(7)

    def test_each_live_reference_blocks_entry(self) -> None:
        for reference in (1, 2, 4, 8, 16, 15):
            with self.subTest(reference=reference):
                self.run_scenario(8, reference)

    def test_idle_owner_cannot_be_retargeted_to_erase_replay_history(self) -> None:
        self.run_scenario(9)

    def test_new_hit_yields_before_another_entry(self) -> None:
        self.run_scenario(10)

    def test_every_discarded_proposal_preserves_both_input_objects(self) -> None:
        for transition in range(4):
            with self.subTest(transition=transition):
                self.run_scenario(11, transition)


if __name__ == '__main__':
    unittest.main()
