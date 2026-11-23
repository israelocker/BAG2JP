"""Independent byte fixtures for the native PHV2 producer contract."""
from dataclasses import FrozenInstanceError
import struct
import unittest

from tools.move_viewer.prehistory import parse_prehistory, select_actor_record


def record_bytes(frame=37, actor=0x80100000, weight=2048,
                 local=b'L' * 960, history=b'H' * 960, magic=0x32564850):
    return struct.pack('<4I', magic, frame, actor, weight) + local + history


class PrehistoryTest(unittest.TestCase):
    def test_preserves_two_actors_and_distinct_raw_payloads_in_order(self):
        local = bytes(range(256)) * 3 + bytes(range(192))
        history = local[::-1]
        records = parse_prehistory(
            record_bytes(local=local, history=history) +
            record_bytes(actor=0x80101000, local=b'A' * 960, history=b'B' * 960))
        self.assertIsInstance(records, tuple)
        self.assertEqual([(r.frame, r.actor, r.draw_weight,
                           r.local_matrices, r.history_matrices) for r in records],
                         [(37, 0x80100000, 2048, local, history),
                          (37, 0x80101000, 2048, b'A' * 960, b'B' * 960)])
        self.assertIsInstance(records[0].local_matrices, bytes)
        self.assertIsInstance(records[0].history_matrices, bytes)

    def test_record_is_immutable(self):
        record = parse_prehistory(record_bytes())[0]
        with self.assertRaises(FrozenInstanceError):
            record.frame = 5

    def test_rejects_mutable_or_aliasing_input_buffers(self):
        data = bytearray(record_bytes())
        for buffer in (data, memoryview(data), memoryview(bytes(data))):
            with self.subTest(buffer_type=type(buffer)), self.assertRaises(ValueError):
                parse_prehistory(buffer)

    def test_preserves_full_unsigned_halfword_from_producer(self):
        for weight in (0, 4096, 4097, 65535):
            with self.subTest(weight=weight):
                self.assertEqual(parse_prehistory(record_bytes(weight=weight))[0].draw_weight,
                                 weight)

    def test_rejects_empty_truncated_trailing_and_partial_second_record(self):
        valid = record_bytes()
        for data in (b'', valid[:15], valid[:-1], valid + b'x', valid + valid[:-1]):
            with self.subTest(length=len(data)):
                with self.assertRaises(ValueError):
                    parse_prehistory(data)

    def test_checks_magic_in_every_record(self):
        invalid = record_bytes(magic=0x31564850)
        for data in (invalid, record_bytes() + invalid):
            with self.subTest(length=len(data)):
                with self.assertRaises(ValueError):
                    parse_prehistory(data)

    def test_checks_weight_in_every_record(self):
        for weight in (65536, 0xFFFFFFFF):
            for prefix in (b'', record_bytes()):
                with self.subTest(weight=weight, prefix=bool(prefix)):
                    with self.assertRaises(ValueError):
                        parse_prehistory(prefix + record_bytes(weight=weight))

    def test_selects_exact_frame_actor_pair(self):
        records = parse_prehistory(record_bytes() + record_bytes(frame=38) +
                                   record_bytes(actor=0x80101000))
        self.assertIs(select_actor_record(records, 37, 0x80101000), records[2])

    def test_selection_rejects_missing_exact_pair(self):
        records = parse_prehistory(record_bytes())
        for frame, actor in ((38, 0x80100000), (37, 0x80101000)):
            with self.subTest(frame=frame, actor=actor):
                with self.assertRaises(ValueError):
                    select_actor_record(records, frame, actor)
        with self.assertRaises(ValueError):
            select_actor_record((), 37, 0x80100000)

    def test_preserves_repeated_calls_and_rejects_ambiguous_selection(self):
        records = parse_prehistory(record_bytes() + record_bytes(local=b'X' * 960))
        self.assertEqual(len(records), 2)
        self.assertEqual(records[1].local_matrices, b'X' * 960)
        with self.assertRaises(ValueError):
            select_actor_record(records, 37, 0x80100000)


if __name__ == '__main__':
    unittest.main()
