"""Local Heat regression: models and body atlas follow costume, not player side.

Native BAG1 selection uses side*14 + costume*28 + character (SCUS_942.63
FUN_8003AE20). These byte checks do not establish visual acceptance.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/bag1import"))
from alternate_payload import BASE, ROW
from model_bag1_to_bag2 import convert
from rebuild_dfs_members import read_members
from tim_retarget import parse


@unittest.skipUnless((ROOT / "_work/bag1_disc/PLAYER4/P_HEATA4.DFS").is_file(),
                     "Requires local BAG1 extracts")
class HeatCostumeAssetsTests(unittest.TestCase):
    def test_package_models_and_atlases_use_same_costume_on_both_sides(self) -> None:
        """P2 must not silently substitute the alternate costume's model."""
        package = ROOT / "mods-src/bag2jp.feature.bag1-content"
        payload = (package / "1.0.0/payload/bag1_alt.bin").read_bytes()
        rows = {int(row[1]): row for row in ROW.finditer(
            (package / "bag2jp_bag1_alt_index.h").read_text())}

        def members(entry: int) -> list[bytes]:
            """Read one indexed archive with the shared strict DFS parser."""
            row = rows[entry]
            offset = int(row[6], 16) - BASE
            return read_members(payload[offset:offset + int(row[7])])[0]

        for costume, pack_folder, model_folder, number, pack_ids, model_ids in (
            ("a", "PLAYER1E", "PLAYER2", 2, (59, 60), (95, 96)),
            ("b", "PLAYER3E", "PLAYER4", 4, (131, 132), (167, 168)),
        ):
            for side, suffix in enumerate(("A", "B")):
                with self.subTest(costume=costume, side=side):
                    source, _ = read_members((ROOT / "_work/bag1_disc" / model_folder /
                                             f"P_HEAT{suffix}{number}.DFS").read_bytes())
                    expected, _, tail = convert(source[0])
                    self.assertEqual(tail, 0)
                    actual = members(model_ids[side])[0]
                    self.assertEqual(actual[:len(expected)], expected)
                    self.assertFalse(any(actual[len(expected):]), "Only zero padding may follow model")
                    source_pack, _ = read_members((ROOT / "_work/bag1_disc" / pack_folder /
                                                  f"P_HEAT{suffix}{number - 1}.DFS").read_bytes())
                    _, expected_clut, expected_image = parse(source_pack[4])
                    _, actual_clut, actual_image = parse(members(pack_ids[side])[2 - side])
                    self.assertEqual(actual_image["data"], expected_image["data"])
                    self.assertEqual(actual_clut["data"][:len(expected_clut["data"])],
                                     expected_clut["data"])


if __name__ == "__main__":
    unittest.main()
