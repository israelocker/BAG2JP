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

    def test_real_attack_spawn_anchors_base_at_floor_not_pelvis(self) -> None:
        self.run_scenario(5)


if __name__ == '__main__':
    unittest.main()
