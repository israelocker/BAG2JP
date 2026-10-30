"""Give a BAG1 character version its own sound cue ids, so it can share a match with the BAG2 version.

BAG2 loads both players' voice banks into one global cue table (0x8007F180, 12-byte records) and
FUN_8002E2D0 plays the FIRST record whose id matches. Each character owns 0x1000 + n*0x100 (Heat 0x1000,
Strike 0x1100, ... up to 0x2100), so a mirror match normally loads two identical banks. With BAG1 Heat
on one side and BAG2 Heat on the other, ids 0x1000-0x1007 existed in both banks and the first loaded won:
the other Heat's anims played the wrong voices (BAG2 Heat's short 0x1000/0x1001 shouts became BAG1's
1 s phrases). BAG1 versions therefore use 0x6000 + BAG2 char id * 0x100 (free range).

usage: rebase_cues.py <in.sedt> <out.sedt> <old base hex> <new base hex>   (ids old..old+0xFF)
       or import: rebase_events(anim, old, new, count), rebase_sedt(data, old, new)"""
import struct, sys, os
sys.path.insert(0, os.path.dirname(__file__))

B1_CUE_BASE = 0x6000

def b1_cue_base(char_id):
    return B1_CUE_BASE + char_id * 0x100

def rebase_sedt(d, old, new):
    d = bytearray(d)
    n = struct.unpack_from('<I', d, 4)[0] // 3
    offs = struct.unpack_from('<%dI' % (3 * n), d, 8)
    moved = 0
    for b in range(n):
        t = offs[2 * n + b]
        for i in range(struct.unpack_from('<I', d, t)[0]):
            p = t + 4 + 8 * i
            cid = struct.unpack_from('<H', d, p)[0]
            if old <= cid < old + 0x100:
                struct.pack_into('<H', d, p, cid - old + new); moved += 1
    return bytes(d), moved

def rebase_events(a, old, new, count):
    """Anim events type 2/3 with ids old..old+count-1 -> new base (ids the BAG1 bank really has)."""
    from animlib import info
    d = bytearray(a)
    hb, ev, o, end = info(bytes(d))
    p = o + len(hb)
    for t, f, v in ev:
        if t in (2, 3) and old <= v < old + count: v = v - old + new
        struct.pack_into('<HHH', d, p, t, f, v); p += 6
    return bytes(d)

def sedt_ids(d, lo, hi):
    n = struct.unpack_from('<I', d, 4)[0] // 3
    offs = struct.unpack_from('<%dI' % (3 * n), d, 8)
    out = []
    for b in range(n):
        t = offs[2 * n + b]
        out += [struct.unpack_from('<H', d, t + 4 + 8 * i)[0] for i in range(struct.unpack_from('<I', d, t)[0])]
    return [x for x in out if lo <= x < hi]

if __name__ == '__main__':
    d, moved = rebase_sedt(open(sys.argv[1], 'rb').read(), int(sys.argv[3], 16), int(sys.argv[4], 16))
    open(sys.argv[2], 'wb').write(d)
    print(f'{sys.argv[2]}: {moved} cue ids rebased')
