"""Dancer motion request code -> model anim index, read from both main exes.
BAG2 FUN_8002a090, BAG1 FUN_80030090."""
import struct
B2 = open('_work/mainexe/slpm.bin', 'rb').read()
B1 = open('_work/bag1/scus.bin', 'rb').read()
def rb(b, a): return b[a - 0x80010000]
def bag2(r):
    if r < 0x2b: return rb(B2, 0x8005180c + r)
    if r < 100:
        v = rb(B2, 0x8005182e + r); return None if v == 0 or v > 0x4f else v
    if r < 200: return rb(B2, 0x8005181c + r)
    if r < 300: return rb(B2, 0x800518e4 + r - 200)
def bag1(r):
    if r < 0x24: return rb(B1, 0x80055830 + r)
    if r < 100:
        if 0x32 <= r < 0x35: return rb(B1, 0x8005585e + r)
        if 0x3c <= r < 0x3f: return rb(B1, 0x80055857 + r)
        if 0x46 <= r < 0x49: return rb(B1, 0x80055850 + r)
        return None
    if r < 0xb4: return rb(B1, 0x80055838 + r)
    if r < 200: return None
    if r < 300: return rb(B1, 0x800558ec + r - 200)
def overrides():
    o2 = [tuple(B2[0x80051838 - 0x80010000 + 4 * i:][:4]) for i in range(10)]
    o1 = [tuple(B1[0x80055854 - 0x80010000 + 4 * i:][:4]) for i in range(15)]
    return o2, o1
if __name__ == '__main__':
    for r in range(300):
        a, b = bag2(r), bag1(r)
        if a is None and b is None: continue
        print(f'req {r:3d} (0x{r:02x}): BAG2 {a}  BAG1 {b}')
    o2, o1 = overrides(); print('BAG2 overrides (from,to,if cur):', o2); print('BAG1 overrides (from,to,cur a,cur b):', o1)
