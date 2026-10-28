"""HD replacements for every UI (archive/system) TIM, JP disc and the US files used by the
regional overlays. DuckStation texupload names: source hash = XXH3 of the TIM image words,
palette hash = XXH3 of the CLUT row words (16 for P4, 256 for P8).
- 4bpp: palette-index 'label' upscale (font_hd.label_upscale), coloured per palette row.
- 8bpp: Real-ESRGAN (anime model) on the coloured image (run on Windows, step 2), alpha from
  the label upscale of the transparent mask.
Palettes: the TIM's own rows plus the rows of palette-only TIMs in the same folder (HUD sheets
drawn with external palettes). system/000/000.tim (font atlas) is handled by font_hd.py.
usage: gen_ui_pack.py plan|build4|prep8|finish8"""
import os, sys, struct, json, hashlib
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.expanduser('~/work/vs'))
import font_hd as F
import xxhash
HOME = os.path.expanduser('~')
SRC = [f'{HOME}/work/jpbase/archive/system', f'{HOME}/work/bag2us/assets/archive/system']
OUT = f'{HOME}/work/uipack/out'
ESR = f'{HOME}/mnt/Dev/Recomp/BAG2JP/_work/uipack'
S = 4

def read_tim(p):
    d = open(p, 'rb').read()
    if len(d) < 20 or d[:4] != b'\x10\0\0\0': return None
    fl = struct.unpack_from('<I', d, 4)[0]; q = 8; clut = None
    if fl & 8:
        ln, x, y, w, h = struct.unpack_from('<IHHHH', d, q); clut = (w, h, d[q + 12:q + 12 + w * h * 2]); q += ln
    ln, x, y, w, h = struct.unpack_from('<IHHHH', d, q)
    return {'mode': fl & 7, 'clut': clut, 'w': w, 'h': h, 'pix': d[q + 12:q + 12 + w * h * 2]}

def rows_of(clut, n):
    w, h, raw = clut; out = []
    for r in range(h):
        for off in range(0, w, n):
            if off + n <= w: out.append(raw[(r * w + off) * 2:(r * w + off + n) * 2])
    return out

def plan():
    jobs = {}
    for root in SRC:
        for dp, _, fs in os.walk(root):
            tims = {f: read_tim(os.path.join(dp, f)) for f in sorted(fs) if f.endswith('.tim')}
            tims = {f: t for f, t in tims.items() if t}
            ext4 = [r for t in tims.values() if t['clut'] and (t['w'] == 0 or t['h'] == 0) for r in rows_of(t['clut'], 16)]
            for f, t in tims.items():
                if t['w'] == 0 or t['h'] == 0 or t['mode'] not in (0, 1): continue
                rel = os.path.relpath(os.path.join(dp, f), root)
                if rel.replace('\\', '/') == '000/000.tim': continue
                n = 16 if t['mode'] == 0 else 256
                pals = (rows_of(t['clut'], n) if t['clut'] else []) + (ext4 if n == 16 else [])
                tex = xxhash.xxh3_64(t['pix']).hexdigest().upper()
                W = t['w'] * (4 if t['mode'] == 0 else 2)
                for pal in pals:
                    if len(pal) != n * 2 or not any(pal): continue
                    ph = xxhash.xxh3_64(pal).hexdigest().upper()
                    name = f"texupload-P{4 if n == 16 else 8}-{tex}-{ph}-{t['w']}x{t['h']}-0-0-{W}x{t['h']}-P0-{n - 1}.png"
                    if name in jobs: continue
                    jobs[name] = {'src': os.path.join(dp, f), 'mode': t['mode'], 'pal': pal.hex()}
    json.dump(jobs, open(f'{HOME}/work/uipack/jobs.json', 'w'))
    from collections import Counter
    print(len(jobs), Counter(j['mode'] for j in jobs.values()), len({j['src'] for j in jobs.values()}), 'images')

def indices(t):
    pix = np.frombuffer(t['pix'], np.uint8).reshape(t['h'], t['w'] * 2)
    if t['mode'] == 1: return pix.copy()
    idx = np.zeros((t['h'], t['w'] * 4), np.uint8); idx[:, 0::2] = pix & 15; idx[:, 1::2] = pix >> 4
    return idx

def pal_list(hexs):
    raw = bytes.fromhex(hexs); return [struct.unpack_from('<H', raw, 2 * i)[0] for i in range(len(raw) // 2)]

def build4():
    jobs = json.load(open(f'{HOME}/work/uipack/jobs.json')); os.makedirs(OUT, exist_ok=True)
    by_src = {}
    for n, j in jobs.items():
        if j['mode'] == 0: by_src.setdefault(j['src'], []).append(n)
    done = 0
    for src, names in by_src.items():
        todo = [n for n in names if not os.path.exists(os.path.join(OUT, n))]
        if not todo: continue
        lab, ss = F.label_upscale(indices(read_tim(src)), S, blur=0.2)
        for n in todo:
            F.colorize(lab, pal_list(jobs[n]['pal']), ss).save(os.path.join(OUT, n), optimize=True); done += 1
    print('4bpp written', done)

def colour8(t, pal):
    idx = indices(t); P = np.array([[(c & 31) * 255 // 31, ((c >> 5) & 31) * 255 // 31, ((c >> 10) & 31) * 255 // 31] for c in pal], np.uint8)
    return idx, P[idx], np.array([c == 0 for c in pal])[idx]

def prep8(all_modes=False):
    jobs = json.load(open(f'{HOME}/work/uipack/jobs.json'))
    os.makedirs(f'{ESR}/in', exist_ok=True); os.makedirs(f'{ESR}/out', exist_ok=True)
    m = {}
    for n, j in jobs.items():
        if j['mode'] != 1 and not all_modes: continue
        _, rgb, transp = colour8(read_tim(j['src']), pal_list(j['pal']))
        key = hashlib.sha1(n.encode()).hexdigest()[:16] + '.png'
        Image.fromarray(rgb, 'RGB').save(f'{ESR}/in/{key}'); m[key] = n
    json.dump(m, open(f'{ESR}/map.json', 'w')); print('8bpp prepared', len(m))

_mask_cache = {}
ESR_MAX_ERR = 30.0
def esr_error(up, rgb, transp):
    """Mean abs RGB error of the box-downscaled upscale against the source on opaque pixels.
    A GPU run that died (VK_ERROR_DEVICE_LOST) leaves black, inverted or striped garbage."""
    h, w = rgb.shape[:2]; H, W = up.shape[:2]
    if H % h or W % w or H // h != W // w: return 1e9
    k = H // h; small = up.astype(np.float32).reshape(h, k, w, k, 3).mean((1, 3)); op = ~transp
    return float(np.abs(small - rgb)[op].mean()) if op.any() else 0.0
def finish8():
    jobs = json.load(open(f'{HOME}/work/uipack/jobs.json')); m = json.load(open(f'{ESR}/map.json')); n_ok = 0
    for key, n in m.items():
        p = f'{ESR}/out/{key}'
        if not os.path.exists(p) or os.path.exists(os.path.join(OUT, n)) and os.path.getmtime(os.path.join(OUT, n)) > os.path.getmtime(p): continue
        j = jobs[n]; t = read_tim(j['src'])
        _, rgb, transp = colour8(t, pal_list(j['pal']))
        up = Image.open(p).convert('RGB'); W, H = up.size
        mask = transp.astype(np.uint8)
        ck = (j['src'], mask.tobytes())
        if ck not in _mask_cache: _mask_cache[ck] = F.label_upscale(mask, W // mask.shape[1], blur=0.2)
        lab, ss = _mask_cache[ck]
        a = (lab.reshape(H, ss, W, ss).mean((1, 3)) < 0.5) if ss > 1 else (lab == 0)
        rgba = np.dstack([np.array(up), (a * 255).astype(np.uint8)])
        Image.fromarray(rgba, 'RGBA').save(os.path.join(OUT, n), optimize=True); n_ok += 1
    print('8bpp finished', n_ok)


def finishall():
    """Write every job: Real-ESRGAN result (out_retry first, then out) unless it is missing or
    black (failed GPU run), else the palette-index label upscale."""
    jobs = json.load(open(f'{HOME}/work/uipack/jobs.json')); m = json.load(open(f'{ESR}/map.json'))
    inv = {v: k for k, v in m.items()}; os.makedirs(OUT, exist_ok=True)
    stats = {'esrgan': 0, 'label': 0}; lab_cache = {}
    names = sorted(jobs); a0, a1 = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (0, len(names))
    for n in names[a0:a1]:
        j = jobs[n]
        t = read_tim(j['src']); pal = pal_list(j['pal'])
        idx, rgb, transp = colour8(t, pal)
        up = None
        for d in ('out_retry2', 'out_retry', 'out'):
            p = f"{ESR}/{d}/{inv.get(n, '')}"
            if inv.get(n) and os.path.exists(p):
                a = np.array(Image.open(p).convert('RGB'))
                if esr_error(a, rgb, transp) <= ESR_MAX_ERR: up = a; break
        if up is None:
            if inv.get(n) and os.path.exists(f'{ESR}/in/{inv[n]}'):
                os.makedirs(f'{ESR}/in_retry2', exist_ok=True)
                Image.open(f'{ESR}/in/{inv[n]}').save(f'{ESR}/in_retry2/{inv[n]}'); stats.setdefault('queued', 0); stats['queued'] += 1
            if j['src'] not in lab_cache: lab_cache[j['src']] = F.label_upscale(idx, S, blur=0.2)
            lab, ss = lab_cache[j['src']]
            F.colorize(lab, pal, ss).save(os.path.join(OUT, n), optimize=True); stats['label'] += 1; continue
        H, W = up.shape[:2]
        mask = transp.astype(np.uint8); ck = (j['src'], mask.tobytes())
        if ck not in _mask_cache: _mask_cache[ck] = F.label_upscale(mask, W // mask.shape[1], blur=0.2)
        lab, ss = _mask_cache[ck]
        a = (lab.reshape(H, ss, W, ss).mean((1, 3)) < 0.5) if ss > 1 else (lab == 0)
        Image.fromarray(np.dstack([up, (a * 255).astype(np.uint8)]), 'RGBA').save(os.path.join(OUT, n), optimize=True)
        stats['esrgan'] += 1
    print(stats)

if __name__ == '__main__':
    {'plan': plan, 'build4': build4, 'prep8': prep8, 'prepall': lambda: prep8(True), 'finish8': finish8,
     'finishall': finishall}[sys.argv[1]]()
