"""BAG1 import scripts read host inputs through the shared configuration."""
import re, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "bag1import"))
sys.path.insert(0, str(ROOT))
import host_inputs
from tools.workflow import project_config as pc

MIGRATED = ("audit_animation_roles.py", "build_stage_package.py", "build_stage_previews.py",
            "fever_entries.py", "funcmatch.py", "generate_gaso_contract.py",
            "generate_strike_contract.py", "reqmap.py", "restore_heat_winner.py")
# A quoted _work segment, an f-string join or a parents[] walk to the machine Tools folder.
FIXED_PATH = re.compile(r"""["']_work[/\\"']|/_work/|parents\[1\]\s*/\s*["']Tools""")


class HostInputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "config").mkdir()

    def load(self, text):
        (self.root / "config" / "project.toml").write_text("schema_version=1\n" + text, encoding="utf-8")
        return pc.load_config(repo_root=self.root)

    def test_input_follows_its_key(self):
        config = self.load('[inputs]\nbag2_main_exe="relocated/slpm.bin"\n')
        self.assertEqual(host_inputs.input_path("inputs.bag2_main_exe", config=config),
                         (self.root / "relocated" / "slpm.bin").resolve())

    def test_missing_key_is_not_silently_defaulted(self):
        config = self.load("")
        for key in ("inputs.bag1_main_exe", "inputs.bag2_main_exe", "inputs.bag1_disc_files",
                    "inputs.character_inventory", "tools.psx_asset_tools"):
            with self.subTest(key=key), self.assertRaises(pc.ConfigError):
                host_inputs.input_path(key, config=config)

    def test_project_label_is_relative_inside_and_absolute_outside(self):
        inside = self.root / "_work" / "x.bin"
        self.assertEqual(host_inputs.project_label(inside, self.root), "_work/x.bin")
        outside = Path(tempfile.gettempdir()).resolve().parent / "elsewhere.bin"
        self.assertEqual(host_inputs.project_label(outside, self.root), outside.as_posix())

    def test_migrated_scripts_have_no_fixed_host_paths(self):
        for name in MIGRATED:
            text = (ROOT / "tools" / "bag1import" / name).read_text(encoding="utf-8")
            with self.subTest(script=name):
                self.assertEqual(FIXED_PATH.findall(text), [])


if __name__ == "__main__":
    unittest.main()
