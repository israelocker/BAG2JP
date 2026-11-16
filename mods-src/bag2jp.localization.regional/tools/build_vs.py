"""Build the HD layers of the international (US) 2P VS loading screen from the US disc assets.

US BUST2.BIN entries 51..86: per character a P1 entry (red flames, blue flames, VS logo,
P1 portrait, name [, extra]) and a P2 entry (P2 portrait, name [, extra]); char id -> entry from
the US tables at 0x80056990 (P1) / 0x800569b4 (P2). Layout from SLUS FUN_80033324 (screen
512x240): flames at x 0 / 256, portraits at x 0 / 256 (P2 mirrored except chars 9,10,11), names
centred at (112,204) / (400,204) with CLUT row = command difficulty, VS centred at (256,204),
extras (chars 11, 13) additive at (98,44)/(6,0) for P1 and mirrored at (300,44)/(304,0) for P2.
Output: PNG layers scaled to a 2048x1536 (4:3) canvas: sx=4, sy=6.4."""
import struct, os, sys, json
import sys as _sys, pathlib as _pathlib  # configured locations: tools/workflow/configured.py
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[3]))
from tools.workflow import configured as C  # noqa: E402
from PIL import Image
US = C.text('inputs.bag2us_assets')
OUT = sys.argv[1] if len(sys.argv) > 1 else C.text('paths.vs_work') + '/vs_hd'
SX, SY = 4.0, 6.4
P1 = [61, 81, 59, 85, 65, 79, 75, 67, 63, 51, 53, 77, 57, 83, 55, 73, 71, 69]
P2 = [62, 82, 60, 86, 66, 80, 76, 68, 64, 52, 54, 78, 58, 84, 56, 74, 72, 70]
import csv
cat = {int(r['index']): r['path'] for r in csv.DictReader(open(f'{US}/catalog.csv'))}

def tims(entry):
    d = os.path.join(US, cat[entry]); return [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.endswith('.tim')]

def decode(path, row=0):
    """-> RGBA image; alpha 255 opaque, 0 transparent (colour 0x0000); STP stored in a mask list"""
    d = open(path, 'rb').read(); fl = struct.unpack_from('<I', d, 4)[0]; q = 8; mode = fl & 7
    ln, cx, cy, cw, ch = struct.unpack_from('<IHHHH', d, q)
    clut = [struct.unpack_from('<H', d, q + 12 + 2 * i)[0] for i in range(cw * ch)]; q += ln
    ln, x, y, w, h = struct.unpack_from('<IHHHH', d, q); pix = d[q + 12:q + ln]
    W = w * (4 if mode == 0 else 2)
    im = Image.new('RGBA', (W, h)); px = im.load(); stp = Image.new('L', (W, h)); sp = stp.load()
    base = row * cw
    for j in range(h):
        for i in range(W):
            if mode == 0:
                b = pix[j * w * 2 + i // 2]; k = (b >> 4) if i & 1 else (b & 15)
            else:
                k = pix[j * w * 2 + i]
            c = clut[base + k]
            if c == 0: px[i, j] = (0, 0, 0, 0); continue
            px[i, j] = ((c & 31) * 255 // 31, ((c >> 5) & 31) * 255 // 31, ((c >> 10) & 31) * 255 // 31, 255)
            sp[i, j] = 255 if c & 0x8000 else 0
    return im, stp

def hd(im):
    w, h = im.size
    # premultiply to avoid dark fringes, resize, un-premultiply
    r, g, b, a = im.split()
    from PIL import ImageChops
    pm = Image.merge('RGB', [ImageChops.multiply(c, a) for c in (r, g, b)])
    W, H = round(w * SX), round(h * SY)
    pm = pm.resize((W, H), Image.LANCZOS); a2 = a.resize((W, H), Image.LANCZOS)
    out = Image.new('RGBA', (W, H)); op = out.load(); pp = pm.load(); ap = a2.load()
    for j in range(H):
        for i in range(W):
            al = ap[i, j]
            if al == 0: op[i, j] = (0, 0, 0, 0); continue
            p = pp[i, j]; op[i, j] = (min(255, p[0] * 255 // al), min(255, p[1] * 255 // al), min(255, p[2] * 255 // al), al)
    return out

os.makedirs(OUT, exist_ok=True)
meta = {'canvas': [2048, 1536], 'sx': SX, 'sy': SY, 'chars': {}}
t = tims(P1[0])
for name, k in (('flames_red', 0), ('flames_blue', 1), ('vs', 2)):
    im, _ = decode(t[k]); hd(im).save(f'{OUT}/{name}.png'); meta[name] = list(im.size)
for c in range(18):
    a, b = tims(P1[c]), tims(P2[c]); m = {}
    im, _ = decode(a[3]); hd(im).save(f'{OUT}/c{c:02d}_p1.png'); m['p1'] = list(im.size)
    im, _ = decode(b[0])
    if c not in (9, 10, 11): im = im.transpose(Image.FLIP_LEFT_RIGHT)
    hd(im).save(f'{OUT}/c{c:02d}_p2.png'); m['p2'] = list(im.size)
    for r in range(3):
        im, _ = decode(a[4], r); hd(im).save(f'{OUT}/c{c:02d}_name{r}.png')
    m['name'] = list(im.size)
    if len(a) > 5:
        im, stp = decode(a[5]); hd(im).save(f'{OUT}/c{c:02d}_p1x.png'); m['p1x'] = list(im.size)
        im2, _ = decode(b[2]); hd(im2.transpose(Image.FLIP_LEFT_RIGHT)).save(f'{OUT}/c{c:02d}_p2x.png'); m['p2x'] = list(im2.size)
        m['stp_frac'] = sum(1 for v in stp.getdata() if v) / max(1, sum(1 for v in im.getchannel('A').getdata() if v))
    meta['chars'][c] = m
json.dump(meta, open(f'{OUT}/layout.json', 'w'), indent=1)
print(json.dumps(meta)[:800])
