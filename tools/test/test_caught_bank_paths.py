"""Host checks for the CAUGHT bank's declared clip sources."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import tools.workflow.project_config as pc

SPEC = importlib.util.spec_from_file_location(
    "build_caught_bank", Path(__file__).parents[1] / "bag1import/build_caught_bank.py")
caught = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(caught)

ROWS = [{"character": character, "source": "_work/bag1_disc_full/PLAYER2/P_%d.DFS" % character,
         "source_sha256": "0" * 64, "clip_bytes": 348, "clip_sha256": "0" * 64}
        for character in (0, 1, 9)]


class CaughtBankSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name, value in (("ROOT", self.root), ("CONTRACT", self.root / "contracts/caught-bank.json")):
            self.addCleanup(setattr, caught, name, getattr(caught, name))
            setattr(caught, name, value)
        self.contract({"clips": ROWS})
        self.configure('[paths]\nwork_root = "relocated_work"\n')

    def contract(self, payload):
        caught.CONTRACT.parent.mkdir(parents=True, exist_ok=True)
        caught.CONTRACT.write_text(json.dumps(payload), encoding="utf-8")

    def configure(self, text):
        directory = self.root / "config"
        directory.mkdir(exist_ok=True)
        (directory / "project.toml").write_text("schema_version = 1\n" + text, encoding="utf-8")

    def paths(self):
        return caught.source_paths(pc.load_config(repo_root=self.root))

    def test_declared_sources_follow_the_configured_work_root(self):
        resolved = self.paths()
        self.assertEqual([row["character"] for row, _path in resolved], [0, 1, 9])
        self.assertEqual(resolved[0][1],
                         (self.root / "relocated_work/bag1_disc_full/PLAYER2/P_0.DFS").resolve())
        self.assertFalse((self.root / "_work").exists())

    def test_default_work_root_is_unchanged(self):
        self.configure('[paths]\nwork_root = "_work"\n')
        self.assertEqual(self.paths()[1][1],
                         (self.root / "_work/bag1_disc_full/PLAYER2/P_1.DFS").resolve())

    def test_missing_work_root_is_a_configuration_error(self):
        self.configure("[harness]\nfps = 60\n")
        with self.assertRaises(pc.ConfigError):
            self.paths()

    def test_declared_sources_cannot_be_absolute_or_escape(self):
        for declared in (str(self.root / "elsewhere/P_0.DFS"), "_work/../P_0.DFS", "_work/.. /P_0.DFS"):
            with self.subTest(declared=declared):
                self.contract({"clips": [dict(ROWS[0], source=declared)]})
                with self.assertRaises(ValueError):
                    self.paths()

    def test_foreign_project_configuration_is_rejected(self):
        other = self.root / "other"
        (other / "config").mkdir(parents=True)
        (other / "config/project.toml").write_text(
            'schema_version = 1\n[paths]\nwork_root = "relocated_work"\n', encoding="utf-8")
        with self.assertRaises(pc.ConfigError):
            caught.source_paths(pc.load_config(repo_root=other))


if __name__ == "__main__":
    unittest.main()
