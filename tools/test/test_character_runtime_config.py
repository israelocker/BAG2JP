"""Central runtime authority at the public profile/cache/CLI seams."""
import hashlib
import json
import contextlib
import io
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.test import test_character_workflow as fixtures
from tools.workflow import project_config as pc


class RuntimeConfigTests(fixtures.ReferenceCacheTests):
    def setUp(self):
        super().setUp()
        self.config_dir = self.root / "config"
        self.config_dir.mkdir(exist_ok=True)
        self.common = self.config_dir / "project.toml"
        self.runtime = self.root / "runtime ñ &.bin"
        self.runtime.write_bytes(b"configured runtime")
        self.common.write_text('schema_version=1\n[inputs]\nbag1_reference_runtime="runtime ñ &.bin"\n', encoding="utf-8")

    def test_relocated_characters_use_central_bytes_not_historical_field(self):
        for name in ("heat", "strike", "gaso"):
            with self.subTest(character=name):
                self.data.update(character=name, source_region="usa", target_region="jp")
                self.save_profile()
                key = fixtures.workflow.signature(self.profile, self.root)
                self.assertEqual(key["runtime_sha256"], hashlib.sha256(b"configured runtime").hexdigest())
                self.assertEqual(key["character"], name)
                self.assertEqual(json.loads(self.profile.read_text())["source_region"], "usa")

    def test_equivalent_relocation_hits_but_changed_runtime_bytes_miss(self):
        self.record()
        other = self.root / "relocated.bin"
        other.write_bytes(self.runtime.read_bytes())
        self.common.write_text('schema_version=1\n[inputs]\nbag1_reference_runtime="relocated.bin"\n')
        self.assertEqual(self.check(), "hit")
        other.write_bytes(b"changed runtime")
        self.assertEqual(self.check(), "miss")

    def test_missing_runtime_authority_never_falls_back(self):
        self.common.write_text("schema_version=1\n")
        with self.assertRaises(pc.ConfigError):
            fixtures.workflow.signature(self.profile, self.root)
        self.assertFalse(self.cache.exists())

    def test_historical_runtime_is_optional_and_not_validated(self):
        del self.data["reference_runtime"]
        self.save_profile()
        try:
            profile, _ = fixtures.workflow.load_profile(self.profile, self.root)
        except ValueError as error:
            self.fail(f"Historical runtime is not an operative input: {error}")
        self.assertEqual(profile["character"], "alpha")

    def test_record_resolves_one_snapshot_and_protects_runtime(self):
        real = fixtures.workflow.load_config
        with patch.object(fixtures.workflow, "load_config", wraps=real) as resolver:
            self.record()
        self.assertEqual(resolver.call_count, 1)
        before = self.runtime.read_bytes()
        with self.assertRaises(ValueError):
            fixtures.workflow.record_cache(self.profile, self.root, self.runtime, [self.root / "video.bin"])
        self.assertEqual(self.runtime.read_bytes(), before)

    def test_cli_all_readers_select_overlay_once(self):
        selected = self.root / "selected.toml"
        selected.write_text('[inputs]\nbag1_reference_runtime="runtime.bin"\n[paths]\nwork_root="work"\nstable_install="stable"\n')
        for action in ("validate-profile", "status", "acceptance-plan", "plan", "cache-record", "cache-check"):
            with self.subTest(action=action):
                real = fixtures.workflow.load_config
                with patch.object(fixtures.workflow, "load_config", wraps=real) as resolver, contextlib.redirect_stdout(io.StringIO()) as output:
                    result = fixtures.workflow.main([action, "--project", str(self.root), "--profile", str(self.profile),
                        "--local-config", str(selected), "--cache", str(self.cache), "--evidence", str(self.root / "video.bin")])
                self.assertEqual(result, 0)
                self.assertEqual(resolver.call_count, 1)
                if action == "cache-record":
                    self.assertEqual(json.loads(output.getvalue())["runtime_sha256"], hashlib.sha256(b"runtime").hexdigest())

    def test_missing_runtime_file_rejected_before_cache_write(self):
        self.runtime.unlink()
        with self.assertRaises(pc.ConfigError):
            self.record()
        self.assertFalse(self.cache.exists())

    def test_cache_rejects_runtime_hardlink(self):
        os.link(self.runtime, self.cache)
        with self.assertRaisesRegex(ValueError, "overwrite an input"):
            self.record()
        self.assertEqual(self.runtime.read_bytes(), b"configured runtime")

    def test_supplied_snapshot_survives_overlay_edits_and_rejects_wrong_root(self):
        config = pc.load_config(repo_root=self.root)
        self.common.write_text("schema_version=1\n")
        key = fixtures.workflow.signature(self.profile, self.root, config=config)
        self.assertEqual(key["runtime_sha256"], hashlib.sha256(b"configured runtime").hexdigest())
        with self.assertRaises(pc.ConfigError):
            fixtures.workflow.signature(self.profile, self.root.parent, config=config)

    # The inherited runtime-change check refers to the historical fixture path.
    def test_runtime_change_invalidates(self):
        self.record()
        self.runtime.write_bytes(b"changed")
        self.assertEqual(self.check(), "miss")


if __name__ == "__main__":
    unittest.main()
