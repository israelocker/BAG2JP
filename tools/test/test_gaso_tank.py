"""Packet-level regression for tank vertical direction and rival-space anchoring."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


def linux_path(path: Path) -> str:
    """Convert an absolute Windows checkout path for the recorded WSL compiler."""
    return '/mnt/' + path.drive[0].lower() + path.as_posix()[2:]


class GasoTankTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        """Build the complete production headers with a bounded guest-RAM shim."""
        cls.directory = tempfile.TemporaryDirectory(dir=ROOT / '_work')
        cls.addClassCleanup(cls.directory.cleanup)
        cls.binary = linux_path(Path(cls.directory.name) / 'tank')
        subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', 'gcc', '-std=c11',
                        '-Wall', '-Werror', '-Wno-unused-function',
                        '-I' + linux_path(ROOT / 'mods-src/bag2jp.feature.bag1-content'),
                        linux_path(ROOT / 'tools/test/gaso_tank_harness.c'),
                        '-o', cls.binary], check=True)

    def run_scenario(self, scenario: int) -> None:
        """Check the actual emitted packets, not a duplicate geometry function."""
        result = subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', self.binary,
                                 str(scenario)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_tank_visual_never_overwrites_rival_coordinates(self) -> None:
        self.run_scenario(32)

    def test_tank_visual_leaves_both_actors_and_epoch_coordinates_native(self) -> None:
        self.run_scenario(33)

    def test_landed_tank_cap_is_above_floor(self) -> None:
        self.run_scenario(0)

    def test_falling_tank_starts_above_landed_tank(self) -> None:
        self.run_scenario(1)

    def test_tank_uses_rival_model_transform(self) -> None:
        self.run_scenario(2)

    def test_invalid_rival_does_not_emit_stale_tank(self) -> None:
        self.run_scenario(3)

    def test_rival_whose_record_exceeds_ram_is_rejected(self) -> None:
        self.run_scenario(4)

    def test_hit_spawn_anchors_base_at_floor_not_pelvis(self) -> None:
        self.run_scenario(5)

    def test_tank_lasts_while_trapped_and_cuts_after_release(self) -> None:
        self.run_scenario(6)

    def test_next_attack_clears_tank_and_its_hit_drops_a_new_one(self) -> None:
        self.run_scenario(7)

    def test_attack_running_before_the_drop_does_not_clear_it(self) -> None:
        self.run_scenario(8)

    def test_hits_before_a_reset_are_not_replayed(self) -> None:
        self.run_scenario(9)

    def test_trap_reentry_restarts_release_countdown(self) -> None:
        self.run_scenario(10)

    def test_character_change_invalidates_tank(self) -> None:
        self.run_scenario(11)

    def test_valid_replacement_actor_does_not_inherit_tank(self) -> None:
        self.run_scenario(12)

    def test_disabling_bag1_invalidates_tank(self) -> None:
        self.run_scenario(13)

    def test_unowned_slot1_does_not_prolong_trap(self) -> None:
        self.run_scenario(14)

    def test_lifecycle_change_in_combat_discards_old_tank_and_hits(self) -> None:
        self.run_scenario(15)

    def test_paused_existing_attack_never_becomes_a_new_attack(self) -> None:
        self.run_scenario(16)

    def test_attack_edge_is_observed_while_rendering_is_unavailable(self) -> None:
        self.run_scenario(17)

    def test_render_failure_does_not_pause_tank_lifetime_bound(self) -> None:
        self.run_scenario(18)

    def test_new_hit_after_lifecycle_callback_before_first_tick_is_not_lost(self) -> None:
        self.run_scenario(19)

    def test_first_hit_after_combat_reentry_is_not_lost(self) -> None:
        self.run_scenario(20)

    def test_liquid_is_one_additive_tint_layer_with_faint_bubble_outlines(self) -> None:
        self.run_scenario(21)

    def test_culling_follows_a_mirrored_rival(self) -> None:
        self.run_scenario(22)

    def test_camera_above_tank_sees_cap_not_inner_glass(self) -> None:
        self.run_scenario(23)

    def test_camera_below_floor_culls_the_whole_cap(self) -> None:
        self.run_scenario(24)

    def test_bubble_radii_follow_pixel_aspect(self) -> None:
        for scenario in (25, 26, 27):
            with self.subTest(scenario=scenario):
                self.run_scenario(scenario)

    def test_unknown_or_extreme_aspect_skips_bubbles_not_tank(self) -> None:
        for scenario in (28, 29, 30):
            with self.subTest(scenario=scenario):
                self.run_scenario(scenario)

    def test_bubble_aspect_is_not_cached_across_ticks(self) -> None:
        self.run_scenario(31)

    def test_lock_and_bubble_cues_follow_bag1_controller(self) -> None:
        self.run_scenario(34)

    def test_no_tank_cues_after_release_or_reset(self) -> None:
        self.run_scenario(35)


if __name__ == '__main__':
    unittest.main()
