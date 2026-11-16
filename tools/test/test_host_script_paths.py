"""Host test/workflow scripts take work locations and redaction roots from configuration."""
import re, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.workflow import project_config as pc

SCRIPTS = ("tools/test/accept_versus_calibration.py", "tools/test/discover_strike_id.py",
           "tools/test/discover_strike_id_p1.py", "tools/test/preview_endings_label.py",
           "tools/workflow/audit_docs.py", "tools/workflow/measure_context.py",
           "tools/workflow/token-report.py", "tools/workflow/generate_digests.py")
FIXED_PATH = re.compile(r"""["']_work[/\\"']|[A-Za-z]:\\\\|["'][A-Za-z]:[/\\]|C:\\\\Users|israe""")


class HostScriptPathTests(unittest.TestCase):
    def test_scripts_have_no_fixed_locations(self):
        for rel in SCRIPTS:
            with self.subTest(script=rel):
                self.assertEqual(FIXED_PATH.findall((ROOT / rel).read_text(encoding="utf-8")), [])

    def test_mods_src_tools_have_no_machine_or_home_locations(self):
        home = re.compile(r"""expanduser|['"]~/|/mnt/|["'][A-Za-z]:[/\\]|\{HOME\}""")
        for path in sorted((ROOT / "mods-src").glob("*/tools/**/*.py")):
            with self.subTest(script=path.relative_to(ROOT).as_posix()):
                self.assertEqual(home.findall(path.read_text(encoding="utf-8")), [])

    def test_current_state_follows_its_key(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "config").mkdir()
            (root / "config" / "project.toml").write_text(
                'schema_version=1\n[paths]\ncurrent_state="elsewhere/state.json"\n', encoding="utf-8")
            config = pc.load_config(repo_root=root)
            self.assertEqual(pc.require_paths(config, ("paths.current_state",))[0],
                             (root / "elsewhere" / "state.json").resolve())


if __name__ == "__main__":
    unittest.main()
