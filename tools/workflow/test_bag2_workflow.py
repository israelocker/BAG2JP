"""Regression checks for compact process logs, tag validation and source comparison."""
import argparse
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import contextlib
import io
import json
import subprocess
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bag2_workflow as workflow
from tools.workflow import project_config as config

REPO = Path(__file__).resolve().parents[2]

class WorkflowTests(unittest.TestCase):
    def test_tag_rejects_paths_shell_text_and_oversize(self):
        for value in ("", "../stable", "x/y", "x\\y", "x;whoami", "a" * 65):
            with self.subTest(value=value), self.assertRaises(argparse.ArgumentTypeError):
                workflow.valid_tag(value)
        self.assertEqual(workflow.valid_tag("heat_bag1-2"), "heat_bag1-2")

    def test_failed_child_keeps_full_log_but_limits_summary(self):
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / "child.log"
            result = workflow.run_command(
                [sys.executable, "-c", "for i in range(30): print(i)\nraise SystemExit(7)"], log)
            self.assertEqual(result["returncode"], 7)
            self.assertEqual(log.read_text().splitlines(), list(map(str, range(30))))
            self.assertEqual(result["tail"], list(map(str, range(18, 30))))

    def test_success_child_reports_only_last_two_lines(self):
        with tempfile.TemporaryDirectory() as temp:
            result = workflow.run_command(
                [sys.executable, "-c", "print('a');print('b');print('c')"],
                Path(temp) / "ok.log")
            self.assertEqual(result, {"returncode": 0, "tail": ["b", "c"]})

    def test_report_preserves_state_even_before_long_cue_output(self):
        with tempfile.TemporaryDirectory() as temp:
            code = "print('state: ready')\nfor i in range(30): print('cue: noise')\nprint('phases: complete')"
            result = workflow.run_command([sys.executable, "-c", code],
                Path(temp) / "report.log", summary_prefixes=("state:", "phases:"))
            self.assertEqual(result, {"returncode": 0,
                             "summary": ["state: ready", "phases: complete"]})

    def test_missing_command_fails_instead_of_reporting_success(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(OSError):
                workflow.run_command([str(Path(temp) / "missing.exe")], Path(temp) / "missing.log")

    def test_source_summary_detects_drift_without_overwriting(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, build = root / "repo", root / "build"
            (repo / "mods-src/pkg").mkdir(parents=True)
            (build / "src").mkdir(parents=True)
            (repo / "mods-src/pkg/same.c").write_bytes(b"same\n")
            (repo / "mods-src/pkg/changed.inc").write_bytes(b"new\n")
            (repo / "mods-src/pkg/unmapped.h").write_bytes(b"archive\n")
            (build / "src/same.c").write_bytes(b"same\n")
            (build / "src/changed.inc").write_bytes(b"old\n")
            result = workflow.source_summary(repo, build)
            self.assertEqual(result["matching"], 1)
            self.assertEqual(result["different"], ["mods-src/pkg/changed.inc"])
            self.assertEqual(result["unmapped"], 1)
            self.assertEqual((build / "src/changed.inc").read_bytes(), b"old\n")

    def test_failed_phase_preserves_exit_code_and_timing(self):
        with tempfile.TemporaryDirectory() as temp:
            records = []
            with self.assertRaises(RuntimeError):
                workflow.run_phase("fail", lambda log: {"returncode": 7, "tail": ["bad"]},
                                   Path(temp), records)
            self.assertEqual(records[0]["status"], "failed")
            self.assertEqual(records[0]["result"]["returncode"], 7)
            self.assertGreaterEqual(records[0]["seconds"], 0)

    def test_failed_preflight_emits_metrics_and_nonzero_exit(self):
        with tempfile.TemporaryDirectory() as temp:
            cfg = fixture_config(Path(temp))
            output = io.StringIO()
            with mock.patch.object(workflow, "load_config", return_value=cfg), \
                    contextlib.redirect_stdout(output):
                self.assertEqual(workflow.main(["preflight", "--tag", "missing"]), 1)
            report = json.loads(output.getvalue())
            self.assertEqual(report["status"], "failed")
            stored = json.loads(Path(report["metrics"]).read_text())
            self.assertEqual(stored["phases"][0]["status"], "failed")
            self.assertIn("Missing required paths", stored["phases"][0]["error"])

def fixture_config(root: Path, omit=(), **overrides):
    """Build a resolved config from a disposable tree, never from the real repo."""
    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / "config/project.toml").write_text(
        'schema_version = 1\n[paths]\nwork_root = "_work"\n[wsl]\ndistribution = "Ubuntu"\n'
        '[build]\njobs = 2\n[pins]\npsxrecomp = "1a3fc0db"\nrecomp_ui = "3f1d6f1"\n',
        encoding="utf-8", newline="\n")
    values = {
        "build_root": "build",
        "experimental_install": "exp",
        "stable_install": "stable",
        "work_root": "_work",
        "build_script": "tools build/build_bag2jp.sh",
        "python_report": "python/python.exe",
        "audio_probe": "probe/audio_probe.py",
    }
    values.update(overrides)
    for name in omit:
        values.pop(name, None)
    lines = ["schema_version = 1", "[paths]"]
    for name in ("build_root", "experimental_install", "stable_install", "work_root"):
        if values.get(name):
            lines.append(f'{name} = "{values[name]}"')
    lines.append("[tools]")
    for name in ("build_script", "python_report", "audio_probe"):
        if values.get(name):
            lines.append(f'{name} = "{values[name]}"')
    local = root / "config/project.local.toml"
    local.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return config.load_config(repo_root=root, local_config=local)


class ConfigurationTests(unittest.TestCase):
    """The workflow derives its machine locations from the shared configuration."""

    def test_settings_resolve_from_configuration(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            settings = workflow.resolve_settings(fixture_config(root))
            self.assertEqual(settings.repo, root)
            self.assertEqual(settings.build, root / "build")
            self.assertEqual(settings.experimental, root / "exp")
            self.assertEqual(settings.build_script, root / "tools build/build_bag2jp.sh")
            self.assertEqual(settings.report_python, root / "python/python.exe")
            self.assertEqual(settings.pins, {"psxrecomp": "1a3fc0db", "recomp-ui": "3f1d6f1"})
            self.assertEqual(settings.wsl_distribution, "Ubuntu")
            self.assertEqual(settings.report_script, root / "tools/test/bag2_report.py")

    def test_missing_key_is_named_before_touching_anything(self):
        with tempfile.TemporaryDirectory() as temp:
            cfg = fixture_config(Path(temp), omit=("build_root",))
            with self.assertRaisesRegex(config.ConfigError, "paths.build_root"):
                workflow.resolve_settings(cfg)

    def test_no_machine_locations_live_in_the_module(self):
        for name in ("REPO", "BUILD", "EXPERIMENTAL", "BUILD_SCRIPT", "REPORT_PYTHON", "PINS"):
            with self.subTest(name=name):
                self.assertFalse(hasattr(workflow, name), f"{name} must come from configuration")
        absolute = {name for name, value in vars(workflow).items()
                    if isinstance(value, Path) and value.is_absolute()}
        self.assertEqual(sorted(absolute), [])

    def test_import_does_not_read_configuration(self):
        import importlib
        patches = [mock.patch(name, side_effect=AssertionError(f"{name} used at import time"))
                   for name in ("pathlib.Path.read_bytes", "pathlib.Path.read_text",
                                "builtins.open", "tomllib.load")]
        for patch in patches:
            patch.start()
        try:
            module = importlib.reload(workflow)
        finally:
            for patch in reversed(patches):
                patch.stop()
        self.assertTrue(callable(module.resolve_settings))

    def test_documented_script_invocation_prints_help(self):
        with tempfile.TemporaryDirectory(prefix="workflow-cwd-", dir=REPO / "_work") as cwd:
            result = subprocess.run(
                [sys.executable, str(REPO / "tools/workflow/bag2_workflow.py"), "--help"],
                cwd=cwd, capture_output=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        self.assertIn(b"--tag", result.stdout)

    def test_configured_work_root_and_overlay_reach_report_and_metrics(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cfg = fixture_config(root, work_root="evidence with spaces")
            out = io.StringIO()
            with mock.patch.object(workflow, "load_config", return_value=cfg), \
                    mock.patch.object(workflow, "preflight", return_value={}), \
                    mock.patch.object(workflow, "run_command", return_value={"returncode": 0}) as child, \
                    contextlib.redirect_stdout(out):
                code = workflow.main(["report", "--tag", "fixture"])
            self.assertEqual(code, 0, out.getvalue())
            data = json.loads(out.getvalue())
            metrics = Path(data["metrics"])
            self.assertTrue(metrics.is_relative_to(root / "evidence with spaces/workflow"))
            self.assertIn("--local-config", child.call_args.args[0])
            selected = child.call_args.args[0].index("--local-config") + 1
            self.assertEqual(Path(child.call_args.args[0][selected]), Path(cfg.input_files["local"]))
            self.assertEqual(data["configuration"]["config"], dict(cfg.input_hashes))
            self.assertEqual(data["configuration"]["values"]["paths.work_root"],
                             str(root / "evidence with spaces"))

    def test_work_root_inside_stable_fails_before_creating_logs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cfg = fixture_config(root, work_root="stable/evidence")
            out, err = io.StringIO(), io.StringIO()
            with mock.patch.object(workflow, "load_config", return_value=cfg), \
                    mock.patch.object(workflow, "preflight", side_effect=AssertionError("preflight ran")), \
                    contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                self.assertEqual(workflow.main(["preflight"]), 2)
            self.assertFalse((root / "stable").exists())
            self.assertEqual(out.getvalue(), "")
            self.assertIn("stable", err.getvalue())

    def test_report_python_is_only_required_for_report_execution(self):
        with tempfile.TemporaryDirectory() as temp:
            cfg = fixture_config(Path(temp), omit=("python_report",))
            try:
                settings = workflow.resolve_settings(cfg)
            except config.ConfigError as exc:
                self.fail(f"preflight must diagnose absent report interpreter, not reject config: {exc}")
            self.assertIsNone(settings.report_python)

    def test_fixed_build_script_contract_reads_actual_targets_without_executing(self):
        self.assertTrue(hasattr(workflow, "build_script_contract"), "missing fixed-script safety check")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            settings = workflow.resolve_settings(fixture_config(root))
            settings.build_script.parent.mkdir(parents=True)
            fixed = workflow.wsl_path(settings.build / "build-win-codex")
            settings.build_script.write_text(
                '#!/usr/bin/env bash\nset -euo pipefail\n'
                'toolchain=/mnt/x/fixed-toolchain\nexport PATH="$toolchain/bin:$PATH"\n'
                'command -v x86_64-w64-mingw32-windres\n'
                f'cmake --build "{fixed}" --target psx-runtime -j 2\n', encoding="utf-8")
            contract = workflow.build_script_contract(settings)
            self.assertTrue(contract["compatible"], contract)
            self.assertEqual(contract["toolchain"], "/mnt/x/fixed-toolchain")
            self.assertEqual(workflow.command_for(settings, "build", "fixture"),
                             ["wsl.exe", "-d", "Ubuntu", "--exec", "bash",
                              workflow.wsl_path(settings.build_script)])
            self.assertFalse(settings.build.exists(), "argv validation must not create a build tree")
            settings.build_script.write_text(settings.build_script.read_text().replace(fixed, "/mnt/x/wrong"))
            contract = workflow.build_script_contract(settings)
            self.assertFalse(contract["compatible"], contract)

    def test_build_mismatch_never_launches_build_subprocess(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cfg = fixture_config(root)
            script = Path(cfg.values["tools.build_script"])
            script.parent.mkdir(parents=True)
            script.write_text("#!/bin/sh\necho 'unsupported fixed-script contract'\n")
            out = io.StringIO()
            with mock.patch.object(workflow, "load_config", return_value=cfg), \
                    mock.patch.object(workflow, "preflight", return_value={}), \
                    mock.patch.object(workflow, "run_command", side_effect=AssertionError("build launched")), \
                    contextlib.redirect_stdout(out):
                self.assertEqual(workflow.main(["build"]), 1)
            data = json.loads(out.getvalue())
            self.assertEqual(data["status"], "failed")

    def test_fixed_build_jobs_and_unknown_shell_text_are_not_assumed_safe(self):
        with tempfile.TemporaryDirectory() as temp:
            settings = workflow.resolve_settings(fixture_config(Path(temp)))
            settings.build_script.parent.mkdir(parents=True)
            text = ('#!/usr/bin/env bash\nset -euo pipefail\n'
                    'toolchain=/mnt/x/fixed-toolchain\nexport PATH="$toolchain/bin:$PATH"\n'
                    'command -v x86_64-w64-mingw32-windres\n'
                    f'cmake --build "{workflow.wsl_path(settings.build / "build-win-codex")}" '
                    '--target psx-runtime -j 4\n')
            settings.build_script.write_text(text)
            self.assertFalse(workflow.build_script_contract(settings)["compatible"])
            settings.build_script.write_text(text.replace('toolchain=/mnt/x/fixed-toolchain',
                                                          'toolchain=$(echo unsafe)').replace('-j 4', '-j 2'))
            self.assertFalse(workflow.build_script_contract(settings)["compatible"])

    def test_build_target_inside_stable_is_rejected_even_with_matching_script(self):
        with tempfile.TemporaryDirectory() as temp:
            settings = workflow.resolve_settings(fixture_config(Path(temp), build_root="stable/build"))
            settings.build_script.parent.mkdir(parents=True)
            settings.build_script.write_text(
                '#!/usr/bin/env bash\nset -euo pipefail\n'
                'toolchain=/mnt/x/toolchain\nexport PATH="$toolchain/bin:$PATH"\n'
                'command -v x86_64-w64-mingw32-windres\n'
                f'cmake --build "{workflow.wsl_path(settings.build / "build-win-codex")}" '
                '--target psx-runtime -j 2\n')
            self.assertTrue(workflow.build_script_contract(settings)["compatible"])
            with self.assertRaisesRegex(config.ConfigError, "protected stable"):
                workflow.command_for(settings, "build", "fixture")

    def test_build_toolchain_redirection_is_not_a_literal_assignment(self):
        with tempfile.TemporaryDirectory() as temp:
            settings = workflow.resolve_settings(fixture_config(Path(temp)))
            settings.build_script.parent.mkdir(parents=True)
            for suffix in ('>/mnt/x/escape', '</mnt/x/input', '&echo bad', '|echo bad'):
                text = ('#!/usr/bin/env bash\nset -euo pipefail\n'
                        f'toolchain=/mnt/x/toolchain{suffix}\nexport PATH="$toolchain/bin:$PATH"\n'
                        'command -v x86_64-w64-mingw32-windres\n'
                        f'cmake --build "{workflow.wsl_path(settings.build / "build-win-codex")}" '
                        '--target psx-runtime -j 2\n')
                settings.build_script.write_text(text)
                with self.subTest(operator=suffix):
                    self.assertFalse(workflow.build_script_contract(settings)["compatible"])

    def test_preflight_preserves_optional_python_diagnostic_and_contract_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            settings = workflow.resolve_settings(fixture_config(root, omit=("python_report",)))
            for name in ("NOTES.md", "AGENTS.md", "build/CMakeLists.txt", "exp/BAG2JP.exe"):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"fixture")
            (root / "exp/mods/bundled").mkdir(parents=True)
            cache = root / "build/build-win-codex/CMakeCache.txt"
            cache.parent.mkdir()
            cache.write_text("CMAKE_HOME_DIRECTORY:INTERNAL=" + workflow.wsl_path(settings.build) + "\n")
            settings.build_script.parent.mkdir(parents=True)
            settings.build_script.write_text("#!/bin/sh\n# unsupported contract is diagnostic in preflight\n")

            def fake_git(path, *args):
                if args == ("rev-parse", "HEAD"):
                    return settings.pins[path.name] + "fixture"
                return "fixture" if args[-1] == "HEAD" else ""

            with mock.patch.object(workflow, "git", side_effect=fake_git):
                data = workflow.preflight(root / "preflight.json", settings)
            self.assertFalse(data["report_python_present"])
            self.assertFalse(data["fixed_build_contract"]["compatible"])
            self.assertIn("sha256", data["fixed_build_contract"])


if __name__ == "__main__":
    unittest.main()
