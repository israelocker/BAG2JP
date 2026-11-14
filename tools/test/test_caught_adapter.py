"""Composed CAUGHT adapter tests; not a live hook, controller or game acceptance."""
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.test.test_caught_loan import ROOT, linux_path


class CaughtAdapterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        """Compile the real policy plus transaction headers, not a Python copy."""
        cls.directory = tempfile.TemporaryDirectory(dir=ROOT / '_work')
        cls.addClassCleanup(cls.directory.cleanup)
        cls.binary = linux_path(Path(cls.directory.name) / 'caught-adapter')
        subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', 'gcc', '-std=c11',
                        '-Wall', '-Wextra', '-Werror',
                        '-I' + linux_path(ROOT / 'mods-src/bag2jp.feature.bag1-content'),
                        linux_path(ROOT / 'tools/test/caught_adapter_harness.c'),
                        '-o', cls.binary], check=True)

    def run_scenario(self, scenario: int, value: int = 0) -> None:
        """Run one composed scenario against byte-level RAM assertions."""
        result = subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', self.binary,
                                 str(scenario), str(value)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_enter_publishes_before_adopting_then_yields_and_retires(self) -> None:
        self.run_scenario(0)

    def test_failed_publication_keeps_loan_and_ram_then_retries(self) -> None:
        for kind in range(7):
            with self.subTest(kind=kind):
                self.run_scenario(1, kind)

    def test_failed_retirement_keeps_borrow_then_retries(self) -> None:
        for kind in range(8):
            with self.subTest(kind=kind):
                self.run_scenario(2, kind)

    def test_abandon_is_terminal_without_leaking_slot_one(self) -> None:
        for kind in range(2):
            with self.subTest(kind=kind):
                self.run_scenario(3, kind)

    def test_lost_adapter_state_cannot_publish_the_borrow_twice(self) -> None:
        self.run_scenario(4)

    def test_candidate_must_match_every_observed_identity_field(self) -> None:
        for kind in range(6):
            with self.subTest(kind=kind):
                self.run_scenario(5, kind)

    def test_every_legitimate_reaction_yields_without_rewriting_it(self) -> None:
        for kind in range(3):
            with self.subTest(kind=kind):
                self.run_scenario(6, kind)

    def test_refused_retirement_keeps_the_binding_bytes(self) -> None:
        self.run_scenario(7)

    def test_live_reference_blocks_retirement(self) -> None:
        self.run_scenario(8)

    def test_shared_tables_by_another_actor_block_publication(self) -> None:
        for kind in range(2):
            with self.subTest(kind=kind):
                self.run_scenario(9, kind)

    def test_retired_hit_cannot_replay_the_same_attack(self) -> None:
        self.run_scenario(10)

    def test_stale_binding_flag_cannot_destroy_an_intact_borrow(self) -> None:
        self.run_scenario(11)

    def test_every_entry_precondition_keeps_the_descriptor_idle(self) -> None:
        for kind in range(11):
            with self.subTest(kind=kind):
                self.run_scenario(12, kind)

    def test_owned_region_publishes_and_retires_only_main_ram_slot_bytes(self) -> None:
        self.run_scenario(13)

    def test_owned_region_negatives_quiescent_and_identity(self) -> None:
        for kind in range(3):
            with self.subTest(kind=kind):
                self.run_scenario(14, kind)

    def test_retire_failure_owned_requires_quiescent_stopped_unreferenced_slot(self) -> None:
        for kind in range(4):
            with self.subTest(kind=kind):
                self.run_scenario(15, kind)

    def test_partner_exclusion_owned_tables_inside_region_block_enter(self) -> None:
        for kind in range(4):
            with self.subTest(kind=kind):
                self.run_scenario(16, kind)

    def test_retire_owned_region_defects_require_region_identity(self) -> None:
        for kind in range(4, 9):
            with self.subTest(kind=kind):
                self.run_scenario(17, kind)

    def test_reset_on_idle_without_binding_succeeds_and_clears(self) -> None:
        self.run_scenario(18)

    def test_reset_with_installed_binding_fails_and_keeps_state(self) -> None:
        self.run_scenario(19)

    def test_save_and_load_state_roundtrip_preserves_everything(self) -> None:
        self.run_scenario(20)

    def test_save_fail_closed_for_null_and_short_output_buffers(self) -> None:
        self.run_scenario(21)

    def test_load_fail_closed_for_null_and_short_input_buffers(self) -> None:
        self.run_scenario(22)

    def test_save_load_region_metadata_not_restored(self) -> None:
        self.run_scenario(23)

    def test_save_state_exactly_128_bytes_with_region_padding_zero(self) -> None:
        self.run_scenario(24)


if __name__ == '__main__':
    unittest.main()
