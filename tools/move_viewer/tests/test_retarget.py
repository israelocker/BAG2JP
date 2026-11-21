"""Retarget keeps bytes under identity and refuses unreviewed tracks."""
import struct
import sys
import unittest
from pathlib import Path

from tools.move_viewer import retarget

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'bag1import'))
import motion_codec  # noqa: E402


def motion(bones=(0, 1), root=(100, -50, 7), events=b'\x00\x00\x02\x00\x00\x00\x00\x00'):
    frames, step = 3, 1
    head = struct.pack('<IHBB', 0, frames, step, len(bones)) + bytes(bones)
    offset = len(head)
    decoded = {'frames': frames, 'step': step, 'bones': list(bones),
               'translation': [[v, v + 1, v + 2] for v in root],
               'rotations': [[[i, i + 3, i + 6]] * 3 for i in range(len(bones))],
               'tails': [b''] * (3 * (1 + len(bones)))}
    streams = motion_codec.encode(decoded, b'')
    prefix = bytearray(struct.pack('<I', offset) + head[4:] + struct.pack('<I', 4 + len(streams)))
    body = bytes(prefix) + streams + events
    return struct.pack('<I', len(body)) + body


class RetargetTest(unittest.TestCase):
    def test_identity_is_byte_exact(self):
        m = motion()
        self.assertEqual(retarget.apply(m, retarget.Retarget({0: 0, 1: 1}, 1.0)), m)

    def test_scale_moves_root_and_event_pointer(self):
        m = motion(root=(100, -50, 7))
        out = retarget.apply(m, retarget.Retarget({0: 0, 1: 1}, 2.0))
        d = motion_codec.decode(out[4:])
        self.assertEqual(d['translation'][0], [200, 202, 204])
        self.assertEqual(out[-8:], m[-8:])
        self.assertEqual(struct.unpack_from('<I', out, 4 + d['offset'])[0] + d['offset'],
                         len(out) - 4 - 8)

    def test_unmapped_or_merged_tracks_refused(self):
        with self.assertRaisesRegex(ValueError, 'no reviewed mapping'):
            retarget.apply(motion(), retarget.Retarget({0: 0}, 1.0))
        with self.assertRaisesRegex(ValueError, 'merges'):
            retarget.apply(motion(), retarget.Retarget({0: 0, 1: 0}, 1.0))


if __name__ == '__main__':
    unittest.main()
