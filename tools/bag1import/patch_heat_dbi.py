"""Patch BAG2 Heat's character code (pack DBI) for the BAG1 Heat model (outfit A slot).

The outfit-A init (p1 0x801CEDA8) fills dancer+0x7CC[bone] = animation slot. BAG2 Heat outfit A has an
extra unanimated bone 12 (chest piece) and the head at bone 13, so it stores slot 12 at bone 13.
BAG1 Heat has the head at bone 12 and the beanie at bone 13 (child of the head, unanimated), so the
store `sb v0(=12), 0xd(t8)` becomes `sb v0, 0xc(t8)`: head animated, beanie left at 0xFF (follows the
head). Everything else in that table (arms 14-19) already matches BAG1.
usage: patch_heat_dbi.py <dbi in> <dbi out>"""
import sys
SEQ = bytes.fromhex('0c000224' '0d000924' '0e000624' '0f000724' '10000524' '0d0002a3')
d = bytearray(open(sys.argv[1], 'rb').read())
n = d.count(SEQ)
assert n == 1, f'pattern found {n} times'
i = d.find(SEQ) + len(SEQ) - 4
d[i:i + 4] = bytes.fromhex('0c0002a3')
open(sys.argv[2], 'wb').write(d)
print(f'{sys.argv[1]}: patched head slot store at payload offset 0x{i - 12:x}')
