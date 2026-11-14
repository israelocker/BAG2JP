"""Capture -> take integration: producer site 0x8009b5b4 then consumer call."""
import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.test.test_caught_loan import ROOT, linux_path


class CaughtIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        """Compile the real capture/readers against original fixture code."""
        cls.source = ROOT / 'mods-src/bag2jp.feature.bag1-content'
        cls.main = ROOT / '_work/mainexe/slpm.bin'
        cls.overlay = ROOT / 'assets/archive/system/005.dbi'
        for path, digest in ((cls.main, '143b4bf866bf6e47876f54c9667aa476e178b3aaa1ecf4d8a9f022c7583cc00b'),
                             (cls.overlay, 'bc5f3045084e4b3e19009910441627977863c8b5791b5cdb716a766e68b28fb2')):
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise AssertionError(f'Original fixture hash mismatch: {path}')
        cls.directory = tempfile.TemporaryDirectory(dir=ROOT / '_work')
        cls.addClassCleanup(cls.directory.cleanup)
        cls.binary = linux_path(Path(cls.directory.name) / 'caught-integration')
        subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', 'gcc', '-std=c11',
                        '-Wall', '-Wextra', '-Werror', '-I' + linux_path(cls.source),
                        linux_path(cls.source / 'bag2jp_caught_source.c'),
                        linux_path(cls.source / 'bag2jp_caught_context.c'),
                        linux_path(ROOT / 'tools/test/caught_integration_harness.c'),
                        '-o', cls.binary], check=True)

    def run_scenario(self, scenario: int, kind: int) -> None:
        result = subprocess.run(['wsl.exe', '-d', 'Ubuntu', '--exec', self.binary,
                                 str(scenario), str(kind)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_capture_then_take_happy_path_all_sides_chars(self) -> None:
        for side in range(2):
            for is_self in range(2):
                for char in (0, 1, 9):
                    kind = side | (is_self << 1) | (char << 2)
                    with self.subTest(side=side, is_self=is_self, char=char):
                        self.run_scenario(0, kind)

    def test_take_rejects_clock_mismatch(self) -> None:
        for side in range(2):
            for is_self in range(2):
                kind = side | (is_self << 1) | (9 << 2)
                with self.subTest(side=side, is_self=is_self):
                    self.run_scenario(1, kind)

    def test_take_rejects_actor_mismatch(self) -> None:
        for side in range(2):
            for is_self in range(2):
                kind = side | (is_self << 1) | (9 << 2)
                with self.subTest(side=side, is_self=is_self):
                    self.run_scenario(2, kind)

    def test_capture_rejects_wrong_pc(self) -> None:
        for side in range(2):
            for is_self in range(2):
                kind = side | (is_self << 1) | (9 << 2)
                with self.subTest(side=side, is_self=is_self):
                    self.run_scenario(3, kind)


if __name__ == '__main__':
    unittest.main()
