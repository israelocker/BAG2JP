"""Minimal ISO9660 reader for raw 2352-byte MODE2 PS1 images.
usage: iso_extract.py <bin> list | <bin> extract <outdir> [glob...]"""
import sys, struct, os, fnmatch

class Disc:
    def __init__(self, path):
        self.f = open(path, 'rb')
        hdr = self.f.read(16)
        self.raw = hdr[:12] == b'\x00' + b'\xff' * 10 + b'\x00'
    def sector(self, lba):
        if self.raw:
            self.f.seek(lba * 2352 + 24); return self.f.read(2048)
        self.f.seek(lba * 2048); return self.f.read(2048)
    def read(self, lba, size):
        out = bytearray()
        while len(out) < size:
            out += self.sector(lba); lba += 1
        return bytes(out[:size])
    def walk(self):
        pvd = self.sector(16)
        root = pvd[156:156 + 34]
        yield from self._dir(struct.unpack_from('<I', root, 2)[0], struct.unpack_from('<I', root, 10)[0], '')
    def _dir(self, lba, size, prefix):
        data = self.read(lba, size); o = 0
        while o < len(data):
            ln = data[o]
            if ln == 0:
                o = (o // 2048 + 1) * 2048; continue
            rec = data[o:o + ln]; o += ln
            elba, esz = struct.unpack_from('<I', rec, 2)[0], struct.unpack_from('<I', rec, 10)[0]
            flags = rec[25]; nl = rec[32]; name = rec[33:33 + nl]
            if name in (b'\x00', b'\x01'): continue
            name = name.decode('ascii', 'replace').split(';')[0]
            p = prefix + name
            if flags & 2: yield from self._dir(elba, esz, p + '/')
            else: yield p, elba, esz

if __name__ == '__main__':
    d = Disc(sys.argv[1])
    if sys.argv[2] == 'list':
        for p, l, s in d.walk(): print(f'{l:7d} {s:9d} {p}')
    else:
        out = sys.argv[3]; pats = sys.argv[4:] or ['*']
        for p, l, s in d.walk():
            if any(fnmatch.fnmatch(p, x) for x in pats):
                dst = os.path.join(out, p); os.makedirs(os.path.dirname(dst), exist_ok=True)
                open(dst, 'wb').write(d.read(l, s)); print('x', p, s)
