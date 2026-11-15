"""Host regression for bag2_record.py alignment math and finalize, without a game."""
import json
import itertools
import math
import shutil
import struct
import subprocess
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import Mock, patch

from tools.test import bag2_record as rec
from tools.test.recording_window import RecordingWindow
from tools.test.test_recording_window import FakeWindows
from tools.test.recording_settings_fixture import recorder_settings

START = 1794469436.698643     # a real gdigrab wall-clock stamp
PERIOD = 1.0 / 59.94
ORIGIN = START - 1000 * PERIOD  # game frame 1000 is on screen when the video starts
RATE = 44100


def clock_rows(first: int, last: int, jitter_ms: float = 0.0) -> list[tuple[float, int]]:
    """Heartbeat rows every 6 frames, as the debug plugin writes them."""
    return [(ORIGIN + PERIOD * f + (jitter_ms / 1000.0) * (1 if (f // 6) % 2 else -1), f)
            for f in range(first, last, 6)]


def linear_sync(first: int, last: int) -> list[tuple[int, int]]:
    """Sync pairs of an audio dump that started at game frame `first`."""
    return [(f, round((f - first) * PERIOD * RATE)) for f in range(first, last)]


REAL_CHUNKS = (693, 777, 936, 534, 1230, 240)   # per-vblank increments seen in rec-smoke-3


def chunked_sync(first: int, last: int, chunks: tuple[int, ...]) -> list[tuple[int, int]]:
    """Sync pairs of a dump that writes `chunks` samples per vblank in rotation."""
    pairs, total = [], 0
    for f in range(first, last):
        pairs.append((f, total))
        total += chunks[(f - first) % len(chunks)]
    return pairs


class WindowCaptureTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.settings = recorder_settings(Path(temporary.name))

    def test_process_audio_option_starts_before_video_and_stops_after_video(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / rec.GAME_EXE).write_bytes(b"owned image")
            order = []
            helper, child, watch, window, tail = Mock(), Mock(), Mock(), Mock(), Mock()
            window.key = "window-token"
            helper.target.identity = {"pid": 700, "path": str(root / rec.GAME_EXE), "creation_filetime": "123"}
            helper.stop.side_effect = lambda: order.append("audio-stop") or {"helper_exit": 0}
            child.returncode = 0
            tail.lines.return_value = []
            settings = recorder_settings(root)
            with patch.object(rec, "Tail", return_value=tail), \
                    patch.object(rec, "ProcessAudio", create=True) as backend, \
                    patch.object(rec.subprocess, "Popen", side_effect=lambda *a, **k: order.append("video-start") or child), \
                    patch.object(rec, "stop_ffmpeg", side_effect=lambda *a, **k: order.append("video-stop") or ""), \
                    patch.object(rec, "copy_audio", return_value=[]), \
                    patch.object(rec.time, "time", side_effect=itertools.count(1000, 0.6).__next__):
                backend.start.side_effect = lambda *a, **k: order.append("audio-start") or helper
                try:
                    rec._record_capture("native", 60, 0.1, root, 700, (0, 0, 640, 480),
                                        window, watch, audio_backend="process", settings=settings)
                except TypeError as error:
                    self.fail(f"process audio opt-in is not wired: {error}")
            self.assertEqual(order, ["audio-start", "video-start", "video-stop", "audio-stop"])
            session = json.loads((settings.recordings / "native/session.json").read_text())
            self.assertEqual(session["audio_source"], "process")
            self.assertEqual(session["process_audio"]["identity"]["pid"], 700)

    def test_real_capture_loop_marks_exit_cancellation_and_shutdown_failure_invalid(self) -> None:
        for failure in ("exit", "interrupt", "shutdown-interrupt"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / rec.GAME_EXE).write_bytes(b"explicit unit-test executable identity")
                process, watch, window = Mock(), Mock(), Mock()
                process.returncode = None
                process.poll.side_effect = lambda: process.returncode
                process.kill.side_effect = lambda: setattr(process, "returncode", -9)
                calls = 0

                def finish(timeout=None):
                    nonlocal calls
                    calls += 1
                    if failure == "shutdown-interrupt" and calls == 1:
                        raise KeyboardInterrupt()
                    process.returncode = 0 if process.returncode is None else process.returncode

                process.wait.side_effect = finish
                watch.alive.return_value = failure != "exit"
                tail = Mock()
                tail.lines.return_value = []
                settings = recorder_settings(root)
                with patch.object(rec.subprocess, "Popen", return_value=process), \
                        patch.object(rec, "Tail", return_value=tail), \
                        patch.object(rec, "read_heartbeat", return_value=100), \
                        patch.object(rec.time, "time", side_effect=itertools.count(1000, 0.6).__next__), \
                        patch.object(rec.time, "sleep", side_effect=KeyboardInterrupt()):
                    code = rec._record_capture("capture", 60, 2, root, 700,
                                               (0, 0, 640, 480), window, watch, settings=settings)
                self.assertEqual(code, rec.EXIT_REJECTED)
                session = json.loads((settings.recordings / "capture/session.json").read_text())
                self.assertTrue(session.get("capture_error"))
                self.assertEqual(session["recording_state"], "restoring")
                self.assertFalse(session["window_guard"]["passed"])
                self.assertIsNotNone(process.poll())

    def test_stop_kills_child_before_propagating_repeated_cancellation(self) -> None:
        process = Mock()
        process.returncode = None
        process.poll.side_effect = lambda: process.returncode
        process.wait.side_effect = [KeyboardInterrupt(), KeyboardInterrupt(), None]
        def killed():
            process.returncode = -9
        process.kill.side_effect = killed
        with self.assertRaises(KeyboardInterrupt):
            rec.stop_ffmpeg(process, Mock(), settings=self.settings)
        process.kill.assert_called_once()
        self.assertEqual(process.poll(), -9)

    def test_stop_detects_window_loss_while_ffmpeg_is_still_finishing(self) -> None:
        process = Mock()
        process.returncode = None
        process.poll.side_effect = lambda: process.returncode
        process.kill.side_effect = lambda: setattr(process, "returncode", -9)
        waits = 0
        def finish(timeout=None):
            nonlocal waits
            waits += 1
            if waits == 1:
                raise subprocess.TimeoutExpired("ffmpeg", 0.1)
            process.returncode = 0
        process.wait.side_effect = finish
        check = Mock(side_effect=[None, None, RuntimeError("covered during shutdown")])
        with self.assertRaisesRegex(RuntimeError, "covered during shutdown"):
            rec.stop_ffmpeg(process, check, settings=self.settings)
        process.kill.assert_called_once()

    def test_recorder_pins_capture_only_and_restores_after_success_or_failure(self) -> None:
        for fail in (False, True):
            with self.subTest(fail=fail), tempfile.TemporaryDirectory() as temporary:
                api, watch, user = FakeWindows(), Mock(), Mock()
                root = Path(temporary)

                def capture(*args, **kwargs):
                    self.assertTrue(api.pinned)
                    self.assertEqual(api.front, 100)
                    if fail:
                        raise RuntimeError("capture startup failed")
                    folder = settings.recordings / "capture"
                    folder.mkdir()
                    (folder / "session.json").write_text("{}", encoding="utf-8")
                    return 0

                settings = recorder_settings(root)
                with patch.object(rec, "_win32", return_value=(user, Mock())), \
                        patch.object(rec, "game_pid", return_value=700), \
                        patch.object(rec, "client_rect", return_value=api.bounds), \
                        patch.object(rec, "find_window", return_value=100), \
                        patch.object(rec, "on_primary", return_value=True), \
                        patch.object(rec, "ProcessWatch", return_value=watch), \
                        patch.object(rec, "_record_capture", side_effect=capture), \
                        patch.object(rec, "RecordingWindow", side_effect=lambda hwnd, pid:
                                     RecordingWindow(hwnd, pid, api=api)):
                    self.assertEqual(rec.record("capture", 60, 2, root, capture_backend="gdigrab", settings=settings),
                                     rec.EXIT_REJECTED if fail else 0)
                self.assertFalse(api.pinned)
                self.assertEqual(api.front, 200)
                watch.close.assert_called_once()
                if not fail:
                    session = json.loads((settings.recordings / "capture/session.json").read_text())
                    self.assertTrue(session["window_guard"]["passed"])

    def test_resolve_capture_backend_prefers_wgc_in_auto_and_falls_back(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            wgc_exe = Path(directory) / "ffmpeg.exe"
            wgc_exe.write_bytes(b"stub")
            settings = recorder_settings(Path(directory), environ={"BAG2JP_FFMPEG_WGC": str(wgc_exe)})
            self.assertEqual(rec.resolve_capture_backend("auto", settings=settings), ("wgc", str(wgc_exe)))
            self.assertEqual(rec.resolve_capture_backend("wgc", settings=settings), ("wgc", str(wgc_exe)))
            self.assertEqual(rec.resolve_capture_backend("gdigrab", settings=settings),
                             ("gdigrab", str(settings.tool("ffmpeg_review"))))
            missing = Path(directory) / "absent.exe"
            settings = recorder_settings(Path(directory), environ={"BAG2JP_FFMPEG_WGC": str(missing)})
            self.assertEqual(rec.resolve_capture_backend("auto", settings=settings),
                             ("gdigrab", str(settings.tool("ffmpeg_review"))))
            with self.assertRaises(RuntimeError):
                rec.resolve_capture_backend("wgc", settings=settings)

    def test_record_wgc_allows_covered_window_and_uses_gfxcapture_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / rec.GAME_EXE).write_bytes(b"wgc fixture")
            wgc_exe = root / "ffmpeg-wgc.exe"
            wgc_exe.write_bytes(b"stub")
            api, watch, user = FakeWindows(), Mock(), Mock()
            api.cover = True
            api.bounds = (-50, 20, 640, 480)
            process = Mock()
            process.poll.return_value = None
            process.returncode = 0
            tail = Mock()
            tail.lines.return_value = []
            seen_commands: list[list[str]] = []

            def fake_popen(cmd, **kwargs):
                seen_commands.append(cmd)
                return process

            settings = recorder_settings(root, environ={"BAG2JP_FFMPEG_WGC": str(wgc_exe)})
            with patch.object(rec, "logger"), \
                    patch.object(rec, "_win32", return_value=(user, Mock())), \
                    patch.object(rec, "game_pid", return_value=700), \
                    patch.object(rec, "client_rect", return_value=api.bounds), \
                    patch.object(rec, "find_window", return_value=100), \
                    patch.object(rec, "on_primary", return_value=False), \
                    patch.object(rec, "ProcessWatch", return_value=watch), \
                    patch.object(rec.subprocess, "Popen", side_effect=fake_popen), \
                    patch.object(rec, "Tail", return_value=tail), \
                    patch.object(rec, "stop_ffmpeg", return_value=""), \
                    patch.object(rec, "copy_audio", return_value=[]), \
                    patch.object(rec, "read_heartbeat", side_effect=list(range(100, 400, 6))), \
                    patch.object(rec.time, "sleep"), \
                    patch.object(rec.time, "time", side_effect=[1000.0 + i * 0.05 for i in range(120)]), \
                    patch.object(rec, "RecordingWindow", side_effect=lambda hwnd, pid, require_uncovered=True:
                                 RecordingWindow(hwnd, pid, api=api, require_uncovered=require_uncovered)):
                result = rec.record("wgc_capture", 60, 2.0, root, settings=settings)
            self.assertEqual(result, 0)
            self.assertFalse(api.pinned)
            self.assertEqual(api.front, 200)
            self.assertEqual(api.calls, [])
            self.assertFalse(api.tags)
            self.assertEqual(len(seen_commands), 1)
            cmd = seen_commands[0]
            self.assertEqual(cmd[0], str(wgc_exe))
            self.assertIn("lavfi", cmd)
            self.assertIn("gfxcapture=hwnd=100:max_framerate=60:capture_cursor=0", cmd)
            self.assertIn("hwdownload,format=bgra,crop=trunc(iw/2)*2:trunc(ih/2)*2:0:0", cmd)
            self.assertIn("-use_wallclock_as_timestamps", cmd)
            session = json.loads((settings.recordings / "wgc_capture/session.json").read_text(encoding="utf-8"))
            self.assertEqual(session["capture_backend"], "wgc")
            self.assertEqual(session["recording_state"], "closed")
            self.assertTrue(session["window_guard"]["passed"])
            self.assertFalse(session["window_guard"]["require_uncovered"])

    def test_record_wgc_refuses_missing_binary_and_rejects_resize_mid_capture(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            missing = root / "missing-wgc.exe"
            settings = recorder_settings(root, environ={"BAG2JP_FFMPEG_WGC": str(missing)})
            with patch.object(rec, "logger"):
                self.assertEqual(rec.record("wgc_missing", 60, 1.0, root, capture_backend="wgc", settings=settings),
                                 rec.EXIT_REJECTED)
            (root / rec.GAME_EXE).write_bytes(b"wgc resize fixture")
            wgc_exe = root / "ffmpeg-wgc.exe"
            wgc_exe.write_bytes(b"stub")
            api, watch, user = FakeWindows(), Mock(), Mock()
            process = Mock()
            process.poll.return_value = None
            process.returncode = 0
            tail = Mock()
            tail.lines.return_value = []

            def resize_after_two_beats(*_args):
                calls = getattr(resize_after_two_beats, "n", 0) + 1
                resize_after_two_beats.n = calls
                if calls >= 3:
                    api.bounds = (0, 0, 800, 600)
                return 100 + calls * 6

            settings = recorder_settings(root, environ={"BAG2JP_FFMPEG_WGC": str(wgc_exe)})
            with patch.object(rec, "logger"), \
                    patch.object(rec, "_win32", return_value=(user, Mock())), \
                    patch.object(rec, "game_pid", return_value=700), \
                    patch.object(rec, "client_rect", return_value=api.bounds), \
                    patch.object(rec, "find_window", return_value=100), \
                    patch.object(rec, "ProcessWatch", return_value=watch), \
                    patch.object(rec.subprocess, "Popen", return_value=process), \
                    patch.object(rec, "Tail", return_value=tail), \
                    patch.object(rec, "stop_ffmpeg", return_value=""), \
                    patch.object(rec, "copy_audio", return_value=[]), \
                    patch.object(rec, "read_heartbeat", side_effect=resize_after_two_beats), \
                    patch.object(rec.time, "sleep"), \
                    patch.object(rec.time, "time", side_effect=[1000.0 + i * 0.25 for i in range(40)]), \
                    patch.object(rec, "RecordingWindow", side_effect=lambda hwnd, pid, require_uncovered=True:
                                 RecordingWindow(hwnd, pid, api=api, require_uncovered=require_uncovered)):
                result = rec.record("wgc_resize", 60, 2.0, root, capture_backend="wgc", settings=settings)
            self.assertEqual(result, rec.EXIT_REJECTED)
            session = json.loads((settings.recordings / "wgc_resize/session.json").read_text(encoding="utf-8"))
            self.assertEqual(session["capture_error"], "capture window resized")
            self.assertFalse(session["window_guard"]["passed"])


class ClockTest(unittest.TestCase):
    def test_producer_probe_is_retained_after_backward_wall_clock_step(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / 'capture'; output.mkdir()
            source = root / 'bag2jp_clock_probe.csv'
            source.write_bytes(b'frame,samples,producer_ticks,producer_hz\n6,3675,120,1000\n')
            rec.os.utime(source, (900, 900))
            self.assertTrue(rec.copy_clock_probe(root, output, None))
            self.assertEqual((output / source.name).read_bytes(), source.read_bytes())

    def test_producer_probe_copy_is_optional_fresh_and_reports_io_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / 'capture'; output.mkdir()
            source = root / 'bag2jp_clock_probe.csv'
            self.assertFalse(rec.copy_clock_probe(root, output, None))
            source.write_bytes(b'frame,samples,producer_ticks,producer_hz\n')
            initial = rec.clock_probe_identity(root)
            with patch.object(rec, 'logger') as log:
                self.assertTrue(rec.copy_clock_probe(root, output, initial))
                log.warning.assert_called_once()  # Retained, but activity is ambiguous.
            source.write_bytes(source.read_bytes() + b'6,3675,120,1000\n')
            rec.os.utime(source, (1, 1))  # Changed producer file, backwards civil clock.
            self.assertNotEqual(rec.clock_probe_identity(root), initial)
            self.assertTrue(rec.copy_clock_probe(root, output, initial))
            self.assertEqual((output / source.name).read_bytes(), source.read_bytes())
            with patch.object(rec.shutil, 'copy2', side_effect=PermissionError('fixture denied')), \
                    patch.object(rec, 'logger') as log:
                self.assertFalse(rec.copy_clock_probe(root, output, initial))
                log.warning.assert_called_once()

    def test_capture_writes_monotonic_wall_bracket_without_changing_heartbeat_csv(self) -> None:
        """The actual recorder loop preserves repeats and clock steps in a sidecar."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / rec.GAME_EXE).write_bytes(b'host clock fixture')
            process, window, watch = Mock(), Mock(), Mock()
            process.poll.return_value = None
            process.returncode = 0
            tail = Mock(); tail.lines.return_value = []
            settings = recorder_settings(root)
            with patch.object(rec, 'logger'), \
                    patch.object(rec.subprocess, 'Popen', return_value=process), \
                    patch.object(rec, 'Tail', return_value=tail), \
                    patch.object(rec, 'stop_ffmpeg', return_value=''), \
                    patch.object(rec, 'copy_audio', return_value=[]), \
                    patch.object(rec, 'read_heartbeat', side_effect=[100, 100, 106]), \
                    patch.object(rec.time, 'sleep'), \
                    patch.object(rec.time, 'time', side_effect=[1000,1000,1000,1000.1,1000.1,1000.6,1000.6,1002,1002]), \
                    patch.object(rec.time, 'perf_counter_ns', side_effect=[10,20,110,120,210,220]), \
                    patch.object(rec.time, 'time_ns', side_effect=[1000,1001,1100,1101,1600,1601]):
                rec._record_capture('probe', 60, 1, root, 700, (0,0,640,480), window, watch, settings=settings)
            self.assertEqual(rec.read_rows(settings.recordings / 'probe/heartbeat.csv'),
                             [['1000.000000','100'],['1000.600000','106']])
            path = settings.recordings / 'probe/clock_observations.csv'
            self.assertTrue(path.exists(), 'recorder must retain independent clocks')
            self.assertEqual(rec.read_rows(path), [
                ['frame','mono_before_ns','mono_after_ns','wall_before_ns','wall_after_ns'],
                ['100','10','20','1000','1001'], ['100','110','120','1100','1101'],
                 ['106','210','220','1600','1601']])

    def test_capture_survives_optional_observation_open_and_write_failures(self) -> None:
        original_open = Path.open
        for failure in ('none', 'open', 'header', 'write', 'close'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / rec.GAME_EXE).write_bytes(b'optional clock fixture')
                process, window, watch = Mock(), Mock(), Mock()
                process.poll.return_value = None; process.returncode = 0
                tail = Mock(); tail.lines.return_value = []
                sink = Mock()
                sink.__enter__ = Mock(return_value=sink)
                sink.__exit__ = Mock(return_value=False)
                if failure == 'header':
                    sink.write.side_effect = PermissionError('clock header denied')
                elif failure == 'write':
                    sink.write.side_effect = [1, PermissionError('clock write denied')]
                else:
                    sink.write.return_value = 1
                if failure == 'close':
                    sink.close.side_effect = PermissionError('clock flush denied')

                def opened(path: Path, *args, **kwargs):
                    if path.name == 'clock_observations.csv':
                        if failure == 'none':
                            return original_open(path, *args, **kwargs)
                        if failure == 'open':
                            raise PermissionError('clock open denied')
                        return sink
                    return original_open(path, *args, **kwargs)

                settings = recorder_settings(root)
                with patch.object(Path, 'open', opened), patch.object(rec, 'logger') as log, \
                        patch.object(rec.subprocess, 'Popen', return_value=process), \
                        patch.object(rec, 'Tail', return_value=tail), \
                        patch.object(rec, 'stop_ffmpeg', return_value=''), \
                        patch.object(rec, 'copy_audio', return_value=[]), \
                        patch.object(rec, 'read_heartbeat', side_effect=[None, 100, 106]), \
                        patch.object(rec.time, 'sleep'), \
                        patch.object(rec.time, 'time', side_effect=[1000,1000,1000,1000.1,1000.1,1000.6,1000.6,1002,1002]):
                    try:
                        result = rec._record_capture('probe', 60, 1, root, 700, (0,0,640,480), window, watch, settings=settings)
                    except OSError as error:
                        self.fail(f'optional sidecar aborted capture: {error}')
                session = json.loads((settings.recordings / 'probe/session.json').read_text())
                self.assertNotIn('capture_error', session)
                self.assertEqual(result, rec.EXIT_REJECTED)  # Only the ordinary too-short clock gate.
                self.assertEqual(rec.read_rows(settings.recordings / 'probe/heartbeat.csv'),
                                 [['1000.100000','100'], ['1000.600000','106']])
                if failure == 'none':
                    observations = rec.read_rows(settings.recordings / 'probe/clock_observations.csv')
                    self.assertEqual([row[0] for row in observations[1:]], ['', '100', '106'])
                    self.assertEqual(len(observations), 4)
                else:
                    self.assertTrue(log.warning.called)

    def test_ffmpeg_start_is_read_from_gdigrab_and_lavfi_wallclock_banners(self) -> None:
        log = ("Input #0, gdigrab, from 'desktop':\n"
               "  Duration: N/A, start: 1794469436.698643, bitrate: 3945 kb/s\n")
        self.assertAlmostEqual(rec.parse_ffmpeg_start(log), START, places=6)
        lavfi_log = ("Input #0, lavfi, from 'gfxcapture=hwnd=100:max_framerate=60:capture_cursor=0':\n"
                     "  Duration: N/A, start: 1794469436.698643, bitrate: N/A\n")
        self.assertAlmostEqual(rec.parse_ffmpeg_start(lavfi_log), START, places=6)
        with self.assertRaises(ValueError):
            rec.parse_ffmpeg_start("Input #0, gdigrab\n  Duration: N/A, start: 0.000000\n")
        with self.assertRaises(ValueError):
            rec.parse_ffmpeg_start("Input #0, lavfi\n  Duration: N/A, start: 0.000000\n")
        with self.assertRaises(ValueError):
            rec.parse_ffmpeg_start("Input #0, lavfi\n")

    def test_heartbeat_parser_rejects_torn_snapshots(self) -> None:
        self.assertEqual(rec.parse_heartbeat("0012348 3/1/0          \n"), 12348)
        self.assertIsNone(rec.parse_heartbeat(""))
        self.assertIsNone(rec.parse_heartbeat("00123"))

    def test_clock_recovers_rate_and_reports_jitter(self) -> None:
        clock = rec.HeartbeatClock(clock_rows(900, 2000, jitter_ms=4.0))
        self.assertAlmostEqual(clock.summary()["fps"], 59.94, places=1)
        self.assertLess(abs(clock.frame_of(START) - 1000), 0.5)
        self.assertLess(clock.jitter_p99_ms, 9.0)
        self.assertEqual(clock.stalls, [])
        self.assertEqual(clock.dropped, set())

    def test_late_stamp_is_dropped_but_counted(self) -> None:
        rows = clock_rows(900, 2000)
        late = list(range(10, len(rows) - 1, 25))
        for i in late:                               # a stalled poll sees a stamp late
            rows[i] = (rows[i][0] + 0.080, rows[i][1])
        clock = rec.HeartbeatClock(rows)
        self.assertEqual(clock.dropped, set(late))
        self.assertEqual(clock.stalls, [])
        for frame in (1000, 1500, 1990):
            self.assertAlmostEqual(clock.wall_of(frame), ORIGIN + PERIOD * frame, delta=0.002)

    def test_pause_near_the_end_is_kept_confined_and_reported(self) -> None:
        # A 2 s game pause after frame 5802: the frames after it are shown 2 s later.
        rows = [(w + (2.0 if f > 5802 else 0.0), f) for w, f in clock_rows(0, 6000)]
        clock = rec.HeartbeatClock(rows)
        self.assertEqual(len(clock.stalls), 1)
        self.assertEqual(clock.stalls[0]["after_frame"], 5802)
        self.assertAlmostEqual(clock.stalls[0]["seconds"], 2.0, places=2)
        self.assertEqual(clock.dropped, set())
        self.assertAlmostEqual(clock.wall_of(5900), ORIGIN + PERIOD * 5900 + 2.0, delta=0.002)
        self.assertAlmostEqual(clock.wall_of(3000), ORIGIN + PERIOD * 3000, delta=0.002)
        # One audio offset cannot place both sides of the pause: the gate says so.
        audio = rec.audio_placement(clock, linear_sync(0, 6000), START)
        self.assertGreater(audio["dropped"], 0.02 * audio["pairs"])   # frames after the pause
        self.assertTrue(any("pause" in r for r in rec.gates(clock, audio)))

    def test_chunked_dump_at_the_game_rate_is_placed_without_rejection(self) -> None:
        # Real dump: 735 samples per vblank on average, in uneven chunks (measured
        # in rec-smoke-3), i.e. ~44056 Hz against wall time at 59.94 fps.
        clock = rec.HeartbeatClock(clock_rows(900, 2100, jitter_ms=4.0))
        audio = rec.audio_placement(clock, chunked_sync(400, 2100, REAL_CHUNKS), START)
        self.assertEqual(audio["rate_hz"], round(735 / PERIOD))
        self.assertAlmostEqual(audio["offset_s"], -600 * PERIOD, delta=0.003)
        self.assertGreater(audio["residual_p99_ms"], 5.0)     # single pairs scatter...
        self.assertLess(audio["window_max_ms"], 5.0)          # ...windows do not
        self.assertEqual(audio["dropped"], 0)
        self.assertEqual(rec.gates(clock, audio), [])

    def test_unusable_heartbeats_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            rec.HeartbeatClock(clock_rows(0, 30))
        stale_first = [(START - 300.0, 50000)] + clock_rows(900, 2000)
        with self.assertRaisesRegex(ValueError, "did not increase"):
            rec.HeartbeatClock(stale_first)
        with self.assertRaises(ValueError):
            rec.HeartbeatClock([(START + i, 5) for i in range(20)])

    def test_audio_placement_uses_only_recorded_frames(self) -> None:
        clock = rec.HeartbeatClock(clock_rows(900, 2000))
        sync = linear_sync(400, 2000)            # dump began before the video
        sync[700] = (sync[700][0], sync[700][1] + 9000)   # one torn pair is absorbed
        audio = rec.audio_placement(
            clock, rec.parse_sync_log("\n".join(f"{f} {s}" for f, s in sync) + "\ntorn"), START)
        self.assertAlmostEqual(audio["offset_s"], -600 * PERIOD, delta=0.002)
        self.assertEqual(audio["rate_hz"], RATE)
        self.assertEqual(audio["dropped"], 1)
        self.assertEqual(rec.gates(clock, audio), [])
        with self.assertRaisesRegex(ValueError, "another session"):
            rec.audio_placement(clock, linear_sync(1, 300), START)   # relaunched game

    def test_gates_accept_clean_and_reject_missing_audio(self) -> None:
        clock = rec.HeartbeatClock(clock_rows(900, 2000))
        good = {"offset_s": 0.0, "rate_hz": 44056, "pairs": 1000, "dropped": 0,
                "residual_p99_ms": 20.0, "window_max_ms": 2.0}
        self.assertEqual(rec.gates(clock, good), [])
        self.assertTrue(rec.gates(clock, {"error": "no audio dump copied"}))
        self.assertTrue(rec.gates(clock, {**good, "rate_hz": 45000}))
        self.assertTrue(rec.gates(clock, {**good, "dropped": 6}))
        sparse = rec.HeartbeatClock(clock_rows(900, 2000)[::3])
        self.assertTrue(any("missed" in r for r in rec.gates(sparse, good)))

    def test_filters_and_labels(self) -> None:
        fit = "apad=whole_dur=4.000000,atrim=end=4.000000"
        self.assertEqual(rec.audio_filter(0.25, 4.0), f"adelay=250:all=1,{fit}")
        self.assertEqual(rec.audio_filter(-1.5, 4.0), f"atrim=start=1.500000,asetpts=PTS-STARTPTS,{fit}")
        self.assertEqual(rec.audio_filter(0.25, 4.0, 44056),
                         f"asetrate=44056,aresample=44100,adelay=250:all=1,{fit}")
        self.assertEqual(rec.ass_time(3725.456), "1:02:05.46")
        clock = rec.HeartbeatClock(clock_rows(900, 2000))
        slots = {f: (s, e) for s, e, f in rec.label_events(clock, START)}
        self.assertNotIn(998, slots)                  # ends before the video starts
        self.assertAlmostEqual(slots[1060][0], 60 * PERIOD, delta=0.001)
        self.assertAlmostEqual(slots[1060][1] - slots[1060][0], PERIOD, delta=0.001)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
class FinalizeTest(unittest.TestCase):
    """Synthetic recordings whose video starts at game frame 1000, with beeps written
    into the game audio at known game frames."""

    def test_process_audio_finalize_preserves_float_samples_and_never_uses_dump(self) -> None:
        from tools.test.test_process_audio_capture import fixture, write_journal, IDENTITY, TOKEN, FILETIME
        out = self.make_recording("native-float", 1, linear_sync(940, 1240), (1060,))
        rows = fixture(out)
        desired_filetime = round((START - 0.25) * 10000000) + 116444736000000000
        for row in rows:
            if row["kind"] == "anchor":
                row["utc_filetime"] = str(int(row["utc_filetime"]) - FILETIME + desired_filetime)
        write_journal(out, rows)
        session = {"rect": [0, 0, 320, 240], "audio_source": "process",
                   "pid": IDENTITY["pid"], "recording_state": "closed", "ffmpeg_exit": 0,
                   "window_guard": {"passed": True},
                   "process_audio": {"identity": IDENTITY, "token": TOKEN, "helper_exit": 0}}
        (out / "session.json").write_text(json.dumps(session))
        with patch.object(rec, "audio_placement", side_effect=AssertionError("must not use mixer dump")):
            self.assertEqual(rec.finalize(out.name, settings=self.settings), 0)
        manifest = json.loads((out / "manifest.json").read_text())
        self.assertEqual(manifest["audio_source"], "process")
        probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
                                "stream=codec_name", "-of", "csv=p=0", str(out / "review.mkv")],
                               capture_output=True, text=True, check=True)
        self.assertEqual(probe.stdout.strip(), "pcm_f32le")
        decoded = subprocess.run(["ffmpeg", "-v", "error", "-i", str(out / "review.mkv"),
                                  "-map", "0:a:0", "-f", "f32le", "-"], capture_output=True, check=True).stdout
        expected = (out / "process_audio.f32").read_bytes()[11025*8:55125*8]
        self.assertEqual(decoded, expected)
        # Even a valid diagnostic dump must not rescue a failed native journal.
        rows[-1]["clean"] = False
        write_journal(out, rows)
        self.assertEqual(rec.finalize(out.name, settings=self.settings), rec.EXIT_REJECTED)
        manifest = json.loads((out / "manifest.json").read_text())
        self.assertFalse(manifest["accepted"])

    def make_recording(self, name: str, seconds: int, sync: list[tuple[int, int]],
                       beep_frames: tuple[int, ...]) -> Path:
        out = self.settings.recordings / name
        out.mkdir()
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
                        f"testsrc=size=320x240:rate=60:duration={seconds}", "-c:v", "libx264",
                        "-qp", "0", "-preset", "ultrafast", str(out / "raw.mkv")], check=True)
        (out / "ffmpeg.log").write_text(
            f"Input #0, gdigrab, from 'desktop':\n  Duration: N/A, start: {START:.6f}, bitrate: 1 kb/s\n")
        last = sync[-1][0] + 1
        with (out / "heartbeat.csv").open("w") as handle:
            for wall, frame in clock_rows(996, last):
                handle.write(f"{wall:.6f},{frame}\n")
        with (out / "events.csv").open("w", encoding="utf-8") as handle:
            handle.write(f"{ORIGIN + PERIOD * (beep_frames[0] + 0.5):.6f},gaso_caught: slot1 published\n")
        at = dict(sync)
        pcm = bytearray(4 * (sync[-1][1] + 735))
        tone = b"".join(struct.pack("<hh", v, v) for v in
                        (int(20000 * math.sin(2 * math.pi * 1000 * i / RATE)) for i in range(2205)))
        for frame in beep_frames:
            pcm[4 * at[frame]:4 * at[frame] + len(tone)] = tone
        with wave.open(str(out / rec.AUDIO_WAV), "wb") as wav:
            wav.setnchannels(2)
            wav.setsampwidth(2)
            wav.setframerate(RATE)
            wav.writeframes(bytes(pcm))
        # Like the game, the header under-reports the data by up to one second.
        data = bytearray((out / rec.AUDIO_WAV).read_bytes())
        data[40:44] = struct.pack("<I", max(0, len(data) - 44 - 4 * RATE))
        (out / rec.AUDIO_WAV).write_bytes(bytes(data))
        (out / rec.AUDIO_SYNC).write_text("".join(f"{f} {s}\n" for f, s in sync))
        (out / "session.json").write_text(json.dumps({"rect": [0, 0, 320, 240]}))
        return out

    def beep_starts(self, path: Path) -> list[float]:
        """Video seconds at which each beep starts (end of the preceding silence)."""
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af",
             "silencedetect=noise=-30dB:d=0.02", "-f", "null", "-"],
            capture_output=True, text=True, check=True)
        ends = [float(line.split("silence_end: ")[1].split()[0])
                for line in result.stderr.splitlines() if "silence_end" in line]
        last = self.duration(path) - 0.05      # silencedetect also closes a silence at EOF
        return [e for e in ends if e < last]

    def duration(self, path: Path) -> float:
        probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True)
        return float(probe.stdout)

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2] / "_work")
        self.addCleanup(self.tmp.cleanup)
        self.settings = recorder_settings(Path(self.tmp.name), operation="finalize")

    def test_finalize_aligns_beep_events_and_keeps_full_video(self) -> None:
        for audio_first in (940, 1060):            # audio started before / after the video
            with self.subTest(audio_first=audio_first):
                out = self.make_recording(f"synthetic-{audio_first}", 4,
                                          linear_sync(audio_first, 1240), (1120,))
                self.assertEqual(rec.finalize(out.name, settings=self.settings), 0)
                manifest = json.loads((out / "manifest.json").read_text())
                self.assertTrue(manifest["accepted"], manifest["rejections"])
                self.assertAlmostEqual(manifest["audio"]["offset_s"],
                                       (audio_first - 1000) * PERIOD, delta=0.002)
                events = json.loads((out / "events.json").read_text(encoding="utf-8"))
                self.assertEqual(events[0]["game_frame"], 1120)
                for name in ("owner.mp4", "review.mkv"):
                    self.assertIn(name, manifest["files"])
                    self.assertGreater(self.duration(out / name), 3.9, name)   # not cut short
                    starts = self.beep_starts(out / name)
                    self.assertTrue(starts, name)
                    self.assertAlmostEqual(starts[0], 120 * PERIOD, delta=0.02, msg=name)

    def test_finalize_rejects_failed_window_guard_despite_valid_timing(self) -> None:
        out = self.make_recording("covered", 4, linear_sync(940, 1240), (1120,))
        session = json.loads((out / "session.json").read_text())
        session["window_guard"] = {"passed": False, "error": "capture window is covered"}
        (out / "session.json").write_text(json.dumps(session), encoding="utf-8")
        self.assertEqual(rec.finalize(out.name, settings=self.settings), rec.EXIT_REJECTED)
        manifest = json.loads((out / "manifest.json").read_text())
        self.assertFalse(manifest["accepted"])
        self.assertTrue(any("visibility guard" in reason for reason in manifest["rejections"]))

    def test_pending_restoration_is_not_treated_as_a_legacy_recording(self) -> None:
        out = self.settings.recordings / "still-restoring"
        out.mkdir()
        (out / "session.json").write_text(json.dumps({"recording_state": "restoring",
                                                     "window_guard": {"passed": False}}))
        self.assertEqual(rec.finalize(out.name, settings=self.settings), rec.EXIT_REJECTED)
        self.assertFalse((out / "manifest.json").exists())

    def test_finalize_corrects_dump_rate_drift_across_a_long_take(self) -> None:
        # 731 samples per vblank in uneven chunks: the dump runs 0.65 % slow
        # against wall time. Beeps 1 s and 19 s into a 20 s take must both land.
        sync = chunked_sync(940, 2220, tuple(c - 4 for c in REAL_CHUNKS))
        out = self.make_recording("synthetic-drift", 20, sync, (1060, 2140))
        self.assertEqual(rec.finalize(out.name, settings=self.settings), 0)
        manifest = json.loads((out / "manifest.json").read_text())
        self.assertEqual(manifest["audio"]["rate_hz"], round(731 / PERIOD))
        for name in ("owner.mp4", "review.mkv"):
            starts = self.beep_starts(out / name)
            self.assertEqual(len(starts), 2, name)
            self.assertAlmostEqual(starts[0], 60 * PERIOD, delta=0.02, msg=name)
            self.assertAlmostEqual(starts[1], 1140 * PERIOD, delta=0.02, msg=name)


    def test_finalize_accepts_wgc_lavfi_session_and_records_backend_limits(self) -> None:
        out = self.make_recording("wgc-lavfi", 4, linear_sync(940, 1240), (1120,))
        (out / "ffmpeg.log").write_text(
            f"Input #0, lavfi, from 'gfxcapture=hwnd=100':\n  Duration: N/A, start: {START:.6f}, bitrate: N/A\n",
            encoding="utf-8")
        (out / "session.json").write_text(json.dumps({
            "rect": [0, 0, 320, 240],
            "capture_backend": "wgc",
            "recording_state": "closed",
            "ffmpeg_exit": 0,
            "window_guard": {"passed": True, "require_uncovered": False},
        }), encoding="utf-8")
        self.assertEqual(rec.finalize(out.name, settings=self.settings), 0)
        manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
        self.assertTrue(manifest["accepted"], manifest["rejections"])
        self.assertEqual(manifest["capture_backend"], "wgc")
        self.assertTrue(any("overlapping windows" in lim for lim in manifest["limits"]))


if __name__ == "__main__":
    unittest.main()
