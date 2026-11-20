"""Rebuild a BAG2 model animation list (model_*/001.bin, 101 slots in BAG2 order) from a BAG1 list
(84 anims), plus the fever-time list (choreography_a/000.bin) from BAG1's fever anims.

Request codes and role names differ between games. audit_animation_roles.py compares both
Dance View tables with the installed animation bytes. The data policy in profiles/heat-animation-policy.json overrides legacy ROLES entries
with documented exact matches/adaptations and required target events.
Dance moves (requests 1-42): see the grid notes below.

Anim events (info block after the channel data, records of u16 type, frame, value):
type 2/3 = sound cue, 1 = character effect (BAG2 character code), 16 = attack launch.
Sound cues 0x1000+ move to the BAG1 version's own range (rebase_cues.py) together with its voice bank,
so BAG1 and BAG2 Heat can share a match (one global cue table, first id match wins).
Effect values 1-6 are hand-mesh swaps; BAG2 Heat's handler uses the same hand bones as BAG1 Heat.
usage: anim_remap.py <bag1 001.bin> <out model 001.bin> <bag2 choreography_a 000.bin> <out choreography 000.bin>
"""
import struct, sys, os
from pathlib import Path
from animation_policy import load_policy, native_variant, adapt_events
POLICY = load_policy(Path(__file__).with_name("profiles") / "heat-animation-policy.json", Path(__file__).resolve().parents[2])
sys.path.insert(0, os.path.dirname(__file__))
from animlib import anim_list, frames, info
from rebase_cues import rebase_events, b1_cue_base

CHAR_ID = 0                 # BAG2 char id (Heat): BAG1 cue ids 0x1000+ -> b1_cue_base(CHAR_ID)

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
#        v, constant along it); bar 7 = double, request 35 - v for levels 0..6 (BAG1 0x800243f4 decodes
#        requests >= 29 as bar 7, level 35 - request). The normal anim of (s, v) follows
#        (s-1, v); its alternate (table 0x80055854) follows a level-up from (s-1, v-1). Same rule as BAG2.
# Each BAG2 row (level L, bar s) maps to BAG1 bar s + (7 - last bar of the row), so every row ends on a
# BAG1 double, at BAG1 level min(B1_LEVEL[L], bar). Within a row, consecutive cells are designed BAG1
# transitions, except row 0's first cell (clap override below). Between rows, B1_LEVEL is not monotonic
# (L3 -> L4 drops 3 -> 0, L4 -> L5 jumps 0 -> 4), so BAG2 level-ups across row 4 have no BAG1 level-up
# variant: native_variant keeps the normal anim there (e.g. slot 44 == slot 43). Unresolved by design.
B2_ROWS = {0: (0, [6, 11, 21, 53]), 1: (0, [5, 10, 19, 26, 36, 52]), 2: (0, [4, 9, 17, 25, 34, 51]),
           3: (0, [3, 8, 15, 24, 32, 50]), 4: (0, [2, 7, 13, 23, 30, 39, 45, 49]),
           5: (2, [12, 22, 28, 38, 43, 48]), 6: (4, [27, 37, 41, 47]), 7: (6, [40, 46])}
B2_ALT = {19: 20, 17: 18, 15: 16, 13: 14, 34: 35, 32: 33, 30: 31, 28: 29, 43: 44, 41: 42}  # slot -> alt
# Target BAG1 level per BAG2 row ("escalado", owner 2026-11-20): L4, the only 8-bar row, plays the full
# BAG1 level-0 combo (bars 0-6 plus the level-0 double), so 34 of the 35 BAG1 grid anims are used
# (only anim 2 is not) and no anim fills more than 3 rows (v = L left 3 anims unused, others in 4-5).
B1_LEVEL = {0: 0, 1: 1, 2: 2, 3: 3, 4: 0, 5: 4, 6: 5, 7: 6}
if set(B1_LEVEL) != set(B2_ROWS) or not all(0 <= v <= 6 for v in B1_LEVEL.values()):
    raise ValueError("B1_LEVEL must map every BAG2 row to a BAG1 level 0..6")

def b1_path(L: int) -> list[tuple[int, int]]:
    """Return the BAG1 (bar, level) cell played by each bar of BAG2 row L."""
    s0, row = B2_ROWS[L]; k = 7 - (s0 + len(row) - 1)
    path = [(s + k, min(B1_LEVEL[L], s + k)) for s in range(s0, s0 + len(row))]
    if L == 0:
        # BAG2 starts every combo (request 1) on row 0; BAG1 starts it on cell A (bar 0). PCSX-Redux
        # traced BAG1 req 1 -> anim 1; that A is the clap is inferred from stills (owner accepted the
        # BAG2 take 2026-11-20). Replaces cell (4, 0), so row 0 jumps from bar 0 to bar 5.
        path[0] = (0, 0)
    return path
B1_PATHS = {L: b1_path(L) for L in B2_ROWS}
B1_REQ_ANIM = [None, 1, 2, 3, 4, 5, 7, 8, 9, 11, 13, 14, 15, 17, 19, 21, 22, 23, 25, 27, 29, 31, 32, 33,
               35, 37, 39, 41, 43, 44, 45, 46, 47, 48, 49, 50]     # BAG1 table 0x80055830
B1_ALT = {5: 6, 9: 10, 11: 12, 15: 16, 17: 18, 19: 20, 23: 24, 25: 26, 27: 28, 29: 30, 33: 34, 35: 36,
          37: 38, 39: 40, 41: 42}

def b1_anim(cell, prev):
    s, v = cell
    if s == 7: return B1_REQ_ANIM[35 - min(v, 6)]               # doubles: level 0..6
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
    for edge in POLICY["alternate_edges"]:
        slots[edge["slot"]] = native_variant(slots[edge["normal_slot"]], slots[edge["previous_slot"]], POLICY["native_transitions"])
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

def mute_voices(d, lo=0x1000, hi=0x2000):
    """Fever: BAG1 anims 82/83 (requests 160/161) fire Heat voice cue 0x1006 eight times plus low values
    0-3, which the engine plays from the character bank (1 -> 0x1001, the BAG1 hit shouts); BAG2's
    fever has no voices (only 0x1C04/05). Point them at a missing cue (play returns -1, no sound)."""
    d = bytearray(d)
    hb, ev, o, end = info(bytes(d))
    p = o + len(hb)
    for t, f, v in ev:
        if t in (2, 3) and lo <= v < hi: v = 0x1FFF
        struct.pack_into('<HHH', d, p, t, f, v); p += 6
    return bytes(d)

def build(b1):
    slots = dance_slots()
    slots.update(ROLES)
    if any(not 0 <= row["target"] < 101 or not 0 <= row["source"] < len(b1) for row in POLICY["roles"]):
        raise ValueError("Animation role outside source/target list")
    rules = {row["target"]: row for row in POLICY["roles"]}
    slots.update({slot: row["source"] for slot, row in rules.items()})
    out = bytearray(); used = {}
    for i in range(101):
        if i in (1, 97):
            data = EMPTY
        else:
            src = slots[i]; used[i] = src
            data = rebase_events(fix_events(b1[src], attack=(i == 74)), 0x1000, b1_cue_base(CHAR_ID), 0x100)
            if i in rules: data = adapt_events(data, rules[i])
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
    # all char-bank cues muted (low values are bank-relative)
    fever = [mute_voices(fix_events(b1[i]), 0, 0x2000) for i in (82, 83, 82)] + [EMPTY] * (len(ch) - 3)
    out = b''.join(struct.pack('<I', len(x)) + x for x in fever) + b'\x00' * 4
    open(sys.argv[4], 'wb').write(out)
    print(f'choreography 000: {len(out)} bytes (stock {os.path.getsize(sys.argv[3])}), {len(ch)} slots')
    # duet fever (choreography_b, BAG2 dances): its Heat bank cues 0x1000/0x1001 (BAG2 Heat fever
    # shouts) would play BAG1 Heat's hit voices from the swapped bank 1 -> muted
    if len(sys.argv) > 6:
        cb = anim_list(open(sys.argv[5], 'rb').read())
        out = b''.join(struct.pack('<I', len(x)) + (mute_voices(x, 0x1000, 0x1100) if len(x) > 8 else x) for x in cb) + b'\x00' * 4
        open(sys.argv[6], 'wb').write(out)
        print(f'choreography_b: {len(cb)} slots, Heat voice cues muted')
