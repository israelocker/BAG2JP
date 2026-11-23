"""Regression audit over every archived character variant (assets/archive/characters)."""
import struct
import unittest
from pathlib import Path

from tools.move_viewer import audit, pose

ROOT = Path(__file__).resolve().parents[3]
CHARACTERS = ROOT / 'assets/archive/characters'


class EmptyMotionTests(unittest.TestCase):
    def test_stub_is_empty_and_decode_says_so(self):
        bank = struct.pack('<I', 4) + bytes(4) + struct.pack('<I', 0)
        self.assertTrue(pose.is_empty_motion(bytes(4)))
        self.assertFalse(pose.is_empty_motion(bytes(4) + b'\x01'))
        with self.assertRaises(pose.EmptyMotionError):
            pose.decode_motion(bank, 0)


@unittest.skipUnless(CHARACTERS.is_dir(), 'archived characters absent')
class AllCharactersAuditTests(unittest.TestCase):
    def test_every_variant_has_no_blocking_finding(self):
        results = audit.audit_all(CHARACTERS, samples=2)
        self.assertEqual(len(results), 72)
        failing = {f"{r['char']}/{r['variant']}": audit.blocking(r)
                   for r in results if audit.blocking(r)}
        self.assertEqual(failing, {})


if __name__ == '__main__':
    unittest.main()
