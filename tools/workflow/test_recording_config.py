"""Prepare recording host settings; no recorder, media tools or game are started."""

import json
from pathlib import Path
import unittest

from tools.workflow import project_config as config
from tools.workflow.test_project_config import ConfigFixture, working_directory

REPO = Path(__file__).resolve().parents[2]
DEFAULTS = {
    "fps": 60,
    "max_seconds": 900.0,
    "poll_seconds": 0.004,
    "alive_check_seconds": 1.0,
    "window_wait_seconds": 60.0,
    "window_poll_seconds": 0.5,
    "ffmpeg_quit_seconds": 30.0,
    "ffmpeg_extra_seconds": 5,
    "ffmpeg_stop_poll_seconds": 0.1,
    "process_audio_extra_seconds": 60.0,
}
PATHS = ("ffprobe_review", "ffmpeg_look", "recording_font")
INTEGER_FIELDS = frozenset(("fps", "ffmpeg_extra_seconds"))
BOUNDS = {name: 240 if name == "fps" else 86400 for name in DEFAULTS}


class RecordingConfigurationTests(ConfigFixture):
    def assert_registered(self):
        expected = {f"recording.{name}" for name in DEFAULTS} | {f"tools.{name}" for name in PATHS}
        self.assertFalse(expected - set(config.FIELDS), "recording settings must be registered first")

    def test_common_defaults_match_current_recorder_and_operations(self):
        self.assert_registered()
        self.common.write_bytes((REPO / "config/project.toml").read_bytes())
        resolved = self.load()
        for name, expected in DEFAULTS.items():
            key = f"recording.{name}"
            with self.subTest(key=key):
                self.assertEqual(resolved.values[key], expected)
                self.assertEqual(type(resolved.values[key]), type(expected))
                self.assertEqual(resolved.origins[key], "common")
                self.assertEqual(config.FIELDS[key].operations, ("recording-record",))
                self.assertEqual(config.FIELDS[key].kind, "integer" if name in INTEGER_FIELDS else "number")
        for name in PATHS:
            self.assertNotIn(f"tools.{name}", resolved.values, "distributed TOML must not supply machine paths")

    def test_numeric_overrides_are_typed_independent_and_immutable(self):
        self.assert_registered()
        self.common.write_bytes((REPO / "config/project.toml").read_bytes())
        first = self.load()
        for name in DEFAULTS:
            key = f"recording.{name}"
            value = 2 if name in INTEGER_FIELDS else 0.01
            self.write_local(f"[recording]\n{name} = {value}\n")
            second = self.load()
            exported = json.loads(json.dumps(config.export_config(second, operation="inspect"), allow_nan=False))
            with self.subTest(key=key):
                self.assertEqual(second.values[key], value)
                self.assertEqual(exported["values"][key], value)
                self.assertEqual(second.origins[key], "local")
                self.assertEqual(first.values[key], DEFAULTS[name])
                for other, default in DEFAULTS.items():
                    other_key = f"recording.{other}"
                    self.assertEqual(second.values[other_key], value if other == name else default)
                    self.assertEqual(second.origins[other_key], "local" if other == name else "common")
                with self.assertRaises(TypeError):
                    second.values[key] = 999

    def test_each_numeric_field_rejects_wrong_type_nonpositive_nonfinite_and_overflow(self):
        self.assert_registered()
        for name in DEFAULTS:
            invalid = ['true', '"2"', '0', '-1', 'nan', 'inf', '-inf', str(10 ** 400),
                       str(BOUNDS[name] + 1)]
            if name in INTEGER_FIELDS:
                invalid += ["1.5", "2.0"]
            for literal in invalid:
                self.write_local(f"[recording]\n{name} = {literal}\n")
                with self.subTest(name=name, literal=literal[:20]):
                    try:
                        self.load()
                    except config.ConfigError as exc:
                        self.assertRegex(str(exc), f"recording\\.{name}: expected")
                    except Exception as exc:
                        self.fail(f"recording.{name}: expected ConfigError, got {type(exc).__name__}: {exc}")
                    else:
                        self.fail(f"recording.{name}: expected ConfigError for {literal[:20]}")

    def test_numeric_schema_bounds_are_inclusive(self):
        self.assert_registered()
        for name in DEFAULTS:
            key = f"recording.{name}"
            spec = config.FIELDS[key]
            self.assertEqual(spec.maximum, BOUNDS[name])
            value = BOUNDS[name]
            self.write_local(f"[recording]\n{name} = {value}\n")
            with self.subTest(name=name):
                self.assertEqual(self.load().values[key], value)

    def test_new_paths_anchor_to_relocated_repo_and_are_optional(self):
        self.assert_registered()
        empty = self.load()
        for name in PATHS:
            key = f"tools.{name}"
            with self.subTest(key=key):
                self.assertNotIn(key, empty.values)
                self.assertEqual(config.FIELDS[key].operations,
                                 ("recording-frames",) if name == "ffmpeg_look" else ("recording-finalize",))
                with self.assertRaisesRegex(config.ConfigError, "unresolved"):
                    config.require_paths(empty, (key,))
        self.write_local('[tools]\n' + ''.join(f'{name} = "helpers ñ ; &/{name}"\n' for name in PATHS))
        with working_directory(self.root.parent):
            loaded = self.load()
        for name in PATHS:
            key = f"tools.{name}"
            self.assertEqual(config.require_paths(loaded, (key,)), (self.root / "helpers ñ ; &" / name,))
            self.assertEqual(loaded.origins[key], "local")
        for literal in ('""', 'true', '5', '"\\u0000"'):
            for name in PATHS:
                self.write_local(f"[tools]\n{name} = {literal}\n")
                with self.subTest(name=name, literal=literal):
                    self.assert_config_error(f"tools\\.{name}: expected")

    def test_absent_recording_fields_are_not_required_by_existing_operations(self):
        self.assert_registered()
        resolved = self.load()
        for operation in config.OPERATIONS:
            if operation.startswith("recording-"):
                continue
            exported = config.export_config(resolved, operation=operation)
            with self.subTest(operation=operation):
                self.assertFalse(set(exported["missing"]) & {f"recording.{name}" for name in DEFAULTS})
                self.assertFalse(set(exported["missing"]) & {f"tools.{name}" for name in PATHS})


if __name__ == "__main__":
    unittest.main()
