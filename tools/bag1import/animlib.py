import struct
def dfs_entries(b):
    assert b[:4] == b'DFS_'
    n = struct.unpack_from('<I', b, 4)[0]
    return [b[o:o + s] for o, s in (struct.unpack_from('<II', b, 8 + 8 * i) for i in range(n))]
def anim_list(b, off=0):
    out = []; o = off
    while o + 4 <= len(b):
        s = struct.unpack_from('<I', b, o)[0]
        if s == 0: break
        out.append(b[o + 4:o + 4 + s]); o += 4 + s
    return out
def frames(d):
    return struct.unpack_from('<H', d, 4)[0] if len(d) >= 8 else 0
def info_off(d):
    a = struct.unpack_from('<I', d, 0)[0]
    return a + struct.unpack_from('<I', d, a)[0]
def info(d):
    """returns (header bytes, events[(type, frame, value)])"""
    o = info_off(d)
    n = struct.unpack_from('<H', d, o + 2)[0]
    p = o + n * 2 + 4; ev = []
    while True:
        t = struct.unpack_from('<H', d, p)[0]
        if t == 0: break
        ev.append(struct.unpack_from('<HHH', d, p)); p += 6
    return d[o:o + 4 + n * 2], ev, o, p + 2
