"""Rebuild BAG1/BAG2 stage thumbnails from the original menu assets.

BAG1 ST_SEL.BPE entry 23 + stage id holds each 154x64 BAG1 preview; BAG2
system/015.bpe content 029 + stage id holds each 186x60 BAG2 preview.
Strike (stage 1): BAG1 entry 24 is not Strike; entry 25 matches the
imported stage (ceiling light strips, grey corridor), BAG2 030 the vault.
"""
from pathlib import Path
import argparse, hashlib, sys, tempfile
from PIL import Image, ImageOps
root = Path(__file__).resolve().parents[2]
# name -> (BAG1 ST_SEL entry, BAG2 015.bpe preview index); verified visually.
STAGES = {"heat": (23, 29), "strike": (25, 30)}
p = argparse.ArgumentParser()
p.add_argument("--asset-tools", type=Path, default=root.parents[1] / "Tools/psx-asset-tools")
p.add_argument("--bag1", type=Path, default=root / "_work/bag1_disc/DFS1/ST_SEL.BPE")
p.add_argument("--bag2", type=Path, default=root / "assets/archive/system/015.bpe/content")
p.add_argument("--out", type=Path, default=root / "mods-src/bag2jp.feature.bag1-content/1.0.0/popup_assets")
p.add_argument("--stage", choices=sorted(STAGES), action="append")
a = p.parse_args()
sys.path.insert(0, str(a.asset_tools))
from psxassets import bpe, containers, tim
raw = bpe.decode(a.bag1.read_bytes())
assert containers.is_archive(raw), "BAG1 stage selector is not a DFS archive"
entries = containers.parse_archive(raw)
a.out.mkdir(parents=True, exist_ok=True)
for name in a.stage or sorted(STAGES):
    bag1_entry, bag2_index = STAGES[name]
    off, size = entries[bag1_entry]
    data = raw[off:off + size]
    assert tim.is_tim(data), f"BAG1 {name} thumbnail is not TIM"
    with tempfile.TemporaryDirectory() as scratch:
        preview = Path(scratch) / f"{name}.png"
        tim.to_png(data, preview)
        im = Image.open(preview).convert("RGB")
        assert im.size == (154, 64), "Unexpected BAG1 thumbnail layout"
        ImageOps.fit(im, (186, 60), Image.Resampling.LANCZOS).save(a.out / f"{name}_bag1.png")
    im = Image.open(a.bag2 / f"{bag2_index:03d}.png").convert("RGB")
    assert im.size == (186, 60), "Unexpected BAG2 thumbnail layout"
    im.save(a.out / f"{name}_bag2.png")
    for version in ("bag1", "bag2"):
        f = a.out / f"{name}_{version}.png"
        print(f.name, Image.open(f).size, hashlib.sha256(f.read_bytes()).hexdigest())
