"""Exercise the exact HUD callback against original combat overlay bytes."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


def linux_path(path: Path) -> str:
    """Translate canonical Windows paths for the recorded WSL gcc harness."""
    return '/mnt/' + path.drive[0].lower() + path.as_posix()[2:]


class GasoHudRuntimeTest(unittest.TestCase):
    def test_sprite_callback_is_scoped_and_preserves_shared_state(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / '_work') as folder:
            binary = Path(folder) / 'hud'
            subprocess.run([
                'wsl.exe', '-d', 'Ubuntu', '--exec', 'gcc', '-std=c11',
                '-Wall', '-Wextra', '-Werror',
                '-I' + linux_path(ROOT / 'mods-src/bag2jp.feature.bag1-content'),
                linux_path(ROOT / 'tools/test/gaso_hud_harness.c'), '-o', linux_path(binary),
            ], check=True, capture_output=True, text=True)
            result = subprocess.run([
                'wsl.exe', '-d', 'Ubuntu', '--exec', linux_path(binary),
                linux_path(ROOT / 'assets/archive/system/005.dbi'),
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_load_latch_site_matches_original_executable(self) -> None:
        """The harness writes the latch fingerprints itself; check them against SLPM_862.19."""
        exe = (ROOT / 'assets/disc_files/SLPM_862.19').read_bytes()
        self.assertEqual(exe[:8], b'PS-X EXE')
        text = int.from_bytes(exe[0x18:0x1C], 'little')
        word = lambda address: int.from_bytes(exe[0x800 + address - text:][:4], 'little')
        self.assertEqual(word(0x8001F8A0), 0x3C028006)   # lui v0,0x8006
        self.assertEqual(word(0x8001F8A4), 0x8C900008)   # lw s0,0x8(a0)
        self.assertEqual(word(0x8001F8A8), 0x8C92000C)   # lw s2,0xc(a0)
        header = (ROOT / 'mods-src/bag2jp.feature.bag1-content/bag2jp_bag1_load_latch.h').read_text()
        for name, value in (('B1LOAD_SITE', '0x8001F8A4u'), ('B1LOAD_PREV_WORD', '0x3C028006u'),
                            ('B1LOAD_WORD', '0x8C900008u'), ('B1LOAD_NEXT_WORD', '0x8C92000Cu'),
                            ('B1LOAD_TABLE_PTR', '0x8005D410u'), ('B1LOAD_TABLE', '0x8005D418u')):
            self.assertRegex(header, rf'#define {name}\s+{value}')


if __name__ == '__main__':
    unittest.main()
