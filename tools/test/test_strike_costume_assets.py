"""Local asset regression: BAG1 folder pairs select costume, suffix A/B selects side.

Requires the inventoried legal-disc extracts in _work; skips without those inputs.
Native SCUS_942.63 FUN_8003AE20 indexes costume by 28 and player side by 14.
This checks candidate bytes, not in-game visual acceptance.
"""
import hashlib
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/bag1import"))
from model_bag1_to_bag2 import convert
from rebuild_dfs_members import read_members
from tim_retarget import retarget
from alternate_payload import BASE, ROW
from model_bag1_to_bag2 import check_bag2
from animlib import anim_list

SOURCE_ROOT = ROOT / "_work/bag1_disc"
CANDIDATE = ROOT / "_work/character_import/strike/alternate_dfs"
STOCK = ROOT / "_work/character_import/strike/original_dfs"


@unittest.skipUnless((SOURCE_ROOT / "PLAYER4/P_STRIA4.DFS").is_file(),
                     "Requires local BAG1 source assets")
class StrikeCostumeAssetsTests(unittest.TestCase):
    def test_native_neutral_is_preserved_for_all_four_models(self) -> None:
        """A required neutral must contain its native clip, not an empty slot."""
        source, _ = read_members((SOURCE_ROOT / 'PLAYER2/P_STRIA2.DFS').read_bytes())
        neutral = anim_list(source[1])[0]
        package = ROOT / 'mods-src/bag2jp.feature.bag1-content'
        payload = (package / '1.0.0/payload/bag1_alt.bin').read_bytes()
        rows = {int(row[1]): row for row in ROW.finditer(
            (package / 'bag2jp_bag1_alt_index.h').read_text(encoding='utf-8'))}
        for entry in (109, 110, 181, 182):
            with self.subTest(entry=entry):
                row = rows[entry]
                start = int(row[6], 16) - BASE
                members, _ = read_members(payload[start:start + int(row[7])])
                self.assertEqual(anim_list(members[1])[0], neutral)

    def test_package_keeps_models_separate_from_texture_packs(self) -> None:
        """The loader expects two model members, never a texture/DBI pack."""
        package = ROOT / "mods-src/bag2jp.feature.bag1-content"
        payload = (package / "1.0.0/payload/bag1_alt.bin").read_bytes()
        rows = {int(row[1]): row for row in ROW.finditer(
            (package / "bag2jp_bag1_alt_index.h").read_text())}
        for entry in (109, 110, 181, 182):
            with self.subTest(entry=entry):
                row = rows[entry]
                offset = int(row[6], 16) - BASE
                members, _ = read_members(payload[offset:offset + int(row[7])])
                self.assertEqual(len(members), 2, "Model entry replaced with a texture pack")
                self.assertEqual(struct.unpack_from("<I", members[0])[0], 44)
                self.assertEqual(check_bag2(members[0]), 0)
                self.assertEqual(len(anim_list(members[1])), 101)
        self.assertTrue({22, 40, 59, 60, 95, 96, 131, 132, 167, 168, 200} <= rows.keys(),
                        "Existing Heat entries must all be preserved")

    def test_candidate_models_follow_costume_on_both_player_sides(self) -> None:
        """Wrong costume-to-folder assignments must fail even if skeletons match."""
        for costume, folder, number in (("a", "PLAYER2", 2), ("b", "PLAYER4", 4)):
            for side, suffix in (("p1", "A"), ("p2", "B")):
                with self.subTest(costume=costume, side=side):
                    source, _ = read_members((SOURCE_ROOT / folder / f"P_STRI{suffix}{number}.DFS").read_bytes())
                    expected, _, _ = convert(source[0])
                    actual, _ = read_members((CANDIDATE / f"model_{costume}_{side}.dfs").read_bytes())
                    self.assertEqual(hashlib.sha256(actual[0]).digest(), hashlib.sha256(expected).digest())

    def test_candidate_atlas_follows_costume_not_player_side(self) -> None:
        """Costume B needs the extra CLUT row used by its shirt emblem."""
        for costume, folder, number in (("a", "PLAYER1E", 1), ("b", "PLAYER3E", 3)):
            for side, suffix, slot in (("p1", "A", 2), ("p2", "B", 1)):
                with self.subTest(costume=costume, side=side):
                    source, _ = read_members((SOURCE_ROOT / folder / f"P_STRI{suffix}{number}.DFS").read_bytes())
                    stock, _ = read_members((STOCK / f"pack_{costume}_{side}.dfs").read_bytes())
                    actual, _ = read_members((CANDIDATE / f"pack_{costume}_{side}.dfs").read_bytes())
                    self.assertEqual(hashlib.sha256(actual[slot]).hexdigest(),
                                     hashlib.sha256(retarget(source[4], stock[slot])).hexdigest())


if __name__ == "__main__":
    unittest.main()
