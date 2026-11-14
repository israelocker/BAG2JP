"""Unit tests for Gas-O character code (DBI) patching."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/bag1import"))

from patch_gaso_dbi import (
    patch_gaso_dbi,
    P1_INIT_OFF, P1_EVENT_OFF, P1_POST_OFF,
    P2_INIT_OFF, P2_EVENT_OFF, P2_POST_OFF,
)
from rebuild_dfs_members import read_members
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32


class TestGasoDbiPatch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        stock_bio_dir = ROOT / "_work/stage_import/gaso/stock_bio_entries"
        stock_p1, _ = read_members((stock_bio_dir / "pack_a_p1.dfs").read_bytes())
        stock_p2, _ = read_members((stock_bio_dir / "pack_a_p2.dfs").read_bytes())
        cls.stock_p1_dbi = stock_p1[1]
        cls.stock_p2_dbi = stock_p2[0]

    def test_p1_patch_length_and_header(self):
        patched = patch_gaso_dbi(self.stock_p1_dbi)
        self.assertEqual(len(patched), len(self.stock_p1_dbi))
        self.assertEqual(patched[:12], self.stock_p1_dbi[:12])

    def test_p2_patch_length_and_header(self):
        patched = patch_gaso_dbi(self.stock_p2_dbi)
        self.assertEqual(len(patched), len(self.stock_p2_dbi))
        self.assertEqual(patched[:12], self.stock_p2_dbi[:12])

    def test_p1_init_stores(self):
        patched = patch_gaso_dbi(self.stock_p1_dbi)
        md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32)
        insns = list(md.disasm(patched[P1_INIT_OFF:P1_INIT_OFF + 264], 0x801CEDBC))
        stores = [i for i in insns if i.mnemonic == "sb"]
        # Exactly 35 store byte instructions matching native Gas-O
        self.assertEqual(len(stores), 35)
        # Stores include 0x7cc base and 0x80b
        store_targets = [s.op_str.split(",")[-1].strip() for s in stores]
        self.assertIn("0x7cc($a0)", store_targets)
        self.assertIn("0x80b($a0)", store_targets)
        # Ends with jr $ra
        jr_insns = [i for i in insns if i.mnemonic == "jr" and i.op_str == "$ra"]
        self.assertEqual(len(jr_insns), 1)

    def test_p1_postprocess_node_copies(self):
        patched = patch_gaso_dbi(self.stock_p1_dbi)
        md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32)
        insns = list(md.disasm(patched[P1_POST_OFF:P1_POST_OFF + 468], 0x801CF1B0))
        # No jal instructions (no zombie calls)
        jals = [i for i in insns if i.mnemonic == "jal"]
        self.assertEqual(len(jals), 0)
        # 7 bal instructions (calls to copy_node)
        bals = [i for i in insns if i.mnemonic == "bal"]
        self.assertEqual(len(bals), 7)
        # Check node offsets loaded in $a1 and $a2 before the 7 bals:
        expected_offsets = [
            (0x0b00, 0x0dc0),  # 16 -> 20
            (0x0d10, 0x0fd0),  # 19 -> 23
            (0x0b00, 0x0e70),  # 16 -> 21
            (0x0d10, 0x1080),  # 19 -> 24
            (0x0d10, 0x11e0),  # 19 -> 26
            (0x0840, 0x1130),  # 12 -> 25
            (0x0b00, 0x0f20),  # 16 -> 22
        ]
        addius = [i for i in insns if i.mnemonic == "addiu" and ("$a1" in i.op_str or "$a2" in i.op_str)]
        pairs = []
        for j in range(0, len(addius), 2):
            val1 = int(addius[j].op_str.split(",")[-1], 16)
            val2 = int(addius[j + 1].op_str.split(",")[-1], 16)
            pairs.append((val1, val2))
        self.assertEqual(pairs, expected_offsets)
        # Ends with jr $ra
        jr_insns = [i for i in insns if i.mnemonic == "jr" and i.op_str == "$ra"]
        self.assertEqual(len(jr_insns), 2)  # main return and copy_node return

    def test_p1_event_stub(self):
        patched = patch_gaso_dbi(self.stock_p1_dbi)
        md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32)
        insns = list(md.disasm(patched[P1_EVENT_OFF:P1_EVENT_OFF + 748], 0x801CEEC4))
        # First instruction is jr $ra
        self.assertEqual(insns[0].mnemonic, "jr")
        self.assertEqual(insns[0].op_str, "$ra")
        # Delay slot is addiu $v0, $zero, 0
        self.assertEqual(insns[1].mnemonic, "addiu")
        self.assertIn("$v0", insns[1].op_str)
        # No jals or memory writes in event handler
        jals = [i for i in insns if i.mnemonic in ("jal", "jalr")]
        self.assertEqual(len(jals), 0)


if __name__ == "__main__":
    unittest.main()
