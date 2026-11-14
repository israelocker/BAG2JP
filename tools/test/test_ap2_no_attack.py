"""Exercise the 2P autoplay no-attack hook against original combat overlay bytes."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


def linux_path(path: Path) -> str:
    """Translate canonical Windows paths for the recorded WSL gcc harness."""
    return '/mnt/' + path.drive[0].lower() + path.as_posix()[2:]


class Ap2NoAttackTest(unittest.TestCase):
    def test_only_autoplayed_players_lose_the_attack_roll(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / '_work') as folder:
            binary = Path(folder) / 'ap2'
            subprocess.run([
                'wsl.exe', '-d', 'Ubuntu', '--exec', 'gcc', '-std=c11',
                '-Wall', '-Wextra', '-Werror',
                '-I' + linux_path(ROOT / 'mods-src/bag2jp.feature.autoplay'),
                linux_path(ROOT / 'tools/test/ap2_no_attack_harness.c'), '-o', linux_path(binary),
            ], check=True, capture_output=True, text=True)
            result = subprocess.run([
                'wsl.exe', '-d', 'Ubuntu', '--exec', linux_path(binary),
                linux_path(ROOT / 'assets/archive/system/005.dbi'),
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
