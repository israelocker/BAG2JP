"""Build a TIM with BAG1 pixels/CLUT rows at the BAG2 TIM's VRAM coordinates.
When the BAG2 CLUT has more rows than the BAG1 one, the extra BAG2 rows are kept after the BAG1
rows (other BAG2 graphics, e.g. the name label, use them).
usage: tim_retarget.py <bag1.tim> <bag2.tim> <out.tim>"""
import struct, sys

def parse(b):
    flags = struct.unpack_from('<I', b, 4)[0]; o = 8; clut = None
    if flags & 8:
        ln, x, y, w, h = struct.unpack_from('<IHHHH', b, o)
        clut = dict(x=x, y=y, w=w, h=h, data=b[o + 12:o + ln]); o += ln
    ln, x, y, w, h = struct.unpack_from('<IHHHH', b, o)
    img = dict(x=x, y=y, w=w, h=h, data=b[o + 12:o + ln])
    return flags, clut, img

def build(flags, clut, img):
    out = struct.pack('<II', 0x10, flags)
    if clut:
        out += struct.pack('<IHHHH', 12 + len(clut['data']), clut['x'], clut['y'], clut['w'], clut['h']) + clut['data']
    out += struct.pack('<IHHHH', 12 + len(img['data']), img['x'], img['y'], img['w'], img['h']) + img['data']
    return out

def retarget(b1, b2):
    f1, c1, i1 = parse(b1); f2, c2, i2 = parse(b2)
    img = dict(i1, x=i2['x'], y=i2['y'])
    clut = None
    if c1:
        clut = dict(c1)
        if c2:
            clut.update(x=c2['x'], y=c2['y'])
            if c2['w'] == c1['w'] and c2['h'] > c1['h']:
                row = c1['w'] * 2
                clut['data'] = c1['data'] + c2['data'][c1['h'] * row:]
                clut['h'] = c2['h']
    return build(f1, clut, img)

if __name__ == '__main__':
    open(sys.argv[3], 'wb').write(retarget(open(sys.argv[1], 'rb').read(), open(sys.argv[2], 'rb').read()))

def paste_rect(dst_tim, src_tim, x0, y0, x1, y1):
    """4bpp: copy pixels [x0,x1) x [y0,y1) (x even) from src TIM into dst TIM (same size)."""
    fd, cd, idd = parse(dst_tim); fs, cs, isrc = parse(src_tim)
    rowb = idd['w'] * 2
    d = bytearray(idd['data']); s = isrc['data']
    for y in range(y0, y1):
        d[y * rowb + x0 // 2: y * rowb + x1 // 2] = s[y * rowb + x0 // 2: y * rowb + x1 // 2]
    idd = dict(idd, data=bytes(d))
    return build(fd, cd, idd)
