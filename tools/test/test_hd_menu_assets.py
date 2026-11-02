"""Verify the built menu atlas/provenance; run after build_hd_menu.py with py -3.13."""
from pathlib import Path
import hashlib
import json
import unittest
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "mods-src/bag2jp.feature.endings-view/1.0.0/menu_hd"


class HdMenuAssetsTests(unittest.TestCase):
    def test_source_provenance_and_complete_row_coverage(self):
        source = ROOT / "assets/ui/ending-view-menu.png"
        meta = json.loads((OUT / "ready.txt").read_text())
        with Image.open(source) as image:
            self.assertEqual(meta.get("source_size"), list(image.size))
            bands = meta.get("source_bands", [])
            self.assertEqual(len(bands), 7)
            self.assertEqual(bands[0], 0)
            self.assertEqual(bands[-1], image.height)
        self.assertEqual(meta["source_sha256"], hashlib.sha256(source.read_bytes()).hexdigest())

    def test_both_palettes_contain_six_nonempty_transparent_cells(self):
        meta = json.loads((OUT / "ready.txt").read_text())
        self.assertEqual(len(meta["files"]), 2)
        for filename in meta["files"]:
            with Image.open(OUT / filename) as image:
                self.assertEqual(image.size, (1536, 960))
                self.assertEqual(image.mode, "RGBA")
                for i, (u, v, width) in enumerate(meta["cells"]):
                    cell = image.crop((u * 8, v * 8, (u + width) * 8, (v + 24) * 8))
                    self.assertEqual(cell.getchannel("A").getextrema(), (0, 255))
                    self.assertGreater(cell.convert("L").getextrema()[1], 100)
                    bbox = cell.getchannel("A").getbbox()
                    self.assertIsNotNone(bbox)
                    left, top, right, bottom = bbox
                    # Artwork is 85% of the previous fitted size and centered.
                    self.assertLessEqual(right - left, round(width * 8 * 0.85) + 2)
                    self.assertLessEqual(bottom - top, round(meta["visible_heights"][i] * 8 * 0.85) + 2)
                    self.assertGreaterEqual(top, 4 * 8)
                    self.assertGreaterEqual(cell.height - bottom, 4 * 8)


if __name__ == "__main__":
    unittest.main()
