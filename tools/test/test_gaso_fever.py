"""Gas-O solo fever choreography is rebuilt from BAG1 fever animations 82/83."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/bag1import"))

from anim_remap import EMPTY  # noqa: E402
from anim_remap_gaso import FEVER_SOURCES, build_fever  # noqa: E402
from animlib import anim_list, info  # noqa: E402

GASO_SOURCE = ROOT / "_work/character_inventory/gaso/001.bin"
BIO_FEVER = ROOT / "assets/archive/characters/bi_o/choreography_a/000.bin"


def voice_cues(anim: bytes) -> set[int]:
    return {value for event_type, _, value in info(anim)[1] if event_type in (2, 3) and value >= 0x100}


@unittest.skipUnless(GASO_SOURCE.exists() and BIO_FEVER.exists(), "Gas-O BAG1 source or stock fever missing")
class TestGasoFever(unittest.TestCase):
    def setUp(self) -> None:
        self.source = anim_list(GASO_SOURCE.read_bytes())
        self.stock = anim_list(BIO_FEVER.read_bytes())
        self.fever = anim_list(build_fever(self.source, len(self.stock)))

    def test_fever_keeps_stock_slot_count_with_empty_tail(self) -> None:
        self.assertEqual(len(self.fever), len(self.stock))
        self.assertTrue(all(anim == EMPTY for anim in self.fever[len(FEVER_SOURCES):]))

    def test_fever_motions_come_from_bag1_fever_animations(self) -> None:
        for slot, source in enumerate(FEVER_SOURCES):
            self.assertEqual(self.fever[slot][:info(self.fever[slot])[2]],
                             self.source[source][:info(self.source[source])[2]])

    def test_fever_voices_use_rebased_gaso_bank(self) -> None:
        cues = set().union(*(voice_cues(anim) for anim in self.fever[:len(FEVER_SOURCES)]))
        self.assertEqual(cues, {0x6908, 0x6909})

    def test_too_few_stock_slots_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_fever(self.source, len(FEVER_SOURCES) - 1)


if __name__ == "__main__":
    unittest.main()
