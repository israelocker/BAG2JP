"""Rebuild a BAG2 model animation list (model_*/001.bin, 101 slots in BAG2 order) from a BAG1 list
(84 anims), plus the fever-time list (choreography_a/000.bin) from BAG1's fever anims.

Slot roles come from the motion request tables of both main executables (tools/bag1import/reqmap.py)
and an in-game trace of stock BAG2 (src/bag2jp_anim_trace.c). Request codes 100+ keep their meaning
in both games (106 stand, 110 attack, 124 miss, 130-135 hit, 140-142 win, 150-152 lose, 160+ fever);
dance moves (requests 1-48) are matched by length (single bar / double) in difficulty order.

Anim events (info block after the channel data, records of u16 type, frame, value):
type 2/3 = sound cue, 1 = character effect (BAG2 character code), 16 = attack launch.
BAG1 sound cues 0x1000+ point into BAG1 voice banks, which BAG2 does not load yet: 0x1006 (BAG1 step
sound in dance moves) becomes the BAG2 step pair 0x1000/0x1001, other 0x10xx cues are dropped.
Effect values 3 and 6 are dropped (BAG2 Heat's code only knows 1/2/4/5 there).
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
# BAG2 dance-move slots in request order (primary, then the alternate played after a given move)
B2_SINGLE = [6, 11, 21, 5, 10, 19, 26, 36, 4, 9, 17, 25, 34, 3, 8, 15, 24, 32, 2, 7, 13, 23, 30, 39, 45,
             12, 22, 28, 38, 43, 27, 37, 41, 40]
B2_DOUBLE = [53, 52, 51, 50, 49, 48, 47, 46]
B2_ALT = {20: 19, 18: 17, 16: 15, 14: 13, 35: 34, 33: 32, 31: 30, 29: 28, 44: 43, 42: 41}  # alt <- primary
B1_SINGLE = [1, 2, 3, 4, 5, 7, 8, 9, 11, 13, 14, 15, 17, 19, 21, 22, 23, 25, 27, 29, 31, 32, 33, 35, 37,
             39, 41, 43]
B1_DOUBLE = [44, 45, 46, 47, 48, 49, 50]
B1_ALT = {5: 6, 9: 10, 11: 12, 15: 16, 17: 18, 19: 20, 23: 24, 25: 26, 27: 28, 29: 30, 33: 34, 35: 36,
          37: 38, 39: 40, 41: 42}

def fix_events(d, attack=False):
    """Rewrite the event list in place (same record count, dropped records become type 2 cue 0xFFFF)."""
    d = bytearray(d)
    hb, ev, o, end = info(bytes(d))
    p = o + len(hb); step = 0
    for t, f, v in ev:
        if t in (2, 3) and v >= 0x1000:
            if v == 0x1006 and t == 2:
                v = 0x1000 + (step & 1); step += 1
            else:
                v = 0xFFFF
        elif t == 1 and v in (3, 6):
            t, v = 2, 0xFFFF
        elif t == 16:
            v = 0
            if attack: f = 29          # BAG2 Heat launches the fire mid-swing (frame 38 of 66)
        struct.pack_into('<HHH', d, p, t, f, v); p += 6
    return bytes(d)

def build(b1):
    slots = {}
    singles = B1_SINGLE + B1_SINGLE[::-1]
    for i, s in enumerate(B2_SINGLE):
        slots[s] = singles[i]
    for i, s in enumerate(B2_DOUBLE):
        slots[s] = B1_DOUBLE[i % len(B1_DOUBLE)]
    for alt, prim in B2_ALT.items():
        slots[alt] = B1_ALT.get(slots[prim], slots[prim])
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
