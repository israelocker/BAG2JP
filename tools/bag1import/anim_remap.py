"""Rebuild a BAG2 model animation list (model_*/001.bin, 101 slots in BAG2 order) from a BAG1 list
(84 anims), plus the fever-time list (choreography_a/000.bin) from BAG1's fever anims.

Slot roles come from the motion request tables of both main executables (tools/bag1import/reqmap.py)
and an in-game trace of stock BAG2 (src/bag2jp_anim_trace.c). Request codes 100+ keep their meaning
in both games (106 stand, 110 attack, 124 miss, 130-135 hit, 140-142 win, 150-152 lose, 160+ fever);
dance moves (requests 1-48): see the grid notes below.

Anim events (info block after the channel data, records of u16 type, frame, value):
type 2/3 = sound cue, 1 = character effect (BAG2 character code), 16 = attack launch.
Sound cues are kept: the BAG1 voice banks replace BAG2 Heat's (pack SEDTs, see build_heat_test.sh).
Effect values 1-6 are hand-mesh swaps; BAG2 Heat's handler uses the same hand bones as BAG1 Heat.
usage: anim_remap.py <bag1 001.bin> <out model 001.bin> <bag2 choreography_a 000.bin> <out choreography 000.bin>
"""
import struct, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from animlib import anim_list, frames, info

EMPTY = b'\x00\x00\x00\x00'

# BAG2 slot -> BAG1 anim (non dance-move roles)
ROLES = {
    0: 0,                      # r0 idle bounce
    54: 51, 55: 52, 56: 53,    # r50-52 special singles
    57: 54, 58: 55, 59: 56,    # r60-62 special doubles
    60: 55, 61: 56, 62: 54,    # r63-65 special doubles (BAG2 only)
    63: 57, 64: 58, 65: 59, 66: 57,  # r70-73 special quads
    67: 64, 68: 61,            # r101/102 held poses
    69: 0, 70: 0,              # r107/108 recovery after specials (BAG1 has none: idle)
    71: 60,                    # r106 stand (before/after the dance)
    72: 62, 73: 62,            # r103/104 intro appeal
    74: 63,                    # r110 attack
    75: 65, 76: 66, 77: 67,    # r170-172 attack variants / counters
    78: 70,                    # r123
    79: 69, 80: 69, 81: 69, 82: 69, 83: 69, 84: 68,  # r124-129 miss
    85: 71, 86: 72, 87: 73, 88: 74, 89: 75, 90: 76,  # r130-135 / r200-210 hit by attack
    91: 72, 92: 74, 93: 76,    # r136-138
    94: 77, 95: 78, 96: 79,    # r140-142 win
    98: 80, 99: 81, 100: 80,   # r150-152 lose
}
# Dance moves. Both games pick a move per bar from a grid, but the grids differ:
#  BAG2: request = row base[level] + bar (main exe 0x8004DA14 = 1,5,11,17,23; levels 5-7 start at
#        bar 2/4/6). A row is one choreography played bar after bar; its last bar is a double.
#        Level-up (only into even bars) plays the row's alternate slot (table 0x80051838).
#  BAG1: cell (bar s 0..6, level v <= s), request s(s+1)/2 + (s - v) + 1 (command length grows with
#        v, constant along it); bar 7 = double, request 29 + (7 - v). The normal anim of (s, v) follows
#        (s-1, v); its alternate (table 0x80055854) follows a level-up from (s-1, v-1). Same rule as BAG2.
# Each BAG2 row (level L, bar s) maps to BAG1 bar s + (7 - last bar of the row), so every row ends on a
# BAG1 double, at BAG1 level min(L, bar): consecutive cells are always a designed BAG1 transition.
B2_ROWS = {0: (0, [6, 11, 21, 53]), 1: (0, [5, 10, 19, 26, 36, 52]), 2: (0, [4, 9, 17, 25, 34, 51]),
           3: (0, [3, 8, 15, 24, 32, 50]), 4: (0, [2, 7, 13, 23, 30, 39, 45, 49]),
           5: (2, [12, 22, 28, 38, 43, 48]), 6: (4, [27, 37, 41, 47]), 7: (6, [40, 46])}
B2_ALT = {19: 20, 17: 18, 15: 16, 13: 14, 34: 35, 32: 33, 30: 31, 28: 29, 43: 44, 41: 42}  # slot -> alt
def b1_path(L):
    s0, row = B2_ROWS[L]; k = 7 - (s0 + len(row) - 1)
    return [(s + k, min(L, s + k)) for s in range(s0, s0 + len(row))]
B1_PATHS = {L: b1_path(L) for L in B2_ROWS}
B1_REQ_ANIM = [None, 1, 2, 3, 4, 5, 7, 8, 9, 11, 13, 14, 15, 17, 19, 21, 22, 23, 25, 27, 29, 31, 32, 33,
               35, 37, 39, 41, 43, 44, 45, 46, 47, 48, 49, 50]     # BAG1 table 0x80055830
B1_ALT = {5: 6, 9: 10, 11: 12, 15: 16, 17: 18, 19: 20, 23: 24, 25: 26, 27: 28, 29: 30, 33: 34, 35: 36,
          37: 38, 39: 40, 41: 42}

def b1_anim(cell, prev):
    s, v = cell
    if s == 7: return B1_REQ_ANIM[29 + 7 - max(v, 1)]           # doubles: level 1..7
    a = B1_REQ_ANIM[s * (s + 1) // 2 + (s - v) + 1]
    if prev and prev[1] == v - 1: a = B1_ALT.get(a, a)          # entered by a level-up
    return a

def dance_slots():
    slots = {}
    for L, (s0, row) in B2_ROWS.items():
        path = B1_PATHS[L]
        for i, slot in enumerate(row):
            slots[slot] = b1_anim(path[i], path[i - 1] if i else None)
            s = s0 + i
            if slot in B2_ALT:                                 # entered by level-up from (L-1, s-1)
                ps0, prow = B2_ROWS[L - 1]
                slots[B2_ALT[slot]] = b1_anim(path[i], B1_PATHS[L - 1][s - 1 - ps0])
    return slots

def fix_events(d, attack=False):
    """Attack launch (type 16) uses BAG2 Heat's handler: value 0, mid-swing frame."""
    d = bytearray(d)
    hb, ev, o, end = info(bytes(d))
    p = o + len(hb)
    for t, f, v in ev:
        if t == 16:
            v = 0
            if attack: f = 29          # BAG2 Heat launches the fire mid-swing (frame 38 of 66)
        struct.pack_into('<HHH', d, p, t, f, v); p += 6
    return bytes(d)

def build(b1):
    slots = dance_slots()
    slots.update(ROLES)
    out = bytearray(); used = {}
    for i in range(101):
        if i in (1, 97):
            data = EMPTY
        else:
            src = slots[i]; used[i] = src
            data = fix_events(b1[src], attack=(i == 74))
        out += struct.pack('<I', len(data)) + data
    out += b'\x00' * 4
    return bytes(out), used

if __name__ == '__main__':
    b1 = anim_list(open(sys.argv[1], 'rb').read())
    assert len(b1) == 84
    data, used = build(b1)
    open(sys.argv[2], 'wb').write(data)
    missing = [i for i in range(101) if i not in used and i not in (1, 97)]
    print(f'model 001: {len(data)} bytes (BAG2 stock 280484), slots missing: {missing}')
    print('map:', ' '.join(f'{k}<{v}' for k, v in sorted(used.items())))
    ch = anim_list(open(sys.argv[3], 'rb').read())
    fever = [fix_events(b1[82]), fix_events(b1[83]), fix_events(b1[82])] + [EMPTY] * (len(ch) - 3)
    out = b''.join(struct.pack('<I', len(x)) + x for x in fever) + b'\x00' * 4
    open(sys.argv[4], 'wb').write(out)
    print(f'choreography 000: {len(out)} bytes (stock {os.path.getsize(sys.argv[3])}), {len(ch)} slots')
