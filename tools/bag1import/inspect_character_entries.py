"""Inspect native BAG2 character archive entries without modifying the disc.

The main executable encodes a loader byte as ``character | table_block << 5``.
The low five bits index one of 18 characters; blocks select costume/side in
the order A-P1, A-P2, B-P1, B-P2. This tool resolves the pack and model entry
IDs and inventories their DFS members through the raw-sector ISO reader.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
from pathlib import Path
import struct
import sys
from typing import Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))
from iso_extract import Disc

CHARACTER_COUNT = 18
TABLE_BLOCKS = 4
TABLE_HALFWORDS = CHARACTER_COUNT * TABLE_BLOCKS
PSX_EXE_HEADER_SIZE = 0x800
PACK_TABLE_ADDRESS = 0x80055180
MODEL_TABLE_ADDRESS = 0x80055258
TABLE_NAMES = ("costume_a_p1", "costume_a_p2", "costume_b_p1", "costume_b_p2")


def entry_for_loader_byte(table: Sequence[int], loader_byte: int) -> int:
    """Resolve one loader byte against a native 18-by-4 halfword table."""
    character_id = loader_byte & 0x1F
    block = loader_byte >> 5
    if character_id >= CHARACTER_COUNT or block >= TABLE_BLOCKS:
        raise ValueError("loader_byte selects outside the native character table")
    if len(table) != TABLE_HALFWORDS:
        raise ValueError("table must contain 72 halfwords")
    return table[block * CHARACTER_COUNT + character_id]


def entries_for_character(table: Sequence[int], character_id: int) -> dict[str, int]:
    """Return all costume/side entries for one native character ID."""
    if not 0 <= character_id < CHARACTER_COUNT:
        raise ValueError("character_id must be in range 0..17")
    return {
        name: entry_for_loader_byte(table, character_id | (block << 5))
        for block, name in enumerate(TABLE_NAMES)
    }


def read_halfword_table(executable: bytes, address: int) -> list[int]:
    """Read a 72-halfword table from a complete PS-X EXE image."""
    if len(executable) < PSX_EXE_HEADER_SIZE or executable[:8] != b"PS-X EXE":
        raise ValueError("invalid PS-X EXE")
    load_address = struct.unpack_from("<I", executable, 0x18)[0]
    offset = PSX_EXE_HEADER_SIZE + address - load_address
    size = TABLE_HALFWORDS * 2
    if offset < PSX_EXE_HEADER_SIZE or offset + size > len(executable):
        raise ValueError("table address is outside the executable")
    return list(struct.unpack_from(f"<{TABLE_HALFWORDS}H", executable, offset))


def sha256(data: bytes) -> str:
    """Return the SHA-256 of exact evidence bytes."""
    return hashlib.sha256(data).hexdigest()


def inspect_dfs(data: bytes) -> dict[str, object]:
    """Validate one DFS container and inventory all bounded members."""
    if len(data) < 8 or data[:4] != b"DFS_":
        raise ValueError("archive entry is not a DFS container")
    count = struct.unpack_from("<I", data, 4)[0]
    if 8 + count * 8 > len(data):
        raise ValueError("DFS member table exceeds the container")
    members: list[dict[str, object]] = []
    for index in range(count):
        offset, size = struct.unpack_from("<II", data, 8 + index * 8)
        if offset + size > len(data):
            raise ValueError(f"DFS member {index} exceeds the container")
        payload = data[offset:offset + size]
        members.append({
            "member": index,
            "offset": offset,
            "size": size,
            "prefix_hex": payload[:16].hex(),
            "sha256": sha256(payload),
        })
    return {"size": len(data), "sha256": sha256(data), "members": members}


def inspect_character(disc_path: Path, character_id: int) -> dict[str, object]:
    """Resolve and inventory one character from an original raw PS1 image."""
    disc = Disc(disc_path)
    try:
        extents = {name: (lba, size) for name, lba, size in disc.walk()}
        executable = disc.read(*extents["SLPM_862.19"])
        archive_lba, archive_size = extents["BUST2.BIN"]
        header = disc.read(archive_lba, 4096)
        if header[:4] != b"DF2_":
            raise ValueError("BUST2.BIN lacks a DF2 header")
        count = struct.unpack_from("<I", header, 4)[0]
        if 8 + count * 8 > len(header):
            raise ValueError("DF2 table exceeds the captured header")
        tables = {
            "packs": read_halfword_table(executable, PACK_TABLE_ADDRESS),
            "models": read_halfword_table(executable, MODEL_TABLE_ADDRESS),
        }
        resolved = {name: entries_for_character(table, character_id) for name, table in tables.items()}
        entries: dict[str, object] = {}
        for table_name, roles in resolved.items():
            for role, entry_id in roles.items():
                if entry_id >= count:
                    raise ValueError(f"entry {entry_id} exceeds the DF2 table")
                offset, size = struct.unpack_from("<II", header, 8 + entry_id * 8)
                if offset + size > archive_size:
                    raise ValueError(f"entry {entry_id} exceeds BUST2.BIN")
                payload = disc.read(archive_lba + offset // 2048, size + offset % 2048)[offset % 2048:]
                record = inspect_dfs(payload)
                record.update({
                    "entry": entry_id,
                    "archive_offset": offset,
                    "disc_user_offset": archive_lba * 2048 + offset,
                })
                entries[f"{table_name}.{role}"] = record
        return {
            "disc": str(disc_path),
            "character_id": character_id,
            "main_exe_sha256": sha256(executable),
            "entries": entries,
        }
    finally:
        disc.f.close()


def main() -> None:
    """Run the read-only character-entry inspection CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("disc", type=Path)
    parser.add_argument("character_id", type=int)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = inspect_character(args.disc, args.character_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    logging.info("Wrote %d verified entry roles to %s", len(report["entries"]), args.output)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
