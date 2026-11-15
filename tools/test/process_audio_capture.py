"""Validate process-only WASAPI audio without repairing gaps or changing samples."""
import hashlib
import ctypes
import ctypes.wintypes as wt
import json
import math
import os
from pathlib import Path
import queue
import struct
import subprocess
import threading
import time


class ProcessLease:
    """Hold one process identity on a query/synchronize handle, never a PID lookup loop."""

    def __init__(self, pid: int, expected_path: Path | None = None) -> None:
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        signatures = {
            "OpenProcess": ([wt.DWORD, wt.BOOL, wt.DWORD], wt.HANDLE),
            "CloseHandle": ([wt.HANDLE], wt.BOOL),
            "WaitForSingleObject": ([wt.HANDLE, wt.DWORD], wt.DWORD),
            "GetProcessTimes": ([wt.HANDLE, *([ctypes.POINTER(wt.FILETIME)] * 4)], wt.BOOL),
            "QueryFullProcessImageNameW": ([wt.HANDLE, wt.DWORD, wt.LPWSTR, ctypes.POINTER(wt.DWORD)], wt.BOOL),
        }
        for name, (arguments, result) in signatures.items():
            function = getattr(self.kernel, name)
            function.argtypes, function.restype = arguments, result
        if not 0 < pid <= 0xffffffff:
            raise ValueError("explicit nonzero process identity required")
        self.handle = self.kernel.OpenProcess(0x00101000, False, pid)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            created, exited, kernel, user = (wt.FILETIME() for _ in range(4))
            path, size = ctypes.create_unicode_buffer(32768), wt.DWORD(32768)
            if (not self.kernel.GetProcessTimes(self.handle, ctypes.byref(created), ctypes.byref(exited),
                                                ctypes.byref(kernel), ctypes.byref(user)) or
                    not self.kernel.QueryFullProcessImageNameW(self.handle, 0, path, ctypes.byref(size))):
                raise ctypes.WinError(ctypes.get_last_error())
            if expected_path is not None and Path(path.value).resolve() != expected_path.resolve():
                raise ValueError("process executable path does not match the selected game")
            self.identity = {"pid": pid, "path": path.value,
                             "creation_filetime": str((created.dwHighDateTime << 32) | created.dwLowDateTime)}
            self.check()
        except BaseException:
            self.close()
            raise

    def check(self) -> None:
        """Raise if the held process exited or its wait cannot be verified."""
        if not self.handle or self.kernel.WaitForSingleObject(self.handle, 0) != 258:
            raise RuntimeError("bound process exited or wait failed")

    def close(self) -> None:
        """Release only this lease's handle."""
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None


class ProcessAudio:
    """Own one isolated helper; clean closure requires explicit STOP and matching terminal."""

    @classmethod
    def start(cls, pid: int, expected_path: Path, directory: Path,
              max_seconds: float, token: str) -> "ProcessAudio":
        """Verify the selected game, start INCLUDE-only audio and wait for native packets."""
        self = cls()
        self.child = self.target = self.parent = self.log = None
        self.messages = queue.Queue()
        self.token, self.directory = token, directory
        try:
            self.target = ProcessLease(pid, expected_path)
            self.parent = ProcessLease(os.getpid())
            request = {"identity": self.target.identity, "parent": self.parent.identity,
                       "token": token, "max_seconds": max_seconds}
            with (directory / "process_audio_request.json").open("x", encoding="utf-8") as stream:
                json.dump(request, stream)
            self.log = (directory / "process_audio_helper.log").open("x", encoding="utf-8")
            self.child = subprocess.Popen(
                ["pwsh.exe", "-NoProfile", "-MTA", "-File", str(Path(__file__).with_suffix(".ps1")),
                 "-RequestPath", str((directory / "process_audio_request.json").resolve())],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.log,
                text=True, encoding="utf-8", creationflags=subprocess.CREATE_NO_WINDOW)
            self.reader = threading.Thread(target=self._read_messages, daemon=True)
            self.reader.start()
            self._wait_message("READY " + token, 20)
            self.check()
            return self
        except BaseException:
            self.abort()
            raise

    def _read_messages(self) -> None:
        for line in self.child.stdout:
            self.messages.put(line.rstrip("\r\n"))
        self.messages.put(None)

    def _wait_message(self, expected: str, seconds: float) -> None:
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            self.target.check()
            try:
                message = self.messages.get(timeout=0.05)
            except queue.Empty:
                if self.child.poll() is not None:
                    raise RuntimeError("audio helper exited before " + expected)
                continue
            if message != expected:
                raise RuntimeError(f"invalid audio helper response: {message!r}")
            return
        raise RuntimeError("audio helper timeout waiting for " + expected)

    def check(self) -> None:
        """Fail closed on target exit or unexpected helper termination."""
        self.target.check()
        if self.child.poll() is not None:
            raise RuntimeError("audio helper exited during recording")

    def stop(self) -> dict:
        """Stop after video, while target lives; verify STOP, exit and terminal before closing."""
        try:
            self.check()
            # Let the last complete native packet cover the video encoder's tail.
            time.sleep(0.1)
            self.check()
            self.child.stdin.write("STOP " + self.token + "\n")
            self.child.stdin.flush()
            self._wait_message("CLOSED " + self.token, 10)
            if self.child.wait(timeout=10) != 0:
                raise RuntimeError("audio helper failed during shutdown")
            self.target.check()
            rows = _read_journal(self.directory)
            terminal = rows[-1]
            if (terminal.get("kind") != "terminal" or terminal.get("clean") is not True or
                    terminal.get("reason") != "STOP" or terminal.get("token") != self.token or
                    terminal.get("target_alive") is not True):
                raise RuntimeError("audio helper terminal was not a clean STOP")
            return {"identity": self.target.identity, "token": self.token, "helper_exit": 0}
        finally:
            self.abort()

    def abort(self) -> None:
        """Reap only this helper on errors; never close or signal the game process."""
        try:
            if self.child:
                try:
                    if self.child.stdin and not self.child.stdin.closed:
                        self.child.stdin.close()  # EOF is an explicit failure, never STOP.
                except (OSError, KeyboardInterrupt, SystemExit):
                    self._kill_helper()  # Broken IPC must not skip termination/reaping.
                try:
                    self.child.wait(timeout=3)
                except (subprocess.TimeoutExpired, OSError, KeyboardInterrupt, SystemExit):
                    self._kill_helper()
                finally:
                    if self.child.poll() is None:
                        self._kill_helper()
        finally:
            if self.child and self.child.stdout:
                if hasattr(self, "reader"):
                    self.reader.join(timeout=1)
                self.child.stdout.close()
            for lease in (self.target, self.parent):
                if lease:
                    lease.close()
            if self.log:
                self.log.close()

    def _kill_helper(self) -> None:
        # As with the recorder's FFmpeg child, repeated Ctrl+C cannot transfer
        # ownership of an active collector back to the caller.
        while True:
            try:
                if self.child.poll() is None:
                    self.child.kill()
                self.child.wait(timeout=5)
                return
            except (KeyboardInterrupt, SystemExit, subprocess.TimeoutExpired):
                continue

RATE = 44100
BLOCK_ALIGN = 8
TICKS_PER_SECOND = 10000000
UNIX_FILETIME = 116444736000000000
PACKET_TOLERANCE = 1 / RATE + 0.0000002
FORMAT = {"rate_hz": RATE, "channels": 2, "sample_format": "f32le"}
PCM_NAME = "process_audio.f32"
JOURNAL_NAME = "process_audio.jsonl"


def _uint(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, (str, int)) or not str(value).isascii() or not str(value).isdigit():
        raise ValueError("invalid unsigned integer in audio journal")
    return int(value)


def _read_journal(directory: Path) -> list[dict]:
    rows = []
    with (directory / JOURNAL_NAME).open("rb") as stream:
        for line in stream:
            if not line.endswith(b"\n"):
                raise ValueError("truncated audio journal")
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError("invalid audio journal row")
            rows.append(row)
    if len(rows) < 4:
        raise ValueError("incomplete audio journal")
    return rows


def _clock(anchors: list[dict], period: float) -> tuple[float, float, float, float]:
    if len(anchors) < 2:
        raise ValueError("missing native clock anchors")
    frequency = _uint(anchors[0]["frequency"])
    if frequency == 0:
        raise ValueError("zero QPC frequency")
    first_tick = (_uint(anchors[0]["qpc_before"]) + _uint(anchors[0]["qpc_after"])) / 2
    first_utc = _uint(anchors[0]["utc_filetime"])
    errors, uncertainty, previous = [], 0.0, None
    last_tick = first_tick
    for anchor in anchors:
        before, after = _uint(anchor["qpc_before"]), _uint(anchor["qpc_after"])
        utc = _uint(anchor["utc_filetime"])
        if _uint(anchor["frequency"]) != frequency or after < before or utc <= UNIX_FILETIME:
            raise ValueError("invalid native clock bracket/frequency")
        middle = (before + after) / 2
        if previous is not None and not 0 < (middle - previous) / frequency <= 2:
            raise ValueError("unordered or missing periodic native clock anchors")
        errors.append((utc - first_utc) / TICKS_PER_SECOND - (middle - first_tick) / frequency)
        uncertainty = max(uncertainty, (after - before) / frequency / 2)
        previous = last_tick = middle
    clock_error = max(abs(error) for error in errors) + uncertainty
    if clock_error > period:
        raise ValueError("native QPC/UTC clock error exceeds one frame")
    first_qpc = first_tick * TICKS_PER_SECOND / frequency
    last_qpc = last_tick * TICKS_PER_SECOND / frequency
    return first_qpc, (first_utc - UNIX_FILETIME) / TICKS_PER_SECOND, last_qpc, clock_error


def validate_capture(directory: Path, identity: dict, token: str, video_start: float,
                     duration: float, frame_period: float) -> dict:
    """Return proven sample placement, or raise ValueError on incomplete evidence."""
    if (not all(math.isfinite(v) for v in (video_start, duration, frame_period)) or
            duration <= 0 or frame_period <= 0 or not token):
        raise ValueError("invalid video interval or session token")
    try:
        rows = _read_journal(directory)
        ready, terminal = rows[0], rows[-1]
        if (ready.get("kind") != "ready" or ready.get("schema") != 1 or
                ready.get("identity") != identity or ready.get("token") != token or
                ready.get("mode") != "include_target_tree" or ready.get("format") != FORMAT):
            raise ValueError("unverified process identity/token/format/mode")
        if (terminal.get("kind") != "terminal" or terminal.get("clean") is not True or
                terminal.get("target_alive") is not True or terminal.get("reason") != "STOP" or
                terminal.get("token") != token):
            raise ValueError("audio helper did not finish a clean STOP while target alive")
        anchors, packets = [], []
        for row in rows[1:-1]:
            if row.get("kind") == "anchor":
                anchors.append(row)
            elif row.get("kind") == "packet":
                packets.append(row)
            else:
                raise ValueError("unknown or out-of-order audio journal record")
        if len(packets) < 10:
            raise ValueError("insufficient native audio packets")
        anchor_qpc, anchor_wall, final_qpc, clock_error = _clock(anchors, frame_period)
        first_qpc = _uint(packets[0]["qpc_100ns"])
        samples, max_gap, max_drift = 0, 0.0, 0.0
        digest = hashlib.sha256()
        previous_qpc, previous_frames = first_qpc, 0
        with (directory / PCM_NAME).open("rb") as pcm:
            for sequence, packet in enumerate(packets):
                frames, flags = _uint(packet["frames"]), _uint(packet["flags"])
                qpc = _uint(packet["qpc_100ns"])
                _uint(packet["device_position"])  # diagnostic only; zero is legitimate
                if (packet["seq"] != sequence or packet["offset_bytes"] != samples * BLOCK_ALIGN or
                        not 0 < frames <= RATE or not qpc or flags & ~3 or (sequence and flags & 1)):
                    raise ValueError("invalid packet sequence/offset/flags/geometry")
                if sequence:
                    gap = abs((qpc - previous_qpc) / TICKS_PER_SECOND - previous_frames / RATE)
                    max_gap = max(max_gap, gap)
                    if gap > PACKET_TOLERANCE:
                        raise ValueError("missing/overlapping native audio packet")
                drift = abs((qpc - first_qpc) / TICKS_PER_SECOND - samples / RATE)
                max_drift = max(max_drift, drift)
                data = pcm.read(frames * BLOCK_ALIGN)
                if len(data) != frames * BLOCK_ALIGN:
                    raise ValueError("truncated float PCM")
                if any(not math.isfinite(value) for (value,) in struct.iter_unpack("<f", data)):
                    raise ValueError("nonfinite float PCM")
                if flags & 2 and any(data):
                    raise ValueError("native SILENT packet contains nonzero PCM")
                digest.update(data)
                samples += frames
                previous_qpc, previous_frames = qpc, frames
            if pcm.read(1):
                raise ValueError("unaccounted PCM bytes")
        if (terminal.get("frames") != samples or terminal.get("packets") != len(packets) or
                terminal.get("bytes") != samples * BLOCK_ALIGN or terminal.get("pcm_sha256") != digest.hexdigest()):
            raise ValueError("terminal totals or PCM digest mismatch")
        if anchor_qpc > first_qpc or final_qpc < previous_qpc:
            raise ValueError("clock anchors do not cover audio packets")
        if max_drift + clock_error > frame_period:
            raise ValueError("audio placement drift/clock uncertainty exceeds one frame")
        start_wall = anchor_wall + (first_qpc - anchor_qpc) / TICKS_PER_SECOND
        video_offset = video_start - start_wall
        native_duration = (previous_qpc - first_qpc) / TICKS_PER_SECOND + previous_frames / RATE
        # Nominal sample count alone cannot prove wall-time coverage: permitted
        # sub-sample errors can accumulate, and anchors have nonzero uncertainty.
        if (video_offset < clock_error or
                video_offset + duration > min(samples / RATE, native_duration - clock_error)):
            raise ValueError("native audio does not cover the entire video interval")
        # Include every source sample intersecting the video, never round away
        # an uncovered fractional tail. Original PCM is retained untouched.
        trim_start = math.floor(video_offset * RATE)
        trim_end = math.ceil((video_offset + duration) * RATE)
        if trim_start < 0 or trim_end > samples:
            raise ValueError("native audio does not cover the entire video sample interval")
        effective_rate = (samples - previous_frames) / ((previous_qpc - first_qpc) / TICKS_PER_SECOND)
        return {"audio_source": "process", "offset_s": start_wall - video_start,
                "rate_hz": effective_rate, "pairs": len(packets), "dropped": 0,
                "window_max_ms": (max_drift + clock_error) * 1000,
                "packet_error_us": max_gap * 1000000, "clock_error_ms": clock_error * 1000,
                "frames": samples, "trim_start_sample": trim_start, "trim_end_sample": trim_end,
                "pcm_sha256": digest.hexdigest()}
    except (OSError, KeyError, TypeError, ZeroDivisionError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid process-audio evidence: {error}") from error
