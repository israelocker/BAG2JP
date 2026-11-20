"""Safety checks that prevent deployment from unverified Strike assumptions."""
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

PROJECT = Path(__file__).parents[2]
sys.path.insert(0, str(PROJECT / "tools/bag1import"))
from animlib import anim_list, info, info_off
import anim_remap_strike


class StrikeImportSafetyTests(unittest.TestCase):
    def test_animation_builder_rejects_unaccepted_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "animations.bin"
            result = subprocess.run(
                [
                    sys.executable,
                    str(PROJECT / "tools/bag1import/anim_remap_strike.py"),
                    str(PROJECT / "_work/character_inventory/strike/001.bin"),
                    str(output),
                ],
                cwd=PROJECT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())
            self.assertIn("policy is not accepted", result.stderr)

    @unittest.skipUnless((PROJECT / "_work/character_inventory/strike/001.bin").is_file(),
                         "Requires local BAG1 Strike animation list")
    def test_strike_policy_populates_all_99_active_slots_and_preserves_semantics(self) -> None:
        source = anim_list((PROJECT / "_work/character_inventory/strike/001.bin").read_bytes())
        built, used, missing = anim_remap_strike.build(source)
        slots = anim_list(built)
        self.assertEqual(len(slots), 101)
        self.assertEqual(missing, [])
        self.assertEqual([i for i, s in enumerate(slots) if len(s) <= 4], [1, 97])
        for slot, data in enumerate(slots):
            self.assertEqual(len(data) % 4, 0, f"slot {slot} is not word-aligned")
        for slot in range(2, 67):
            header, events, _, _ = info(slots[slot])
            beats = struct.unpack_from("<H", header, 2)[0]
            expected_beats = 8 if 46 <= slot <= 53 or 57 <= slot <= 62 else 16 if 63 <= slot <= 66 else 4
            self.assertEqual(beats, expected_beats, f"slot {slot} beat mismatch")
            self.assertNotIn(used[slot], (82, 83), f"slot {slot} mapped to fever animation")
        self.assertEqual(used[6], 1)  # request 1 opens on BAG1 cell A, the clap (owner 2026-11-20)
        self.assertEqual(used[11], 31)
        self.assertEqual(used[16], 16)
        self.assertEqual(used[18], 18)
        self.assertEqual(used[71], 60)
        self.assertEqual(used[78], 69)
        for slot, source_idx in ((67, 64), (68, 60)):
            self.assertEqual(used[slot], source_idx)
            self.assertEqual(slots[slot][info_off(slots[slot]) + 5], 1)
        for slot, effect in ((76, 902), (77, 903)):
            self.assertIn((1, 1, effect), info(slots[slot])[1])
            self.assertFalse(any(t == 16 for t, _, _ in info(slots[slot])[1]))
        attack_events = info(slots[74])[1]
        self.assertEqual([(t, f, v) for t, f, v in attack_events if t == 16], [(16, 26, 0)])
        self.assertIn((1, 21, 1100), attack_events)
        self.assertIn((2, 26, 0x6104), attack_events)


if __name__ == "__main__":
    unittest.main()
