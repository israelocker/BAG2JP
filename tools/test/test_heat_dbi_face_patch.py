"""Local Heat regression: the BAG2 face MoveImage calls must not run for BAG1 Heat.

With BAG1 textures loaded, the BAG2 Heat DBI face animation copies rects over the
BAG1 flame strip (tpage x768 y256) used by the native attack effect. These byte
checks do not establish visual acceptance.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/bag1import"))
from alternate_payload import BASE, ROW
from patch_heat_dbi import MOVE_IMAGE_JAL, MOVE_IMAGE_SITES, nop_attack_render, nop_face_move_image
from rebuild_dfs_members import read_members

PACKAGE = ROOT / "mods-src/bag2jp.feature.bag1-content"
# (entry, DBI member index): costume A P1/P2, costume B P1/P2.
HEAT_PACK_DBIS = ((59, 1), (60, 0), (131, 1), (132, 0))


def jal_sites(data: bytes) -> list[int]:
    return [i for i in range(0, len(data) - 3, 4) if data[i:i + 4] == MOVE_IMAGE_JAL]


class HeatDbiFacePatchTests(unittest.TestCase):
    def test_nop_face_move_image_clears_exactly_the_calls(self) -> None:
        stock = (ROOT / "assets/archive/characters/heat/pack_a_p1/001.dbi").read_bytes()
        patched = bytearray(stock)
        nop_face_move_image(patched)
        self.assertEqual(len(jal_sites(stock)), MOVE_IMAGE_SITES)
        self.assertEqual(jal_sites(patched), [])
        changed = [i for i in range(0, len(stock), 4) if stock[i:i + 4] != patched[i:i + 4]]
        self.assertEqual(changed, jal_sites(stock))

    def test_payload_heat_dbis_have_no_face_move_image(self) -> None:
        payload = (PACKAGE / "1.0.0/payload/bag1_alt.bin").read_bytes()
        rows = {int(row[1]): row for row in ROW.finditer(
            (PACKAGE / "bag2jp_bag1_alt_index.h").read_text())}
        for entry, member in HEAT_PACK_DBIS:
            with self.subTest(entry=entry):
                row = rows[entry]
                offset = int(row[6], 16) - BASE
                dbi = read_members(payload[offset:offset + int(row[7])])[0][member]
                self.assertEqual(len(dbi), 19556)
                self.assertEqual(jal_sites(dbi), [])
                self.assertIsNone(nop_attack_render(bytearray(dbi)))

    def test_nop_attack_render_clears_only_the_renderer_call(self) -> None:
        for dbi_path in ("pack_a_p1/001.dbi", "pack_a_p2/000.dbi"):
            with self.subTest(dbi=dbi_path):
                stock = (ROOT / f"assets/archive/characters/heat/{dbi_path}").read_bytes()
                patched = bytearray(stock)
                offset = nop_attack_render(patched)
                self.assertIsNotNone(offset)
                changed = [i for i in range(0, len(stock), 4) if stock[i:i + 4] != patched[i:i + 4]]
                self.assertEqual(changed, [offset])
                self.assertEqual(stock[offset + 3], 0x0C)
                self.assertIsNone(nop_attack_render(patched))


if __name__ == "__main__":
    unittest.main()
