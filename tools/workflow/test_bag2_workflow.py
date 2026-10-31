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
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bag2_workflow as workflow

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
            output = io.StringIO()
            with mock.patch.object(workflow, "REPO", Path(temp)), contextlib.redirect_stdout(output):
                self.assertEqual(workflow.main(["preflight", "--tag", "missing"]), 1)
            report = json.loads(output.getvalue())
            self.assertEqual(report["status"], "failed")
            stored = json.loads(Path(report["metrics"]).read_text())
            self.assertEqual(stored["phases"][0]["status"], "failed")
            self.assertIn("Missing required paths", stored["phases"][0]["error"])

if __name__ == "__main__":
    unittest.main()
