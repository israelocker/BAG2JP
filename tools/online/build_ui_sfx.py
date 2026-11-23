#!/usr/bin/env python3
"""Generate crisp PS1-arcade menu SFX WAV files (44.1kHz 16-bit mono)
for the BAG2JP Online Lobby & 1v1 Waiting Room."""

import math
import struct
import wave
from pathlib import Path

OUT_DIR = Path(r"D:\Games\Bust A Groove 2 (Japan)\BAG2JP-exp-8mb\online_avatars")
SR = 44100


def write_wav(path: Path, samples: list[float]) -> None:
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        raw = bytearray()
        for s in samples:
            v = max(-1.0, min(1.0, s))
            raw += struct.pack("<h", int(v * 28000))
        wf.writeframes(bytes(raw))
    print(f"Saved {path.name} ({len(samples)/SR*1000:.0f} ms)")


def tone(freq_start: float, freq_end: float, dur_s: float, amp: float = 0.65, wave_type: str = "tri") -> list[float]:
    n = int(SR * dur_s)
    out = []
    phase = 0.0
    for i in range(n):
        t = i / max(1, n - 1)
        f = freq_start + (freq_end - freq_start) * t
        phase += 2.0 * math.pi * f / SR
        env = min(1.0, i / (SR * 0.004)) * ((1.0 - t) ** 1.6)
        if wave_type == "sq":
            val = 1.0 if math.sin(phase) >= 0 else -1.0
        elif wave_type == "tri":
            val = (2.0 / math.pi) * math.asin(math.sin(phase))
        else:
            val = math.sin(phase)
        out.append(val * env * amp)
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # 1. Cursor move (short crisp PS1 blip)
    write_wav(OUT_DIR / "sfx_cursor.wav", tone(880, 1180, 0.055, 0.55, "tri"))
    # 2. Confirm / Join / Create (two-note upbeat arcade chime)
    write_wav(OUT_DIR / "sfx_confirm.wav", tone(660, 660, 0.06, 0.6, "tri") + tone(990, 1320, 0.12, 0.65, "tri"))
    # 3. Cancel / Back (descending retro tone)
    write_wav(OUT_DIR / "sfx_cancel.wav", tone(520, 260, 0.11, 0.55, "tri"))
    # 4. Error / Blocked START without READY (low double buzz)
    write_wav(OUT_DIR / "sfx_error.wav", tone(190, 160, 0.08, 0.65, "sq") + [0.0] * int(SR * 0.03) + tone(160, 130, 0.12, 0.65, "sq"))
    # 5. READY! (energetic 3-note ascending fanfare)
    write_wav(OUT_DIR / "sfx_ready.wav", tone(587, 587, 0.05, 0.6, "tri") + tone(880, 880, 0.05, 0.6, "tri") + tone(1174, 1568, 0.14, 0.7, "tri"))
    # 6. Chat message notification (soft pop)
    write_wav(OUT_DIR / "sfx_chat.wav", tone(1046, 1318, 0.07, 0.45, "sin"))


if __name__ == "__main__":
    main()
