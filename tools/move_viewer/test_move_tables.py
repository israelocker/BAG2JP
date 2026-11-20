"""Host tests for move_tables: synthetic images plus the configured binaries when present."""
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.move_viewer import move_tables as mt  # noqa: E402


def synthetic():
    exe = bytearray(0x50000)
    overlay = bytearray(0x10000)

    def put(buf, base, address, data):
        buf[address - base:address - base + len(data)] = data
    names = [b"HEAT", b"STRIKE"]
    for i, name in enumerate(names):
        put(exe, mt.MAIN_BASE, 0x80010300 + 8 * i, name + b"\0")
        put(exe, mt.MAIN_BASE, mt.NAME_POINTERS + 4 * i, struct.pack("<I", 0x80010300 + 8 * i))
    put(exe, mt.MAIN_BASE, mt.REQ_SLOT_LOW, bytes(range(0x2B)))
    put(exe, mt.MAIN_BASE, mt.REQ_SLOT_MID + 60, bytes([0x39]))
    put(exe, mt.MAIN_BASE, mt.REQ_SLOT_MID + 61, bytes([0x50]))
    put(exe, mt.MAIN_BASE, mt.REQ_SLOT_HIGH + 110, bytes([0x44]))
    put(exe, mt.MAIN_BASE, mt.REQ_SLOT_DOWN, bytes([0x55]))
    put(exe, mt.MAIN_BASE, mt.POSE_COUNTS, bytes([2, 1]))
    put(exe, mt.MAIN_BASE, mt.FEVER_COUNTS, bytes([3, 5]))
    put(exe, mt.MAIN_BASE, mt.HIT_REQUEST, bytes([202, 1, 201, 2]))
    put(exe, mt.MAIN_BASE, mt.SOLO_LISTS + 16, bytes([0x35]))
    put(overlay, mt.OVERLAY_BASE, mt.SOLO_CHAIN, bytes([0x35, 2, 0x3C, 0, 0, 0, 0, 0]))
    return (mt.Image(bytes(exe), mt.MAIN_BASE, "exe"),
            mt.Image(bytes(overlay), mt.OVERLAY_BASE, "overlay"))


class SyntheticTests(unittest.TestCase):
    def setUp(self):
        self.exe, self.overlay = synthetic()

    def test_names_from_pointer_table(self):
        self.assertEqual(mt.character_names(self.exe), ["HEAT", "STRIKE"])

    def test_resolver_ranges(self):
        self.assertEqual(mt.resolve_slot(self.exe, 7), 7)
        self.assertEqual(mt.resolve_slot(self.exe, 60), 0x39)
        self.assertIsNone(mt.resolve_slot(self.exe, 61))  # > 0x4F means no slot
        self.assertEqual(mt.resolve_slot(self.exe, 110), 0x44)
        self.assertEqual(mt.resolve_slot(self.exe, 200), 0x55)

    def test_per_character_counts_drive_roles(self):
        heat = mt.role_requests(self.exe, self.overlay, 0)
        strike = mt.role_requests(self.exe, self.overlay, 1)
        count = lambda rows, role: sum(r == role for r, _, _ in rows)  # noqa: E731
        self.assertEqual((count(heat, "Pose"), count(heat, "Fever")), (2, 3))
        self.assertEqual((count(strike, "Pose"), count(strike, "Fever")), (1, 5))
        self.assertIn(("Solo 8", "code 53 (2 bars)", 60), heat)
        self.assertIn(("Down", "hit reaction (0x80051458)", 201), strike)

    def test_grid_excludes_finish_and_covers_levels(self):
        rows = mt.role_requests(self.exe, self.overlay, 0)
        grid = [q for r, _, q in rows if r == "Grid"]
        finish = [q for r, _, q in rows if r == "Finish/Groovin"]
        self.assertEqual(sorted(grid + finish), list(range(1, 43)))
        self.assertEqual(finish, list(mt.FINISH_REQUESTS))

    def test_wrong_base_is_rejected(self):
        with self.assertRaises(ValueError):
            mt.character_names(mt.Image(self.exe.data, mt.MAIN_BASE + 0x100, "x"))


@unittest.skipUnless(mt.ROOT.joinpath("_work/mainexe/slpm.bin").is_file(), "binaries absent")
class RealBinaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = mt.load_default()

    def test_eighteen_characters_known_ids(self):
        names = [c["name"] for c in self.result["characters"]]
        self.assertEqual(len(names), 18)
        self.assertEqual((names[0], names[1], names[5], names[9], names[10]),
                         ("HEAT", "STRIKE", "SHORTY", "BI-O", "CAPOEIRA"))

    def test_bytes_match_ghidra_reads(self):
        g = self.result["global"]
        # Ghidra read_memory 2026-11-19: 0x8005180C = 00 06 0b 15 35 ...
        self.assertEqual([g["request_slot"][str(r)] for r in range(5)], [0, 6, 0x0B, 0x15, 0x35])
        heat = self.result["characters"][0]
        self.assertEqual((heat["pose_count"], heat["fever_count"], heat["hit_request"]), (2, 3, [202, 1]))
        self.assertEqual(g["solo_lists"]["solo16"], [0x41, 0x45, 0x49, 0x4D])


if __name__ == "__main__":
    unittest.main()
