"""Automate entering a 2P match and recording an attack in native BAG1.

Usage:
  py -3.13 tools/bag1native/run_match_and_attack.py --out-dir <dir>
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

u = ctypes.windll.user32
VK_RETURN = 0x0D
VK_DOWN = 0x28
VK_UP = 0x26
VK_LEFT = 0x27
VK_RIGHT = 0x29
VK_S = 0x53   # P1 Circle (Confirm)
VK_X = 0x58   # P1 Cross (Cancel)
VK_A = 0x41   # P1 Triangle (Attack)
VK_M = 0x4D   # P2 Circle (Confirm)
VK_N = 0x4E   # P2 Cross (Cancel)
VK_V = 0x56   # P2 Triangle (Attack)


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
    u.SetForegroundWindow(hwnd)
    time.sleep(0.2)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--p1-char", type=int, default=0, help="0=Heat, 1=Strike, etc.")
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

    print("Character Select: P1 Heat, P2 Frida...")
    activate(hwnd)
    tap(VK_S)
    time.sleep(1.0)
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

    video_path = args.out_dir / "heat-native-attack.mp4"
    ff_cmd = [
        r"D:\ffmpeg\bin\ffmpeg.exe", "-y", "-loglevel", "error",
        "-filter_complex", "ddagrab=output_idx=0:framerate=60:offset_x=360:offset_y=0:video_size=1840x1380,hwdownload,format=bgra,scale=920:690",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-t", str(args.duration),
        str(video_path)
    ]
    ff = subprocess.Popen(ff_cmd)

    print("Waiting for dance to start...")
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < 30.0:
        state = mem.u32(STATE_ADDR)
        if state & 0x01:
            print(f"Dance active! state={state:#x} beat={mem.u32(BEAT_ADDR)&0xffff}")
            break
        time.sleep(0.05)

    print("Running attack bot...")
    events, prev_state, bar, accepted = [], mem.u32(STATE_ADDR), 0, 0
    t_start = time.perf_counter()
    while time.perf_counter() - t_start < 25.0 and accepted < 2:
        state = mem.u32(STATE_ADDR)
        if state & 0x10 and not prev_state & 0x10:
            bar += 1
            attacks = mem.s16(ATTACKS_ADDR)
            if attacks > 0:
                activate(hwnd)
                tap(VK_A)
                t_press = time.perf_counter() - t_start
                time.sleep(0.25)
                flags = mem.u16(FLAG_ADDR)
                after = mem.s16(ATTACKS_ADDR)
                ok = after < attacks
                accepted += ok
                ev = {
                    "t": round(t_press, 3), "bar": bar, "beat": mem.u32(BEAT_ADDR) & 0xFFFF,
                    "attacks_before": attacks, "attacks_after": after,
                    "flags": hex(flags), "accepted": ok
                }
                events.append(ev)
                print(json.dumps(ev), flush=True)
        prev_state = state
        time.sleep(0.001)

    (args.out_dir / "heat-native-attack.json").write_text(json.dumps(events, indent=2), encoding="utf-8")
    print(f"Attacks accepted: {accepted}/2. Waiting for video to finish...")
    ff.wait()
    print(f"Video saved to {video_path} ({video_path.stat().st_size} bytes)")
    return 0 if accepted else 1


if __name__ == "__main__":
    sys.exit(main())
