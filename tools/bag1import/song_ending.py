"""BAG1 song endings: the BAG1 in-game edit cuts the song at the end of the dance (Heat 2Bad: a short
gap at 123.37 s, then a soft tail), while the CD keeps playing. The CD render switches to the game's
tail there (level-matched), and both versions fade to silence by STOP s, the song length the plugin
gives the game (main exe table 0x800555A8, seconds) so the result/fever phase does not wait for the
end of BAG2's longer XA slot.
usage: song_ending.py <game.wav> <cd_render.flac> <out_dir> <name> <cut_s> <fade_start_s> <stop_s>"""
import numpy as np, subprocess, sys
SR = 44100
def load(f): return np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', f, '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout, dtype=np.float32).reshape(-1, 2).copy()
def save(x, f): subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', '-sample_fmt', 's16', '-compression_level', '8', f], input=np.clip(x, -1, 1).astype(np.float32).tobytes())
gw, cf, out, name = sys.argv[1:5]; cut, f0, stop = map(float, sys.argv[5:8])
g, c = load(gw), load(cf); n = min(len(g), len(c)); g, c = g[:n], c[:n]
rms = lambda x: float(np.sqrt((x ** 2).mean()) + 1e-9)
ratio = np.median([rms(c[t * SR:(t + 1) * SR]) / rms(g[t * SR:(t + 1) * SR]) for t in range(20, int(cut) - 5)])
k = int(cut * SR); X = int(0.01 * SR); w = np.linspace(0, 1, X)[:, None]
cd = c.copy(); cd[k:] = g[k:] * ratio; cd[k - X:k] = c[k - X:k] * (1 - w) + g[k - X:k] * ratio * w
fade = np.ones(n); a, b = int(f0 * SR), int(stop * SR); fade[a:b] = np.linspace(1, 0, b - a) ** 2; fade[b:] = 0
for x, tag in ((cd, 'cd'), (g.copy(), 'game')):
    save(x * fade[:, None], f'{out}/{name}_{tag}.flac')
print('level ratio cd/game', round(ratio, 3))
