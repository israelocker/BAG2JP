"""Locate a song FLAC inside a BAG2JP audio dump by cross-correlation.
usage: python xcorr.py <take_dir> <song.wav 44.1k mono> <request_frame> <gate_frame>"""
import sys, wave
import numpy as np

E, S, req, gate = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
sync = dict(tuple(map(int, l.split())) for l in open(E + "/bag2jp_audio_sync.log"))
w = wave.open(E + "/bag2jp_audio.wav"); sr = w.getframerate(); ch = w.getnchannels()
a = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, ch).astype(float).mean(1)
s = wave.open(S); b = np.frombuffer(s.readframes(s.getnframes()), np.int16).astype(float)
s0 = sync[req]
seg = a[s0 - sr: s0 + 4 * sr]            # 1 s before request .. 4 s after
ref = b[: 3 * sr]                        # first 3 s of the song
n = 1 << int(np.ceil(np.log2(len(seg) + len(ref))))
c = np.fft.irfft(np.fft.rfft(seg, n) * np.conj(np.fft.rfft(ref, n)), n)[: len(seg) - len(ref)]
k = int(np.argmax(c)); norm = c[k] / (np.linalg.norm(ref) * np.linalg.norm(seg[k:k + len(ref)]) + 1e-9)
t = (k - sr) / sr * 1000
print(f"song sample 0 at {t:.1f} ms after request; gate at {(gate - req) * 1000 / 59.94:.1f} ms; "
      f"music-gate {t - (gate - req) * 1000 / 59.94:+.1f} ms; corr {norm:.2f}")
