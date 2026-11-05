"""Nop the BAG2 face MoveImage calls and the attack fire renderer call in the BAG1 Heat pack DBIs
of the alternate payload.

See patch_heat_dbi.py (patches 3 and 4). Already-patched DBIs are left unchanged.
usage: patch_heat_face_payload.py <package dir>"""
import sys
from pathlib import Path

from alternate_payload import BASE, ROW, repack
from patch_heat_dbi import MOVE_IMAGE_JAL, nop_attack_render, nop_face_move_image
from rebuild_dfs_members import read_members, replace_members

# (entry, DBI member index): costume A P1/P2, costume B P1/P2.
HEAT_PACK_DBIS = ((59, 1), (60, 0), (131, 1), (132, 0))


def main() -> int:
    package = Path(sys.argv[1])
    payload_path = package / "1.0.0/payload/bag1_alt.bin"
    header_path = package / "bag2jp_bag1_alt_index.h"
    payload = payload_path.read_bytes()
    header = header_path.read_text()
    rows = {int(row[1]): row for row in ROW.finditer(header)}
    replacements = {}
    for entry, member in HEAT_PACK_DBIS:
        offset = int(rows[entry][6], 16) - BASE
        archive = payload[offset:offset + int(rows[entry][7])]
        members, padding = read_members(archive)
        dbi = bytearray(members[member])
        face = MOVE_IMAGE_JAL in dbi
        if face:
            nop_face_move_image(dbi)
        if nop_attack_render(dbi) is None and not face:
            continue
        # Keep the archive's trailing padding so the loaded size stays unchanged.
        rebuilt = replace_members(archive, {member: bytes(dbi)})
        replacements[entry] = rebuilt + archive[len(archive) - padding:]
        assert len(replacements[entry]) == len(archive), f"entry {entry} changed size"
        print(f"entry {entry}: member {member} patched")
    if not replacements:
        print("nothing to patch")
        return 0
    result, header, _ = repack(payload, header, replacements)
    payload_path.write_bytes(result)
    header_path.write_text(header)
    print(f"payload {len(result)} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
