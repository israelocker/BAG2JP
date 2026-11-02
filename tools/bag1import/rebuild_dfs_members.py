"""Rebuild a `DFS_` container with selected members replaced, keeping the table honest.

BAG1 imports replace individual members inside a stock BAG2 archive member container
(character packs hold texture TIMs, models hold the mesh plus the animation list). A
member's length changes with the replacement, so every later member has to move and the
offset/size table must be rewritten with the new positions.

Getting that table wrong is silent: the game keeps loading successfully but every member
lookup returns the same bytes. That is exactly how a Strike pack once served member 0
(the name-plate TIM) as the body texture and froze the versus screen.

Layout, from the stock files: `DFS_`, a little-endian member count, `count` pairs of
little-endian {offset, size}, then the members back to back without padding.

Usage:
    py -3.13 tools/bag1import/rebuild_dfs_members.py --spec containers.json

The spec names one container per row:

    {"containers": [{"source": "stock.dfs", "out": "built.dfs",
                     "replace": {"3": "new_member.tim"}}]}
"""
import argparse
import json
import struct
from pathlib import Path

MAGIC = b"DFS_"
HEADER = 8


class DfsError(ValueError):
    """Raised when a container does not match the documented layout."""


def read_members(data: bytes) -> tuple[list[bytes], int]:
    """Return the member payloads plus the byte count of trailing padding."""
    if len(data) < HEADER or data[:4] != MAGIC:
        raise DfsError("not a DFS_ container")
    count = struct.unpack_from("<I", data, 4)[0]
    table_end = HEADER + count * 8
    if count == 0 or table_end > len(data):
        raise DfsError(f"member count {count} does not fit the header")

    members = []
    previous_end = table_end
    for index in range(count):
        offset, size = struct.unpack_from("<II", data, HEADER + index * 8)
        if size == 0:
            raise DfsError(f"member {index} is empty")
        if offset < previous_end or offset + size > len(data):
            raise DfsError(f"member {index} at {offset}+{size} is out of bounds or overlaps")
        members.append(data[offset:offset + size])
        previous_end = offset + size
    return members, len(data) - previous_end


def build_container(members: list[bytes]) -> bytes:
    """Pack members sequentially and describe them with the matching table."""
    if not members:
        raise DfsError("a container needs at least one member")
    table_end = HEADER + len(members) * 8
    out = bytearray(MAGIC)
    out += struct.pack("<I", len(members))
    out += b"\x00" * (len(members) * 8)
    offsets = []
    for member in members:
        if not member:
            raise DfsError("refusing to write an empty member")
        offsets.append((len(out), len(member)))
        out += member
    for index, (offset, size) in enumerate(offsets):
        struct.pack_into("<II", out, HEADER + index * 8, offset, size)
    return bytes(out)


def replace_members(source: bytes, replacements: dict[int, bytes]) -> bytes:
    """Rebuild `source` with the named members swapped in."""
    members, _padding = read_members(source)
    for index, payload in replacements.items():
        if not 0 <= index < len(members):
            raise DfsError(f"member {index} does not exist (container has {len(members)})")
        if not payload:
            raise DfsError(f"member {index} replacement is empty")
        members[index] = payload
    rebuilt = build_container(members)
    check, _ = read_members(rebuilt)
    if check != members:
        raise AssertionError("rebuilt container does not read back as written")
    return rebuilt


def build_from_spec(spec: dict, root: Path) -> list[dict]:
    """Build every container in the spec, reporting what changed."""
    report = []
    for row in spec["containers"]:
        source_path = (root / row["source"]).resolve()
        out_path = (root / row["out"]).resolve()
        source = source_path.read_bytes()
        stock, padding = read_members(source)
        replacements = {int(index): (root / name).resolve().read_bytes()
                        for index, name in row.get("replace", {}).items()}
        rebuilt = replace_members(source, replacements)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(rebuilt)
        report.append({
            "out": str(out_path),
            "members": len(stock),
            "stock_bytes": len(source),
            "stock_padding": padding,
            "bytes": len(rebuilt),
            "delta": len(rebuilt) - len(source),
            "replaced": {str(index): len(payload) for index, payload in sorted(replacements.items())},
        })
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True, help="container spec JSON")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="base for relative paths")
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    report = build_from_spec(spec, args.root)
    for row in report:
        members = ", ".join(f"{index}:{size}B" for index, size in row["replaced"].items())
        print(f"{Path(row['out']).name}: {row['members']} members, "
              f"{row['bytes']} B ({row['delta']:+d}), replaced [{members}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
