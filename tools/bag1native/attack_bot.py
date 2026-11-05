"""Press a native BAG1 button exactly on the bar boundary, driven by game RAM.

Usage:
  py -3.13 tools/bag1native/attack_bot.py [--player 1] [--seconds 60] [--every 1] [--vk 0x41] [--max 2]

RAM facts (SCUS_942.63, see tools/bag1native/README.md):
  0x80068704 bit 0x10 rises on the bar boundary (4th beat); bit 0x02 marks the
  bar evaluation a few frames later (FUN_80021c6c scans the input history).
  0x80068766 + p*0x14 (s16) = remaining attacks; 0x8006875e + p*0x14 flags
  (|= 0x0c when the attack is accepted, |= 0x900 when it backfires).
The key (default VK 'A' = P1 Triangle with the temporary keybinds) is sent with
keybd_event only while the game window is in the foreground.
"""
from __future__ import annotations

import argparse
import ctypes
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bag1_mem import Bag1Mem  # noqa: E402

user32 = ctypes.WinDLL("user32")
FLAG_ADDR, ATTACKS_ADDR, STATE_ADDR, BEAT_ADDR = 0x8006875E, 0x80068766, 0x80068704, 0x80068440


def foreground_pid() -> int:
    pid = ctypes.c_ulong()
    user32.GetWindowThreadProcessId(user32.GetForegroundWindow(), ctypes.byref(pid))
    return pid.value


def tap(vk: int, hold_s: float = 0.08, extended: bool = False) -> None:
    scan = user32.MapVirtualKeyA(vk, 0)
    flags_down = 1 if extended else 0
    flags_up = flags_down | 2
    user32.keybd_event(vk, scan, flags_down, 0)
    time.sleep(hold_s)
    user32.keybd_event(vk, scan, flags_up, 0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--player", type=int, default=1)
    ap.add_argument("--seconds", type=float, default=60)
    ap.add_argument("--every", type=int, default=1, help="press on every Nth bar")
    ap.add_argument("--max", type=int, default=2, help="stop after this many accepted attacks")
    ap.add_argument("--vk", type=lambda s: int(s, 0), default=0x41)
    ap.add_argument("--lead", type=float, default=0.0, help="seconds to wait after the boundary edge")
    ap.add_argument("--log", type=Path)
    args = ap.parse_args()

    mem = Bag1Mem()
    p = args.player - 1
    events, prev_state, bar, accepted = [], mem.u32(STATE_ADDR), 0, 0
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < args.seconds and accepted < args.max:
        state = mem.u32(STATE_ADDR)
        if state & 0x10 and not prev_state & 0x10:
            bar += 1
            attacks = mem.s16(ATTACKS_ADDR + p * 0x14)
            if bar % args.every == 0 and attacks > 0 and foreground_pid() == mem.pid:
                if args.lead:
                    time.sleep(args.lead)
                tap(args.vk)
                t_press = time.perf_counter() - t0
                time.sleep(0.25)  # evaluation (bit 0x02) follows within a few frames
                flags = mem.u16(FLAG_ADDR + p * 0x14)
                after = mem.s16(ATTACKS_ADDR + p * 0x14)
                ok = after < attacks
                accepted += ok
                ev = {"t": round(t_press, 3), "bar": bar, "beat": mem.u32(BEAT_ADDR) & 0xFFFF,
                      "attacks_before": attacks, "attacks_after": after, "flags": hex(flags), "accepted": ok}
                events.append(ev)
                print(json.dumps(ev), flush=True)
        prev_state = state
        time.sleep(0.001)
    if args.log:
        args.log.write_text(json.dumps(events, indent=1), encoding="utf-8")
    return 0 if accepted else 1


if __name__ == "__main__":
    sys.exit(main())
