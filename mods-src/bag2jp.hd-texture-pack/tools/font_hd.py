"""HD versions of the system font atlas (system/000/000.tim, 4bpp 256x240) for the HD texture pack.
Method 'label': each palette index is a layer; layers are upscaled as smooth fields (bicubic of the
binary mask after a light blur) and every HD pixel takes the index with the strongest field, computed
at 2x the target and box-downsampled for anti-aliased edges; then the palette row is applied.
Index 0 = transparent (alpha 0)."""
import numpy as np, struct, sys, os
from PIL import Image
from scipy import ndimage
TIM = os.path.expanduser('~/work/jpbase/archive/system/000/000.tim')
def load_indices():
    d = open(TIM, 'rb').read(); ln = struct.unpack_from('<I', d, 8)[0]; q = 8 + ln
    _, x, y, w, h = struct.unpack_from('<IHHHH', d, q); pix = np.frombuffer(d[q + 12:q + 12 + w * 2 * h], np.uint8).reshape(h, w * 2)
    idx = np.zeros((h, w * 4), np.uint8); idx[:, 0::2] = pix & 15; idx[:, 1::2] = pix >> 4
    return idx
def clut_rows(path):
    d = open(path, 'rb').read(); ln, x, y, w, h = struct.unpack_from('<IHHHH', d, 8)
    return [[struct.unpack_from('<H', d, 20 + 2 * (r * w + i))[0] for i in range(16)] for r in range(h)], d
def label_upscale(idx, S, blur=0.6, ss=2):
    T = S * ss; H, W = idx.shape; best = np.full((H * T, W * T), -1e9, np.float32); lab = np.zeros((H * T, W * T), np.uint8)
    for k in np.unique(idx):
        m = (idx == k).astype(np.float32)
        if blur: m = ndimage.gaussian_filter(m, blur)
        f = ndimage.zoom(m, T, order=3, mode='nearest')
        sel = f > best; best[sel] = f[sel]; lab[sel] = k
    return lab, T // S if ss > 1 else 1
def colorize(lab, row, ss):
    pal = np.array([[(c & 31) * 255 // 31, ((c >> 5) & 31) * 255 // 31, ((c >> 10) & 31) * 255 // 31, 0 if c == 0 else 255] for c in row], np.float32)
    rgba = pal[lab]                                   # (H*T, W*T, 4)
    if ss > 1:
        h, w = lab.shape[0] // ss, lab.shape[1] // ss
        a = rgba[..., 3:4] / 255.0
        prem = (rgba[..., :3] * a).reshape(h, ss, w, ss, 3).mean((1, 3)); al = a.reshape(h, ss, w, ss, 1).mean((1, 3))
        rgb = np.where(al > 0, prem / np.maximum(al, 1e-6), 0)
        alpha = np.where(al >= 0.5, 255, 0)          # cutout alpha (pack rule: <128 transparent)
        rgba = np.concatenate([rgb, alpha], -1)
    return Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), 'RGBA')
if __name__ == '__main__':
    S = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    idx = load_indices()
    crop = idx[128:158, 64:236]
    rows, _ = clut_rows(os.path.expanduser('~/work/jpbase/archive/system/000/001.tim'))
    lab, ss = label_upscale(crop, S)
    out = os.path.expanduser('~/mnt/Dev/Recomp/BAG2JP/_work/font_test')
    colorize(lab, rows[6], ss).save(f'{out}/label_block_x{S}.png')
    pal = rows[6]
    near = Image.fromarray(crop).resize((crop.shape[1] * S, crop.shape[0] * S), Image.NEAREST)
    colorize(np.array(near), pal, 1).save(f'{out}/nearest_block_x{S}.png')
    print('ok')

def build_pack(out_dir, S=6, blur=0.2):
    """32 replacements (palettes: 000.tim rows 0-15, 001.tim rows 0-15) for the whole atlas upload."""
    import xxhash
    os.makedirs(out_dir, exist_ok=True)
    idx = load_indices()
    d = open(TIM, 'rb').read(); ln = struct.unpack_from('<I', d, 8)[0]; q = 8 + ln
    _, x, y, w, h = struct.unpack_from('<IHHHH', d, q)
    tex = xxhash.xxh3_64(d[q + 12:q + 12 + w * 2 * h]).hexdigest().upper()
    lab, ss = label_upscale(idx, S, blur=blur)
    n = 0
    for f in ('000.tim', '001.tim'):
        rows, raw = clut_rows(os.path.expanduser(f'~/work/jpbase/archive/system/000/{f}'))
        for r, row in enumerate(rows):
            ph = xxhash.xxh3_64(raw[20 + r * 32:20 + r * 32 + 32]).hexdigest().upper()
            name = f'texupload-P4-{tex}-{ph}-{w}x{h}-0-0-{w * 4}x{h}-P0-15.png'
            colorize(lab, row, ss).save(os.path.join(out_dir, name), optimize=True); n += 1
    return n
