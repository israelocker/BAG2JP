"""Process-audio journal, PCM and native clock contract; no game or desktop audio."""
import hashlib
import copy
import os
import json
from pathlib import Path
import struct
import tempfile
import subprocess
import sys
import time
import unittest
from unittest.mock import Mock

from tools.test import process_audio_capture as audio

IDENTITY = {"pid": 1234, "path": "D:\\Owned\\BAG2JP.exe", "creation_filetime": "133000000000000000"}
TOKEN = "test-owned-recording"
START = 1794720000.0
FILETIME = 134391936000000000  # 2026-11-15T08:00:00Z (Windows epoch)
QPC = 5000000000


def fixture(root: Path) -> list[dict]:
    """Two seconds of stereo PCM from one identity, including a native SILENT row."""
    pcm = struct.pack("<ff", 0.001, -0.001) * 44100 * 2
    # One explicit silent packet between two signals; nothing is inferred from a gap.
    pcm = pcm[:441 * 8 * 40] + bytes(441 * 8) + pcm[441 * 8 * 41:]
    (root / "process_audio.f32").write_bytes(pcm)
    rows = [{"kind": "ready", "schema": 1, "identity": IDENTITY, "token": TOKEN,
             "mode": "include_target_tree", "format": {"rate_hz": 44100, "channels": 2,
                                                         "sample_format": "f32le"}}]
    for i in range(201):
        if i % 50 == 0:
            rows.append({"kind": "anchor", "qpc_before": str(QPC + i*100000 - 10),
                         "qpc_after": str(QPC + i*100000 + 10), "frequency": "10000000",
                         "utc_filetime": str(FILETIME + i*100000)})
        if i < 200:
            rows.append({"kind": "packet", "seq": i, "offset_bytes": i*441*8,
                         "frames": 441, "flags": 2 if i == 40 else 0,
                         "qpc_100ns": str(QPC + i*100000), "device_position": "0"})
    rows.append({"kind": "terminal", "clean": True, "reason": "STOP", "token": TOKEN,
                 "target_alive": True, "frames": 88200, "packets": 200,
                 "bytes": len(pcm), "pcm_sha256": hashlib.sha256(pcm).hexdigest()})
    write_journal(root, rows)
    return rows


def write_journal(root: Path, rows: list[dict]) -> None:
    """Serialize the exact helper protocol, with a complete final line."""
    (root / "process_audio.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


class ProcessAudioTest(unittest.TestCase):
    def test_abort_reaps_on_broken_ipc_and_repeated_cancellation(self) -> None:
        for failure in ("pipe", "cancel", "close-cancel"):
            with self.subTest(failure=failure):
                helper = audio.ProcessAudio()
                child = Mock()
                child.returncode, child.stdout, child.stdin.closed = None, None, False
                child.poll.side_effect = lambda: child.returncode
                child.kill.side_effect = lambda: setattr(child, "returncode", -9)
                interrupts = [KeyboardInterrupt(), SystemExit()] if failure == "cancel" else []

                def wait(timeout=None):
                    if interrupts:
                        raise interrupts.pop(0)
                    if child.returncode is None:
                        child.returncode = 0
                    return child.returncode

                child.wait.side_effect = wait
                if failure != "cancel":
                    child.stdin.close.side_effect = (BrokenPipeError("closed reader") if failure == "pipe"
                                                     else KeyboardInterrupt())
                helper.child, helper.target, helper.parent, helper.log = child, None, None, None
                helper.abort()
                self.assertIsNotNone(child.poll(), "helper abandoned while active")
                child.kill.assert_called()

    def test_fractional_native_drift_or_uncertain_tail_cannot_claim_full_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = fixture(root)
            for case in ("fraction", "drift", "clock-start", "clock-end"):
                rows = copy.deepcopy(baseline)
                if case == "drift":
                    for row in rows:
                        if row["kind"] == "packet":
                            row["qpc_100ns"] = str(QPC + row["seq"] * 99800)
                if case.startswith("clock"):
                    for row in rows:
                        if row["kind"] == "anchor":
                            row["qpc_before"] = str(int(row["qpc_before"]) - 9990)
                            row["qpc_after"] = str(int(row["qpc_after"]) + 9990)
                write_journal(root, rows)
                start, duration = {"fraction": (START + .25 + .4/44100, 1.75),
                                   "drift": (START + .001, 1.998),
                                   "clock-start": (START + .0005, 1.5),
                                   "clock-end": (START + .25, 1.7495)}[case]
                with self.subTest(case=case), self.assertRaisesRegex(ValueError, "cover"):
                    audio.validate_capture(root, IDENTITY, TOKEN, start, duration, 1/60)

    def test_native_qpc_to_utc_places_float_pcm_and_covers_full_video(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture(root)
            result = audio.validate_capture(root, IDENTITY, TOKEN, START + 0.25, 1.5, 1/60)
            self.assertEqual(result.get("trim_start_sample"), 11025)
            self.assertEqual(result["trim_end_sample"], 77175)
            self.assertEqual(result["frames"], 88200)
            self.assertEqual(result["dropped"], 0)
            self.assertEqual(result["audio_source"], "process")

    def test_identity_format_token_and_terminal_fail_closed(self) -> None:
        changes = [(0, "identity", {**IDENTITY, "pid": 5678}), (0, "token", "other"),
                   (0, "mode", "exclude_target_tree"), (0, "schema", 2),
                   (0, "format", {"rate_hz": 48000}), (-1, "clean", False),
                   (-1, "target_alive", False), (-1, "reason", "EOF"), (-1, "token", "other"),
                   (-1, "frames", 1), (-1, "packets", 1), (-1, "bytes", 1),
                   (-1, "pcm_sha256", "0"*64)]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = fixture(root)
            for index, key, value in changes:
                rows = copy.deepcopy(baseline)
                rows[index][key] = value
                write_journal(root, rows)
                with self.subTest(key=key, index=index), self.assertRaises(ValueError):
                    audio.validate_capture(root, IDENTITY, TOKEN, START + 0.25, 1.5, 1/60)

    def test_packet_loss_overlap_flags_offsets_and_invalid_timestamps_reject(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = fixture(root)
            index = next(i for i, r in enumerate(baseline) if r.get("seq") == 70)
            for key, value in (("seq", 69), ("offset_bytes", 0), ("frames", 0), ("frames", 50000),
                               ("flags", 1), ("flags", 4), ("flags", 8), ("qpc_100ns", "0"),
                               ("qpc_100ns", str(QPC+7100000)), ("qpc_100ns", str(QPC+6900000))):
                rows = copy.deepcopy(baseline)
                rows[index][key] = value
                write_journal(root, rows)
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    audio.validate_capture(root, IDENTITY, TOKEN, START + 0.25, 1.5, 1/60)
            del baseline[index]
            write_journal(root, baseline)
            with self.assertRaises(ValueError):
                audio.validate_capture(root, IDENTITY, TOKEN, START + 0.25, 1.5, 1/60)

    def test_missing_terminal_or_partial_json_is_not_success(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = fixture(root)
            for changed in (rows[:-1], rows + [rows[0]], rows[:1] + [{"kind": "unknown"}] + rows[1:]):
                write_journal(root, changed)
                with self.assertRaises(ValueError):
                    audio.validate_capture(root, IDENTITY, TOKEN, START + 0.25, 1.5, 1/60)
            write_journal(root, rows)
            path = root / audio.JOURNAL_NAME
            path.write_bytes(path.read_bytes()[:-1])
            with self.assertRaises(ValueError):
                audio.validate_capture(root, IDENTITY, TOKEN, START + 0.25, 1.5, 1/60)

    def test_changed_extra_truncated_nonfinite_and_falsely_silent_pcm_reject(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = fixture(root)
            path = root / audio.PCM_NAME
            original = path.read_bytes()
            for bad in (original[:-8], original + bytes(8), bytes(8) + original[8:],
                        struct.pack("<f", float("nan")) + original[4:]):
                path.write_bytes(bad)
                with self.assertRaises(ValueError):
                    audio.validate_capture(root, IDENTITY, TOKEN, START + 0.25, 1.5, 1/60)
            bad = original[:40*441*8] + struct.pack("<f", 0.001) + original[40*441*8+4:]
            path.write_bytes(bad)
            rows[-1]["pcm_sha256"] = hashlib.sha256(bad).hexdigest()
            write_journal(root, rows)
            with self.assertRaises(ValueError):
                audio.validate_capture(root, IDENTITY, TOKEN, START + 0.25, 1.5, 1/60)

    def test_bad_native_clock_brackets_jumps_and_coverage_reject(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = fixture(root)
            index = next(i for i, r in enumerate(baseline) if r.get("kind") == "anchor" and i > 1)
            for key, value in (("frequency", "0"), ("qpc_before", str(QPC+999999999)),
                               ("utc_filetime", str(FILETIME+999999999))):
                rows = copy.deepcopy(baseline)
                rows[index][key] = value
                write_journal(root, rows)
                with self.subTest(key=key), self.assertRaises(ValueError):
                    audio.validate_capture(root, IDENTITY, TOKEN, START + 0.25, 1.5, 1/60)
            write_journal(root, baseline)
            for start, duration in ((START-0.1, 1), (START+0.5, 1.51), (START, float("nan"))):
                with self.subTest(start=start, duration=duration), self.assertRaises(ValueError):
                    audio.validate_capture(root, IDENTITY, TOKEN, start, duration, 1/60)


@unittest.skipUnless(sys.platform == "win32", "WASAPI requires Windows")
class NativeProcessAudioTest(unittest.TestCase):
    def setUp(self) -> None:
        temp = Path.home() / "AppData/Local/Temp/opencode"
        self.temp = tempfile.TemporaryDirectory(dir=temp if temp.exists() else None)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        lease = audio.ProcessLease(os.getpid())
        try:
            # Store Python's execution alias differs from the actual process image.
            self.python_image = Path(lease.identity["path"])
        finally:
            lease.close()

    def test_helper_captures_only_own_process_and_closes_with_native_anchors(self) -> None:
        helper = audio.ProcessAudio.start(os.getpid(), self.python_image, self.root, 10, TOKEN)
        self.addCleanup(helper.abort)
        start = time.time()
        time.sleep(0.25)
        result = helper.stop()
        placement = audio.validate_capture(self.root, result["identity"], TOKEN, start, 0.2, 1/60)
        self.assertGreater(placement["frames"], 4410)
        self.assertIsNotNone(helper.child.poll())
        self.assertEqual(result["helper_exit"], 0)
        self.assertTrue(all(not b for b in (self.root / audio.PCM_NAME).read_bytes()))

    def test_wrong_executable_path_is_rejected_before_starting_audio(self) -> None:
        with self.assertRaisesRegex(ValueError, "path"):
            audio.ProcessAudio.start(os.getpid(), self.root / "other.exe", self.root, 10, TOKEN)
        self.assertFalse((self.root / audio.PCM_NAME).exists())

    def test_eof_or_target_exit_cannot_emit_clean_terminal(self) -> None:
        for failure in ("eof", "exit"):
            with self.subTest(failure=failure):
                root = self.root / failure
                root.mkdir()
                target = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(20)"])
                self.addCleanup(lambda p=target: p.poll() is None and p.terminate())
                helper = audio.ProcessAudio.start(target.pid, self.python_image, root, 10, TOKEN)
                self.addCleanup(helper.abort)
                if failure == "eof":
                    helper.child.stdin.close()
                else:
                    target.terminate()
                    target.wait(timeout=5)
                self.assertNotEqual(helper.child.wait(timeout=5), 0)
                rows = [json.loads(line) for line in (root / audio.JOURNAL_NAME).read_text().splitlines()]
                self.assertFalse(rows[-1]["clean"])
                if target.poll() is None:
                    target.terminate()
                    target.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
