"""Derive the native menu atlas HD replacements from the owner's six-row image.

Run with Windows py -3.13 (Pillow). XXH3 is read from WSL's existing libxxhash;
no package installation, AI upscaling, disc change or source-image overwrite.
"""
from pathlib import Path
import hashlib
import json
import struct
import subprocess
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "assets/ui/ending-view-menu.png"
TIM = ROOT / "assets/archive/system/016/001.tim"
OUT = Path(__file__).resolve().parent / "1.0.0/menu_hd"
SCALE = 8
ART_SCALE = 0.85
# Source row bands; native atlas cells preserve the original five label sizes.
BANDS = (0, 144, 288, 432, 566, 680, 800)
CELLS = ((0, 0, 186), (0, 24, 186), (0, 48, 121), (0, 72, 148),
         (101, 96, 91), (0, 96, 101))
# Visible native alpha bounds: the 24px stride includes transparent padding.
HEIGHTS = (17, 16, 17, 18, 18, 17)


def hashes(blobs):
    code = """import ctypes,json,sys
lib=ctypes.CDLL('libxxhash.so.0')
lib.XXH3_64bits.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
lib.XXH3_64bits.restype=ctypes.c_uint64
print(json.dumps([f'{lib.XXH3_64bits(b,len(b)):016X}' for b in map(bytes.fromhex,json.load(sys.stdin))]))
"""
    result = subprocess.run(["wsl.exe", "-d", "Ubuntu", "--exec", "python3", "-c", code],
                            input=json.dumps([b.hex() for b in blobs]),
                            capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def transparent_row(image):
    """Remove only edge-connected black background; retain enclosed black strokes."""
    image = image.convert("RGBA")
    if image.getchannel("A").getextrema()[0] < 255:
        return image.crop(image.getbbox())
    rgb = image.convert("RGB")
    visible = rgb.convert("L").point(lambda v: 255 if v > 12 else 0)
    box = visible.getbbox()
    if box is None:
        raise ValueError("An input menu row is empty")
    image = image.crop(box)
    solid = ImageOps.expand(visible.crop(box), border=1, fill=0)
    ImageDraw.floodfill(solid, (0, 0), 128)
    alpha = solid.point(lambda v: 0 if v == 128 else 255).crop((1, 1, image.width + 1, image.height + 1))
    image.putalpha(alpha)
    return image


def build():
    source = Image.open(SOURCE)
    if abs(source.width / source.height - 1.6) > 0.025:
        raise ValueError("Expected the supplied six-row artwork, with approximately 1.6 aspect ratio")
    bands = tuple(round(y * source.height / 800) for y in BANDS)
    raw = TIM.read_bytes()
    assert struct.unpack_from("<II", raw) == (16, 8), "Expected the audited 4bpp TIM"
    clut_size, _, _, cw, ch = struct.unpack_from("<IHHHH", raw, 8)
    palettes = [raw[20 + i * 32:20 + (i + 1) * 32] for i in range(cw * ch // 16)]
    q = 8 + clut_size
    _, _, _, tw, th = struct.unpack_from("<IHHHH", raw, q)
    assert (tw * 4, th) == (192, 120)
    tex_hash, *pal_hashes = hashes([raw[q + 12:]] + palettes)
    atlas = Image.new("RGBA", (192 * SCALE, 120 * SCALE))
    preview = Image.new("RGBA", (source.width, 6 * 144), (130, 190, 215, 255))
    for i, (u, v, width) in enumerate(CELLS):
        row = transparent_row(source.crop((0, bands[i], source.width, bands[i + 1])))
        art_width = round(width * SCALE * ART_SCALE)
        art_height = round(HEIGHTS[i] * SCALE * ART_SCALE)
        cell_x = u * SCALE + (width * SCALE - art_width) // 2
        cell_y = v * SCALE + (24 * SCALE - art_height) // 2
        # The ending cell uses unused OPTIONS-row UVs and is drawn as a 150px quad.
        atlas.alpha_composite(row.resize((art_width, art_height), Image.Resampling.LANCZOS),
                              (cell_x, cell_y))
        shown_width = round((150 if i == 4 else width) * 5 * ART_SCALE)
        shown_height = round(HEIGHTS[i] * 5 * ART_SCALE)
        shown = row.resize((shown_width, shown_height), Image.Resampling.LANCZOS)
        preview.alpha_composite(shown, ((source.width - shown_width) // 2,
                                        i * 144 + (120 - shown_height) // 2))
    OUT.mkdir(parents=True, exist_ok=True)
    files = []
    for palette, ph in zip(palettes, pal_hashes):
        colors = struct.unpack("<16H", palette)
        level = max(max(c & 31, c >> 5 & 31, c >> 10 & 31) for c in colors) / 31
        name = f"texupload-P4-{tex_hash}-{ph}-{tw}x{th}-0-0-192x120-P0-15.png"
        r, g, b, a = atlas.split()
        colored = Image.merge("RGBA", (r.point(lambda x: round(x * level)),
                              g.point(lambda x: round(x * level)), b.point(lambda x: round(x * level)), a))
        colored.save(OUT / name)
        files.append(name)
    manifest = {"source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                "source_size": list(source.size), "source_bands": bands,
                "atlas_size": list(atlas.size), "cells": CELLS, "visible_heights": HEIGHTS,
                "art_scale": ART_SCALE, "files": files,
                "source": "Owner-supplied menu artwork; no generated lettering"}
    (OUT / "ready.txt").write_text(json.dumps(manifest, indent=2) + "\n")
    preview_path = ROOT / "_work/endings-view/hd-menu-preview.png"
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    preview.save(preview_path)
    print(json.dumps({"files": len(files), "atlas": list(atlas.size), "preview": str(preview_path),
                      "texture_hash": tex_hash, "palette_hashes": pal_hashes}))


if __name__ == "__main__":
    build()
