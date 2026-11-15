"""Automate entering a 1P/2P match and recording Gas-O attack in native BAG1.

Usage:
  py -3.13 tools/bag1native/run_match_and_attack.py --out-dir <dir> --p1-char 9
"""
from __future__ import annotations

import argparse
import ctypes
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bag1_mem import Bag1Mem
from attack_bot import tap, STATE_ADDR, ATTACKS_ADDR, FLAG_ADDR, BEAT_ADDR

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.workflow.project_config import load_config, require_paths

u = ctypes.windll.user32
VK_RETURN = 0x0D
VK_DOWN = 0x28
VK_UP = 0x26
VK_LEFT = 0x25
VK_RIGHT = 0x27
VK_S = 0x53   # P1 Circle (Confirm)
VK_X = 0x58   # P1 Cross (Cancel)
VK_A = 0x41   # P1 Triangle (Attack)
VK_M = 0x4D   # P2 Circle (Confirm)
VK_N = 0x4E   # P2 Cross (Cancel)
VK_V = 0x56   # P2 Triangle (Attack)


def ffmpeg_native(config=None) -> Path:
    """Resolve the native BAG1 capture FFmpeg from the shared host config.

    Fails fast with a clear error if the machine location is not configured
    in config/project.local.toml (never a hardcoded machine path).
    """
    if config is None:
        config = load_config(repo_root=Path(__file__).resolve().parents[2])
    path, = require_paths(config, ("tools.ffmpeg_native",))
    return path


def get_hwnd(pid: int) -> int:
    hwnd = 0
    def cb(h, _):
        nonlocal hwnd
        p = ctypes.c_ulong()
        u.GetWindowThreadProcessId(h, ctypes.byref(p))
        if p.value == pid:
            hwnd = h
            return False
        return True
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    u.EnumWindows(WNDENUMPROC(cb), 0)
    return hwnd


def activate(hwnd: int) -> None:
    u.ShowWindow(hwnd, 9)
    u.SetForegroundWindow(hwnd)
    time.sleep(0.3)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--p1-char", type=int, default=9, help="0=Heat, 1=Strike, 9=Gas-O")
    ap.add_argument("--duration", type=float, default=45.0)
    args = ap.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    mem = Bag1Mem()
    hwnd = get_hwnd(mem.pid)
    if not hwnd:
        raise RuntimeError("Game window not found")

    activate(hwnd)
    print("Quitting demonstration / returning to Title...")
    tap(VK_RETURN)
    time.sleep(0.5)
    tap(VK_DOWN, extended=True)
    time.sleep(0.3)
    tap(VK_DOWN, extended=True)
    time.sleep(0.3)
    tap(VK_S)
    time.sleep(1.5)

    print("Opening MODE SELECT from Title...")
    activate(hwnd)
    tap(VK_RETURN)
    time.sleep(1.2)

    print("Navigating to 2PLAYER GAME...")
    activate(hwnd)
    tap(VK_DOWN, extended=True)
    time.sleep(0.5)
    tap(VK_S)
    time.sleep(2.0)

    print(f"Navigating P1 character to {args.p1_char}...")
    # On character select screen:
    # 0x80068718 holds P1 char, 0x8006871C holds P2 char
    # We pulse Right/Down until P1 is the target character
    for step in range(25):
        p1 = mem.u32(0x80068718)
        p2 = mem.u32(0x8006871C)
        print(f"Selector step {step}: P1={p1}, P2={p2}")
        if p1 == args.p1_char:
            print(f"P1 reached character {args.p1_char}!")
            break
        activate(hwnd)
        tap(VK_RIGHT, extended=True)
        time.sleep(0.3)
    else:
        # If Right didn't change P1, try Down
        for step in range(25):
            p1 = mem.u32(0x80068718)
            print(f"Selector retry with Down step {step}: P1={p1}")
            if p1 == args.p1_char:
                print(f"P1 reached character {args.p1_char}!")
                break
            activate(hwnd)
            tap(VK_DOWN, extended=True)
            time.sleep(0.3)

    time.sleep(0.5)
    print("Confirming P1...")
    activate(hwnd)
    tap(VK_S)
    time.sleep(1.0)

    print("Confirming P2...")
    activate(hwnd)
    tap(VK_M)
    time.sleep(1.5)

    print("Stage Select: confirming...")
    activate(hwnd)
    tap(VK_S)
    time.sleep(0.5)
    tap(VK_M)
    time.sleep(0.5)
    print("Match confirmed, starting video capture...")

    video_path = args.out_dir / "gaso-native-attack-60fps.mp4"
    ff_cmd = [
        str(ffmpeg_native()), "-y", "-loglevel", "error",
        "-filter_complex", "ddagrab=output_idx=0:framerate=60:offset_x=360:offset_y=0:video_size=1840x1380,hwdownload,format=bgra,scale=920:690",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-t", str(args.duration),
        str(video_path)
    ]
    ff = subprocess.Popen(ff_cmd)

    print("Waiting for dance to start (state & 0x01)...")
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < 35.0:
        state = mem.u32(STATE_ADDR)
        if state & 0x01:
            print(f"Dance active! state={state:#x} beat={mem.u32(BEAT_ADDR)&0xffff}")
            break
        time.sleep(0.05)

    print(f"Running attack bot for P1 (char={args.p1_char})...")
    events, prev_st, bar, accepted = [], mem.u32(STATE_ADDR), 0, 0
    t_start = time.perf_counter()
    while time.perf_counter() - t_start < 30.0 and accepted < 2:
        st = mem.u32(STATE_ADDR)
        # 4th beat detection: 0x10 bit in STATE_ADDR
        if (st & 0x10) and not (prev_st & 0x10):
            bar += 1
            attacks = mem.s16(ATTACKS_ADDR)
            if attacks > 0:
                activate(hwnd)
                tap(VK_A)  # P1 Triangle
                t_press = time.perf_counter() - t_start
                time.sleep(0.25)
                flags = mem.u16(FLAG_ADDR)
                after = mem.s16(ATTACKS_ADDR)
                ok = after < attacks
                accepted += int(ok)
                ev = {
                    "t": round(t_press, 3), "bar": bar, "beat": mem.u32(BEAT_ADDR) & 0xFFFF,
                    "attacks_before": attacks, "attacks_after": after,
                    "flags": hex(flags), "accepted": ok
                }
                events.append(ev)
                print(json.dumps(ev), flush=True)
        prev_st = st
        time.sleep(0.001)

    (args.out_dir / "attack-bot.json").write_text(json.dumps(events, indent=2), encoding="utf-8")
    print(f"Attacks accepted: {accepted}/2. Waiting for video recording to complete...")
    ff.wait()
    print(f"Video saved to {video_path} ({video_path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
