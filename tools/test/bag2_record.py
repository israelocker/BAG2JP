"""Record a BAG2JP game test as video + exact game audio, aligned to game frames.

The video is a capture of the game window's client area (by default via Windows
Graphics Capture `gfxcapture` in FFmpeg >= 8.0 when available, falling back to
`gdigrab` desktop region capture; both stamp the first frame with wall-clock
time). The audio is the game's own final mix (BAG2JP_AUDIO_DUMP=1 ->
bag2jp_audio.wav + bag2jp_audio_sync.log), never a microphone or desktop
loopback. A poller stamps every bag2jp_frame.txt update (BAG2JP_ANIM_TRACE=1,
every 6 frames) and every new bag2jp_bag1_versions.log line with wall-clock
time. Other logs (anim trace, watch) carry game frames and map through the
same clock; they are not stamped by the recorder.

With `--capture-backend wgc` (selected automatically in `auto` mode when
`BAG2JP_FFMPEG_WGC` or `DEFAULT_FFMPEG_WGC` exists), FFmpeg captures the
target HWND directly through WGC: overlapping windows on top do not appear in
the video and the game window is not pinned topmost or forced into focus,
though the window must remain visible, unminimized and at constant size. With
`gdigrab`, the selected HWND/PID is brought to the foreground and temporarily
pinned topmost, and overlap/movement/cancellation rejects the capture. Window
state and handle tags are restored before the session is marked closed.

The frame clock interpolates between heartbeats, so a game pause or hitch moves
only its own interval; pauses are listed in manifest.json. The audio dump counts
the same vblanks as the heartbeat (anim_trace `af` and `frame` both start with
the trace), so one offset places it; its spread is measured and gated.

Unvalidated: the label is the frame the plugin *reported* at that wall time;
display/compositor latency is not calibrated yet, so the picture may lag the
label by a few frames. Tested on the primary monitor at 125 % scaling only; the
window must be fully on the primary monitor and uncovered.

usage:
  py -3.13 tools/test/bag2_record.py record --tag T [--fps 60] [--max-seconds 900] [--capture-backend auto|wgc|gdigrab]
      (run in background; stop by creating _work/recordings/T/STOP, closing the
       game, or reaching --max-seconds)
  py -3.13 tools/test/bag2_record.py finalize --tag T
      -> owner.mp4 (H.264 + AAC, to watch), review.mkv (lossless + FLAC, to
         inspect), raw.mkv (clean capture), events.json, manifest.json; exit 0
         only when every alignment gate passed (manifest "accepted")
  py -3.13 tools/test/bag2_record.py frames --tag T --frame F [--span N] [--step S]
      -> PNG stills of review.mkv around game frame F via ffmpeg-skill look.py
"""
from __future__ import annotations

import argparse
import bisect
import csv
import ctypes
import ctypes.wintypes as wt
import hashlib
import json
import logging
import math
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from collections.abc import Callable

if __package__:
    from .recording_window import RecordingWindow, find_window
else:
    from recording_window import RecordingWindow, find_window

logger = logging.getLogger("bag2_record")

REPO = Path(__file__).resolve().parents[2]
GAME_DIR = Path(r"D:\Games\Bust A Groove 2 (Japan)\BAG2JP-exp-8mb")
RECORDINGS = REPO / "_work" / "recordings"
LOOK = REPO / ".agents" / "skills" / "ffmpeg-skill" / "scripts" / "look.py"
GAME_EXE = "BAG2JP.exe"
HEARTBEAT = "bag2jp_frame.txt"
DEFAULT_FFMPEG_WGC = Path(r"D:\Dev\Tools\ffmpeg-wgc\ffmpeg-n8.1-latest-win64-gpl-8.1\bin\ffmpeg.exe")
FFMPEG_WGC_ENV = "BAG2JP_FFMPEG_WGC"
HEARTBEAT_STRIDE = 6            # the debug plugin rewrites the heartbeat every 6 frames
VERSIONS_LOG = "bag2jp_bag1_versions.log"
AUDIO_WAV = "bag2jp_audio.wav"
AUDIO_SYNC = "bag2jp_audio_sync.log"
LABELS = "labels.ass"
AUDIO_RATE = 44100
POLL_SECONDS = 0.004
ALIVE_CHECK_SECONDS = 1.0
WINDOW_WAIT_SECONDS = 60.0
FFMPEG_QUIT_SECONDS = 30.0
FFMPEG_EXTRA_SECONDS = 5        # hard -t margin so an orphaned capture still ends
FFMPEG_STOP_POLL_SECONDS = 0.1
MIN_HEARTBEATS = 10
MIN_SYNC_PAIRS = 10
MAX_DROPPED_FRACTION = 0.02
STALL_PERIODS = 2.0             # an interval this many frames longer than expected is a pause
PERIOD_BASELINE_ROWS = 30       # ~3 s baselines for the median frame period
MAX_AUDIO_DROPPED = 0.005       # tolerated fraction of torn sync pairs
AUDIO_OUTLIER_SECONDS = 0.1     # a pair this far off the first fit is a torn line
AUDIO_WINDOW_PAIRS = 60         # ~1 s of vblanks; smooths the per-vblank chunking
MAX_AUDIO_RATE_ERROR = 0.01     # effective dump rate must be within 1 % of 44100 Hz
EXIT_REJECTED = 5


class HeartbeatClock:
    """Piecewise-linear map between game frames and wall-clock seconds.

    Heartbeats are only observed after they are written, so a stamp can be late.
    A row is dropped as late when its interval in is long *and* the next one is
    short (the stamp moved, not the game). A long interval followed by a normal
    one is a genuine pause and is kept, so interpolation confines it.
    """

    def __init__(self, rows: list[tuple[float, int]]) -> None:
        """Validate and clean (wall, frame) rows.

        Raises:
            ValueError: too few rows or frames that do not strictly increase.
        """
        if len(rows) < MIN_HEARTBEATS:
            raise ValueError(f"only {len(rows)} heartbeats; need {MIN_HEARTBEATS}")
        for i in range(1, len(rows)):
            if rows[i][1] <= rows[i - 1][1]:
                raise ValueError(f"heartbeat frame did not increase at row {i}: "
                                 f"{rows[i - 1][1]} -> {rows[i][1]}")
        # Long baselines: per-interval slopes are dominated by stamp jitter, and
        # a median over many baselines ignores the few that cross a pause.
        k = max(1, min(PERIOD_BASELINE_ROWS, len(rows) // 4))
        slopes = sorted((rows[i][0] - rows[i - k][0]) / (rows[i][1] - rows[i - k][1])
                        for i in range(k, len(rows)))
        self.period = slopes[len(slopes) // 2]
        if self.period <= 0:
            raise ValueError("wall clock did not advance between heartbeats")
        self.dropped = self._drop_late(rows)
        self.rows = [r for i, r in enumerate(rows) if i not in self.dropped]
        self.walls = [w for w, _ in self.rows]
        self.frames = [f for _, f in self.rows]
        excess = [(self.walls[i] - self.walls[i - 1]) - (self.frames[i] - self.frames[i - 1]) * self.period
                  for i in range(1, len(self.rows))]
        self.stalls = [{"after_frame": self.frames[i - 1], "wall": self.walls[i - 1],
                        "seconds": round(e, 3)}
                       for i, e in enumerate(excess, start=1) if e > STALL_PERIODS * self.period]
        normal = sorted(abs(e) for e in excess if e <= STALL_PERIODS * self.period)
        self.jitter_p99_ms = normal[min(len(normal) - 1, int(0.99 * len(normal)))] * 1000.0
        self.observed = len(rows)

    def _drop_late(self, rows: list[tuple[float, int]]) -> set[int]:
        """Indexes of stamps observed late (long interval in, short interval out)."""
        dropped: set[int] = set()
        for i in range(1, len(rows) - 1):
            inside = (rows[i][0] - rows[i - 1][0]) - (rows[i][1] - rows[i - 1][1]) * self.period
            after = (rows[i + 1][0] - rows[i][0]) - (rows[i + 1][1] - rows[i][1]) * self.period
            if inside > self.period and after < -self.period / 2:
                dropped.add(i)
        return dropped

    def frame_of(self, wall: float) -> float:
        """Game frame at a wall time (extrapolated with the median period outside)."""
        i = bisect.bisect_right(self.walls, wall)
        if i == 0:
            return self.frames[0] - (self.walls[0] - wall) / self.period
        if i == len(self.walls):
            return self.frames[-1] + (wall - self.walls[-1]) / self.period
        w0, w1, f0, f1 = self.walls[i - 1], self.walls[i], self.frames[i - 1], self.frames[i]
        return f0 + (f1 - f0) * (wall - w0) / (w1 - w0)

    def wall_of(self, frame: float) -> float:
        """Wall time at which a game frame was reported."""
        i = bisect.bisect_right(self.frames, frame)
        if i == 0:
            return self.walls[0] - (self.frames[0] - frame) * self.period
        if i == len(self.frames):
            return self.walls[-1] + (frame - self.frames[-1]) * self.period
        w0, w1, f0, f1 = self.walls[i - 1], self.walls[i], self.frames[i - 1], self.frames[i]
        return w0 + (w1 - w0) * (frame - f0) / (f1 - f0)

    def summary(self) -> dict:
        """Facts for manifest.json."""
        return {"observed": self.observed, "dropped_late": len(self.dropped),
                "first_frame": self.frames[0], "last_frame": self.frames[-1],
                "fps": 1.0 / self.period, "jitter_p99_ms": round(self.jitter_p99_ms, 2),
                "stalls": self.stalls}


def parse_ffmpeg_start(log_text: str) -> float:
    """Return first-frame wall-clock time from FFmpeg's gdigrab or lavfi banner.

    Raises:
        ValueError: when the banner has no plausible wall-clock start.
    """
    match = re.search(
        r"Input #0, (?:gdigrab|lavfi)\b[^\n]*\n\s*Duration:[^\n]*?\bstart: ([0-9]+\.[0-9]+)",
        log_text,
    )
    if not match:
        raise ValueError("FFmpeg log has no gdigrab/lavfi start stamp")
    start = float(match.group(1))
    if start < 1.0e9:
        raise ValueError(f"FFmpeg start {start} is not a wall-clock stamp")
    return start


def parse_heartbeat(text: str) -> int | None:
    """Return the game frame in a bag2jp_frame.txt snapshot, or None if torn."""
    match = re.match(r"\s*(\d{7}) ", text)
    return int(match.group(1)) if match else None


def parse_sync_log(text: str) -> list[tuple[int, int]]:
    """Return (game frame, audio sample) pairs from bag2jp_audio_sync.log."""
    pairs: list[tuple[int, int]] = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            pairs.append((int(parts[0]), int(parts[1])))
    return pairs


def audio_placement(clock: HeartbeatClock, sync: list[tuple[int, int]], video_start: float,
                    rate: int = AUDIO_RATE) -> dict:
    """Rate and offset that place every audio sample at its video time.

    The dump writes a whole number of samples per emulated vblank (735 on
    average), so its clock follows the game, not 44100 Hz of wall time: about
    0.1 % slow at 59.94 fps (measured). A line fitted through (sample, video time)
    gives the effective rate, rounded to an integer because asetrate takes one,
    and the offset of sample 0 at that rate. The per-vblank chunks scatter single
    pairs by about +-20 ms, so the gate uses the median residual of 1 s windows;
    a pause shows up there because the dump stops while wall time goes on.

    Only pairs inside the heartbeat range count, so a dump from another session
    or frames long before the recording cannot decide the placement. Pairs more
    than AUDIO_OUTLIER_SECONDS off the first fit (torn lines) are dropped once.

    Returns:
        {"offset_s", "rate_hz", "pairs", "dropped", "residual_p99_ms",
         "window_max_ms"}.

    Raises:
        ValueError: when too few pairs overlap the recording.
    """
    inside = [(s, clock.wall_of(f) - video_start) for f, s in sync
              if clock.frames[0] <= f <= clock.frames[-1]]
    if len(inside) < MIN_SYNC_PAIRS:
        raise ValueError(f"audio sync covers {len(inside)} recorded frames; "
                         "the dump is from another session or missing")
    offset, seconds_per_sample = _fit_line(inside)
    kept = [(s, t) for s, t in inside if abs(t - offset - s * seconds_per_sample) <= AUDIO_OUTLIER_SECONDS]
    if len(kept) < MIN_SYNC_PAIRS:
        raise ValueError("audio sync pairs do not follow the frame clock (a pause or another session)")
    _, seconds_per_sample = _fit_line(kept)
    rate_hz = max(1, round(1.0 / seconds_per_sample))
    estimates = sorted(t - s / rate_hz for s, t in kept)
    offset = estimates[len(estimates) // 2]
    residuals = [t - s / rate_hz - offset for s, t in kept]
    windows = [sorted(residuals[i:i + AUDIO_WINDOW_PAIRS])
               for i in range(0, len(residuals), AUDIO_WINDOW_PAIRS)]
    window_medians = [abs(w[len(w) // 2]) for w in windows if len(w) >= AUDIO_WINDOW_PAIRS // 2]
    magnitudes = sorted(abs(r) for r in residuals)
    return {"offset_s": round(offset, 6), "rate_hz": rate_hz, "pairs": len(inside),
            "dropped": len(inside) - len(kept),
            "residual_p99_ms": round(magnitudes[int(0.99 * (len(magnitudes) - 1))] * 1000.0, 2),
            "window_max_ms": round(max(window_medians, default=0.0) * 1000.0, 2)}


def _fit_line(points: list[tuple[float, float]]) -> tuple[float, float]:
    """Least-squares intercept and slope of y against x.

    Raises:
        ValueError: when x does not vary.
    """
    n = len(points)
    mean_x = sum(x for x, _ in points) / n
    mean_y = sum(y for _, y in points) / n
    var_x = sum((x - mean_x) ** 2 for x, _ in points)
    if var_x <= 0 or n < 2:
        raise ValueError("audio sample counter never advanced")
    slope = sum((x - mean_x) * (y - mean_y) for x, y in points) / var_x
    if slope <= 0:
        raise ValueError("audio sample counter went backwards against the frame clock")
    return mean_y - slope * mean_x, slope


def audio_filter(offset: float, duration: float, rate_hz: int = AUDIO_RATE) -> str:
    """Play the dump at its measured rate, put sample 0 at the given video time and
    pad/trim to the video duration.

    asetrate relabels the samples (pitch moves by the same ~0.1 %, about 2 cents),
    aresample returns to 44100 Hz for the encoders. A finite pad is required: apad
    without a length plus -shortest never ends inside -filter_complex here.
    """
    rate = f"asetrate={rate_hz},aresample={AUDIO_RATE}," if rate_hz != AUDIO_RATE else ""
    fit = f"apad=whole_dur={duration:.6f},atrim=end={duration:.6f}"
    if offset >= 0:
        return f"{rate}adelay={int(round(offset * 1000))}:all=1,{fit}"
    return f"{rate}atrim=start={-offset:.6f},asetpts=PTS-STARTPTS,{fit}"


def media_duration(path: Path) -> float:
    """Container duration in seconds (ffprobe)."""
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                             "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


def ass_time(seconds: float) -> str:
    """ASS timestamp h:mm:ss.cc."""
    centis = max(0, int(round(seconds * 100)))
    return f"{centis // 360000}:{centis // 6000 % 60:02d}:{centis // 100 % 60:02d}.{centis % 100:02d}"


def label_events(clock: HeartbeatClock, video_start: float) -> list[tuple[float, float, int]]:
    """(start, end, frame) video-time slots for every game frame in the heartbeat range."""
    slots = []
    for frame in range(clock.frames[0], clock.frames[-1]):
        start = clock.wall_of(frame) - video_start
        end = clock.wall_of(frame + 1) - video_start
        if end > 0:
            slots.append((max(0.0, start), end, frame))
    return slots


def write_labels(path: Path, clock: HeartbeatClock, video_start: float, height: int) -> None:
    """ASS subtitles showing `gf <frame>` in the top-left corner."""
    size = max(12, height // 22)
    lines = ["[Script Info]", "ScriptType: v4.00+", f"PlayResY: {height}", "",
             "[V4+ Styles]",
             "Format: Name, Fontname, Fontsize, PrimaryColour, BackColour, BorderStyle, Outline, "
             "Shadow, Alignment, MarginL, MarginR, MarginV",
             f"Style: L,Consolas,{size},&H0000FFFF,&H99000000,3,2,0,7,6,6,6", "",
             "[Events]", "Format: Layer, Start, End, Style, Text"]
    lines += [f"Dialogue: 0,{ass_time(s)},{ass_time(e)},L,gf {f}"
              for s, e, f in label_events(clock, video_start)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    """Hex SHA-256 of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


# ---- Windows process and window lookup -------------------------------------

def _win32() -> tuple[ctypes.WinDLL, ctypes.WinDLL]:
    """user32/kernel32 with explicit signatures (HWND/HANDLE may exceed int)."""
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    user32.EnumWindows.argtypes = [ctypes.c_void_p, wt.LPARAM]
    user32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
    user32.IsWindowVisible.argtypes = [wt.HWND]
    user32.GetWindow.argtypes = [wt.HWND, ctypes.c_uint]
    user32.GetWindow.restype = wt.HWND
    user32.GetClientRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
    user32.ClientToScreen.argtypes = [wt.HWND, ctypes.POINTER(wt.POINT)]
    user32.GetSystemMetrics.argtypes = [ctypes.c_int]
    user32.SetProcessDpiAwarenessContext.argtypes = [ctypes.c_void_p]
    kernel32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
    kernel32.OpenProcess.restype = wt.HANDLE
    kernel32.WaitForSingleObject.argtypes = [wt.HANDLE, wt.DWORD]
    kernel32.WaitForSingleObject.restype = wt.DWORD
    kernel32.CloseHandle.argtypes = [wt.HANDLE]
    kernel32.QueryFullProcessImageNameW.argtypes = [wt.HANDLE, wt.DWORD, wt.LPWSTR,
                                                    ctypes.POINTER(wt.DWORD)]
    return user32, kernel32


PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
SYNCHRONIZE = 0x00100000
WAIT_TIMEOUT = 0x102
GW_OWNER = 4
SM_CXSCREEN, SM_CYSCREEN = 0, 1
DPI_PER_MONITOR_AWARE_V2 = -4


def game_pid(game_dir: Path) -> int | None:
    """PID of the BAG2JP.exe running from game_dir (not another install), or None."""
    _, kernel32 = _win32()
    out = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {GAME_EXE}", "/FO", "CSV", "/NH"],
                         capture_output=True, text=True, check=False).stdout
    wanted = str((game_dir / GAME_EXE).resolve()).lower()
    for pid in (int(m) for m in re.findall(r'"%s","(\d+)"' % re.escape(GAME_EXE), out, re.I)):
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            continue
        buffer, size = ctypes.create_unicode_buffer(1024), wt.DWORD(1024)
        ok = kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size))
        kernel32.CloseHandle(handle)
        if ok and buffer.value.lower() == wanted:
            return pid
    return None


def client_rect(pid: int) -> tuple[int, int, int, int] | None:
    """Physical-pixel screen rectangle (x, y, w, h) of the game's main client area."""
    user32, _ = _win32()
    found: list[int] = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def visit(hwnd: int, _: int) -> bool:
        owner = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid and user32.IsWindowVisible(hwnd) and not user32.GetWindow(hwnd, GW_OWNER):
            found.append(hwnd)
        return True

    user32.EnumWindows(visit, 0)
    for hwnd in found:
        rect = wt.RECT()
        user32.GetClientRect(hwnd, ctypes.byref(rect))
        corner = wt.POINT(0, 0)
        user32.ClientToScreen(hwnd, ctypes.byref(corner))
        width, height = rect.right & ~1, rect.bottom & ~1   # even sizes for yuv420p
        if width >= 64 and height >= 64:
            return corner.x, corner.y, width, height
    return None


def on_primary(rect: tuple[int, int, int, int]) -> bool:
    """True when the rectangle lies fully on the primary monitor (the tested setup)."""
    user32, _ = _win32()
    x, y, width, height = rect
    return (x >= 0 and y >= 0 and x + width <= user32.GetSystemMetrics(SM_CXSCREEN)
            and y + height <= user32.GetSystemMetrics(SM_CYSCREEN))


class ProcessWatch:
    """Non-blocking liveness check (tasklist stalls the poller for ~0.5 s)."""

    def __init__(self, pid: int) -> None:
        """Open a SYNCHRONIZE handle.

        Raises:
            OSError: when the process cannot be opened.
        """
        _, self.kernel32 = _win32()
        self.handle = self.kernel32.OpenProcess(SYNCHRONIZE, False, pid)
        if not self.handle:
            raise OSError(ctypes.get_last_error(), f"OpenProcess({pid}) failed")

    def alive(self) -> bool:
        """True while the watched process has not exited."""
        return self.kernel32.WaitForSingleObject(self.handle, 0) == WAIT_TIMEOUT

    def close(self) -> None:
        """Release the process handle."""
        if self.handle:
            self.kernel32.CloseHandle(self.handle)
            self.handle = None


# ---- record ----------------------------------------------------------------

class Tail:
    """Incremental reader of a byte log that the game may recreate."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.position = 0
        self.pending = b""

    def lines(self) -> list[str]:
        """Complete new lines since the last call."""
        try:
            size = self.path.stat().st_size
            if size < self.position:
                self.position, self.pending = 0, b""
            if size == self.position:
                return []
            with self.path.open("rb") as handle:
                handle.seek(self.position)
                chunk = handle.read(size - self.position)
            self.position += len(chunk)
        except OSError:
            return []
        parts = (self.pending + chunk).split(b"\n")
        self.pending = parts.pop()
        return [p.decode("utf-8", "replace").rstrip("\r") for p in parts if p.strip()]


def read_heartbeat(path: Path, not_before: float) -> int | None:
    """Current heartbeat frame, ignoring a file not rewritten since not_before."""
    try:
        if path.stat().st_mtime < not_before:
            return None
        return parse_heartbeat(path.read_text(encoding="ascii", errors="replace"))
    except OSError:
        return None


def copy_audio(game_dir: Path, out: Path, not_before: float) -> list[str]:
    """Copy this session's audio dump at stop, before a relaunch can replace it."""
    copied = []
    for name in (AUDIO_WAV, AUDIO_SYNC):
        source = game_dir / name
        try:
            if source.stat().st_mtime >= not_before:
                shutil.copy2(source, out / name)
                copied.append(name)
        except OSError as error:
            logger.warning("audio copy %s failed: %s", name, error)
    return copied


def clock_probe_identity(game_dir: Path) -> tuple[int, int, int, int] | None:
    """Snapshot file identity/activity without trusting the civil-clock epoch."""
    try:
        stat = (game_dir / "bag2jp_clock_probe.csv").stat()
        return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns
    except FileNotFoundError:
        return None
    except OSError as error:
        logger.warning("clock probe identity unavailable: %s", error)
        return None


def copy_clock_probe(game_dir: Path, out: Path,
                     initial: tuple[int, int, int, int] | None) -> bool:
    """Retain diagnostics even when activity is ambiguous; copying is not validation."""
    source = game_dir / "bag2jp_clock_probe.csv"
    try:
        current = clock_probe_identity(game_dir)
        if current is None:
            return False
        if current == initial:
            logger.warning("clock probe unchanged during capture; retaining ambiguous diagnostics")
        shutil.copy2(source, out / source.name)
        return True
    except FileNotFoundError:
        return False  # Older runtimes do not emit the optional sidecar.
    except OSError as error:
        logger.warning("clock probe copy failed: %s", error)
        return False


class ClockObservations:
    """Best-effort diagnostic sidecar; its I/O cannot abort the primary capture."""

    def __init__(self, path: Path) -> None:
        self.file = None
        self.writer = None
        try:
            self.file = path.open("w", newline="", encoding="ascii")
            self.writer = csv.writer(self.file)
            self.write(["frame", "mono_before_ns", "mono_after_ns",
                        "wall_before_ns", "wall_after_ns"])
        except OSError as error:
            self._disable(error)

    def _disable(self, error: OSError) -> None:
        logger.warning("clock observations disabled: %s", error)
        self.writer = None
        self.close()

    def write(self, row: list[int | str | None]) -> None:
        """Append a bracket, disabling only this diagnostic after an I/O failure."""
        if self.writer is not None:
            try:
                self.writer.writerow(row)
            except OSError as error:
                self._disable(error)

    def close(self) -> None:
        """Flush/close once; delayed filesystem failures remain diagnostic warnings."""
        handle, self.file = self.file, None
        self.writer = None
        if handle is not None:
            try:
                handle.close()
            except OSError as error:
                logger.warning("clock observations close failed: %s", error)

    def __enter__(self) -> ClockObservations:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def _kill_ffmpeg(ffmpeg: subprocess.Popen) -> None:
    """Reap our child even if a second Ctrl+C arrives during cleanup."""
    while True:
        try:
            if ffmpeg.poll() is not None:
                return
            ffmpeg.kill()
            ffmpeg.wait(timeout=FFMPEG_EXTRA_SECONDS)
            return
        except (KeyboardInterrupt, subprocess.TimeoutExpired):
            continue


def stop_ffmpeg(ffmpeg: subprocess.Popen, validate: Callable[[], None] | None = None) -> str:
    """Keep checking the window until FFmpeg stops; never release an orphan."""
    try:
        if validate:
            validate()
        if ffmpeg.poll() is not None:
            return ""
        try:
            ffmpeg.stdin.write(b"q")
            ffmpeg.stdin.flush()
        except (BrokenPipeError, OSError):
            pass
        deadline = time.monotonic() + FFMPEG_QUIT_SECONDS
        while ffmpeg.poll() is None:
            if validate:
                validate()
            try:
                ffmpeg.wait(timeout=FFMPEG_STOP_POLL_SECONDS)
            except subprocess.TimeoutExpired:
                if time.monotonic() >= deadline:
                    _kill_ffmpeg(ffmpeg)
                    return "; ffmpeg killed"
        if validate:
            validate()
        return ""
    except (OSError, RuntimeError, KeyboardInterrupt, SystemExit):
        _kill_ffmpeg(ffmpeg)
        raise


def _write_session(path: Path, session: dict) -> None:
    """Publish a complete snapshot, never a half-written restoration status."""
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(session, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def resolve_wgc_ffmpeg() -> Path | None:
    """Locate FFmpeg >= 8.0 with Windows.Graphics.Capture (gfxcapture) support."""
    configured = os.environ.get(FFMPEG_WGC_ENV)
    if configured is not None:
        candidate = Path(configured) if configured else None
        return candidate if candidate and candidate.is_file() else None
    return DEFAULT_FFMPEG_WGC if DEFAULT_FFMPEG_WGC.is_file() else None


def resolve_capture_backend(backend: str = "auto") -> tuple[str, str]:
    """Select video capture backend ('wgc' or 'gdigrab') and FFmpeg executable."""
    if backend == "gdigrab":
        return "gdigrab", "ffmpeg"
    if backend in ("auto", "wgc"):
        wgc = resolve_wgc_ffmpeg()
        if wgc is not None:
            return "wgc", str(wgc)
        if backend == "wgc":
            raise RuntimeError("WGC capture requested, but FFmpeg with gfxcapture was not found")
        return "gdigrab", "ffmpeg"
    raise ValueError(f"unsupported capture backend: {backend}")


def record(tag: str, fps: int, max_seconds: float, game_dir: Path,
           capture_backend: str = "auto") -> int:
    """Capture until STOP file, game exit or timeout. Returns a process exit code."""
    out = RECORDINGS / tag
    if out.exists():
        logger.error("%s exists; choose a new tag", out)
        return 2
    try:
        backend, ffmpeg_bin = resolve_capture_backend(capture_backend)
    except (RuntimeError, ValueError) as error:
        logger.error("recording refused: %s", error)
        return EXIT_REJECTED
    user32, _ = _win32()
    if not user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(DPI_PER_MONITOR_AWARE_V2)):
        logger.warning("DPI awareness not set (error %d); coordinates may be scaled",
                       ctypes.get_last_error())
    deadline = time.time() + WINDOW_WAIT_SECONDS
    pid = rect = None
    while time.time() < deadline and not rect:
        pid = game_pid(game_dir)
        rect = client_rect(pid) if pid else None
        if not rect:
            time.sleep(0.5)
    if not pid or not rect:
        logger.error("no visible %s window from %s within %.0f s", GAME_EXE, game_dir, WINDOW_WAIT_SECONDS)
        return 3
    if backend == "gdigrab" and not on_primary(rect):
        logger.error("game client area %s is not fully on the primary monitor; move it there", rect)
        return 3
    window, watch = None, None
    try:
        hwnd = find_window(pid)
        if not hwnd:
            raise RuntimeError("capture window disappeared")
        window = (RecordingWindow(hwnd, pid) if backend == "gdigrab"
                  else RecordingWindow(hwnd, pid, require_uncovered=False))
        with window:
            rect = window.bounds
            if backend == "gdigrab" and not on_primary(rect):
                raise RuntimeError("capture window is not fully on the primary monitor")
            watch = ProcessWatch(pid)
            if backend == "gdigrab":
                return _record_capture(tag, fps, max_seconds, game_dir, pid, rect, window, watch)
            return _record_capture(tag, fps, max_seconds, game_dir, pid, rect, window, watch,
                                   capture_backend=backend, ffmpeg_bin=ffmpeg_bin)
    except (OSError, RuntimeError) as error:
        logger.error("recording refused: %s", error)
        return EXIT_REJECTED
    finally:
        if watch:
            watch.close()
        session_path = out / "session.json"
        if window and session_path.exists():
            session = json.loads(session_path.read_text(encoding="utf-8"))
            session["window_guard"] = window.summary()
            session["recording_state"] = "closed"
            _write_session(session_path, session)


def _record_capture(tag: str, fps: int, max_seconds: float, game_dir: Path, pid: int,
                    rect: tuple[int, int, int, int], window: RecordingWindow,
                    watch: ProcessWatch, capture_backend: str = "gdigrab",
                    ffmpeg_bin: str | Path = "ffmpeg") -> int:
    """Record only inside the capture window guard's lifetime."""
    out = RECORDINGS / tag
    out.mkdir(parents=True)
    x, y, width, height = rect
    if capture_backend == "wgc":
        command = [str(ffmpeg_bin), "-hide_banner", "-nostats", "-use_wallclock_as_timestamps", "1",
                   "-f", "lavfi", "-i",
                   f"gfxcapture=hwnd={window.hwnd}:max_framerate={fps}:capture_cursor=0",
                   "-vf", "hwdownload,format=bgra,crop=trunc(iw/2)*2:trunc(ih/2)*2:0:0",
                   "-t", str(int(max_seconds) + FFMPEG_EXTRA_SECONDS), "-fps_mode", "passthrough",
                   "-c:v", "libx264", "-qp", "0", "-preset", "ultrafast", str(out / "raw.mkv")]
    else:
        command = [str(ffmpeg_bin), "-hide_banner", "-nostats", "-f", "gdigrab", "-framerate", str(fps),
                   "-draw_mouse", "0", "-offset_x", str(x), "-offset_y", str(y),
                   "-video_size", f"{width}x{height}", "-i", "desktop",
                   "-t", str(int(max_seconds) + FFMPEG_EXTRA_SECONDS), "-fps_mode", "passthrough",
                   "-c:v", "libx264", "-qp", "0", "-preset", "ultrafast", str(out / "raw.mkv")]
    producer_probe_before = clock_probe_identity(game_dir)
    started = time.time()
    session = {"tag": tag, "pid": pid, "rect": rect, "fps": fps, "game_dir": str(game_dir),
                "game_exe_sha256": sha256(game_dir / GAME_EXE), "capture_backend": capture_backend,
                "command": command, "record_started": started, "recording_state": "recording",
                "window_guard": {"passed": False, "pending": True}}
    _write_session(out / "session.json", session)
    heartbeat = game_dir / HEARTBEAT
    versions = Tail(game_dir / VERSIONS_LOG)
    versions.lines()   # skip lines written before the recording
    reason, beats_seen = "timeout", 0
    with (out / "ffmpeg.log").open("w", encoding="utf-8") as ffmpeg_log, \
          (out / "heartbeat.csv").open("w", newline="") as beats_file, \
          (out / "events.csv").open("w", newline="", encoding="utf-8") as events_file, \
          ClockObservations(out / "clock_observations.csv") as observations:
        window.check()
        ffmpeg = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                  stderr=ffmpeg_log)
        try:
            beats, events = csv.writer(beats_file), csv.writer(events_file)
            last_frame = None
            stop_at = started + max_seconds
            next_alive_check = started + ALIVE_CHECK_SECONDS
            while time.time() < stop_at:
                if (out / "STOP").exists():
                    reason = "stop file"
                    break
                if ffmpeg.poll() is not None:
                    reason = "ffmpeg exited"
                    break
                mono_before, wall_before = time.perf_counter_ns(), time.time_ns()
                frame = read_heartbeat(heartbeat, started)
                now = time.time()
                mono_after, wall_after = time.perf_counter_ns(), time.time_ns()
                # Keep repeated/missing frames: they distinguish a stopped producer
                # from a delayed poller. This file never feeds HeartbeatClock/finalize.
                observations.write([frame, mono_before, mono_after, wall_before, wall_after])
                if frame is not None and frame != last_frame:
                    beats.writerow([f"{now:.6f}", frame])
                    last_frame, beats_seen = frame, beats_seen + 1
                for line in versions.lines():
                    events.writerow([f"{now:.6f}", line])
                if now >= next_alive_check:
                    next_alive_check = now + ALIVE_CHECK_SECONDS
                    if not watch.alive():
                        reason = "game exited"
                        session["capture_error"] = "capture process exited before recorder stopped"
                        break
                    window.check()
                time.sleep(POLL_SECONDS)
            window.check()
        except KeyboardInterrupt:
            reason = "interrupted"
            session["capture_error"] = "recording interrupted"
        except (OSError, RuntimeError) as error:
            reason = f"capture aborted: {error}"
            session["capture_error"] = str(error)
        finally:
            try:
                reason += stop_ffmpeg(ffmpeg, window.check)
            except (OSError, RuntimeError, KeyboardInterrupt, SystemExit) as error:
                session["capture_error"] = f"capture shutdown interrupted or unsafe: {error}"
            session.update(record_ended=time.time(), stop_reason=reason, ffmpeg_exit=ffmpeg.returncode,
                             heartbeats=beats_seen, audio_copied=copy_audio(game_dir, out, started),
                              producer_clock_copied=copy_clock_probe(game_dir, out, producer_probe_before),
                              producer_clock_initial_identity=producer_probe_before,
                              producer_clock_final_identity=clock_probe_identity(game_dir),
                            recording_state="restoring")
            _write_session(out / "session.json", session)
    logger.info("recorded %s: %s, ffmpeg exit %s, %d heartbeats, audio %s", out, reason,
                ffmpeg.returncode, beats_seen, session["audio_copied"] or "none")
    if session.get("capture_error"):
        return EXIT_REJECTED
    if beats_seen < MIN_HEARTBEATS:
        logger.error("no frame clock: start the game with BAG2JP_ANIM_TRACE=1")
        return EXIT_REJECTED
    return 0 if ffmpeg.returncode == 0 else 4


# ---- finalize --------------------------------------------------------------

def read_rows(path: Path) -> list[list[str]]:
    """CSV rows of a recording side file."""
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.reader(handle))


def load_clock(out: Path) -> tuple[HeartbeatClock, float]:
    """Frame clock and video start of a recording folder."""
    video_start = parse_ffmpeg_start((out / "ffmpeg.log").read_text(encoding="utf-8", errors="replace"))
    rows = [(float(w), int(f)) for w, f in read_rows(out / "heartbeat.csv")]
    return HeartbeatClock(rows), video_start


def gates(clock: HeartbeatClock, audio: dict) -> list[str]:
    """Reasons the alignment cannot be trusted; empty when accepted."""
    reasons = []
    expected = (clock.frames[-1] - clock.frames[0]) // HEARTBEAT_STRIDE + 1
    if clock.observed < 0.9 * expected:
        reasons.append(f"heartbeats {clock.observed} of ~{expected}: poller missed updates")
    if len(clock.dropped) > MAX_DROPPED_FRACTION * clock.observed:
        reasons.append(f"{len(clock.dropped)} late heartbeats dropped (> {MAX_DROPPED_FRACTION:.0%})")
    if clock.jitter_p99_ms > clock.period * 1000.0:
        reasons.append(f"heartbeat jitter p99 {clock.jitter_p99_ms:.1f} ms > 1 frame")
    if audio.get("error"):
        reasons.append(f"audio: {audio['error']}")
    else:
        if abs(audio["rate_hz"] / AUDIO_RATE - 1.0) > MAX_AUDIO_RATE_ERROR:
            reasons.append(f"audio: effective rate {audio['rate_hz']} Hz is > "
                           f"{MAX_AUDIO_RATE_ERROR:.0%} from {AUDIO_RATE} (pause or wrong dump)")
        if audio["dropped"] > MAX_AUDIO_DROPPED * audio["pairs"]:
            reasons.append(f"audio: {audio['dropped']} of {audio['pairs']} sync pairs > "
                           f"{AUDIO_OUTLIER_SECONDS * 1000:.0f} ms off the fitted placement "
                           "(torn lines, a pause or drift)")
        if audio["window_max_ms"] > clock.period * 1000.0:
            reasons.append(f"audio: a 1 s window is {audio['window_max_ms']:.0f} ms off the fitted "
                           "placement (> 1 frame; pause or drift)")
    return reasons


def run_ffmpeg(arguments: list[str], cwd: Path) -> None:
    """Run FFmpeg in cwd, raising with its last lines on failure."""
    result = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *arguments],
                            capture_output=True, text=True, encoding="utf-8", errors="replace",
                            check=False, cwd=cwd)
    if result.returncode:
        raise RuntimeError(result.stderr[-2000:])


def finalize(tag: str) -> int:
    """Build videos, events.json and manifest.json; exit 0 only if every gate passed."""
    out = RECORDINGS / tag
    session = json.loads((out / "session.json").read_text(encoding="utf-8"))
    if "recording_state" in session and session["recording_state"] != "closed":
        logger.error("recording or window restoration is still pending; finalize refused")
        return EXIT_REJECTED
    clock, video_start = load_clock(out)
    audio: dict = {}
    if (out / AUDIO_WAV).exists() and (out / AUDIO_SYNC).exists():
        try:
            audio = audio_placement(
                clock, parse_sync_log((out / AUDIO_SYNC).read_text(encoding="ascii", errors="replace")),
                video_start)
        except ValueError as error:
            audio = {"error": str(error)}
    else:
        audio = {"error": "no audio dump copied (start the game with BAG2JP_AUDIO_DUMP=1)"}
    height = int(session["rect"][3])
    write_labels(out / LABELS, clock, video_start, height)
    clock_text = (f"drawtext=fontfile='C\\:/Windows/Fonts/consola.ttf':fontsize={max(12, height // 22)}:"
                  f"fontcolor=white:box=1:boxcolor=black@0.6:x=6:y={max(12, height // 22) * 2}:"
                  f"text='t %{{pts\\:hms}}'")
    has_audio = "offset_s" in audio
    inputs = ["-i", "raw.mkv"] + (["-ignore_length", "1", "-i", AUDIO_WAV] if has_audio else [])
    graph = f"[0:v]subtitles={LABELS},{clock_text}[v]"
    if has_audio:
        graph += f";[1:a]{audio_filter(audio['offset_s'], media_duration(out / 'raw.mkv'), audio['rate_hz'])}[a]"
    maps = ["-map", "[v]"] + (["-map", "[a]"] if has_audio else [])
    run_ffmpeg([*inputs, "-filter_complex", graph, *maps, "-fps_mode", "passthrough",
                "-c:v", "libx264", "-qp", "0", "-preset", "ultrafast", "-c:a", "flac",
                "review.mkv"], out)
    run_ffmpeg([*inputs, "-filter_complex", graph, *maps, "-fps_mode", "passthrough",
                "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "owner.mp4"], out)
    events = [{"video_time": round(float(w) - video_start, 3),
               "game_frame": math.floor(clock.frame_of(float(w))), "line": line}
              for w, line in read_rows(out / "events.csv")]
    (out / "events.json").write_text(json.dumps(events, indent=1, ensure_ascii=False), encoding="utf-8")
    reasons = gates(clock, audio)
    if session.get("capture_error"):
        reasons.append(f"capture: {session['capture_error']}")
    if "window_guard" in session and not session["window_guard"].get("passed"):
        reasons.append("capture: foreground/topmost/visibility guard or restoration failed")
    if "recording_state" in session and session.get("ffmpeg_exit") != 0:
        reasons.append("capture: FFmpeg did not exit cleanly")
    capture_backend = session.get("capture_backend", "gdigrab")
    limits = ["label = frame reported by the plugin; display latency uncalibrated"]
    if capture_backend == "wgc":
        limits.append("wgc capture ignores overlapping windows, but requires the target window to remain visible and unminimized")
    else:
        limits.append("tested on the primary monitor at 125 % scaling only")
    manifest = {"accepted": not reasons, "rejections": reasons, "capture_backend": capture_backend,
                "session": session, "video_start": video_start, "clock": clock.summary(),
                "audio": audio, "events": len(events), "limits": limits,
                "files": {p.name: sha256(p) for p in sorted(out.iterdir())
                          if p.is_file() and p.name != "manifest.json"}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    summary = clock.summary()
    logger.info("finalized %s: %s; heartbeats %d (dropped %d), jitter p99 %.1f ms, %.3f fps, "
                "stalls %d, audio %s, %d events", out, "ACCEPTED" if not reasons else "REJECTED",
                summary["observed"], summary["dropped_late"], summary["jitter_p99_ms"], summary["fps"],
                len(summary["stalls"]), audio, len(events))
    for reason in reasons:
        logger.error("rejected: %s", reason)
    return 0 if not reasons else EXIT_REJECTED


def frames(tag: str, frame: int, span: int, step: int) -> int:
    """Extract review stills around a game frame through ffmpeg-skill look.py."""
    out = RECORDINGS / tag
    clock, video_start = load_clock(out)
    stills = out / "stills"
    stills.mkdir(exist_ok=True)
    command = [sys.executable, str(LOOK), str(out / "review.mkv"), "-o",
               str(stills / f"gf{frame:07d}"), "--overwrite"]
    times = []
    for target in range(frame - span, frame + span + 1, step):
        # Middle of the frame's slot, so the still shows that label.
        at = (clock.wall_of(target) + clock.wall_of(target + 1)) / 2 - video_start
        if at < 0:
            logger.warning("game frame %d precedes the video; skipped", target)
            continue
        times.append(at)
    if not times:
        return 2
    for at in times:
        command += ["--at", f"{at:.3f}"]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    logger.info("%s", (result.stdout or result.stderr).strip()[-1500:])
    return result.returncode


def main() -> int:
    """Command-line entry point."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    rec = sub.add_parser("record")
    rec.add_argument("--tag", required=True)
    rec.add_argument("--fps", type=int, default=60)
    rec.add_argument("--max-seconds", type=float, default=900.0)
    rec.add_argument("--game-dir", type=Path, default=GAME_DIR)
    rec.add_argument("--capture-backend", choices=("auto", "wgc", "gdigrab"), default="auto")
    fin = sub.add_parser("finalize")
    fin.add_argument("--tag", required=True)
    fr = sub.add_parser("frames")
    fr.add_argument("--tag", required=True)
    fr.add_argument("--frame", type=int, required=True)
    fr.add_argument("--span", type=int, default=6)
    fr.add_argument("--step", type=int, default=1)
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", args.tag):
        parser.error("tag: use 1-64 ASCII letters, digits, _ or -")
    if args.command == "record":
        return record(args.tag, args.fps, args.max_seconds, args.game_dir,
                      capture_backend=args.capture_backend)
    if args.command == "finalize":
        return finalize(args.tag)
    return frames(args.tag, args.frame, args.span, max(1, args.step))


if __name__ == "__main__":
    sys.exit(main())
