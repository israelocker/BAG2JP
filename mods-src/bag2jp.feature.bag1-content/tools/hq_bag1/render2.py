"""Render v2 (2026-10-27): fixes audible artefacts of render.py.
1. Offset smoothing: blockmap anchors that flip between repeated passages of the CD (same bar
   in another chorus, often with different shouts) are replaced by the locally dominant offset
   (mode filter, +-1.2 s, 15 ms tolerance). Genuine edits (long runs) are kept.
2. Short unmapped gaps whose two sides are continuous on the CD are filled with the CD.
3. Splices are refined: CD offsets by cross-correlation (+-8 ms) and the switch moment is chosen
   where the two alignments disagree least; 25 ms equal-power crossfade.
4. Level: one smooth gain curve (rolling median over 2 s, linear per sample) instead of a step
   per 100 ms block, so no zipper noise or dips; game fades are still followed.
Output: same timeline and length as the game XA channel (2352 frames per channel sector)."""
import numpy as np, os, json, subprocess, sys
OUT = 44100; BS = 4410
HQ = os.path.expanduser('~/work/hq_b1')
bm = json.load(open(f'{HQ}/blockmap.json'))
CDDIR = os.path.expanduser('~/mnt/Dev/Recomp/BAG2JP/assets/music_cd/Bust a Move')
flacs = sorted(f for f in os.listdir(CDDIR) if f.endswith('.flac'))
TOL = 0.015; WIN = 12

def load_cd(track):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', os.path.join(CDDIR, flacs[track - 1]), '-f', 'f32le',
                        '-ac', '2', '-ar', str(OUT), '-'], capture_output=True).stdout
    return np.frombuffer(r, dtype=np.float32).reshape(-1, 2)

def smooth_offsets(blocks):
    n = len(blocks)
    o = [None if t is None else t - 0.1 * b for b, (t, g) in enumerate(blocks)]
    out = [None] * n
    for b in range(n):
        vals = [o[k] for k in range(max(0, b - WIN), min(n, b + WIN + 1)) if o[k] is not None]
        if not vals: continue
        best, bc = None, 0
        for v in vals:
            c = sum(1 for w in vals if abs(w - v) < TOL)
            if c > bc: best, bc = v, c
        if bc < 3: out[b] = o[b]; continue
        dom = float(np.median([w for w in vals if abs(w - best) < TOL]))
        out[b] = o[b] if (o[b] is not None and abs(o[b] - dom) < TOL) else dom
    # fill gaps: continuous on both sides -> interpolate
    b = 0
    while b < n:
        if out[b] is None:
            e = b
            while e < n and out[e] is None: e += 1
            if 0 < b and e < n and abs(out[b - 1] - out[e]) < TOL and (e - b) <= 30:
                for k in range(b, e): out[k] = out[b - 1] + (out[e] - out[b - 1]) * (k - b + 1) / (e - b + 1)
            b = e
        else: b += 1
    return out

def runs_of(off):
    """[(b0, b1, None|'cd')] contiguous runs; cd runs have no jump > TOL inside."""
    R = []; b = 0; n = len(off)
    while b < n:
        e = b + 1
        while e < n and (off[e] is None) == (off[b] is None) and (off[b] is None or abs(off[e] - off[e - 1]) < TOL): e += 1
        R.append((b, e)); b = e
    return R

def mono(x): return x.mean(axis=1)

def xcorr_refine(G, C, g0, g1, off, rng=0.008):
    """best extra offset (s) in +-rng aligning game[g0:g1] with cd[g0+off:...]"""
    a = mono(G[g0:g1]); best, bv = 0.0, -2
    for d in range(-int(rng * OUT), int(rng * OUT) + 1, 4):
        s = int(round((g0 / OUT + off) * OUT)) + d
        if s < 0 or s + len(a) > len(C): continue
        c = mono(C[s:s + len(a)]); den = np.linalg.norm(a) * np.linalg.norm(c)
        v = float(a @ c / den) if den > 1e-6 else -2
        if v > bv: bv, best = v, d / OUT
    if best != 0.0:   # fine pass
        base = best
        for d in range(-4, 5):
            s = int(round((g0 / OUT + off + base) * OUT)) + d
            if s < 0 or s + len(a) > len(C): continue
            c = mono(C[s:s + len(a)]); den = np.linalg.norm(a) * np.linalg.norm(c)
            v = float(a @ c / den) if den > 1e-6 else -2
            if v > bv: bv, best = v, base + d / OUT
    return best, bv

def synth(G, C, pos, gcurve, X):
    N = len(G); out = G.copy()
    idx = np.where(~np.isnan(pos))[0]
    p = pos[idx] * OUT; i0 = np.floor(p).astype(np.int64); fr = (p - i0)[:, None]
    ok = (i0 >= 0) & (i0 + 1 < len(C)); i0c = np.clip(i0, 0, len(C) - 2)
    v = (C[i0c] * (1 - fr) + C[i0c + 1] * fr) * gcurve[idx, None]; v[~ok] = 0
    out[idx] = v
    q = np.nan_to_num(pos, nan=-1e9)
    jumps = np.where(np.abs(np.diff(q) - 1.0 / OUT) > 2.0 / OUT)[0] + 1
    for s in jumps:
        if s < X or s + X > N: continue
        if np.isnan(pos[s - 1]): ext = G[s:s + X]
        else:
            pp = (pos[s - 1] + np.arange(1, X + 1) / OUT) * OUT; ii = np.clip(pp.astype(np.int64), 0, len(C) - 1)
            ext = C[ii] * gcurve[s:s + X, None]
        w = np.linspace(0, np.pi / 2, X)[:, None]
        out[s:s + X] = ext * np.cos(w) + out[s:s + X] * np.sin(w)
    return out

def render(name, G):
    m = bm[name]; C = load_cd(int(m['track'])); blocks = m['blocks']; n = len(blocks)
    off = smooth_offsets(blocks)
    N = len(G)
    # per-sample CD position (seconds) or nan (= game audio)
    pos = np.full(N, np.nan)
    centers = []; offs = []
    for b in range(n):
        if off[b] is not None: centers.append(b * 0.1 + 0.05); offs.append(off[b])
    R = runs_of(off)
    seg_off = []   # per run: offset function samples
    for (b0, b1) in R:
        s0, s1 = b0 * BS, min(N, b1 * BS)
        if s0 >= N: break
        if off[b0] is None: continue
        t = np.arange(s0, s1) / OUT
        bc = np.array([b * 0.1 + 0.05 for b in range(b0, b1)]); bo = np.array([off[b] for b in range(b0, b1)])
        pos[s0:s1] = t + np.interp(t, bc, bo)
    # refine splices between consecutive cd runs
    X = int(0.025 * OUT)
    splices = []
    for i in range(1, len(R)):
        (a0, a1), (c0, c1) = R[i - 1], R[i]
        s = c0 * BS
        if s >= N: break
        if off[a0] is None or off[c0] is None: splices.append((s, None, None)); continue
        oA, oB = off[a1 - 1], off[c0]
        w = int(0.8 * OUT)
        dA, _ = xcorr_refine(G, C, max(0, s - w), s, oA)
        dB, _ = xcorr_refine(G, C, s, min(N, s + w), oB)
        oA += dA; oB += dB
        # choose the switch sample in [s-0.3, s+0.3] (10 ms frames)
        lo, hi = max(0, s - int(0.3 * OUT)), min(N, s + int(0.3 * OUT))
        F = 441; fr = range(lo, hi - F, F); eA = []; eB = []
        for f in fr:
            g = mono(G[f:f + F])
            for o, E in ((oA, eA), (oB, eB)):
                k = int(round(f + o * OUT))
                c = mono(C[k:k + F]) if 0 <= k and k + F <= len(C) else np.zeros(F)
                den = np.linalg.norm(g) * np.linalg.norm(c)
                E.append(1 - (g @ c / den) if den > 1e-6 else 0.5)
        eA, eB = np.array(eA), np.array(eB)
        cost = [eA[:j].sum() + eB[j:].sum() for j in range(len(eA) + 1)]
        j = int(np.argmin(cost)); sw = lo + j * F
        t = np.arange(lo, hi) / OUT
        pos[lo:sw] = t[:sw - lo] + oA; pos[sw:hi] = t[sw - lo:] + oB
        splices.append((sw, oA, oB))
    # gain curve (smooth)
    g = np.array([gg if (t is not None and gg > 0) else np.nan for t, gg in blocks], dtype=float)
    med = np.nanmedian(g)
    gl = np.minimum(1.0, np.nan_to_num(g, nan=med) / med)
    k = 10; gs = np.array([np.median(gl[max(0, b - k):b + k + 1]) for b in range(n)]) * med
    gcurve = np.interp(np.arange(N) / OUT, np.arange(n) * 0.1 + 0.05, gs)
    out = synth(G, C, pos, gcurve, X)
    # game-only content (shouts/voices the CD mix lacks at that spot): play the game audio there
    W = 2205; gm, om = mono(G), mono(out); flag = np.zeros(N // W + 1, bool)
    for k in range(0, N - W, W):
        if np.isnan(pos[k:k + W]).all(): continue
        a_, b_ = gm[k:k + W], om[k:k + W]; ea, eb = np.linalg.norm(a_), np.linalg.norm(b_)
        if ea < 1e-3: continue
        c = (a_ @ b_) / (ea * eb) if eb > 1e-6 else 0
        if eb / ea < 0.55 and c < 0.6: flag[k // W] = True
    spans = []; k = 0
    while k < len(flag):
        if flag[k]:
            e = k
            while e < len(flag) and flag[e]: e += 1
            if e - k >= 3: spans.append([max(0, k * W - 3528), min(N, e * W + 3528)])
            k = e
        k += 1
    merged = []
    for sp in spans:
        if merged and sp[0] - merged[-1][1] < int(0.4 * OUT): merged[-1][1] = sp[1]
        else: merged.append(sp)
    spans = merged
    for s0, s1 in spans: pos[s0:s1] = np.nan
    if spans: out = synth(G, C, pos, gcurve, X)
    splices.append(('game_only', [(round(a / OUT, 2), round(b / OUT, 2)) for a, b in spans]))
    return out, off, splices

def score(G, out):
    a, b = mono(G), mono(out); W = 4410; sc = []
    for k in range(0, len(a) - W, W):
        x, y = a[k:k + W], b[k:k + W]; den = np.linalg.norm(x) * np.linalg.norm(y)
        if den > 1e-4: sc.append(float(x @ y / den))
    sc = np.array(sc); return round(float(np.median(sc)), 3), int((sc < 0.5).sum()), len(sc)

if __name__ == '__main__':
    for name in sys.argv[1:] or list(bm):
        G = np.fromfile(f'{HQ}/xafull/{name}.f32', dtype=np.float32).reshape(-1, 2)
        out, off, spl = render(name, G)
        nj = sum(1 for (a, b) in [(off[i - 1], off[i]) for i in range(1, len(off))] if (a is None) != (b is None) or (a is not None and abs(a - b) > TOL))
        tmp = f'{HQ}/_r2.f32'; np.clip(out, -1, 1).astype(np.float32).tofile(tmp)
        dst = f'{HQ}/music_hq2/{name}.flac'; os.makedirs(os.path.dirname(dst), exist_ok=True)
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'f32le', '-ar', str(OUT), '-ac', '2', '-i', tmp,
                        '-sample_fmt', 's16', '-compression_level', '8', dst])
        print(name, 'transitions', nj, 'score', score(G, out), 'game_only', spl[-1][1] if spl and spl[-1][0]=='game_only' else [], flush=True)
