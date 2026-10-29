"""Render v3 (2026-10-29): CD audio only.
v2 (render2.py) played the game's own XA audio wherever the CD could not be mapped (unmapped blocks,
and "game-only" spans with shouts the CD mix lacks), cross-fading between the two; the user heard
those blends as smears and odd cuts. v3 never uses game audio:
- unmapped blocks continue the CD from the previous mapped offset (leading ones take the first);
- every change of CD offset is a splice (refined as in v2, 25 ms equal-power crossfade);
- where the game is silent in an unmapped block (song start/end) the output is silent;
- no game-only spans. Only a game intro that comes before the CD track starts (pos < 0) keeps the
  game audio, since the CD has nothing there; it switches to the CD where the track begins.
Same timeline and length as the game XA channel."""
import numpy as np, os, sys, subprocess, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render2 as r2
OUT, BS, HQ = r2.OUT, r2.BS, r2.HQ

def lead_offset(blocks, win=30, need=20, tol=0.03):
    """First reliable CD offset: a window of `win` blocks where at least `need` raw matches agree."""
    o = [None if t is None else t - 0.1 * b for b, (t, g) in enumerate(blocks)]
    for b in range(len(o) - win):
        vals = [v for v in o[b:b + win] if v is not None]
        if len(vals) < need: continue
        med = float(np.median(vals))
        if sum(1 for v in vals if abs(v - med) < tol) >= need:
            first = next(k for k in range(b, b + win) if o[k] is not None and abs(o[k] - med) < tol)
            return first, med
    return 0, 0.0

def fill_all(off, blocks):
    """Before the first reliable match every block takes its offset (short early matches are
    unreliable); after it, unmapped blocks continue the previous offset."""
    out = list(off); lead, lo = lead_offset(blocks)
    for i in range(lead): out[i] = lo
    prev = lo
    for i in range(len(out)):
        if out[i] is None: out[i] = prev
        prev = out[i]
    return out

def render(name, G):
    m = r2.bm[name]; C = r2.load_cd(int(m['track'])); blocks = m['blocks']; n = len(blocks)
    mapped = [t is not None for t, g in blocks]
    off = fill_all(r2.smooth_offsets(blocks), blocks)
    N = len(G); pos = np.full(N, np.nan)
    R = r2.runs_of(off)
    for (b0, b1) in R:
        s0, s1 = b0 * BS, min(N, b1 * BS)
        if s0 >= N: break
        t = np.arange(s0, s1) / OUT
        bc = np.array([b * 0.1 + 0.05 for b in range(b0, b1)]); bo = np.array([off[b] for b in range(b0, b1)])
        pos[s0:s1] = t + np.interp(t, bc, bo)
    pos[np.isnan(pos)] = (np.arange(N) / OUT + off[-1])[np.isnan(pos)]
    X = int(0.025 * OUT); nsplice = 0
    for i in range(1, len(R)):
        (a0, a1), (c0, c1) = R[i - 1], R[i]
        s = c0 * BS
        if s >= N: break
        oA, oB = off[a1 - 1], off[c0]
        w = int(0.8 * OUT)
        dA, _ = r2.xcorr_refine(G, C, max(0, s - w), s, oA) if mapped[a1 - 1] else (0.0, 0)
        dB, _ = r2.xcorr_refine(G, C, s, min(N, s + w), oB) if mapped[c0] else (0.0, 0)
        oA += dA; oB += dB
        lo, hi = max(0, s - int(0.3 * OUT)), min(N, s + int(0.3 * OUT))
        F = 441; eA = []; eB = []
        for f in range(lo, hi - F, F):
            g = r2.mono(G[f:f + F])
            for o, E in ((oA, eA), (oB, eB)):
                k = int(round(f + o * OUT))
                c = r2.mono(C[k:k + F]) if 0 <= k and k + F <= len(C) else np.zeros(F)
                den = np.linalg.norm(g) * np.linalg.norm(c)
                E.append(1 - (g @ c / den) if den > 1e-6 else 0.5)
        eA, eB = np.array(eA), np.array(eB)
        cost = [eA[:j].sum() + eB[j:].sum() for j in range(len(eA) + 1)]
        sw = lo + int(np.argmin(cost)) * F
        t = np.arange(lo, hi) / OUT
        pos[lo:sw] = t[:sw - lo] + oA; pos[sw:hi] = t[sw - lo:] + oB
        nsplice += 1
    # gain: mapped blocks as v2; unmapped: silent where the game is silent, else the median level
    g = np.array([gg if (t is not None and gg > 0) else np.nan for t, gg in blocks], dtype=float)
    med = np.nanmedian(g)
    rms = np.array([np.sqrt(np.mean(G[b * BS:(b + 1) * BS] ** 2)) if b * BS < N else 0 for b in range(n)])
    for b in range(n):
        if np.isnan(g[b]): g[b] = 0.0 if rms[b] < 0.004 else med
    gl = np.minimum(1.0, g / med)
    k = 10; gs = np.array([np.median(gl[max(0, b - k):b + k + 1]) for b in range(n)]) * med
    # a silent game block stays silent even inside the median window (song edges)
    gs[rms < 0.004] = np.minimum(gs[rms < 0.004], g[rms < 0.004])
    gcurve = np.interp(np.arange(N) / OUT, np.arange(n) * 0.1 + 0.05, gs)
    # before the CD track starts (game-only intro, e.g. Shorty's first 11 s) there is no CD audio:
    # the game's audio plays there, with a plain switch where the CD begins
    pre = pos < 0; pos[pre] = np.nan
    out = r2.synth(G, C, pos, gcurve, X)
    return out, nsplice, round(float(pre.sum()) / OUT, 2)

if __name__ == '__main__':
    dst_dir = f'{HQ}/music_hq3'; os.makedirs(dst_dir, exist_ok=True)
    for name in sys.argv[1:] or list(r2.bm):
        G = np.fromfile(f'{HQ}/xafull/{name}.f32', dtype=np.float32).reshape(-1, 2)
        out, ns, nu = render(name, G)
        tmp = f'{HQ}/_r3.f32'; np.clip(out, -1, 1).astype(np.float32).tofile(tmp)
        dst = f'{dst_dir}/{name}.flac'
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'f32le', '-ar', str(OUT), '-ac', '2', '-i', tmp,
                        '-sample_fmt', 's16', '-compression_level', '8', dst])
        print(name, 'splices', ns, 'game-only intro s', nu, 'score', r2.score(G, out), flush=True)
