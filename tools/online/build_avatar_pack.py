#!/usr/bin/env python3
"""Export official BAG2 character select HD portraits as 128x160 raw RGBA files
for the in-game Online Lobby & 1v1 Waiting Room profile system."""

from pathlib import Path
from PIL import Image

SRC_DIR = Path(
    r"D:\Games\Bust A Groove 2 (Japan)\BAG2JP-exp-8mb\mods\texture-packs"
    r"\SLPM-86219\replacements\bag2jp_charsel_hd"
)
OUT_DIR = Path(r"D:\Games\Bust A Groove 2 (Japan)\BAG2JP-exp-8mb\online_avatars")

# Ordered to match s_avatars[] in bag2jp_lobby_ui.c (0..11)
AVATAR_MAP = [
    (0,  "HEAT",     "0941951802FA55FB", (217, 41, 36)),
    (1,  "HIRO",     "CB7FE61E466A7EE6", (46, 92, 217)),
    (2,  "KITTY-N",  "03C66E58A0B1BAB5", (235, 71, 158)),
    (3,  "KELLY",    "DA06BA3D4DBE89E3", (41, 158, 224)),
    (4,  "STRIKE",   "181D40C9687A4C1E", (56, 133, 71)),
    (5,  "TSUTOMU",  "74FDA3D0DDC28020", (224, 115, 31)),
    (6,  "SHORTY",   "FC67081A4D19F628", (242, 133, 184)),
    (7,  "GAS-O",    "D1F36DAEBACA74C2", (97, 173, 56)),
    (8,  "COMET",    "0DF543E9547BF883", (115, 82, 219)),
    (9,  "CAPOEIRA", "089E386E02E4B918", (36, 184, 133)),
    (10, "ROBO-Z",   "8A0B27F4B1C931F5", (199, 163, 41)),
    (11, "PANDER",   "425FEE1FED7C43E2", (56, 56, 66)),
]

W, H = 128, 160


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for idx, name, prefix, bg_rgb in AVATAR_MAP:
        matches = sorted(SRC_DIR.glob(f"texupload-P8-{prefix}-*-P0-255.png"))
        if not matches:
            raise FileNotFoundError(f"Missing portrait for {name} ({prefix})")
        im = Image.open(matches[0]).convert("RGBA")
        # Crop top 75% (upper body/face) and resize to 128x160
        cw, ch = im.size
        im = im.crop((0, 0, cw, int(ch * 0.78))).resize((W, H), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (W, H), (*bg_rgb, 255))
        canvas.alpha_composite(im)
        # Flip vertically for OpenGL bottom-up origin
        canvas = canvas.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        out_path = OUT_DIR / f"avatar_{idx}.rgba"
        out_path.write_bytes(canvas.tobytes())
        print(f"Exported {idx:2d} {name:<10s} -> {out_path.name} ({W}x{H})")


if __name__ == "__main__":
    main()
