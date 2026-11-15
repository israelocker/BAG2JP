"""The report derives its game, shots and probe locations from the shared configuration."""

import contextlib
import importlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from tools.test import bag2_report as report
from tools.workflow import project_config as config


REPO = Path(__file__).resolve().parents[2]


def fixture_config(root: Path, *, with_probe: bool = True):
    """Resolve a disposable tree; nothing here points at a real install."""
    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / "config/project.toml").write_text(
        'schema_version = 1\n[paths]\nwork_root = "_work"\n', encoding="utf-8", newline="\n")
    lines = ["schema_version = 1", "[paths]", 'experimental_install = "exp"',
             'stable_install = "stable"']
    if with_probe:
        lines += ["[tools]", 'audio_probe = "probe/audio_probe.py"']
    local = root / "config/project.local.toml"
    local.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return config.load_config(repo_root=root, local_config=local)


class PathTests(unittest.TestCase):
    def test_paths_come_from_configuration(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            experimental, shots, probe = report.resolve_paths(fixture_config(root))
            self.assertEqual(experimental, root / "exp")
            self.assertEqual(shots, root / "_work/shots")
            self.assertEqual(probe, root / "probe/audio_probe.py")

    def test_missing_probe_is_named(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(config.ConfigError, "tools.audio_probe"):
                report.resolve_paths(fixture_config(Path(temp), with_probe=False), need_audio=True)

    def test_state_report_does_not_require_unused_audio_tool(self):
        with tempfile.TemporaryDirectory() as temp:
            cfg = fixture_config(Path(temp), with_probe=False)
            try:
                paths = report.resolve_paths(cfg)
            except config.ConfigError as exc:
                self.fail(f"unused audio tool should not be required: {exc}")
            self.assertIsNone(paths[2])

    def test_no_machine_locations_live_in_the_module(self):
        for name in ("E", "SHOTS", "PROBE"):
            with self.subTest(name=name):
                self.assertFalse(hasattr(report, name), f"{name} must come from configuration")
        absolute = {name for name, value in vars(report).items()
                    if isinstance(value, Path) and value.is_absolute()}
        self.assertEqual(sorted(absolute), [])

    def test_import_does_not_read_configuration(self):
        patches = [mock.patch(name, side_effect=AssertionError(f"{name} used at import time"))
                   for name in ("pathlib.Path.read_bytes", "pathlib.Path.read_text",
                                "builtins.open", "tomllib.load")]
        for patch in patches:
            patch.start()
        try:
            module = importlib.reload(report)
        finally:
            for patch in reversed(patches):
                patch.stop()
        self.assertTrue(callable(module.main))


class MainTests(unittest.TestCase):
    def setUp(self):
        parent = REPO / "_work"
        parent.mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(prefix="report-config-", dir=parent)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.config = fixture_config(self.root)
        self.experimental = self.root / "exp"
        self.experimental.mkdir()
        self.shots = self.root / "_work/shots"

    def run_main(self, *arguments):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(report, "load_config", return_value=self.config), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = report.main(list(arguments))
        return code, out.getvalue(), err.getvalue()

    def test_reads_the_configured_install_and_reports_state(self):
        (self.experimental / "bag2jp_frame.txt").write_text("4321 1-2 0.0\n", encoding="utf-8")
        code, out, _err = self.run_main("--tag", "t", "--frame", "4321", "--timeout", "0")
        self.assertEqual(code, 0)
        self.assertIn("state: frame 4321 phase 1-2", out)

    def test_sheet_is_written_under_the_configured_work_root(self):
        (self.experimental / "bag2jp_frame.txt").write_text("1 1/1 0.0\n", encoding="utf-8")
        shot_dir = self.shots / "t"
        shot_dir.mkdir(parents=True)
        from PIL import Image
        Image.new("RGB", (8, 8)).save(shot_dir / "f000001.png")
        code, out, _err = self.run_main("--tag", "t", "--timeout", "0")
        self.assertEqual(code, 0)
        sheet = self.shots / "t_sheet.png"
        self.assertTrue(sheet.is_file())
        self.assertIn(str(sheet).replace("\\", "/"), out.replace("\\", "/"))

    def test_invalid_configuration_exits_two_without_output(self):
        broken = self.root / "config/broken.toml"
        broken.write_text('schema_version = 9\n', encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = report.main(["--tag", "t", "--local-config", str(broken)])
        self.assertEqual(code, 2)
        self.assertEqual(out.getvalue(), "")

    def test_documented_script_invocation_prints_help(self):
        with tempfile.TemporaryDirectory(prefix="report-cwd-", dir=REPO / "_work") as cwd:
            result = subprocess.run(
                [sys.executable, str(REPO / "tools/test/bag2_report.py"), "--help"],
                cwd=cwd, capture_output=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        self.assertIn(b"--tag", result.stdout)

    def test_sheet_cannot_overwrite_a_destination_inside_stable(self):
        self.config = fixture_config(self.root)
        # Point the work root physically at the protected installation in the local overlay.
        local = self.root / "config/project.local.toml"
        text = local.read_text().replace('experimental_install = "exp"',
                                         'experimental_install = "exp"\nwork_root = "stable"')
        local.write_text(text)
        self.config = config.load_config(repo_root=self.root, local_config=local)
        images = self.root / "stable/shots/t"
        images.mkdir(parents=True)
        from PIL import Image
        Image.new("RGB", (8, 8)).save(images / "f000001.png")
        code, out, err = self.run_main("--tag", "t", "--timeout", "0")
        self.assertEqual(code, 2, err)
        self.assertEqual(out, "")
        self.assertFalse((images.parent / "t_sheet.png").exists())

    def test_tag_rejects_traversal_before_loading_configuration(self):
        with mock.patch.object(report, "load_config", side_effect=AssertionError("config loaded")), \
                contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                report.main(["--tag", "../stable"])
        self.assertEqual(caught.exception.code, 2)

    def test_find_requires_probe_before_printing_or_launching_audio(self):
        self.config = fixture_config(self.root, with_probe=False)
        (self.experimental / "bag2jp_audio.wav").write_bytes(b"audio fixture")
        code, out, err = self.run_main("--find", "sample.wav", "--timeout", "0")
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("tools.audio_probe", err)

    def test_real_cli_uses_overlay_from_another_cwd_and_preserves_summary(self):
        (self.experimental / "bag2jp_frame.txt").write_text("4321 1/7\n", encoding="utf-8")
        (self.experimental / "bag2jp_anim_trace.log").write_text(
            "f4000 mode1 phase 1/7/0 fever1 | P1 ch0 anim99 req0 | P2 ch1 anim94\n",
            encoding="utf-8")
        (self.experimental / "psx_last_run_report.json").write_text('{"status":"fixture"}')
        overlay = self.root / "absolute local.toml"
        overlay.write_text(
            'schema_version = 1\n[paths]\n'
            f'experimental_install = {json.dumps(str(self.experimental))}\n'
            f'work_root = {json.dumps(str(self.root / "alternate work"))}\n', encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(REPO / "tools/test/bag2_report.py"),
             "--local-config", str(overlay), "--tag", "fixture", "--timeout", "0"],
            cwd=self.root, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        text = result.stdout.decode("utf-8")
        self.assertIn("state: frame 4321 phase 1/7", text)
        self.assertIn("phases: 4000:1/7 fever1", text)
        self.assertIn("fever anims: f4000 P1 anim99 | P2 anim94", text)
        self.assertIn("run report: status=fixture", text)

    def test_actual_audio_probe_argv_preserves_spaces_without_shell(self):
        probe = self.root / "probe/audio_probe.py"
        probe.parent.mkdir()
        receipt = self.root / "audio argv.json"
        probe.write_text(
            'import json,sys\nfrom pathlib import Path\n'
            f'Path({str(receipt)!r}).write_text(json.dumps(sys.argv[1:]))\n'
            'print("audio fixture matched")\n', encoding="utf-8")
        (self.experimental / "bag2jp_audio.wav").write_bytes(b"stub audio")
        code, out, _err = self.run_main("--find", "sample with spaces.wav", "--timeout", "0")
        self.assertEqual(code, 0)
        self.assertIn("audio fixture matched", out)
        argv = json.loads(receipt.read_text())
        self.assertEqual(argv, ["find", str(self.experimental) + "/bag2jp_audio.wav",
                                "sample with spaces.wav", "--sync",
                                str(self.experimental) + "/bag2jp_audio_sync.log", "--thr", "0.5"])

    def test_wav_appearing_while_waiting_requires_probe_before_any_output(self):
        self.config = fixture_config(self.root, with_probe=False)
        frame = self.experimental / "bag2jp_frame.txt"
        frame.write_text("1 1/1\n")

        def publish_wav(_seconds):
            (self.experimental / "bag2jp_audio.wav").write_bytes(b"late WAV")
            frame.write_text("2 1/1\n")

        with mock.patch.object(report.time, "sleep", side_effect=publish_wav), \
                mock.patch.object(report.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "audio", "")) as child:
            code, out, err = self.run_main("--frame", "2", "--find", "sample.wav", "--timeout", "10")
        self.assertEqual(code, 2, err)
        self.assertEqual(out, "")
        child.assert_not_called()

    def test_directory_named_wav_is_not_an_audio_input(self):
        (self.experimental / "bag2jp_audio.wav").mkdir()
        with mock.patch.object(report.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "audio", "")) as child:
            code, _out, _err = self.run_main("--find", "sample.wav", "--timeout", "0")
        self.assertEqual(code, 0)
        child.assert_not_called()


if __name__ == "__main__":
    unittest.main()
