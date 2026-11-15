"""Recorder configuration seams; effects are mocked or confined to owned temp files."""
import dataclasses
import json
import itertools
from pathlib import Path
import subprocess
from unittest.mock import MagicMock, Mock, patch

from tools.test import bag2_record as rec
from tools.workflow import project_config as pc
from tools.workflow.test_project_config import ConfigFixture, working_directory, _make_directory_alias


class RecordingConfigTests(ConfigFixture):
    def setUp(self):
        super().setUp()
        self.common.write_bytes((Path(__file__).resolve().parents[2] / "config/project.toml").read_bytes())
        self.write_local('[paths]\nexperimental_install="game ñ"\nstable_install="stable"\n'
                         'work_root="evidence ; &"\n[tools]\nffmpeg_review="tools/video.exe"\n'
                         'ffmpeg_wgc="tools/wgc.exe"\nffprobe_review="tools/probe.exe"\n'
                         'ffmpeg_look="tools/look.py"\nrecording_font="tools/font.ttf"\n')
        (self.root / "tools").mkdir()
        for name in ("video.exe", "wgc.exe", "probe.exe", "look.py", "font.ttf"):
            (self.root / "tools" / name).write_bytes(b"owned fixture, never executed")

    def settings(self, **kwargs):
        self.assertTrue(callable(getattr(rec, "resolve_settings", None)), "recorder must resolve per-run settings")
        return rec.resolve_settings(self.load(), environ={}, **kwargs)

    def test_relocated_immutable_settings_and_independent_loads(self):
        with working_directory(self.root.parent):
            first = self.settings()
        self.assertEqual(first.recordings, self.root / "evidence ; &/recordings")
        self.assertEqual(first.game_dir, self.root / "game ñ")
        self.assertEqual((first.fps, first.max_seconds), (60, 900.0))
        self.assertEqual(first.value("poll_seconds"), .004)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            first.game_dir = self.root
        self.write_local(self.local.read_text(encoding="utf-8") + '[recording]\nfps=48\npoll_seconds=0.025\n')
        second = self.settings()
        self.assertEqual((second.fps, second.value("poll_seconds")), (48, .025))
        self.assertEqual((first.fps, first.value("poll_seconds")), (60, .004))

    def test_environment_and_explicit_cli_have_recorded_precedence(self):
        self.assertTrue(callable(getattr(rec, "resolve_settings", None)), "recorder must resolve per-run settings")
        env = {"BAG2JP_FFMPEG_WGC": str(self.root / "tools/probe.exe")}
        settings = rec.resolve_settings(self.load(), environ=env, fps=30, max_seconds=12.5,
                                        game_dir=self.root / "explicit game")
        env["BAG2JP_FFMPEG_WGC"] = "changed after resolution"
        self.assertEqual((settings.fps, settings.max_seconds), (30, 12.5))
        self.assertEqual(settings.game_dir, self.root / "explicit game")
        self.assertEqual(rec.resolve_capture_backend("auto", settings=settings),
                         ("wgc", str(self.root / "tools/probe.exe")))
        payload = settings.provenance()
        self.assertEqual(payload["origins"]["recording.fps"], "cli")
        self.assertIn("BAG2JP_FFMPEG_WGC", payload["origins"]["tools.ffmpeg_wgc"])
        self.assertEqual(payload["values"]["paths.experimental_install"], str(self.root / "explicit game"))

    def test_disabled_or_missing_wgc_never_uses_old_defaults(self):
        self.assertTrue(callable(getattr(rec, "resolve_settings", None)), "recorder must resolve per-run settings")
        for value in ("", str(self.root / "missing.exe")):
            settings = rec.resolve_settings(self.load(), environ={"BAG2JP_FFMPEG_WGC": value})
            self.assertEqual(rec.resolve_capture_backend("auto", settings=settings),
                             ("gdigrab", str(self.root / "tools/video.exe")))
            with self.assertRaisesRegex(RuntimeError, "WGC"):
                rec.resolve_capture_backend("wgc", settings=settings)

    def test_output_alias_and_invalid_tag_rejected_before_effects(self):
        settings = self.settings()
        with patch.object(rec, "_win32", side_effect=AssertionError("must not reach game")):
            for tag in ("../escape", "", "."):
                with self.assertRaises(pc.ConfigError):
                    rec.record(tag, 60, 1, settings.game_dir, settings=settings)
        root = self.root / "evidence ; &"
        root.mkdir()
        # Portable directory symlink where permitted; the existing ancestry guard is shared.
        (root / "recordings").mkdir()
        self.assertEqual(settings.output("valid"), root / "recordings/valid")
        self.write_local('[paths]\nwork_root="stable"\nstable_install="stable"\n')
        with self.assertRaises(pc.ConfigError):
            self.settings(operation="frames")

    def test_main_cli_values_reach_capture_and_config_errors_exit_two(self):
        self.assertTrue(callable(getattr(rec, "resolve_settings", None)), "recorder must resolve per-run settings")
        with patch.object(rec, "load_config", return_value=self.load()), \
                patch.object(rec, "record", return_value=7) as capture:
            self.assertEqual(rec.main(["record", "--tag", "fresh", "--fps", "25", "--max-seconds", "2.5",
                                       "--game-dir", str(self.root / "explicit")]), 7)
            args = capture.call_args
            self.assertEqual(args.args[:4], ("fresh", 25, 2.5, self.root / "explicit"))
            self.assertEqual(args.kwargs["settings"].fps, 25)
        with patch.object(rec, "load_config", return_value=self.load()), patch.object(rec, "record") as capture:
            with self.assertRaises(SystemExit) as exit_code:
                rec.main(["record", "--tag", "fresh", "--fps", "0"])
            self.assertEqual(exit_code.exception.code, 2)
            capture.assert_not_called()

    def test_operation_requirements_do_not_pull_unrelated_tools(self):
        self.write_local('[paths]\nwork_root="work"\nstable_install="stable"\n'
                         '[tools]\nffmpeg_wgc="tools/wgc.exe"\n')
        settings = self.settings(game_dir=self.root / "explicit")
        self.assertEqual(rec.resolve_capture_backend("wgc", settings=settings)[0], "wgc")
        for operation, missing in (("finalize", "ffmpeg_review"), ("frames", "ffmpeg_look")):
            with self.assertRaisesRegex(pc.ConfigError, missing):
                self.settings(operation=operation)

    def test_missing_gdigrab_configuration_exits_two_before_win32(self):
        self.write_local('[paths]\nwork_root="work"\nstable_install="stable"\nexperimental_install="game"\n')
        with patch.object(rec, "load_config", return_value=self.load()), \
                patch.object(rec, "_win32", side_effect=AssertionError("no game calls")):
            with self.assertRaises(SystemExit) as result:
                rec.main(["record", "--tag", "fresh", "--capture-backend", "gdigrab"])
            self.assertEqual(result.exception.code, 2)

    def test_window_wait_and_poll_budgets_reach_real_loop(self):
        self.write_local(self.local.read_text(encoding="utf-8") +
                         '[recording]\nwindow_wait_seconds=0.25\nwindow_poll_seconds=0.125\n')
        settings = self.settings()
        with patch.object(rec, "_win32", return_value=(Mock(), Mock())), \
                patch.object(rec, "game_pid", return_value=None), \
                patch.object(rec.time, "time", side_effect=[0, .1, .3]), \
                patch.object(rec.time, "sleep") as sleep:
            self.assertEqual(rec.record("waiting", 60, 1, settings.game_dir, settings=settings), 3)
        sleep.assert_called_once_with(.125)
        self.assertFalse(settings.recordings.exists())

    def test_shutdown_uses_quit_poll_and_reap_budgets(self):
        self.write_local(self.local.read_text(encoding="utf-8") +
                         '[recording]\nffmpeg_quit_seconds=0.25\nffmpeg_stop_poll_seconds=0.025\nffmpeg_extra_seconds=9\n')
        settings = self.settings()
        child = Mock()
        child.poll.return_value = None
        waits = 0
        def wait(timeout=None):
            nonlocal waits
            waits += 1
            if waits == 1:
                raise subprocess.TimeoutExpired("owned", timeout)
            child.poll.return_value = 0
        child.wait.side_effect = wait
        with patch.object(rec.time, "monotonic", side_effect=[0, 1]):
            self.assertEqual(rec.stop_ffmpeg(child, settings=settings), "; ffmpeg killed")
        self.assertEqual([c.kwargs["timeout"] for c in child.wait.call_args_list], [.025, 9])
        child.kill.assert_called_once()

    def test_capture_budget_sinks_and_provenance_without_starting_helpers(self):
        self.write_local(self.local.read_text(encoding="utf-8") +
            '[recording]\npoll_seconds=0.025\nalive_check_seconds=0.05\n'
            'ffmpeg_extra_seconds=9\nprocess_audio_extra_seconds=11.0\n')
        settings = self.settings(fps=30, max_seconds=1.5)
        game = settings.game_dir; game.mkdir(); (game / rec.GAME_EXE).write_bytes(b"fixture")
        for requested in ("gdigrab", "wgc", "auto"):
            with self.subTest(backend=requested):
                child, window, watch, audio, tail = Mock(), Mock(), Mock(), Mock(), Mock()
                child.poll.return_value = None; child.returncode = 0; tail.lines.return_value = []
                window.key = "owned"; window.hwnd = 10
                audio.target.identity = {"pid": 7}; audio.stop.return_value = {"helper_exit": 0}
                checks = []
                watch.alive.side_effect = lambda: checks.append("alive") or True
                window.check.side_effect = lambda: checks.append("window")
                audio.check.side_effect = lambda: checks.append("audio")
                with patch.object(rec.subprocess, "Popen", return_value=child) as popen, \
                        patch.object(rec, "ProcessAudio") as backend, patch.object(rec, "Tail", return_value=tail), \
                        patch.object(rec, "read_heartbeat", return_value=100), patch.object(rec, "copy_audio", return_value=[]), \
                        patch.object(rec, "stop_ffmpeg", return_value="") as stop, \
                        patch.object(rec.time, "time", side_effect=itertools.count(100, .2).__next__), \
                        patch.object(rec.time, "sleep") as sleep:
                    backend.start.return_value = audio
                    rec._record_capture("sinks-" + requested, 30, 1.5, game, 7, (0, 0, 640, 480), window, watch,
                                        capture_backend=requested, audio_backend="process", settings=settings)
                command = popen.call_args.args[0]
                effective = "gdigrab" if requested == "gdigrab" else "wgc"
                self.assertEqual(command[0], str(self.root / ("tools/video.exe" if effective == "gdigrab" else "tools/wgc.exe")))
                if effective == "gdigrab":
                    self.assertEqual(command[command.index("-framerate") + 1], "30")
                else:
                    self.assertIn("gfxcapture=hwnd=10:max_framerate=30:capture_cursor=0", command)
                    self.assertEqual(command[command.index("-use_wallclock_as_timestamps") + 1], "1")
                self.assertEqual(command[command.index("-t") + 1], "10")
                self.assertEqual(backend.start.call_args.args[3], 12.5)
                self.assertTrue(sleep.call_args_list)
                self.assertTrue(all(c.args == (.025,) for c in sleep.call_args_list))
                self.assertEqual(checks, ["window"] + ["alive", "window", "audio"] * 4 + ["window"])
                self.assertIs(stop.call_args.kwargs.get("settings"), settings)
                session = json.loads((settings.output("sinks-" + requested) / "session.json").read_text(encoding="utf-8"))
                self.assertEqual(session["capture_backend"], effective)
                self.assertIn("configuration", session)
                self.assertEqual(session["configuration"]["values"]["recording.poll_seconds"], .025)
                self.assertEqual(session["configuration"]["origins"]["recording.fps"], "cli")

    def test_actual_alias_targets_are_rejected_before_any_artifact_write(self):
        settings = self.settings(operation="finalize")
        settings.recordings.mkdir(parents=True)
        outside = self.root / "outside"; outside.mkdir()
        (outside / "session.json").write_text('{}', encoding="utf-8")
        self.assertTrue(_make_directory_alias(settings.recordings / "aliased", outside))
        with patch.object(rec, "load_clock", side_effect=AssertionError("no outside reads")):
            with self.assertRaises(pc.ConfigError):
                rec.finalize("aliased", settings=settings)
        out = settings.output("take"); out.mkdir()
        (out / "session.json").write_text('{}', encoding="utf-8")
        self.assertTrue(_make_directory_alias(out / "clock-font.ttf", outside))
        with patch.object(rec, "load_clock", side_effect=AssertionError("no artifact writes")):
            with self.assertRaises(pc.ConfigError):
                rec.finalize("take", settings=settings)

    def test_hardlinked_artifacts_are_rejected_without_touching_shared_files(self):
        import os
        settings = self.settings(operation="finalize")
        stable = self.root / "stable"; stable.mkdir()
        source = stable / "protected.bin"; source.write_bytes(b"stable fixture")
        for name in ("clock-font.ttf", "labels.ass", "review.mkv", "owner.mp4", "events.json", "manifest.json"):
            with self.subTest(artifact=name):
                out = settings.output("hardlink-" + name.replace(".", "-")); out.mkdir(parents=True)
                (out / "session.json").write_text('{}', encoding="utf-8")
                os.link(source, out / name)
                with patch.object(rec, "load_clock", side_effect=AssertionError("no shared artifact writes")):
                    with self.assertRaises(pc.ConfigError):
                        rec.finalize(out.name, settings=settings)
                self.assertEqual(source.read_bytes(), b"stable fixture")

    def test_directory_artifacts_are_rejected_before_any_write(self):
        import os
        settings = self.settings(operation="finalize")
        source = self.root / "stable/font.ttf"; source.parent.mkdir(); source.write_bytes(b"protected font")
        for name in ("clock-font.ttf", "labels.ass", "review.mkv", "owner.mp4", "events.json", "manifest.json"):
            out = settings.output("directory-" + name.replace(".", "-")); (out / name).mkdir(parents=True)
            if name == "clock-font.ttf":
                os.link(source, out / name / "font.ttf")
            (out / "session.json").write_text('{}', encoding="utf-8")
            with self.subTest(name=name), patch.object(rec, "load_clock", side_effect=AssertionError("no writes")):
                with self.assertRaises(pc.ConfigError):
                    rec.finalize(out.name, settings=settings)
            self.assertEqual(source.read_bytes(), b"protected font")

    def test_supplied_record_settings_require_review_tools_before_effects(self):
        for missing in ("recording_font", "ffmpeg_review", "ffprobe_review", "ffmpeg_look"):
            text = self.local.read_text(encoding="utf-8")
            self.write_local('\n'.join(line for line in text.splitlines() if not line.startswith(missing + '=')))
            settings = self.settings()
            out = settings.output("missing-" + missing.replace("_", "-")); out.mkdir(parents=True)
            (out / "session.json").write_text('{}', encoding="utf-8")
            with self.subTest(missing=missing), patch.object(rec, "load_clock", side_effect=AssertionError("before effects")):
                with self.assertRaises(pc.ConfigError):
                    if missing == "ffmpeg_look":
                        rec.frames(out.name, 10, 2, 2, settings=settings)
                    else:
                        rec.finalize(out.name, settings=settings)
            self.write_local(text)

    def test_shutdown_still_kills_and_reaps_if_configuration_cannot_be_resolved(self):
        child = Mock(); calls = []
        child.kill.side_effect = lambda: calls.append("kill")
        child.wait.side_effect = lambda: calls.append("wait")
        with patch.object(rec, "resolve_settings", side_effect=pc.ConfigError("invalid configuration")):
            with self.assertRaises(pc.ConfigError):
                rec.stop_ffmpeg(child)
        self.assertEqual(calls, ["kill", "wait"])

    def test_existing_still_aliases_are_rejected_before_the_helper_is_called(self):
        settings = self.settings(operation="frames")
        stills = settings.output("take") / "stills"; stills.mkdir(parents=True)
        outside = self.root / "outside"; outside.mkdir()
        self.assertTrue(_make_directory_alias(stills / "gf0000010-0.png", outside))
        with patch.object(rec, "load_clock", return_value=(Mock(), 0)), \
                patch.object(rec.subprocess, "run", side_effect=AssertionError("before helper")):
            with self.assertRaises(pc.ConfigError):
                rec.frames("take", 10, 2, 2, settings=settings)

    def test_frames_and_media_tools_use_effective_argv(self):
        settings = self.settings(operation="frames")
        settings.output("take").mkdir(parents=True)
        clock = Mock(); clock.wall_of.side_effect = lambda frame: 10 + frame * .1
        with patch.object(rec, "load_clock", return_value=(clock, 10)), \
                patch.object(rec.subprocess, "run", return_value=Mock(returncode=0, stdout="ok")) as run:
            self.assertEqual(rec.frames("take", 10, 2, 2, settings=settings), 0)
        command = run.call_args.args[0]
        self.assertEqual(command[1], str(self.root / "tools/look.py"))
        self.assertEqual(command[2], str(settings.output("take") / "review.mkv"))
        self.assertEqual(command[command.index("-o") + 1], str(settings.output("take") / "stills/gf0000010"))
        self.assertEqual(command[-6:], ["--at", "0.850", "--at", "1.050", "--at", "1.250"])
        final = self.settings(operation="finalize")
        with patch.object(rec.subprocess, "run", return_value=Mock(returncode=0, stdout="2.5")) as run:
            self.assertEqual(rec.media_duration(self.root / "raw.mkv", settings=final), 2.5)
            self.assertEqual(run.call_args.args[0][0], str(self.root / "tools/probe.exe"))
            rec.run_ffmpeg(["-i", "raw.mkv", "review.mkv"], self.root, settings=final)
            self.assertEqual(run.call_args.args[0], [str(self.root / "tools/video.exe"),
                "-hide_banner", "-loglevel", "error", "-y", "-i", "raw.mkv", "review.mkv"])

    def test_explicit_python_arguments_are_validated_and_match_provenance(self):
        settings = self.settings()
        window = MagicMock(); window.bounds = (0, 0, 640, 480)
        window.__enter__.return_value = window
        with patch.object(rec, "_win32", return_value=(Mock(), Mock())), \
                patch.object(rec, "game_pid", return_value=7), \
                patch.object(rec, "client_rect", return_value=window.bounds), \
                patch.object(rec, "find_window", return_value=10), \
                patch.object(rec, "RecordingWindow", return_value=window), \
                patch.object(rec, "ProcessWatch"), \
                patch.object(rec, "_record_capture", return_value=0) as capture:
            explicit = self.root / "explicit"
            self.assertEqual(rec.record("direct", 25, 2.5, explicit, settings=settings), 0)
        bound = capture.call_args.kwargs["settings"]
        self.assertEqual((bound.fps, bound.max_seconds, bound.game_dir), (25, 2.5, explicit))
        self.assertEqual(bound.provenance()["values"]["recording.max_seconds"], 2.5)
        self.assertEqual((settings.fps, settings.max_seconds), (60, 900.0))

    def test_review_operations_ignore_unused_legacy_capture_environment(self):
        for operation in ("finalize", "frames"):
            try:
                settings = rec.resolve_settings(self.load(), operation=operation,
                                               environ={"BAG2JP_FFMPEG_WGC": "\0"})
            except pc.ConfigError as error:
                self.fail(f"unused capture environment blocked {operation}: {error}")
            self.assertEqual(settings.config.values["tools.ffmpeg_wgc"], self.root / "tools/wgc.exe")

    def test_relative_cli_and_environment_paths_keep_the_callers_cwd(self):
        cwd = self.root / "caller"; cwd.mkdir()
        (cwd / "tools").mkdir(); (cwd / "tools/wgc.exe").write_bytes(b"different owned helper")
        with working_directory(cwd):
            settings = rec.resolve_settings(self.load(), environ={"BAG2JP_FFMPEG_WGC": "tools/wgc.exe"},
                                            game_dir=Path("source"))
        self.assertEqual(settings.game_dir, cwd / "source")
        self.assertEqual(rec.resolve_capture_backend("wgc", settings=settings),
                         ("wgc", str(cwd / "tools/wgc.exe")))

    def test_selected_overlay_reaches_loader_and_bad_direct_types_fail_before_effects(self):
        with patch.object(rec, "load_config", return_value=self.load()) as load, \
                patch.object(rec, "record", return_value=0):
            self.assertEqual(rec.main(["--local-config", str(self.local), "record", "--tag", "fresh"]), 0)
            load.assert_called_once_with(local_config=self.local)
        settings = self.settings(fps=1, max_seconds=1)
        with patch.object(rec, "_win32", side_effect=AssertionError("before effects")):
            for fps, seconds in ((True, 1), (1, True), (0, 1), (1, float("nan"))):
                with self.subTest(fps=fps, seconds=seconds), self.assertRaises(pc.ConfigError):
                    rec.record("invalid", fps, seconds, settings.game_dir, settings=settings)

    def test_tools_are_required_to_be_files_only_when_the_operation_uses_them(self):
        for name in ("video.exe", "probe.exe", "font.ttf", "look.py"):
            path = self.root / "tools" / name
            path.unlink()
            with self.subTest(name=name), self.assertRaises(pc.ConfigError):
                self.settings(operation="frames" if name == "look.py" else "finalize")
            path.write_bytes(b"owned fixture")

    def test_finalize_copies_effective_font_without_interpolating_its_host_path(self):
        settings = self.settings(operation="finalize")
        font = self.root / "tools/font.ttf"; font.write_bytes(b"distinct selected font")
        out = settings.output("take"); out.mkdir(parents=True)
        (out / "session.json").write_text('{"rect":[0,0,640,480]}', encoding="utf-8")
        (out / "events.csv").write_text('', encoding="utf-8")
        clock = Mock(); clock.summary.return_value = {"observed":10, "dropped_late":0,
            "jitter_p99_ms":0, "fps":60, "stalls":[]}
        with patch.object(rec, "load_clock", return_value=(clock, 0)), \
                patch.object(rec, "write_labels"), patch.object(rec, "gates", return_value=["fixture"]), \
                patch.object(rec, "run_ffmpeg") as run:
            self.assertEqual(rec.finalize("take", settings=settings), rec.EXIT_REJECTED)
        self.assertTrue((out / "clock-font.ttf").is_file())
        self.assertEqual((out / "clock-font.ttf").read_bytes(), b"distinct selected font")
        self.assertEqual(run.call_count, 2)
        for call in run.call_args_list:
            argv = call.args[0]
            graph = argv[argv.index("-filter_complex") + 1]
            self.assertIn("fontfile='clock-font.ttf'", graph)
            self.assertNotIn(str(font), graph)
            self.assertIs(call.kwargs.get("settings"), settings)
        manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
        self.assertIn("finalize_configuration", manifest)
        self.assertEqual(manifest["finalize_configuration"]["values"]["tools.recording_font"], str(font))
