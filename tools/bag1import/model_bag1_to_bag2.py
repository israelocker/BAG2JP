"""Convert a Bust A Groove 1 model (P_xxxA2.DFS entry 000.bin) to the Bust A Groove 2 layout.

Both games share the model file: u32 bone count, count x 4 s32 links (parent?, child, sibling,
next root), then one record per bone in tree order (roots via link[3], each root recursing
child -> sibling): u32 type, payload, 10 u32 transform.
  type 0: nothing    type 2: u32 bone index (shares that bone's mesh)
  type 3/4: same layout in both games
  type 1 (mesh): header + data. BAG1 header = 0x3C words, BAG2 header = 0x48 words:
    BAG1 [0x01..0x1C] runtime pointers (28)   -> BAG2 [0x01..0x24] (36, 8 new, zero in files)
    BAG1 [0x1D..0x2E] counts (18 words)       -> BAG2 [0x25..0x36]; BAG2 adds [0x37..0x3A] = 0
    BAG1 [0x2F..0x3B] other fields (13)       -> BAG2 [0x3B..0x47]
  The primitive arrays that follow are the same in both games (BAG2 only adds new kinds).
Sizes per mesh (both games, from the parsers at BAG1 0x80029624 / BAG2 0x800220B8)."""
import struct, sys

def walk_order(links):
    order, root = [], 0
    def rec(n):
        if n < 0: return
        order.append(n); rec(links[n][1]); rec(links[n][2])
    while root >= 0:
        rec(root); root = links[root][3]
    return order

def mesh_len_bag1(w, i):
    """words of a type 0-2 mesh starting at w[i] (BAG1 header)."""
    h = lambda k: w[i + k]
    sh = lambda byteoff, hi: struct.unpack('<hh', struct.pack('<i', w[i + byteoff]))[1 if hi else 0]
    p = 0x3C + h(0x1D) * 2
    for _ in range(h(0x1F) + h(0x20)):
        p += w[i + p + 1] * 2 + 2
    p += h(0x21) + h(0x22)
    mult = [(0x23, 2, 2), (0x24, 4, 4), (0x25, 5, 6), (0x26, 3, 3), (0x27, 6, 8), (0x28, 4, 5),
            (0x29, 5, 6), (0x2A, 4, 5), (0x2B, 2, 2), (0x2C, 2, 2), (0x2D, 3, 4), (0x2E, 2, 2)]
    for k, lo, hi in mult:
        p += sh(k, False) * lo + sh(k, True) * hi
    return p

def convert(data, scale=None):
    """scale (num, den): multiply every node's scale and translation (stage world-scale fix)."""
    w = list(struct.unpack('<%di' % (len(data) // 4), data[:len(data) // 4 * 4]))
    n = w[0]
    links = [w[1 + 4 * b: 5 + 4 * b] for b in range(n)]
    out = w[:1 + 4 * n]
    i = 1 + 4 * n
    stats = {}
    for b in walk_order(links):
        t = w[i]
        stats[t] = stats.get(t, 0) + 1
        if t == 0:
            out.append(0); i += 1
        elif t == 2:
            out += w[i:i + 2]; i += 2
        elif t == 3:
            ln = 3 + w[i + 2] * 2; out += w[i:i + ln]; i += ln
        elif t == 4:
            hi = struct.unpack('<hh', struct.pack('<i', w[i + 5]))
            ln = 0x13 + w[i + 4] * 2 + hi[0] * 2 + hi[1] * 2
            out += w[i:i + ln]; i += ln
        elif t == 1:
            ln = mesh_len_bag1(w, i)
            hdr = w[i:i + 0x3C]
            new = [hdr[0]] + hdr[1:0x1D] + [0] * 8 + hdr[0x1D:0x2F] + [0] * 4 + hdr[0x2F:0x3C]
            assert len(new) == 0x48
            out += new + w[i + 0x3C:i + ln]; i += ln
        else:
            raise ValueError(f'bone {b}: unknown type {t} at word {i}')
        xf = w[i:i + 10]
        if scale:
            xf = xf[:2] + [v * scale[0] // scale[1] for v in xf[2:5]] + xf[5:6] + \
                 [v * scale[0] // scale[1] for v in xf[6:9]] + xf[9:]
        out += xf; i += 10
    tail = data[i * 4:]
    return struct.pack('<%di' % len(out), *out) + tail, stats, len(tail)

if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    data = open(src, 'rb').read()
    res, stats, tail = convert(data)
    open(dst, 'wb').write(res)
    print(f'{src}: {len(data)} -> {len(res)} bytes, node types {stats}, {tail} trailing bytes')

def mesh_len_bag2(w, i):
    h = lambda k: w[i + k]
    sh = lambda k, hi: struct.unpack('<hh', struct.pack('<i', w[i + k]))[1 if hi else 0]
    p = 0x48 + h(0x25) * 2
    for _ in range(h(0x27) + h(0x28)):
        p += w[i + p + 1] * 2 + 2
    p += h(0x29) + h(0x2A)
    mult = [(0x2B, 2, 2), (0x2C, 4, 4), (0x2D, 5, 6), (0x2E, 3, 3), (0x2F, 6, 8), (0x30, 4, 5),
            (0x31, 5, 6), (0x32, 4, 5), (0x33, 2, 2), (0x34, 2, 2), (0x35, 3, 4), (0x36, 2, 2),
            (0x37, 4, 5), (0x38, 6, 8), (0x39, 6, 8)]
    for k, lo, hi in mult:
        p += sh(k, False) * lo + sh(k, True) * hi
    p += sh(0x3A, False) * 4
    return p * 4 + sh(0x3A, True) * 0x14     # bytes

def check_bag2(data):
    """Walk a BAG2-layout model; returns trailing bytes (0 = the layout parses exactly)."""
    w = list(struct.unpack('<%di' % (len(data) // 4), data[:len(data) // 4 * 4]))
    n = w[0]; links = [w[1 + 4 * b: 5 + 4 * b] for b in range(n)]
    i = (1 + 4 * n) * 4
    for b in walk_order(links):
        wi = i // 4; t = w[wi]
        if t == 0: i += 4
        elif t == 2: i += 8
        elif t == 3: i += (3 + w[wi + 2] * 2) * 4
        elif t == 4:
            hi = struct.unpack('<hh', struct.pack('<i', w[wi + 5])); i += (0x13 + w[wi + 4] * 2 + hi[0] * 2 + hi[1] * 2) * 4
        elif t == 1: i += mesh_len_bag2(w, wi)
        else: raise ValueError(f'bone {b}: type {t}')
        i += 40
    return len(data) - i
