"""Quarantine regression, not evidence of CAUGHT playback or fidelity."""
import os
import re
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.test.test_caught_loan import ROOT, linux_path

# Overridable so the same harness can prove a stale callback source RED.
SOURCE = Path(os.environ.get(
    'GASO_CAUGHT_SOURCE',
    ROOT / 'mods-src/bag2jp.feature.bag1-content/bag2jp_gaso_caught.c'))


class GasoCaughtRuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        """Compile the actual callback with the installed framework's real ABI.

        The default build matches the runtime (no clip published, never
        redirects); the published build proves the contract publication,
        the redirect onto it and the slot1 retirement against simulated RAM.
        """
        include = ROOT.parent / 'BAG2JP-codex-build/BAG2JP/psxrecomp/runtime/include'
        if not include.is_dir():
            raise RuntimeError(f'Required framework headers unavailable: {include}')
        cls.directory = tempfile.TemporaryDirectory(dir=ROOT / '_work')
        cls.addClassCleanup(cls.directory.cleanup)
        cls.binaries = {}
        for published in (0, 1):
            binary = linux_path(Path(cls.directory.name) / f'gaso-caught-runtime-{published}')
            result = subprocess.run(
                ['wsl.exe', '-d', 'Ubuntu', '--exec', 'gcc', '-std=c11',
                 '-Wall', '-Wextra', '-Werror', '-I' + linux_path(include),
                 '-I' + linux_path(ROOT / 'mods-src/bag2jp.feature.bag1-content'),
                 f'-DGASO_CAUGHT_CLIP_PUBLISHED={published}',
                 linux_path(ROOT / 'tools/test/gaso_caught_runtime_harness.c'),
                 linux_path(SOURCE),
                 linux_path(ROOT / 'mods-src/bag2jp.feature.bag1-content/bag2jp_caught_bank.c'),
                 '-o', binary], capture_output=True, text=True)
            if result.returncode:
                raise AssertionError(result.stdout + result.stderr)
            cls.binaries[published] = binary

    def run_scenario(self, scenario: int) -> None:
        """Run a controlled callback boundary in both builds without a game."""
        for published, binary in self.binaries.items():
            with self.subTest(published=published):
                result = subprocess.run(
                    ['wsl.exe', '-d', 'Ubuntu', '--exec', binary, str(scenario)],
                    capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_unverified_callback_preserves_cpu_and_never_accesses_guest(self) -> None:
        self.run_scenario(0)

    def test_reactivation_copies_authentic_bank_once_and_keeps_entry_inert(self) -> None:
        self.run_scenario(1)

    def test_heat_strike_and_unauthenticated_sources_never_redirect(self) -> None:
        self.run_scenario(2)

    def test_authenticated_gaso_record_is_consumed_once(self) -> None:
        self.run_scenario(3)

    def test_failed_bank_allocation_is_terminal_without_guest_writes(self) -> None:
        self.run_scenario(4)

    def test_corrupted_bank_is_reported_and_never_repaired(self) -> None:
        self.run_scenario(5)

    def test_prepared_bank_leaves_capture_and_entry_read_only(self) -> None:
        self.run_scenario(6)

    def test_unsafe_actor_and_stack_pointers_are_rejected_before_reads(self) -> None:
        self.run_scenario(7)

    def test_stack_span_tracks_live_retail_or_expanded_ram(self) -> None:
        """Accept the expanded stack, not its out-of-range tail or retail alias."""
        self.run_scenario(8)

    def test_lookup_uses_recipient_character_and_version_without_writes(self) -> None:
        """All three authentic clips, both sides, and fail-closed negatives."""
        self.run_scenario(9)

    def test_reset_and_savestate_invalidate_captured(self) -> None:
        """Session reset and savestate clear captured records without writes."""
        self.run_scenario(10)

    def test_secondary_effect_is_cleared_only_after_owned_publication(self) -> None:
        """Clear selector1 on direct owned CAUGHT, preserving other effects and side."""
        self.run_scenario(13)

    def test_secondary_effect_is_preserved_when_caught_is_rejected(self) -> None:
        """Preserve BAG2 recipients, refused binding, foreign attackers and reflection."""
        self.run_scenario(14)

    def test_secondary_effect_span_is_checked_at_ram_boundary(self) -> None:
        """An actor may fit its binding while its secondary selector is out of RAM."""
        self.run_scenario(15)

    def test_publication_slot1_guarded_and_restorable(self) -> None:
        """Slot1 publication is gated by CLIP_PUBLISHED; reset/savestate clear it."""
        self.run_scenario(11)

    def test_slot1_retires_after_the_clip_leaves_it(self) -> None:
        """Restore once the actor left slot1 (or never entered it); refusals retry and fail closed."""
        self.run_scenario(12)

    def test_rehit_preserves_only_compatible_live_pose_and_never_writes_timers(self) -> None:
        """Continue verified settled CAUGHT, otherwise retain normal native entry."""
        self.run_scenario(16)

    def test_rehit_barriers_keep_the_native_entry(self) -> None:
        """Identity, BAG1 lookup and the RAM contract each refuse on their own."""
        self.run_scenario(17)

    def test_rehit_continuation_is_symmetric_on_side_zero(self) -> None:
        """The mirrored victim side takes the same continuation without writes."""
        self.run_scenario(18)

    def test_capture_is_rejected_after_actor_or_table_identity_drift(self) -> None:
        """Consume stale authorization without take counters, writes or redirect."""
        self.run_scenario(19)

    def test_successful_slot_reuse_emits_positive_verified_log(self) -> None:
        """Make active reuse observable rather than inferring no refusal."""
        self.run_scenario(20)

    def test_replacement_controller_consumes_capture_for_old_actor(self) -> None:
        """Changing both list and controller must not strand old authorization."""
        self.run_scenario(21)

    def test_retirement_and_stale_capture_are_independently_accounted(self) -> None:
        """Legitimate earlier retirement may write even though a new take is stale."""
        self.run_scenario(22)

    def test_native_init_revokes_capture_even_with_identical_actor_bytes(self) -> None:
        """A real init event supersedes either actor's pre-init capture."""
        self.run_scenario(23)

    def test_native_init_rejects_wrong_site_signature_and_arguments(self) -> None:
        """Guard the native main pair; leave companions and unrelated calls alone."""
        self.run_scenario(24)

    def test_init_observer_preserves_published_tuple_and_visual_epoch(self) -> None:
        """Capture invalidation must not silently discard live binding ownership."""
        self.run_scenario(25)

    def test_init_stack_boundaries_and_two_pending_recipient_records(self) -> None:
        """Retail, expanded and scratchpad stack spans revoke both pending sides."""
        self.run_scenario(26)


MANIFEST = ROOT / 'mods-src/bag2jp.feature.bag1-content/1.0.0/manifest.toml'


class GasoCaughtManifestTest(unittest.TestCase):
    def test_init_observer_uses_existing_native_instruction_site(self) -> None:
        """Pin original JP bytes and opt-in without requiring generated artifacts."""
        text = SOURCE.read_text(encoding='utf-8')
        site = int(re.search(r'#define GASO_CAUGHT_INIT_SITE\s+(0x[0-9a-f]+)u', text).group(1), 16)
        word = int(re.search(r'#define GASO_CAUGHT_INIT_WORD\s+(0x[0-9a-f]+)u', text).group(1), 16)
        executable = (ROOT / 'assets/disc_files/SLPM_862.19').read_bytes()
        self.assertEqual(executable[:8], b'PS-X EXE')
        base = int.from_bytes(executable[0x18:0x1c], 'little')
        offset = 0x800 + site - base
        self.assertEqual(int.from_bytes(executable[offset:offset+4], 'little'), word)
        config = tomllib.loads((ROOT / 'patches/BAG2JP-game.toml').read_text(encoding='utf-8'))
        self.assertIn(f'0x{site:08X}', config['recompiler']['mod_instruction_sites'])

    def test_native_instruction_fixture_does_not_read_generated_artifacts(self) -> None:
        """Original-byte regression must run before the external AOT tree exists."""
        read_text = Path.read_text

        def reject_generated(path: Path, *args, **kwargs) -> str:
            if path.suffix == '.c' and path.parent.name == 'generated':
                raise FileNotFoundError(f'No generated fixture: {path}')
            return read_text(path, *args, **kwargs)

        with patch.object(Path, 'read_text', reject_generated):
            self.test_init_observer_uses_existing_native_instruction_site()

    def test_unverified_reaction_is_disabled_by_default(self) -> None:
        """Prevent a default plan from activating the unfinished reaction."""
        manifest = tomllib.loads(MANIFEST.read_text(encoding='utf-8'))
        feature = next(f for f in manifest['feature'] if f['id'] == 'bag1-gaso-caught')
        self.assertIs(feature['default_enabled'], False)

    def test_feature_activates_exactly_the_registered_plugin_ids(self) -> None:
        """Only plan plugin ids get hooks: a renamed id would silently drop one."""
        manifest = tomllib.loads(MANIFEST.read_text(encoding='utf-8'))
        declared = sorted(p['id'] for p in manifest['plugin']
                          if p['feature'] == 'bag1-gaso-caught')
        registered = sorted(set(re.findall(
            r'psx_mod_register_\w+_plugin\(\s*"([^"]+)"', SOURCE.read_text(encoding='utf-8'))))
        self.assertEqual(declared, ['bag2jp.gaso_caught', 'bag2jp.gaso_caught_capture'])
        self.assertEqual(registered, declared)

    def test_runtime_source_never_publishes_the_unverified_clip(self) -> None:
        """Keep the shipped default build unable to change the entry slot."""
        text = SOURCE.read_text(encoding='utf-8')
        self.assertTrue('#define GASO_CAUGHT_CLIP_PUBLISHED 0' in text,
                        f'{SOURCE} must default GASO_CAUGHT_CLIP_PUBLISHED to 0')


class GasoCaughtAotIntegrationTest(unittest.TestCase):
    """Requires emitted main C under BAG2JP_GENERATED_DIR (local build by default).

    Missing emission is an explicit integration skip, never host success or a
    claim that the dispatcher ran. Present but incorrectly ordered C must fail.
    """

    def assert_init_dispatch_order(self, generated: str) -> None:
        """Pin pre-JAL dispatch between native argument setup and CPS transfer."""
        start = generated.index('/* 0x8002BA14: 0x27A60010 */')
        end = generated.index('block_8002BA20:', start)
        seam = generated[start:end]
        markers = (
            'psx_mod_instruction(cpu, 0x8002BA18u, 0x0C00B617u);',
            'cpu->gpr[31] = 0x8002BA20u;',
            '/* 0x8002BA1C: 0x30E7FFFF */',
            'cpu->pc = 0x8002D85Cu; return;',
        )
        for marker in markers:
            self.assertEqual(seam.count(marker), 1, marker)
        positions = [seam.index(marker) for marker in markers]
        self.assertEqual(positions, sorted(positions), 'dispatch must precede link/delay/transfer')

    def test_emitted_init_dispatch_precedes_link_delay_and_transfer(self) -> None:
        """Find the emitted site regardless of recompiler shard numbering."""
        directory = Path(os.environ.get(
            'BAG2JP_GENERATED_DIR',
            ROOT.parent / 'BAG2JP-codex-build/BAG2JP/generated'))
        files = sorted(directory.glob('*.c'))
        if not files:
            self.skipTest(f'AOT integration requires emitted main C: {directory}')
        matches = [text for path in files
                   if '/* 0x8002BA14: 0x27A60010 */' in (text := path.read_text(encoding='utf-8'))]
        self.assertEqual(len(matches), 1, 'native seam must appear in exactly one emitted shard')
        self.assert_init_dispatch_order(matches[0])

    def test_missing_emission_is_explicit_integration_skip(self) -> None:
        """No external generated files must not become a host FileNotFoundError."""
        with patch.object(Path, 'glob', return_value=iter(())):
            with self.assertRaises(unittest.SkipTest):
                self.test_emitted_init_dispatch_precedes_link_delay_and_transfer()

    def test_order_check_rejects_late_missing_and_duplicate_dispatch(self) -> None:
        """Mutate a bounded emitted-C seam, not a generated artifact on disk."""
        start = '/* 0x8002BA14: 0x27A60010 */\n'
        dispatch = 'psx_mod_instruction(cpu, 0x8002BA18u, 0x0C00B617u);\n'
        link = 'cpu->gpr[31] = 0x8002BA20u;\n'
        delay = '/* 0x8002BA1C: 0x30E7FFFF */\n'
        transfer = 'cpu->pc = 0x8002D85Cu; return;\n'
        end = 'block_8002BA20:\n'
        self.assert_init_dispatch_order(start + dispatch + link + delay + transfer + end)
        for middle in (link + dispatch + delay + transfer,
                       link + delay + dispatch + transfer,
                       link + delay + transfer + dispatch,
                       link + delay + transfer,
                       dispatch + dispatch + link + delay + transfer):
            with self.subTest(middle=middle), self.assertRaises(AssertionError):
                self.assert_init_dispatch_order(start + middle + end)


if __name__ == '__main__':
    unittest.main()
