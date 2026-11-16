"""Animation policy input evidence resolves through the configured work root."""
import json, os, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "bag1import"))
sys.path.insert(0, str(ROOT))
import animation_policy
from tools.workflow import project_config as pc
from character_workflow import file_sha as sha


class PolicyInputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.work = self.root / "relocated_work"
        self.work.mkdir(parents=True)
        (self.work / "rom.bin").write_bytes(b"base game")
        (self.root / "config").mkdir()

    def configure(self, text):
        (self.root / "config" / "project.toml").write_text(text, encoding="utf-8")

    def write_policy(self, name="_work/rom.bin", digest=None):
        policy = {
            "schema": 1,
            "character": "alpha",
            "roles": [{"target": 0, "source": 0, "classification": "equivalent",
                       "reason": "same clip"}],
            "input_evidence": [{"file": name,
                                "sha256": digest or sha(self.work / "rom.bin")}],
        }
        path = self.root / "policy.json"
        path.write_text(json.dumps(policy), encoding="utf-8")
        return path

    def test_relocated_work_root_validates_policy_inputs(self):
        self.configure('schema_version=1\n[paths]\nwork_root="relocated_work"\n')
        policy = animation_policy.load_policy(self.write_policy(), self.root)
        self.assertEqual(policy["character"], "alpha")
        self.assertFalse((self.root / "_work").exists())

    def test_default_work_root_matches_project_relative_bytes(self):
        (self.root / "_work").mkdir()
        # Distinct bytes prove the declared `_work` location wins, not the relocated copy.
        (self.root / "_work" / "rom.bin").write_bytes(b"default work tree")
        self.configure('schema_version=1\n[paths]\nwork_root="_work"\n')
        policy = animation_policy.load_policy(
            self.write_policy(digest=sha(self.root / "_work" / "rom.bin")), self.root)
        self.assertEqual(policy["roles"][0]["target"], 0)
        self.assertNotEqual(sha(self.root / "_work" / "rom.bin"), sha(self.work / "rom.bin"))

    def test_changed_policy_input_is_rejected(self):
        self.configure('schema_version=1\n[paths]\nwork_root="relocated_work"\n')
        policy = self.write_policy(digest="0" * 64)
        with self.assertRaisesRegex(ValueError, "Animation policy input changed"):
            animation_policy.load_policy(policy, self.root)

    def test_missing_work_root_is_not_silently_defaulted(self):
        self.configure("schema_version=1\n")
        with self.assertRaises(pc.ConfigError):
            animation_policy.load_policy(self.write_policy(), self.root)

    def test_policy_input_cannot_be_absolute_or_escape(self):
        self.configure('schema_version=1\n[paths]\nwork_root="relocated_work"\n')
        for declared in (str(self.root / "rom.bin"), "_work/../rom.bin", "_work/.. /rom.bin"):
            with self.subTest(declared=declared):
                with self.assertRaisesRegex(ValueError, "project-relative|escape the project"):
                    animation_policy.load_policy(self.write_policy(name=declared), self.root)

    def test_policy_input_cannot_escape_through_a_link(self):
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(outside, ignore_errors=True))
        (outside / "rom.bin").write_bytes(b"base game")
        link = self.work / "linked"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError:
            if os.name != "nt":
                self.skipTest("symlink privilege unavailable")
            result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)],
                                    capture_output=True, text=True)
            if result.returncode != 0:
                self.skipTest(f"directory link unavailable: {result.stderr.strip()}")
        self.configure('schema_version=1\n[paths]\nwork_root="relocated_work"\n')
        with self.assertRaisesRegex(ValueError, "escape the project"):
            animation_policy.load_policy(self.write_policy(name="_work/linked/rom.bin"), self.root)

    def test_policy_evidence_is_never_silently_skipped(self):
        policy = self.write_policy()
        with self.assertRaisesRegex(ValueError, "requires a project"):
            animation_policy.load_policy(policy)
        config = pc.load_config(repo_root=ROOT)
        with self.assertRaisesRegex(ValueError, "requires the project"):
            animation_policy.load_policy(policy, config=config)
        self.configure('schema_version=1\n[paths]\nwork_root="relocated_work"\n')
        no_evidence = self.write_policy()
        document = json.loads(no_evidence.read_text(encoding="utf-8"))
        document["input_evidence"] = []
        no_evidence.write_text(json.dumps(document), encoding="utf-8")
        self.assertEqual(animation_policy.load_policy(no_evidence)["schema"], 1)

    def test_explicit_config_is_reused_without_reload(self):
        self.configure('schema_version=1\n[paths]\nwork_root="relocated_work"\n')
        config = pc.load_config(repo_root=self.root)
        shutil.rmtree(self.root / "config")
        policy = animation_policy.load_policy(self.write_policy(), self.root, config=config)
        self.assertEqual(policy["schema"], 1)


if __name__ == "__main__":
    unittest.main()
