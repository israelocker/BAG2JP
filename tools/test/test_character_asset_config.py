"""Declared catalog/asset locations resolve through the configured host work root."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.test import test_character_workflow as fixtures
from tools.workflow import project_config as pc


workflow = fixtures.workflow


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class DeclaredInputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "config").mkdir()
        (self.root / "runtime.bin").write_bytes(b"runtime")
        (self.root / "outside.bin").write_bytes(b"outside")
        self.work = self.root / "relocated_work"
        self.work.mkdir()
        (self.work / "source.bin").write_bytes(fixtures.animation())
        (self.work / "model.bin").write_bytes(b"model bytes")
        (self.work / "rom.bin").write_bytes(b"base game")
        self.catalog = {"schema": 1, "games": {"game": {"inputs": [
            {"file": "_work/rom.bin", "sha256": sha(self.work / "rom.bin")}]}}}
        (self.work / "catalog.json").write_text(json.dumps(self.catalog))
        self.profile = self.root / "profile.json"
        self.data = {"schema": 1, "character": "alpha", "stage": "inventory",
                     "source_animation_list": "_work/source.bin",
                     "game_catalog": "_work/catalog.json", "exceptions": []}
        self.save_profile()
        self.configure('schema_version=1\n[paths]\nwork_root="relocated_work"\n'
                       '[inputs]\nbag1_reference_runtime="runtime.bin"\n')

    def configure(self, text):
        (self.root / "config" / "project.toml").write_text(text, encoding="utf-8")

    def save_profile(self):
        self.profile.write_text(json.dumps(self.data))

    def test_relocated_work_root_resolves_declared_inputs(self):
        profile, pending = workflow.load_profile(self.profile, self.root)
        self.assertEqual(profile["character"], "alpha")
        self.assertEqual(pending, [])
        key = workflow.signature(self.profile, self.root)
        self.assertEqual(key["catalog_sha256"], sha(self.work / "catalog.json"))
        self.assertEqual(key["animation_count"], 1)

    def test_catalog_input_resolves_through_work_root(self):
        (self.work / "rom.bin").write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "Game catalog input changed"):
            workflow.load_profile(self.profile, self.root)

    def test_asset_file_resolves_through_work_root(self):
        self.data.update(schema=2, display_name="Alpha", capabilities={},
                         assets={"model": {"file": "_work/model.bin",
                                           "sha256": sha(self.work / "model.bin")}})
        self.save_profile()
        workflow.load_profile(self.profile, self.root)
        (self.work / "model.bin").write_bytes(b"other model")
        with self.assertRaisesRegex(ValueError, "Asset input changed"):
            workflow.load_profile(self.profile, self.root)

    def test_declared_input_cannot_be_absolute(self):
        self.data["source_animation_list"] = str(self.root / "outside.bin")
        self.save_profile()
        with self.assertRaisesRegex(ValueError, "project-relative"):
            workflow.load_profile(self.profile, self.root)

    def test_declared_input_cannot_escape_the_project(self):
        self.data["game_catalog"] = "_work/../outside.bin"
        self.save_profile()
        with self.assertRaisesRegex(ValueError, "escape the project"):
            workflow.load_profile(self.profile, self.root)

    def test_missing_work_root_is_not_silently_defaulted(self):
        self.configure('schema_version=1\n[inputs]\nbag1_reference_runtime="runtime.bin"\n')
        with self.assertRaises(pc.ConfigError):
            workflow.load_profile(self.profile, self.root)

    def test_cache_protects_relocated_declared_inputs(self):
        cache = self.root / "cache.json"
        workflow.record_cache(self.profile, self.root, cache, [self.root / "runtime.bin"])
        self.assertEqual(workflow.check_cache(self.profile, self.root, cache)["status"], "hit")
        before = (self.work / "source.bin").read_bytes()
        with self.assertRaisesRegex(ValueError, "overwrite an input"):
            workflow.record_cache(self.profile, self.root, self.work / "source.bin",
                                  [self.root / "runtime.bin"])
        self.assertEqual((self.work / "source.bin").read_bytes(), before)

    def test_validate_profile_cli_uses_work_root(self):
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()) as output:
            code = workflow.main(["validate-profile", "--project", str(self.root),
                                  "--profile", str(self.profile)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.getvalue())["animation_count"], 1)

    def test_default_work_root_matches_project_relative_bytes(self):
        (self.root / "_work").mkdir()
        (self.root / "_work" / "catalog.json").write_bytes((self.work / "catalog.json").read_bytes())
        (self.root / "_work" / "source.bin").write_bytes((self.work / "source.bin").read_bytes())
        (self.root / "_work" / "rom.bin").write_bytes((self.work / "rom.bin").read_bytes())
        self.configure('schema_version=1\n[paths]\nwork_root="_work"\n'
                       '[inputs]\nbag1_reference_runtime="runtime.bin"\n')
        key = workflow.signature(self.profile, self.root)
        self.assertEqual(key["catalog_sha256"], sha(self.root / "_work" / "catalog.json"))

    def test_uppercase_work_component_follows_platform_case_rules(self):
        if os.name != "nt":
            self.skipTest("case-insensitive work root applies to Windows only")
        self.data["source_animation_list"] = "_WORK/source.bin"
        self.save_profile()
        try:
            workflow.load_profile(self.profile, self.root)
        except ValueError as error:
            self.fail(f"uppercase _WORK must follow platform case rules: {error}")

    def test_trailing_dot_or_space_component_is_rejected(self):
        for declared in ("_work/.. /source.bin", "_work/.../source.bin"):
            self.data["source_animation_list"] = declared
            self.save_profile()
            with self.assertRaisesRegex(ValueError, "escape the project"):
                workflow.load_profile(self.profile, self.root)

    def test_declared_input_cannot_escape_through_a_link(self):
        outside_temp = tempfile.TemporaryDirectory()
        self.addCleanup(outside_temp.cleanup)
        outside = Path(outside_temp.name)
        (outside / "source.bin").write_bytes(fixtures.animation())
        link = self.root / "linked_work"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError):
            created = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(link), str(outside)],
                capture_output=True, text=True)
            if created.returncode != 0 or not link.exists():
                self.skipTest(f"link creation unavailable: {created.stderr.strip()}")
        self.data["source_animation_list"] = "linked_work/source.bin"
        self.save_profile()
        with self.assertRaisesRegex(ValueError, "escape the project"):
            workflow.load_profile(self.profile, self.root)

    def test_workspace_inputs_reports_controlled_error_for_unvalidated_evidence(self):
        self.data["validation_evidence"] = [{"sha256": "0" * 64}]
        self.save_profile()
        profile, _ = workflow.load_profile(self.profile, self.root)
        config = pc.load_config(repo_root=self.root)
        with self.assertRaises(ValueError):
            workflow._workspace_inputs(self.profile, self.root, profile, config)


if __name__ == "__main__":
    unittest.main()
