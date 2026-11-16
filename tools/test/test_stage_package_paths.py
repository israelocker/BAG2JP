"""Stage package locations resolve through the configured work root."""
import shutil, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "bag1import"))
sys.path.insert(0, str(ROOT))
import build_stage_package as builder
from tools.workflow import project_config as pc

PROFILE = {
    "stage_id": 1,
    "package": {
        "source": "_work/stage/disc/ST_STRI.DFS",
        "common": "_work/stage/disc/G_COMMON.DFS",
        "exe": "_work/stage/disc/SLPS_012.32",
        "stock": "assets/archive/stages/209_vault_factory",
        "model_entry": 5,
    },
}


class PackagePathTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "config").mkdir()
        self.work = self.root / "relocated_work"
        for name in ("ST_STRI.DFS", "G_COMMON.DFS", "SLPS_012.32"):
            (self.work / "stage" / "disc").mkdir(parents=True, exist_ok=True)
            (self.work / "stage" / "disc" / name).write_bytes(name.encode())
        (self.work / "mainexe").mkdir(parents=True)
        (self.work / "mainexe" / "slpm.bin").write_bytes(b"main exe")

    def configure(self, text):
        (self.root / "config" / "project.toml").write_text(text, encoding="utf-8")

    def test_relocated_work_root_resolves_package_inputs(self):
        self.configure('schema_version=1\n[paths]\nwork_root="relocated_work"\n')
        config = pc.load_config(repo_root=self.root)
        paths = builder.package_paths(self.root, PROFILE, config)
        self.assertEqual(paths["source"], (self.work / "stage" / "disc" / "ST_STRI.DFS").resolve())
        self.assertEqual(paths["common"].read_bytes(), b"G_COMMON.DFS")
        self.assertEqual(paths["exe"].name, "SLPS_012.32")
        self.assertEqual(paths["stock"], (self.root / "assets" / "archive" / "stages" / "209_vault_factory").resolve())
        self.assertEqual(builder.main_exe_path(self.root, config), (self.work / "mainexe" / "slpm.bin").resolve())
        self.assertFalse((self.root / "_work").exists())

    def test_default_work_root_matches_project_relative_bytes(self):
        (self.root / "_work" / "stage" / "disc").mkdir(parents=True)
        shutil.copytree(self.work / "stage" / "disc", self.root / "_work" / "stage" / "disc",
                        dirs_exist_ok=True)
        (self.root / "_work" / "mainexe").mkdir()
        shutil.copyfile(self.work / "mainexe" / "slpm.bin", self.root / "_work" / "mainexe" / "slpm.bin")
        self.configure('schema_version=1\n[paths]\nwork_root="_work"\n')
        config = pc.load_config(repo_root=self.root)
        paths = builder.package_paths(self.root, PROFILE, config)
        self.assertEqual(paths["source"], (self.root / "_work" / "stage" / "disc" / "ST_STRI.DFS").resolve())
        self.assertEqual(builder.main_exe_path(self.root, config),
                         (self.root / "_work" / "mainexe" / "slpm.bin").resolve())

    def test_missing_work_root_is_not_silently_defaulted(self):
        self.configure("schema_version=1\n")
        config = pc.load_config(repo_root=self.root)
        with self.assertRaises(pc.ConfigError):
            builder.package_paths(self.root, PROFILE, config)

    def test_package_input_cannot_be_absolute_or_escape(self):
        self.configure('schema_version=1\n[paths]\nwork_root="relocated_work"\n')
        config = pc.load_config(repo_root=self.root)
        for declared in ("C:/elsewhere/ST_STRI.DFS", "_work/../ST_STRI.DFS", "_work/.. /ST_STRI.DFS"):
            with self.subTest(declared=declared):
                profile = {"stage_id": 1, "package": dict(PROFILE["package"], source=declared)}
                with self.assertRaisesRegex(ValueError, "project-relative|escape the project"):
                    builder.package_paths(self.root, profile, config)

    def test_build_requires_a_configuration_snapshot(self):
        with self.assertRaises(pc.ConfigError):
            builder.build_from_project(self.root, "missing-profile-without-config")


if __name__ == "__main__":
    unittest.main()
