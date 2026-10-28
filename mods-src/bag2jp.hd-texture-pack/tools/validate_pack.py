"""Compare every replacement in out/ against its source TIM (downscaled, opaque pixels only).
Prints the worst ones and writes bad.txt (mean abs RGB error above the threshold)."""
import os, sys, json
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_ui_pack as G
jobs = json.load(open(os.path.join(G.HOME, 'work/uipack/jobs.json')))
TH = float(sys.argv[1]) if len(sys.argv) > 1 else 24
res = []
for n, j in jobs.items():
    p = os.path.join(G.OUT, n)
    if not os.path.exists(p): res.append((999, n)); continue
    t = G.read_tim(j['src']); idx, rgb, transp = G.colour8(t, G.pal_list(j['pal']))
    h, w = rgb.shape[:2]
    im = np.array(Image.open(p).convert('RGBA')).astype(np.float32)
    H, W = im.shape[:2]
    if H % h or W % w: res.append((998, n)); continue
    k = H // h
    small = im.reshape(h, k, w, k, 4).mean((1, 3))
    op = ~transp
    if op.sum() == 0: res.append((0, n)); continue
    err = np.abs(small[..., :3] - rgb.astype(np.float32))[op].mean()
    aerr = np.abs(small[..., 3] / 255 - op).mean()
    res.append((float(err + 100 * aerr), n))
res.sort(reverse=True)
bad = [n for e, n in res if e > TH]
open(os.path.join(G.HOME, 'work/uipack/bad.txt'), 'w').write('\n'.join(bad))
for e, n in res[:25]: print(f'{e:7.1f} {n} {os.path.relpath(jobs[n]["src"], G.HOME)}')
print('bad', len(bad), 'of', len(res))
