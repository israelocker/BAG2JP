"""Quarantine regression, not evidence of CAUGHT playback or fidelity."""
import os
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path

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
        redirects); the published build proves the one-shot redirect logic
        that a future verified clip would enable.
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
                 linux_path(SOURCE), '-o', binary], capture_output=True, text=True)
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

    def test_reset_and_reactivation_never_allocate_or_modify_guest(self) -> None:
        self.run_scenario(1)

    def test_heat_strike_and_unauthenticated_sources_never_redirect(self) -> None:
        self.run_scenario(2)

    def test_authenticated_gaso_record_is_consumed_once(self) -> None:
        self.run_scenario(3)


class GasoCaughtManifestTest(unittest.TestCase):
    def test_unverified_reaction_is_disabled_by_default(self) -> None:
        """Prevent a default plan from activating the unfinished reaction."""
        path = ROOT / 'mods-src/bag2jp.feature.bag1-content/1.0.0/manifest.toml'
        manifest = tomllib.loads(path.read_text(encoding='utf-8'))
        feature = next(f for f in manifest['feature'] if f['id'] == 'bag1-gaso-caught')
        self.assertIs(feature['default_enabled'], False)

    def test_runtime_source_never_publishes_the_unverified_clip(self) -> None:
        """Keep the shipped default build unable to change the entry slot."""
        text = SOURCE.read_text(encoding='utf-8')
        self.assertTrue('#define GASO_CAUGHT_CLIP_PUBLISHED 0' in text,
                        f'{SOURCE} must default GASO_CAUGHT_CLIP_PUBLISHED to 0')


if __name__ == '__main__':
    unittest.main()
