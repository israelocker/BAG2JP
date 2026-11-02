"""Preview the real native menu UV recipe without generating replacement art."""
from pathlib import Path
import re
from PIL import Image

root = Path(__file__).resolve().parents[2]
source = (root / "mods-src/bag2jp.feature.endings-view/bag2jp_endings_view.c").read_text()
table = source.split("s_label_glyphs[][3] = {", 1)[1].split("};", 1)[0]
glyphs = [tuple(map(int, item)) for item in re.findall(r"\{(\d+),(\d+),(\d+)\}", table)]
atlas = Image.open(root / "assets/archive/system/016/001.png").convert("RGBA")
width = sum(w for _, _, w in glyphs) + 8
label = Image.new("RGBA", (width, 24))
x = 0
for i, (u, v, w) in enumerate(glyphs):
    if i == 6:
        x += 8
    label.alpha_composite(atlas.crop((u, v, u + w, v + 24)), (x, 0))
    x += w
sheet = Image.new("RGBA", (192, 72), (130, 190, 215, 255))
sheet.alpha_composite(atlas.crop((0, 72, 192, 96)), (0, 0))
sheet.alpha_composite(label, ((192 - width) // 2, 24))
sheet.alpha_composite(atlas.crop((0, 96, 192, 120)), (0, 48))
out = root / "_work/endings-view/native-lettering-preview.png"
out.parent.mkdir(parents=True, exist_ok=True)
sheet.resize((768, 288), Image.Resampling.NEAREST).save(out)
print(out)
