"""Patch BAG2 Heat's character code (pack DBI) for the BAG1 Heat model.

1. The outfit-A init (p1 0x801CEDA8) fills dancer+0x7CC[bone] = animation slot. BAG2 Heat outfit A has
   an extra unanimated bone 12 (chest piece) and the head at bone 13, so it stores slot 12 at bone 13.
   BAG1 Heat has the head at bone 12 and the beanie at bone 13 (child of the head, unanimated), so the
   store `sb v0(=12), 0xd(t8)` becomes `sb v0, 0xc(t8)`: head animated, beanie left at 0xFF.
   Everything else in that table (arms 14-19, hand bones) already matches BAG1.
2. --outfit-b: BAG1 Heat uses the same skeleton for both costumes, so the outfit-B packs run the
   outfit-A path: the `bnez v0` on dancer+6 (costume) in the init (p1 0x801CEDC8) and in the setup
   handler (p1 0x801CFC10, hand bone indices) become nops.
usage: patch_heat_dbi.py <dbi in> <dbi out> [--outfit-b]"""
import sys

def patch(d, seq, new_last):
    n = d.count(seq)
    assert n == 1, f'pattern {seq.hex()} found {n} times'
    i = d.find(seq) + len(seq) - 4
    d[i:i + 4] = new_last
    return i - 12

d = bytearray(open(sys.argv[1], 'rb').read())
offs = [patch(d, bytes.fromhex('0c000224' '0d000924' '0e000624' '0f000724' '10000524' '0d0002a3'),
              bytes.fromhex('0c0002a3'))]
if '--outfit-b' in sys.argv:
    offs.append(patch(d, bytes.fromhex('06004292' '00000000' '3a004014'), bytes(4)))
    offs.append(patch(d, bytes.fromhex('06000292' '00000000' '21004014'), bytes(4)))
open(sys.argv[2], 'wb').write(d)
print(f'{sys.argv[1]}: patched at payload offsets', ', '.join(f'0x{o:x}' for o in offs))
