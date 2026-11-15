"""Relocated host workspaces; no package builder, installed tools or game."""
import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from tools.test import test_character_workflow as fixtures
from tools.workflow import project_config as pc
from tools.workflow.test_project_config import _make_directory_alias, working_directory


class WorkspaceConfigTests(unittest.TestCase):
    save_profile = fixtures.CharacterPlanTests.save_profile

    def setUp(self):
        fixtures.CharacterPlanTests.setUp(self)
        (self.root / "config").mkdir()
        source = Path(__file__).resolve().parents[2] / "config/project.toml"
        (self.root / "config/project.toml").write_bytes(source.read_bytes())
        self.local = self.root / "config/project.local.toml"
        self.local.write_text('[paths]\nwork_root="evidence ñ &"\nstable_install="stable"\n', encoding="utf-8")

    def workspace(self):
        return self.root / "evidence ñ &/character-import/alpha"

    def test_prepare_and_state_use_selected_config_without_changing_inputs(self):
        # Use the CLI so an unmodified implementation goes red on the observable destination.
        source = Path(fixtures.workflow.__file__)
        inputs = {p: p.read_bytes() for p in self.root.iterdir() if p.is_file()}
        self.local.write_text('[paths]\nwork_root="wrong-default"\nstable_install="stable"\n')
        overlay = self.root / "selected.toml"
        overlay.write_text('[paths]\nwork_root="evidence ñ &"\nstable_install="stable"\n', encoding="utf-8")
        result = subprocess.run([sys.executable, str(source), "prepare", "--project", str(self.root),
            "--profile", str(self.profile), "--local-config", str(overlay)], cwd=self.root.parent,
            capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        manifest = self.workspace() / "candidate/manifest.json"
        state = self.workspace() / "state.json"
        self.assertTrue(manifest.is_file()); self.assertTrue(state.is_file())
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertFalse(data["deployed"])
        self.assertEqual(data["profile_sha256"], fixtures.workflow.file_sha(self.profile))
        self.assertEqual(data["assets"], self.data["assets"])
        config = data.get("configuration", {})
        self.assertEqual(config.get("origins", {}).get("paths.work_root"), "local")
        self.assertEqual(config.get("files", {}).get("local"), str(overlay))
        self.assertEqual(config.get("values", {}).get("paths.work_root"), str(self.root / "evidence ñ &"))
        self.assertEqual(config.get("config", {}).get("local"), hashlib.sha256(overlay.read_bytes()).hexdigest())
        self.assertEqual(config.get("config", {}).get("common"), hashlib.sha256((self.root / "config/project.toml").read_bytes()).hexdigest())
        self.assertEqual(json.loads(state.read_text())["configuration"], config)
        self.assertFalse((self.root / "_work").exists())
        self.assertFalse((self.root / "wrong-default").exists())
        self.assertTrue(all(p.read_bytes() == raw for p, raw in inputs.items()))

    def test_read_only_actions_need_no_machine_configuration(self):
        self.local.unlink()
        (self.root / "config/project.toml").unlink()
        self.assertTrue(fixtures.workflow.character_plan(self.profile, self.root)["prepare_ready"])
        source = Path(fixtures.workflow.__file__)
        for action in ("status", "acceptance-plan", "validate-profile"):
            result = subprocess.run([sys.executable, str(source), action, "--project", str(self.root),
                "--profile", str(self.profile)], capture_output=True, timeout=20)
            with self.subTest(action=action):
                self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        self.assertFalse(self.workspace().exists())

    def test_missing_stable_fails_before_mkdir(self):
        self.local.write_text('[paths]\nwork_root="evidence"\n')
        with self.assertRaises(pc.ConfigError):
            fixtures.workflow.prepare_workspace(self.profile, self.root)
        self.assertFalse((self.root / "evidence").exists())

    def test_snapshot_is_independent_of_later_overlay_edits_and_cwd(self):
        config = pc.load_config(repo_root=self.root)
        original_hash = hashlib.sha256(self.local.read_bytes()).hexdigest()
        self.local.write_text('[paths]\nwork_root="later"\nstable_install="stable"\n')
        with working_directory(self.root.parent):
            result = fixtures.workflow.prepare_workspace(self.profile, self.root, config=config)
        self.assertEqual(Path(result["manifest"]), self.workspace() / "candidate/manifest.json")
        self.assertFalse((self.root / "later").exists())
        data = json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))
        self.assertEqual(data["configuration"]["values"]["paths.work_root"], str(self.root / "evidence ñ &"))
        self.assertEqual(data["configuration"]["config"]["local"], original_hash)

    def test_stable_alias_is_rejected_before_any_write(self):
        stable = self.root / "stable"; stable.mkdir()
        alias = self.root / "evidence ñ &"
        self.assertTrue(_make_directory_alias(alias, stable))
        with self.assertRaises(pc.ConfigError):
            fixtures.workflow.prepare_workspace(self.profile, self.root)
        self.assertEqual(list(stable.iterdir()), [])

    def test_existing_manifest_directories_and_hardlinks_are_rejected(self):
        manifest = self.workspace() / "candidate/manifest.json"; manifest.mkdir(parents=True)
        with patch.object(fixtures.workflow, "_atomic_write_json", side_effect=AssertionError("must reject before writer")), self.assertRaises(pc.ConfigError):
            fixtures.workflow.prepare_workspace(self.profile, self.root)
        manifest.rmdir()
        protected = self.root / "protected"; protected.write_bytes(b"owner")
        os.link(protected, manifest)
        with self.assertRaises(pc.ConfigError):
            fixtures.workflow.prepare_workspace(self.profile, self.root)
        self.assertEqual(protected.read_bytes(), b"owner")

    def test_direct_state_rejects_slug_escape_before_writes(self):
        plan = fixtures.workflow.character_plan(self.profile, self.root)
        for character in ("../../escape", "Invalid Slug", ""):
            plan["character"] = character
            with self.subTest(character=character), self.assertRaises(pc.ConfigError):
                fixtures.workflow.write_state(self.root, plan)
        self.assertFalse((self.root / "evidence ñ &").exists())

    def test_cli_checks_state_before_creating_candidate(self):
        state = self.workspace() / "state.json"; state.mkdir(parents=True)
        source = Path(fixtures.workflow.__file__)
        result = subprocess.run([sys.executable, str(source), "prepare", "--project", str(self.root),
            "--profile", str(self.profile)], capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.workspace() / "candidate").exists())

    def test_supplied_config_cannot_select_a_different_project(self):
        config = pc.load_config(repo_root=self.root)
        plan = fixtures.workflow.character_plan(self.profile, self.root)
        with self.assertRaises(pc.ConfigError):
            fixtures.workflow.write_state(self.root.parent, plan, config=config)
        self.assertFalse(self.workspace().exists())

    def test_prepare_cannot_overwrite_an_asset_at_the_manifest_destination(self):
        manifest = self.workspace() / "candidate/manifest.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_bytes(b"protected asset")
        self.data["assets"]["collision"] = {"file":str(manifest.relative_to(self.root)),
                                            "sha256":fixtures.workflow.file_sha(manifest)}
        self.save_profile()
        with self.assertRaises(pc.ConfigError):
            fixtures.workflow.prepare_workspace(self.profile, self.root)
        self.assertEqual(manifest.read_bytes(), b"protected asset")

    def test_direct_state_preserves_explicitly_protected_inputs(self):
        state = self.workspace() / "state.json"; state.parent.mkdir(parents=True)
        state.write_bytes(b"protected input")
        plan = fixtures.workflow.character_plan(self.profile, self.root)
        with self.assertRaises(pc.ConfigError):
            fixtures.workflow.write_state(self.root, plan, protected_inputs=(state,))
        self.assertEqual(state.read_bytes(), b"protected input")

    def test_cli_rejects_coincident_physical_outputs_before_any_write(self):
        state = self.workspace() / "state.json"; state.parent.mkdir(parents=True)
        state.write_bytes(b"existing state")
        manifest = self.workspace() / "candidate/manifest.json"; manifest.parent.mkdir()
        try:
            os.symlink(state, manifest)
        except OSError as error:
            if getattr(error, "winerror", None) == 1314:
                self.skipTest("File symlink privilege unavailable; assembly collision tested separately")
            raise
        source = Path(fixtures.workflow.__file__)
        result = subprocess.run([sys.executable, str(source), "prepare", "--project", str(self.root),
            "--profile", str(self.profile)], capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(state.read_bytes(), b"existing state")
        self.assertTrue(manifest.is_symlink())

    def test_workspace_output_cannot_overwrite_the_selected_configuration(self):
        state = self.workspace() / "state.json"; state.parent.mkdir(parents=True)
        raw = self.local.read_bytes(); state.write_bytes(raw)
        config = pc.load_config(repo_root=self.root, local_config=state)
        plan = fixtures.workflow.character_plan(self.profile, self.root)
        with self.assertRaises(pc.ConfigError):
            fixtures.workflow.write_state(self.root, plan, config=config)
        self.assertEqual(state.read_bytes(), raw)

    def test_cli_compares_both_resolved_output_paths_before_writers(self):
        state = self.workspace() / "state.json"; state.parent.mkdir(parents=True)
        state.write_bytes(b"existing state")
        real_target = fixtures.workflow._workspace_file

        def resolved_target(*args, **kwargs):
            path = real_target(*args, **kwargs)
            return state if path.name == "manifest.json" else path

        with patch.object(fixtures.workflow, "_workspace_file", side_effect=resolved_target), \
                patch.object(fixtures.workflow, "_atomic_write_json", side_effect=AssertionError("before writer")):
            with self.assertRaises(SystemExit) as result:
                fixtures.workflow.main(["prepare", "--project", str(self.root), "--profile", str(self.profile)])
        self.assertEqual(result.exception.code, 2)
        self.assertEqual(state.read_bytes(), b"existing state")
