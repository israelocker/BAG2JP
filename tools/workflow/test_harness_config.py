"""Prepare typed harness settings without running or modifying the game harness."""

import json
from pathlib import Path
import tomllib
import unittest

from tools.workflow import project_config as config
from tools.workflow.test_project_config import ConfigFixture


REPO = Path(__file__).resolve().parents[2]
TIMEOUTS = {
    "state_timeout_seconds": 25.0,
    "helper_timeout_seconds": 35.0,
    "startup_timeout_seconds": 40.0,
    "finish_timeout_seconds": 420.0,
}
LOCKED_INPUT = {"key_hold_ms": 100, "key_gap_ms": 350, "menu_fade_seconds": 1.3}
BUDGET_ERROR = "expected a positive finite number up to 86400"


class HarnessConfigurationTests(ConfigFixture):
    def assert_registered(self):
        expected = {f"harness.{name}" for name in TIMEOUTS | LOCKED_INPUT}
        self.assertFalse(expected - set(config.FIELDS), "harness settings must be registered first")

    def test_common_defaults_preserve_observed_harness_values(self):
        self.assert_registered()
        self.common.write_bytes((REPO / "config/project.toml").read_bytes())
        resolved = self.load()
        for name, expected in (TIMEOUTS | LOCKED_INPUT).items():
            with self.subTest(name=name):
                self.assertEqual(resolved.values[f"harness.{name}"], expected)
                self.assertEqual(resolved.origins[f"harness.{name}"], "common")

    def test_positive_finite_deadline_overrides_remain_json_numbers(self):
        self.assert_registered()
        for literal, expected in (("0.25", 0.25), ("12", 12), ("50.5", 50.5), ("86400", 86400)):
            self.write_local(f"[harness]\nstate_timeout_seconds = {literal}\n")
            resolved = self.load()
            exported = json.loads(json.dumps(config.export_config(resolved, operation="inspect"), allow_nan=False))
            self.assertEqual(exported["values"]["harness.state_timeout_seconds"], expected)
            self.assertEqual(resolved.origins["harness.state_timeout_seconds"], "local")

    def test_all_deadline_fields_reject_nonpositive_bool_text_and_nonfinite(self):
        self.assert_registered()
        for name in TIMEOUTS:
            for literal in ('true', '"25"', '0', '-1', 'nan', 'inf', '-inf', '86400.5', '1e300',
                            str(10 ** 300), str(10 ** 400)):
                self.write_local(f"[harness]\n{name} = {literal}\n")
                with self.subTest(name=name, literal=literal[:16]):
                    # The value rule, not a disabled local override, must be the cause.
                    self.assert_config_error(f"harness\\.{name}: {BUDGET_ERROR}")

    def test_locked_input_policy_cannot_be_overridden_locally(self):
        self.assert_registered()
        for name, value in LOCKED_INPUT.items():
            self.write_local(f"[harness]\n{name} = {value}\n")
            self.assert_config_error(f"harness\\.{name}: local policy override is forbidden")

    def test_locked_input_policy_has_exact_common_values(self):
        self.assert_registered()
        base = self.common.read_text(encoding="utf-8")
        wrong = {"key_hold_ms": ("101", "100.0", "true", '"100"'),
                 "key_gap_ms": ("351", "350.0", '"350"'),
                 "menu_fade_seconds": ("1.31", "2.3", '"1.3"', "true")}
        for name, value in LOCKED_INPUT.items():
            self.common.write_text(base + f"\n[harness]\n{name} = {value}\n", encoding="utf-8")
            self.assertEqual(self.load().values[f"harness.{name}"], value)
            for literal in wrong[name]:
                self.common.write_text(base + f"\n[harness]\n{name} = {literal}\n", encoding="utf-8")
                with self.subTest(name=name, literal=literal):
                    self.assert_config_error(f"harness\\.{name}: expected")

    def test_versus_session_operation_claims_every_migrated_harness_value(self):
        # S3a migrated versus_session.py; only the session operation consumes the policy values.
        self.assert_registered()
        for name in TIMEOUTS | LOCKED_INPUT:
            expected = ("versus-inspect", "versus-session") if name == "helper_timeout_seconds" \
                else ("versus-session",)
            with self.subTest(name=name):
                self.assertEqual(config.FIELDS[f"harness.{name}"].operations, expected)
        session = set(config.export_config(self.load(), operation="versus-session")["missing"])
        self.assertTrue({"paths.experimental_install", "paths.stable_install",
                         "tools.winshot_root"} <= session)
        self.assertNotIn("paths.work_root", session)

    def test_versus_inspect_requires_only_identity_keys(self):
        self.write_local('[paths]\nexperimental_install = "game"\nstable_install = "stable"\n')
        self.common.write_bytes((REPO / "config/project.toml").read_bytes())
        exported = config.export_config(self.load(), operation="versus-inspect")
        self.assertEqual(exported["missing"], [])
        required = {key for key, spec in config.FIELDS.items() if "versus-inspect" in spec.operations}
        self.assertEqual(required, {"repo_root", "paths.experimental_install", "paths.stable_install",
                                    "harness.helper_timeout_seconds"})

    def test_require_values_returns_any_kind_in_order_and_rejects_unresolved(self):
        self.common.write_bytes((REPO / "config/project.toml").read_bytes())
        resolved = self.load()
        self.assertEqual(config.require_values(resolved, ("harness.key_gap_ms", "paths.work_root")),
                         (350, self.root / "_work"))
        for key in ("tools.winshot_root", "harness.unknown", "repo"):
            with self.subTest(key=key), self.assertRaisesRegex(config.ConfigError, "unresolved"):
                config.require_values(resolved, (key,))

    def test_absent_harness_table_is_unresolved_not_missing_for_active_operations(self):
        self.assert_registered()
        resolved = self.load()
        for operation in ("workflow", "report"):
            exported = config.export_config(resolved, operation=operation)
            for name in TIMEOUTS | LOCKED_INPUT:
                with self.subTest(operation=operation, name=name):
                    self.assertIn(f"harness.{name}", exported["unresolved"])
                    self.assertNotIn(f"harness.{name}", exported["missing"])
        exported = config.export_config(resolved, operation="versus-session")
        for name in TIMEOUTS | LOCKED_INPUT:
            with self.subTest(operation="versus-session", name=name):
                self.assertIn(f"harness.{name}", exported["missing"])

    def test_new_harness_table_does_not_add_personal_paths(self):
        data = tomllib.loads((REPO / "config/project.toml").read_text(encoding="utf-8"))
        self.assertIn("harness", data)
        self.assertEqual(set(data["harness"]), set(TIMEOUTS | LOCKED_INPUT))


if __name__ == "__main__":
    unittest.main()
