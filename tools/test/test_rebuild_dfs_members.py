"""Container rebuild checks: offsets must follow the members, never a stale constant.

A replacement member changes later offsets. Writing the table wrongly still loads, which is
why this needs a test rather than a manual look at the bytes.
"""
import importlib.util
import struct
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "rebuild_dfs_members", Path(__file__).parents[1] / "bag1import/rebuild_dfs_members.py")
dfs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dfs)

MAGIC = b"DFS_"


def container(members: list[bytes]) -> bytes:
    """Stock-shaped container: header, table, members back to back."""
    out = bytearray(MAGIC + struct.pack("<I", len(members)))
    out += b"\x00" * (len(members) * 8)
    for index, member in enumerate(members):
        struct.pack_into("<II", out, 8 + index * 8, len(out), len(member))
        out += member
    return bytes(out)


class ReadTests(unittest.TestCase):
    def test_members_are_read_back_in_order(self):
        data = container([b"one", b"two", b"three"])
        members, padding = dfs.read_members(data)
        self.assertEqual(members, [b"one", b"two", b"three"])
        self.assertEqual(padding, 0)

    def test_trailing_padding_is_reported_not_swallowed(self):
        members, padding = dfs.read_members(container([b"one", b"two"]) + b"\x00\x00")
        self.assertEqual(padding, 2)
        self.assertEqual(len(members), 2)

    def test_non_dfs_file_is_rejected(self):
        with self.assertRaises(dfs.DfsError):
            dfs.read_members(b"XXXX" + bytes(16))

    def test_overlapping_members_are_rejected(self):
        data = bytearray(container([b"aaaa", b"bbbb"]))
        struct.pack_into("<I", data, 16, 8)  # second member points at the header
        with self.assertRaises(dfs.DfsError):
            dfs.read_members(bytes(data))


class BuildTests(unittest.TestCase):
    def test_member_after_halfword_dbi_stays_dma_word_aligned(self):
        """An unaligned TIM makes DMA upload its header height as colour zero."""
        rebuilt = dfs.build_container([b'DBI_' + bytes(2), b'TIM!'])
        offset, size = struct.unpack_from('<II', rebuilt, 16)
        self.assertEqual(offset % 4, 0)
        self.assertEqual(rebuilt[offset:offset + size], b'TIM!')

    def test_every_member_gets_its_own_offset(self):
        rebuilt = dfs.build_container([b"aaaa", b"bb", b"cccccc"])
        offsets = [struct.unpack_from("<II", rebuilt, 8 + index * 8)[0] for index in range(3)]
        self.assertEqual(offsets, [32, 36, 40])

    def test_growing_a_member_moves_the_later_ones(self):
        source = container([b"aaaa", b"bb", b"cc"])
        rebuilt = dfs.replace_members(source, {0: b"aaaaaa"})
        self.assertEqual(dfs.read_members(rebuilt)[0], [b"aaaaaa", b"bb", b"cc"])
        offsets = [struct.unpack_from("<II", rebuilt, 8 + index * 8)[0] for index in range(3)]
        self.assertEqual(offsets, [32, 40, 44])

    def test_unknown_member_is_rejected(self):
        with self.assertRaises(dfs.DfsError):
            dfs.replace_members(container([b"aa"]), {3: b"bb"})

    def test_empty_replacement_is_rejected(self):
        with self.assertRaises(dfs.DfsError):
            dfs.replace_members(container([b"aa"]), {0: b""})


if __name__ == "__main__":
    unittest.main()
