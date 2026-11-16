"""Drive-letter configuration values resolve under the configured WSL mount root on POSIX hosts."""
import sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.workflow import project_config as pc


class DriveTranslationTests(unittest.TestCase):
    def test_posix_host_maps_drive_letters_under_mount_root(self):
        self.assertEqual(pc._translate_drive("D:/Games/a b/x.cue", "/mnt", posix=True), "/mnt/d/Games/a b/x.cue")
        self.assertEqual(pc._translate_drive("C:\\Tools\\y", "/srv/m/", posix=True), "/srv/m/c/Tools/y")

    def test_windows_host_and_relative_values_are_unchanged(self):
        self.assertEqual(pc._translate_drive("D:/Games/x.cue", "/mnt", posix=False), "D:/Games/x.cue")
        self.assertEqual(pc._translate_drive("_work/x", "/mnt", posix=True), "_work/x")

    def test_posix_without_mount_root_rejects_drive_paths(self):
        with self.assertRaises(pc.ConfigError):
            pc._translate_drive("D:/Games/x.cue", None, posix=True)

    def test_mount_root_is_a_registered_key(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "config").mkdir()
            (root / "config" / "project.toml").write_text('schema_version=1\n[wsl]\nmount_root="/mnt"\n')
            self.assertEqual(pc.load_config(repo_root=root).values["wsl.mount_root"], "/mnt")


if __name__ == "__main__":
    unittest.main()
