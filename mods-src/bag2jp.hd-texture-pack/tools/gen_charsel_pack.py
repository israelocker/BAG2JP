#!/usr/bin/env python3
"""Generate DuckStation HD replacement textures for BAG2JP character select (`015.bpe`).

Builds:
  - 18 stock character select portraits (`011.tim`..`028.tim`, 152x240 -> 1216x1920, 8x)
  - 1 Gas-O character select portrait (`020.tim` pixels + CLUT word[255]=1, 152x240 -> 1216x1920, 8x)
  - 9 character select name font sheets (`041.tim`, `042.tim` with Gas-O at u=0,v=226,w=115,h=29,
    and `043.tim` cropped to 192x201 -> 1536x1608, across all 3 CLUT rows: 1P, 2P, CPU)
"""
from __future__ import annotations

import shutil
import sys as _sys, pathlib as _pathlib  # configured locations: tools/workflow/configured.py
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[3]))
from tools.workflow import configured as C  # noqa: E402
import struct
from pathlib import Path

import numpy as np
from PIL import Image

M64 = 0xFFFFFFFFFFFFFFFF
P64_1 = 0x9E3779B185EBCA87
P64_2 = 0xC2B2AE3D27D4EB4F
P64_3 = 0x165667B19E3779F9
P64_4 = 0x85EBCA77C2B2AE63
P64_5 = 0x27D4EB2F165667C5
P32_1 = 0x9E3779B1
P32_2 = 0x85EBCA77
P32_3 = 0xC2B2AE3D
SECRET = bytes(
    [
        0xB8, 0xFE, 0x6C, 0x39, 0x23, 0xA4, 0x4B, 0xBE, 0x7C, 0x01, 0x81, 0x2C, 0xF7, 0x21, 0xAD, 0x1C,
        0xDE, 0xD4, 0x6D, 0xE9, 0x83, 0x90, 0x97, 0xDB, 0x72, 0x40, 0xA4, 0xA4, 0xB7, 0xB3, 0x67, 0x1F,
        0xCB, 0x79, 0xE6, 0x4E, 0xCC, 0xC0, 0xE5, 0x78, 0x82, 0x5A, 0xD0, 0x7D, 0xCC, 0xFF, 0x72, 0x21,
        0xB8, 0x08, 0x46, 0x74, 0xF7, 0x43, 0x24, 0x8E, 0xE0, 0x35, 0x90, 0xE6, 0x81, 0x3A, 0x26, 0x4C,
        0x3C, 0x28, 0x52, 0xBB, 0x91, 0xC3, 0x00, 0xCB, 0x88, 0xD0, 0x65, 0x8B, 0x1B, 0x53, 0x2E, 0xA3,
        0x71, 0x64, 0x48, 0x97, 0xA2, 0x0D, 0xF9, 0x4E, 0x38, 0x19, 0xEF, 0x46, 0xA9, 0xDE, 0xAC, 0xD8,
        0xA8, 0xFA, 0x76, 0x3F, 0xE3, 0x9C, 0x34, 0x3F, 0xF9, 0xDC, 0xBB, 0xC7, 0xC7, 0x0B, 0x4F, 0x1D,
        0x8A, 0x51, 0xE0, 0x4B, 0xCD, 0xB4, 0x59, 0x31, 0xC8, 0x9F, 0x7E, 0xC9, 0xD9, 0x78, 0x73, 0x64,
        0xEA, 0xC5, 0xAC, 0x83, 0x34, 0xD3, 0xEB, 0xC3, 0xC5, 0x81, 0xA0, 0xFF, 0xFA, 0x13, 0x63, 0xEB,
        0x17, 0x0D, 0xDD, 0x51, 0xB7, 0xF0, 0xDA, 0x49, 0xD3, 0x16, 0x55, 0x26, 0x29, 0xD4, 0x68, 0x9E,
        0x2B, 0x16, 0xBE, 0x58, 0x7D, 0x47, 0xA1, 0xFC, 0x8F, 0xF8, 0xB8, 0xD1, 0x7A, 0xD0, 0x31, 0xCE,
        0x45, 0xCB, 0x3A, 0x8F, 0x95, 0x16, 0x04, 0x28, 0xAF, 0xD7, 0xFB, 0xCA, 0xBB, 0x4B, 0x40, 0x7E,
    ]
)


def _r64(b: bytes, o: int) -> int:
    return struct.unpack_from("<Q", b, o)[0]


def _avalanche(h: int) -> int:
    h = ((h ^ (h >> 37)) * 0x165667919E3779F9) & M64
    return h ^ (h >> 32)


def _mix16(b: bytes, o: int, so: int) -> int:
    a = _r64(b, o) ^ _r64(SECRET, so)
    c = _r64(b, o + 8) ^ _r64(SECRET, so + 8)
    p = a * c
    return ((p & M64) ^ (p >> 64)) & M64


def _xxh3_small(data: bytes) -> int:
    n = len(data)
    assert 17 <= n <= 240
    acc = (n * P64_1) & M64
    if n <= 128:
        i = 0
        j = n - 16
        k = 0
        while i < j:
            acc = (acc + _mix16(data, i, k) + _mix16(data, j, k + 16)) & M64
            i += 16
            j -= 16
            k += 32
        if i == j:
            acc = (acc + _mix16(data, i, k)) & M64
        return _avalanche(acc)
    for i in range(0, 128, 16):
        acc = (acc + _mix16(data, i, i)) & M64
    acc = _avalanche(acc)
    for i in range(128, (n // 16) * 16, 16):
        acc = (acc + _mix16(data, i, i - 128 + 3)) & M64
    acc = (acc + _mix16(data, n - 16, 136 - 17)) & M64
    return _avalanche(acc)


def _mix_acc(acc: list[int], sec_off: int, start: int) -> int:
    s = start
    for i in range(4):
        d0, d1 = acc[2 * i], acc[2 * i + 1]
        k0, k1 = _r64(SECRET, sec_off + 16 * i), _r64(SECRET, sec_off + 16 * i + 8)
        lo = ((d0 ^ k0) * (d1 ^ k1)) & M64
        hi = (((d0 ^ k0) * (d1 ^ k1)) >> 64) & M64
        s = (s + (lo ^ hi)) & M64
    return _avalanche(s)


def xxh3_64(data: bytes) -> int:
    n = len(data)
    if n <= 240:
        return _xxh3_small(data)
    acc = [P32_3, P64_1, P64_2, P64_3, P64_4, P32_2, P64_5, P32_1]

    def acc_stripe(stripe_off: int, sec_off: int) -> None:
        for i in range(8):
            d = _r64(data, stripe_off + 8 * i)
            dv = d ^ _r64(SECRET, sec_off + 8 * i)
            acc[i ^ 1] = (acc[i ^ 1] + d) & M64
            acc[i] = (acc[i] + (dv & 0xFFFFFFFF) * (dv >> 32)) & M64

    def scramble() -> None:
        for i in range(8):
            k = _r64(SECRET, 192 - 64 + 8 * i)
            x = acc[i] ^ (acc[i] >> 47) ^ k
            acc[i] = (x * P32_1) & M64

    nb_blocks = (n - 1) // 1024
    for b in range(nb_blocks):
        for s in range(16):
            acc_stripe(b * 1024 + s * 64, s * 8)
        scramble()
    nb_stripes = ((n - 1) - 1024 * nb_blocks) // 64
    for s in range(nb_stripes):
        acc_stripe(nb_blocks * 1024 + s * 64, s * 8)
    acc_stripe(n - 64, 192 - 64 - 7)
    return _mix_acc(acc, 11, (n * P64_1) & M64)

ROOT = Path(__file__).resolve().parents[3]
TIM_DIR = C.path("inputs.bag2jp_assets") / "archive/system/015.bpe/content"
HD_ART_DIR = C.path("paths.work_root") / "gaso/hd_art"
OUT_MOD_SRC = ROOT / "mods-src/bag2jp.hd-texture-pack/SLPM-86219/replacements/bag2jp_charsel_hd"
OUT_EXP = C.path("paths.experimental_install") / "mods/texture-packs/SLPM-86219/replacements/bag2jp_charsel_hd"

PORTRAIT_MAP = {
    11: "portrait_heat.png",
    12: "portrait_comet.png",
    13: "portrait_tsutomu.png",
    14: "portrait_kelly.png",
    15: "portrait_shorty.png",
    16: "portrait_pander.png",
    17: "portrait_kitty_n.png",
    18: "portrait_hiro.png",
    19: "portrait_capoeira.png",
    20: "portrait_bi_o.png",
    21: "portrait_robo_z_gold.png",
    22: "portrait_michael.png",
    23: "portrait_chichi_sally.png",
    24: "portrait_burger_dog.png",
    25: "portrait_hustle_kong.png",
    26: "portrait_sushi_boy.png",
    27: "portrait_mc_load.png",
    28: "portrait_columbo.png",
}


def recolor_name_sheet(im_row0: Image.Image, row: int) -> Image.Image:
    """Map row 0 (1P orange-yellow) to row 1 (2P blue-cyan) or row 2 (CPU green)."""
    if row == 0:
        return im_row0
    arr = np.array(im_row0, dtype=np.float32)
    alpha = arr[:, :, 3]
    mask = alpha > 0
    # In row 0, green channel increases monotonically from 64 (outline) to 246 (highlight).
    t = np.clip((arr[:, :, 1] - 64.0) / (246.0 - 64.0), 0.0, 1.0)
    if row == 1:
        c0 = np.array([32.0, 48.0, 176.0], dtype=np.float32)
        c1 = np.array([64.0, 240.0, 200.0], dtype=np.float32)
    else:
        c0 = np.array([0.0, 88.0, 24.0], dtype=np.float32)
        c1 = np.array([24.0, 248.0, 24.0], dtype=np.float32)
    rgb = c0[None, None, :] + t[:, :, None] * (c1 - c0)[None, None, :]
    out = np.zeros_like(arr, dtype=np.uint8)
    out[:, :, :3] = np.where(mask[:, :, None], np.clip(np.round(rgb), 0, 255).astype(np.uint8), 0)
    out[:, :, 3] = arr[:, :, 3].astype(np.uint8)
    return Image.fromarray(out, mode="RGBA")


def main() -> None:
    OUT_MOD_SRC.mkdir(parents=True, exist_ok=True)
    for old in OUT_MOD_SRC.glob("*.png"):
        old.unlink()

    # 1. Generate 18 stock portraits + 1 Gas-O portrait.
    # Note: Recomp / DuckStation evaluates CLUT hashes only over the referenced palette range (P0-{max_pix}).
    # For 011.tim-028.tim, max(pix) is 235 (236 palette entries -> 472 bytes).
    # We output both exact runtime format (P0-{max_pix}) and full format (P0-255).
    for idx in range(11, 29):
        tim = (TIM_DIR / f"{idx:03d}.tim").read_bytes()
        ln, cx, cy, cw, ch = struct.unpack_from("<IHHHH", tim, 8)
        clut = bytearray(tim[20 : 8 + ln])
        ln2, ix, iy, iw, ih = struct.unpack_from("<IHHHH", tim, 8 + ln)
        pix = tim[8 + ln + 12 : 8 + ln + ln2]
        ph = xxh3_64(pix)
        max_pix = max(pix) if len(pix) > 0 else 255
        used_len = (max_pix + 1) * 2

        ch_used = xxh3_64(bytes(clut[:used_len]))
        ch_full = xxh3_64(bytes(clut[: 256 * 2]))

        src_png = HD_ART_DIR / "duckstation_portraits" / f"{idx:03d}.png"
        dst_235 = f"texupload-P8-{ph:016X}-{ch_used:016X}-{iw}x{ih}-0-0-{iw*2}x{ih}-P0-{max_pix}.png"
        dst_255 = f"texupload-P8-{ph:016X}-{ch_full:016X}-{iw}x{ih}-0-0-{iw*2}x{ih}-P0-255.png"

        shutil.copy2(src_png, OUT_MOD_SRC / dst_235)
        if dst_235 != dst_255:
            shutil.copy2(src_png, OUT_MOD_SRC / dst_255)

        if idx == 20:
            clut_gaso_used = bytearray(clut[:used_len])
            w_toggle = struct.unpack_from("<H", clut_gaso_used, max_pix * 2)[0]
            struct.pack_into("<H", clut_gaso_used, max_pix * 2, w_toggle ^ 1)
            ch_gaso_used = xxh3_64(bytes(clut_gaso_used))

            clut_gaso_full = bytearray(clut[: 256 * 2])
            w255 = struct.unpack_from("<H", clut_gaso_full, 255 * 2)[0]
            struct.pack_into("<H", clut_gaso_full, 255 * 2, w255 ^ 1)
            ch_gaso_full = xxh3_64(bytes(clut_gaso_full))

            gaso_png = HD_ART_DIR / "duckstation_portraits/029_Gas_O.png"
            gaso_name_235 = f"texupload-P8-{ph:016X}-{ch_gaso_used:016X}-{iw}x{ih}-0-0-{iw*2}x{ih}-P0-{max_pix}.png"
            gaso_name_255 = f"texupload-P8-{ph:016X}-{ch_gaso_full:016X}-{iw}x{ih}-0-0-{iw*2}x{ih}-P0-255.png"

            shutil.copy2(gaso_png, OUT_MOD_SRC / gaso_name_235)
            if gaso_name_235 != gaso_name_255:
                shutil.copy2(gaso_png, OUT_MOD_SRC / gaso_name_255)
            print(f"Bi-O runtime hash: {ch_used:016X}, Gas-O runtime hash: {ch_gaso_used:016X} (P0-{max_pix})")

    # 2. Generate 3 character name sheets x 3 CLUT rows = 9 PNGs.
    gaso_font = Image.open(HD_ART_DIR / "name_fonts/name_gaso.png").convert("RGBA")
    # Crop GAS-O from (344, 32, 1264, 264) -> 920x232 (115x29 at 8x).
    gaso_crop = gaso_font.crop((344, 32, 1264, 264))

    sheet_sources = {
        41: Image.open(HD_ART_DIR / "name_fonts/name_font_sheet_a.png").convert("RGBA"),
        42: Image.open(HD_ART_DIR / "name_fonts/name_font_sheet_c.png").convert("RGBA"),
        43: Image.open(HD_ART_DIR / "name_fonts/name_font_sheet_b.png").convert("RGBA").crop((0, 0, 1536, 1608)),
    }
    # Place GAS-O at u=0, v=226 (x=0, y=1808 at 8x) on sheet 42 (042.tim).
    sheet_sources[42].paste(gaso_crop, (0, 226 * 8))

    for idx in (41, 42, 43):
        tim = (TIM_DIR / f"{idx:03d}.tim").read_bytes()
        ln, cx, cy, cw, ch = struct.unpack_from("<IHHHH", tim, 8)
        clut = tim[20 : 8 + ln]
        ln2, ix, iy, iw, ih = struct.unpack_from("<IHHHH", tim, 8 + ln)
        pix = tim[8 + ln + 12 : 8 + ln + ln2]
        ph = xxh3_64(pix)

        for row in range(3):
            rh = xxh3_64(clut[row * 32 : (row + 1) * 32])
            recolored = recolor_name_sheet(sheet_sources[idx], row)
            dst_name = f"texupload-P4-{ph:016X}-{rh:016X}-{iw}x{ih}-0-0-{iw*4}x{ih}-P0-15.png"
            recolored.save(OUT_MOD_SRC / dst_name)

    if OUT_EXP.parent.exists():
        OUT_EXP.mkdir(parents=True, exist_ok=True)
        for old in OUT_EXP.glob("*.png"):
            old.unlink()
        for png in OUT_MOD_SRC.glob("*.png"):
            shutil.copy2(png, OUT_EXP / png.name)

    files = sorted(OUT_MOD_SRC.glob("*.png"))
    print(f"Generated {len(files)} HD character-select textures in {OUT_MOD_SRC} and synced to {OUT_EXP}")


if __name__ == "__main__":
    main()
