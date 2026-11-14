"""Round-trip the BAG2 motion codec on synthetic data and, when present, a real dump."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/bag1import'))
import motion_codec  # noqa: E402

DUMP = ROOT / '_work/character_import/strike/viewer-run/20261106T055110/bag2jp_ram_6000.bin'


def synthetic():
    frames, step, bones = 7, 2, [0, 1]
    count = motion_codec.keyframes(frames, step)
    decoded = {'frames': frames, 'step': step, 'bones': bones,
               'translation': [[0, 5, -120, 300, 299][:count]] * 3,
               'rotations': [[[4000, 4119, 3999, 2000, 4095][:count]] * 3,
                             [[-10, -10, 0x7f5, -10, 0][:count]] * 3],
               'tails': [b''] * 8 + [b'\x78']}
    # Streams start at offset + 4 = 12: 8-byte header, two bone bytes, two padding bytes.
    prefix = struct.pack('<IHBB', 8, frames, step, len(bones)) + bytes(bones) + b'\0\0'
    return decoded, prefix


class MotionCodecTests(unittest.TestCase):
    def test_keyframe_count_matches_interpreter(self):
        self.assertEqual(motion_codec.keyframes(45, 2), 23)
        self.assertEqual(motion_codec.keyframes(55, 3), 19)
        self.assertEqual(motion_codec.keyframes(10, 1), 10)

    def test_synthetic_round_trip_uses_both_delta_widths(self):
        decoded, prefix = synthetic()
        data = motion_codec.encode(decoded, prefix)
        again = motion_codec.decode(data)
        for key in ('frames', 'step', 'bones', 'translation', 'rotations', 'tails'):
            self.assertEqual(again[key], decoded[key], key)
        self.assertEqual(again['end'], len(data))
        self.assertEqual(motion_codec.encode(again, prefix), data)

    def test_rotation_delta_out_of_range_is_rejected(self):
        decoded, prefix = synthetic()
        decoded['rotations'][0][0] = [0, 0x800, 0, 0, 0][:len(decoded['rotations'][0][0])]
        with self.assertRaises(ValueError):
            motion_codec.encode(decoded, prefix)

    @unittest.skipUnless(DUMP.exists(), 'Strike NEUTRAL 8 MB dump not available')
    def test_strike_wait_and_neutral_round_trip_from_ram(self):
        ram = DUMP.read_bytes()
        word = lambda a: struct.unpack_from('<I', ram, a - 0x80000000)[0]
        table = word(word(0x8005F808) + 0x824)
        for slot in (0, 71):
            start = word(table + 4 * slot) - 0x80000000
            decoded = motion_codec.decode(ram[start:start + 0x10000])
            raw = ram[start:start + decoded['end']]
            self.assertEqual(motion_codec.encode(decoded, raw[:decoded['offset'] + 4]), raw)


if __name__ == '__main__':
    unittest.main()
