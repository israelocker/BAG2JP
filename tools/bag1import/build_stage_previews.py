"""Rebuild the two Heat stage thumbnails from the original BAG1/BAG2 menu assets."""
from pathlib import Path
import argparse, hashlib, sys, tempfile
from PIL import Image, ImageOps
root = Path(__file__).resolve().parents[2]
p = argparse.ArgumentParser()
p.add_argument("--asset-tools", type=Path, default=root.parents[1] / "Tools/psx-asset-tools")
p.add_argument("--bag1", type=Path, default=root / "_work/bag1_disc/DFS1/ST_SEL.BPE")
p.add_argument("--bag2", type=Path, default=root / "assets/archive/system/015.bpe/content/029.png")
p.add_argument("--out", type=Path, default=root / "mods-src/bag2jp.feature.bag1-content/1.0.0/popup_assets")
a = p.parse_args()
sys.path.insert(0, str(a.asset_tools))
from psxassets import bpe, containers, tim
raw = bpe.decode(a.bag1.read_bytes())
assert containers.is_archive(raw), "BAG1 stage selector is not a DFS archive"
entries = containers.parse_archive(raw)
off, size = entries[23]  # ST_SEL: first stage preview, Heat's room/fire background.
data = raw[off:off + size]
assert tim.is_tim(data), "BAG1 Heat thumbnail is not TIM"
a.out.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory() as scratch:
    preview = Path(scratch) / "heat.png"
    tim.to_png(data, preview)
    im = Image.open(preview).convert("RGB")
    assert im.size == (154, 64), "Unexpected BAG1 thumbnail layout"
    ImageOps.fit(im, (186, 60), Image.Resampling.LANCZOS).save(a.out / "heat_bag1.png")
im = Image.open(a.bag2).convert("RGB")
assert im.size == (186, 60), "Unexpected BAG2 thumbnail layout"
im.save(a.out / "heat_bag2.png")
for name in ("heat_bag1.png", "heat_bag2.png"):
    f = a.out / name
    print(name, Image.open(f).size, hashlib.sha256(f.read_bytes()).hexdigest())
