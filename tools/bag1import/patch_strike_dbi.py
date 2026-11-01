"""Patch BAG2 Strike's character code (pack DBI) for the BAG1 Strike model.

Based on the Heat DBI patch (patch_heat_dbi.py), adapted for Strike's skeleton.

Analysis of Strike DBI (P_STRIA1.DFS entry 003, 5422 bytes):
- sb $3, 0x000D($2) at offset 0x000C6C: stores $v1 (animation slot) at bone offset 0x0D
- sb $3, 0x000E($2) at offset 0x000C74: stores $v1 at bone offset 0x0E

Strike BAG1 has 42 bones; BAG2 Strike has a different skeleton layout.
The patch moves the head/accessory binding from bone 13 (0x0D) to bone 12 (0x0C),
matching the BAG1 Strike skeleton where the head is at a different index than BAG2.

Usage: patch_strike_dbi.py <dbi in> <dbi out> [--outfit-b]
"""
import sys
import struct


def patch(d, seq, new_last):
    """Replace the last 4 bytes of seq with new_last at the first occurrence of seq."""
    n = d.count(seq)
    assert n == 1, f'pattern {seq.hex()} found {n} times'
    i = d.find(seq) + len(seq) - 4
    d[i:i + 4] = new_last
    return i - 12


d = bytearray(open(sys.argv[1], 'rb').read())

# Patch 1: Move head/accessory binding from bone 13 (0x0D) to bone 12 (0x0C)
# Original: sb $3, 0x000D($2) -> MIPS value 0xA043000D
#           Stored in file little-endian: 0D 00 43 A0
# Patched:  sb $3, 0x000C($2) -> MIPS value 0xA043000C
#           Stored in file little-endian: 0C 00 43 A0
offs = [patch(d, struct.pack('<I', 0xA043000D),
              struct.pack('<I', 0xA043000C))]

if '--outfit-b' in sys.argv:
    # Outfit B: Strike uses the same skeleton for both costumes (like Heat),
    # so the outfit-B path should follow the outfit-A path.
    # The 'bnez v0' on costume check becomes nop (0x00000000).
    offs.append(patch(d, bytes.fromhex('06004292000000003a004014'),
                      bytes(4)))
    offs.append(patch(d, bytes.fromhex('060002920000000021004014'),
                      bytes(4)))

open(sys.argv[2], 'wb').write(d)
print(f'{sys.argv[1]}: patched at payload offsets',
      ', '.join(f'0x{o:x}' for o in offs))
